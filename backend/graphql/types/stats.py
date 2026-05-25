import datetime
from decimal import Decimal

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas


@strawberry.type
class DailyStat:
    date: datetime.date
    total_worked_hours: float
    regular_hours: float
    overtime_hours: float
    is_work_day: bool
    shift_name: str | None
    actual_arrival: datetime.datetime | None
    actual_departure: datetime.datetime | None


@strawberry.type
class WeeklySummary:
    start_date: datetime.date
    end_date: datetime.date
    total_regular_hours: Decimal
    total_overtime_hours: Decimal
    target_hours: Decimal
    debt_hours: Decimal
    surplus_hours: Decimal
    status_message: str


@sp.type(schemas.MonthlyWorkDays)
class MonthlyWorkDays:
    id: strawberry.auto
    year: strawberry.auto
    month: strawberry.auto
    days_count: strawberry.auto


@strawberry.type
class OvertimeStat:
    month: str
    amount: Decimal


@strawberry.type
class LatenessStat:
    user_name: str
    count: int


@strawberry.type
class ManagementStats:
    overtime_by_month: list[OvertimeStat]
    lateness_by_user: list[LatenessStat]
