from typing import Annotated

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.database import models


@sp.type(schemas.AccessZone)
class AccessZone:
    id: strawberry.auto
    zone_id: strawberry.auto
    name: strawberry.auto
    level: strawberry.auto
    depends_on: strawberry.auto
    required_hours_start: strawberry.auto
    required_hours_end: strawberry.auto
    anti_passback_enabled: strawberry.auto
    anti_passback_type: strawberry.auto
    anti_passback_timeout: strawberry.auto
    description: strawberry.auto
    is_active: strawberry.auto

    @strawberry.field
    async def authorized_users(self, info: strawberry.Info) -> list[Annotated["User", strawberry.lazy("backend.graphql.types.user")]]:  # noqa: F821
        from backend.graphql.types.user import User
        db = info.context["db"]
        from backend.database.models import AccessZone as DbZone
        stmt = select(DbZone).where(DbZone.id == self.id).options(selectinload(DbZone.authorized_users))
        res = await db.execute(stmt)
        zone = res.scalar_one_or_none()
        return [User.from_pydantic(u) for u in zone.authorized_users] if zone else []


@sp.type(schemas.AccessDoor)
class AccessDoor:
    id: strawberry.auto
    door_id: strawberry.auto
    name: strawberry.auto
    zone_db_id: strawberry.auto
    gateway_id: strawberry.auto
    device_id: strawberry.auto
    relay_number: strawberry.auto
    terminal_id: strawberry.auto
    terminal_mode: strawberry.auto
    description: strawberry.auto
    is_active: strawberry.auto
    is_online: strawberry.auto
    last_check: strawberry.auto

    @strawberry.field
    async def zone(self, info: strawberry.Info) -> AccessZone | None:
        db = info.context["db"]
        res = await db.get(models.AccessZone, self.zone_db_id)
        return AccessZone.from_pydantic(res) if res else None

    @strawberry.field
    async def gateway(self, info: strawberry.Info) -> Annotated["Gateway", strawberry.lazy("backend.graphql.types.hardware")] | None:  # noqa: F821
        from backend.graphql.types.hardware import Gateway
        db = info.context["db"]
        res = await db.get(models.Gateway, self.gateway_id)
        return Gateway.from_pydantic(res) if res else None


@sp.type(schemas.AccessCode)
class AccessCode:
    id: strawberry.auto
    code: strawberry.auto
    code_type: strawberry.auto
    zones: strawberry.auto
    uses_remaining: strawberry.auto
    expires_at: strawberry.auto
    created_at: strawberry.auto
    last_used_at: strawberry.auto
    is_active: strawberry.auto
    gateway_id: strawberry.auto


@sp.type(schemas.AccessLog)
class AccessLog:
    id: strawberry.auto
    timestamp: strawberry.auto
    user_id: strawberry.auto
    user_name: strawberry.auto
    zone_id: strawberry.auto
    zone_name: strawberry.auto
    door_id: strawberry.auto
    door_name: strawberry.auto
    action: strawberry.auto
    result: strawberry.auto
    reason: strawberry.auto
    method: strawberry.auto
    terminal_id: strawberry.auto
    gateway_id: strawberry.auto
