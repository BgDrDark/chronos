import strawberry
from typing import Optional, List
import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr
from strawberry.experimental.pydantic import input as pydantic_input

# Pydantic models for validation
class UserCreatePydantic(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str = Field(min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    egn: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    iban: Optional[str] = None
    role_id: Optional[int] = None
    
    # New Relation IDs
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    password_force_change: Optional[bool] = False
    
    # Employment Contract
    contract_type: Optional[str] = None
    contract_start_date: Optional[datetime.date] = None
    contract_end_date: Optional[datetime.date] = None
    base_salary: Optional[Decimal] = None
    work_hours_per_week: Optional[int] = None
    probation_months: Optional[int] = None
    salary_calculation_type: Optional[str] = None
    salary_installments_count: Optional[int] = 1
    monthly_advance_amount: Optional[Decimal] = None
    tax_resident: Optional[bool] = None
    insurance_contributor: Optional[bool] = None
    has_income_tax: Optional[bool] = None

class LoginPydantic(BaseModel):
    email: str # Can be email or username
    password: str = Field(min_length=8)

class UpdateUserPydantic(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    egn: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    iban: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    password_force_change: Optional[bool] = None
    
    # Relation IDs
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None

    # Employment Contract
    contract_type: Optional[str] = None
    contract_start_date: Optional[datetime.date] = None
    contract_end_date: Optional[datetime.date] = None
    base_salary: Optional[Decimal] = None
    work_hours_per_week: Optional[int] = None
    salary_calculation_type: Optional[str] = None
    salary_installments_count: Optional[int] = None
    monthly_advance_amount: Optional[Decimal] = None
    tax_resident: Optional[bool] = None
    insurance_contributor: Optional[bool] = None
    has_income_tax: Optional[bool] = None

# Strawberry input types
@pydantic_input(model=UserCreatePydantic)
class UserCreateInput:
    email: strawberry.auto
    username: strawberry.auto
    password: strawberry.auto
    first_name: strawberry.auto
    last_name: strawberry.auto
    phone_number: strawberry.auto
    address: strawberry.auto
    egn: strawberry.auto
    birth_date: strawberry.auto
    iban: strawberry.auto
    role_id: strawberry.auto
    company_id: strawberry.auto
    department_id: strawberry.auto
    position_id: strawberry.auto
    password_force_change: strawberry.auto
    contract_type: strawberry.auto
    contract_start_date: strawberry.auto
    contract_end_date: strawberry.auto
    base_salary: strawberry.auto
    work_hours_per_week: strawberry.auto
    probation_months: strawberry.auto
    salary_calculation_type: strawberry.auto
    salary_installments_count: strawberry.auto
    monthly_advance_amount: strawberry.auto
    tax_resident: strawberry.auto
    insurance_contributor: strawberry.auto
    has_income_tax: strawberry.auto

@strawberry.input
class CompanyCreateInput:
    name: str
    eik: Optional[str] = None
    bulstat: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    mol_name: Optional[str] = None

@strawberry.input
class CompanyUpdateInput:
    id: int
    name: Optional[str] = None
    eik: Optional[str] = None
    bulstat: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    mol_name: Optional[str] = None

@strawberry.input
class SupplierInput:
    name: str
    eik: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company_id: int


@strawberry.input
class UpdateSupplierInput:
    id: int
    name: str
    eik: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@strawberry.input
class StorageZoneInput:
    name: str
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    asset_type: Optional[str] = "KMA"
    zone_type: Optional[str] = "food"
    company_id: int


@strawberry.input
class UpdateStorageZoneInput:
    id: int
    name: str
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    asset_type: Optional[str] = "KMA"
    zone_type: Optional[str] = "food"
    manager_id: Optional[int] = None

@strawberry.input
class DepartmentCreateInput:
    name: str
    company_id: int
    manager_id: Optional[int] = None

@strawberry.input
class DepartmentUpdateInput:
    id: int
    name: Optional[str] = None
    manager_id: Optional[int] = None

@strawberry.input
class PositionCreateInput:
    title: str
    department_id: int

@strawberry.input
class AccessZoneInput:
    zone_id: str
    name: str
    level: int = 1
    depends_on: List[str] = strawberry.field(default_factory=list)
    required_hours_start: str = "00:00"
    required_hours_end: str = "23:59"
    anti_passback_enabled: bool = False
    anti_passback_type: str = "soft"
    anti_passback_timeout: int = 5
    description: Optional[str] = None

@strawberry.input
class AccessDoorInput:
    door_id: str
    name: str
    zone_db_id: int
    gateway_id: int
    device_id: str
    relay_number: int = 1
    terminal_id: Optional[str] = None
    description: Optional[str] = None

@strawberry.input
class AccessCodeInput:
    code: Optional[str] = None
    code_type: str = "one_time"
    zones: List[str] = strawberry.field(default_factory=list)
    uses_remaining: int = 1
    expires_hours: Optional[int] = 24
    gateway_id: Optional[int] = None

@strawberry.input
class LeaveRequestInput:
    start_date: datetime.date
    end_date: datetime.date
    leave_type: str
    reason: Optional[str] = None

@strawberry.input
class UpdateLeaveRequestStatusInput:
    request_id: int
    status: str
    admin_comment: Optional[str] = None
    employer_top_up: Optional[bool] = False

@strawberry.input
class RoleCreateInput:
    name: str
    description: Optional[str] = None

@strawberry.input
class SmtpSettingsInput:
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: str
    use_tls: bool

@pydantic_input(model=LoginPydantic)
class LoginInput:
    email: strawberry.auto
    password: strawberry.auto

@pydantic_input(model=UpdateUserPydantic)
class UpdateUserInput:
    id: strawberry.auto
    email: strawberry.auto
    username: strawberry.auto
    password: strawberry.auto
    first_name: strawberry.auto
    last_name: strawberry.auto
    phone_number: strawberry.auto
    address: strawberry.auto
    egn: strawberry.auto
    birth_date: strawberry.auto
    iban: strawberry.auto
    is_active: strawberry.auto
    role_id: strawberry.auto
    password_force_change: strawberry.auto
    company_id: strawberry.auto
    department_id: strawberry.auto
    position_id: strawberry.auto
    contract_type: strawberry.auto
    contract_start_date: strawberry.auto
    contract_end_date: strawberry.auto
    base_salary: strawberry.auto
    work_hours_per_week: strawberry.auto
    salary_calculation_type: strawberry.auto
    salary_installments_count: strawberry.auto
    monthly_advance_amount: strawberry.auto
    tax_resident: strawberry.auto
    insurance_contributor: strawberry.auto
    has_income_tax: strawberry.auto

@strawberry.input
class ProductionOrderInput:
    recipe_id: int
    quantity: Decimal
    due_date: datetime.datetime
    notes: Optional[str] = None
    company_id: int


@strawberry.input
class QuickSaleInput:
    recipe_id: int
    quantity: Decimal
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    payment_method: str = "В брой"
    price: Optional[Decimal] = None
    notes: Optional[str] = None
    company_id: int


@strawberry.input
class NotificationSettingInput:
    id: Optional[int] = None
    event_type: str
    email_enabled: bool = True
    push_enabled: bool = True
    email_template: Optional[str] = None
    recipients: Optional[str] = None  # JSON string
    interval_minutes: int = 60
    enabled: bool = True
    company_id: int


@pydantic_input
class BonusCreatePydantic(BaseModel):
    user_id: int
    amount: Decimal
    date: datetime.date
    description: Optional[str] = None


@pydantic_input
class MonthlyWorkDaysPydantic(BaseModel):
    year: int
    month: int
    days_count: int


@strawberry.input
class BonusCreateInput:
    user_id: int
    amount: Decimal
    date: datetime.date
    description: Optional[str] = None


@strawberry.input
class MonthlyWorkDaysInput:
    year: int
    month: int
    days_count: int


@pydantic_input
class PasswordSettingsPydantic(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


@strawberry.input
class PasswordSettingsInput:
    current_password: str
    new_password: str


@strawberry.input
class ScheduleTemplateItemInput:
    day_of_week: int
    start_time: str
    end_time: str
    break_minutes: int = 0


@strawberry.input
class StorageZoneInput:
    name: str
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    asset_type: Optional[str] = "KMA"
    zone_type: Optional[str] = "food"
    company_id: int


@strawberry.input
class ScrapTaskInput:
    task_id: int
    quantity: float
    reason: Optional[str] = None


@strawberry.input
class InvoiceItemInput:
    ingredient_id: Optional[int] = None
    batch_id: Optional[int] = None
    name: str
    quantity: Decimal
    unit: str = "br"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")


@strawberry.input
class InvoiceInput:
    type: str  # incoming / outgoing
    document_type: Optional[str] = "ФАКТУРА"
    griff: Optional[str] = "ОРИГИНАЛ"
    description: Optional[str] = None
    date: datetime.date
    supplier_id: Optional[int] = None
    batch_id: Optional[int] = None
    client_name: Optional[str] = None
    client_eik: Optional[str] = None
    client_address: Optional[str] = None
    discount_percent: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("20.0")
    payment_method: Optional[str] = None
    delivery_method: Optional[str] = None
    due_date: Optional[datetime.date] = None
    payment_date: Optional[datetime.date] = None
    status: str = "draft"
    notes: Optional[str] = None
    company_id: int
    items: List[InvoiceItemInput]


@strawberry.input
class CashJournalEntryInput:
    date: datetime.date
    operation_type: str  # income / expense
    amount: Decimal
    description: Optional[str] = None
    reference_type: Optional[str] = None  # invoice / manual / other
    reference_id: Optional[int] = None
    company_id: int


@strawberry.input
class SupplierInput:

    name: str

    eik: Optional[str] = None

    vat_number: Optional[str] = None

    address: Optional[str] = None

    contact_person: Optional[str] = None

    phone: Optional[str] = None

    email: Optional[str] = None

    company_id: int



@strawberry.input

class IngredientInput:

    id: Optional[int] = None

    name: str

    unit: str

    barcode: Optional[str] = None

    baseline_min_stock: Decimal = Decimal("0")

    current_price: Optional[Decimal] = None

    storage_zone_id: Optional[int] = None

    is_perishable: bool = True

    expiry_warning_days: int = 3

    allergens: List[str] = strawberry.field(default_factory=list)

    product_type: str = "raw"

    company_id: int



@strawberry.input

class BatchInput:

    id: Optional[int] = None

    ingredient_id: int

    batch_number: Optional[str] = None

    quantity: Decimal

    expiry_date: datetime.date

    supplier_id: Optional[int] = None

    invoice_number: Optional[str] = None

    invoice_date: Optional[datetime.date] = None

    storage_zone_id: Optional[int] = None



@strawberry.input

class RecipeIngredientInput:

    ingredient_id: int

    quantity_gross: Decimal

    workstation_id: Optional[int] = None



@strawberry.input

class RecipeStepInput:

    workstation_id: int

    name: str

    step_order: int = 0

    estimated_duration_minutes: Optional[int] = None



@strawberry.input

class RecipeSectionInput:

    section_type: str

    name: str

    shelf_life_days: Optional[int] = None

    waste_percentage: Decimal = Decimal("0")

    section_order: int = 0

    ingredients: List[RecipeIngredientInput]

    steps: List[RecipeStepInput]

    brutto_g: Optional[float] = None

    net_g: Optional[float] = None



@strawberry.input

class RecipeInput:

    name: str

    description: Optional[str] = None

    yield_quantity: Decimal = Decimal("1.0")

    yield_unit: str = "br"

    shelf_life_days: int = 7

    shelf_life_frozen_days: int = 30

    default_pieces: int = 12

    production_time_days: int = 1

    standard_quantity: Decimal = Decimal("1.0")

    instructions: Optional[str] = None

    company_id: int

    sections: List[RecipeSectionInput]

    ingredients: List[RecipeIngredientInput] = strawberry.field(default_factory=list)

    steps: List[RecipeStepInput] = strawberry.field(default_factory=list)



@strawberry.input

class ProductionOrderInput:

    recipe_id: int

    quantity: Decimal

    due_date: datetime.datetime

    notes: Optional[str] = None

    company_id: int


@strawberry.input
class CashReceiptInput:
    receipt_number: str
    date: datetime.date
    payment_type: str
    amount: Decimal
    vat_amount: Decimal = Decimal("0")
    items_json: Optional[str] = None
    fiscal_printer_id: Optional[str] = None
    company_id: int


@strawberry.input
class CashReceiptUpdateInput:
    receipt_number: Optional[str] = None
    date: Optional[datetime.date] = None
    payment_type: Optional[str] = None
    amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    items_json: Optional[str] = None
    fiscal_printer_id: Optional[str] = None


@strawberry.input
class BankAccountInput:
    iban: str
    bic: Optional[str] = None
    bank_name: str
    account_type: str = "current"
    is_default: bool = False
    currency: str = "BGN"
    is_active: bool = True
    company_id: int


@strawberry.input
class BankAccountUpdateInput:
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None
    account_type: Optional[str] = None
    is_default: Optional[bool] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


@strawberry.input
class BankTransactionInput:
    bank_account_id: int
    date: datetime.date
    amount: Decimal
    type: str
    description: Optional[str] = None
    reference: Optional[str] = None
    invoice_id: Optional[int] = None
    company_id: int


@strawberry.input
class BankTransactionUpdateInput:
    date: Optional[datetime.date] = None
    amount: Optional[Decimal] = None
    type: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    invoice_id: Optional[int] = None
    matched: Optional[bool] = None


@strawberry.input
class AccountInput:
    code: str
    name: str
    type: str
    parent_id: Optional[int] = None
    company_id: int
    opening_balance: Decimal = Decimal("0")


@strawberry.input
class AccountUpdateInput:
    code: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[int] = None
    opening_balance: Optional[Decimal] = None


@strawberry.input
class AccountingEntryInput:
    date: datetime.date
    entry_number: str
    description: Optional[str] = None
    debit_account_id: int
    credit_account_id: int
    amount: Decimal
    vat_amount: Decimal = Decimal("0")
    invoice_id: Optional[int] = None
    bank_transaction_id: Optional[int] = None
    cash_journal_id: Optional[int] = None
    company_id: int


@strawberry.input
class AccountingEntryUpdateInput:
    date: Optional[datetime.date] = None
    entry_number: Optional[str] = None
    description: Optional[str] = None
    debit_account_id: Optional[int] = None
    credit_account_id: Optional[int] = None
    amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None


@strawberry.input
class VATRegisterInput:
    period_month: int
    period_year: int
    company_id: int
