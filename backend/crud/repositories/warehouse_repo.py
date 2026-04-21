from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.models import Ingredient, StockConsumptionLog, Supplier, StorageZone
from .base import BaseRepository


class WarehouseRepository(BaseRepository):
    """Repository за склад"""
    
    model = Ingredient
    
    async def get_ingredients_low_stock(
        self,
        db: AsyncSession,
        company_id: int,
        threshold: float = 10.0
    ) -> List[Ingredient]:
        """Връща съставки с ниска наличност"""
        result = await db.execute(
            select(Ingredient)
            .where(Ingredient.company_id == company_id)
            .where(Ingredient.quantity <= threshold)
        )
        return list(result.scalars().all())
    
    async def get_suppliers(
        self,
        db: AsyncSession,
        company_id: int
    ) -> List[Supplier]:
        """Връща доставчиците на компанията"""
        result = await db.execute(
            select(Supplier).where(Supplier.company_id == company_id)
        )
        return list(result.scalars().all())
    
    async def get_ingredients_by_supplier(
        self,
        db: AsyncSession,
        supplier_id: int
    ) -> List[Ingredient]:
        """Връща съставки от даден доставчик"""
        result = await db.execute(
            select(Ingredient).where(Ingredient.supplier_id == supplier_id)
        )
        return list(result.scalars().all())
    
    async def get_stock_consumption(
        self,
        db: AsyncSession,
        ingredient_id: int = None,
        batch_id: int = None,
        limit: int = 100
    ) -> List[StockConsumptionLog]:
        """Връща консумация на склад"""
        query = select(StockConsumptionLog)
        
        if ingredient_id:
            query = query.where(StockConsumptionLog.ingredient_id == ingredient_id)
        if batch_id:
            query = query.where(StockConsumptionLog.batch_id == batch_id)
        
        query = query.order_by(StockConsumptionLog.consumed_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_storage_zones(
        self,
        db: AsyncSession,
        company_id: int
    ) -> List[StorageZone]:
        """Връща складови зони"""
        result = await db.execute(
            select(StorageZone).where(StorageZone.company_id == company_id)
        )
        return list(result.scalars().all())


warehouse_repo = WarehouseRepository()