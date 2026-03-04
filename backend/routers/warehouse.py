from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import date, datetime
from backend.database.database import get_db
from backend.auth.jwt_utils import get_current_user
from backend.database import models
from backend import schemas, crud
from backend.auth.module_guard import require_module_dep

router = APIRouter(
    prefix="/warehouse",
    tags=["warehouse"],
    dependencies=[Depends(require_module_dep("confectionery"))]
)

@router.get("/zones", response_model=List[schemas.StorageZone])
async def get_storage_zones(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Списък със складове/зони (т. 1 - Проверка на брой складове)"""
    stmt = select(models.StorageZone)
    if current_user.role.name != "super_admin":
        stmt = stmt.where(models.StorageZone.company_id == current_user.company_id)
    
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/search-ingredient", response_model=List[schemas.Ingredient])
async def search_ingredient(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Търсене по баркод или име (т. 2)"""
    from backend.database.models import Ingredient
    stmt = select(Ingredient).where(
        (Ingredient.name.ilike(f"%{query}%")) | 
        (Ingredient.barcode == query)
    )
    if current_user.role.name != "super_admin":
        stmt = stmt.where(Ingredient.company_id == current_user.company_id)
        
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/receipt", response_model=schemas.Batch)
async def create_warehouse_receipt(
    batch_in: schemas.BatchCreate,
    create_invoice: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Прием на стока (т. 4, т. 7) - опция за автоматично създаване на фактура"""
    from decimal import Decimal
    
    # 1. Check if ingredient exists
    ingredient = await db.get(models.Ingredient, batch_in.ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Продуктът не е намерен")

    # 2. Create Batch (Receiving)
    new_batch = models.Batch(
        **batch_in.model_dump(),
        received_by=current_user.id,
        received_at=datetime.now(),
        status="active"
    )
    
    db.add(new_batch)
    await db.flush()
    
    # 3. Create Invoice automatically if requested
    if create_invoice:
        # Складова/Стокова Разписка format: СР-YYYYMMDD-XXXX
        invoice_number = f"СР-{datetime.now().strftime('%Y%m%d')}-{new_batch.id:04d}"
        
        subtotal = Decimal(str(batch_in.price_no_vat or 0))
        vat_rate = Decimal(str(batch_in.vat_percent or 20))
        vat_amount = subtotal * vat_rate / Decimal("100")
        total = subtotal + vat_amount
        
        new_invoice = models.Invoice(
            number=invoice_number,
            type="incoming",
            date=batch_in.invoice_date or date.today(),
            supplier_id=batch_in.supplier_id,
            batch_id=new_batch.id,
            subtotal=subtotal,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            total=total,
            status="paid",
            company_id=current_user.company_id,
            created_by=current_user.id
        )
        db.add(new_invoice)
        await db.flush()
        
        # 4. Create InvoiceItem
        if ingredient:
            invoice_item = models.InvoiceItem(
                invoice_id=new_invoice.id,
                ingredient_id=ingredient.id,
                batch_id=new_batch.id,
                name=ingredient.name,
                quantity=batch_in.quantity,
                unit=ingredient.unit,
                unit_price=ingredient.current_price or Decimal("1"),
                total=total
            )
            db.add(invoice_item)
    
    await db.commit()
    await db.refresh(new_batch)
    return new_batch

@router.post("/scrap", status_code=status.HTTP_201_CREATED)
async def report_scrap(
    ingredient_id: int,
    quantity: float,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Брак (т. 6)"""
    # Validation: Scrap cannot be more than received today
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    stmt = select(func.sum(models.Batch.quantity)).where(
        models.Batch.ingredient_id == ingredient_id,
        models.Batch.received_at >= today_start,
        models.Batch.status == "active"
    )
    res = await db.execute(stmt)
    received_today = res.scalar() or 0
    
    if quantity >= float(received_today):
        raise HTTPException(
            status_code=400, 
            detail="Бракът не може да бъде по-голям или равен на заведеното количество за деня."
        )

    # Logic for scrap (create a special negative batch or update status)
    scrap_batch = models.Batch(
        ingredient_id=ingredient_id,
        quantity=-quantity,
        batch_number="SCRAP",
        expiry_date=date.today(),
        status="scrap",
        received_by=current_user.id,
        received_at=datetime.now()
    )
    db.add(scrap_batch)
    await db.commit()
    return {"status": "success", "message": "Бракът е отразен"}


@router.post("/receipt/{batch_id}/create-invoice")
async def create_invoice_from_batch(
    batch_id: int,
    supplier_id: Optional[int] = None,
    invoice_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Създаване на входяща фактура от съществуваща партида"""
    from decimal import Decimal
    
    # 1. Get batch
    batch = await db.get(models.Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Партидата не е намерена")
    
    # 2. Check if invoice already exists for this batch
    if batch.invoice_number:
        raise HTTPException(status_code=400, detail="Фактура за тази партида вече съществува")
    
    # 3. Get ingredient
    ingredient = await db.get(models.Ingredient, batch.ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Артикулът не е намерен")
    
    # 4. Create invoice
    # Складова/Стокова Разписка format: СР-YYYYMMDD-XXXX
    invoice_number = f"СР-{datetime.now().strftime('%Y%m%d')}-{batch.id:04d}"
    
    subtotal = Decimal(str(batch.price_no_vat or 0))
    if subtotal == 0 and ingredient.current_price:
        subtotal = ingredient.current_price * batch.quantity
    
    vat_rate = Decimal(str(batch.vat_percent or 20))
    vat_amount = subtotal * vat_rate / Decimal("100")
    total = subtotal + vat_amount
    
    new_invoice = models.Invoice(
        number=invoice_number,
        type="incoming",
        date=invoice_date or date.today(),
        supplier_id=supplier_id or batch.supplier_id,
        batch_id=batch.id,
        subtotal=subtotal,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        total=total,
        status="paid",
        company_id=current_user.company_id,
        created_by=current_user.id
    )
    db.add(new_invoice)
    await db.flush()
    
    # 5. Create InvoiceItem
    invoice_item = models.InvoiceItem(
        invoice_id=new_invoice.id,
        ingredient_id=ingredient.id,
        batch_id=batch.id,
        name=ingredient.name,
        quantity=batch.quantity,
        unit=ingredient.unit,
        unit_price=ingredient.current_price or Decimal("1"),
        total=total
    )
    db.add(invoice_item)
    
    # 6. Update batch with invoice number
    batch.invoice_number = invoice_number
    
    await db.commit()
    await db.refresh(new_invoice)
    return new_invoice
