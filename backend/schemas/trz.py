from datetime import date, datetime
from decimal import Decimal

from backend.schemas.base import CustomBaseModel


class NightWorkBonus(CustomBaseModel):
    id: int
    user_id: int
    period_id: int | None = None
    date: date
    hours: Decimal
    hourly_rate: Decimal
    amount: Decimal
    is_paid: bool = False
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class OvertimeWork(CustomBaseModel):
    id: int
    user_id: int
    period_id: int | None = None
    date: date
    hours: Decimal
    hourly_rate: Decimal
    multiplier: Decimal = Decimal("1.5")
    amount: Decimal
    is_paid: bool = False
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BusinessTrip(CustomBaseModel):
    id: int
    user_id: int
    period_id: int | None = None
    department_id: int | None = None
    destination: str
    start_date: date
    end_date: date
    daily_allowance: Decimal = Decimal(0)
    accommodation: Decimal = Decimal(0)
    transport: Decimal = Decimal(0)
    other_expenses: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
    status: str = "pending"
    approved_by_id: int | None = None
    approved_at: datetime | None = None
    approved_notes: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkExperience(CustomBaseModel):
    id: int
    user_id: int
    company_id: int | None = None
    company_name: str
    position: str | None = None
    start_date: date
    end_date: date | None = None
    years: int = 0
    months: int = 0
    class_level: str | None = None
    is_current: bool = False
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
