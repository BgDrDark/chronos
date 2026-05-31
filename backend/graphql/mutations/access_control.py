import datetime
import logging
import secrets

import strawberry
from sqlalchemy import delete, insert, select, update

from backend import schemas
from backend.database import models
from backend.exceptions import (
    NotFoundException,
    ValidationException,
)
from backend.graphql import inputs, types
from backend.graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


@strawberry.type
class AccessControlMutation:
    @strawberry.mutation
    async def create_access_code(
        self, input: inputs.AccessCodeInput, info: strawberry.Info
    ) -> types.AccessCode:
        db = info.context["db"]
        current_user = get_current_user(info)

        code = input.code or secrets.token_hex(4).upper()
        expires_at = None
        if input.expires_hours:
            expires_at = datetime.datetime.now() + datetime.timedelta(
                hours=input.expires_hours
            )

        new_code = models.AccessCode(
            code=code,
            code_type=input.code_type,
            zones=input.zones,
            uses_remaining=input.uses_remaining,
            expires_at=expires_at,
            created_by=current_user.id,
            gateway_id=input.gateway_id,
        )
        db.add(new_code)
        await db.commit()
        await db.refresh(new_code)
        return types.AccessCode.from_pydantic(schemas.AccessCode.model_validate(new_code))

    @strawberry.mutation
    async def delete_access_code(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        code = await db.get(models.AccessCode, id)
        if code:
            await db.delete(code)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def revoke_access_code(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        code = await db.get(models.AccessCode, id)
        if code:
            code.is_active = False
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def assign_zone_to_user(
        self, user_id: int, zone_id: int, info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        get_current_user(info)

        stmt = select(models.user_access_zones).where(
            models.user_access_zones.c.user_id == user_id,
            models.user_access_zones.c.zone_id == zone_id,
        )
        res = await db.execute(stmt)
        if res.first():
            return True

        await db.execute(
            insert(models.user_access_zones).values(user_id=user_id, zone_id=zone_id)
        )
        await db.commit()
        return True

    @strawberry.mutation
    async def remove_zone_from_user(
        self, user_id: int, zone_id: int, info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        get_current_user(info)

        await db.execute(
            delete(models.user_access_zones).where(
                models.user_access_zones.c.user_id == user_id,
                models.user_access_zones.c.zone_id == zone_id,
            )
        )
        await db.commit()
        return True

    @strawberry.mutation
    async def open_door(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        door = await db.get(models.AccessDoor, id)
        if not door:
            raise NotFoundException.record("Door")

        gw = await db.get(models.Gateway, door.gateway_id)
        if not gw or not gw.ip_address:
            raise ValidationException(detail="Gateway offline or no IP")

        import aiohttp

        url = f"http://{gw.ip_address}:{gw.web_port}/access/doors/{door.door_id}/trigger"
        try:
            async with aiohttp.ClientSession() as session, session.post(
                url, timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    return True
                try:
                    data = await r.json()
                    msg = data.get("message", "Gateway error")
                except Exception:
                    msg = f"Gateway returned {r.status}"
                raise ValidationException(detail=msg)
        except Exception as e:
            raise ValidationException(detail=f"Connection error: {str(e)}") from e
        except Exception as e:
            raise ValidationException(detail=f"Connection error: {str(e)}") from e

    @strawberry.mutation
    async def create_access_door(self, input: inputs.AccessDoorInput, info: strawberry.Info) -> types.AccessDoor:
        db = info.context["db"]
        get_current_user(info)
        
        new_door = models.AccessDoor(
            door_id=input.door_id,
            name=input.name,
            zone_db_id=input.zone_db_id,
            gateway_id=input.gateway_id,
            device_id=input.device_id,
            relay_number=input.relay_number,
            terminal_id=input.terminal_id,
            description=input.description
        )
        db.add(new_door)
        await db.commit()
        await db.refresh(new_door)
        return types.AccessDoor.from_pydantic(schemas.AccessDoor.model_validate(new_door))

    @strawberry.mutation
    async def delete_access_door(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)
        
        door = await db.get(models.AccessDoor, id)
        if door:
            await db.delete(door)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def update_door_terminal(
        self,
        id: int,
        terminal_id: str | None,
        terminal_mode: str | None,
        info: strawberry.Info
    ) -> types.AccessDoor:
        db = info.context["db"]
        get_current_user(info)
        
        door = await db.get(models.AccessDoor, id)
        if not door:
            raise NotFoundException.resource("Door")
        
        if terminal_id:
            await db.execute(
                update(models.AccessDoor)
                .where(models.AccessDoor.terminal_id == terminal_id)
                .where(models.AccessDoor.id != id)
                .values(terminal_id=None)
            )
            
            res = await db.execute(select(models.Terminal).where(models.Terminal.hardware_uuid == terminal_id))
            terminal = res.scalar_one_or_none()
            if terminal and terminal_mode:
                terminal.mode = terminal_mode
        
        door.terminal_id = terminal_id
        if terminal_mode is not None:
            door.terminal_mode = terminal_mode
        
        await db.commit()
        await db.refresh(door)
        return types.AccessDoor.from_pydantic(schemas.AccessDoor.model_validate(door))

    @strawberry.mutation
    async def create_access_zone(self, input: inputs.AccessZoneInput, info: strawberry.Info) -> types.AccessZone:
        db = info.context["db"]
        current_user = get_current_user(info)
        
        new_zone = models.AccessZone(
            zone_id=input.zone_id,
            name=input.name,
            level=input.level,
            depends_on=input.depends_on,
            required_hours_start=input.required_hours_start,
            required_hours_end=input.required_hours_end,
            anti_passback_enabled=input.anti_passback_enabled,
            anti_passback_type=input.anti_passback_type,
            anti_passback_timeout=input.anti_passback_timeout,
            description=input.description,
            company_id=current_user.company_id
        )
        db.add(new_zone)
        await db.commit()
        await db.refresh(new_zone)
        return types.AccessZone.from_pydantic(schemas.AccessZone.model_validate(new_zone))

    @strawberry.mutation
    async def delete_access_zone(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)
        
        zone = await db.get(models.AccessZone, id)
        if zone:
            await db.delete(zone)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def update_access_zone(self, id: int, input: inputs.AccessZoneInput, info: strawberry.Info) -> types.AccessZone:
        db = info.context["db"]
        get_current_user(info)
            
        zone = await db.get(models.AccessZone, id)
        if not zone:
            raise NotFoundException.resource("Zone")
            
        zone.zone_id = input.zone_id
        zone.name = input.name
        zone.level = input.level
        zone.depends_on = input.depends_on
        zone.required_hours_start = input.required_hours_start
        zone.required_hours_end = input.required_hours_end
        zone.anti_passback_enabled = input.anti_passback_enabled
        zone.anti_passback_type = input.anti_passback_type
        zone.anti_passback_timeout = input.anti_passback_timeout
        zone.description = input.description
        
        await db.commit()
        await db.refresh(zone)
        return types.AccessZone.from_pydantic(schemas.AccessZone.model_validate(zone))
