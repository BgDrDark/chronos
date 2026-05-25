import datetime
from decimal import Decimal

import strawberry
from strawberry.experimental import pydantic as sp
from sqlalchemy import select

from backend import schemas
from backend.database import models
from backend.graphql.types import Company, Department, Position


@sp.type(schemas.ContractAnnex)
class ContractAnnex:
    id: strawberry.auto
    contract_id: strawberry.auto
    annex_number: strawberry.auto
    effective_date: strawberry.auto
    base_salary: strawberry.auto
    position_id: strawberry.auto
    work_hours_per_week: strawberry.auto
    probation_months: strawberry.auto
    night_work_rate: strawberry.auto
    overtime_rate: strawberry.auto
    holiday_rate: strawberry.auto
    work_class: strawberry.auto
    is_signed: strawberry.auto
    signed_at: strawberry.auto
    status: strawberry.auto
    template_id: strawberry.auto
    change_type: strawberry.auto
    change_description: strawberry.auto
    signature_requested_at: strawberry.auto
    signed_by_employee: strawberry.auto
    signed_by_employee_at: strawberry.auto
    signed_by_employer: strawberry.auto
    signed_by_employer_at: strawberry.auto
    rejection_reason: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def position(self, info: strawberry.Info) -> Position | None:
        if not self.position_id:
            return None
        return await info.context["dataloaders"]["position_by_id"].load(self.position_id)


@sp.type(schemas.EmploymentContract)
class EmploymentContract:
    id: strawberry.auto
    user_id: strawberry.auto
    company_id: strawberry.auto
    contract_type: strawberry.auto
    contract_number: strawberry.auto
    start_date: strawberry.auto
    end_date: strawberry.auto
    base_salary: strawberry.auto
    work_hours_per_week: strawberry.auto
    probation_months: strawberry.auto
    is_active: strawberry.auto
    salary_calculation_type: strawberry.auto
    salary_installments_count: strawberry.auto
    monthly_advance_amount: strawberry.auto
    tax_resident: strawberry.auto
    insurance_contributor: strawberry.auto
    has_income_tax: strawberry.auto
    payment_day: strawberry.auto
    experience_start_date: strawberry.auto
    night_work_rate: strawberry.auto
    overtime_rate: strawberry.auto
    holiday_rate: strawberry.auto
    work_class: strawberry.auto
    dangerous_work: strawberry.auto
    template_id: strawberry.auto
    position_id: strawberry.auto
    department_id: strawberry.auto
    clause_ids: strawberry.auto
    employee_name: strawberry.auto
    employee_egn: strawberry.auto
    status: strawberry.auto
    signed_at: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Company | None:
        if not self.company_id:
            return None
        result = await info.context["dataloaders"]["company_by_id"].load(self.company_id)
        return Company.from_pydantic(result) if result else None

    @strawberry.field
    async def department(self, info: strawberry.Info) -> Department | None:
        if not self.department_id:
            return None
        result = await info.context["dataloaders"]["department_by_id"].load(self.department_id)
        return Department.from_pydantic(result) if result else None

    @strawberry.field
    async def position(self, info: strawberry.Info) -> Position | None:
        if not self.position_id:
            return None
        result = await info.context["dataloaders"]["position_by_id"].load(self.position_id)
        return Position.from_pydantic(result) if result else None

    @strawberry.field
    async def position_title(self, info: strawberry.Info) -> str | None:
        if not self.position_id:
            return None
        result = await info.context["dataloaders"]["position_by_id"].load(self.position_id)
        return result.title if result else None

    # @strawberry.field
    # async def annexes(self, info: strawberry.Info) -> list["ContractAnnex"]:
    #     from backend.database.models import ContractAnnex as ModelContractAnnex
    #     db = info.context["db"]
    #     stmt = select(ModelContractAnnex).where(
    #         ModelContractAnnex.contract_id == self.id,
    #     ).order_by(ModelContractAnnex.effective_date.desc())
    #     result = await db.execute(stmt)
    #     annexes = result.scalars().all()
    #     return [ContractAnnex.from_pydantic(a) for a in annexes]


@sp.type(schemas.ContractTemplateSection)
class ContractTemplateSection:
    id: strawberry.auto
    template_id: strawberry.auto
    version_id: strawberry.auto
    title: strawberry.auto
    content: strawberry.auto
    order_index: strawberry.auto
    is_required: strawberry.auto


@sp.type(schemas.ContractTemplateVersion)
class ContractTemplateVersion:
    id: strawberry.auto
    template_id: strawberry.auto
    version: strawberry.auto
    contract_type: strawberry.auto
    base_salary: strawberry.auto
    work_hours_per_week: strawberry.auto
    probation_months: strawberry.auto
    salary_calculation_type: strawberry.auto
    payment_day: strawberry.auto
    night_work_rate: strawberry.auto
    overtime_rate: strawberry.auto
    holiday_rate: strawberry.auto
    work_class: strawberry.auto
    position_id: strawberry.auto
    department_id: strawberry.auto
    is_current: strawberry.auto
    created_by: strawberry.auto
    created_at: strawberry.auto
    change_note: strawberry.auto

    @strawberry.field
    async def sections(self, info: strawberry.Info) -> list[ContractTemplateSection]:
        from backend.database.models import ContractTemplateSection as ModelSection
        db = info.context["db"]
        stmt = select(ModelSection).where(ModelSection.version_id == self.id).order_by(ModelSection.order_index)
        result = await db.execute(stmt)
        sections = result.scalars().all()
        return [ContractTemplateSection.from_pydantic(s) for s in sections]


@sp.type(schemas.ContractTemplate)
class ContractTemplate:
    id: strawberry.auto
    company_id: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto
    contract_type: strawberry.auto
    base_salary: strawberry.auto
    work_hours_per_week: strawberry.auto
    probation_months: strawberry.auto
    salary_calculation_type: strawberry.auto
    payment_day: strawberry.auto
    night_work_rate: strawberry.auto
    overtime_rate: strawberry.auto
    holiday_rate: strawberry.auto
    work_class: strawberry.auto
    position_id: strawberry.auto
    department_id: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def current_version(self, info: strawberry.Info) -> ContractTemplateVersion | None:
        from backend.database.models import ContractTemplateVersion as ModelVersion
        db = info.context["db"]
        stmt = select(ModelVersion).where(
            ModelVersion.template_id == self.id,
            ModelVersion.is_current,
        ).order_by(ModelVersion.version.desc())
        result = await db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            return None
        return ContractTemplateVersion.from_pydantic(version)


@sp.type(schemas.AnnexTemplateSection)
class AnnexTemplateSection:
    id: strawberry.auto
    template_id: strawberry.auto
    version_id: strawberry.auto
    title: strawberry.auto
    content: strawberry.auto
    order_index: strawberry.auto
    is_required: strawberry.auto


@sp.type(schemas.AnnexTemplateVersion)
class AnnexTemplateVersion:
    id: strawberry.auto
    template_id: strawberry.auto
    version: strawberry.auto
    change_type: strawberry.auto
    new_base_salary: strawberry.auto
    new_work_hours_per_week: strawberry.auto
    new_night_work_rate: strawberry.auto
    new_overtime_rate: strawberry.auto
    new_holiday_rate: strawberry.auto
    is_current: strawberry.auto
    created_by: strawberry.auto
    created_at: strawberry.auto
    change_note: strawberry.auto

    @strawberry.field
    async def sections(self, info: strawberry.Info) -> list[AnnexTemplateSection]:
        from backend.database.models import AnnexTemplateSection as ModelSection
        db = info.context["db"]
        stmt = select(ModelSection).where(ModelSection.version_id == self.id).order_by(ModelSection.order_index)
        result = await db.execute(stmt)
        sections = result.scalars().all()
        return [AnnexTemplateSection.from_pydantic(s) for s in sections]


@sp.type(schemas.AnnexTemplate)
class AnnexTemplate:
    id: strawberry.auto
    company_id: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto
    change_type: strawberry.auto
    new_base_salary: strawberry.auto
    new_work_hours_per_week: strawberry.auto
    new_night_work_rate: strawberry.auto
    new_overtime_rate: strawberry.auto
    new_holiday_rate: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

    @strawberry.field
    async def current_version(self, info: strawberry.Info) -> AnnexTemplateVersion | None:
        from backend.database.models import AnnexTemplateVersion as ModelVersion
        db = info.context["db"]
        stmt = select(ModelVersion).where(
            ModelVersion.template_id == self.id,
            ModelVersion.is_current,
        ).order_by(ModelVersion.version.desc())
        result = await db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            return None
        return AnnexTemplateVersion.from_pydantic(version)


@sp.type(schemas.ClauseTemplate)
class ClauseTemplate:
    id: strawberry.auto
    company_id: strawberry.auto
    title: strawberry.auto
    content: strawberry.auto
    category: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto
