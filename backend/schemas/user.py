import re
from datetime import date, datetime
from decimal import Decimal

from pydantic import EmailStr, field_validator

from backend.schemas.base import CustomBaseModel


class RoleBase(CustomBaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int


class UserBase(CustomBaseModel):
    email: EmailStr | None = None
    username: str | None = None
    first_name: str | None = None
    surname: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    egn: str | None = None
    birth_date: date | None = None
    iban: str | None = None
    job_title: str | None = None
    department: str | None = None
    company: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

    company_id: int | None = None
    department_id: int | None = None
    position_id: int | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if v is not None and (len(v) < 3 or len(v) > 50):
            raise ValueError("Потребителското име трябва да е между 3 и 50 символа")
        return v

    @field_validator("egn", mode="before")
    @classmethod
    def validate_egn(cls, v):
        if v is None or v == "":
            return None
        if not re.match(r"^\d{10}$", v):
            raise ValueError("ЕГН трябва да съдържа точно 10 цифри")
        return v

    @field_validator("iban", mode="before")
    @classmethod
    def validate_iban(cls, v):
        if v is None or v == "":
            return None
        v = v.replace(" ", "").upper()
        if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{4,}$", v):
            raise ValueError("Невалиден IBAN формат")
        return v

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone(cls, v):
        if v is None or v == "":
            return None
        v = v.replace(" ", "").replace("-", "")
        if not re.match(r"^(\+359|0)?\d{9}$", v):
            raise ValueError("Невалиден телефонен номер (очакван формат: +359888123456 или 0888123456)")
        return v


class UserCreate(UserBase):
    password: str
    password_force_change: bool = False
    contract_type: str | None = None
    contract_number: str | None = None
    contract_start_date: date | None = None
    contract_end_date: date | None = None
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
    experience_start_date: date | None = None
    night_work_rate: Decimal | None = Decimal("0.50")
    overtime_rate: Decimal | None = Decimal("1.50")
    holiday_rate: Decimal | None = Decimal("2.00")
    work_class: str | None = None
    dangerous_work: bool | None = False


class UserUpdate(CustomBaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    egn: str | None = None
    birth_date: date | None = None
    iban: str | None = None
    is_active: bool | None = None
    role_id: int | None = None
    password_force_change: bool | None = None
    company_id: int | None = None
    department_id: int | None = None
    position_id: int | None = None
    contract_type: str | None = None
    contract_start_date: date | None = None
    contract_end_date: date | None = None
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
    experience_start_date: date | None = None
    night_work_rate: Decimal | None = None
    overtime_rate: Decimal | None = None
    holiday_rate: Decimal | None = None
    work_class: str | None = None
    dangerous_work: bool | None = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class User(UserBase):
    id: int
    is_active: bool
    role_id: int
    role: Role
    created_at: datetime | None = None
    last_login: datetime | None = None
    qr_token: str | None = None
    password_force_change: bool = False
    profile_picture: str | None = None


class UserSessionBase(CustomBaseModel):
    user_id: int
    ip_address: str | None = None
    user_agent: str | None = None
    device_type: str | None = None
    is_active: bool


class UserSession(UserSessionBase):
    id: int
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
