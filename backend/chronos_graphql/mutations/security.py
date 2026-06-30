import datetime
import logging

import strawberry
from sqlalchemy import select

from backend import schemas
from backend.database import models
from backend.exceptions import (
    NotFoundException,
    ValidationException,
)
from backend.chronos_graphql import inputs, types
from backend.chronos_graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


@strawberry.type
class SecurityMutations:

    @strawberry.mutation
    async def trigger_emergency(self, input: inputs.EmergencyTriggerInput, info: strawberry.Info) -> types.EmergencyEvent:
        db = info.context["db"]
        current_user = get_current_user(info)

        if input.event_type not in ("lockdown", "emergency_unlock", "fire_alarm", "evacuation", "drill"):
            raise ValidationException(detail="Невалиден тип на извънредна ситуация")

        if input.scope == "zone" and not input.zone_id:
            raise ValidationException(detail="При scope='zone' трябва да се зададе zone_id")

        new_event = models.EmergencyEvent(
            event_type=input.event_type,
            scope=input.scope,
            gateway_id=input.gateway_id,
            zone_id=input.zone_id,
            triggered_by=current_user.id,
            notes=input.notes,
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        return types.EmergencyEvent.from_pydantic(schemas.security.EmergencyEvent.model_validate(new_event))

    @strawberry.mutation
    async def resolve_emergency(self, id: int, info: strawberry.Info) -> types.EmergencyEvent:
        db = info.context["db"]
        current_user = get_current_user(info)

        event = await db.get(models.EmergencyEvent, id)
        if not event:
            raise NotFoundException.resource("EmergencyEvent")

        if not event.is_active:
            raise ValidationException(detail="Събитието вече е разрешено")

        event.is_active = False
        event.resolved_at = datetime.datetime.now()
        event.resolved_by = current_user.id
        await db.commit()
        await db.refresh(event)
        return types.EmergencyEvent.from_pydantic(schemas.security.EmergencyEvent.model_validate(event))

    @strawberry.mutation
    async def update_zone_emergency_settings(
        self,
        id: int,
        info: strawberry.Info,
        is_safe_zone: bool | None = None,
        lockdown_behavior: str | None = None,
        emergency_contact: str | None = None,
    ) -> types.AccessZone:
        db = info.context["db"]
        get_current_user(info)

        zone = await db.get(models.AccessZone, id)
        if not zone:
            raise NotFoundException.resource("Zone")

        if lockdown_behavior is not None and lockdown_behavior not in ("lock", "unlock", "safe"):
            raise ValidationException(detail="lockdown_behavior трябва да бъде 'lock', 'unlock' или 'safe'")

        if is_safe_zone is not None:
            zone.is_safe_zone = is_safe_zone
        if lockdown_behavior is not None:
            zone.lockdown_behavior = lockdown_behavior
        if emergency_contact is not None:
            zone.emergency_contact = emergency_contact

        await db.commit()
        await db.refresh(zone)
        return types.AccessZone.from_pydantic(schemas.AccessZone.model_validate(zone))
