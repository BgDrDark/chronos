import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func
from backend.database.database import AsyncSessionLocal
from backend.database import models
from backend.config import settings

logger = logging.getLogger(__name__)


async def generate_request_number(db, company_id: int, is_auto: bool = False) -> str:
    """Generate a unique request number."""
    prefix = "AR" if is_auto else "PR"
    year = datetime.now().year
    
    stmt = select(func.count(models.PurchaseRequest.id)).where(
        models.PurchaseRequest.company_id == company_id
    )
    result = await db.execute(stmt)
    count = result.scalar() or 0
    
    return f"{prefix}-{year}-{count + 1:05d}"


async def check_inventory_levels():
    """
    Periodic job to check inventory levels and create auto-purchase requests.
    Runs daily at 2:00 AM.
    """
    logger.info("Starting scheduled inventory level check...")
    
    async with AsyncSessionLocal() as db:
        try:
            stmt = select(models.Ingredient).where(
                models.Ingredient.is_auto_reorder == True,
                models.Ingredient.preferred_supplier_id.isnot(None)
            )
            result = await db.execute(stmt)
            ingredients = result.scalars().all()
            
            created_count = 0
            for ingredient in ingredients:
                total_quantity = 0
                if ingredient.batches:
                    for batch in ingredient.batches:
                        if batch.status == "active" and batch.expiry_date >= datetime.now().date():
                            total_quantity += float(batch.quantity or 0)
                
                min_qty = float(ingredient.min_quantity or 0)
                
                if total_quantity < min_qty:
                    reorder_qty = float(ingredient.reorder_quantity or min_qty * 2)
                    
                    request_number = await generate_request_number(db, ingredient.company_id, is_auto=True)
                    
                    new_request = models.PurchaseRequest(
                        request_number=request_number,
                        requested_by_id=1,
                        department_id=ingredient.storage_zone_id,
                        status="pending",
                        priority="medium",
                        reason=f"Auto-generated: {ingredient.name} below minimum stock ({total_quantity:.2f} < {min_qty:.2f})",
                        is_auto=True,
                        notes=f"Auto-reorder for ingredient: {ingredient.name}",
                        company_id=ingredient.company_id
                    )
                    db.add(new_request)
                    await db.flush()
                    
                    new_item = models.PurchaseRequestItem(
                        purchase_request_id=new_request.id,
                        item_name=ingredient.name,
                        quantity=Decimal(str(reorder_qty)),
                        unit=ingredient.unit,
                        notes=f"Min: {min_qty}, Current: {total_quantity:.2f}"
                    )
                    db.add(new_item)
                    
                    created_count += 1
                    logger.info(f"Created auto-purchase request {request_number} for {ingredient.name}")
            
            await db.commit()
            logger.info(f"Inventory check completed. Created {created_count} auto-purchase requests.")
            
        except Exception as e:
            logger.error(f"Error during inventory check: {e}")
            await db.rollback()
            raise
