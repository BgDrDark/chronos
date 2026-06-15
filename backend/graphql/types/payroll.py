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
    batch_id: strawberry.auto
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


@strawberry.type
class SalaryPaymentBatchType:
    id: int
    company_id: int
    period_start: datetime.date
    period_end: datetime.date
    payment_date: datetime.datetime
    total_amount: float
    status: str
    payment_method: str
    payment_reference: str | None = None
    notes: str | None = None
    created_at: datetime.datetime

    @strawberry.field
    async def paid_by_user(self, info: strawberry.Info) -> User | None:
        return await info.context["dataloaders"]["user_by_id"].load(self.paid_by)

    @strawberry.field
    async def items(self, info: strawberry.Info) -> list["SalaryPaymentItemType"]:
        from backend.crud.repositories.salary_payment_repo import salary_payment_repo
        db = info.context["db"]
        raw_items = await salary_payment_repo.list_items_by_batch(db, self.id)
        return [SalaryPaymentItemType(
            id=item.id,
            batch_id=item.batch_id,
            payslip_id=item.payslip_id,
            user_id=item.user_id,
            amount=float(item.amount),
            paid_at=item.paid_at,
        ) for item in raw_items]


@strawberry.type
class SalaryPaymentItemType:
    id: int
    batch_id: int
    payslip_id: int | None = None
    user_id: int
    amount: float
    paid_at: datetime.datetime | None = None

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User | None:
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@strawberry.type
class PaymentStatisticsType:
    total_batches: int
    total_amount: float
    total_employees_paid: int
    average_payment_per_employee: float
    by_method: dict[str, float] | None = None
    by_status: dict[str, int] | None = None


@sp.type(schemas.AdvancePayment)
class AdvancePayment:
    id: strawberry.auto
    user_id: strawberry.auto
    amount: strawberry.auto
    payment_date: strawberry.auto
    description: strawberry.auto
    is_processed: strawberry.auto
    created_at: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


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

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


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
    