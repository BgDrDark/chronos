import strawberry
from typing import Optional, List
import datetime
from decimal import Decimal


@strawberry.input
class UserCreateInput:
    email: Optional[str] = None
    username: Optional[str] = None
    password: str
    first_name: Optional[str] = None
    surname: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    egn: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    iban: Optional[str] = None
    role_id: Optional[int] = None
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    password_force_change: Optional[bool] = False
    contract_type: Optional[str] = None
    contract_number: Optional[str] = None
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
    payment_day: Optional[int] = 25
    experience_start_date: Optional[datetime.date] = None
    night_work_rate: Optional[Decimal] = Decimal("0.50")
    overtime_rate: Optional[Decimal] = Decimal("1.50")
    holiday_rate: Optional[Decimal] = Decimal("2.00")
    work_class: Optional[str] = None
    dangerous_work: Optional[bool] = False


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.input
class UpdateUserInput:
    id: int
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    surname: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    egn: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    iban: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    password_force_change: Optional[bool] = None
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    contract_type: Optional[str] = None
    contract_number: Optional[str] = None
    contract_start_date: Optional[datetime.date] = None
    contract_end_date: Optional[datetime.date] = None
    base_salary: Optional[Decimal] = None
    work_hours_per_week: Optional[int] = None
    probation_months: Optional[int] = None
    salary_calculation_type: Optional[str] = None
    salary_installments_count: Optional[int] = None
    monthly_advance_amount: Optional[Decimal] = None
    tax_resident: Optional[bool] = None
    insurance_contributor: Optional[bool] = None
    has_income_tax: Optional[bool] = None
    payment_day: Optional[int] = None
    experience_start_date: Optional[datetime.date] = None
    night_work_rate: Optional[float] = None
    overtime_rate: Optional[float] = None
    holiday_rate: Optional[float] = None
    dangerous_work: Optional[bool] = None
    work_class: Optional[str] = None


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
    default_sales_account_id: Optional[int] = None
    default_expense_account_id: Optional[int] = None
    default_vat_account_id: Optional[int] = None
    default_customer_account_id: Optional[int] = None
    default_supplier_account_id: Optional[int] = None
    default_cash_account_id: Optional[int] = None
    default_bank_account_id: Optional[int] = None


@strawberry.input
class CompanyAccountingSettingsInput:
    company_id: int
    default_sales_account_id: Optional[int] = None
    default_expense_account_id: Optional[int] = None
    default_vat_account_id: Optional[int] = None
    default_customer_account_id: Optional[int] = None
    default_supplier_account_id: Optional[int] = None
    default_cash_account_id: Optional[int] = None
    default_bank_account_id: Optional[int] = None


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
class CostCenterInput:
    name: str
    department_id: Optional[int] = None
    is_active: Optional[bool] = True
    company_id: int


@strawberry.input
class UpdateCostCenterInput:
    id: int
    name: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


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
    recipients: Optional[str] = None
    interval_minutes: int = 60
    enabled: bool = True
    company_id: int


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
    unit_price_with_vat: Optional[Decimal] = None
    discount_percent: Decimal = Decimal("0")
    expiration_date: Optional[str] = None
    batch_number: Optional[str] = None


@strawberry.input
class InvoiceInput:
    type: str
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
    operation_type: str
    amount: Decimal
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
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
    quantity_net: Optional[Decimal] = Decimal("0")
    waste_percentage: Optional[Decimal] = Decimal("0")
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
class RecipePriceUpdateInput:
    markup_percentage: Optional[Decimal] = None
    premium_amount: Optional[Decimal] = None
    portions: Optional[int] = None
    reason: Optional[str] = None


@strawberry.input
class RecipePriceInput:
    recipe_id: int
    markup_percentage: Optional[Decimal] = None
    premium_amount: Optional[Decimal] = None


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


@strawberry.input
class VehicleCreateInput:
    registration_number: str
    vin: Optional[str] = None
    make: str
    model: Optional[str] = None
    year: Optional[int] = None
    vehicle_type: Optional[str] = "car"
    fuel_type: Optional[str] = "dizel"
    status: Optional[str] = "active"
    color: Optional[str] = None
    initial_mileage: Optional[int] = 0
    is_company_vehicle: Optional[bool] = True
    notes: Optional[str] = None
    company_id: Optional[int] = None


@strawberry.input
class VehicleUpdateInput:
    registration_number: Optional[str] = None
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vehicle_type: Optional[str] = None
    fuel_type: Optional[str] = None
    status: Optional[str] = None
    color: Optional[str] = None
    initial_mileage: Optional[int] = None
    is_company_vehicle: Optional[bool] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleMileageInput:
    vehicle_id: int
    date: datetime.datetime
    mileage: int
    notes: Optional[str] = None


@strawberry.input
class VehicleFuelInput:
    vehicle_id: int
    date: datetime.datetime
    liters: float
    price: float
    total: float
    fuel_type: Optional[str] = "dizel"
    notes: Optional[str] = None


@strawberry.input
class VehicleRepairInput:
    vehicle_id: int
    date: datetime.datetime
    description: str
    cost: Optional[float] = 0
    repair_type: Optional[str] = "maintenance"
    notes: Optional[str] = None


@strawberry.input
class VehicleInsuranceInput:
    vehicle_id: int
    provider: str
    policy_number: str
    start_date: datetime.datetime
    end_date: datetime.datetime
    premium: Optional[float] = 0
    insurance_type: Optional[str] = "grazhdanska"
    notes: Optional[str] = None


@strawberry.input
class VehicleInspectionInput:
    vehicle_id: int
    date: datetime.datetime
    next_date: Optional[datetime.datetime] = None
    cost: Optional[float] = 0
    result: Optional[str] = "passed"
    protocol_number: Optional[str] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleDriverInput:
    vehicle_id: int
    user_id: int
    license_number: str
    license_expiry: datetime.datetime
    phone: Optional[str] = None
    category: Optional[str] = "B"
    is_primary: Optional[bool] = False
    notes: Optional[str] = None


@strawberry.input
class VehicleTripInput:
    vehicle_id: int
    user_id: int
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    distance: Optional[float] = 0
    trip_type: Optional[str] = "business"
    notes: Optional[str] = None


@strawberry.input
class VehicleMileageUpdateInput:
    date: Optional[datetime.datetime] = None
    mileage: Optional[int] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleFuelUpdateInput:
    date: Optional[datetime.datetime] = None
    liters: Optional[float] = None
    price: Optional[float] = None
    total: Optional[float] = None
    fuel_type: Optional[str] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleRepairUpdateInput:
    date: Optional[datetime.datetime] = None
    description: Optional[str] = None
    cost: Optional[float] = None
    repair_type: Optional[str] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleInsuranceUpdateInput:
    provider: Optional[str] = None
    policy_number: Optional[str] = None
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    premium: Optional[float] = None
    insurance_type: Optional[str] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleInspectionUpdateInput:
    date: Optional[datetime.datetime] = None
    next_date: Optional[datetime.datetime] = None
    cost: Optional[float] = None
    result: Optional[str] = None
    protocol_number: Optional[str] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleDriverUpdateInput:
    license_number: Optional[str] = None
    license_expiry: Optional[datetime.datetime] = None
    phone: Optional[str] = None
    category: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


@strawberry.input
class VehicleTripUpdateInput:
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    distance: Optional[float] = None
    trip_type: Optional[str] = None
    notes: Optional[str] = None


@strawberry.input
class EmploymentContractCreateInput:
    employee_name: str
    employee_egn: str
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    template_id: Optional[int] = None  # Избор на шаблон
    contract_type: str
    contract_number: Optional[str] = None
    start_date: datetime.date
    end_date: Optional[datetime.date] = None
    base_salary: Optional[float] = None
    work_hours_per_week: int = 40
    job_description: Optional[str] = None
    # TRZ полета от шаблон
    probation_months: Optional[int] = None
    salary_calculation_type: Optional[str] = 'gross'
    payment_day: Optional[int] = 25
    night_work_rate: Optional[float] = 0.5
    overtime_rate: Optional[float] = 1.5
    holiday_rate: Optional[float] = 2.0
    work_class: Optional[str] = None
    clause_ids: Optional[str] = None  # JSON string like "[1,2,3]"


@strawberry.input
class EmploymentContractUpdateInput:
    employee_name: Optional[str] = None
    employee_egn: Optional[str] = None
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    template_id: Optional[int] = None
    contract_number: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    base_salary: Optional[float] = None
    work_hours_per_week: Optional[int] = None
    job_description: Optional[str] = None
    probation_months: Optional[int] = None
    salary_calculation_type: Optional[str] = None
    payment_day: Optional[int] = None
    night_work_rate: Optional[float] = None
    overtime_rate: Optional[float] = None
    holiday_rate: Optional[float] = None
    work_class: Optional[str] = None


@strawberry.input
class ContractTemplateSectionInput:
    title: str
    content: str
    order_index: int = 0
    is_required: bool = False


@strawberry.input
class ContractTemplateSectionUpdateInput:
    title: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None
    is_required: Optional[bool] = None


@strawberry.input
class AnnexTemplateSectionInput:
    title: str
    content: str
    order_index: int = 0
    is_required: bool = False


@strawberry.input
class AnnexTemplateSectionUpdateInput:
    title: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None
    is_required: Optional[bool] = None
