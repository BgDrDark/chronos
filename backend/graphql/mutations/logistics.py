import datetime
import logging
from decimal import Decimal

import strawberry
from sqlalchemy import func, select

from backend.database.transaction_manager import atomic_transaction
from backend.exceptions import (
    AuthenticationException,
    PermissionDeniedException,
    ValidationException,
)
from backend.graphql import inputs, types

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class LogisticsMutation:

    @strawberry.mutation
    async def create_storage_zone(self, input: inputs.StorageZoneInput, info: strawberry.Info) -> types.StorageZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Company, StorageZone

        company = await db.get(Company, input.company_id)
        if not company:
            raise PermissionDeniedException.for_action("manage storage zones")
        if current_user.role.name not in ["admin", "super_admin"] and company.id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage storage zones")

        zone = StorageZone(
            name=input.name,
            temp_min=input.temp_min,
            temp_max=input.temp_max,
            description=input.description,
            company_id=input.company_id,
            is_active=input.is_active if input.is_active is not None else True,
            asset_type=input.asset_type or "KMA",
            zone_type=input.zone_type or "food",
        )
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        return types.StorageZone.from_pydantic(zone)

    @strawberry.mutation
    async def update_storage_zone(self, input: inputs.UpdateStorageZoneInput, info: strawberry.Info) -> types.StorageZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import StorageZone

        zone = await db.get(StorageZone, input.id)
        if not zone:
            raise ValidationException(detail="Зоната не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and zone.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage storage zones")

        zone.name = input.name
        zone.temp_min = input.temp_min
        zone.temp_max = input.temp_max
        zone.description = input.description
        zone.is_active = input.is_active if input.is_active is not None else True
        zone.asset_type = input.asset_type or "KMA"
        zone.zone_type = input.zone_type or "food"
        await db.commit()
        await db.refresh(zone)
        return types.StorageZone.from_pydantic(zone)

    @strawberry.mutation
    async def create_supplier(self, input: inputs.SupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Company, Supplier

        company = await db.get(Company, input.company_id)
        if not company:
            raise PermissionDeniedException.for_action("manage suppliers")
        if current_user.role.name not in ["admin", "super_admin"] and company.id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage suppliers")

        supplier = Supplier(
            name=input.name, eik=input.eik, vat_number=input.vat_number,
            address=input.address, contact_person=input.contact_person,
            phone=input.phone, email=input.email, company_id=input.company_id,
        )
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
        return types.Supplier.from_pydantic(supplier)

    @strawberry.mutation
    async def update_supplier(self, input: inputs.UpdateSupplierInput, info: strawberry.Info) -> types.Supplier:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Supplier

        supplier = await db.get(Supplier, input.id)
        if not supplier:
            raise ValidationException(detail="Доставчикът не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and supplier.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage suppliers")

        supplier.name = input.name
        supplier.eik = input.eik
        supplier.vat_number = input.vat_number
        supplier.address = input.address
        supplier.contact_person = input.contact_person
        supplier.phone = input.phone
        supplier.email = input.email
        await db.commit()
        await db.refresh(supplier)
        return types.Supplier.from_pydantic(supplier)

    @strawberry.mutation
    async def create_ingredient(self, input: inputs.IngredientInput, info: strawberry.Info) -> types.Ingredient:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Company, Ingredient

        company = await db.get(Company, input.company_id)
        if not company:
            raise PermissionDeniedException.for_action("manage ingredients")
        if current_user.role.name not in ["admin", "super_admin"] and company.id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage ingredients")

        ingredient = Ingredient(
            name=input.name, unit=input.unit, barcode=input.barcode,
            baseline_min_stock=input.baseline_min_stock,
            current_price=input.current_price,
            storage_zone_id=input.storage_zone_id,
            is_perishable=input.is_perishable,
            expiry_warning_days=input.expiry_warning_days,
            allergens=input.allergens or [],
            company_id=input.company_id,
            product_type=input.product_type or "raw",
        )
        db.add(ingredient)
        await db.commit()
        await db.refresh(ingredient)
        return types.Ingredient.from_pydantic(ingredient)

    @strawberry.mutation
    async def update_ingredient(self, input: inputs.IngredientInput, info: strawberry.Info) -> types.Ingredient:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Ingredient

        ingredient = await db.get(Ingredient, input.id)
        if not ingredient:
            raise ValidationException(detail="Съставката не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage ingredients")

        ingredient.name = input.name
        ingredient.unit = input.unit
        ingredient.barcode = input.barcode
        ingredient.baseline_min_stock = input.baseline_min_stock
        ingredient.current_price = input.current_price
        ingredient.storage_zone_id = input.storage_zone_id
        ingredient.is_perishable = input.is_perishable
        ingredient.expiry_warning_days = input.expiry_warning_days
        ingredient.allergens = input.allergens or []
        ingredient.product_type = input.product_type or "raw"
        await db.commit()
        await db.refresh(ingredient)
        return types.Ingredient.from_pydantic(ingredient)

    @strawberry.mutation
    async def add_batch(self, input: inputs.BatchInput, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Batch, Ingredient

        ingredient = await db.get(Ingredient, input.ingredient_id)
        if not ingredient:
            raise ValidationException(detail="Съставката не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage batches")

        batch = Batch(
            ingredient_id=input.ingredient_id,
            batch_number=input.batch_number,
            quantity=input.quantity,
            expiry_date=input.expiry_date,
            status="active",
            received_at=datetime.datetime.now(),
            supplier_id=input.supplier_id,
            invoice_number=input.invoice_number,
            storage_zone_id=input.storage_zone_id,
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_pydantic(batch)

    @strawberry.mutation
    async def update_batch_status(self, id: int, status: str, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Batch, Ingredient

        batch = await db.get(Batch, id)
        if not batch:
            raise ValidationException(detail="Партидата не съществува")
        ingredient = await db.get(Ingredient, batch.ingredient_id)
        if current_user.role.name not in ["admin", "super_admin"] and ingredient and ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage batches")

        batch.status = status
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_pydantic(batch)

    @strawberry.mutation
    async def update_batch(self, input: inputs.BatchInput, info: strawberry.Info) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Batch, Ingredient

        batch = await db.get(Batch, input.id)
        if not batch:
            raise ValidationException(detail="Партидата не съществува")
        ingredient = await db.get(Ingredient, batch.ingredient_id)
        if current_user.role.name not in ["admin", "super_admin"] and ingredient and ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage batches")

        batch.batch_number = input.batch_number
        batch.quantity = input.quantity
        batch.expiry_date = input.expiry_date
        batch.supplier_id = input.supplier_id
        batch.invoice_number = input.invoice_number
        batch.storage_zone_id = input.storage_zone_id
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_pydantic(batch)

    @strawberry.mutation
    async def consume_from_batch(
            self, batch_id: int, quantity: Decimal, reason: str,
            info: strawberry.Info, notes: str | None = None,
    ) -> types.Batch:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Batch, StockConsumptionLog

        batch = await db.get(Batch, batch_id)
        if not batch:
            raise ValidationException(detail="Партидата не съществува")

        if quantity > batch.quantity:
            raise ValidationException(detail="Количеството надвишава наличното")

        batch.quantity -= quantity

        log = StockConsumptionLog(
            ingredient_id=batch.ingredient_id,
            batch_id=batch.id,
            quantity=quantity,
            reason=reason,
            notes=notes,
            created_by=current_user.id,
            created_at=datetime.datetime.now(),
        )
        db.add(log)
        await db.commit()
        await db.refresh(batch)
        return types.Batch.from_pydantic(batch)

    @strawberry.mutation
    async def auto_consume_fefo(
            self, ingredient_id: int, quantity: Decimal, reason: str,
            info: strawberry.Info, notes: str | None = None,
    ) -> list[types.StockConsumptionLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Batch, StockConsumptionLog

        stmt = select(Batch).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active",
            Batch.quantity > 0,
        ).order_by(Batch.expiry_date.asc())
        res = await db.execute(stmt)
        batches = res.scalars().all()

        logs = []
        remaining = quantity
        for batch in batches:
            if remaining <= 0:
                break
            to_take = min(batch.quantity, remaining)
            batch.quantity -= to_take

            log = StockConsumptionLog(
                ingredient_id=ingredient_id,
                batch_id=batch.id,
                quantity=to_take,
                reason=reason,
                notes=notes,
                created_by=current_user.id,
                created_at=datetime.datetime.now(),
            )
            db.add(log)
            logs.append(log)
            remaining -= to_take

        if remaining > 0:
            raise ValidationException(detail="Няма достатъчно наличност")

        await db.commit()
        return [types.StockConsumptionLog.from_instance(l) for l in logs]

    @strawberry.mutation
    async def start_inventory_session(self, info: strawberry.Info) -> types.InventorySession:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import InventorySession, sofia_now

        session = InventorySession(
            company_id=current_user.company_id,
            started_by=current_user.id,
            started_at=sofia_now(),
            status="in_progress",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return types.InventorySession.from_instance(session)

    @strawberry.mutation
    async def add_inventory_item(
            self, session_id: int, ingredient_id: int, found_quantity: float,
            info: strawberry.Info,
    ) -> types.InventoryItem:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            Batch,
            Ingredient,
            InventoryItem,
            InventorySession,
        )

        session = await db.get(InventorySession, session_id)
        if not session:
            raise ValidationException(detail="Сесията не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and session.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage inventory")

        ingredient = await db.get(Ingredient, ingredient_id)
        if not ingredient:
            raise ValidationException(detail="Съставката не съществува")

        stmt = select(func.coalesce(func.sum(Batch.quantity), 0)).where(
            Batch.ingredient_id == ingredient_id, Batch.status == "active",
        )
        res = await db.execute(stmt)
        system_qty = res.scalar() or 0

        existing_stmt = select(InventoryItem).where(
            InventoryItem.session_id == session_id,
            InventoryItem.ingredient_id == ingredient_id,
        )
        existing_res = await db.execute(existing_stmt)
        existing = existing_res.scalars().first()

        if existing:
            existing.found_quantity = Decimal(str(found_quantity))
            existing.difference = existing.found_quantity - existing.system_quantity
            await db.commit()
            await db.refresh(existing)
            return types.InventoryItem.from_instance(existing)

        item = InventoryItem(
            session_id=session_id, ingredient_id=ingredient_id,
            found_quantity=Decimal(str(found_quantity)),
            system_quantity=Decimal(str(system_qty)),
            difference=Decimal(str(found_quantity)) - Decimal(str(system_qty)),
            adjusted=False,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return types.InventoryItem.from_instance(item)

    @strawberry.mutation
    async def complete_inventory_session(self, session_id: int, info: strawberry.Info) -> types.InventorySession:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        import uuid

        from backend.database.models import (
            Batch,
            InventoryItem,
            InventorySession,
            sofia_now,
        )

        session = await db.get(InventorySession, session_id)
        if not session:
            raise ValidationException(detail="Сесията не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and session.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage inventory")

        async with atomic_transaction(db):
            session.status = "completed"
            session.completed_at = sofia_now()
            session.protocol_number = f"INV-{session.id}-{uuid.uuid4().hex[:6].upper()}"

            items_stmt = select(InventoryItem).where(InventoryItem.session_id == session_id)
            items_res = await db.execute(items_stmt)
            for item in items_res.scalars().all():
                if not item.adjusted and item.difference is not None and item.difference != 0:
                    batch_stmt = select(Batch).where(
                        Batch.ingredient_id == item.ingredient_id,
                        Batch.status == "active", Batch.quantity > 0,
                    ).order_by(Batch.expiry_date.asc())
                    batch_res = await db.execute(batch_stmt)
                    batch = batch_res.scalars().first()
                    if batch:
                        batch.quantity += item.difference
                    item.adjusted = True

        await db.commit()
        await db.refresh(session)
        return types.InventorySession.from_instance(session)

    @strawberry.mutation
    async def bulk_add_batches(
            self, invoice_number: str, supplier_id: int, date: datetime.date,
            items: list[inputs.BatchInput], create_invoice: bool,
            info: strawberry.Info,
    ) -> list[types.Batch]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Batch, Ingredient, Supplier

        supplier = await db.get(Supplier, supplier_id)
        if not supplier:
            raise ValidationException(detail="Доставчикът не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and supplier.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage batches")

        created_batches = []
        for item in items:
            ingredient = await db.get(Ingredient, item.ingredient_id)
            if not ingredient:
                continue

            batch = Batch(
                ingredient_id=item.ingredient_id,
                batch_number=item.batch_number,
                quantity=item.quantity,
                expiry_date=item.expiry_date,
                status="active",
                received_at=datetime.datetime.now(),
                supplier_id=supplier_id,
                invoice_number=invoice_number,
                storage_zone_id=item.storage_zone_id,
            )
            db.add(batch)
            await db.flush()
            created_batches.append(batch)

        await db.commit()
        for b in created_batches:
            await db.refresh(b)
        return [types.Batch.from_pydantic(b) for b in created_batches]
