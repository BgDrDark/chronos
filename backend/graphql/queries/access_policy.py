import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import models
from backend.graphql.types.access_policy import AccessLevel, AccessSchedule


@strawberry.type
class AccessPolicyQuery:
    @strawberry.field
    async def access_levels(self, info: strawberry.Info, company_id: int) -> list[AccessLevel]:
        db = info.context["db"]
        stmt = (
            select(models.AccessLevel)
            .where(models.AccessLevel.company_id == company_id)
            .options(selectinload(models.AccessLevel.assignments))
        )
        res = await db.execute(stmt)
        return [AccessLevel.from_pydantic(level) for level in res.scalars().all()]

    @strawberry.field
    async def access_level(self, info: strawberry.Info, id: int) -> AccessLevel | None:
        db = info.context["db"]
        stmt = (
            select(models.AccessLevel)
            .where(models.AccessLevel.id == id)
            .options(selectinload(models.AccessLevel.assignments))
        )
        res = await db.execute(stmt)
        level = res.scalar_one_or_none()
        return AccessLevel.from_pydantic(level) if level else None

    @strawberry.field
    async def access_schedules(self, info: strawberry.Info, company_id: int) -> list[AccessSchedule]:
        db = info.context["db"]
        stmt = select(models.AccessSchedule).where(models.AccessSchedule.company_id == company_id)
        res = await db.execute(stmt)
        return [AccessSchedule.from_pydantic(s) for s in res.scalars().all()]

    @strawberry.field
    async def access_schedule(self, info: strawberry.Info, id: int) -> AccessSchedule | None:
        db = info.context["db"]
        res = await db.get(models.AccessSchedule, id)
        return AccessSchedule.from_pydantic(res) if res else None
