import re

from pydantic import field_validator

from backend.schemas.base import CustomBaseModel


class CompanyBase(CustomBaseModel):
    name: str
    eik: str | None = None
    bulstat: str | None = None
    vat_number: str | None = None
    address: str | None = None
    mol_name: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Името на компанията трябва да е между 2 и 200 символа")
        return v

    @field_validator("eik", mode="before")
    @classmethod
    def validate_eik(cls, v):
        if v is None or v == "":
            return None
        v = v.strip()
        if not re.match(r"^\d{9}$", v):
            raise ValueError("ЕИК трябва да съдържа точно 9 цифри")
        return v

    @field_validator("bulstat", mode="before")
    @classmethod
    def validate_bulstat(cls, v):
        if v is None or v == "":
            return None
        v = v.strip()
        if not re.match(r"^\d{9,13}$", v):
            raise ValueError("Булстат трябва да съдържа между 9 и 13 цифри")
        return v

    @field_validator("vat_number", mode="before")
    @classmethod
    def validate_vat_number(cls, v):
        if v is None or v == "":
            return None
        v = v.strip().upper()
        if not re.match(r"^BG\d{9,10}$", v):
            raise ValueError("ДДС номерът трябва да е във формат BG + 9-10 цифри")
        return v

    @field_validator("address", mode="before")
    @classmethod
    def validate_address(cls, v):
        if v is None or v == "":
            return None
        if len(v) > 500:
            raise ValueError("Адресът не може да надвишава 500 символа")
        return v

    @field_validator("mol_name", mode="before")
    @classmethod
    def validate_mol_name(cls, v):
        if v is None or v == "":
            return None
        if len(v) > 200:
            raise ValueError("Името на МОЛ не може да надвишава 200 символа")
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CustomBaseModel):
    name: str | None = None
    eik: str | None = None
    bulstat: str | None = None
    vat_number: str | None = None
    address: str | None = None
    mol_name: str | None = None


class Company(CompanyBase):
    id: int
    default_sales_account_id: int | None = None
    default_expense_account_id: int | None = None
    default_vat_account_id: int | None = None
    default_customer_account_id: int | None = None
    default_supplier_account_id: int | None = None
    default_cash_account_id: int | None = None
    default_bank_account_id: int | None = None


class DepartmentBase(CustomBaseModel):
    name: str
    company_id: int
    manager_id: int | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(CustomBaseModel):
    name: str | None = None
    manager_id: int | None = None


class Department(DepartmentBase):
    id: int


class PositionBase(CustomBaseModel):
    title: str
    department_id: int


class PositionCreate(PositionBase):
    pass


class Position(PositionBase):
    id: int


class GlobalSetting(CustomBaseModel):
    key: str
    value: str
