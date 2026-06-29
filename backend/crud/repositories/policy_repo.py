from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import AccessLevel, AccessLevelZone, AccessSchedule

from .base import BaseRepository


class AccessPolicyRepository(BaseRepository):
    model = AccessLevel

    async def get_level_with_assignments(self, db: AsyncSession, level_id: int) -> AccessLevel | None:
        result = await db.execute(
            select(AccessLevel)
            .options(selectinload(AccessLevel.assignments))
            .where(AccessLevel.id == level_id),
        )
        return result.scalar_one_or_none()

    async def get_levels_by_company(self, db: AsyncSession, company_id: int) -> list[AccessLevel]:
        result = await db.execute(
            select(AccessLevel)
            .options(selectinload(AccessLevel.assignments))
            .where(AccessLevel.company_id == company_id, AccessLevel.is_active.is_(True)),
        )
        return list(result.scalars().all())

    async def create_zone_assignment(
        self,
        db: AsyncSession,
        access_level_id: int,
        zone_id: int,
        schedule_id: int | None = None,
        out_of_hours_behavior: str = "deny",
        priority: int = 0,
    ) -> AccessLevelZone:
        assignment = AccessLevelZone(
            access_level_id=access_level_id,
            zone_id=zone_id,
            schedule_id=schedule_id,
            out_of_hours_behavior=out_of_hours_behavior,
            priority=priority,
        )
        db.add(assignment)
        await db.flush()
        await db.refresh(assignment)
        return assignment

    async def get_zone_assignment(self, db: AsyncSession, access_level_id: int, zone_id: int) -> AccessLevelZone | None:
        result = await db.execute(
            select(AccessLevelZone).where(
                AccessLevelZone.access_level_id == access_level_id,
                AccessLevelZone.zone_id == zone_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_assignments_by_level(self, db: AsyncSession, access_level_id: int) -> list[AccessLevelZone]:
        result = await db.execute(
            select(AccessLevelZone)
            .options(selectinload(AccessLevelZone.schedule))
            .where(AccessLevelZone.access_level_id == access_level_id),
        )
        return list(result.scalars().all())

    async def delete_zone_assignment(self, db: AsyncSession, access_level_id: int, zone_id: int) -> bool:
        assignment = await self.get_zone_assignment(db, access_level_id, zone_id)
        if assignment:
            await db.delete(assignment)
            await db.flush()
            return True
        return False

    async def get_schedule_by_id(self, db: AsyncSession, schedule_id: int) -> AccessSchedule | None:
        return await self.get_by_id(db, schedule_id) if self.model else None  # noqa

    async def get_schedules_by_company(self, db: AsyncSession, company_id: int) -> list[AccessSchedule]:
        result = await db.execute(
            select(AccessSchedule).where(
                AccessSchedule.company_id == company_id,
                AccessSchedule.is_active.is_(True),
            ),
        )
        return list(result.scalars().all())


policy_repo = AccessPolicyRepository()
