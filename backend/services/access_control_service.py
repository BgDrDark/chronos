from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    AccessDoor,
    AccessLevel,
    AccessLevelZone,
    AccessSchedule,
    AccessZone,
    Gateway,
    User,
    WorkSchedule,
    user_access_zones,
)
from backend.services.schedule_service import schedule_service


class AccessControlService:

    async def resolve_user_zones(self, user_id: int, db: AsyncSession) -> list[int]:
        user = await db.get(User, user_id)
        if not user:
            return []

        zone_ids: set[int] = set()

        if user.access_level_id:
            result = await db.execute(
                select(AccessLevelZone.zone_id).where(
                    AccessLevelZone.access_level_id == user.access_level_id,
                ),
            )
            zone_ids.update(row[0] for row in result.all())

        result = await db.execute(
            select(user_access_zones.c.zone_id).where(
                user_access_zones.c.user_id == user_id,
            ),
        )
        direct_zone_ids = {row[0] for row in result.all()}
        zone_ids.update(direct_zone_ids)

        return sorted(zone_ids)

    async def resolve_user_assignments(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> list[AccessLevelZone]:
        user = await db.get(User, user_id)
        if not user or not user.access_level_id:
            return []

        result = await db.execute(
            select(AccessLevelZone)
            .options(selectinload(AccessLevelZone.schedule))
            .where(AccessLevelZone.access_level_id == user.access_level_id),
        )
        return list(result.scalars().all())

    async def build_gateway_config(
        self,
        company_id: int,
        db: AsyncSession,
    ) -> dict:
        zones_result = await db.execute(
            select(AccessZone).where(
                AccessZone.company_id == company_id,
                AccessZone.is_active.is_(True),
            ),
        )
        zones = list(zones_result.scalars().all())

        doors_result = await db.execute(
            select(AccessDoor).where(
                AccessDoor.company_id == company_id,
                AccessDoor.is_active.is_(True),
            ),
        )
        doors = list(doors_result.scalars().all())

        levels_result = await db.execute(
            select(AccessLevel)
            .options(selectinload(AccessLevel.assignments))
            .where(AccessLevel.company_id == company_id, AccessLevel.is_active.is_(True)),
        )
        levels = list(levels_result.scalars().all())

        schedules_result = await db.execute(
            select(AccessSchedule).where(
                AccessSchedule.company_id == company_id,
                AccessSchedule.is_active.is_(True),
            ),
        )
        schedules = list(schedules_result.scalars().all())

        users_result = await db.execute(
            select(User)
            .options(selectinload(User.accessible_zones))
            .where(User.company_id == company_id, User.is_active.is_(True)),
        )
        users = list(users_result.scalars().all())

        holidays_result = await db.execute(
            select(WorkSchedule)
            .options(selectinload(WorkSchedule.shift))
            .where(WorkSchedule.user_id.in_([u.id for u in users])) if users else select().where(False),
        )
        work_schedules = list(holidays_result.scalars().all()) if users else []

        return {
            "zones": [
                {"id": z.id, "name": z.name, "description": z.description}
                for z in zones
            ],
            "doors": [
                {
                    "id": d.id,
                    "name": d.name,
                    "zone_id": d.zone_id,
                    "relay": d.relay_number,
                    "terminal_uuid": d.terminal_id,
                }
                for d in doors
            ],
            "access_levels": [
                {
                    "id": lv.id,
                    "name": lv.name,
                    "description": lv.description,
                    "zone_assignments": [
                        {
                            "zone_id": a.zone_id,
                            "schedule_id": a.schedule_id,
                            "out_of_hours_behavior": a.out_of_hours_behavior,
                            "priority": a.priority,
                        }
                        for a in (lv.assignments or [])
                    ],
                }
                for lv in levels
            ],
            "schedules": [
                {
                    "id": s.id,
                    "name": s.name,
                    "timezone": s.timezone,
                    "config": s.config,
                    "holiday_override_auto": s.holiday_override_auto,
                }
                for s in schedules
            ],
            "authorized_users": [
                {
                    "external_id": u.external_id,
                    "access_level_id": u.access_level_id,
                    "zone_overrides": [z.id for z in (u.accessible_zones or [])],
                }
                for u in users if u.external_id is not None
            ],
        }

    async def check_user_zone_access(
        self,
        user_id: int,
        zone_id: int,
        db: AsyncSession,
        now=None,
    ) -> tuple[bool, str, str]:
        from datetime import datetime, timezone

        now = now or datetime.now(timezone.utc)

        user = await db.get(User, user_id)
        if not user:
            return False, "user_not_found", "Потребителят не е намерен"

        if not user.access_level_id:
            return False, "no_access_level", "Няма зададено ниво на достъп"

        direct_result = await db.execute(
            select(user_access_zones.c.zone_id).where(
                user_access_zones.c.user_id == user_id,
                user_access_zones.c.zone_id == zone_id,
            ),
        )
        if direct_result.first():
            return True, "granted", "Достъпът е разрешен"

        result = await db.execute(
            select(AccessLevelZone)
            .options(selectinload(AccessLevelZone.schedule))
            .where(
                AccessLevelZone.access_level_id == user.access_level_id,
                AccessLevelZone.zone_id == zone_id,
            ),
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return False, "zone_not_in_level", "Зоната не е включена в нивото на достъп"

        if not assignment.schedule_id:
            return True, "granted", "Достъпът е разрешен"

        allowed, reason = await schedule_service.is_access_allowed(
            assignment.schedule_id,
            now,
            db,
        )
        if allowed:
            return True, "granted", "Достъпът е разрешен"

        if assignment.out_of_hours_behavior == "allow_with_log":
            return True, "granted_out_of_hours", f"Извънработно време: {reason}"

        return False, "denied_by_schedule", reason


access_control_service = AccessControlService()
