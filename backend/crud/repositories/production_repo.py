from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.models import ProductionOrder, Recipe, Batch, ProductionTask, Workstation
from .base import BaseRepository


class ProductionRepository(BaseRepository):
    """Repository за производство"""
    
    model = ProductionOrder
    
    async def get_active_orders(
        self,
        db: AsyncSession,
        company_id: int = None
    ) -> List[ProductionOrder]:
        """Връща активните производствени поръчки"""
        query = select(ProductionOrder).where(
            ProductionOrder.status.in_(["pending", "in_progress"])
        )
        
        if company_id:
            query = query.where(ProductionOrder.company_id == company_id)
        
        result = await db.execute(query.order_by(ProductionOrder.scheduled_date))
        return list(result.scalars().all())
    
    async def get_recipes(
        self,
        db: AsyncSession,
        company_id: int = None,
        category: str = None,
        is_active: bool = True
    ) -> List[Recipe]:
        """Връща рецепти"""
        query = select(Recipe).where(Recipe.is_active == is_active)
        
        if company_id:
            query = query.where(Recipe.company_id == company_id)
        if category:
            query = query.where(Recipe.category == category)
        
        result = await db.execute(query.order_by(Recipe.name))
        return list(result.scalars().all())
    
    async def get_recipe_by_id(self, db: AsyncSession, recipe_id: int) -> Optional[Recipe]:
        """Връща рецепта с съставки"""
        result = await db.execute(
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients))
        )
        return result.scalar_one_or_none()
    
    async def get_batches(
        self,
        db: AsyncSession,
        recipe_id: int = None,
        status: str = None,
        limit: int = 100
    ) -> List[Batch]:
        """Връща партиди"""
        query = select(Batch)
        
        if recipe_id:
            query = query.where(Batch.recipe_id == recipe_id)
        if status:
            query = query.where(Batch.status == status)
        
        query = query.order_by(Batch.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_workstations(
        self,
        db: AsyncSession,
        company_id: int = None
    ) -> List[Workstation]:
        """Връща работни станции"""
        query = select(Workstation)
        if company_id:
            query = query.where(Workstation.company_id == company_id)
        result = await db.execute(query.order_by(Workstation.name))
        return list(result.scalars().all())


production_repo = ProductionRepository()