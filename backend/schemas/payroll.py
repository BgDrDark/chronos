import re
from datetime import date, datetime
from decimal import Decimal

from pydantic import field_validator

from backend.schemas.base import CustomBaseModel


class Payroll(CustomBaseModel):
    id: int
    hourly_rate: Decimal
    monthly_salary: Decimal | None = None
    overtime_multiplier: Decimal = Decimal(1)
    standard_hours_per_day: int = 8
    currency: str = "BGN"
    annual_leave_days: int = 20
    tax_percent: Decimal = Decimal("10.00")
    health_insurance_percent: Decimal = Decimal("13.78")
    has_tax_deduction: bool = True
    has_health_insurance: bool = True
    user_id: int | None = None
    position_id: int | None = None

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, v):
        if v <= 0:
            raise ValueError("Часовата ставка трябва да бъде положителна")
        if v > 10000:
            raise ValueError("Часовата ставка не може да надвишава 10000")
        return v

    @field_validator("monthly_salary")
    @classmethod
    def validate_monthly_salary(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Месечната заплата не може да бъде отрицателна")
            if v > 1000000:
                raise ValueError("Месечната заплата не може да надвишава 1000000")
        return v

    @field_validator("overtime_multiplier")
    @classmethod
    def validate_overtime_multiplier(cls, v):
        if v < 1:
            raise ValueError("Мултипликаторът за извънреден труд трябва да бъде поне 1")
        if v > 10:
            raise ValueError("Мултипликаторът за извънреден труд не може да надвишава 10")
        return v

    @field_validator("standard_hours_per_day")
    @classmethod
    def validate_standard_hours(cls, v):
        if v < 1 or v > 24:
            raise ValueError("Стандартните часове на ден трябва да са между 1 и 24")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("Валутата трябва да е 3-буквен ISO код (напр. BGN, EUR, USD)")
        return v

    @field_validator("annual_leave_days")
    @classmethod
    def validate_annual_leave(cls, v):
        if v < 0:
            raise ValueError("Дните отпуск не могат да бъдат отрицателни")
        if v > 365:
            raise ValueError("Дните отпуск не могат да надвишават 365")
        return v

    @field_validator("tax_percent")
    @classmethod
    def validate_tax_percent(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Данъчният процент трябва да е между 0 и 100")
        return v

    @field_validator("health_insurance_percent")
    @classmethod
    def validate_health_insurance_percent(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Процентът за здравно осигуряване трябва да е между 0 и 100")
        return v


class Payslip(CustomBaseModel):
    id: int
    user_id: int
    period_start: datetime
    period_end: datetime
    total_regular_hours: Decimal = Decimal(0)
    total_overtime_hours: Decimal = Decimal(0)
    regular_amount: Decimal = Decimal(0)
    overtime_amount: Decimal = Decimal(0)
    bonus_amount: Decimal = Decimal(0)
    night_work_amount: Decimal = Decimal(0)
    trip_amount: Decimal = Decimal(0)
    voucher_amount: Decimal = Decimal(0)
    benefit_amount: Decimal = Decimal(0)
    sick_leave_amount: Decimal = Decimal(0)
    tax_amount: Decimal = Decimal(0)
    insurance_amount: Decimal = Decimal(0)
    sick_days: int = 0
    leave_days: int = 0
    doo_employee: Decimal = Decimal(0)
    doo_employer: Decimal = Decimal(0)
    zo_employee: Decimal = Decimal(0)
    zo_employer: Decimal = Decimal(0)
    dzpo_employee: Decimal = Decimal(0)
    dzpo_employer: Decimal = Decimal(0)
    tzpb_employer: Decimal = Decimal(0)
    gross_salary: Decimal = Decimal(0)
    taxable_base: Decimal = Decimal(0)
    income_tax: Decimal = Decimal(0)
    standard_deduction: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
    payment_status: str = "pending"
    actual_payment_date: datetime | None = None
    payment_method: str = "bank"
    batch_id: int | None = None
    generated_at: datetime


class Bonus(CustomBaseModel):
    id: int
    user_id: int
    amount: Decimal
    date: date
    description: str | None = None


class AdvancePayment(CustomBaseModel):
    id: int
    user_id: int
    amount: Decimal
    payment_date: date
    description: str | None = None
    is_processed: bool = False
    created_at: datetime


class ServiceLoan(CustomBaseModel):
    id: int
    user_id: int
    total_amount: Decimal
    installment_amount: Decimal
    remaining_amount: Decimal
    installments_count: int
    installments_paid: int = 0
    start_date: date
    description: str | None = None
    is_active: bool = True
    created_at: datetime
