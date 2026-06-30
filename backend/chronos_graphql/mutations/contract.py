import datetime
import logging

import strawberry
from sqlalchemy import select

from backend import schemas
from backend.database import models
from backend.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from backend.chronos_graphql import inputs, types
from backend.chronos_graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


@strawberry.type
class ContractMutation:
    @strawberry.mutation
    async def add_section_to_contract_template(
        self,
        template_id: int,
        section: inputs.ContractTemplateSectionInput,
        info: strawberry.Info,
    ) -> types.ContractTemplateSection:
        db = info.context["db"]
        current_user = get_current_user(info)

        template = await db.get(models.ContractTemplate, template_id)
        if not template:
            raise NotFoundException.record("Template")
        if (
            template.company_id != current_user.company_id
            and current_user.role.name != "super_admin"
        ):
            raise PermissionDeniedException.for_action(
                "Този шаблон не принадлежи на вашата компания"
            )

        stmt = select(models.ContractTemplateVersion).where(
            models.ContractTemplateVersion.template_id == template_id,
            models.ContractTemplateVersion.is_current,
        )
        result = await db.execute(stmt)
        current_version = result.scalar_one_or_none()

        if not current_version:
            raise NotFoundException.record("Version")

        new_section = models.ContractTemplateSection(
            template_id=template_id,
            version_id=current_version.id,
            title=section.title,
            content=section.content,
            order_index=section.order_index,
            is_required=section.is_required,
        )
        db.add(new_section)
        await db.commit()
        await db.refresh(new_section)

        return types.ContractTemplateSection.from_pydantic(
            schemas.ContractTemplateSection.model_validate(new_section)
        )

    @strawberry.mutation
    async def sign_contract_annex(
        self,
        annex_id: int,
        role: str,
        info: strawberry.Info,
    ) -> types.ContractAnnex:
        db = info.context["db"]
        get_current_user(info)

        annex = await db.get(models.ContractAnnex, annex_id)
        if not annex:
            raise NotFoundException.record("Annex")

        now = models.sofia_now()

        if role == "employer":
            annex.signed_by_employer = True
            annex.signed_by_employer_at = now
        elif role == "employee":
            annex.signed_by_employee = True
            annex.signed_by_employee_at = now

        if annex.signed_by_employer and annex.signed_by_employee:
            annex.is_signed = True
            annex.signed_at = now
            annex.status = "signed"

            if annex.effective_date <= datetime.date.today():
                contract = await db.get(models.EmploymentContract, annex.contract_id)
                if contract:
                    if annex.base_salary is not None:
                        contract.base_salary = annex.base_salary
                    if annex.position_id is not None:
                        contract.position_id = annex.position_id
                    if annex.work_hours_per_week is not None:
                        contract.work_hours_per_week = annex.work_hours_per_week
                    if annex.night_work_rate is not None:
                        contract.night_work_rate = annex.night_work_rate
                    if annex.overtime_rate is not None:
                        contract.overtime_rate = annex.overtime_rate
                    if annex.holiday_rate is not None:
                        contract.holiday_rate = annex.holiday_rate
        else:
            annex.status = "pending"

        await db.commit()
        await db.refresh(annex)
        return types.ContractAnnex.from_pydantic(
            schemas.ContractAnnex.model_validate(annex)
        )

    @strawberry.mutation
    async def sign_employment_contract(
        self,
        id: int,
        info: strawberry.Info,
    ) -> types.EmploymentContract:
        db = info.context["db"]
        get_current_user(info)

        contract = await db.get(models.EmploymentContract, id)
        if not contract:
            raise NotFoundException.record("Договор")

        if contract.status == "signed":
            raise ValidationException.field("Договор", "Вече е подписан")

        if contract.status == "linked":
            raise ValidationException.field(
                "Договор",
                "Договорът е линкнат към потребител и не може да бъде подписван отново",
            )

        contract.status = "signed"
        contract.signed_at = datetime.datetime.now()

        await db.commit()
        await db.refresh(contract, ["company", "position", "department"])

        return types.EmploymentContract.from_pydantic(
            schemas.EmploymentContract.model_validate(contract)
        )

    @strawberry.mutation
    async def reject_contract_annex(
        self,
        annex_id: int,
        reason: str,
        info: strawberry.Info,
    ) -> types.ContractAnnex:
        db = info.context["db"]
        get_current_user(info)

        annex = await db.get(models.ContractAnnex, annex_id)
        if not annex:
            raise NotFoundException.record("Annex")

        annex.status = "rejected"
        annex.rejection_reason = reason

        await db.commit()
        await db.refresh(annex)
        return types.ContractAnnex.from_pydantic(
            schemas.ContractAnnex.model_validate(annex)
        )

    @strawberry.mutation
    async def restore_contract_template_version(
        self,
        version_id: int,
        info: strawberry.Info,
    ) -> types.ContractTemplate:
        db = info.context["db"]
        get_current_user(info)

        version = await db.get(models.ContractTemplateVersion, version_id)
        if not version:
            raise NotFoundException.record("Version")

        template = await db.get(models.ContractTemplate, version.template_id)
        if not template:
            raise NotFoundException.record("Template")

        stmt = select(models.ContractTemplateVersion).where(
            models.ContractTemplateVersion.template_id == template.id,
            models.ContractTemplateVersion.is_current,
        )
        result = await db.execute(stmt)
        current = result.scalar_one_or_none()
        if current:
            current.is_current = False

        version.is_current = True

        template.contract_type = version.contract_type
        template.work_hours_per_week = version.work_hours_per_week
        template.probation_months = version.probation_months
        template.salary_calculation_type = version.salary_calculation_type
        template.payment_day = version.payment_day
        template.night_work_rate = version.night_work_rate
        template.overtime_rate = version.overtime_rate
        template.holiday_rate = version.holiday_rate
        template.work_class = version.work_class

        await db.commit()
        await db.refresh(template)
        return types.ContractTemplate.from_pydantic(
            schemas.ContractTemplate.model_validate(template)
        )

    @strawberry.mutation
    async def link_employment_contract_to_user(
        self,
        contract_id: int,
        user_id: int,
        info: strawberry.Info,
    ) -> types.EmploymentContract:
        db = info.context["db"]
        get_current_user(info)

        contract = await db.get(models.EmploymentContract, contract_id)
        if not contract:
            raise NotFoundException.record("Договор")

        user = await db.get(models.User, user_id)
        if not user:
            raise NotFoundException.user()

        if contract.status != "signed":
            raise ValidationException.field("Договор", "Трябва първо да бъде подписан")

        if contract.user_id == user_id and contract.status == "linked":
            raise ValidationException.field(
                "Договор", "Вече е линкнат към този потребител"
            )

        contract.user_id = user_id
        contract.status = "linked"

        user.company_id = contract.company_id
        user.department_id = contract.department_id
        user.position_id = contract.position_id
        db.add(user)

        await db.commit()
        await db.refresh(contract, ["company", "position", "department"])

        return types.EmploymentContract.from_pydantic(
            schemas.EmploymentContract.model_validate(contract)
        )
