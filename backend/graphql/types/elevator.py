from typing import Annotated

import strawberry
from strawberry.experimental import pydantic as sp
from strawberry import auto

import backend.schemas.elevator as schemas


@sp.type(schemas.ElevatorFloor)
class ElevatorFloor:
    id: strawberry.auto
    elevator_group_id: strawberry.auto
    floor_number: strawberry.auto
    name: strawberry.auto
    zone_id: strawberry.auto
    relay_device_id: strawberry.auto
    relay_number: strawberry.auto
    order: strawberry.auto
    is_active: strawberry.auto

    @strawberry.field
    async def zone(self, info: strawberry.Info) -> Annotated["AccessZone", strawberry.lazy("backend.graphql.types.access_control")] | None:  # noqa: F821
        if not self.zone_id:
            return None
        from backend.database.models import AccessZone as DbZone
        db = info.context["db"]
        res = await db.get(DbZone, self.zone_id)
        if not res:
            return None
        from backend.graphql.types.access_control import AccessZone
        return AccessZone.from_pydantic(res)


@sp.type(schemas.ElevatorGroup)
class ElevatorGroup:
    id: strawberry.auto
    name: strawberry.auto
    gateway_id: strawberry.auto
    terminal_id: strawberry.auto
    controller_type: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def floors(self, info: strawberry.Info) -> list[ElevatorFloor]:
        from sqlalchemy import select
        from backend.database.models import ElevatorFloor as DbFloor
        db = info.context["db"]
        stmt = select(DbFloor).where(DbFloor.elevator_group_id == self.id).order_by(DbFloor.order)
        res = await db.execute(stmt)
        return [ElevatorFloor.from_pydantic(f) for f in res.scalars().all()]
