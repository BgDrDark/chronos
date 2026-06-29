import logging

import strawberry
from sqlalchemy import select

from backend.database import models
from backend.exceptions import NotFoundException, ValidationException
from backend.graphql.inputs.access_policy import (
    AccessLevelInput,
    AccessLevelUpdateInput,
    AccessScheduleInput,
    AccessScheduleUpdateInput,
    AssignAccessLevelToUserInput,
    AssignLevelToZoneInput,
)
from backend.graphql.types.access_policy import AccessLevel, AccessLevelZone, AccessSchedule
from backend.graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


@strawberry.type
class AccessPolicyMutation:
    @strawberry.mutation
    async def create_access_level(self, input: AccessLevelInput, company_id: int, info: strawberry.Info) -> AccessLevel:
        db = info.context["db"]
        get_current_user(info)

        level = models.AccessLevel(name=input.name, description=input.description, company_id=company_id, is_active=input.is_active)
        db.add(level)
        await db.commit()
        await db.refresh(level)
        return AccessLevel.from_pydantic(level)

    @strawberry.mutation
    async def update_access_level(self, id: int, input: AccessLevelUpdateInput, info: strawberry.Info) -> AccessLevel:
        db = info.context["db"]
        get_current_user(info)

        level = await db.get(models.AccessLevel, id)
        if not level:
            raise NotFoundException("Нивото на достъп не е намерено")

        if input.name is not None:
            level.name = input.name
        if input.description is not None:
            level.description = input.description
        if input.is_active is not None:
            level.is_active = input.is_active

        await db.commit()
        await db.refresh(level)
        return AccessLevel.from_pydantic(level)

    @strawberry.mutation
    async def delete_access_level(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        level = await db.get(models.AccessLevel, id)
        if not level:
            raise NotFoundException("Нивото на достъп не е намерено")

        await db.delete(level)
        await db.commit()
        return True

    @strawberry.mutation
    async def create_access_schedule(self, input: AccessScheduleInput, company_id: int, info: strawberry.Info) -> AccessSchedule:
        db = info.context["db"]
        get_current_user(info)

        schedule = models.AccessSchedule(
            name=input.name,
            company_id=company_id,
            timezone=input.timezone,
            config=input.config or {},
            holiday_override_auto=input.holiday_override_auto,
            is_active=input.is_active,
        )
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        return AccessSchedule.from_pydantic(schedule)

    @strawberry.mutation
    async def update_access_schedule(self, id: int, input: AccessScheduleUpdateInput, info: strawberry.Info) -> AccessSchedule:
        db = info.context["db"]
        get_current_user(info)

        schedule = await db.get(models.AccessSchedule, id)
        if not schedule:
            raise NotFoundException("Графикът не е намерен")

        if input.name is not None:
            schedule.name = input.name
        if input.timezone is not None:
            schedule.timezone = input.timezone
        if input.config is not None:
            schedule.config = input.config
        if input.holiday_override_auto is not None:
            schedule.holiday_override_auto = input.holiday_override_auto
        if input.is_active is not None:
            schedule.is_active = input.is_active

        await db.commit()
        await db.refresh(schedule)
        return AccessSchedule.from_pydantic(schedule)

    @strawberry.mutation
    async def delete_access_schedule(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        schedule = await db.get(models.AccessSchedule, id)
        if not schedule:
            raise NotFoundException("Графикът не е намерен")

        await db.delete(schedule)
        await db.commit()
        return True

    @strawberry.mutation
    async def assign_level_to_zone(self, input: AssignLevelToZoneInput, info: strawberry.Info) -> AccessLevelZone:
        db = info.context["db"]
        get_current_user(info)

        existing = await db.execute(
            select(models.AccessLevelZone).where(
                models.AccessLevelZone.access_level_id == input.access_level_id,
                models.AccessLevelZone.zone_id == input.zone_id,
            ),
        )
        if existing.scalar_one_or_none():
            raise ValidationException("Тази зона вече е добавена към нивото")

        assignment = models.AccessLevelZone(
            access_level_id=input.access_level_id,
            zone_id=input.zone_id,
            schedule_id=input.schedule_id,
            out_of_hours_behavior=input.out_of_hours_behavior,
            priority=input.priority,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return AccessLevelZone.from_pydantic(assignment)

    @strawberry.mutation
    async def remove_level_from_zone(self, access_level_id: int, zone_id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        result = await db.execute(
            select(models.AccessLevelZone).where(
                models.AccessLevelZone.access_level_id == access_level_id,
                models.AccessLevelZone.zone_id == zone_id,
            ),
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise NotFoundException("Връзката между ниво и зона не е намерена")

        await db.delete(assignment)
        await db.commit()
        return True

    @strawberry.mutation
    async def assign_access_level_to_user(self, input: AssignAccessLevelToUserInput, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        user = await db.get(models.User, input.user_id)
        if not user:
            raise NotFoundException("Потребителят не е намерен")

        if input.access_level_id:
            level = await db.get(models.AccessLevel, input.access_level_id)
            if not level:
                raise NotFoundException("Нивото на достъп не е намерено")

        user.access_level_id = input.access_level_id
        await db.commit()
        return True

    @strawberry.mutation
    async def remove_access_level_from_user(self, user_id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        user = await db.get(models.User, user_id)
        if not user:
            raise NotFoundException("Потребителят не е намерен")

        user.access_level_id = None
        await db.commit()
        return True
