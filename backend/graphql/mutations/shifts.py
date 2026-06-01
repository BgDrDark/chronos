import datetime
import logging
from datetime import time as dt_time
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend import schemas
from backend.auth.module_guard import verify_module_enabled
from backend.crud.repositories import settings_repo, time_repo
from backend.database.models import (
    NightWorkBonus,
    OvertimeWork,
    PublicHoliday,
    WorkOnHoliday,
)
from backend.database.transaction_manager import (
    atomic_transaction,
    atomic_with_savepoint,
)
from backend.exceptions import (
    AuthenticationException,
    InvalidOperationException,
    NotFoundException,
    ValidationException,
)
from backend.graphql import inputs, types
from backend.graphql.utils.permission_checker import (
    check_company_access,
    get_current_user,
)
from backend.services.payroll_service import payroll_service
from backend.services.time_tracking_service import time_tracking_service

logger = logging.getLogger(__name__)


def _timelog_to_gql(log) -> types.TimeLog:
    return types.TimeLog.from_pydantic(schemas.TimeLog.model_validate(log))


async def create_trz_records_on_clock_out(
    db,
    user_id: int,
    clock_in: datetime.datetime,
    clock_out: datetime.datetime
):
    """
    Автоматично създава NightWorkBonus, OvertimeWork и WorkOnHoliday записи при clock-out.

    Логика:
    1. Ако работата е в нощен период (22:00 - 06:00) -> NightWorkBonus
    2. Ако работеното време е над 8 часа -> OvertimeWork
    3. Ако денят е празничен -> WorkOnHoliday
    """


    auto_night = await settings_repo.get_setting(db, "payroll_auto_night_work")
    auto_overtime = await settings_repo.get_setting(db, "payroll_auto_overtime")
    auto_holiday = await settings_repo.get_setting(db, "payroll_auto_holiday")

    auto_night = auto_night.lower() == "true" if auto_night else False
    auto_overtime = auto_overtime.lower() == "true" if auto_overtime else False
    auto_holiday = auto_holiday.lower() == "true" if auto_holiday else False

    if not (auto_night or auto_overtime or auto_holiday):
        return

    night_supplement_str = await settings_repo.get_setting(db, "payroll_night_hourly_supplement")
    overtime_rate_str = await settings_repo.get_setting(db, "payroll_overtime_rate")
    holiday_rate_str = await settings_repo.get_setting(db, "payroll_holiday_rate")
    night_supplement = Decimal(night_supplement_str) if night_supplement_str else Decimal("0.15")
    overtime_rate = Decimal(overtime_rate_str) if overtime_rate_str else Decimal("50")
    holiday_rate = Decimal(holiday_rate_str) if holiday_rate_str else Decimal("100")

    work_date = clock_in.date()
    result = await db.execute(
        select(PublicHoliday).where(PublicHoliday.date == work_date)
    )
    holiday = result.scalars().first()
    is_holiday = holiday is not None

    duration = clock_out - clock_in
    total_hours = Decimal(str(duration.total_seconds() / 3600))

    min_wage_str = await settings_repo.get_setting(db, "payroll_min_wage")
    hourly_rate = Decimal(min_wage_str) if min_wage_str else Decimal("1213")
    hourly_rate = hourly_rate / Decimal("8")

    created_records = []

    if auto_night:
        night_hours = Decimal("0")

        if clock_in.time() >= dt_time(22, 0) or clock_in.time() < dt_time(6, 0):
            night_hours = total_hours
        elif clock_out.time() >= dt_time(22, 0):
            night_start = datetime.datetime.combine(work_date, dt_time(22, 0))
            if clock_in.time() < dt_time(22, 0):
                night_hours = Decimal(str((clock_out - night_start).total_seconds() / 3600))

        if night_hours > 0:
            night_amount = night_hours * night_supplement
            night_bonus = NightWorkBonus(
                user_id=user_id,
                date=work_date,
                hours=night_hours,
                hourly_rate=night_supplement,
                amount=night_amount,
                is_paid=False,
                notes="Автоматично създаден при clock-out"
            )
            db.add(night_bonus)
            created_records.append(f"NightWorkBonus: {night_hours}h")

    if auto_overtime and total_hours > Decimal("8"):
        overtime_hours = total_hours - Decimal("8")
        base_hourly = hourly_rate
        overtime_amount = overtime_hours * base_hourly * (overtime_rate / Decimal("100"))

        overtime = OvertimeWork(
            user_id=user_id,
            date=work_date,
            hours=overtime_hours,
            hourly_rate=base_hourly,
            multiplier=overtime_rate / Decimal("100"),
            amount=overtime_amount,
            is_paid=False,
            notes="Автоматично създаден при clock-out"
        )
        db.add(overtime)
        created_records.append(f"OvertimeWork: {overtime_hours}h")

    if auto_holiday and is_holiday:
        base_hourly = hourly_rate
        holiday_amount = total_hours * base_hourly * (holiday_rate / Decimal("100"))

        holiday_work = WorkOnHoliday(
            user_id=user_id,
            date=work_date,
            hours=total_hours,
            hourly_rate=base_hourly,
            multiplier=holiday_rate / Decimal("100"),
            amount=holiday_amount,
            is_paid=False,
            notes="Автоматично създаден при clock-out"
        )
        db.add(holiday_work)
        created_records.append(f"WorkOnHoliday: {total_hours}h")

    return created_records


@strawberry.type
class ShiftMutation:
    @strawberry.mutation
    async def clock_in(
            self,
            info: strawberry.Info,
            latitude: float | None = None,
            longitude: float | None = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail="Not authenticated")

        await verify_module_enabled("shifts", db)

        service = time_tracking_service(db)
        log = await service.clock_in(current_user.id, latitude, longitude)
        await db.commit()
        await db.refresh(log)
        return _timelog_to_gql(log)

    @strawberry.mutation
    async def clock_out(
            self,
            info: strawberry.Info,
            notes: str | None = None,
            latitude: float | None = None,
            longitude: float | None = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail="Not authenticated")

        await verify_module_enabled("shifts", db)

        service = time_tracking_service(db)
        active_log = await service.get_active_timelog(current_user.id)

        if not active_log:
            raise InvalidOperationException.cannot_complete("No active time log found")

        log = await service.clock_out(current_user.id, latitude, longitude, notes=notes)

        await create_trz_records_on_clock_out(
            db=db,
            user_id=current_user.id,
            clock_in=active_log.start_time,
            clock_out=log.end_time
        )

        await db.commit()
        await db.refresh(log)

        return _timelog_to_gql(log)

    @strawberry.mutation(name="adminClockIn")
    async def admin_clock_in(
            self,
            user_id: int,
            info: strawberry.Info,
            custom_time: datetime.datetime | None = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = get_current_user(info)

        await check_company_access(db, current_user, "User", user_id)
        await verify_module_enabled("shifts", db)

        service = time_tracking_service(db)
        active_log = await service.get_active_timelog(user_id)
        if active_log:
            raise InvalidOperationException.cannot_complete("User already has an active time log")

        async with atomic_transaction(db):
            log = await service.clock_in(user_id, custom_time=custom_time, skip_geofence=True)
            await db.refresh(log)

        return _timelog_to_gql(log)

    @strawberry.mutation(name="adminClockOut")
    async def admin_clock_out(
            self,
            user_id: int,
            info: strawberry.Info,
            notes: str | None = None,
            custom_time: datetime.datetime | None = None
    ) -> types.TimeLog:
        db = info.context["db"]
        current_user = get_current_user(info)

        await check_company_access(db, current_user, "User", user_id)
        await verify_module_enabled("shifts", db)

        service = time_tracking_service(db)
        active_log = await service.get_active_timelog(user_id)

        if not active_log:
            raise InvalidOperationException.cannot_complete("No active time log found")

        log = await service.clock_out(user_id, custom_time=custom_time, notes=notes, skip_geofence=True)

        await create_trz_records_on_clock_out(
            db=db,
            user_id=user_id,
            clock_in=active_log.start_time,
            clock_out=log.end_time,
        )

        await db.commit()
        await db.refresh(log)

        return _timelog_to_gql(log)

    @strawberry.mutation
    async def create_time_log(
            self,
            user_id: int,
            start_time: datetime.datetime,
            end_time: datetime.datetime | None = None,
            is_manual: bool = False,
            break_duration_minutes: int = 0,
            notes: str | None = None,
            info: strawberry.Info | None = None
    ) -> types.TimeLog:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)

        await check_company_access(db, current_user, "User", user_id)

        if not end_time:
            raise ValidationException(detail="Краен час е задължителен за ръчно въвеждане")

        time_svc = time_tracking_service(db)
        has_overlap = await time_svc.check_time_overlap(user_id, start_time, end_time)
        if has_overlap:
            raise ValidationException(detail="Записът се застъпва с друг запис за този период")

        log = await time_repo.create_manual_time_log(
            db, user_id, start_time, end_time, break_duration_minutes or 0, notes, is_manual=is_manual
        )
        await db.commit()
        await db.refresh(log)
        return _timelog_to_gql(log)

    @strawberry.mutation
    async def update_time_log(
            self, id: int, start_time: datetime.datetime, end_time: datetime.datetime | None = None,
            is_manual: bool = False, break_duration_minutes: int = 0, notes: str | None = None,
            info: strawberry.Info | None = None
    ) -> types.TimeLog:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)

        await check_company_access(db, current_user, "TimeLog", id)

        log = await time_repo.update_time_log(
            db, log_id=id, start_time=start_time, end_time=end_time, is_manual=is_manual, break_duration_minutes=break_duration_minutes, notes=notes
        )
        await db.commit()
        await db.refresh(log)
        return _timelog_to_gql(log)

    @strawberry.mutation
    async def delete_time_log(self, id: int, info: strawberry.Info | None) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "TimeLog", id)
        result = await time_repo.delete_time_log(db, log_id=id)
        await db.commit()
        return result

    @strawberry.mutation
    async def create_manual_time_log(
            self,
            user_id: int,
            start_time: datetime.datetime,
            end_time: datetime.datetime,
            break_duration_minutes: int = 0,
            notes: str | None = None,
            info: strawberry.Info | None = None
    ) -> types.TimeLog:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "User", user_id)

        time_svc = time_tracking_service(db)
        has_overlap = await time_svc.check_time_overlap(user_id, start_time, end_time)
        if has_overlap:
            raise ValidationException(detail="Записът се застъпва с друг запис за този период")

        log = await time_repo.create_manual_time_log(
            db, user_id, start_time, end_time, break_duration_minutes, notes
        )
        async with atomic_with_savepoint(db, "manual_timelog_created"):
            pass
        return _timelog_to_gql(log)

    @strawberry.mutation
    async def set_monthly_work_days(self, input: inputs.MonthlyWorkDaysInput, info: strawberry.Info) -> types.MonthlyWorkDays:
        db = info.context["db"]
        get_current_user(info)
        
        payroll_svc = payroll_service(db)
        res = await payroll_svc.set_monthly_work_days(input.year, input.month, input.days_count)
        return types.MonthlyWorkDays.from_pydantic(schemas.MonthlyWorkDays.model_validate(res))

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
        current_user = get_current_user(info)

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
        return types.Shift.from_pydantic(schemas.Shift.model_validate(s))

    @strawberry.mutation
    async def update_shift(
            self, id: int, name: str, start_time: datetime.time, end_time: datetime.time,
            tolerance_minutes: int | None = None, break_duration_minutes: int | None = None,
            pay_multiplier: Decimal | None = None, shift_type: str | None = None,
            overnight: bool | None = None,
            info: strawberry.Info | None = None
    ) -> types.Shift:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "Shift", id)

        s = await time_repo.update_shift(
            db, shift_id=id, name=name, start_time=start_time, end_time=end_time,
            tolerance_minutes=tolerance_minutes, break_duration_minutes=break_duration_minutes,
            pay_multiplier=pay_multiplier, shift_type=shift_type, overnight=overnight
        )
        await db.commit()
        await db.refresh(s)
        return types.Shift.from_pydantic(schemas.Shift.model_validate(s))

    @strawberry.mutation
    async def delete_shift(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "Shift", id)
        result = await time_repo.delete_shift(db, id)
        await db.commit()
        return result

    @strawberry.mutation
    async def set_work_schedule(self, user_id: int, shift_id: int, date: datetime.date,
                                info: strawberry.Info) -> types.WorkSchedule | None:
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "User", user_id)

        if not shift_id:
            await time_repo.delete_schedule_by_user_date(db, user_id, date)
            await db.commit()
            return None

        res = await time_repo.create_or_update_schedule(db, user_id, shift_id, date)
        await db.commit()
        await db.refresh(res)
        return types.WorkSchedule.from_pydantic(schemas.WorkSchedule.model_validate(res))

    @strawberry.mutation
    async def delete_work_schedule(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "WorkSchedule", id)

        result = await time_repo.delete_schedule(db, id)
        await db.commit()
        return result

    @strawberry.mutation
    async def bulk_set_schedule(self, user_ids: list[int], shift_id: int, start_date: datetime.date,
                                end_date: datetime.date, days_of_week: list[int], info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)
        
        for user_id in user_ids:
            await check_company_access(db, current_user, "User", user_id)

        result = await time_repo.create_bulk_schedules(db, user_ids, shift_id, start_date, end_date, days_of_week)
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
        current_user = get_current_user(info)
        
        for user_id in user_ids:
            await check_company_access(db, current_user, "User", user_id)

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
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "User", user_id)

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
    async def create_schedule_template(self, name: str, description: str | None,
                                       items: list[inputs.ScheduleTemplateItemInput],
                                       info: strawberry.Info) -> types.ScheduleTemplate:
        db = info.context["db"]
        current_user = get_current_user(info)
        
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
        return types.ScheduleTemplate.from_pydantic(schemas.ScheduleTemplate.model_validate(template))

    @strawberry.mutation
    async def update_schedule_template(
            self,
            id: int,
            name: str | None = None,
            description: str | None = None,
            items: list[inputs.ScheduleTemplateItemInput] | None = None,
            info: strawberry.Info | None = None,
    ) -> types.ScheduleTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "ScheduleTemplate", id)
        
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
        return types.ScheduleTemplate.from_pydantic(schemas.ScheduleTemplate.model_validate(template))

    @strawberry.mutation
    async def delete_schedule_template(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)
        await check_company_access(db, current_user, "ScheduleTemplate", id)
        
        await verify_module_enabled("shifts", db)
        result = await time_repo.delete_schedule_template(db, id, company_id=current_user.company_id)
        if not result:
            raise NotFoundException.resource("ScheduleTemplate", id)
        await db.commit()
        return True

    @strawberry.mutation
    async def apply_schedule_template(
            self,
            template_id: int,
            user_ids: list[int],
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)
        
        await check_company_access(db, current_user, "ScheduleTemplate", template_id)
        for user_id in user_ids:
            await check_company_access(db, current_user, "User", user_id)
        
        await verify_module_enabled("shifts", db)

        for user_id in user_ids:
            async with atomic_with_savepoint(db, f"schedule_applied_{user_id}"):
                await time_repo.apply_schedule_template(
                    db, template_id, user_id, start_date, end_date, current_user.id
                )
        return True
