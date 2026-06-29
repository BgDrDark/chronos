from __future__ import annotations

import strawberry
from sqlalchemy import select

from backend.database import models
from backend.graphql.types.elevator import ElevatorFloor, ElevatorGroup


@strawberry.type
class ElevatorQueries:
    @strawberry.field
    async def elevator_groups(self, info: strawberry.Info) -> list[ElevatorGroup]:
        db = info.context["db"]
        stmt = select(models.ElevatorGroup).where(models.ElevatorGroup.is_active == True).order_by(models.ElevatorGroup.name)
        res = await db.execute(stmt)
        return [ElevatorGroup.from_pydantic(g) for g in res.scalars().all()]

    @strawberry.field
    async def elevator_group(self, info: strawberry.Info, id: int) -> ElevatorGroup | None:
        db = info.context["db"]
        res = await db.get(models.ElevatorGroup, id)
        return ElevatorGroup.from_pydantic(res) if res else None

    @strawberry.field
    async def elevator_floors(self, info: strawberry.Info, elevator_group_id: int) -> list[ElevatorFloor]:
        db = info.context["db"]
        stmt = select(models.ElevatorFloor).where(models.ElevatorFloor.elevator_group_id == elevator_group_id).order_by(models.ElevatorFloor.order)
        res = await db.execute(stmt)
        return [ElevatorFloor.from_pydantic(f) for f in res.scalars().all()]
