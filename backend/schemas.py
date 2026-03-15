from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator, field_validator
import re

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class LoginResponse(Token):
    password_force_change: bool = False

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    egn: Optional[str] = None
    birth_date: Optional[date] = None
    iban: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    
    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == '' or v is None:
            return None
        return v
    
    # Relation IDs
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None and (len(v) < 3 or len(v) > 50):
            raise ValueError('Потребителското име трябва да е между 3 и 50 символа')
        return v

    @field_validator('egn')
    @classmethod
    def validate_egn(cls, v):
        if v is not None:
            # БГ ЕГН: 10 цифри
            if not re.match(r'^\d{10}$', v):
                raise ValueError('ЕГН трябва да съдържа точно 10 цифри')
        return v

    @field_validator('iban')
    @classmethod
    def validate_iban(cls, v):
        if v is not None:
            # IBAN формат - премахваме разстояния и правим главни букви
            v = v.replace(' ', '').upper()
            if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{4,}$', v):
                raise ValueError('Невалиден IBAN формат')
            v = v  # Връщаме форматирания IBAN
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            # Български телефонен номер - премахваме разстояния и тирета
            v = v.replace(' ', '').replace('-', '')
            if not re.match(r'^\+?359?\d{9}$', v):
                raise ValueError('Невалиден телефонен номер (очакван формат: +359888123456 или 0888123456)')
        return v

class UserCreate(UserBase):
    password: str
    password_force_change: bool = False
    
    # Employment Contract
    contract_type: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    base_salary: Optional[Decimal] = None
    work_hours_per_week: Optional[int] = None
    probation_months: Optional[int] = None
    salary_calculation_type: Optional[str] = None
    salary_installments_count: Optional[int] = 1
    monthly_advance_amount: Optional[Decimal] = None
    tax_resident: Optional[bool] = None
    insurance_contributor: Optional[bool] = None
    has_income_tax: Optional[bool] = None

    # ТРЗ разширение
    payment_day: Optional[int] = 25
    experience_start_date: Optional[date] = None
    night_work_rate: Optional[Decimal] = Decimal("0.50")
    overtime_rate: Optional[Decimal] = Decimal("1.50")
    holiday_rate: Optional[Decimal] = Decimal("2.00")
    work_class: Optional[str] = None
    dangerous_work: Optional[bool] = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    egn: Optional[str] = None
    birth_date: Optional[date] = None
    iban: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    password_force_change: Optional[bool] = None
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None

    # Employment Contract
    contract_type: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    base_salary: Optional[Decimal] = None
    work_hours_per_week: Optional[int] = None
    probation_months: Optional[int] = None
    salary_calculation_type: Optional[str] = None
    salary_installments_count: Optional[int] = None
    monthly_advance_amount: Optional[Decimal] = None
    tax_resident: Optional[bool] = None
    insurance_contributor: Optional[bool] = None
    has_income_tax: Optional[bool] = None

    # TRZ extension
    payment_day: Optional[int] = None
    experience_start_date: Optional[date] = None
    night_work_rate: Optional[Decimal] = None
    overtime_rate: Optional[Decimal] = None
    holiday_rate: Optional[Decimal] = None
    work_class: Optional[str] = None
    dangerous_work: Optional[bool] = None

    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == '' or v is None:
            return None
        return v # For payroll linkage

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    id: int
    is_active: bool
    role_id: int
    role: Role
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    qr_token: Optional[str] = None
    password_force_change: bool = False
    profile_picture: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CompanyBase(BaseModel):
    name: str
    eik: Optional[str] = None
    bulstat: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    mol_name: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    eik: Optional[str] = None
    bulstat: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    mol_name: Optional[str] = None

class Company(CompanyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DepartmentBase(BaseModel):
    name: str
    company_id: int
    manager_id: Optional[int] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    manager_id: Optional[int] = None

class Department(DepartmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PositionBase(BaseModel):
    title: str
    department_id: int

class PositionCreate(PositionBase):
    pass

class Position(PositionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class GlobalSetting(BaseModel):
    key: str
    value: str

class ModuleBase(BaseModel):
    code: str
    is_enabled: bool
    name: str
    description: Optional[str] = None

class ModuleUpdate(BaseModel):
    is_enabled: bool

class Module(ModuleBase):
    id: int
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PasswordSettings(BaseModel):
    min_length: int
    max_length: int
    require_upper: bool
    require_lower: bool
    require_digit: bool
    require_special: bool

class PasswordSettingsUpdate(PasswordSettings):
    pass

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class WorkplaceLocationBase(BaseModel):
    company_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    radius_meters: int

class WorkplaceLocationCreate(WorkplaceLocationBase):

    pass



class RecipeBase(BaseModel):



    name: str



    description: Optional[str] = None



    yield_quantity: Decimal



    yield_unit: str = "br"

    shelf_life_days: int = 7  # Срок на годност на готовия продукт в дни



    production_time_days: int = 1



    company_id: int







class RecipeCreate(RecipeBase):



    pass







class Recipe(RecipeBase):



    id: int



    model_config = ConfigDict(from_attributes=True)







class ProductionOrderBase(BaseModel):



    recipe_id: int



    quantity: Decimal



    due_date: datetime



    status: str = "pending"



    notes: Optional[str] = None



    company_id: int







class ProductionOrderCreate(ProductionOrderBase):



    pass







class ProductionOrderUpdate(BaseModel):



    status: Optional[str] = None



    notes: Optional[str] = None



    completed_by: Optional[int] = None







class ProductionOrder(ProductionOrderBase):



    id: int



    created_at: datetime



    completed_at: Optional[datetime] = None



    completed_by: Optional[int] = None

    confirmed_at: Optional[datetime] = None

    confirmed_by: Optional[int] = None



    model_config = ConfigDict(from_attributes=True)







class SmtpSettings(BaseModel):

    smtp_server: str

    smtp_port: int

    smtp_username: str

    smtp_password: str

    sender_email: str

    use_tls: bool



class StorageZoneBase(BaseModel):

    name: str

    temp_min: Optional[Decimal] = None

    temp_max: Optional[Decimal] = None

    description: Optional[str] = None

    company_id: int

    is_active: bool = True

    asset_type: str = "KMA" # ДМА/КМА

    zone_type: str = "food" # хранителен/нехранителен



class StorageZoneCreate(StorageZoneBase):
    pass


class StorageZone(StorageZoneBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class IngredientBase(BaseModel):
    name: str
    unit: str = "kg"
    barcode: Optional[str] = None
    baseline_min_stock: Decimal = Decimal("0")
    current_price: Optional[Decimal] = None
    storage_zone_id: Optional[int] = None
    is_perishable: bool = True
    expiry_warning_days: int = 3
    allergens: List[Any] = []
    company_id: int


class IngredientCreate(IngredientBase):
    pass


class Ingredient(IngredientBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class BatchBase(BaseModel):



    ingredient_id: int



    batch_number: Optional[str] = None



    quantity: Decimal



    unit_value: Optional[Decimal] = None



    production_date: Optional[date] = None



    expiry_date: date



    price_no_vat: Optional[Decimal] = None



    vat_percent: Optional[Decimal] = 20.0



    price_with_vat: Optional[Decimal] = None



    supplier_id: Optional[int] = None



    is_stock_receipt: bool = False



    invoice_number: Optional[str] = None



    invoice_date: Optional[date] = None







class BatchCreate(BatchBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def validate_production_info(self):



        # Rule 9: Both batch_number and production_date must be present if one is



        if (self.batch_number or self.production_date) and not (self.batch_number and self.production_date):



            raise ValueError("Партиден номер и дата на производство трябва да бъдат въведени заедно.")



        return self







    # Pydantic v2 validator



    @model_validator(mode='after')



    def check_production_fields(self) -> 'BatchCreate':



        if (self.batch_number or self.production_date) and not (self.batch_number and self.production_date):



            raise ValueError("Партиден номер и дата на производство трябва да бъдат въведени заедно.")



        return self







class Batch(BatchBase):







    id: int







    received_by: Optional[int] = None







    status: str







    received_at: datetime







    model_config = ConfigDict(from_attributes=True)












