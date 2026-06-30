from typing import Annotated

import strawberry
from strawberry.experimental import pydantic as sp

import backend.schemas.security as schemas


@sp.type(schemas.EmergencyEvent)
class EmergencyEvent:
    id: strawberry.auto
    event_type: strawberry.auto
    scope: strawberry.auto
    gateway_id: strawberry.auto
    zone_id: strawberry.auto
    triggered_by: strawberry.auto
    triggered_at: strawberry.auto
    resolved_at: strawberry.auto
    resolved_by: strawberry.auto
    is_active: strawberry.auto
    notes: strawberry.auto

    @strawberry.field
    async def zone(self, info: strawberry.Info) -> Annotated["AccessZone", strawberry.lazy("backend.chronos_graphql.types.access_control")] | None:  # noqa: F821
        if not self.zone_id:
            return None
        from backend.database.models import AccessZone as DbZone
        db = info.context["db"]
        res = await db.get(DbZone, self.zone_id)
        if not res:
            return None
        from backend.chronos_graphql.types.access_control import AccessZone
        return AccessZone.from_pydantic(res)
