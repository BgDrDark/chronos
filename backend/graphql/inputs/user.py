import datetime
from decimal import Decimal

import strawberry


@strawberry.input
class UserCreateInput:
    email: str | None = None
    username: str | None = None
    password: str
    first_name: str | None = None
    surname: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    egn: str | None = None
    birth_date: datetime.date | None = None
    iban: str | None = None
    role_id: int | None = None
    company_id: int | None = None
    department_id: int | None = None
    position_id: int | None = None
    password_force_change: bool | None = False
    contract_type: str | None = None
    contract_number: str | None = None
    contract_start_date: datetime.date | None = None
    contract_end_date: datetime.date | None = None
    base_salary: Decimal | None = None
    work_hours_per_week: int | None = None
    probation_months: int | None = None
    salary_calculation_type: str | None = None
    salary_installments_count: int | None = 1
    monthly_advance_amount: Decimal | None = None
    tax_resident: bool | None = None
    insurance_contributor: bool | None = None
    has_income_tax: bool | None = None
    payment_day: int | None = 25
    experience_start_date: datetime.date | None = None
    night_work_rate: Decimal | None = Decimal("0.50")
    overtime_rate: Decimal | None = Decimal("1.50")
    holiday_rate: Decimal | None = Decimal("2.00")
    work_class: str | None = None
    dangerous_work: bool | None = False


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.input
class UpdateUserInput:
    id: int
    email: str | None = None
    username: str | None = None
    password: str | None = None
    first_name: str | None = None
    surname: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    egn: str | None = None
    birth_date: datetime.date | None = None
    iban: str | None = None
    is_active: bool | None = None
    role_id: int | None = None
    password_force_change: bool | None = None
    company_id: int | None = None
    department_id: int | None = None
    position_id: int | None = None
    contract_type: str | None = None
    contract_number: str | None = None
    contract_start_date: datetime.date | None = None
    contract_end_date: datetime.date | None = None
    base_salary: Decimal | None = None
    work_hours_per_week: int | None = None
    probation_months: int | None = None
    salary_calculation_type: str | None = None
    salary_installments_count: int | None = None
    monthly_advance_amount: Decimal | None = None
    tax_resident: bool | None = None
    insurance_contributor: bool | None = None
    has_income_tax: bool | None = None
    payment_day: int | None = None
    experience_start_date: datetime.date | None = None
    night_work_rate: float | None = None
    overtime_rate: float | None = None
    holiday_rate: float | None = None
    dangerous_work: bool | None = None
    work_class: str | None = None


@strawberry.input
class PasswordSettingsInput:
    current_password: str
    new_password: str
