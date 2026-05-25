import datetime
from decimal import Decimal
from typing import Optional

import strawberry
from sqlalchemy import select
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.database import models
from backend.graphql.types import User


@sp.type(schemas.Shift)
class Shift:
    id: strawberry.auto
    name: strawberry.auto
    start_time: strawberry.auto
    end_time: strawberry.auto
    overnight: strawberry.auto
    tolerance_minutes: strawberry.auto
    break_duration_minutes: strawberry.auto
    pay_multiplier: strawberry.auto
    shift_type: strawberry.auto


@sp.type(schemas.WorkSchedule)
class WorkSchedule:
    id: strawberry.auto
    date: strawberry.auto
    user_id: strawberry.auto
    shift_id: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @strawberry.field
    async def shift(self, info: strawberry.Info) -> Optional["Shift"]:
        if not self.shift_id:
            return None
        db_shift = await info.context["dataloaders"]["shift_by_id"].load(self.shift_id)
        return Shift.from_pydantic(db_shift) if db_shift else None


@strawberry.type
class TemplatePreviewItem:
    date: datetime.date
    shift_id: int | None
    shift_name: str
    day_index: int


@strawberry.type
class ScheduleStat:
    user_id: int
    user_name: str
    assigned_days: int
    work_days_norm: int
    is_complete: bool


@sp.type(schemas.ShiftSwapRequest)
class ShiftSwapRequest:
    id: strawberry.auto
    requestor_id: strawberry.auto
    target_user_id: strawberry.auto
    requestor_schedule_id: strawberry.auto
    target_schedule_id: strawberry.auto
    status: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def requestor(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.requestor_id)

    @strawberry.field
    async def target_user(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.target_user_id)

    @strawberry.field
    async def requestor_schedule(self, info: strawberry.Info) -> WorkSchedule:
        db = info.context["db"]
        res = await db.get(models.WorkSchedule, self.requestor_schedule_id)
        return WorkSchedule.from_pydantic(res)

    @strawberry.field
    async def target_schedule(self, info: strawberry.Info) -> WorkSchedule:
        db = info.context["db"]
        res = await db.get(models.WorkSchedule, self.target_schedule_id)
        return WorkSchedule.from_pydantic(res)


@sp.type(schemas.ScheduleTemplateItem)
class ScheduleTemplateItem:
    id: strawberry.auto
    day_index: strawberry.auto
    shift_id: strawberry.auto

    @strawberry.field
    async def shift(self, info: strawberry.Info) -> Shift | None:
        if not self.shift_id:
            return None
        db = info.context["db"]
        from backend.database.models import Shift as DbShift
        res = await db.get(DbShift, self.shift_id)
        return Shift.from_pydantic(res) if res else None


@sp.type(schemas.ScheduleTemplate)
class ScheduleTemplate:
    id: strawberry.auto
    company_id: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto
    created_at: strawberry.auto

    @strawberry.field
    async def items(self, info: strawberry.Info) -> list[ScheduleTemplateItem]:
        db = info.context["db"]
        from backend.database.models import ScheduleTemplateItem as DbItem
        stmt = select(DbItem).where(DbItem.template_id == self.id).order_by(DbItem.day_index)
        res = await db.execute(stmt)
        items = res.scalars().all()
        return [ScheduleTemplateItem.from_pydantic(i) for i in items]


__all__ = [
    "ScheduleStat",
    "ScheduleTemplate",
    "ScheduleTemplateItem",
    "Shift",
    "ShiftSwapRequest",
    "TemplatePreviewItem",
    "WorkSchedule",
]
