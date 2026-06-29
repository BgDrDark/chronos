from typing import Annotated

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.database import models
from backend.utils.json_type import JSONScalar


@sp.type(schemas.AccessLevelZone)
class AccessLevelZone:
    id: strawberry.auto
    access_level_id: strawberry.auto
    zone_id: strawberry.auto
    schedule_id: strawberry.auto
    out_of_hours_behavior: strawberry.auto
    priority: strawberry.auto

    @strawberry.field
    async def zone(self, info: strawberry.Info) -> Annotated["AccessZone", strawberry.lazy("backend.graphql.types.access_control")] | None:  # noqa: F821
        from backend.graphql.types.access_control import AccessZone
        db = info.context["db"]
        res = await db.get(models.AccessZone, self.zone_id)
        return AccessZone.from_pydantic(res) if res else None


@sp.type(schemas.AccessSchedule)
class AccessSchedule:
    id: strawberry.auto
    name: strawberry.auto
    company_id: strawberry.auto
    timezone: strawberry.auto
    config: JSONScalar
    holiday_override_auto: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.AccessLevel)
class AccessLevel:
    id: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto
    company_id: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def zone_assignments(
        self, info: strawberry.Info
    ) -> list["AccessLevelZone"]:
        db = info.context["db"]
        stmt = (
            select(models.AccessLevelZone)
            .where(models.AccessLevelZone.access_level_id == self.id)
            .options(selectinload(models.AccessLevelZone.zone))
        )
        res = await db.execute(stmt)
        return [AccessLevelZone.from_pydantic(a) for a in res.scalars().all()]

    @strawberry.field
    async def user_count(self, info: strawberry.Info) -> int:
        db = info.context["db"]
        stmt = select(models.User).where(models.User.access_level_id == self.id)
        res = await db.execute(stmt)
        return len(res.scalars().all())
