from datetime import date, datetime
from decimal import Decimal

from backend.schemas.base import CustomBaseModel


class EmploymentContract(CustomBaseModel):
    id: int
    user_id: int | None = None
    company_id: int
    contract_type: str
    contract_number: str | None = None
    start_date: date
    end_date: date | None = None
    base_salary: Decimal | None = None
    work_hours_per_week: int = 40
    probation_months: int = 0
    probation_beneficiary: str | None = "employer"
    notice_period_days: int | None = 30
    is_active: bool = True
    salary_calculation_type: str = "gross"
    salary_installments_count: int = 1
    monthly_advance_amount: Decimal = Decimal(0)
    tax_resident: bool = True
    insurance_contributor: bool = True
    has_income_tax: bool = True
    payment_day: int = 25
    experience_start_date: date | None = None
    night_work_rate: Decimal = Decimal("0.5")
    overtime_rate: Decimal = Decimal("1.5")
    holiday_rate: Decimal = Decimal("2.0")
    work_class: str | None = None
    dangerous_work: bool = False
    template_id: int | None = None
    position_id: int | None = None
    department_id: int | None = None
    clause_ids: str | None = None
    employee_name: str | None = None
    employee_egn: str | None = None
    status: str = "draft"
    signed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ContractAnnex(CustomBaseModel):
    id: int
    contract_id: int
    annex_number: str | None = None
    effective_date: date
    base_salary: Decimal | None = None
    position_id: int | None = None
    work_hours_per_week: int | None = None
    probation_months: int | None = None
    night_work_rate: Decimal | None = None
    overtime_rate: Decimal | None = None
    holiday_rate: Decimal | None = None
    work_class: str | None = None
    is_signed: bool = False
    signed_at: datetime | None = None
    status: str = "draft"
    template_id: int | None = None
    change_type: str | None = None
    change_description: str | None = None
    signature_requested_at: datetime | None = None
    signed_by_employee: bool = False
    signed_by_employee_at: datetime | None = None
    signed_by_employer: bool = False
    signed_by_employer_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ContractTemplateSection(CustomBaseModel):
    id: int
    template_id: int
    version_id: int
    title: str
    content: str | None = None
    order_index: int = 0
    is_required: bool = False


class ContractTemplateVersion(CustomBaseModel):
    id: int
    template_id: int
    version: int
    contract_type: str
    base_salary: Decimal | None = None
    work_hours_per_week: int
    probation_months: int
    salary_calculation_type: str
    payment_day: int
    night_work_rate: Decimal
    overtime_rate: Decimal
    holiday_rate: Decimal
    work_class: str | None = None
    position_id: int | None = None
    department_id: int | None = None
    is_current: bool = False
    created_by: str | None = None
    created_at: datetime
    change_note: str | None = None


class ContractTemplate(CustomBaseModel):
    id: int
    company_id: int
    name: str
    description: str | None = None
    contract_type: str
    base_salary: Decimal | None = None
    work_hours_per_week: int = 40
    probation_months: int = 6
    salary_calculation_type: str = "gross"
    payment_day: int = 25
    night_work_rate: Decimal = Decimal("0.5")
    overtime_rate: Decimal = Decimal("1.5")
    holiday_rate: Decimal = Decimal("2.0")
    work_class: str | None = None
    position_id: int | None = None
    department_id: int | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class AnnexTemplateSection(CustomBaseModel):
    id: int
    template_id: int
    version_id: int
    title: str
    content: str | None = None
    order_index: int = 0
    is_required: bool = False


class AnnexTemplateVersion(CustomBaseModel):
    id: int
    template_id: int
    version: int
    change_type: str | None = None
    new_base_salary: Decimal | None = None
    new_work_hours_per_week: int | None = None
    new_night_work_rate: Decimal | None = None
    new_overtime_rate: Decimal | None = None
    new_holiday_rate: Decimal | None = None
    is_current: bool = False
    created_by: str | None = None
    created_at: datetime
    change_note: str | None = None


class AnnexTemplate(CustomBaseModel):
    id: int
    company_id: int
    name: str
    description: str | None = None
    change_type: str | None = None
    new_base_salary: Decimal | None = None
    new_work_hours_per_week: int | None = None
    new_night_work_rate: Decimal | None = None
    new_overtime_rate: Decimal | None = None
    new_holiday_rate: Decimal | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class ClauseTemplate(CustomBaseModel):
    id: int
    company_id: int
    title: str
    content: str | None = None
    category: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None
