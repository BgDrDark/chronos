import datetime
import logging
from decimal import Decimal

import strawberry

from backend.auth.module_guard import verify_module_enabled
from backend.crud.repositories import time_repo
from backend.database.transaction_manager import atomic_with_savepoint
from backend.exceptions import (
    AuthenticationException,
    InvalidOperationException,
    NotFoundException,
    PermissionDeniedException,
)
from backend.graphql import inputs, types
from backend.services.shift_swap_service import shift_swap_service

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class ShiftsMutation:

    @strawberry.mutation
    async def create_shift(
            self,
            name: str,
            start_time: datetime.time,
            end_time: datetime.time,
            info: strawberry.Info,
            tolerance_minutes: int | None = 15,
            break_duration_minutes: int | None = 0,
            pay_multiplier: Decimal | None = None,
            shift_type: str | None = None,
            overnight: bool | None = False,
    ) -> types.Shift:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        s = await time_repo.create_shift(
            db, name, start_time, end_time,
            tolerance_minutes=tolerance_minutes,
            break_duration_minutes=break_duration_minutes,
            pay_multiplier=pay_multiplier if pay_multiplier is not None else 1.0,
            shift_type=shift_type if shift_type is not None else "regular",
            company_id=current_user.company_id,
            overnight=overnight,
        )
        await db.commit()
        await db.refresh(s)
        return types.Shift.from_pydantic(s)

    @strawberry.mutation
    async def update_shift(
            self, id: int, name: str, start_time: datetime.time, end_time: datetime.time,
            tolerance_minutes: int | None = None, break_duration_minutes: int | None = None,
            pay_multiplier: Decimal | None = None, shift_type: str | None = None,
            overnight: bool | None = None,
            info: strawberry.Info = None,
    ) -> types.Shift:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        s = await time_repo.update_shift(
            db, shift_id=id, name=name, start_time=start_time, end_time=end_time,
            tolerance_minutes=tolerance_minutes, break_duration_minutes=break_duration_minutes,
            pay_multiplier=pay_multiplier, shift_type=shift_type, overnight=overnight,
        )
        await db.commit()
        await db.refresh(s)
        return types.Shift.from_pydantic(s)

    @strawberry.mutation
    async def delete_shift(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        result = await time_repo.delete_shift(db, id)
        await db.commit()
        return result

    @strawberry.mutation
    async def create_schedule_template(self, name: str, description: str | None,
                                       items: list[inputs.ScheduleTemplateItemInput],
                                       info: strawberry.Info) -> types.ScheduleTemplate:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("shifts", db)

        items_dicts = []
        for item in items:
            items_dicts.append({
                "day_index": item.day_index,
                "shift_id": item.shift_id,
            })
        template = await time_repo.create_schedule_template(db, name, current_user.company_id, description, items_dicts)
        await db.commit()
        await db.refresh(template)
        return types.ScheduleTemplate.from_pydantic(template)

    @strawberry.mutation
    async def delete_schedule_template(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("shifts", db)
        result = await time_repo.delete_schedule_template(db, id, company_id=current_user.company_id)
        if not result:
            raise NotFoundException.resource("ScheduleTemplate", id)
        await db.commit()
        return True

    @strawberry.mutation
    async def update_schedule_template(
            self,
            id: int,
            name: str | None = None,
            description: str | None = None,
            items: list[inputs.ScheduleTemplateItemInput] | None = None,
            info: strawberry.Info = None,
    ) -> types.ScheduleTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("shifts", db)

        template_items = None
        if items is not None:
            template_items = [
                {"day_index": item.day_index, "shift_id": item.shift_id}
                for item in items
            ]

        template = await time_repo.update_schedule_template(
            db,
            template_id=id,
            company_id=current_user.company_id,
            name=name,
            description=description,
            items=template_items,
        )
        await db.commit()
        await db.refresh(template)
        return types.ScheduleTemplate.from_pydantic(template)

    @strawberry.mutation
    async def apply_schedule_template(
            self,
            template_id: int,
            user_ids: list[int],
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info,
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        await verify_module_enabled("shifts", db)

        for user_id in user_ids:
            await time_repo.apply_schedule_template(
                db, template_id, user_id, start_date, end_date, current_user.id,
            )
            async with atomic_with_savepoint(db, f"schedule_applied_{user_id}"):
                pass
        return True

    @strawberry.mutation
    async def delete_work_schedule(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        result = await time_repo.delete_schedule(db, id)
        await db.commit()
        return result

    @strawberry.mutation
    async def bulk_delete_schedules(
            self,
            user_ids: list[int],
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info,
    ) -> int:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        count = await time_repo.bulk_delete_schedules(
            db,
            user_ids=user_ids,
            start_date=start_date,
            end_date=end_date,
            actor_id=current_user.id,
        )
        await db.commit()
        return count

    @strawberry.mutation
    async def set_work_schedule(self, user_id: int, shift_id: int, date: datetime.date,
                                info: strawberry.Info) -> types.WorkSchedule | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        if not shift_id:
            await time_repo.delete_schedule_by_user_date(db, user_id, date)
            await db.commit()
            return None

        res = await time_repo.create_or_update_schedule(db, user_id, shift_id, date)
        await db.commit()
        await db.refresh(res)
        return types.WorkSchedule.from_pydantic(res)

    @strawberry.mutation
    async def bulk_set_schedule(self, user_ids: list[int], shift_id: int, start_date: datetime.date,
                                end_date: datetime.date, days_of_week: list[int], info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        result = await time_repo.create_bulk_schedules(db, user_ids, shift_id, start_date, end_date, days_of_week)
        await db.commit()
        return result

    @strawberry.mutation
    async def copy_schedules_from_month(
            self,
            user_id: int,
            source_month: int,
            source_year: int,
            target_month: int,
            target_year: int,
            info: strawberry.Info,
    ) -> int:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage schedules")

        count = await time_repo.copy_schedules_from_month(
            db,
            user_id=user_id,
            source_month=source_month,
            source_year=source_year,
            target_month=target_month,
            target_year=target_year,
        )
        await db.commit()
        return count

    @strawberry.mutation
    async def respond_to_swap(self, swap_id: int, accept: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        new_status = "accepted" if accept else "rejected"
        service = shift_swap_service(db)
        res = await service.update_status(swap_id, new_status)
        await db.commit()
        await db.refresh(res)
        return types.ShiftSwapRequest.from_pydantic(res)

    @strawberry.mutation
    async def approve_swap(self, swap_id: int, approve: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        new_status = "approved" if approve else "rejected"
        service = shift_swap_service(db)
        async with atomic_with_savepoint(db, "swap_approved"):
            res = await service.update_status(swap_id, new_status, admin_user_id=current_user.id)
        await db.commit()
        await db.refresh(res)
        return types.ShiftSwapRequest.from_pydantic(res)

    @strawberry.mutation
    async def create_swap_request(self, requestor_schedule_id: int, target_user_id: int, target_schedule_id: int,
                                  info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        service = shift_swap_service(db)
        async with atomic_with_savepoint(db, "swap_created"):
            res = await service.create_request(current_user.id, requestor_schedule_id, target_user_id, target_schedule_id)
        await db.commit()
        await db.refresh(res)
        return types.ShiftSwapRequest.from_pydantic(res)
