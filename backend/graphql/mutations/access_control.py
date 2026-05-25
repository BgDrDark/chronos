import logging

import strawberry
from sqlalchemy import select

from backend.exceptions import (
    NotFoundException,
    PermissionDeniedException,
)
from backend.graphql import inputs, types

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class AccessControlMutation:

    @strawberry.mutation
    async def create_access_zone(self, input: inputs.AccessZoneInput, info: strawberry.Info) -> types.AccessZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AccessZone
        new_zone = AccessZone(
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
            company_id=current_user.company_id,
        )
        db.add(new_zone)
        await db.commit()
        await db.refresh(new_zone)
        return types.AccessZone.from_pydantic(new_zone)

    @strawberry.mutation
    async def update_access_zone(self, id: int, input: inputs.AccessZoneInput, info: strawberry.Info) -> types.AccessZone:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AccessZone
        zone = await db.get(AccessZone, id)
        if not zone:
            raise NotFoundException.resource("Zone")

        # Update fields
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
        return types.AccessZone.from_pydantic(zone)

    @strawberry.mutation
    async def delete_access_zone(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AccessZone
        zone = await db.get(AccessZone, id)
        if zone:
            await db.delete(zone)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def create_access_door(self, input: inputs.AccessDoorInput, info: strawberry.Info) -> types.AccessDoor:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AccessDoor
        new_door = AccessDoor(
            door_id=input.door_id,
            name=input.name,
            zone_db_id=input.zone_db_id,
            gateway_id=input.gateway_id,
            device_id=input.device_id,
            relay_number=input.relay_number,
            terminal_id=input.terminal_id,
            description=input.description,
        )
        db.add(new_door)
        await db.commit()
        await db.refresh(new_door)
        return types.AccessDoor.from_pydantic(new_door)

    @strawberry.mutation
    async def delete_access_door(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import AccessDoor
        door = await db.get(AccessDoor, id)
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
        info: strawberry.Info,
    ) -> types.AccessDoor:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from sqlalchemy import update

        from backend.database.models import AccessDoor, Terminal

        door = await db.get(AccessDoor, id)
        if not door:
            raise NotFoundException.resource("Door")

        # 1. Ако задаваме нов терминал на тази врата, първо разкачаме този терминал от ВСИЧКИ други врати
        if terminal_id:
            await db.execute(
                update(AccessDoor)
                .where(AccessDoor.terminal_id == terminal_id)
                .where(AccessDoor.id != id)
                .values(terminal_id=None),
            )

            # Обновяваме режима и на самия терминал за синхрон
            res = await db.execute(select(Terminal).where(Terminal.hardware_uuid == terminal_id))
            terminal = res.scalar_one_or_none()
            if terminal and terminal_mode:
                terminal.mode = terminal_mode

        # 2. Обновяваме вратата
        door.terminal_id = terminal_id
        if terminal_mode is not None:
            door.terminal_mode = terminal_mode

        await db.commit()
        await db.refresh(door)
        return types.AccessDoor.from_pydantic(door)

