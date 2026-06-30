import datetime
import logging
from datetime import time as dt_time
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend.crud.repositories import settings_repo
from backend.database.models import (
    NightWorkBonus,
    OvertimeWork,
    PublicHoliday,
    WorkOnHoliday,
)
from backend.chronos_graphql import types
from backend.chronos_graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


async def create_trz_records_on_clock_out(
    db,
    user_id: int,
    clock_in: datetime.datetime,
    clock_out: datetime.datetime,
):
    """Автоматично създава NightWorkBonus, OvertimeWork и WorkOnHoliday записи при clock-out.
    
    Логика:
    1. Ако работата е в нощен период (22:00 - 06:00) -> NightWorkBonus
    2. Ако работеното време е над 8 часа -> OvertimeWork
    3. Ако денят е празничен -> WorkOnHoliday
    """
    # Провери дали автоматизацията е активирана
    auto_night = await settings_repo.get_setting(db, "payroll_auto_night_work")
    auto_overtime = await settings_repo.get_setting(db, "payroll_auto_overtime")
    auto_holiday = await settings_repo.get_setting(db, "payroll_auto_holiday")

    auto_night = auto_night.lower() == "true" if auto_night else False
    auto_overtime = auto_overtime.lower() == "true" if auto_overtime else False
    auto_holiday = auto_holiday.lower() == "true" if auto_holiday else False

    if not (auto_night or auto_overtime or auto_holiday):
        return None  # Автоматизацията е изключена

    # Вземи настройките
    night_supplement_str = await settings_repo.get_setting(db, "payroll_night_hourly_supplement")
    overtime_rate_str = await settings_repo.get_setting(db, "payroll_overtime_rate")
    holiday_rate_str = await settings_repo.get_setting(db, "payroll_holiday_rate")
    night_supplement = Decimal(night_supplement_str) if night_supplement_str else Decimal("0.15")
    overtime_rate = Decimal(overtime_rate_str) if overtime_rate_str else Decimal(50)
    holiday_rate = Decimal(holiday_rate_str) if holiday_rate_str else Decimal(100)

    # Провери за празничен ден
    work_date = clock_in.date()
    result = await db.execute(
        select(PublicHoliday).where(PublicHoliday.date == work_date),
    )
    holiday = result.scalars().first()
    is_holiday = holiday is not None

    # Изчисли работеното време
    duration = clock_out - clock_in
    total_hours = Decimal(str(duration.total_seconds() / 3600))

    # Вземи заплатата на служителя (за опростенение - използваме мин заплата)
    # В реална имплементация - от employment_contract
    min_wage_str = await settings_repo.get_setting(db, "payroll_min_wage")
    hourly_rate = Decimal(min_wage_str) if min_wage_str else Decimal(1213)
    hourly_rate = hourly_rate / Decimal(8)  # Дневна / 8 часа

    created_records = []

    # 1. Нощен труд (22:00 - 06:00)
    if auto_night:
        night_hours = Decimal(0)

        # Провери дали clock-in е в нощен период
        if clock_in.time() >= dt_time(22, 0) or clock_in.time() < dt_time(6, 0):
            # Цялата смяна е нощна
            night_hours = total_hours
        elif clock_out.time() >= dt_time(22, 0):
            # Частично нощна работа
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
                notes="Автоматично създаден при clock-out",
            )
            db.add(night_bonus)
            created_records.append(f"NightWorkBonus: {night_hours}h")

    # 2. Извънреден труд (над 8 часа)
    if auto_overtime and total_hours > Decimal(8):
        overtime_hours = total_hours - Decimal(8)
        base_hourly = hourly_rate
        overtime_amount = overtime_hours * base_hourly * (overtime_rate / Decimal(100))

        overtime = OvertimeWork(
            user_id=user_id,
            date=work_date,
            hours=overtime_hours,
            hourly_rate=base_hourly,
            multiplier=overtime_rate / Decimal(100),
            amount=overtime_amount,
            is_paid=False,
            notes="Автоматично създаден при clock-out",
        )
        db.add(overtime)
        created_records.append(f"OvertimeWork: {overtime_hours}h")

    # 3. Празничен труд
    if auto_holiday and is_holiday:
        base_hourly = hourly_rate
        holiday_amount = total_hours * base_hourly * (holiday_rate / Decimal(100))

        holiday_work = WorkOnHoliday(
            user_id=user_id,
            date=work_date,
            hours=total_hours,
            hourly_rate=base_hourly,
            multiplier=holiday_rate / Decimal(100),
            amount=holiday_amount,
            is_paid=False,
            notes="Автоматично създаден при clock-out",
        )
        db.add(holiday_work)
        created_records.append(f"WorkOnHoliday: {total_hours}h")

    return created_records


@strawberry.type
class TrzMutation:

    @strawberry.mutation
    async def create_night_work_bonus(
        self,
        info: strawberry.Info,
        user_id: int,
        date: datetime.date,
        hours: float,
        hourly_rate: float,
        period_id: int | None = None,
        notes: str | None = None,
    ) -> types.NightWorkBonus:
        db = info.context["db"]
        get_current_user(info)

        from decimal import Decimal

        from backend.database.models import NightWorkBonus

        amount = Decimal(str(hours)) * Decimal(str(hourly_rate)) * Decimal("1.5")

        night_work = NightWorkBonus(
            user_id=user_id,
            period_id=period_id,
            date=date,
            hours=Decimal(str(hours)),
            hourly_rate=Decimal(str(hourly_rate)),
            amount=amount,
            is_paid=False,
            notes=notes,
        )
        db.add(night_work)
        await db.commit()
        await db.refresh(night_work)
        return types.NightWorkBonus.from_pydantic(night_work)

    @strawberry.mutation
    async def create_overtime_work(
        self,
        info: strawberry.Info,
        user_id: int,
        date: datetime.date,
        hours: float,
        hourly_rate: float,
        multiplier: float = 1.5,
        period_id: int | None = None,
        notes: str | None = None,
    ) -> types.OvertimeWork:
        db = info.context["db"]
        get_current_user(info)

        from decimal import Decimal

        from backend.database.models import OvertimeWork

        amount = Decimal(str(hours)) * Decimal(str(hourly_rate)) * Decimal(str(multiplier))

        overtime = OvertimeWork(
            user_id=user_id,
            period_id=period_id,
            date=date,
            hours=Decimal(str(hours)),
            hourly_rate=Decimal(str(hourly_rate)),
            multiplier=Decimal(str(multiplier)),
            amount=amount,
            is_paid=False,
            notes=notes,
        )
        db.add(overtime)
        await db.commit()
        await db.refresh(overtime)
        return types.OvertimeWork.from_pydantic(overtime)

    @strawberry.mutation
    async def create_business_trip(
        self,
        info: strawberry.Info,
        user_id: int,
        destination: str,
        start_date: datetime.date,
        end_date: datetime.date,
        daily_allowance: float = 40.00,
        accommodation: float = 0,
        transport: float = 0,
        other_expenses: float = 0,
        department_id: int | None = None,
        period_id: int | None = None,
        notes: str | None = None,
    ) -> types.BusinessTrip:
        db = info.context["db"]
        get_current_user(info)

        from decimal import Decimal

        from backend.database.models import BusinessTrip

        days = (end_date - start_date).days + 1
        total_amount = Decimal(str(daily_allowance)) * Decimal(str(days)) + \
                      Decimal(str(accommodation)) + Decimal(str(transport)) + Decimal(str(other_expenses))

        trip = BusinessTrip(
            user_id=user_id,
            period_id=period_id,
            department_id=department_id,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            daily_allowance=Decimal(str(daily_allowance)),
            accommodation=Decimal(str(accommodation)),
            transport=Decimal(str(transport)),
            other_expenses=Decimal(str(other_expenses)),
            total_amount=total_amount,
            status="pending",
            notes=notes,
        )
        db.add(trip)
        await db.commit()
        await db.refresh(trip)
        return types.BusinessTrip.from_pydantic(trip)

    @strawberry.mutation
    async def create_work_experience(
        self,
        info: strawberry.Info,
        user_id: int,
        company_name: str,
        start_date: datetime.date,
        end_date: datetime.date | None = None,
        position: str | None = None,
        years: int = 0,
        months: int = 0,
        class_level: str | None = None,
        is_current: bool = False,
        notes: str | None = None,
    ) -> types.WorkExperience:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import WorkExperience

        experience = WorkExperience(
            user_id=user_id,
            company_id=current_user.company_id,
            company_name=company_name,
            position=position,
            start_date=start_date,
            end_date=end_date,
            years=years,
            months=months,
            class_level=class_level,
            is_current=is_current,
            notes=notes,
        )
        db.add(experience)
        await db.commit()
        await db.refresh(experience)
        return types.WorkExperience.from_pydantic(experience)
