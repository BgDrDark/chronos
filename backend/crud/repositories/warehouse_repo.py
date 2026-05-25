from datetime import date, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Batch,
    Ingredient,
    InventoryItem,
    InventorySession,
    StockConsumptionLog,
    StorageZone,
    Supplier,
)

from .base import BaseRepository


class WarehouseRepository(BaseRepository):
    """Repository за склад"""

    model = Ingredient

    # ────────────────────────── Ingredient ──────────────────────────

    async def create_ingredient(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> Ingredient:
        instance = Ingredient(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_ingredient(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> Ingredient | None:
        instance = await db.execute(
            select(Ingredient).where(Ingredient.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_ingredient(
        self,
        db: AsyncSession,
        id: int,
    ) -> bool:
        instance = await db.execute(
            select(Ingredient).where(Ingredient.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_ingredient_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> Ingredient | None:
        result = await db.execute(
            select(Ingredient)
            .options(selectinload(Ingredient.storage_zone))
            .where(Ingredient.id == id),
        )
        return result.scalar_one_or_none()

    async def get_ingredients_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        search: str | None = None,
    ) -> list[Ingredient]:
        query = select(Ingredient).where(Ingredient.company_id == company_id)
        if search:
            query = query.where(
                Ingredient.name.ilike(f"%{search}%"),
            )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_ingredients_low_stock(
        self,
        db: AsyncSession,
        company_id: int,
        threshold: float = 10.0,
    ) -> list[Ingredient]:
        result = await db.execute(
            select(Ingredient)
            .where(Ingredient.company_id == company_id)
            .where(Ingredient.quantity <= threshold),
        )
        return list(result.scalars().all())

    async def search_ingredients(
        self,
        db: AsyncSession,
        company_id: int,
        search_term: str,
    ) -> list[Ingredient]:
        result = await db.execute(
            select(Ingredient)
            .where(Ingredient.company_id == company_id)
            .where(
                or_(
                    Ingredient.name.ilike(f"%{search_term}%"),
                    Ingredient.barcode.ilike(f"%{search_term}%"),
                ),
            ),
        )
        return list(result.scalars().all())

    # ────────────────────────── Supplier ──────────────────────────

    async def create_supplier(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> Supplier:
        instance = Supplier(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_supplier(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> Supplier | None:
        instance = await db.execute(
            select(Supplier).where(Supplier.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_supplier(
        self,
        db: AsyncSession,
        id: int,
    ) -> bool:
        instance = await db.execute(
            select(Supplier).where(Supplier.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_supplier_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> Supplier | None:
        result = await db.execute(
            select(Supplier).where(Supplier.id == id),
        )
        return result.scalar_one_or_none()

    async def get_suppliers(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[Supplier]:
        result = await db.execute(
            select(Supplier).where(Supplier.company_id == company_id),
        )
        return list(result.scalars().all())

    async def search_suppliers(
        self,
        db: AsyncSession,
        company_id: int,
        search_term: str,
    ) -> list[Supplier]:
        result = await db.execute(
            select(Supplier)
            .where(Supplier.company_id == company_id)
            .where(
                or_(
                    Supplier.name.ilike(f"%{search_term}%"),
                    Supplier.eik.ilike(f"%{search_term}%"),
                    Supplier.contact_person.ilike(f"%{search_term}%"),
                ),
            ),
        )
        return list(result.scalars().all())

    # ────────────────────────── Batch ──────────────────────────

    async def create_batch(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> Batch:
        instance = Batch(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_batch(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> Batch | None:
        instance = await db.execute(
            select(Batch).where(Batch.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def update_batch_status(
        self,
        db: AsyncSession,
        id: int,
        status: str,
    ) -> Batch | None:
        instance = await db.execute(
            select(Batch).where(Batch.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            instance.status = status
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_batch(
        self,
        db: AsyncSession,
        id: int,
    ) -> bool:
        instance = await db.execute(
            select(Batch).where(Batch.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_batch_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> Batch | None:
        result = await db.execute(
            select(Batch)
            .options(
                selectinload(Batch.ingredient),
                selectinload(Batch.supplier),
            )
            .where(Batch.id == id),
        )
        return result.scalar_one_or_none()

    async def get_batches_by_ingredient(
        self,
        db: AsyncSession,
        ingredient_id: int,
        status: str | None = None,
    ) -> list[Batch]:
        query = select(Batch).where(Batch.ingredient_id == ingredient_id)
        if status:
            query = query.where(Batch.status == status)
        query = query.order_by(Batch.expiry_date.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_batches_by_supplier(
        self,
        db: AsyncSession,
        supplier_id: int,
    ) -> list[Batch]:
        result = await db.execute(
            select(Batch)
            .where(Batch.supplier_id == supplier_id)
            .order_by(Batch.received_at.desc()),
        )
        return list(result.scalars().all())

    async def get_batches_by_storage_zone(
        self,
        db: AsyncSession,
        storage_zone_id: int,
    ) -> list[Batch]:
        result = await db.execute(
            select(Batch)
            .where(Batch.storage_zone_id == storage_zone_id)
            .order_by(Batch.expiry_date.asc()),
        )
        return list(result.scalars().all())

    async def get_expiring_batches(
        self,
        db: AsyncSession,
        company_id: int,
        days: int = 7,
    ) -> list[Batch]:
        cutoff = date.today() + timedelta(days=days)
        result = await db.execute(
            select(Batch)
            .join(Ingredient, Batch.ingredient_id == Ingredient.id)
            .where(Ingredient.company_id == company_id)
            .where(Batch.expiry_date <= cutoff)
            .where(Batch.status == "active")
            .order_by(Batch.expiry_date.asc()),
        )
        return list(result.scalars().all())

    # ────────────────────────── StorageZone ──────────────────────────

    async def create_storage_zone(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> StorageZone:
        instance = StorageZone(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_storage_zone(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> StorageZone | None:
        instance = await db.execute(
            select(StorageZone).where(StorageZone.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_storage_zone(
        self,
        db: AsyncSession,
        id: int,
    ) -> bool:
        instance = await db.execute(
            select(StorageZone).where(StorageZone.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_storage_zone_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> StorageZone | None:
        result = await db.execute(
            select(StorageZone).where(StorageZone.id == id),
        )
        return result.scalar_one_or_none()

    async def get_storage_zones(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[StorageZone]:
        result = await db.execute(
            select(StorageZone).where(StorageZone.company_id == company_id),
        )
        return list(result.scalars().all())

    # ────────────────────────── StockConsumptionLog ──────────────────────────

    async def create_consumption_log(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> StockConsumptionLog:
        instance = StockConsumptionLog(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_stock_consumption(
        self,
        db: AsyncSession,
        ingredient_id: int = None,
        batch_id: int = None,
        limit: int = 100,
    ) -> list[StockConsumptionLog]:
        query = select(StockConsumptionLog)

        if ingredient_id:
            query = query.where(StockConsumptionLog.ingredient_id == ingredient_id)
        if batch_id:
            query = query.where(StockConsumptionLog.batch_id == batch_id)

        query = query.order_by(StockConsumptionLog.consumed_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_consumption_logs(
        self,
        db: AsyncSession,
        ingredient_id: int | None = None,
        batch_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[StockConsumptionLog]:
        query = select(StockConsumptionLog)

        if ingredient_id:
            query = query.where(StockConsumptionLog.ingredient_id == ingredient_id)
        if batch_id:
            query = query.where(StockConsumptionLog.batch_id == batch_id)
        if start_date:
            query = query.where(StockConsumptionLog.created_at >= start_date)
        if end_date:
            query = query.where(StockConsumptionLog.created_at <= end_date)

        query = query.order_by(StockConsumptionLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ────────────────────────── InventorySession ──────────────────────────

    async def create_inventory_session(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> InventorySession:
        instance = InventorySession(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_inventory_session(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> InventorySession | None:
        instance = await db.execute(
            select(InventorySession).where(InventorySession.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def complete_inventory_session(
        self,
        db: AsyncSession,
        id: int,
    ) -> InventorySession | None:
        instance = await db.execute(
            select(InventorySession).where(InventorySession.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            instance.status = "completed"
            instance.completed_at = datetime.now()
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_inventory_session_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> InventorySession | None:
        result = await db.execute(
            select(InventorySession)
            .options(selectinload(InventorySession.items))
            .where(InventorySession.id == id),
        )
        return result.scalar_one_or_none()

    async def get_inventory_sessions_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        status: str | None = None,
    ) -> list[InventorySession]:
        query = select(InventorySession).where(
            InventorySession.company_id == company_id,
        )
        if status:
            query = query.where(InventorySession.status == status)
        query = query.order_by(InventorySession.started_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    # ────────────────────────── InventoryItem ──────────────────────────

    async def create_inventory_item(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> InventoryItem:
        instance = InventoryItem(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_inventory_item(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> InventoryItem | None:
        instance = await db.execute(
            select(InventoryItem).where(InventoryItem.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_inventory_items_by_session(
        self,
        db: AsyncSession,
        session_id: int,
    ) -> list[InventoryItem]:
        result = await db.execute(
            select(InventoryItem)
            .where(InventoryItem.session_id == session_id),
        )
        return list(result.scalars().all())


warehouse_repo = WarehouseRepository()
