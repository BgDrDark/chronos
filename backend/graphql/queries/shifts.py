import datetime

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.crud.repositories import time_repo
from backend.exceptions import PermissionDeniedException
from backend.graphql import types


@strawberry.type
class ShiftsQuery:

    @strawberry.field
    async def shifts(self, info: strawberry.Info) -> list[types.Shift]:
        db = info.context["db"]
        current_user = info.context.get("current_user")
        company_id = current_user.company_id if current_user and current_user.role and current_user.role.name != "super_admin" else None
        db_shifts = await time_repo.get_all_shifts(db, company_id=company_id)
        return [types.Shift.from_pydantic(s) for s in db_shifts]

    @strawberry.field
    async def my_schedules(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        info: strawberry.Info,
    ) -> list[types.WorkSchedule]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return []

        from backend.database.models import WorkSchedule

        result = await db.execute(
            select(WorkSchedule)
            .where(WorkSchedule.user_id == current_user.id)
            .where(WorkSchedule.date >= start_date)
            .where(WorkSchedule.date <= end_date)
            .options(selectinload(WorkSchedule.shift)),
        )
        return [types.WorkSchedule.from_pydantic(s) for s in result.scalars().all()]

    @strawberry.field
    async def work_schedules(
        self,
        info: strawberry.Info,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[types.WorkSchedule]:
        db = info.context["db"]
        current_user = info.context["current_user"]

        company_id = None
        if current_user and current_user.role.name != "super_admin":
            company_id = current_user.company_id

        res = await time_repo.get_schedules_by_period(db, start_date, end_date, company_id=company_id)
        return [types.WorkSchedule.from_pydantic(s) for s in res]

    @strawberry.field
    async def my_swap_requests(self, info: strawberry.Info) -> list[types.ShiftSwapRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return []
        res = await time_repo.get_my_swap_requests(db, current_user.id)
        return [types.ShiftSwapRequest.from_pydantic(s) for s in res]

    @strawberry.field
    async def pending_admin_swaps(self, info: strawberry.Info) -> list[types.ShiftSwapRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view swap requests")
        res = await time_repo.get_all_pending_swaps(db)
        return [types.ShiftSwapRequest.from_pydantic(s) for s in res]

    @strawberry.field
    async def schedule_templates(self, info: strawberry.Info) -> list[types.ScheduleTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view schedule templates")
        res = await time_repo.get_schedule_templates(db, company_id=current_user.company_id)
        return [types.ScheduleTemplate.from_pydantic(t) for t in res]

    @strawberry.field
    async def schedule_template(self, info: strawberry.Info, id: int) -> types.ScheduleTemplate | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view schedule template")
        res = await time_repo.get_schedule_template(db, id, company_id=current_user.company_id)
        if res and res.company_id != current_user.company_id:
            return None
        return types.ScheduleTemplate.from_pydantic(res) if res else None

    @strawberry.field
    async def template_preview(
            self,
            template_id: int,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info,
    ) -> list[types.TemplatePreviewItem]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view schedule template")

        preview = await time_repo.get_template_preview(
            db,
            template_id=template_id,
            start_date=start_date,
            end_date=end_date,
        )
        return [types.TemplatePreviewItem(**item) for item in preview]

    @strawberry.field
    async def schedule_stats(
            self,
            month: int,
            year: int,
            info: strawberry.Info,
    ) -> list[types.ScheduleStat]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view schedule stats")

        company_id = current_user.company_id if current_user.role.name != "super_admin" else None
        stats = await time_repo.get_schedule_stats(db, month=month, year=year, company_id=company_id)
        return [types.ScheduleStat(**s) for s in stats]
