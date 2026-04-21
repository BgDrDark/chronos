import datetime
import os, sys
import json
import enum
import strawberry
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database import models
from backend.database.models import sofia_now
from backend.utils.json_type import JSONScalar
from backend.crud.repositories import time_repo, settings_repo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))



if TYPE_CHECKING:
    from backend.graphql.types import Workstation

@strawberry.type
class Role:
    id: int
    name: str
    description: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.Role) -> "Role":
        return cls(
            id=instance.id,
            name=instance.name,
            description=instance.description,
        )

@strawberry.type
class Company:
    id: int
    name: str
    eik: Optional[str]
    bulstat: Optional[str]
    vat_number: Optional[str]
    address: Optional[str]
    mol_name: Optional[str]
    
    # Default accounting accounts
    default_sales_account_id: Optional[int]
    default_expense_account_id: Optional[int]
    default_vat_account_id: Optional[int]
    default_customer_account_id: Optional[int]
    default_supplier_account_id: Optional[int]
    default_cash_account_id: Optional[int]
    default_bank_account_id: Optional[int]

    @strawberry.field
    async def default_sales_account(self, info: strawberry.Info) -> Optional["Account"]:
        if not self.default_sales_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_sales_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def default_expense_account(self, info: strawberry.Info) -> Optional["Account"]:
        if not self.default_expense_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_expense_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def default_vat_account(self, info: strawberry.Info) -> Optional["Account"]:
        if not self.default_vat_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_vat_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def default_customer_account(self, info: strawberry.Info) -> Optional["Account"]:
        if not self.default_customer_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_customer_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def default_supplier_account(self, info: strawberry.Info) -> Optional["Account"]:
        if not self.default_supplier_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_supplier_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def default_cash_account(self, info: strawberry.Info) -> Optional["Account"]:
        if not self.default_cash_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_cash_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def default_bank_account(self, info: strawberry.Info) -> Optional["Account"]:
        if not self.default_bank_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.default_bank_account_id)
        return Account.from_instance(result) if result else None

    @classmethod
    def from_instance(cls, instance: models.Company) -> "Company":
        return cls(
            id=instance.id, 
            name=instance.name,
            eik=instance.eik,
            bulstat=instance.bulstat,
            vat_number=instance.vat_number,
            address=instance.address,
            mol_name=instance.mol_name,
            default_sales_account_id=instance.default_sales_account_id,
            default_expense_account_id=instance.default_expense_account_id,
            default_vat_account_id=instance.default_vat_account_id,
            default_customer_account_id=instance.default_customer_account_id,
            default_supplier_account_id=instance.default_supplier_account_id,
            default_cash_account_id=instance.default_cash_account_id,
            default_bank_account_id=instance.default_bank_account_id,
        )

@strawberry.type
class Department:
    id: int
    name: str
    company_id: Optional[int]
    manager_id: Optional[int]

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Optional[Company]:
        if not self.company_id: return None
        db = info.context["db"]
        from backend.database.models import Company as DbCompany
        res = await db.get(DbCompany, self.company_id)
        return Company.from_instance(res) if res else None

    @strawberry.field
    async def manager(self, info: strawberry.Info) -> Optional["User"]:
        if not self.manager_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.manager_id)

    @classmethod
    def from_instance(cls, instance: models.Department) -> "Department":
        return cls(
            id=instance.id, 
            name=instance.name, 
            company_id=instance.company_id,
            manager_id=getattr(instance, "manager_id", None)
        )

@strawberry.type
class Position:
    id: int
    title: str
    department_id: Optional[int]

    @strawberry.field
    async def department(self, info: strawberry.Info) -> Optional[Department]:
        if not self.department_id: return None
        # TODO: Add dataloader
        db = info.context["db"]
        from backend.database.models import Department as DbDepartment
        res = await db.get(DbDepartment, self.department_id)
        return Department.from_instance(res) if res else None

    @strawberry.field
    async def payrolls(self, info: strawberry.Info) -> List["Payroll"]:
        db = info.context["db"]
        from backend.database.models import Payroll as DbPayroll
        result = await db.execute(
            select(DbPayroll).where(DbPayroll.position_id == self.id)
        )
        rows = result.scalars().all()
        return [Payroll.from_instance(r) for r in rows]

    @classmethod
    def from_instance(cls, instance: models.Position) -> "Position":
        return cls(id=instance.id, title=instance.title, department_id=instance.department_id)

@strawberry.type
class GoogleCalendarSyncSettings:
    id: int
    calendar_id: str
    sync_work_schedules: bool
    sync_time_logs: bool
    sync_leave_requests: bool
    sync_public_holidays: bool
    sync_direction: str
    sync_frequency_minutes: int
    privacy_level: str

@strawberry.type
class KioskSecuritySettings:
    require_gps: bool
    require_same_network: bool

@strawberry.type
class GoogleCalendarAccount:
    id: int
    email: str
    is_active: bool
    sync_settings: Optional[GoogleCalendarSyncSettings]

@strawberry.type
class LoanDetail:
    loan_id: int
    amount: float
    description: Optional[str]
    remaining_before: float

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
    installments: Optional[SalaryInstallments]

@strawberry.type
class EmploymentContract:
    id: int
    user_id: Optional[int]
    company_id: int
    company: Optional["Company"]
    department_id: Optional[int]
    department: Optional["Department"]
    contract_type: str
    contract_number: Optional[str]
    start_date: datetime.date
    end_date: Optional[datetime.date]
    base_salary: Optional[Decimal]
    work_hours_per_week: int
    probation_months: int
    is_active: bool
    salary_calculation_type: str
    salary_installments_count: int
    monthly_advance_amount: Decimal
    tax_resident: bool
    insurance_contributor: bool
    has_income_tax: bool
    # ТРЗ разширение
    payment_day: int
    experience_start_date: Optional[datetime.date]
    night_work_rate: Optional[Decimal]
    overtime_rate: Optional[Decimal]
    holiday_rate: Optional[Decimal]
    work_class: Optional[str]
    dangerous_work: bool
    position_id: Optional[int]
    position_title: Optional[str]
    position: Optional["Position"]
    # Нови полета за трудов договор
    employee_name: Optional[str]
    employee_egn: Optional[str]
    status: str
    signed_at: Optional[datetime.datetime]

    @strawberry.field
    async def annexes(self, info: strawberry.Info) -> List["ContractAnnex"]:
        """Връща списък с всички анекси за този договор"""
        from sqlalchemy import select
        from backend.database.models import ContractAnnex as ModelContractAnnex
        db = info.context["db"]
        stmt = select(ModelContractAnnex).where(
            ModelContractAnnex.contract_id == self.id
        ).order_by(ModelContractAnnex.effective_date.desc())
        result = await db.execute(stmt)
        annexes = result.scalars().all()
        return [ContractAnnex.from_instance(a) for a in annexes]

    @classmethod
    def from_instance(cls, instance: models.EmploymentContract) -> "EmploymentContract":
        position_obj = None
        position_title = None
        department_obj = None
        company_obj = None
        if hasattr(instance, 'position_id') and instance.position_id:
            position_obj = instance.position
            if position_obj:
                position_title = position_obj.title
        if hasattr(instance, 'department_id') and instance.department_id:
            department_obj = instance.department
        if hasattr(instance, 'company_id') and instance.company_id:
            company_obj = instance.company
        return cls(
            id=instance.id,
            user_id=getattr(instance, 'user_id', None),
            company_id=instance.company_id,
            department_id=getattr(instance, 'department_id', None),
            contract_type=instance.contract_type,
            contract_number=instance.contract_number if hasattr(instance, "contract_number") else None,
            start_date=instance.start_date,
            end_date=instance.end_date,
            base_salary=instance.base_salary,
            work_hours_per_week=instance.work_hours_per_week,
            probation_months=instance.probation_months,
            is_active=instance.is_active,
            salary_calculation_type=instance.salary_calculation_type,
            salary_installments_count=instance.salary_installments_count,
            monthly_advance_amount=instance.monthly_advance_amount or Decimal("0"),
            tax_resident=instance.tax_resident if instance.tax_resident is not None else True,
            insurance_contributor=instance.insurance_contributor if instance.insurance_contributor is not None else True,
            has_income_tax=instance.has_income_tax if instance.has_income_tax is not None else True,
            # ТРЗ разширение
            payment_day=instance.payment_day if hasattr(instance, "payment_day") and instance.payment_day is not None else 25,
            experience_start_date=instance.experience_start_date if hasattr(instance, "experience_start_date") else None,
            night_work_rate=instance.night_work_rate,
            overtime_rate=instance.overtime_rate,
            holiday_rate=instance.holiday_rate,
            work_class=instance.work_class,
            dangerous_work=instance.dangerous_work if instance.dangerous_work is not None else False,
            position_id=getattr(instance, 'position_id', None),
            position_title=position_title,
            position=Position.from_instance(position_obj) if position_obj else None,
            department=Department.from_instance(department_obj) if department_obj else None,
            company=Company.from_instance(company_obj) if company_obj else None,
            # Нови полета
            employee_name=getattr(instance, 'employee_name', None),
            employee_egn=getattr(instance, 'employee_egn', None),
            status=getattr(instance, 'status', 'draft') or 'draft',
            signed_at=getattr(instance, 'signed_at', None),
        )

@strawberry.type
class ContractAnnex:
    id: int
    contract_id: int
    annex_number: Optional[str]
    effective_date: datetime.date
    base_salary: Optional[Decimal]
    position_id: Optional[int]
    work_hours_per_week: Optional[int]
    night_work_rate: Optional[Decimal]
    overtime_rate: Optional[Decimal]
    holiday_rate: Optional[Decimal]
    is_signed: bool
    signed_at: Optional[datetime.datetime]
    status: str
    template_id: Optional[int]
    change_type: Optional[str]
    change_description: Optional[str]
    signature_requested_at: Optional[datetime.datetime]
    signed_by_employee: bool
    signed_by_employee_at: Optional[datetime.datetime]
    signed_by_employer: bool
    signed_by_employer_at: Optional[datetime.datetime]
    rejection_reason: Optional[str]
    created_at: datetime.datetime

    @strawberry.field
    async def position(self, info: strawberry.Info) -> Optional["Position"]:
        if not self.position_id:
            return None
        return await info.context["dataloaders"]["position_by_id"].load(self.position_id)

    @classmethod
    def from_instance(cls, instance: models.ContractAnnex) -> "ContractAnnex":
        return cls(
            id=instance.id,
            contract_id=instance.contract_id,
            annex_number=instance.annex_number,
            effective_date=instance.effective_date,
            base_salary=instance.base_salary,
            position_id=instance.position_id,
            work_hours_per_week=instance.work_hours_per_week,
            night_work_rate=instance.night_work_rate,
            overtime_rate=instance.overtime_rate,
            holiday_rate=instance.holiday_rate,
            is_signed=instance.is_signed,
            signed_at=instance.signed_at,
            status=instance.status if instance.status else "draft",
            template_id=instance.template_id,
            change_type=instance.change_type,
            change_description=instance.change_description,
            signature_requested_at=instance.signature_requested_at,
            signed_by_employee=instance.signed_by_employee if instance.signed_by_employee else False,
            signed_by_employee_at=instance.signed_by_employee_at,
            signed_by_employer=instance.signed_by_employer if instance.signed_by_employer else False,
            signed_by_employer_at=instance.signed_by_employer_at,
            rejection_reason=instance.rejection_reason,
            created_at=instance.created_at
        )


@strawberry.type
class ContractTemplateSection:
    id: int
    template_id: int
    version_id: int
    title: str
    content: Optional[str]
    order_index: int
    is_required: bool


@strawberry.type
class ContractTemplateVersion:
    id: int
    template_id: int
    version: int
    contract_type: str
    work_hours_per_week: int
    probation_months: int
    salary_calculation_type: str
    payment_day: int
    night_work_rate: float
    overtime_rate: float
    holiday_rate: float
    work_class: Optional[str]
    is_current: bool
    created_by: Optional[str]
    created_at: datetime.datetime
    change_note: Optional[str]

    @strawberry.field
    async def sections(self, info: strawberry.Info) -> List["ContractTemplateSection"]:
        from sqlalchemy import select
        from backend.database.models import ContractTemplateSection as ModelSection
        db = info.context["db"]
        stmt = select(ModelSection).where(ModelSection.version_id == self.id).order_by(ModelSection.order_index)
        result = await db.execute(stmt)
        sections = result.scalars().all()
        return [ContractTemplateSection(
            id=s.id,
            template_id=s.template_id,
            version_id=s.version_id,
            title=s.title,
            content=s.content,
            order_index=s.order_index,
            is_required=s.is_required
        ) for s in sections]


@strawberry.type
class ContractTemplate:
    id: int
    company_id: int
    name: str
    description: Optional[str]
    contract_type: str
    work_hours_per_week: int
    probation_months: int
    salary_calculation_type: str
    payment_day: int
    night_work_rate: float
    overtime_rate: float
    holiday_rate: float
    work_class: Optional[str]
    is_active: bool
    created_at: datetime.datetime

    @strawberry.field
    async def current_version(self, info: strawberry.Info) -> Optional["ContractTemplateVersion"]:
        from sqlalchemy import select
        from backend.database.models import ContractTemplateVersion as ModelVersion
        db = info.context["db"]
        stmt = select(ModelVersion).where(
            ModelVersion.template_id == self.id,
            ModelVersion.is_current == True
        ).order_by(ModelVersion.version.desc())
        result = await db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            return None
        return ContractTemplateVersion(
            id=version.id,
            template_id=version.template_id,
            version=version.version,
            contract_type=version.contract_type,
            work_hours_per_week=version.work_hours_per_week,
            probation_months=version.probation_months,
            salary_calculation_type=version.salary_calculation_type,
            payment_day=version.payment_day,
            night_work_rate=float(version.night_work_rate),
            overtime_rate=float(version.overtime_rate),
            holiday_rate=float(version.holiday_rate),
            work_class=version.work_class,
            is_current=version.is_current,
            created_by=version.created_by,
            created_at=version.created_at,
            change_note=version.change_note
        )


@strawberry.type
class AnnexTemplateSection:
    id: int
    template_id: int
    version_id: int
    title: str
    content: Optional[str]
    order_index: int
    is_required: bool


@strawberry.type
class AnnexTemplateVersion:
    id: int
    template_id: int
    version: int
    change_type: str
    new_base_salary: Optional[float]
    new_work_hours_per_week: Optional[int]
    new_night_work_rate: Optional[float]
    new_overtime_rate: Optional[float]
    new_holiday_rate: Optional[float]
    is_current: bool
    created_by: Optional[str]
    created_at: datetime.datetime
    change_note: Optional[str]

    @strawberry.field
    async def sections(self, info: strawberry.Info) -> List["AnnexTemplateSection"]:
        from sqlalchemy import select
        from backend.database.models import AnnexTemplateSection as ModelSection
        db = info.context["db"]
        stmt = select(ModelSection).where(ModelSection.version_id == self.id).order_by(ModelSection.order_index)
        result = await db.execute(stmt)
        sections = result.scalars().all()
        return [AnnexTemplateSection(
            id=s.id,
            template_id=s.template_id,
            version_id=s.version_id,
            title=s.title,
            content=s.content,
            order_index=s.order_index,
            is_required=s.is_required
        ) for s in sections]


@strawberry.type
class AnnexTemplate:
    id: int
    company_id: int
    name: str
    description: Optional[str]
    change_type: str
    new_base_salary: Optional[float]
    new_work_hours_per_week: Optional[int]
    new_night_work_rate: Optional[float]
    new_overtime_rate: Optional[float]
    new_holiday_rate: Optional[float]
    is_active: bool
    created_at: datetime.datetime

    @strawberry.field
    async def current_version(self, info: strawberry.Info) -> Optional["AnnexTemplateVersion"]:
        from sqlalchemy import select
        from backend.database.models import AnnexTemplateVersion as ModelVersion
        db = info.context["db"]
        stmt = select(ModelVersion).where(
            ModelVersion.template_id == self.id,
            ModelVersion.is_current == True
        ).order_by(ModelVersion.version.desc())
        result = await db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            return None
        return AnnexTemplateVersion(
            id=version.id,
            template_id=version.template_id,
            version=version.version,
            change_type=version.change_type,
            new_base_salary=float(version.new_base_salary) if version.new_base_salary else None,
            new_work_hours_per_week=version.new_work_hours_per_week,
            new_night_work_rate=float(version.new_night_work_rate) if version.new_night_work_rate else None,
            new_overtime_rate=float(version.new_overtime_rate) if version.new_overtime_rate else None,
            new_holiday_rate=float(version.new_holiday_rate) if version.new_holiday_rate else None,
            is_current=version.is_current,
            created_by=version.created_by,
            created_at=version.created_at,
            change_note=version.change_note
        )


@strawberry.type
class ClauseTemplate:
    id: int
    company_id: int
    title: str
    content: Optional[str]
    category: str
    is_active: bool
    created_at: datetime.datetime


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

@strawberry.type
class User:
    id: int
    email: Optional[str]
    username: Optional[str]
    first_name: Optional[str]
    surname: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]
    egn: Optional[str]
    pin: Optional[str] = strawberry.field(name="pin", default=None, deprecation_reason="Use egn instead")
    birth_date: Optional[datetime.date]
    iban: Optional[str]
    is_active: bool
    role_id: int 
    
    created_at: Optional[datetime.datetime]
    last_login: Optional[datetime.datetime]
    qr_token: Optional[str] # New field for Kiosk
    password_force_change: bool
    profile_picture: Optional[str]

    @strawberry.field
    async def role(self, info: strawberry.Info) -> "Role":
        return await info.context["dataloaders"]["role_by_id"].load(self.role_id)
    
    # Deprecated String Fields - must be defined as fields to be kept by strawberry/pydantic
    job_title_legacy: Optional[str] = strawberry.field(deprecation_reason="Use position relation", name="jobTitleLegacy")
    department_legacy: Optional[str] = strawberry.field(deprecation_reason="Use department relation", name="departmentLegacy")
    company_legacy: Optional[str] = strawberry.field(deprecation_reason="Use company relation", name="companyLegacy")

    # Compatibility fields for frontend (as scalars)
    @strawberry.field
    async def job_title(self, info: strawberry.Info) -> Optional[str]:
        if self.position_id:
            db = info.context["db"]
            from backend.database.models import Position as DbPosition
            res = await db.get(DbPosition, self.position_id)
            if res: return res.title
        return self.job_title_legacy

    # New relations as objects (restored original names)
    @strawberry.field
    async def company(self, info: strawberry.Info) -> Optional[Company]:
        if not self.company_id: return None
        db = info.context["db"]
        from backend.database.models import Company as DbCompany
        res = await db.get(DbCompany, self.company_id)
        return Company.from_instance(res) if res else None

    @strawberry.field
    async def department(self, info: strawberry.Info) -> Optional[Department]:
        if not self.department_id: return None
        db = info.context["db"]
        from backend.database.models import Department as DbDepartment
        res = await db.get(DbDepartment, self.department_id)
        return Department.from_instance(res) if res else None

    # Scalar versions for settings page
    @strawberry.field
    async def company_name(self, info: strawberry.Info) -> Optional[str]:
        if not self.company_id: return self.company_legacy
        obj = await info.context["dataloaders"]["company_by_id"].load(self.company_id)
        return obj.name if obj else self.company_legacy

    @strawberry.field
    async def department_name(self, info: strawberry.Info) -> Optional[str]:
        if not self.department_id: 
            return self.department_legacy
        obj = await info.context["dataloaders"]["department_by_id"].load(self.department_id)
        return obj.name if obj else self.department_legacy

    # New Relations (internal IDs)
    company_id: Optional[int]
    department_id: Optional[int]
    position_id: Optional[int]

    @strawberry.field
    async def position(self, info: strawberry.Info) -> Optional["Position"]:
        if not self.position_id: return None
        return await info.context["dataloaders"]["position_by_id"].load(self.position_id)

    @strawberry.field
    async def employment_contract(self, info: strawberry.Info) -> Optional["EmploymentContract"]:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from backend.database.models import EmploymentContract as EmploymentContractModel
        db = info.context["db"]
        stmt = select(EmploymentContractModel).options(
            selectinload(EmploymentContractModel.company),
            selectinload(EmploymentContractModel.position),
            selectinload(EmploymentContractModel.department)
        ).where(
            EmploymentContractModel.user_id == self.id,
            EmploymentContractModel.is_active == True
        )
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()
        return EmploymentContract.from_instance(contract) if contract else None
    
    @strawberry.field
    async def timelogs(
        self, 
        info: strawberry.Info,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None
    ) -> List["TimeLog"]:
        db = info.context["db"]
        from backend import crud
        
        if start_date and end_date:
            start_dt = datetime.datetime.combine(start_date, datetime.time.min)
            end_dt = datetime.datetime.combine(end_date, datetime.time.max)
        else:
            # Fallback to last 30 days
            end_dt = sofia_now()
            start_dt = end_dt - datetime.timedelta(days=30)

        logs = await crud.get_timelogs_by_user_and_period(
            db, 
            self.id, 
            start_dt,
            end_dt
        )
        return [TimeLog.from_instance(l) for l in logs]
    
    @strawberry.field
    async def payrolls(self, info: strawberry.Info) -> List["Payroll"]:
        db = info.context["db"]
        from backend.database.models import Payroll as DbPayroll
        result = await db.execute(
            select(DbPayroll).where(DbPayroll.user_id == self.id)
        )
        rows = result.scalars().all()
        return [Payroll.from_instance(r) for r in rows]

    @strawberry.field
    async def payslips(self, info: strawberry.Info) -> List["Payslip"]:
        db = info.context["db"]
        from backend.database.models import Payslip as DbPayslip
        result = await db.execute(
            select(DbPayslip).where(DbPayslip.user_id == self.id)
        )
        rows = result.scalars().all()
        return [Payslip.from_instance(r) for r in rows]

    @strawberry.field
    async def bonuses(self, info: strawberry.Info) -> List["Bonus"]:
        db = info.context["db"]
        from backend.database.models import Bonus as DbBonus
        result = await db.execute(
            select(DbBonus).where(DbBonus.user_id == self.id)
        )
        rows = result.scalars().all()
        return [Bonus.from_instance(r) for r in rows]

    @strawberry.field
    async def current_schedule(self, info: strawberry.Info) -> Optional["WorkSchedule"]:
        db = info.context["db"]
        from backend.database.models import WorkSchedule as DbWorkSchedule
        
        # Get today's schedule
        today = datetime.datetime.now().date()
        result = await db.execute(
            select(DbWorkSchedule)
            .where(DbWorkSchedule.user_id == self.id)
            .where(DbWorkSchedule.date == today)
            .options(selectinload(DbWorkSchedule.shift))
        )
        schedule = result.scalars().first()
        # Ensure we use the global WorkSchedule type for the response
        return WorkSchedule.from_instance(schedule) if schedule else None

    @strawberry.field
    async def leave_balance(self, info: strawberry.Info, year: Optional[int] = None) -> Optional["LeaveBalance"]:
        db = info.context["db"]
        target_year = year if year is not None else datetime.datetime.now().year
        balance = await time_repo.get_leave_balance(db, self.id, target_year)
        return LeaveBalance.from_instance(balance) if balance else None

    @strawberry.field
    async def is_smtp_configured(self, info: strawberry.Info) -> bool:
        if self.role_id != 1: 
             db = info.context["db"]
             from backend.database.models import Role
             role_res = await db.get(Role, self.role_id)
             if not role_res or role_res.name != "admin":
                 return True 
        
        from backend import crud
        db = info.context["db"]
        return await settings_repo.is_smtp_configured(db)

    @classmethod
    def from_instance(cls, instance: models.User) -> "User":
        from backend.auth.security import decrypt_data
        return cls(
            id=instance.id,
            email=instance.email,
            username=instance.username,
            first_name=instance.first_name,
            surname=getattr(instance, 'surname', None),
            last_name=instance.last_name,
            phone_number=getattr(instance, 'phone_number', None),
            address=getattr(instance, 'address', None),
            egn=decrypt_data(str(instance.egn)) if instance.egn else None,
            birth_date=getattr(instance, 'birth_date', None),
            iban=decrypt_data(str(instance.iban)) if instance.iban else None,
            is_active=instance.is_active,
            role_id=instance.role_id,
            # Legacy mapping
            job_title_legacy=instance.job_title,
            department_legacy=instance.department,
            company_legacy=instance.company,
            # New mapping
            company_id=instance.company_id,
            department_id=instance.department_id,
            position_id=instance.position_id,
            
            created_at=instance.created_at,
            last_login=instance.last_login,
            qr_token=instance.qr_token, 
            password_force_change=getattr(instance, "password_force_change", False) or False,
            profile_picture=getattr(instance, "profile_picture", None),
            failed_login_attempts=instance.failed_login_attempts if hasattr(instance, "failed_login_attempts") and instance.failed_login_attempts is not None else 0,
            locked_until=instance.locked_until if hasattr(instance, "locked_until") else None
        )
    
    # Security Fields
    failed_login_attempts: int
    locked_until: Optional[datetime.datetime]

    @strawberry.field
    async def active_contract(self, info: strawberry.Info) -> Optional["EmploymentContract"]:
        return await info.context["dataloaders"]["contract_by_user_id"].load(self.id)

    @strawberry.field
    async def accessible_zones(self, info: strawberry.Info) -> List["AccessZone"]:
        db = info.context["db"]
        from backend.database.models import User as DbUser
        stmt = select(DbUser).where(DbUser.id == self.id).options(selectinload(DbUser.accessible_zones))
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        return [AccessZone.from_instance(z) for z in user.accessible_zones] if user else []

@strawberry.type
class UserSession:
    id: int
    user_id: int
    refresh_token_jti: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_type: Optional[str]
    is_active: bool
    created_at: Optional[datetime.datetime]
    expires_at: datetime.datetime
    last_used_at: Optional[datetime.datetime]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.UserSession) -> "UserSession":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            refresh_token_jti=instance.refresh_token_jti,
            ip_address=instance.ip_address,
            user_agent=instance.user_agent,
            device_type=instance.device_type,
            is_active=instance.is_active if instance.is_active is not None else False,
            created_at=instance.created_at,
            expires_at=instance.expires_at,
            last_used_at=instance.last_used_at
        )

@strawberry.type
class PaginatedUsers:
    users: List[User]
    total_count: int

@strawberry.type
class TimeLog:
    id: int
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    is_manual: bool = False
    break_duration_minutes: int = 0
    user_id: int

    @strawberry.field
    async def user(self, info: strawberry.Info) -> Optional[User]:
        if not self.user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.TimeLog) -> "TimeLog":
        return cls(
            id=instance.id,
            start_time=instance.start_time,
            end_time=instance.end_time,
            is_manual=instance.is_manual if hasattr(instance, 'is_manual') and instance.is_manual is not None else False,
            break_duration_minutes=instance.break_duration_minutes if hasattr(instance, 'break_duration_minutes') and instance.break_duration_minutes is not None else 0,
            user_id=instance.user_id
        )

@strawberry.type
class Payroll:
    id: int
    hourly_rate: Decimal
    monthly_salary: Optional[Decimal]
    overtime_multiplier: Decimal
    standard_hours_per_day: int
    currency: str
    annual_leave_days: int
    
    # Deductions
    tax_percent: Decimal
    health_insurance_percent: Decimal
    has_tax_deduction: bool
    has_health_insurance: bool
    
    user_id: Optional[int]
    position_id: Optional[int]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> Optional["User"]:
        if not self.user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.Payroll) -> "Payroll":
        return cls(
            id=instance.id,
            hourly_rate=instance.hourly_rate,
            monthly_salary=instance.monthly_salary,
            overtime_multiplier=instance.overtime_multiplier,
            standard_hours_per_day=instance.standard_hours_per_day,
            currency=instance.currency if instance.currency is not None else "BGN",
            annual_leave_days=instance.annual_leave_days if instance.annual_leave_days is not None else 20,
            
            tax_percent=instance.tax_percent if instance.tax_percent is not None else Decimal("10.00"),
            health_insurance_percent=instance.health_insurance_percent if instance.health_insurance_percent is not None else Decimal("13.78"),
            has_tax_deduction=instance.has_tax_deduction if instance.has_tax_deduction is not None else True,
            has_health_insurance=instance.has_health_insurance if instance.has_health_insurance is not None else True,
            
            user_id=instance.user_id,
            position_id=instance.position_id
        )

@strawberry.type
class Payslip:
    id: int
    user_id: int
    period_start: datetime.datetime
    period_end: datetime.datetime
    total_regular_hours: Decimal
    total_overtime_hours: Decimal
    regular_amount: Decimal
    overtime_amount: Decimal
    bonus_amount: Decimal
    
    # ТРЗ разширение
    night_work_amount: Decimal
    trip_amount: Decimal
    voucher_amount: Decimal
    benefit_amount: Decimal
    sick_leave_amount: Decimal
    
    # Existing detail fields
    tax_amount: Decimal
    insurance_amount: Decimal
    sick_days: int
    leave_days: int
    
    # Оссигуровки (Фаза 1)
    doo_employee: Decimal
    doo_employer: Decimal
    zo_employee: Decimal
    zo_employer: Decimal
    dzpo_employee: Decimal
    dzpo_employer: Decimal
    tzpb_employer: Decimal
    
    # Данъци (Фаза 2)
    gross_salary: Decimal
    taxable_base: Decimal
    income_tax: Decimal
    standard_deduction: Decimal
    
    total_amount: Decimal
    
    # Плащане
    payment_status: str
    actual_payment_date: Optional[datetime.datetime]
    payment_method: str

    generated_at: datetime.datetime

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.Payslip) -> "Payslip":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            period_start=instance.period_start,
            period_end=instance.period_end,
            total_regular_hours=instance.total_regular_hours,
            total_overtime_hours=instance.total_overtime_hours,
            regular_amount=instance.regular_amount,
            overtime_amount=instance.overtime_amount,
            bonus_amount=instance.bonus_amount if hasattr(instance, "bonus_amount") and instance.bonus_amount is not None else Decimal("0"),
            night_work_amount=instance.night_work_amount if hasattr(instance, "night_work_amount") and instance.night_work_amount is not None else Decimal("0"),
            trip_amount=instance.trip_amount if hasattr(instance, "trip_amount") and instance.trip_amount is not None else Decimal("0"),
            voucher_amount=instance.voucher_amount if hasattr(instance, "voucher_amount") and instance.voucher_amount is not None else Decimal("0"),
            benefit_amount=instance.benefit_amount if hasattr(instance, "benefit_amount") and instance.benefit_amount is not None else Decimal("0"),
            sick_leave_amount=instance.sick_leave_amount if hasattr(instance, "sick_leave_amount") and instance.sick_leave_amount is not None else Decimal("0"),
            tax_amount=instance.tax_amount if hasattr(instance, "tax_amount") and instance.tax_amount is not None else Decimal("0"),
            insurance_amount=instance.insurance_amount if hasattr(instance, "insurance_amount") and instance.insurance_amount is not None else Decimal("0"),
            sick_days=instance.sick_days if hasattr(instance, "sick_days") and instance.sick_days is not None else 0,
            leave_days=instance.leave_days if hasattr(instance, "leave_days") and instance.leave_days is not None else 0,
            # Оссигуровки (Фаза 1)
            doo_employee=instance.doo_employee if hasattr(instance, "doo_employee") and instance.doo_employee is not None else Decimal("0"),
            doo_employer=instance.doo_employer if hasattr(instance, "doo_employer") and instance.doo_employer is not None else Decimal("0"),
            zo_employee=instance.zo_employee if hasattr(instance, "zo_employee") and instance.zo_employee is not None else Decimal("0"),
            zo_employer=instance.zo_employer if hasattr(instance, "zo_employer") and instance.zo_employer is not None else Decimal("0"),
            dzpo_employee=instance.dzpo_employee if hasattr(instance, "dzpo_employee") and instance.dzpo_employee is not None else Decimal("0"),
            dzpo_employer=instance.dzpo_employer if hasattr(instance, "dzpo_employer") and instance.dzpo_employer is not None else Decimal("0"),
            tzpb_employer=instance.tzpb_employer if hasattr(instance, "tzpb_employer") and instance.tzpb_employer is not None else Decimal("0"),
            # Данъци (Фаза 2)
            gross_salary=instance.gross_salary if hasattr(instance, "gross_salary") and instance.gross_salary is not None else Decimal("0"),
            taxable_base=instance.taxable_base if hasattr(instance, "taxable_base") and instance.taxable_base is not None else Decimal("0"),
            income_tax=instance.income_tax if hasattr(instance, "income_tax") and instance.income_tax is not None else Decimal("0"),
            standard_deduction=instance.standard_deduction if hasattr(instance, "standard_deduction") and instance.standard_deduction is not None else Decimal("0"),
            total_amount=instance.total_amount,
            payment_status=instance.payment_status if hasattr(instance, "payment_status") and instance.payment_status else "pending",
            actual_payment_date=instance.actual_payment_date if hasattr(instance, "actual_payment_date") else None,
            payment_method=instance.payment_method if hasattr(instance, "payment_method") and instance.payment_method else "bank",
            generated_at=instance.generated_at,
        )

@strawberry.type
class Notification:
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.Notification) -> "Notification":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            message=instance.message,
            is_read=instance.is_read,
            created_at=instance.created_at
        )

@strawberry.type
class Shift:
    id: int
    name: str
    start_time: datetime.time
    end_time: datetime.time
    tolerance_minutes: int
    break_duration_minutes: int
    pay_multiplier: Decimal
    shift_type: str

    @classmethod
    def from_instance(cls, instance: models.Shift) -> "Shift":
        return cls(
            id=instance.id,
            name=instance.name,
            start_time=instance.start_time,
            end_time=instance.end_time,
            tolerance_minutes=instance.tolerance_minutes if instance.tolerance_minutes is not None else 0,
            break_duration_minutes=instance.break_duration_minutes if instance.break_duration_minutes is not None else 0,
            pay_multiplier=instance.pay_multiplier if instance.pay_multiplier is not None else Decimal("1.0"),
            shift_type=instance.shift_type
        )

@strawberry.type
class WorkSchedule:
    id: int
    date: datetime.date
    user_id: int
    shift_id: int

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @strawberry.field
    async def shift(self, info: strawberry.Info) -> Optional["Shift"]:
        db = info.context["db"]
        db_shift = await time_repo.get_shift_by_id(db, self.shift_id)
        return Shift.from_instance(db_shift) if db_shift else None

    @classmethod
    def from_instance(cls, instance: models.WorkSchedule) -> "WorkSchedule":
        return cls(
            id=instance.id,
            date=instance.date,
            user_id=instance.user_id,
            shift_id=instance.shift_id
        )

@strawberry.type
class LeaveRequest:
    id: int
    user_id: int
    start_date: datetime.date
    end_date: datetime.date
    leave_type: str
    reason: Optional[str]
    status: str
    created_at: datetime.datetime
    admin_comment: Optional[str]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.LeaveRequest) -> "LeaveRequest":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            start_date=instance.start_date,
            end_date=instance.end_date,
            leave_type=instance.leave_type,
            reason=instance.reason,
            status=instance.status,
            created_at=instance.created_at,
            admin_comment=instance.admin_comment
        )

@strawberry.type
class LeaveBalance:
    id: int
    user_id: int
    year: int
    total_days: int
    used_days: int

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.LeaveBalance) -> "LeaveBalance":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            year=instance.year,
            total_days=instance.total_days,
            used_days=instance.used_days
        )

@strawberry.type
class PublicHoliday:
    id: int
    date: datetime.date
    name: str
    local_name: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.PublicHoliday) -> "PublicHoliday":
        return cls(
            id=instance.id,
            date=instance.date,
            name=instance.name,
            local_name=instance.local_name
        )

@strawberry.type
class OrthodoxHoliday:
    id: int
    date: datetime.date
    name: str
    local_name: Optional[str]
    is_fixed: bool

    @classmethod
    def from_instance(cls, instance: models.OrthodoxHoliday) -> "OrthodoxHoliday":
        return cls(
            id=instance.id,
            date=instance.date,
            name=instance.name,
            local_name=instance.local_name,
            is_fixed=instance.is_fixed if hasattr(instance, 'is_fixed') else True
        )

@strawberry.enum
class PresenceStatus(str, enum.Enum):
    ON_DUTY = "ON_DUTY"
    ABSENT = "ABSENT"
    LATE = "LATE"
    SICK_LEAVE = "SICK_LEAVE"
    PAID_LEAVE = "PAID_LEAVE"
    OFF_DUTY = "OFF_DUTY"

@strawberry.type
class UserPresence:
    user: User
    shift_start: Optional[datetime.time]
    shift_end: Optional[datetime.time]
    actual_arrival: Optional[datetime.datetime]
    actual_departure: Optional[datetime.datetime]
    status: PresenceStatus
    is_on_duty: bool

@strawberry.type
class SmtpSettings:
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: Optional[str] = None
    sender_email: str
    use_tls: bool


@strawberry.type
class NotificationSetting:
    id: int
    company_id: int
    event_type: str
    email_enabled: bool
    push_enabled: bool
    email_template: Optional[str]
    recipients: Optional[str]  # JSON string [{"type": "role", "value": "employee"}]
    interval_minutes: int
    enabled: bool
    last_sent_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.NotificationSetting) -> "NotificationSetting":
        return cls(
            id=instance.id,
            company_id=instance.company_id,
            event_type=instance.event_type,
            email_enabled=instance.email_enabled or False,
            push_enabled=instance.push_enabled or False,
            email_template=instance.email_template,
            recipients=json.dumps(instance.recipients) if instance.recipients else None,
            interval_minutes=instance.interval_minutes or 60,
            enabled=instance.enabled or True,
            last_sent_at=instance.last_sent_at,
            created_at=instance.created_at,
            updated_at=instance.updated_at
        )


@strawberry.type
class OfficeLocation:
    latitude: Optional[float]
    longitude: Optional[float]
    radius: Optional[int]
    entry_enabled: Optional[bool] = False
    exit_enabled: Optional[bool] = False

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

@strawberry.type
class WeeklySummary:
    start_date: datetime.date
    end_date: datetime.date
    total_regular_hours: Decimal
    total_overtime_hours: Decimal
    target_hours: Decimal
    debt_hours: Decimal
    surplus_hours: Decimal # Overtime + Extra Regular (if any)
    status_message: str

@strawberry.type
class Bonus:
    id: int
    user_id: int
    amount: Decimal
    date: datetime.date
    description: Optional[str]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.Bonus) -> "Bonus":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            amount=instance.amount,
            date=instance.date,
            description=instance.description,
        )

@strawberry.type
class MonthlyWorkDays:
    id: int
    year: int
    month: int
    days_count: int

    @classmethod
    def from_instance(cls, instance: models.MonthlyWorkDays) -> "MonthlyWorkDays":
        return cls(
            id=instance.id,
            year=instance.year,
            month=instance.month,
            days_count=instance.days_count,
        )

@strawberry.type
class AdvancePayment:
    id: int
    user_id: int
    amount: Decimal
    payment_date: datetime.date
    description: Optional[str]
    is_processed: bool
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.AdvancePayment) -> "AdvancePayment":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            amount=instance.amount,
            payment_date=instance.payment_date,
            description=instance.description,
            is_processed=instance.is_processed,
            created_at=instance.created_at
        )

@strawberry.type
class ServiceLoan:
    id: int
    user_id: int
    total_amount: Decimal
    installment_amount: Decimal
    remaining_amount: Decimal
    installments_count: int
    installments_paid: int
    start_date: datetime.date
    description: Optional[str]
    is_active: bool
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.ServiceLoan) -> "ServiceLoan":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            total_amount=instance.total_amount,
            installment_amount=instance.installment_amount,
            remaining_amount=instance.remaining_amount,
            installments_count=instance.installments_count,
            installments_paid=instance.installments_paid,
            start_date=instance.start_date,
            description=instance.description,
            is_active=instance.is_active,
            created_at=instance.created_at
        )

@strawberry.type
class DailyStat:
    date: datetime.date
    total_worked_hours: float
    regular_hours: float
    overtime_hours: float
    is_work_day: bool
    shift_name: Optional[str]
    actual_arrival: Optional[datetime.datetime] = None
    actual_departure: Optional[datetime.datetime] = None

@strawberry.type
class AuditLog:
    id: int
    user_id: Optional[int]
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    details: Optional[str]
    created_at: datetime.datetime

    @strawberry.field
    async def user(self, info: strawberry.Info) -> Optional[User]:
        if not self.user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.AuditLog) -> "AuditLog":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            action=instance.action,
            target_type=instance.target_type,
            target_id=instance.target_id,
            details=instance.details,
            created_at=instance.created_at
        )

@strawberry.type
class ShiftSwapRequest:
    id: int
    requestor_id: int
    target_user_id: int
    requestor_schedule_id: int
    target_schedule_id: int
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @strawberry.field
    async def requestor(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.requestor_id)

    @strawberry.field
    async def target_user(self, info: strawberry.Info) -> User:
        return await info.context["dataloaders"]["user_by_id"].load(self.target_user_id)

    @strawberry.field
    async def requestor_schedule(self, info: strawberry.Info) -> WorkSchedule:
        db = info.context["db"]
        from backend import crud
        res = await db.get(models.WorkSchedule, self.requestor_schedule_id)
        return WorkSchedule.from_instance(res)

    @strawberry.field
    async def target_schedule(self, info: strawberry.Info) -> WorkSchedule:
        db = info.context["db"]
        res = await db.get(models.WorkSchedule, self.target_schedule_id)
        return WorkSchedule.from_instance(res)

    @classmethod
    def from_instance(cls, instance: models.ShiftSwapRequest) -> "ShiftSwapRequest":
        return cls(
            id=instance.id,
            requestor_id=instance.requestor_id,
            target_user_id=instance.target_user_id,
            requestor_schedule_id=instance.requestor_schedule_id,
            target_schedule_id=instance.target_schedule_id,
            status=instance.status,
            created_at=instance.created_at,
            updated_at=instance.updated_at
        )

@strawberry.type
class OvertimeStat:
    month: str # e.g. "2026-01"
    amount: Decimal

@strawberry.type
class LatenessStat:
    user_name: str
    count: int

@strawberry.type
class ManagementStats:
    overtime_by_month: List[OvertimeStat]
    lateness_by_user: List[LatenessStat]

@strawberry.type
class ScheduleTemplateItem:
    id: int
    day_index: int
    shift_id: Optional[int]
    
    @strawberry.field
    async def shift(self, info: strawberry.Info) -> Optional[Shift]:
        if not self.shift_id: return None
        db = info.context["db"]
        from backend.database.models import Shift as DbShift
        res = await db.get(DbShift, self.shift_id)
        return Shift.from_instance(res)

@strawberry.type
class ScheduleTemplate:
    id: int
    company_id: int
    name: str
    description: Optional[str]
    created_at: datetime.datetime

    @strawberry.field
    async def items(self, info: strawberry.Info) -> List[ScheduleTemplateItem]:
        db = info.context["db"]
        from backend.database.models import ScheduleTemplateItem as DbItem
        stmt = select(DbItem).where(DbItem.template_id == self.id).order_by(DbItem.day_index)
        res = await db.execute(stmt)
        items = res.scalars().all()
        return [
            ScheduleTemplateItem(id=i.id, day_index=i.day_index, shift_id=i.shift_id)
            for i in items
        ]

    @classmethod
    def from_instance(cls, instance: models.ScheduleTemplate) -> "ScheduleTemplate":
        return cls(
            id=instance.id,
            company_id=instance.company_id,
            name=instance.name,
            description=instance.description,
            created_at=instance.created_at
        )

@strawberry.type
class DepartmentForecast:
    department_name: str
    amount: float

@strawberry.type
class PayrollForecast:
    total_amount: float
    by_department: List[DepartmentForecast]

@strawberry.type
class APIKey:
    id: int
    name: str
    key_prefix: str
    permissions: List[str]
    is_active: bool
    created_at: datetime.datetime
    last_used_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.APIKey) -> "APIKey":
        return cls(
            id=instance.id,
            name=instance.name,
            key_prefix=instance.key_prefix,
            permissions=instance.permissions,
            is_active=instance.is_active,
            created_at=instance.created_at,
            last_used_at=instance.last_used_at
        )

@strawberry.type
class APIKeyWithSecret:
    key_info: APIKey
    raw_key: str # The secret, only shown once

@strawberry.type
class Webhook:
    id: int
    url: str
    description: Optional[str]
    events: List[str]
    is_active: bool
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.Webhook) -> "Webhook":
        return cls(
            id=instance.id,
            url=instance.url,
            description=instance.description,
            events=instance.events,
            is_active=instance.is_active,
            created_at=instance.created_at
        )

@strawberry.type
class GlobalSetting:
    key: str
    value: str

    @classmethod
    def from_instance(cls, instance: models.GlobalSetting) -> "GlobalSetting":
        return cls(
            key=instance.key,
            value=instance.value
        )

@strawberry.type
class Module:
    id: int
    code: str
    is_enabled: bool
    name: str
    description: Optional[str]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.Module) -> "Module":
        return cls(
            id=instance.id,
            code=instance.code,
            is_enabled=instance.is_enabled,
            name=instance.name,
            description=instance.description,
            updated_at=instance.updated_at
        )

@strawberry.type
class PasswordSettings:
    min_length: int
    max_length: int
    require_upper: bool
    require_lower: bool
    require_digit: bool
    require_special: bool

# --- Confectionery Module GraphQL Types ---

@strawberry.type
class StorageZone:
    id: int
    name: str
    temp_min: Optional[float]
    temp_max: Optional[float]
    description: Optional[str]
    company_id: int
    is_active: bool
    asset_type: str
    zone_type: str

    @classmethod
    def from_instance(cls, instance: models.StorageZone) -> "StorageZone":
        return cls(
            id=instance.id,
            name=instance.name,
            temp_min=instance.temp_min,
            temp_max=instance.temp_max,
            description=instance.description,
            company_id=instance.company_id,
            is_active=instance.is_active if instance.is_active is not None else True,
            asset_type=instance.asset_type or "KMA",
            zone_type=instance.zone_type or "food"
        )

@strawberry.type
class Supplier:
    id: int
    name: str
    eik: Optional[str]
    vat_number: Optional[str]
    address: Optional[str]
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    company_id: int

    @classmethod
    def from_instance(cls, instance: models.Supplier) -> "Supplier":
        return cls(
            id=instance.id,
            name=instance.name,
            eik=instance.eik,
            vat_number=instance.vat_number,
            address=instance.address,
            contact_person=instance.contact_person,
            phone=instance.phone,
            email=instance.email,
            company_id=instance.company_id
        )

@strawberry.type
class Ingredient:
    id: int
    name: str
    unit: str
    barcode: Optional[str]
    baseline_min_stock: Decimal
    current_price: Optional[Decimal]
    storage_zone_id: Optional[int]
    is_perishable: bool
    expiry_warning_days: int
    allergens: List[str]
    company_id: int
    product_type: str

    @strawberry.field
    async def storage_zone(self, info: strawberry.Info) -> Optional[StorageZone]:
        if not self.storage_zone_id: return None
        result = await info.context["dataloaders"]["storage_zone_by_id"].load(self.storage_zone_id)
        return StorageZone.from_instance(result) if result else None

    @strawberry.field
    async def current_stock(self, info: strawberry.Info) -> Decimal:
        db = info.context["db"]
        stmt = select(models.Batch).where(
            models.Batch.ingredient_id == self.id,
            models.Batch.status == "active"
        )
        res = await db.execute(stmt)
        batches = res.scalars().all()
        return sum((b.quantity for b in batches), Decimal("0"))

    @classmethod
    def from_instance(cls, instance: models.Ingredient) -> "Ingredient":
        return cls(
            id=instance.id,
            name=instance.name,
            unit=instance.unit,
            barcode=instance.barcode,
            baseline_min_stock=instance.baseline_min_stock,
            current_price=instance.current_price,
            storage_zone_id=instance.storage_zone_id,
            is_perishable=instance.is_perishable,
            expiry_warning_days=instance.expiry_warning_days,
            allergens=instance.allergens or [],
            company_id=instance.company_id,
            product_type=instance.product_type or "raw"
        )

@strawberry.type
class Batch:
    id: int
    ingredient_id: int
    batch_number: Optional[str]
    quantity: Decimal
    expiry_date: datetime.date
    status: str
    received_at: datetime.datetime
    supplier_id: Optional[int]
    invoice_number: Optional[str]
    storage_zone_id: Optional[int]

    @strawberry.field
    def available_stock(self) -> Decimal:
        """Returns quantity only for active batches with positive stock"""
        if self.status == "active" and self.quantity > 0:
            return self.quantity
        return Decimal("0")

    @strawberry.field
    def is_expired(self) -> bool:
        """Check if batch is expired"""
        return datetime.date.today() > self.expiry_date

    @strawberry.field
    def days_until_expiry(self) -> int:
        """Days until expiry (negative if expired)"""
        delta = self.expiry_date - datetime.date.today()
        return delta.days

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> Ingredient:
        result = await info.context["dataloaders"]["ingredient_by_id"].load(self.ingredient_id)
        return Ingredient.from_instance(result)

    @strawberry.field
    async def supplier(self, info: strawberry.Info) -> Optional[Supplier]:
        if not self.supplier_id: return None
        result = await info.context["dataloaders"]["supplier_by_id"].load(self.supplier_id)
        return Supplier.from_instance(result) if result else None

    @strawberry.field
    async def storage_zone(self, info: strawberry.Info) -> Optional[StorageZone]:
        if not self.storage_zone_id: return None
        result = await info.context["dataloaders"]["storage_zone_by_id"].load(self.storage_zone_id)
        return StorageZone.from_instance(result) if result else None

    @classmethod
    def from_instance(cls, instance: models.Batch) -> "Batch":
        return cls(
            id=instance.id,
            ingredient_id=instance.ingredient_id,
            batch_number=instance.batch_number,
            quantity=instance.quantity,
            expiry_date=instance.expiry_date,
            status=instance.status,
            received_at=instance.received_at,
            supplier_id=instance.supplier_id,
            invoice_number=instance.invoice_number,
            storage_zone_id=instance.storage_zone_id
        )

@strawberry.type
class StockConsumptionLog:
    id: int
    ingredient_id: int
    batch_id: int
    quantity: Decimal
    reason: str
    production_order_id: Optional[int]
    notes: Optional[str]
    created_by: int
    created_at: datetime.datetime

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> "Ingredient":
        result = await info.context["dataloaders"]["ingredient_by_id"].load(self.ingredient_id)
        return Ingredient.from_instance(result)

    @strawberry.field
    async def batch(self, info: strawberry.Info) -> "Batch":
        result = await info.context["dataloaders"]["batch_by_id"].load(self.batch_id)
        return Batch.from_instance(result)

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> "User":
        result = await info.context["dataloaders"]["user_by_id"].load(self.created_by)
        return User.from_instance(result)

    @classmethod
    def from_instance(cls, instance: models.StockConsumptionLog) -> "StockConsumptionLog":
        return cls(
            id=instance.id,
            ingredient_id=instance.ingredient_id,
            batch_id=instance.batch_id,
            quantity=instance.quantity,
            reason=instance.reason,
            production_order_id=instance.production_order_id,
            notes=instance.notes,
            created_by=instance.created_by,
            created_at=instance.created_at,
        )

@strawberry.type
class FefoSuggestion:
    batch_id: int
    batch_number: str
    available_quantity: Decimal
    quantity_to_take: Decimal
    expiry_date: datetime.date
    days_until_expiry: int

@strawberry.type
class RecipeIngredient:
    id: int
    recipe_id: int
    section_id: Optional[int]
    ingredient_id: int
    workstation_id: Optional[int]
    quantity_gross: Decimal
    quantity_net: Decimal
    waste_percentage: Decimal

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> Ingredient:
        result = await info.context["dataloaders"]["ingredient_by_id"].load(self.ingredient_id)
        return Ingredient.from_instance(result)

    @strawberry.field
    async def workstation(self, info: strawberry.Info) -> Optional["Workstation"]:
        if not self.workstation_id:
            return None
        db = info.context["db"]
        res = await db.get(models.Workstation, self.workstation_id)
        return Workstation.from_instance(res)

    @classmethod
    def from_instance(cls, instance: models.RecipeIngredient) -> "RecipeIngredient":
        return cls(
            id=instance.id,
            section_id=instance.section_id,
            recipe_id=instance.recipe_id,
            ingredient_id=instance.ingredient_id,
            workstation_id=instance.workstation_id,
            quantity_gross=instance.quantity_gross,
            quantity_net=instance.quantity_net,
            waste_percentage=Decimal(instance.waste_percentage or 0),
        )

@strawberry.type
class RecipeSection:
    id: int
    recipe_id: int
    section_type: str
    name: str
    shelf_life_days: Optional[int]
    waste_percentage: float
    section_order: int

    @strawberry.field
    async def ingredients(self, info: strawberry.Info) -> List[RecipeIngredient]:
        try:
            db = info.context["db"]
            stmt = select(models.RecipeIngredient).where(models.RecipeIngredient.section_id == self.id)
            res = await db.execute(stmt)
            return [RecipeIngredient.from_instance(i) for i in res.scalars().all()]
        except Exception as e:
            print(f"Error loading ingredients for section {self.id}: {e}")
            return []

    @strawberry.field
    async def steps(self, info: strawberry.Info) -> List["RecipeStep"]:
        db = info.context["db"]
        stmt = select(models.RecipeStep).where(models.RecipeStep.section_id == self.id).order_by(models.RecipeStep.step_order)
        res = await db.execute(stmt)
        return [RecipeStep.from_instance(s) for s in res.scalars().all()]

    @classmethod
    def from_instance(cls, instance: models.RecipeSection) -> "RecipeSection":
        return cls(
            id=instance.id,
            recipe_id=instance.recipe_id,
            section_type=instance.section_type,
            name=instance.name,
            shelf_life_days=instance.shelf_life_days,
            waste_percentage=float(instance.waste_percentage or 0),
            section_order=instance.section_order or 0
        )

@strawberry.type
class RecipeStep:
    id: int
    section_id: Optional[int]
    recipe_id: Optional[int]
    workstation_id: int
    name: str
    step_order: int
    estimated_duration_minutes: Optional[int]

    @strawberry.field
    async def workstation(self, info: strawberry.Info) -> "Workstation":
        db = info.context["db"]
        res = await db.get(models.Workstation, self.workstation_id)
        return Workstation.from_instance(res)

    @classmethod
    def from_instance(cls, instance: models.RecipeStep) -> "RecipeStep":
        return cls(
            id=instance.id,
            section_id=instance.section_id,
            recipe_id=instance.recipe_id,
            workstation_id=instance.workstation_id,
            name=instance.name,
            step_order=instance.step_order or 0,
            estimated_duration_minutes=instance.estimated_duration_minutes
        )

@strawberry.type
class Recipe:
    id: int
    name: str
    category: Optional[str]
    description: Optional[str]
    yield_quantity: Decimal
    yield_unit: str
    shelf_life_days: int
    shelf_life_frozen_days: int
    default_pieces: int
    production_time_days: int
    production_deadline_days: Optional[int]
    standard_quantity: Decimal
    instructions: Optional[str]
    company_id: int
    
    # PRICING FIELDS
    selling_price: Optional[Decimal]
    cost_price: Optional[Decimal]
    markup_percentage: Decimal
    premium_amount: Decimal
    portions: int
    last_price_update: Optional[datetime.datetime]
    price_calculated_at: Optional[datetime.datetime]

    @strawberry.field
    def markup_amount(self) -> Decimal:
        """Изчислена стойност на маржа в лв"""
        if not self.cost_price or not self.markup_percentage or self.markup_percentage == 0:
            return Decimal("0")
        return self.cost_price * self.markup_percentage / 100

    @strawberry.field
    def final_price(self) -> Decimal:
        """Крайна продажна цена"""
        base = self.cost_price or Decimal("0")
        markup = Decimal("0")
        if self.cost_price and self.markup_percentage and self.markup_percentage != 0:
            markup = self.cost_price * self.markup_percentage / 100
        premium = self.premium_amount or Decimal("0")
        return base + markup + premium

    @strawberry.field
    def portion_price(self) -> Optional[Decimal]:
        """Цена за 1 бр. парче"""
        if not self.default_pieces or self.default_pieces <= 0:
            return None
        base = self.cost_price or Decimal("0")
        markup = Decimal("0")
        if self.cost_price and self.markup_percentage and self.markup_percentage != 0:
            markup = self.cost_price * self.markup_percentage / 100
        premium = self.premium_amount or Decimal("0")
        return (base + markup + premium) / self.default_pieces  if self.default_pieces and self.default_pieces > 0 else None

    @strawberry.field
    async def sections(self, info: strawberry.Info) -> List[RecipeSection]:
        db = info.context["db"]
        stmt = select(models.RecipeSection).where(
            models.RecipeSection.recipe_id == self.id
        ).order_by(models.RecipeSection.section_order)
        res = await db.execute(stmt)
        return [RecipeSection.from_instance(s) for s in res.scalars().all()]

    @strawberry.field
    async def ingredients(self, info: strawberry.Info) -> List[RecipeIngredient]:
        db = info.context["db"]
        stmt = select(models.RecipeIngredient).where(models.RecipeIngredient.recipe_id == self.id)
        res = await db.execute(stmt)
        return [RecipeIngredient.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def steps(self, info: strawberry.Info) -> List[RecipeStep]:
        db = info.context["db"]
        stmt = select(models.RecipeStep).where(models.RecipeStep.recipe_id == self.id).order_by(models.RecipeStep.step_order)
        res = await db.execute(stmt)
        return [RecipeStep.from_instance(s) for s in res.scalars().all()]

    @classmethod
    def from_instance(cls, instance: models.Recipe) -> "Recipe":
        return cls(
            id=instance.id,
            name=instance.name,
            category=instance.category,
            description=instance.description,
            yield_quantity=instance.yield_quantity or Decimal("1.0"),
            yield_unit=instance.yield_unit or "br",
            shelf_life_days=instance.shelf_life_days or 7,
            shelf_life_frozen_days=instance.shelf_life_frozen_days or 30,
            default_pieces=instance.default_pieces or 12,
            production_time_days=instance.production_time_days or 1,
            production_deadline_days=instance.production_deadline_days,
            standard_quantity=instance.standard_quantity or Decimal("1.0"),
            instructions=instance.instructions,
            company_id=instance.company_id,
            # PRICING
            selling_price=instance.selling_price,
            cost_price=instance.cost_price,
            markup_percentage=instance.markup_percentage or Decimal("0"),
            premium_amount=instance.premium_amount or Decimal("0"),
            portions=instance.portions or 1,
            last_price_update=instance.last_price_update,
            price_calculated_at=instance.price_calculated_at
        )


@strawberry.type
class PriceHistory:
    id: int
    recipe_id: int
    old_price: Optional[Decimal]
    new_price: Optional[Decimal]
    old_cost: Optional[Decimal]
    new_cost: Optional[Decimal]
    old_markup: Optional[Decimal]
    new_markup: Optional[Decimal]
    old_premium: Optional[Decimal]
    new_premium: Optional[Decimal]
    changed_by: int
    changed_at: datetime.datetime
    reason: Optional[str]

    @strawberry.field
    async def recipe(self, info: strawberry.Info) -> Optional[Recipe]:
        result = await info.context["dataloaders"]["recipe_by_id"].load(self.recipe_id)
        return Recipe.from_instance(result) if result else None

    @strawberry.field
    async def user(self, info: strawberry.Info) -> Optional[User]:
        result = await info.context["dataloaders"]["user_by_id"].load(self.changed_by)
        return User.from_instance(result) if result else None

    @classmethod
    def from_instance(cls, instance: models.PriceHistory) -> "PriceHistory":
        return cls(
            id=instance.id,
            recipe_id=instance.recipe_id,
            old_price=instance.old_price,
            new_price=instance.new_price,
            old_cost=instance.old_cost,
            new_cost=instance.new_cost,
            old_markup=instance.old_markup,
            new_markup=instance.new_markup,
            old_premium=instance.old_premium,
            new_premium=instance.new_premium,
            changed_by=instance.changed_by,
            changed_at=instance.changed_at,
            reason=instance.reason
        )


@strawberry.type
class RecipeCostResult:
    recipe_id: int
    recipe_name: str
    cost_price: Decimal
    markup_amount: Decimal
    premium_amount: Decimal
    final_price: Decimal
    portion_price: Decimal


@strawberry.type
class RecalculateResult:
    recipe_id: int
    recipe_name: str
    cost_price: Decimal
    markup_amount: Decimal
    final_price: Decimal
    portion_price: Decimal


@strawberry.type
class Workstation:
    id: int
    name: str
    description: Optional[str]
    company_id: int

    @classmethod
    def from_instance(cls, instance: models.Workstation) -> "Workstation":
        return cls(
            id=instance.id,
            name=instance.name,
            description=instance.description,
            company_id=instance.company_id
        )

@strawberry.type
class ProductionTask:
    id: int
    order_id: int
    workstation_id: int
    step_id: Optional[int]
    name: str
    status: str
    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]
    assigned_user_id: Optional[int]

    @strawberry.field
    async def workstation(self, info: strawberry.Info) -> Workstation:
        db = info.context["db"]
        res = await db.get(models.Workstation, self.workstation_id)
        return Workstation.from_instance(res)

    @strawberry.field
    async def assigned_user(self, info: strawberry.Info) -> Optional[User]:
        if not self.assigned_user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.assigned_user_id)

    @classmethod
    def from_instance(cls, instance: models.ProductionTask) -> "ProductionTask":
        return cls(
            id=instance.id,
            order_id=instance.order_id,
            workstation_id=instance.workstation_id,
            step_id=instance.step_id,
            name=instance.name,
            status=instance.status,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            assigned_user_id=instance.assigned_user_id
        )


@strawberry.type
class ProductionScrapLog:
    id: int
    task_id: int
    user_id: int
    quantity: Decimal
    reason: Optional[str]
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.ProductionScrapLog) -> "ProductionScrapLog":
        return cls(
            id=instance.id,
            task_id=instance.task_id,
            user_id=instance.user_id,
            quantity=instance.quantity,
            reason=instance.reason,
            created_at=instance.created_at
        )


@strawberry.type
class TerminalTask:
    id: int
    name: str
    quantity: int
    status: str

    @classmethod
    def from_instance(cls, instance: models.ProductionTask, order_quantity: int) -> "TerminalTask":
        return cls(
            id=instance.id,
            name=instance.name,
            quantity=order_quantity,
            status=instance.status
        )


@strawberry.type
class TerminalOrder:
    id: int
    order_number: str
    product_name: str
    quantity: int
    status: str
    recipe_name: str
    instructions: Optional[str]
    tasks: List[TerminalTask]

    @classmethod
    def from_instance(cls, instance: models.ProductionOrder, recipe_name: str, instructions: Optional[str], tasks: List[TerminalTask]) -> "TerminalOrder":
        return cls(
            id=instance.id,
            order_number=str(instance.id),
            product_name=recipe_name,
            quantity=int(instance.quantity) if instance.quantity else 0,
            status=instance.status,
            recipe_name=recipe_name,
            instructions=instructions,
            tasks=tasks
        )


@strawberry.type
class ProductionOrder:
    id: int
    recipe_id: int
    quantity: Decimal
    due_date: datetime.datetime
    production_deadline: Optional[datetime.datetime]
    status: str
    notes: Optional[str]
    created_at: datetime.datetime
    created_by: Optional[int]
    company_id: int
    confirmed_at: Optional[datetime.datetime]
    confirmed_by: Optional[int]

    @strawberry.field
    async def recipe(self, info: strawberry.Info) -> Recipe:
        db = info.context["db"]
        res = await db.get(models.Recipe, self.recipe_id)
        return Recipe.from_instance(res)

    @strawberry.field
    async def tasks(self, info: strawberry.Info) -> List[ProductionTask]:
        db = info.context["db"]
        stmt = select(models.ProductionTask).where(models.ProductionTask.order_id == self.id)
        res = await db.execute(stmt)
        return [ProductionTask.from_instance(t) for t in res.scalars().all()]

    @classmethod
    def from_instance(cls, instance: models.ProductionOrder) -> "ProductionOrder":
        return cls(
            id=instance.id,
            recipe_id=instance.recipe_id,
            quantity=instance.quantity,
            due_date=instance.due_date,
            production_deadline=instance.production_deadline,
            status=instance.status,
            notes=instance.notes,
            created_at=instance.created_at,
            created_by=instance.created_by,
            company_id=instance.company_id,
            confirmed_at=instance.confirmed_at,
            confirmed_by=instance.confirmed_by
        )

@strawberry.type
class LabelData:
    product_name: str
    batch_number: str
    production_date: datetime.datetime
    expiry_date: datetime.date
    allergens: List[str]
    storage_conditions: Optional[str]
    qr_code_content: str
    quantity: str


@strawberry.type
class ProductionRecordIngredient:
    id: int
    ingredient_id: int
    ingredient_name: Optional[str]
    batch_number: str
    expiry_date: Optional[datetime.date]
    quantity_used: Decimal
    unit: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.ProductionRecordIngredient) -> "ProductionRecordIngredient":
        return cls(
            id=instance.id,
            ingredient_id=instance.ingredient_id,
            ingredient_name=instance.ingredient.name if instance.ingredient else None,
            batch_number=instance.batch_number,
            expiry_date=instance.expiry_date,
            quantity_used=instance.quantity_used,
            unit=instance.unit
        )


@strawberry.type
class ProductionRecordWorker:
    id: int
    user_id: int
    user_name: Optional[str]
    workstation_id: Optional[int]
    workstation_name: Optional[str]
    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.ProductionRecordWorker) -> "ProductionRecordWorker":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            user_name=instance.user.full_name if instance.user else None,
            workstation_id=instance.workstation_id,
            workstation_name=instance.workstation.name if instance.workstation else None,
            started_at=instance.started_at,
            completed_at=instance.completed_at
        )


@strawberry.type
class ProductionRecord:
    id: int
    order_id: int
    confirmed_by: Optional[int]
    confirmed_at: Optional[datetime.datetime]
    expiry_date: Optional[datetime.date]
    notes: Optional[str]
    created_at: datetime.datetime

    @strawberry.field
    async def ingredients(self, info: strawberry.Info) -> List[ProductionRecordIngredient]:
        from sqlalchemy.orm import selectinload
        db = info.context["db"]
        stmt = select(models.ProductionRecordIngredient).options(
            selectinload(models.ProductionRecordIngredient.ingredient)
        ).where(models.ProductionRecordIngredient.record_id == self.id)
        res = await db.execute(stmt)
        return [ProductionRecordIngredient.from_instance(t) for t in res.scalars().all()]

    @strawberry.field
    async def workers(self, info: strawberry.Info) -> List[ProductionRecordWorker]:
        from sqlalchemy.orm import selectinload
        db = info.context["db"]
        stmt = select(models.ProductionRecordWorker).options(
            selectinload(models.ProductionRecordWorker.user),
            selectinload(models.ProductionRecordWorker.workstation)
        ).where(models.ProductionRecordWorker.record_id == self.id)
        res = await db.execute(stmt)
        return [ProductionRecordWorker.from_instance(t) for t in res.scalars().all()]

    @classmethod
    def from_instance(cls, instance: models.ProductionRecord) -> "ProductionRecord":
        return cls(
            id=instance.id,
            order_id=instance.order_id,
            confirmed_by=instance.confirmed_by,
            confirmed_at=instance.confirmed_at,
            expiry_date=instance.expiry_date,
            notes=instance.notes,
            created_at=instance.created_at
        )


@strawberry.type
class InventoryItem:
    id: int
    session_id: int
    ingredient_id: int
    ingredient_name: Optional[str]
    ingredient_unit: Optional[str]
    found_quantity: Optional[Decimal]
    system_quantity: Optional[Decimal]
    difference: Optional[Decimal]
    adjusted: bool

    @classmethod
    def from_instance(cls, instance: models.InventoryItem) -> "InventoryItem":
        return cls(
            id=instance.id,
            session_id=instance.session_id,
            ingredient_id=instance.ingredient_id,
            ingredient_name=instance.ingredient.name if instance.ingredient else None,
            ingredient_unit=instance.ingredient.unit if instance.ingredient else None,
            found_quantity=instance.found_quantity,
            system_quantity=instance.system_quantity,
            difference=instance.difference,
            adjusted=instance.adjusted
        )


@strawberry.type
class InventorySession:
    id: int
    company_id: int
    started_by: Optional[int]
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime]
    status: str
    protocol_number: Optional[str]
    notes: Optional[str]

    @strawberry.field
    async def items(self, info: strawberry.Info) -> List[InventoryItem]:
        from sqlalchemy.orm import selectinload
        db = info.context["db"]
        stmt = select(models.InventoryItem).options(
            selectinload(models.InventoryItem.ingredient)
        ).where(models.InventoryItem.session_id == self.id)
        res = await db.execute(stmt)
        return [InventoryItem.from_instance(t) for t in res.scalars().all()]

    @classmethod
    def from_instance(cls, instance: models.InventorySession) -> "InventorySession":
        return cls(
            id=instance.id,
            company_id=instance.company_id,
            started_by=instance.started_by,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            status=instance.status,
            protocol_number=instance.protocol_number,
            notes=instance.notes
        )


@strawberry.type
class InvoiceItem:
    id: int
    invoice_id: int
    ingredient_id: Optional[int]
    batch_id: Optional[int]
    name: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    unit_price_with_vat: Optional[Decimal]
    discount_percent: Decimal
    total: Decimal
    expiration_date: Optional[datetime.date]
    batch_number: Optional[str]

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> Optional[Ingredient]:
        if not self.ingredient_id: return None
        db = info.context["db"]
        res = await db.get(models.Ingredient, self.ingredient_id)
        return Ingredient.from_instance(res) if res else None

    @strawberry.field
    async def batch(self, info: strawberry.Info) -> Optional[Batch]:
        if not self.batch_id: return None
        db = info.context["db"]
        res = await db.get(models.Batch, self.batch_id)
        return Batch.from_instance(res) if res else None

    @classmethod
    def from_instance(cls, instance: models.InvoiceItem) -> "InvoiceItem":
        return cls(
            id=instance.id,
            invoice_id=instance.invoice_id,
            ingredient_id=instance.ingredient_id,
            batch_id=instance.batch_id,
            name=instance.name,
            quantity=instance.quantity,
            unit=instance.unit or "br",
            unit_price=instance.unit_price,
            unit_price_with_vat=instance.unit_price_with_vat,
            discount_percent=instance.discount_percent or Decimal("0"),
            total=instance.total,
            expiration_date=instance.expiration_date,
            batch_number=instance.batch_number
        )


@strawberry.type
class Invoice:
    id: int
    number: str
    type: str
    date: datetime.date
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    status: str
    company_id: int
    created_at: datetime.datetime
    document_type: Optional[str] = "ФАКТУРА"
    griff: Optional[str] = "ОРИГИНАЛ"
    description: Optional[str] = None
    supplier_id: Optional[int] = None
    batch_id: Optional[int] = None
    client_name: Optional[str] = None
    client_eik: Optional[str] = None
    client_address: Optional[str] = None
    payment_method: Optional[str] = None
    delivery_method: Optional[str] = "Доставка до адрес"
    due_date: Optional[datetime.date] = None
    payment_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None

    @strawberry.field
    async def supplier(self, info: strawberry.Info) -> Optional[Supplier]:
        if not self.supplier_id: return None
        result = await info.context["dataloaders"]["supplier_by_id"].load(self.supplier_id)
        return Supplier.from_instance(result) if result else None

    @strawberry.field
    async def batch(self, info: strawberry.Info) -> Optional[Batch]:
        if not self.batch_id: return None
        result = await info.context["dataloaders"]["batch_by_id"].load(self.batch_id)
        return Batch.from_instance(result) if result else None

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Optional[Company]:
        result = await info.context["dataloaders"]["company_by_id"].load(self.company_id)
        return Company.from_instance(result) if result else None

    @strawberry.field
    async def items(self, info: strawberry.Info) -> List[InvoiceItem]:
        results = await info.context["dataloaders"]["invoice_items_by_invoice_id"].load(self.id)
        return [InvoiceItem.from_instance(t) for t in results]

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> Optional[User]:
        if not self.created_by: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.created_by)

    @classmethod
    def from_instance(cls, instance: models.Invoice) -> "Invoice":
        return cls(
            id=instance.id,
            number=instance.number,
            type=instance.type,
            document_type=instance.document_type,
            griff=instance.griff,
            description=instance.description,
            date=instance.date,
            supplier_id=instance.supplier_id,
            batch_id=instance.batch_id,
            client_name=instance.client_name,
            client_eik=instance.client_eik,
            client_address=instance.client_address,
            subtotal=instance.subtotal or Decimal("0"),
            discount_percent=instance.discount_percent or Decimal("0"),
            discount_amount=instance.discount_amount or Decimal("0"),
            vat_rate=instance.vat_rate or Decimal("20.0"),
            vat_amount=instance.vat_amount or Decimal("0"),
            total=instance.total or Decimal("0"),
            payment_method=instance.payment_method,
            delivery_method=instance.delivery_method,
            due_date=instance.due_date,
            payment_date=instance.payment_date,
            status=instance.status or "draft",
            notes=instance.notes,
            company_id=instance.company_id,
            created_by=instance.created_by,
            created_at=instance.created_at
        )

@strawberry.type
class CashJournalEntryType:
    id: int
    date: Optional[str]
    operation_type: str
    amount: float
    description: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[int]
    created_at: Optional[str]
    created_by: Optional[int]

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> Optional["User"]:
        if not self.created_by: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.created_by)

    @classmethod
    def from_instance(cls, instance: models.CashJournalEntry) -> "CashJournalEntryType":
        return cls(
            id=instance.id,
            date=instance.date.isoformat() if instance.date else None,
            operation_type=instance.operation_type,
            amount=float(instance.amount) if instance.amount else 0,
            description=instance.description,
            reference_type=instance.reference_type,
            reference_id=instance.reference_id,
            created_at=instance.created_at.isoformat() if instance.created_at else None,
            created_by=instance.created_by,
        )


@strawberry.type
class OperationLogType:
    id: int
    timestamp: Optional[str]
    operation: str
    entity_type: str
    entity_id: int
    changes: Optional[str]
    user_id: Optional[int]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> Optional["User"]:
        if not self.user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.OperationLog) -> "OperationLogType":
        changes_str = json.dumps(instance.changes) if instance.changes else None
        return cls(
            id=instance.id,
            timestamp=instance.timestamp.isoformat() if instance.timestamp else None,
            operation=instance.operation,
            entity_type=instance.entity_type,
            entity_id=instance.entity_id,
            changes=changes_str,
            user_id=instance.user_id,
        )


@strawberry.type
class DailySummaryType:
    id: int
    date: Optional[str]
    invoices_count: int
    incoming_invoices_count: int
    outgoing_invoices_count: int
    invoices_total: float
    incoming_invoices_total: float
    outgoing_invoices_total: float
    cash_income: float
    cash_expense: float
    cash_balance: float
    vat_collected: float
    vat_paid: float
    paid_invoices_count: int
    unpaid_invoices_count: int
    overdue_invoices_count: int

    @classmethod
    def from_instance(cls, instance: models.DailySummary) -> "DailySummaryType":
        return cls(
            id=instance.id,
            date=instance.datetime.date.isoformat() if instance.date else None,
            invoices_count=instance.invoices_count or 0,
            incoming_invoices_count=instance.incoming_invoices_count or 0,
            outgoing_invoices_count=instance.outgoing_invoices_count or 0,
            invoices_total=float(instance.invoices_total) if instance.invoices_total else 0,
            incoming_invoices_total=float(instance.incoming_invoices_total) if instance.incoming_invoices_total else 0,
            outgoing_invoices_total=float(instance.outgoing_invoices_total) if instance.outgoing_invoices_total else 0,
            cash_income=float(instance.cash_income) if instance.cash_income else 0,
            cash_expense=float(instance.cash_expense) if instance.cash_expense else 0,
            cash_balance=float(instance.cash_balance) if instance.cash_balance else 0,
            vat_collected=float(instance.vat_collected) if instance.vat_collected else 0,
            vat_paid=float(instance.vat_paid) if instance.vat_paid else 0,
            paid_invoices_count=instance.paid_invoices_count or 0,
            unpaid_invoices_count=instance.unpaid_invoices_count or 0,
            overdue_invoices_count=instance.overdue_invoices_count or 0,
        )


@strawberry.type
class MonthlySummaryType:
    id: int
    year: int
    month: int
    invoices_count: int
    incoming_invoices_count: int
    outgoing_invoices_count: int
    invoices_total: float
    incoming_invoices_total: float
    outgoing_invoices_total: float
    cash_income: float
    cash_expense: float
    cash_balance: float
    vat_collected: float
    vat_paid: float
    paid_invoices_count: int
    unpaid_invoices_count: int
    overdue_invoices_count: int

    @classmethod
    def from_instance(cls, instance: models.MonthlySummary) -> "MonthlySummaryType":
        return cls(
            id=instance.id,
            year=instance.year,
            month=instance.month,
            invoices_count=instance.invoices_count or 0,
            incoming_invoices_count=instance.incoming_invoices_count or 0,
            outgoing_invoices_count=instance.outgoing_invoices_count or 0,
            invoices_total=float(instance.invoices_total) if instance.invoices_total else 0,
            incoming_invoices_total=float(instance.incoming_invoices_total) if instance.incoming_invoices_total else 0,
            outgoing_invoices_total=float(instance.outgoing_invoices_total) if instance.outgoing_invoices_total else 0,
            cash_income=float(instance.cash_income) if instance.cash_income else 0,
            cash_expense=float(instance.cash_expense) if instance.cash_expense else 0,
            cash_balance=float(instance.cash_balance) if instance.cash_balance else 0,
            vat_collected=float(instance.vat_collected) if instance.vat_collected else 0,
            vat_paid=float(instance.vat_paid) if instance.vat_paid else 0,
            paid_invoices_count=instance.paid_invoices_count or 0,
            unpaid_invoices_count=instance.unpaid_invoices_count or 0,
            overdue_invoices_count=instance.overdue_invoices_count or 0,
        )


@strawberry.type
class YearlySummaryType:
    id: int
    year: int
    invoices_count: int
    incoming_invoices_count: int
    outgoing_invoices_count: int
    invoices_total: float
    incoming_invoices_total: float
    outgoing_invoices_total: float
    cash_income: float
    cash_expense: float
    cash_balance: float
    vat_collected: float
    vat_paid: float
    paid_invoices_count: int
    unpaid_invoices_count: int
    overdue_invoices_count: int

    @classmethod
    def from_instance(cls, instance: models.YearlySummary) -> "YearlySummaryType":
        return cls(
            id=instance.id,
            year=instance.year,
            invoices_count=instance.invoices_count or 0,
            incoming_invoices_count=instance.incoming_invoices_count or 0,
            outgoing_invoices_count=instance.outgoing_invoices_count or 0,
            invoices_total=float(instance.invoices_total) if instance.invoices_total else 0,
            incoming_invoices_total=float(instance.incoming_invoices_total) if instance.incoming_invoices_total else 0,
            outgoing_invoices_total=float(instance.outgoing_invoices_total) if instance.outgoing_invoices_total else 0,
            cash_income=float(instance.cash_income) if instance.cash_income else 0,
            cash_expense=float(instance.cash_expense) if instance.cash_expense else 0,
            cash_balance=float(instance.cash_balance) if instance.cash_balance else 0,
            vat_collected=float(instance.vat_collected) if instance.vat_collected else 0,
            vat_paid=float(instance.vat_paid) if instance.vat_paid else 0,
            paid_invoices_count=instance.paid_invoices_count or 0,
            unpaid_invoices_count=instance.unpaid_invoices_count or 0,
            overdue_invoices_count=instance.overdue_invoices_count or 0,
        )


# ============== SAF-T AND ACCOUNTING TYPES ==============

@strawberry.type
class SAFTValidationResult:
    status: str
    errors: List[str]
    warnings: List[str]
    is_valid: bool


@strawberry.type
class SAFTFileResult:
    xml_content: str
    validation_result: SAFTValidationResult
    period_start: datetime.date
    period_end: datetime.date
    file_size: int
    file_name: str


@strawberry.type
class ProformaInvoice:
    id: int
    number: str
    type: str = "proforma"
    date: datetime.date
    client_name: Optional[str]
    client_eik: Optional[str]
    client_address: Optional[str]
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    status: str
    notes: Optional[str]
    company_id: int
    created_by: Optional[int]
    created_at: datetime.datetime
    # Missing fields (identical to Invoice)
    document_type: Optional[str] = "ПРОФОРМА"
    griff: Optional[str] = "ОРИГИНАЛ"
    description: Optional[str] = None
    payment_method: Optional[str] = None
    delivery_method: Optional[str] = "Доставка до адрес"
    due_date: Optional[datetime.date] = None
    payment_date: Optional[datetime.date] = None

    @strawberry.field
    async def items(self, info: strawberry.Info) -> List[InvoiceItem]:
        results = await info.context["dataloaders"]["invoice_items_by_invoice_id"].load(self.id)
        return [InvoiceItem.from_instance(t) for t in results]

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Optional[Company]:
        result = await info.context["dataloaders"]["company_by_id"].load(self.company_id)
        return Company.from_instance(result) if result else None

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> Optional[User]:
        if not self.created_by: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.created_by)

    @classmethod
    def from_instance(cls, instance: models.Invoice) -> "ProformaInvoice":
        return cls(
            id=instance.id,
            number=instance.number,
            type=instance.type or "proforma",
            date=instance.date,
            client_name=instance.client_name,
            client_eik=instance.client_eik,
            client_address=instance.client_address,
            subtotal=instance.subtotal or Decimal("0"),
            discount_percent=instance.discount_percent or Decimal("0"),
            discount_amount=instance.discount_amount or Decimal("0"),
            vat_rate=instance.vat_rate or Decimal("20.0"),
            vat_amount=instance.vat_amount or Decimal("0"),
            total=instance.total or Decimal("0"),
            status=instance.status or "proforma",
            notes=instance.notes,
            company_id=instance.company_id,
            created_by=instance.created_by,
            created_at=instance.created_at,
            document_type=instance.document_type or "ПРОФОРМА",
            griff=instance.griff or "ОРИГИНАЛ",
            description=instance.description,
            payment_method=instance.payment_method,
            delivery_method=instance.delivery_method or "Доставка до адрес",
            due_date=instance.due_date,
            payment_date=instance.payment_date
        )


@strawberry.type
class InvoiceCorrection:
    id: int
    number: str
    type: str
    date: datetime.date
    original_invoice_id: Optional[int]
    client_name: Optional[str]
    client_eik: Optional[str]
    reason: Optional[str]
    subtotal: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    status: str
    company_id: int
    created_by: Optional[int]
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.InvoiceCorrection) -> "InvoiceCorrection":
        # Accessing original_invoice relationship - must be eager loaded with selectinload
        orig = instance.original_invoice
        return cls(
            id=instance.id,
            number=instance.number,
            type=instance.type,
            date=instance.date,
            original_invoice_id=instance.original_invoice_id,
            client_name=orig.client_name if orig else None,
            client_eik=orig.client_eik if orig else None,
            reason=instance.reason,
            subtotal=instance.amount_diff or Decimal("0"),
            vat_rate=orig.vat_rate if orig else Decimal("20.0"),
            vat_amount=instance.vat_diff or Decimal("0"),
            total=(instance.amount_diff or Decimal("0")) + (instance.vat_diff or Decimal("0")),
            status=instance.status or "draft",
            company_id=instance.company_id,
            created_by=instance.created_by,
            created_at=instance.created_at
        )


@strawberry.type
class CashReceipt:
    id: int
    receipt_number: str
    date: datetime.date
    payment_type: str
    amount: Decimal
    vat_amount: Decimal
    items_json: Optional[str]
    fiscal_printer_id: Optional[str]
    company_id: int
    created_by: Optional[int]
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.CashReceipt) -> "CashReceipt":
        return cls(
            id=instance.id,
            receipt_number=instance.receipt_number,
            date=instance.date,
            payment_type=instance.payment_type or "cash",
            amount=instance.amount or Decimal("0"),
            vat_amount=instance.vat_amount or Decimal("0"),
            items_json=instance.items_json,
            fiscal_printer_id=getattr(instance, 'fiscal_printer_id', None),
            company_id=instance.company_id,
            created_by=instance.created_by,
            created_at=instance.created_at
        )


@strawberry.type
class BankAccount:
    id: int
    company_id: int
    iban: str
    bic: Optional[str]
    bank_name: str
    account_type: str
    is_default: bool
    currency: str
    is_active: bool
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.BankAccount) -> "BankAccount":
        return cls(
            id=instance.id,
            company_id=instance.company_id,
            iban=instance.iban,
            bic=instance.bic,
            bank_name=instance.bank_name,
            account_type=instance.account_type or "current",
            is_default=instance.is_default or False,
            currency=instance.currency or "BGN",
            is_active=instance.is_active if instance.is_active is not None else True,
            created_at=instance.created_at
        )


@strawberry.type
class BankTransaction:
    id: int
    bank_account_id: int
    date: datetime.date
    amount: Decimal
    type: str
    description: Optional[str]
    reference: Optional[str]
    invoice_id: Optional[int]
    matched: bool
    company_id: int
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.BankTransaction) -> "BankTransaction":
        return cls(
            id=instance.id,
            bank_account_id=instance.bank_account_id,
            date=instance.date,
            amount=instance.amount or Decimal("0"),
            type=instance.type or "credit",
            description=instance.description,
            reference=instance.reference,
            invoice_id=instance.invoice_id,
            matched=instance.matched or False,
            company_id=instance.company_id,
            created_at=instance.created_at
        )


@strawberry.type
class Account:
    id: int
    code: str
    name: str
    type: str
    parent_id: Optional[int]
    company_id: int
    opening_balance: Decimal
    closing_balance: Decimal

    @classmethod
    def from_instance(cls, instance: models.Account) -> "Account":
        return cls(
            id=instance.id,
            code=instance.code,
            name=instance.name,
            type=instance.type or "expense",
            parent_id=instance.parent_id,
            company_id=instance.company_id,
            opening_balance=instance.opening_balance or Decimal("0"),
            closing_balance=getattr(instance, 'closing_balance', Decimal("0"))
        )


@strawberry.type
class AutoMatchResult:
    matched_count: int
    unmatched_count: int


@strawberry.type
class AccountingEntry:
    id: int
    date: datetime.date
    entry_number: str
    description: Optional[str]
    debit_account_id: int
    credit_account_id: int
    amount: Decimal
    vat_amount: Decimal
    invoice_id: Optional[int]
    bank_transaction_id: Optional[int]
    cash_journal_id: Optional[int]
    company_id: int
    created_by: Optional[int]
    created_at: datetime.datetime

    @strawberry.field
    async def debit_account(self, info: strawberry.Info) -> Optional[Account]:
        if not self.debit_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.debit_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def credit_account(self, info: strawberry.Info) -> Optional[Account]:
        if not self.credit_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.credit_account_id)
        return Account.from_instance(result) if result else None

    @strawberry.field
    async def invoice(self, info: strawberry.Info) -> Optional["Invoice"]:
        if not self.invoice_id:
            return None
        from backend.database.models import Invoice as DbInvoice
        db = info.context["db"]
        result = await db.get(DbInvoice, self.invoice_id)
        return Invoice.from_instance(result) if result else None

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> Optional["User"]:
        if not self.created_by:
            return None
        result = await info.context["dataloaders"]["user_by_id"].load(self.created_by)
        return User.from_instance(result) if result else None

    @classmethod
    def from_instance(cls, instance: models.AccountingEntry) -> "AccountingEntry":
        return cls(
            id=instance.id,
            date=instance.date,
            entry_number=instance.entry_number,
            description=instance.description,
            debit_account_id=instance.debit_account_id,
            credit_account_id=instance.credit_account_id,
            amount=instance.amount or Decimal("0"),
            vat_amount=instance.vat_amount or Decimal("0"),
            invoice_id=instance.invoice_id,
            bank_transaction_id=instance.bank_transaction_id,
            cash_journal_id=instance.cash_journal_id,
            company_id=instance.company_id,
            created_by=instance.created_by,
            created_at=instance.created_at
        )


@strawberry.type
class VATRegister:
    id: int
    company_id: int
    period_month: int
    period_year: int
    vat_collected_20: Decimal
    vat_collected_9: Decimal
    vat_collected_0: Decimal
    vat_paid_20: Decimal
    vat_paid_9: Decimal
    vat_paid_0: Decimal
    vat_adjustment: Decimal
    vat_due: Decimal
    vat_credit: Decimal
    created_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance: models.VATRegister) -> "VATRegister":
        return cls(
            id=instance.id,
            company_id=instance.company_id,
            period_month=instance.period_month,
            period_year=instance.period_year,
            vat_collected_20=instance.vat_collected_20 or Decimal("0"),
            vat_collected_9=instance.vat_collected_9 or Decimal("0"),
            vat_collected_0=instance.vat_collected_0 or Decimal("0"),
            vat_paid_20=instance.vat_paid_20 or Decimal("0"),
            vat_paid_9=instance.vat_paid_9 or Decimal("0"),
            vat_paid_0=instance.vat_paid_0 or Decimal("0"),
            vat_adjustment=instance.vat_adjustment or Decimal("0"),
            vat_due=instance.vat_due or Decimal("0"),
            vat_credit=instance.vat_credit or Decimal("0"),
            created_at=instance.created_at
        )


@strawberry.type
class Gateway:
    id: int
    name: str
    hardware_uuid: str
    alias: Optional[str]
    ip_address: Optional[str]
    local_hostname: Optional[str]
    terminal_port: int
    web_port: int
    is_active: bool
    last_heartbeat: Optional[datetime.datetime]
    registered_at: datetime.datetime
    company_id: Optional[int]

    @classmethod
    def from_instance(cls, instance: models.Gateway) -> "Gateway":
        return cls(
            id=instance.id,
            name=instance.name,
            hardware_uuid=instance.hardware_uuid,
            alias=instance.alias,
            ip_address=instance.ip_address,
            local_hostname=instance.local_hostname,
            terminal_port=instance.terminal_port or 8080,
            web_port=instance.web_port or 8888,
            is_active=instance.is_active,
            last_heartbeat=instance.last_heartbeat,
            registered_at=instance.registered_at,
            company_id=instance.company_id
        )


@strawberry.type
class Terminal:
    id: int
    hardware_uuid: str
    device_name: Optional[str]
    device_type: Optional[str]
    device_model: Optional[str]
    os_version: Optional[str]
    gateway_id: Optional[int]
    is_active: bool
    last_seen: Optional[datetime.datetime]
    total_scans: int
    alias: Optional[str]
    mode: str

    @classmethod
    def from_instance(cls, instance: models.Terminal) -> "Terminal":
        return cls(
            id=instance.id,
            hardware_uuid=instance.hardware_uuid,
            device_name=instance.device_name,
            device_type=instance.device_type,
            device_model=instance.device_model,
            os_version=instance.os_version,
            gateway_id=instance.gateway_id,
            is_active=instance.is_active,
            last_seen=instance.last_seen,
            total_scans=instance.total_scans or 0,
            alias=instance.alias,
            mode=instance.mode or "both"
        )


@strawberry.type
class Printer:
    id: int
    name: str
    printer_type: Optional[str]
    ip_address: Optional[str]
    port: int
    protocol: Optional[str]
    windows_share_name: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    gateway_id: int
    is_active: bool
    is_default: bool
    last_test: Optional[datetime.datetime]
    last_error: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.Printer) -> "Printer":
        return cls(
            id=instance.id,
            name=instance.name,
            printer_type=instance.printer_type,
            ip_address=instance.ip_address,
            port=instance.port or 9100,
            protocol=instance.protocol,
            windows_share_name=instance.windows_share_name,
            manufacturer=instance.manufacturer,
            model=instance.model,
            gateway_id=instance.gateway_id,
            is_active=instance.is_active,
            is_default=instance.is_default,
            last_test=instance.last_test,
            last_error=instance.last_error
        )


@strawberry.type
class GatewayStats:
    total_gateways: int
    active_gateways: int
    inactive_gateways: int
    total_terminals: int
    active_terminals: int
    total_printers: int
    active_printers: int

@strawberry.type
class AccessZone:
    id: int
    zone_id: str
    name: str
    level: int
    depends_on: List[str]
    required_hours_start: str
    required_hours_end: str
    anti_passback_enabled: bool
    anti_passback_type: str
    anti_passback_timeout: int
    description: Optional[str]
    is_active: bool

    @strawberry.field
    async def authorized_users(self, info: strawberry.Info) -> List["User"]:
        db = info.context["db"]
        from backend.database.models import AccessZone as DbZone
        stmt = select(DbZone).where(DbZone.id == self.id).options(selectinload(DbZone.authorized_users))
        res = await db.execute(stmt)
        zone = res.scalar_one_or_none()
        return [User.from_instance(u) for u in zone.authorized_users] if zone else []

    @classmethod
    def from_instance(cls, instance: models.AccessZone) -> "AccessZone":
        return cls(
            id=instance.id,
            zone_id=instance.zone_id,
            name=instance.name,
            level=instance.level,
            depends_on=instance.depends_on or [],
            required_hours_start=instance.required_hours_start,
            required_hours_end=instance.required_hours_end,
            anti_passback_enabled=instance.anti_passback_enabled,
            anti_passback_type=instance.anti_passback_type,
            anti_passback_timeout=instance.anti_passback_timeout,
            description=instance.description,
            is_active=instance.is_active,
        )

@strawberry.type
class AccessDoor:
    id: int
    door_id: str
    name: str
    zone_db_id: int
    gateway_id: int
    device_id: str
    relay_number: int
    terminal_id: Optional[str]
    terminal_mode: Optional[str] = "access"
    description: Optional[str]
    is_active: bool
    is_online: bool
    last_check: Optional[datetime.datetime]

    @strawberry.field
    async def zone(self, info: strawberry.Info) -> Optional[AccessZone]:
        db = info.context["db"]
        res = await db.get(models.AccessZone, self.zone_db_id)
        return AccessZone.from_instance(res) if res else None

    @strawberry.field
    async def gateway(self, info: strawberry.Info) -> Optional[Gateway]:
        db = info.context["db"]
        res = await db.get(models.Gateway, self.gateway_id)
        return Gateway.from_instance(res) if res else None

    @classmethod
    def from_instance(cls, instance: models.AccessDoor) -> "AccessDoor":
        return cls(
            id=instance.id,
            door_id=instance.door_id,
            name=instance.name,
            zone_db_id=instance.zone_db_id,
            gateway_id=instance.gateway_id,
            device_id=instance.device_id,
            relay_number=instance.relay_number,
            terminal_id=instance.terminal_id,
            terminal_mode=instance.terminal_mode or "access",
            description=instance.description,
            is_active=instance.is_active,
            is_online=instance.is_online or False,
            last_check=instance.last_check,
        )

@strawberry.type
class AccessCode:
    id: int
    code: str
    code_type: str
    zones: List[str]
    uses_remaining: int
    expires_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    last_used_at: Optional[datetime.datetime]
    is_active: bool
    gateway_id: Optional[int]

    @classmethod
    def from_instance(cls, instance: models.AccessCode) -> "AccessCode":
        return cls(
            id=instance.id,
            code=instance.code,
            code_type=instance.code_type,
            zones=instance.zones or [],
            uses_remaining=instance.uses_remaining,
            expires_at=instance.expires_at,
            created_at=instance.created_at,
            last_used_at=instance.last_used_at,
            is_active=instance.is_active,
            gateway_id=instance.gateway_id,
        )

@strawberry.type
class AccessLog:
    id: int
    timestamp: datetime.datetime
    user_id: Optional[str]
    user_name: Optional[str]
    zone_id: Optional[str]
    zone_name: Optional[str]
    door_id: Optional[str]
    door_name: Optional[str]
    action: str
    result: str
    reason: Optional[str]
    method: str
    terminal_id: Optional[str]
    gateway_id: int

    @classmethod
    def from_instance(cls, instance: models.AccessLog) -> "AccessLog":
        return cls(
            id=instance.id,
            timestamp=instance.timestamp,
            user_id=instance.user_id,
            user_name=instance.user_name,
            zone_id=instance.zone_id,
            zone_name=instance.zone_name,
            door_id=instance.door_id,
            door_name=instance.door_name,
            action=instance.action,
            result=instance.result,
            reason=instance.reason,
            method=instance.method,
            terminal_id=instance.terminal_id,
            gateway_id=instance.gateway_id,
        )


# ============================================================
# LOGISTICS TYPES
# ============================================================

@strawberry.enum
class PurchaseRequestStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FULFILLED = "fulfilled"


@strawberry.enum
class PurchaseRequestPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@strawberry.enum
class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"


@strawberry.enum
class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@strawberry.type
class SupplierExtended:
    id: int
    name: str
    eik: Optional[str]
    vat_number: Optional[str]
    mol: Optional[str]
    address: Optional[str]
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    is_active: Optional[bool]
    notes: Optional[str]
    company_id: int
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.Supplier) -> "SupplierExtended":
        return cls(
            id=instance.id,
            name=instance.name,
            eik=instance.eik,
            vat_number=instance.vat_number,
            mol=instance.mol,
            address=instance.address,
            contact_person=instance.contact_person,
            phone=instance.phone,
            email=instance.email,
            is_active=instance.is_active,
            notes=instance.notes,
            company_id=instance.company_id,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class RequestTemplate:
    id: int
    name: str
    items: Optional[JSONScalar] = None
    default_department_id: Optional[int]
    notes: Optional[str]
    company_id: int
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.RequestTemplate) -> "RequestTemplate":
        return cls(
            id=instance.id,
            name=instance.name,
            items=instance.items,
            default_department_id=instance.default_department_id,
            notes=instance.notes,
            company_id=instance.company_id,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class PurchaseRequestItem:
    id: int
    purchase_request_id: int
    item_name: str
    quantity: float
    unit: Optional[str]
    notes: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.PurchaseRequestItem) -> "PurchaseRequestItem":
        return cls(
            id=instance.id,
            purchase_request_id=instance.purchase_request_id,
            item_name=instance.item_name,
            quantity=float(instance.quantity),
            unit=instance.unit,
            notes=instance.notes,
        )


@strawberry.type
class PurchaseRequestApproval:
    id: int
    request_id: int
    action: str
    user_id: int
    action_date: Optional[datetime.datetime]
    reason: Optional[str]
    is_auto: Optional[bool]

    @classmethod
    def from_instance(cls, instance: models.PurchaseRequestApproval) -> "PurchaseRequestApproval":
        return cls(
            id=instance.id,
            request_id=instance.request_id,
            action=instance.action,
            user_id=instance.user_id,
            action_date=instance.action_date,
            reason=instance.reason,
            is_auto=instance.is_auto,
        )


@strawberry.type
class PurchaseRequest:
    id: int
    request_number: str
    requested_by_id: int
    department_id: Optional[int]
    status: PurchaseRequestStatus
    priority: PurchaseRequestPriority
    reason: Optional[str]
    due_date: Optional[datetime.date]
    approved_by_id: Optional[int]
    approved_at: Optional[datetime.datetime]
    is_auto: Optional[bool]
    notes: Optional[str]
    company_id: int
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    items: Optional[JSONScalar] = None
    approvals: Optional[JSONScalar] = None

    @classmethod
    def from_instance(cls, instance: models.PurchaseRequest) -> "PurchaseRequest":
        return cls(
            id=instance.id,
            request_number=instance.request_number,
            requested_by_id=instance.requested_by_id,
            department_id=instance.department_id,
            status=PurchaseRequestStatus(instance.status),
            priority=PurchaseRequestPriority(instance.priority),
            reason=instance.reason,
            due_date=instance.due_date,
            approved_by_id=instance.approved_by_id,
            approved_at=instance.approved_at,
            is_auto=instance.is_auto,
            notes=instance.notes,
            company_id=instance.company_id,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class PurchaseOrderItem:
    id: int
    purchase_order_id: int
    item_name: str
    quantity: float
    received_quantity: Optional[float]
    unit_price: Optional[float]
    vat_rate: Optional[float]
    unit: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.PurchaseOrderItem) -> "PurchaseOrderItem":
        return cls(
            id=instance.id,
            purchase_order_id=instance.purchase_order_id,
            item_name=instance.item_name,
            quantity=float(instance.quantity),
            received_quantity=float(instance.received_quantity) if instance.received_quantity else None,
            unit_price=float(instance.unit_price) if instance.unit_price else None,
            vat_rate=float(instance.vat_rate) if instance.vat_rate else None,
            unit=instance.unit,
        )


@strawberry.type
class PurchaseOrder:
    id: int
    order_number: str
    supplier_id: int
    purchase_request_id: Optional[int]
    status: PurchaseOrderStatus
    order_date: Optional[datetime.date]
    expected_date: Optional[datetime.date]
    received_date: Optional[datetime.date]
    total_amount: Optional[float]
    vat_amount: Optional[float]
    notes: Optional[str]
    company_id: int
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.PurchaseOrder) -> "PurchaseOrder":
        return cls(
            id=instance.id,
            order_number=instance.order_number,
            supplier_id=instance.supplier_id,
            purchase_request_id=instance.purchase_request_id,
            status=PurchaseOrderStatus(instance.status),
            order_date=instance.order_date,
            expected_date=instance.expected_date,
            received_date=instance.received_date,
            total_amount=float(instance.total_amount) if instance.total_amount else None,
            vat_amount=float(instance.vat_amount) if instance.vat_amount else None,
            notes=instance.notes,
            company_id=instance.company_id,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class Delivery:
    id: int
    delivery_number: str
    purchase_order_id: Optional[int]
    vehicle_id: Optional[int]
    driver_id: Optional[int]
    status: DeliveryStatus
    shipped_date: Optional[datetime.datetime]
    delivery_date: Optional[datetime.datetime]
    tracking_number: Optional[str]
    notes: Optional[str]
    company_id: int
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.Delivery) -> "Delivery":
        return cls(
            id=instance.id,
            delivery_number=instance.delivery_number,
            purchase_order_id=instance.purchase_order_id,
            vehicle_id=instance.vehicle_id,
            driver_id=instance.driver_id,
            status=DeliveryStatus(instance.status),
            shipped_date=instance.shipped_date,
            delivery_date=instance.delivery_date,
            tracking_number=instance.tracking_number,
            notes=instance.notes,
            company_id=instance.company_id,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


# ============================================================
# FLEET TYPES
# ============================================================

@strawberry.enum
class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    IN_REPAIR = "in_repair"
    OUT_OF_SERVICE = "out_of_service"
    SOLD = "sold"


@strawberry.enum
class FuelType(str, enum.Enum):
    BENZIN = "benzin"
    DIZEL = "dizel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    LNG = "lng"
    CNG = "cng"


@strawberry.enum
class VehicleDocumentType(str, enum.Enum):
    INVOICE = "invoice"
    POLICY = "policy"
    INSPECTION = "inspection"
    CONTRACT = "contract"
    OTHER = "other"


@strawberry.enum
class InsuranceType(str, enum.Enum):
    CIVIL = "civil"
    KASKO = "kasko"
    BORDER = "border"


@strawberry.enum
class InspectionResult(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"


@strawberry.enum
class PreTripStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"


@strawberry.enum
class ExpenseType(str, enum.Enum):
    FUEL = "fuel"
    REPAIR = "repair"
    INSURANCE = "insurance"
    INSPECTION = "inspection"
    VIGNETTE = "vignette"
    TOLL = "toll"
    TAX = "tax"
    OTHER = "other"


@strawberry.type
class VehicleType:
    id: int
    name: str
    code: Optional[str]

    @classmethod
    def from_instance(cls, instance: models.VehicleType) -> "VehicleType":
        return cls(
            id=instance.id,
            name=instance.name,
            code=instance.code,
        )


@strawberry.type
class Vehicle:
    id: int
    registration_number: str
    vin: Optional[str]
    make: str
    model: str
    year: Optional[int]
    vehicle_type_id: Optional[int]
    fuel_type: FuelType
    engine_number: Optional[str]
    chassis_number: Optional[str]
    color: Optional[str]
    initial_mileage: Optional[int]
    is_company: Optional[bool]
    owner_name: Optional[str]
    status: VehicleStatus
    notes: Optional[str]
    company_id: int
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.Vehicle) -> "Vehicle":
        return cls(
            id=instance.id,
            registration_number=instance.registration_number,
            vin=instance.vin,
            make=instance.make,
            model=instance.model,
            year=instance.year,
            vehicle_type_id=instance.vehicle_type_id,
            fuel_type=FuelType(instance.fuel_type) if instance.fuel_type else FuelType.DIZEL,
            engine_number=instance.engine_number,
            chassis_number=instance.chassis_number,
            color=instance.color,
            initial_mileage=instance.initial_mileage,
            is_company=instance.is_company,
            owner_name=instance.owner_name,
            status=VehicleStatus(instance.status) if instance.status else VehicleStatus.ACTIVE,
            notes=instance.notes,
            company_id=instance.company_id,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class VehicleDocument:
    id: int
    vehicle_id: int
    document_type: VehicleDocumentType
    title: str
    file_url: Optional[str]
    issue_date: Optional[datetime.date]
    expiry_date: Optional[datetime.date]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleDocument) -> "VehicleDocument":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            document_type=VehicleDocumentType(instance.document_type),
            title=instance.title,
            file_url=instance.file_url,
            issue_date=instance.issue_date,
            expiry_date=instance.expiry_date,
            notes=instance.notes,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleFuelCard:
    id: int
    vehicle_id: int
    card_number: str
    provider: Optional[str]
    pin: Optional[str]
    limit: Optional[float]
    is_active: Optional[bool]
    expiry_date: Optional[datetime.date]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleFuelCard) -> "VehicleFuelCard":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            card_number=instance.card_number,
            provider=instance.provider,
            pin=instance.pin,
            limit=float(instance.limit) if instance.limit else None,
            is_active=instance.is_active,
            expiry_date=instance.expiry_date,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleVignette:
    id: int
    vehicle_id: int
    vignette_type: str
    purchase_date: Optional[datetime.date]
    valid_from: Optional[datetime.date]
    valid_until: Optional[datetime.date]
    price: Optional[float]
    provider: Optional[str]
    document_url: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleVignette) -> "VehicleVignette":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            vignette_type=instance.vignette_type,
            purchase_date=instance.purchase_date,
            valid_from=instance.valid_from,
            valid_until=instance.valid_until,
            price=float(instance.price) if instance.price else None,
            provider=instance.provider,
            document_url=instance.document_url,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleToll:
    id: int
    vehicle_id: int
    route: Optional[str]
    toll_amount: float
    toll_date: Optional[datetime.datetime]
    section: Optional[str]
    document_url: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleToll) -> "VehicleToll":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            route=instance.route,
            toll_amount=float(instance.toll_amount),
            toll_date=instance.toll_date,
            section=instance.section,
            document_url=instance.document_url,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleMileage:
    id: int
    vehicle_id: int
    date: datetime.date
    mileage: int
    source: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleMileage) -> "VehicleMileage":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            date=instance.date,
            mileage=instance.mileage,
            source=instance.source,
            notes=instance.notes,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleFuel:
    id: int
    vehicle_id: int
    date: datetime.datetime
    fuel_type: Optional[str]
    quantity: float
    price_per_liter: float
    total_amount: float
    mileage: Optional[int]
    location: Optional[str]
    invoice_number: Optional[str]
    fuel_card_id: Optional[int]
    driver_id: Optional[int]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleFuel) -> "VehicleFuel":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            date=instance.date,
            fuel_type=instance.fuel_type,
            quantity=float(instance.quantity),
            price_per_liter=float(instance.price_per_liter),
            total_amount=float(instance.total_amount),
            mileage=instance.mileage,
            location=instance.location,
            invoice_number=instance.invoice_number,
            fuel_card_id=instance.fuel_card_id,
            driver_id=instance.driver_id,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleService:
    id: int
    name: str
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    contact_person: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleService) -> "VehicleService":
        return cls(
            id=instance.id,
            name=instance.name,
            address=instance.address,
            phone=instance.phone,
            email=instance.email,
            contact_person=instance.contact_person,
            notes=instance.notes,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleRepair:
    id: int
    vehicle_id: int
    repair_date: datetime.datetime
    repair_type: Optional[str]
    description: Optional[str]
    parts: Optional[JSONScalar] = None
    labor_hours: Optional[float]
    labor_cost: Optional[float]
    parts_cost: Optional[float]
    total_cost: Optional[float]
    mileage: Optional[int]
    vehicle_service_id: Optional[int]
    warranty_months: Optional[int]
    next_service_km: Optional[int]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleRepair) -> "VehicleRepair":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            repair_date=instance.repair_date,
            repair_type=instance.repair_type,
            description=instance.description,
            parts=instance.parts,
            labor_hours=float(instance.labor_hours) if instance.labor_hours else None,
            labor_cost=float(instance.labor_cost) if instance.labor_cost else None,
            parts_cost=float(instance.parts_cost) if instance.parts_cost else None,
            total_cost=float(instance.total_cost) if instance.total_cost else None,
            mileage=instance.mileage,
            vehicle_service_id=instance.vehicle_service_id,
            warranty_months=instance.warranty_months,
            next_service_km=instance.next_service_km,
            notes=instance.notes,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleSchedule:
    id: int
    vehicle_id: int
    schedule_type: str
    interval_km: Optional[int]
    interval_months: Optional[int]
    last_service_date: Optional[datetime.date]
    last_service_km: Optional[int]
    next_service_date: Optional[datetime.date]
    next_service_km: Optional[int]
    vehicle_service_id: Optional[int]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleSchedule) -> "VehicleSchedule":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            schedule_type=instance.schedule_type,
            interval_km=instance.interval_km,
            interval_months=instance.interval_months,
            last_service_date=instance.last_service_date,
            last_service_km=instance.last_service_km,
            next_service_date=instance.next_service_date,
            next_service_km=instance.next_service_km,
            vehicle_service_id=instance.vehicle_service_id,
            notes=instance.notes,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class VehicleInsurance:
    id: int
    vehicle_id: int
    insurance_type: InsuranceType
    policy_number: str
    insurance_company: Optional[str]
    start_date: datetime.date
    end_date: datetime.date
    premium: Optional[float]
    coverage_amount: Optional[float]
    payment_type: Optional[str]
    document_url: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleInsurance) -> "VehicleInsurance":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            insurance_type=InsuranceType(instance.insurance_type),
            policy_number=instance.policy_number,
            insurance_company=instance.insurance_company,
            start_date=instance.start_date,
            end_date=instance.end_date,
            premium=float(instance.premium) if instance.premium else None,
            coverage_amount=float(instance.coverage_amount) if instance.coverage_amount else None,
            payment_type=instance.payment_type,
            document_url=instance.document_url,
            notes=instance.notes,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleInspection:
    id: int
    vehicle_id: int
    inspection_date: datetime.date
    valid_until: datetime.date
    result: InspectionResult
    mileage: Optional[int]
    inspector: Optional[str]
    certificate_number: Optional[str]
    next_inspection_date: Optional[datetime.date]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleInspection) -> "VehicleInspection":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            inspection_date=instance.inspection_date,
            valid_until=instance.valid_until,
            result=InspectionResult(instance.result) if instance.result else InspectionResult.PENDING,
            mileage=instance.mileage,
            inspector=instance.inspector,
            certificate_number=instance.certificate_number,
            next_inspection_date=instance.next_inspection_date,
            notes=instance.notes,
            created_at=instance.created_at,
        )


@strawberry.type
class VehiclePreTripInspection:
    id: int
    vehicle_id: int
    driver_id: int
    inspection_date: Optional[datetime.datetime]
    tires_condition: Optional[bool]
    tires_pressure: Optional[bool]
    tires_tread: Optional[bool]
    brakes_condition: Optional[bool]
    brakes_parking: Optional[bool]
    lights_headlights: Optional[bool]
    lights_brake: Optional[bool]
    lights_turn: Optional[bool]
    lights_warning: Optional[bool]
    fluids_oil: Optional[bool]
    fluids_coolant: Optional[bool]
    fluids_washer: Optional[bool]
    fluids_brake: Optional[bool]
    mirrors: Optional[bool]
    wipers: Optional[bool]
    horn: Optional[bool]
    seatbelts: Optional[bool]
    first_aid_kit: Optional[bool]
    fire_extinguisher: Optional[bool]
    warning_triangle: Optional[bool]
    overall_status: PreTripStatus
    notes: Optional[str]
    photos: Optional[JSONScalar] = None
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehiclePreTripInspection) -> "VehiclePreTripInspection":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            driver_id=instance.driver_id,
            inspection_date=instance.inspection_date,
            tires_condition=instance.tires_condition,
            tires_pressure=instance.tires_pressure,
            tires_tread=instance.tires_tread,
            brakes_condition=instance.brakes_condition,
            brakes_parking=instance.brakes_parking,
            lights_headlights=instance.lights_headlights,
            lights_brake=instance.lights_brake,
            lights_turn=instance.lights_turn,
            lights_warning=instance.lights_warning,
            fluids_oil=instance.fluids_oil,
            fluids_coolant=instance.fluids_coolant,
            fluids_washer=instance.fluids_washer,
            fluids_brake=instance.fluids_brake,
            mirrors=instance.mirrors,
            wipers=instance.wipers,
            horn=instance.horn,
            seatbelts=instance.seatbelts,
            first_aid_kit=instance.first_aid_kit,
            fire_extinguisher=instance.fire_extinguisher,
            warning_triangle=instance.warning_triangle,
            overall_status=PreTripStatus(instance.overall_status) if instance.overall_status else PreTripStatus.FAILED,
            notes=instance.notes,
            photos=instance.photos,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleDriver:
    id: int
    vehicle_id: int
    user_id: int
    assigned_from: datetime.date
    assigned_to: Optional[datetime.date]
    is_primary: Optional[bool]
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleDriver) -> "VehicleDriver":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            user_id=instance.user_id,
            assigned_from=instance.assigned_from,
            assigned_to=instance.assigned_to,
            is_primary=instance.is_primary,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleTrip:
    id: int
    vehicle_id: int
    driver_id: int
    delivery_id: Optional[int]
    start_address: Optional[str]
    end_address: Optional[str]
    start_time: Optional[datetime.datetime]
    end_time: Optional[datetime.datetime]
    distance_km: Optional[int]
    purpose: Optional[str]
    expenses: Optional[float]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleTrip) -> "VehicleTrip":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            driver_id=instance.driver_id,
            delivery_id=instance.delivery_id,
            start_address=instance.start_address,
            end_address=instance.end_address,
            start_time=instance.start_time,
            end_time=instance.end_time,
            distance_km=instance.distance_km,
            purpose=instance.purpose,
            expenses=float(instance.expenses) if instance.expenses else None,
            notes=instance.notes,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class VehicleCostCenter:
    id: int
    name: str
    department_id: Optional[int]
    is_active: Optional[bool]
    company_id: int
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleCostCenter) -> "VehicleCostCenter":
        return cls(
            id=instance.id,
            name=instance.name,
            department_id=instance.department_id,
            is_active=instance.is_active,
            company_id=instance.company_id,
            created_at=instance.created_at,
        )


@strawberry.type
class VehicleExpense:
    id: int
    vehicle_id: int
    expense_type: ExpenseType
    expense_date: datetime.date
    amount: Optional[float]
    vat_amount: Optional[float]
    total_amount: Optional[float]
    description: Optional[str]
    reference_id: Optional[int]
    reference_type: Optional[str]
    is_deductible: Optional[bool]
    cost_center_id: Optional[int]
    company_id: int
    created_at: Optional[datetime.datetime]

    @classmethod
    def from_instance(cls, instance: models.VehicleExpense) -> "VehicleExpense":
        return cls(
            id=instance.id,
            vehicle_id=instance.vehicle_id,
            expense_type=ExpenseType(instance.expense_type),
            expense_date=instance.expense_date,
            amount=float(instance.amount) if instance.amount else None,
            vat_amount=float(instance.vat_amount) if instance.vat_amount else None,
            total_amount=float(instance.total_amount) if instance.total_amount else None,
            description=instance.description,
            reference_id=instance.reference_id,
            reference_type=instance.reference_type,
            is_deductible=instance.is_deductible,
            cost_center_id=instance.cost_center_id,
            company_id=instance.company_id,
            created_at=instance.created_at,
        )


# ==================== ТРЗ Types ====================

@strawberry.enum
class BusinessTripStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


@strawberry.type
class NightWorkBonus:
    id: int
    user_id: int
    period_id: Optional[int]
    date: datetime.date
    hours: Decimal
    hourly_rate: Decimal
    amount: Decimal
    is_paid: bool
    notes: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.NightWorkBonus) -> "NightWorkBonus":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            period_id=instance.period_id,
            date=instance.date,
            hours=instance.hours,
            hourly_rate=instance.hourly_rate,
            amount=instance.amount,
            is_paid=instance.is_paid if instance.is_paid is not None else False,
            notes=instance.notes,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class OvertimeWork:
    id: int
    user_id: int
    period_id: Optional[int]
    date: datetime.date
    hours: Decimal
    hourly_rate: Decimal
    multiplier: Decimal
    amount: Decimal
    is_paid: bool
    notes: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.OvertimeWork) -> "OvertimeWork":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            period_id=instance.period_id,
            date=instance.date,
            hours=instance.hours,
            hourly_rate=instance.hourly_rate,
            multiplier=instance.multiplier if instance.multiplier is not None else Decimal("1.5"),
            amount=instance.amount,
            is_paid=instance.is_paid if instance.is_paid is not None else False,
            notes=instance.notes,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class WorkOnHoliday:
    id: int
    user_id: int
    period_id: Optional[int]
    date: datetime.date
    hours: Decimal
    hourly_rate: Decimal
    multiplier: Decimal
    amount: Decimal
    is_paid: bool
    notes: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.WorkOnHoliday) -> "WorkOnHoliday":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            period_id=instance.period_id,
            date=instance.date,
            hours=instance.hours,
            hourly_rate=instance.hourly_rate,
            multiplier=instance.multiplier if instance.multiplier is not None else Decimal("2.0"),
            amount=instance.amount,
            is_paid=instance.is_paid if instance.is_paid is not None else False,
            notes=instance.notes,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class BusinessTrip:
    id: int
    user_id: int
    period_id: Optional[int]
    department_id: Optional[int]
    destination: str
    start_date: datetime.date
    end_date: datetime.date
    daily_allowance: Decimal
    accommodation: Decimal
    transport: Decimal
    other_expenses: Decimal
    total_amount: Decimal
    status: BusinessTripStatus
    approved_by_id: Optional[int]
    approved_at: Optional[datetime.datetime]
    approved_notes: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @strawberry.field
    async def approved_by(self, info: strawberry.Info) -> Optional["User"]:
        if self.approved_by_id:
            return await info.context["dataloaders"]["user_by_id"].load(self.approved_by_id)
        return None

    @classmethod
    def from_instance(cls, instance: models.BusinessTrip) -> "BusinessTrip":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            period_id=instance.period_id,
            department_id=instance.department_id,
            destination=instance.destination,
            start_date=instance.start_date,
            end_date=instance.end_date,
            daily_allowance=instance.daily_allowance if instance.daily_allowance is not None else Decimal("0"),
            accommodation=instance.accommodation if instance.accommodation is not None else Decimal("0"),
            transport=instance.transport if instance.transport is not None else Decimal("0"),
            other_expenses=instance.other_expenses if instance.other_expenses is not None else Decimal("0"),
            total_amount=instance.total_amount if instance.total_amount is not None else Decimal("0"),
            status=BusinessTripStatus(instance.status),
            approved_by_id=instance.approved_by_id,
            approved_at=instance.approved_at,
            approved_notes=instance.approved_notes,
            notes=instance.notes,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


@strawberry.type
class WorkExperience:
    id: int
    user_id: int
    company_id: Optional[int]
    company_name: str
    position: Optional[str]
    start_date: datetime.date
    end_date: Optional[datetime.date]
    years: int
    months: int
    class_level: Optional[str]
    is_current: bool
    notes: Optional[str]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    @strawberry.field
    async def user(self, info: strawberry.Info) -> "User":
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)

    @classmethod
    def from_instance(cls, instance: models.WorkExperience) -> "WorkExperience":
        return cls(
            id=instance.id,
            user_id=instance.user_id,
            company_id=instance.company_id,
            company_name=instance.company_name,
            position=instance.position,
            start_date=instance.start_date,
            end_date=instance.end_date,
            years=instance.years if instance.years is not None else 0,
            months=instance.months if instance.months is not None else 0,
            class_level=instance.class_level,
            is_current=instance.is_current if instance.is_current is not None else False,
            notes=instance.notes,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )
