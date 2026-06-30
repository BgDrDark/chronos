import datetime
from decimal import Decimal

import strawberry
from sqlalchemy import Time, desc, select

from backend import crud
from backend.exceptions import PermissionDeniedException
from backend.chronos_graphql import types
from backend.services.payroll_calculator import PayrollCalculator

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class StatsQuery:
    @strawberry.field
    async def user_daily_stats(
        self,
        info: strawberry.Info,
        user_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[types.DailyStat]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("view records")

        calculator = PayrollCalculator(db)

        stats = await calculator.get_daily_stats(user_id, start_date, end_date)

        return [
            types.DailyStat(
                date=s["date"],
                total_worked_hours=s["total_worked_hours"],
                regular_hours=s["regular_hours"],
                overtime_hours=s["overtime_hours"],
                is_work_day=s["is_work_day"],
                shift_name=s["shift_name"],
                actual_arrival=s.get("actual_arrival"),
                actual_departure=s.get("actual_departure"),
            )
            for s in stats
        ]

    @strawberry.field
    async def my_daily_stats(
        self,
        info: strawberry.Info,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[types.DailyStat]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return []

        calculator = PayrollCalculator(db)

        stats = await calculator.get_daily_stats(current_user.id, start_date, end_date)

        return [
            types.DailyStat(
                date=s["date"],
                total_worked_hours=s["total_worked_hours"],
                regular_hours=s["regular_hours"],
                overtime_hours=s["overtime_hours"],
                is_work_day=s["is_work_day"],
                shift_name=s["shift_name"],
                actual_arrival=s.get("actual_arrival"),
                actual_departure=s.get("actual_departure"),
            )
            for s in stats
        ]

    @strawberry.field
    async def weekly_summary(
        self,
        info: strawberry.Info,
        date: datetime.date | None = None,
        user_id: int | None = None,
    ) -> types.WeeklySummary | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None

        target_user_id = current_user.id
        if user_id:
            if current_user.role.name not in ["admin", "super_admin"] and current_user.id != user_id:
                raise PermissionDeniedException.for_action("view weekly summary")
            target_user_id = user_id

        ref_date = date or datetime.datetime.now().date()

        calculator = PayrollCalculator(db)

        config = await crud.get_payroll_config(db, target_user_id)
        daily_hours = config.standard_hours_per_day if config and config.standard_hours_per_day else 8
        target = float(daily_hours * 5)

        summary = await calculator.get_weekly_summary(target_user_id, ref_date, target)

        return types.WeeklySummary(
            start_date=summary["start_date"],
            end_date=summary["end_date"],
            total_regular_hours=Decimal(str(summary["total_regular_hours"])),
            total_overtime_hours=Decimal(str(summary["total_overtime_hours"])),
            target_hours=Decimal(str(summary["target_hours"])),
            debt_hours=Decimal(str(summary["debt_hours"])),
            surplus_hours=Decimal(str(summary["surplus_hours"])),
            status_message=summary["status_message"],
        )

    @strawberry.field
    async def monthly_work_days(
        self,
        info: strawberry.Info,
        year: int,
        month: int,
    ) -> types.MonthlyWorkDays | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None

        res = await crud.get_monthly_work_days(db, year, month)
        if res:
            return types.MonthlyWorkDays.from_pydantic(res)
        return None

    @strawberry.field
    async def management_stats(self, info: strawberry.Info) -> types.ManagementStats:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view management stats")

        from sqlalchemy import func

        from backend.database.models import Payslip, Shift, TimeLog, User, WorkSchedule

        stmt_ot = select(
            func.to_char(Payslip.period_start, "YYYY-MM").label("month"),
            func.sum(Payslip.overtime_amount).label("total_ot"),
        ).group_by("month").order_by("month").limit(12)

        res_ot = await db.execute(stmt_ot)
        overtime_data = [
            types.OvertimeStat(month=row[0], amount=Decimal(str(row[1])))
            for row in res_ot.all()
        ]

        cutoff = datetime.datetime.now() - datetime.timedelta(days=30)

        stmt_late = select(
            User.first_name,
            User.last_name,
            func.count(TimeLog.id).label("late_count"),
        ).join(TimeLog, User.id == TimeLog.user_id).join(
            WorkSchedule, (User.id == WorkSchedule.user_id) & (func.date(TimeLog.start_time) == WorkSchedule.date),
        ).join(
            Shift, WorkSchedule.shift_id == Shift.id,
        ).where(
            TimeLog.start_time > cutoff,
            func.cast(TimeLog.start_time, Time) > Shift.start_time,
        ).group_by(User.id).order_by(desc("late_count")).limit(10)

        res_late = await db.execute(stmt_late)
        lateness_data = [
            types.LatenessStat(user_name=f"{row[0]} {row[1]}", count=row[2])
            for row in res_late.all()
        ]

        return types.ManagementStats(
            overtime_by_month=overtime_data,
            lateness_by_user=lateness_data,
        )
