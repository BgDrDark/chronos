from datetime import date, datetime, time
from decimal import Decimal

from pydantic import field_validator

from backend.schemas.base import CustomBaseModel


class ShiftBase(CustomBaseModel):
    name: str
    start_time: time
    end_time: time
    overnight: bool = False
    tolerance_minutes: int = 0
    break_duration_minutes: int = 0
    pay_multiplier: Decimal = Decimal("1.0")
    shift_type: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Името на смяната трябва да е между 2 и 100 символа")
        return v

    @field_validator("tolerance_minutes")
    @classmethod
    def validate_tolerance(cls, v):
        if v < 0:
            raise ValueError("Толерансът не може да бъде отрицателен")
        if v > 120:
            raise ValueError("Толерансът не може да надвишава 120 минути")
        return v

    @field_validator("break_duration_minutes")
    @classmethod
    def validate_break_duration(cls, v):
        if v < 0:
            raise ValueError("Продължителността на почивката не може да бъде отрицателна")
        if v > 480:
            raise ValueError("Продължителността на почивката не може да надвишава 480 минути (8 часа)")
        return v

    @field_validator("pay_multiplier")
    @classmethod
    def validate_pay_multiplier(cls, v):
        if v <= 0:
            raise ValueError("Мултипликаторът на заплащане трябва да бъде положителен")
        if v > 10:
            raise ValueError("Мултипликаторът на заплащане не може да надвишава 10")
        return v


class Shift(ShiftBase):
    id: int


class WorkScheduleBase(CustomBaseModel):
    date: date
    user_id: int
    shift_id: int


class WorkSchedule(WorkScheduleBase):
    id: int


class ShiftSwapRequestBase(CustomBaseModel):
    requestor_id: int
    target_user_id: int
    requestor_schedule_id: int
    target_schedule_id: int
    status: str = "pending"
    created_at: datetime
    updated_at: datetime


class ShiftSwapRequest(ShiftSwapRequestBase):
    id: int


class ScheduleTemplateBase(CustomBaseModel):
    company_id: int
    name: str
    description: str | None = None
    created_at: datetime


class ScheduleTemplate(ScheduleTemplateBase):
    id: int


class ScheduleTemplateItemBase(CustomBaseModel):
    day_index: int
    shift_id: int | None = None


class ScheduleTemplateItem(ScheduleTemplateItemBase):
    id: int
