import datetime
from decimal import Decimal
from typing import Optional

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.graphql.types import User


@strawberry.type
class SalaryInstallments:
    count: int
    amount_per_installment: float


@strawberry.type
class PayrollSummaryItem:
    user_id: int
    email: str
    full_name: str
    gross_amount: float
    net_amount: float
    tax_amount: float
    insurance_amount: float
    bonus_amount: float
    advances: float
    loan_deductions: float
    total_deductions: float
    net_payable: float
    contract_type: str
    installments: SalaryInstallments | None


@strawberry.type
class PayrollLegalSettings:
    max_insurance_base: float
    employee_insurance_rate: float
    income_tax_rate: float
    civil_contract_costs_rate: float
    noi_compensation_percent: float
    employer_paid_sick_days: int
    default_tax_resident: bool
    trz_compliance_strict_mode: bool


@sp.type(schemas.Payroll)
class Payroll:
    id: strawberry.auto
    hourly_rate: strawberry.auto
    monthly_salary: strawberry.auto
    overtime_multiplier: strawberry.auto
    standard_hours_per_day: strawberry.auto
    currency: strawberry.auto
    annual_leave_days: strawberry.auto
    tax_percent: strawberry.auto
    health_insurance_percent: strawberry.auto
    has_tax_deduction: strawberry.auto
    has_health_insurance: strawberry.auto
    user_id: strawberry.auto
    position_id: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> Optional["User"]:
        if not self.user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@sp.type(schemas.Payslip)
class Payslip:
    id: strawberry.auto
    user_id: strawberry.auto
    period_start: strawberry.auto
    period_end: strawberry.auto
    total_regular_hours: strawberry.auto
    total_overtime_hours: strawberry.auto
    regular_amount: strawberry.auto
    overtime_amount: strawberry.auto
    bonus_amount: strawberry.auto
    night_work_amount: strawberry.auto
    trip_amount: strawberry.auto
    voucher_amount: strawberry.auto
    benefit_amount: strawberry.auto
    sick_leave_amount: strawberry.auto
    tax_amount: strawberry.auto
    insurance_amount: strawberry.auto
    sick_days: strawberry.auto
    leave_days: strawberry.auto
    doo_employee: strawberry.auto
    doo_employer: strawberry.auto
    zo_employee: strawberry.auto
    zo_employer: strawberry.auto
    dzpo_employee: strawberry.auto
    dzpo_employer: strawberry.auto
    tzpb_employer: strawberry.auto
    gross_salary: strawberry.auto
    taxable_base: strawberry.auto
    income_tax: strawberry.auto
    standard_deduction: strawberry.auto
    total_amount: strawberry.auto
    payment_status: strawberry.auto
    actual_payment_date: strawberry.auto
    payment_method: strawberry.auto
    generated_at: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@strawberry.type
class GlobalPayrollConfig:
    id: str = "global"
    hourly_rate: Decimal
    monthly_salary: Decimal
    overtime_multiplier: Decimal
    standard_hours_per_day: int
    currency: str
    annual_leave_days: int
    tax_percent: Decimal
    health_insurance_percent: Decimal
    has_tax_deduction: bool
    has_health_insurance: bool
    qr_regen_interval_minutes: int


@sp.type(schemas.Bonus)
class Bonus:
    id: strawberry.auto
    user_id: strawberry.auto
    amount: strawberry.auto
    date: strawberry.auto
    description: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@sp.type(schemas.AdvancePayment)
class AdvancePayment:
    id: strawberry.auto
    user_id: strawberry.auto
    amount: strawberry.auto
    payment_date: strawberry.auto
    description: strawberry.auto
    is_processed: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.ServiceLoan)
class ServiceLoan:
    id: strawberry.auto
    user_id: strawberry.auto
    total_amount: strawberry.auto
    installment_amount: strawberry.auto
    remaining_amount: strawberry.auto
    installments_count: strawberry.auto
    installments_paid: strawberry.auto
    start_date: strawberry.auto
    description: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto


@strawberry.type
class DepartmentForecast:
    department_name: str
    amount: float


@strawberry.type
class PayrollForecast:
    total_amount: float
    by_department: list[DepartmentForecast]


@strawberry.type
class LoanDetail:
    loan_id: int
    amount: float
    description: str | None
    remaining_before: float
    remaining_after: float
    date: datetime.date
    