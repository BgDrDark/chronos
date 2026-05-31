import datetime
import uuid
from decimal import Decimal

import strawberry
from sqlalchemy import func, select

from backend.exceptions import (
    NotFoundException,
    ValidationException,
)
from backend.graphql import inputs, types
from backend.graphql.utils.permission_checker import (
    check_company_access,
    get_current_user,
)
from backend.utils.error_handling import handle_db_error


@strawberry.type
class InventoryMutation:
    @strawberry.mutation
    async def create_ingredient(self, input: inputs.IngredientInput, info: strawberry.Info) -> types.Ingredient:
        db = info.context["db"]
        current_user = get_current_user(info)
        
        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")
        
        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)
        
        from backend.database.models import Ingredient
        ingredient = Ingredient(
            name=input.name,
            unit=input.unit,
            barcode=input.barcode,
            baseline_min_stock=input.baseline_min_stock,
            current_price=input.current_price,
            storage_zone_id=input.storage_zone_id,
            is_perishable=input.is_perishable,
            expiry_warning_days=input.expiry_warning_days,
            allergens=input.allergens,
            company_id=target_company_id
        )
        db.add(ingredient)
        await db.commit()
        await db.refresh(ingredient)
        return types.Ingredient.from_instance(ingredient)

    @strawberry.mutation
    async def update_ingredient(self, input: inputs.IngredientInput, info: strawberry.Info) -> types.Ingredient:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import Ingredient
        ingredient = await db.get(Ingredient, input.id)
        if not ingredient:
            raise NotFoundException.ingredient()

        await check_company_access(db, current_user, "Ingredient", input.id)

        ingredient.name = input.name
        ingredient.unit = input.unit
        ingredient.barcode = input.barcode
        ingredient.baseline_min_stock = input.baseline_min_stock
        ingredient.current_price = input.current_price
        ingredient.storage_zone_id = input.storage_zone_id
        ingredient.is_perishable = input.is_perishable
        ingredient.expiry_warning_days = input.expiry_warning_days
        ingredient.allergens = input.allergens
        ingredient.product_type = input.product_type

        await db.commit()
        await db.refresh(ingredient)
        return types.Ingredient.from_instance(ingredient)

    @strawberry.mutation
    async def create_storage_zone(self, input: inputs.StorageZoneInput, info: strawberry.Info) -> types.StorageZone:
        db = info.context["db"]
        current_user = get_current_user(info)

        target_company_id = input.company_id if current_user.role.name == "super_admin" else current_user.company_id
        if not target_company_id:
            raise ValidationException.required_field("Company ID")

        from backend.database.models import Company
        stmt = select(Company).where(Company.id == target_company_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundException.resource("Фирма", target_company_id)

        from backend.database.models import StorageZone
        zone = StorageZone(
            name=input.name,
            temp_min=input.temp_min,
            temp_max=input.temp_max,
            description=input.description,
            is_active=input.is_active if input.is_active is not None else True,
            asset_type=input.asset_type or "KMA",
            zone_type=input.zone_type or "food",
            company_id=target_company_id
        )
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        return types.StorageZone.from_instance(zone)

    @strawberry.mutation
    async def update_storage_zone(self, input: inputs.UpdateStorageZoneInput,
                                info: strawberry.Info) -> types.StorageZone:
        db = info.context["db"]
        current_user = get_current_user(info)
        from backend.database.models import StorageZone
        stmt = select(StorageZone).where(StorageZone.id == input.id)
        res = await db.execute(stmt)
        zone = res.scalar_one_or_none()
        if not zone:
            raise NotFoundException.resource("Зона")
        await check_company_access(db, current_user, "StorageZone", input.id)
        zone.name = input.name
        zone.temp_min = input.temp_min
        zone.temp_max = input.temp_max
        zone.description = input.description
        zone.is_active = input.is_active if input.is_active is not None else True
        zone.asset_type = input.asset_type or "KMA"
        zone.zone_type = input.zone_type or "food"
        await db.commit()
        await db.refresh(zone)
        return types.StorageZone.from_instance(zone)

    @strawberry.mutation
    async def add_batch(self, input: inputs.BatchInput, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import Batch, Ingredient
        res = await db.get(Ingredient, input.ingredient_id)
        if not res:
            raise NotFoundException.ingredient()
        await check_company_access(db, current_user, "Ingredient", input.ingredient_id)

        batch = Batch(
            ingredient_id=input.ingredient_id,
            batch_number=input.batch_number,
            quantity=input.quantity,
            expiry_date=input.expiry_date,
            supplier_id=input.supplier_id,
            invoice_number=input.invoice_number,
            storage_zone_id=input.storage_zone_id,
            status="active"
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_instance(batch)

    @strawberry.mutation
    async def update_batch(self, input: inputs.BatchInput, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import Batch
        batch = await db.get(Batch, input.id)
        if not batch:
            raise NotFoundException.record("Batch")

        await check_company_access(db, current_user, "Batch", input.id)

        batch.ingredient_id = input.ingredient_id
        batch.batch_number = input.batch_number
        batch.quantity = input.quantity
        batch.expiry_date = input.expiry_date
        batch.supplier_id = input.supplier_id
        batch.invoice_number = input.invoice_number
        batch.storage_zone_id = input.storage_zone_id

        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_instance(batch)

    @strawberry.mutation
    async def update_batch_status(self, id: int, status: str, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import Batch
        batch = await db.get(Batch, id)
        if not batch:
            raise NotFoundException.record("Batch")

        await check_company_access(db, current_user, "Batch", id)

        batch.status = status
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_instance(batch)

    @strawberry.mutation
    async def start_inventory_session(self, info: strawberry.Info) -> types.InventorySession:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import InventorySession, sofia_now

        session = InventorySession(
            company_id=current_user.company_id,
            started_by=current_user.id,
            started_at=sofia_now(),
            status="active"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return types.InventorySession.from_instance(session)

    @strawberry.mutation
    async def complete_inventory_session(self, session_id: int, info: strawberry.Info) -> types.InventorySession:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import (
            Batch,
            InventoryItem,
            InventorySession,
            sofia_now,
        )

        session = await db.get(InventorySession, session_id)
        if not session:
            raise NotFoundException.session()
        await check_company_access(db, current_user, "InventorySession", session_id)
        if session.status != "active":
            raise ValidationException.field("Session", "Не е активна")

        stmt = select(InventoryItem).where(InventoryItem.session_id == session_id)
        res = await db.execute(stmt)
        items = res.scalars().all()

        protocol_number = f"INV-{sofia_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        for item in items:
            if item.found_quantity is None:
                continue

            stmt = select(Batch).where(
                Batch.ingredient_id == item.ingredient_id,
                Batch.status == "active"
            ).order_by(Batch.expiry_date.asc())
            res = await db.execute(stmt)
            batches = res.scalars().all()

            target_qty = float(item.found_quantity)
            current_qty = sum(float(b.quantity) for b in batches)
            diff = target_qty - current_qty

            if abs(diff) < 0.001:
                item.adjusted = True
                continue

            if diff > 0:
                new_batch = Batch(
                    ingredient_id=item.ingredient_id,
                    batch_number=f"ADJ-{protocol_number}",
                    quantity=diff,
                    status="active",
                    expiry_date=None
                )
                db.add(new_batch)
            else:
                remaining = abs(diff)
                for batch in batches:
                    if remaining <= 0:
                        break
                    if batch.quantity >= remaining:
                        batch.quantity -= remaining
                        remaining = 0
                    else:
                        remaining -= batch.quantity
                        batch.quantity = 0
                        batch.status = "depleted"

            item.adjusted = True

        session.status = "completed"
        session.completed_at = sofia_now()
        session.protocol_number = protocol_number

        await db.commit()
        await db.refresh(session)
        return types.InventorySession.from_instance(session)

    @strawberry.mutation
    async def add_inventory_item(
            self,
            session_id: int,
            ingredient_id: int,
            found_quantity: float,
            info: strawberry.Info
    ) -> types.InventoryItem:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import (
            Batch,
            Ingredient,
            InventoryItem,
            InventorySession,
        )

        session = await db.get(InventorySession, session_id)
        if not session:
            raise NotFoundException.session()
        await check_company_access(db, current_user, "InventorySession", session_id)
        if session.status != "active":
            raise ValidationException.field("Session", "Не е активна")

        ingredient = await db.get(Ingredient, ingredient_id)
        if not ingredient:
            raise NotFoundException.ingredient()

        stmt = select(func.coalesce(func.sum(Batch.quantity), 0)).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active"
        )
        res = await db.execute(stmt)
        system_qty = res.scalar() or 0

        difference = found_quantity - float(system_qty)

        stmt = select(InventoryItem).where(
            InventoryItem.session_id == session_id,
            InventoryItem.ingredient_id == ingredient_id
        )
        res = await db.execute(stmt)
        item = res.scalars().first()

        if item:
            item.found_quantity = found_quantity
            item.system_quantity = system_qty
            item.difference = difference
        else:
            item = InventoryItem(
                session_id=session_id,
                ingredient_id=ingredient_id,
                found_quantity=found_quantity,
                system_quantity=system_qty,
                difference=difference
            )
            db.add(item)

        await db.commit()
        await db.refresh(item)
        return types.InventoryItem.from_instance(item)

    @strawberry.mutation
    async def consume_from_batch(
        self,
        batch_id: int,
        quantity: Decimal,
        reason: str,
        info: strawberry.Info,
        notes: str | None = None,
    ) -> types.Batch:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import Batch, StockConsumptionLog
        
        batch = await db.get(Batch, batch_id)
        if not batch:
            raise NotFoundException.record("Партида")
        
        if batch.quantity < quantity:
            raise ValidationException.field("quantity", f"Недостатъчно количество (Налично: {batch.quantity})")

        batch.quantity -= quantity
        if batch.quantity == 0:
            batch.status = "depleted"

        log = StockConsumptionLog(
            ingredient_id=batch.ingredient_id,
            batch_id=batch.id,
            quantity=quantity,
            reason=reason,
            notes=notes,
            created_by=current_user.id
        )
        db.add(log)
        
        try:
            await db.commit()
            await db.refresh(batch)
            return types.Batch.from_instance(batch)
        except Exception as e:
            await db.rollback()
            raise handle_db_error(e) from None

    @strawberry.mutation
    async def bulk_add_batches(
            self,
            invoice_number: str,
            supplier_id: int,
            date: datetime.date,
            items: list[inputs.BatchInput],
            create_invoice: bool,
            info: strawberry.Info
    ) -> list[types.Batch]:
        """Bulk add batches from a single delivery and optionally create an invoice"""
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database import models

        batches = []
        invoice_items_data = []
        total_subtotal = Decimal("0")

        # 1. Create Batches
        for idx, item_input in enumerate(items):
            ingredient = await db.get(models.Ingredient, item_input.ingredient_id)
            if not ingredient:
                continue

            # Auto-generate batch number if not provided
            batch_number = item_input.batch_number
            if not batch_number:
                batch_number = f"{date.strftime('%Y%m%d')}-{idx + 1:03d}"

            new_batch = models.Batch(
                ingredient_id=item_input.ingredient_id,
                batch_number=batch_number,
                quantity=item_input.quantity,
                expiry_date=item_input.expiry_date,
                supplier_id=supplier_id,
                invoice_number=invoice_number,
                invoice_date=date,
                storage_zone_id=item_input.storage_zone_id or ingredient.storage_zone_id,
                status="active",
                is_stock_receipt=True
            )
            db.add(new_batch)
            await db.flush()
            batches.append(new_batch)

            if create_invoice:
                unit_price = ingredient.current_price or Decimal("0")
                item_total = item_input.quantity * unit_price
                total_subtotal += item_total
                invoice_items_data.append({
                    "ingredient_id": ingredient.id,
                    "batch_id": new_batch.id,
                    "name": ingredient.name,
                    "quantity": item_input.quantity,
                    "unit": ingredient.unit,
                    "unit_price": unit_price,
                    "total": item_total,
                    "batch_number": batch_number,
                    "expiration_date": item_input.expiry_date
                })

        # 2. Optionally Create Invoice
        if create_invoice and batches:
            vat_rate = Decimal("20.0")
            vat_amount = total_subtotal * (vat_rate / 100)
            total = total_subtotal + vat_amount

            invoice = models.Invoice(
                number=invoice_number,
                type="incoming",
                date=date,
                supplier_id=supplier_id,
                subtotal=total_subtotal,
                discount_percent=Decimal("0"),
                discount_amount=Decimal("0"),
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                total=total,
                status="draft",
                company_id=current_user.company_id,
                created_by=current_user.id
            )
            db.add(invoice)
            await db.flush()

            for item_data in invoice_items_data:
                inv_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    ingredient_id=item_data["ingredient_id"],
                    batch_id=item_data["batch_id"],
                    name=item_data["name"],
                    quantity=item_data["quantity"],
                    unit=item_data["unit"],
                    unit_price=item_data["unit_price"],
                    discount_percent=Decimal("0"),
                    total=item_data["total"],
                    batch_number=item_data.get("batch_number"),
                    expiration_date=item_data.get("expiration_date")
                )
                db.add(inv_item)
                await db.flush()
                
                # Обнови партидата с цената от фактурата
                if item_data.get("batch_id"):
                    batch = await db.get(models.Batch, item_data["batch_id"])
                    if batch:
                        batch.price_no_vat = float(item_data["unit_price"])
                        batch.price_with_vat = float(item_data["unit_price"]) * 1.2  # 20% ДДС

        await db.commit()
        for b in batches:
            await db.refresh(b)

        return [types.Batch.from_instance(b) for b in batches]
