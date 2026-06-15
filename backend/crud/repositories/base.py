from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Базов клас за всички repositories"""

    model: type[T] = None

    async def get_by_id(self, db: AsyncSession, id: int) -> T | None:
        """Връща запис по ID"""
        result = await db.execute(
            select(self.model).where(getattr(self.model, "id") == id),
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        filters: dict | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> list[T]:
        """Връща всички записи с pagination"""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            query = query.order_by(col.desc() if order_desc else col.asc())

        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, filters: dict | None = None) -> int:
        """Брой на записите"""
        query = select(func.count(getattr(self.model, "id")))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await db.execute(query)
        return result.scalar() or 0

    async def create(self, db: AsyncSession, **kwargs) -> T:
        """Създава нов запис"""
        instance = self.model(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update(self, db: AsyncSession, id: int, **kwargs) -> T | None:
        """Обновява запис"""
        instance = await self.get_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Изтрива запис"""
        instance = await self.get_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def exists(self, db: AsyncSession, id: int) -> bool:
        """Проверява дали записът съществува"""
        result = await db.execute(
            select(func.count(getattr(self.model, "id"))).where(getattr(self.model, "id") == id),
        )
        return (result.scalar() or 0) > 0

    async def get_one_by(
        self,
        db: AsyncSession,
        **filters,
    ) -> T | None:
        """Връща един запис по филтри"""
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_many_by(
        self,
        db: AsyncSession,
        filters: dict | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> list[T]:
        """Връща много записи по филтри"""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            query = query.order_by(col.desc() if order_desc else col.asc())

        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())
