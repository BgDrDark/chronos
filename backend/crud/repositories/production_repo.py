from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Batch,
    PriceHistory,
    ProductionOrder,
    ProductionRecord,
    ProductionScrapLog,
    ProductionTask,
    Recipe,
    Workstation,
)

from .base import BaseRepository


class ProductionRepository(BaseRepository):
    """Repository за производство"""

    model = ProductionOrder

    # --- Existing methods ---

    async def get_active_orders(
        self,
        db: AsyncSession,
        company_id: int | None = None,
    ) -> list[ProductionOrder]:
        """Връща активните производствени поръчки"""
        query = select(ProductionOrder).where(
            ProductionOrder.status.in_(["pending", "in_progress"]),
        )

        if company_id:
            query = query.where(ProductionOrder.company_id == company_id)

        result = await db.execute(query.order_by(ProductionOrder.scheduled_date))
        return list(result.scalars().all())

    async def get_recipes(
        self,
        db: AsyncSession,
        company_id: int | None = None,
        category: str | None = None,
        is_active: bool = True,
    ) -> list[Recipe]:
        """Връща рецепти"""
        query = select(Recipe).where(Recipe.is_active == is_active)

        if company_id:
            query = query.where(Recipe.company_id == company_id)
        if category:
            query = query.where(Recipe.category == category)

        result = await db.execute(query.order_by(Recipe.name))
        return list(result.scalars().all())

    async def get_recipe_by_id(self, db: AsyncSession, recipe_id: int) -> Recipe | None:
        """Връща рецепта с съставки"""
        result = await db.execute(
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients)),
        )
        return result.scalar_one_or_none()

    async def get_batches(
        self,
        db: AsyncSession,
        recipe_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Batch]:
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
        company_id: int | None = None,
    ) -> list[Workstation]:
        """Връща работни станции"""
        query = select(Workstation)
        if company_id:
            query = query.where(Workstation.company_id == company_id)
        result = await db.execute(query.order_by(Workstation.name))
        return list(result.scalars().all())

    # --- Recipe methods ---

    async def create_recipe(self, db: AsyncSession, **kwargs) -> Recipe:
        """Създава рецепта"""
        instance = Recipe(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_recipe(self, db: AsyncSession, id: int, **kwargs) -> Recipe | None:
        """Обновява рецепта"""
        instance = await self.get_recipe_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_recipe(self, db: AsyncSession, id: int) -> bool:
        """Изтрива рецепта"""
        instance = await self.get_recipe_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_recipes_by_category(
        self,
        db: AsyncSession,
        company_id: int,
        category: str,
    ) -> list[Recipe]:
        """Връща рецепти по категория"""
        query = select(Recipe).where(
            Recipe.company_id == company_id,
            Recipe.category == category,
            Recipe.is_active,
        )
        result = await db.execute(query.order_by(Recipe.name))
        return list(result.scalars().all())

    async def get_all_recipes(
        self,
        db: AsyncSession,
        company_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Recipe]:
        """Връща всички рецепти с опционални филтри"""
        query = select(Recipe)
        if company_id is not None:
            query = query.where(Recipe.company_id == company_id)
        if is_active is not None:
            query = query.where(Recipe.is_active == is_active)
        result = await db.execute(query.order_by(Recipe.name))
        return list(result.scalars().all())

    # --- ProductionOrder methods ---

    async def create_production_order(self, db: AsyncSession, **kwargs) -> ProductionOrder:
        """Създава производствена поръчка"""
        instance = ProductionOrder(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_production_order(self, db: AsyncSession, id: int, **kwargs) -> ProductionOrder | None:
        """Обновява производствена поръчка"""
        instance = await self.get_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_production_order(self, db: AsyncSession, id: int) -> bool:
        """Изтрива производствена поръчка"""
        instance = await self.get_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_production_order_by_id(self, db: AsyncSession, id: int) -> ProductionOrder | None:
        """Връща производствена поръчка с релации"""
        result = await db.execute(
            select(ProductionOrder)
            .where(ProductionOrder.id == id)
            .options(
                selectinload(ProductionOrder.recipe),
                selectinload(ProductionOrder.tasks),
            ),
        )
        return result.scalar_one_or_none()

    async def get_orders_by_status(
        self,
        db: AsyncSession,
        company_id: int,
        status: str | None,
    ) -> list[ProductionOrder]:
        """Връща поръчки по статус"""
        query = select(ProductionOrder).where(
            ProductionOrder.company_id == company_id,
            ProductionOrder.status == status,
        )
        result = await db.execute(query.order_by(ProductionOrder.due_date))
        return list(result.scalars().all())

    async def get_orders_by_date_range(
        self,
        db: AsyncSession,
        company_id: int,
        start: datetime,
        end: datetime,
    ) -> list[ProductionOrder]:
        """Връща поръчки в диапазон от дати"""
        query = select(ProductionOrder).where(
            ProductionOrder.company_id == company_id,
            ProductionOrder.due_date.between(start, end),
        )
        result = await db.execute(query.order_by(ProductionOrder.due_date))
        return list(result.scalars().all())

    # --- ProductionTask methods ---

    async def create_task(self, db: AsyncSession, **kwargs) -> ProductionTask:
        """Създава производствена задача"""
        instance = ProductionTask(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_task(self, db: AsyncSession, id: int, **kwargs) -> ProductionTask | None:
        """Обновява производствена задача"""
        instance = await self.get_task_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_task_by_id(self, db: AsyncSession, id: int) -> ProductionTask | None:
        """Връща задача с работна станция и потребител"""
        result = await db.execute(
            select(ProductionTask)
            .where(ProductionTask.id == id)
            .options(
                selectinload(ProductionTask.workstation),
                selectinload(ProductionTask.assigned_user),
            ),
        )
        return result.scalar_one_or_none()

    async def get_tasks_by_order(self, db: AsyncSession, order_id: int) -> list[ProductionTask]:
        """Връща задачи по поръчка"""
        result = await db.execute(
            select(ProductionTask)
            .where(ProductionTask.order_id == order_id)
            .order_by(ProductionTask.id),
        )
        return list(result.scalars().all())

    async def get_tasks_by_workstation(self, db: AsyncSession, workstation_id: int) -> list[ProductionTask]:
        """Връща задачи по работна станция"""
        result = await db.execute(
            select(ProductionTask)
            .where(ProductionTask.workstation_id == workstation_id)
            .order_by(ProductionTask.id),
        )
        return list(result.scalars().all())

    async def get_tasks_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        status: str | None = None,
    ) -> list[ProductionTask]:
        """Връща задачи по потребител"""
        query = select(ProductionTask).where(ProductionTask.assigned_user_id == user_id)
        if status:
            query = query.where(ProductionTask.status == status)
        result = await db.execute(query.order_by(ProductionTask.id))
        return list(result.scalars().all())

    # --- Workstation methods ---

    async def create_workstation(self, db: AsyncSession, **kwargs) -> Workstation:
        """Създава работна станция"""
        instance = Workstation(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_workstation(self, db: AsyncSession, id: int, **kwargs) -> Workstation | None:
        """Обновява работна станция"""
        instance = await self.get_workstation_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_workstation_by_id(self, db: AsyncSession, id: int) -> Workstation | None:
        """Връща работна станция по ID"""
        result = await db.execute(
            select(Workstation).where(Workstation.id == id),
        )
        return result.scalar_one_or_none()

    # --- ProductionRecord methods ---

    async def create_production_record(self, db: AsyncSession, **kwargs) -> ProductionRecord:
        """Създава запис за производство"""
        instance = ProductionRecord(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_records_by_order(self, db: AsyncSession, order_id: int) -> list[ProductionRecord]:
        """Връща записи по поръчка"""
        result = await db.execute(
            select(ProductionRecord)
            .where(ProductionRecord.order_id == order_id)
            .options(
                selectinload(ProductionRecord.ingredients),
                selectinload(ProductionRecord.workers),
            )
            .order_by(ProductionRecord.created_at.desc()),
        )
        return list(result.scalars().all())

    # --- ProductionScrapLog methods ---

    async def create_scrap_log(self, db: AsyncSession, **kwargs) -> ProductionScrapLog:
        """Създава запис за брак"""
        instance = ProductionScrapLog(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_scrap_logs_by_task(self, db: AsyncSession, task_id: int) -> list[ProductionScrapLog]:
        """Връща записи за брак по задача"""
        result = await db.execute(
            select(ProductionScrapLog)
            .where(ProductionScrapLog.task_id == task_id)
            .order_by(ProductionScrapLog.created_at.desc()),
        )
        return list(result.scalars().all())

    # --- PriceHistory methods ---

    async def create_price_history(self, db: AsyncSession, **kwargs) -> PriceHistory:
        """Създава запис за ценова история"""
        instance = PriceHistory(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_price_history_by_recipe(self, db: AsyncSession, recipe_id: int) -> list[PriceHistory]:
        """Връща ценова история по рецепта"""
        result = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.recipe_id == recipe_id)
            .order_by(PriceHistory.changed_at.desc()),
        )
        return list(result.scalars().all())


production_repo = ProductionRepository()
