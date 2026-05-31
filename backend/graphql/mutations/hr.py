import datetime
import json
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend import schemas
from backend.exceptions import (
    InvalidOperationException,
    NotFoundException,
    ValidationException,
)
from backend.graphql import inputs, types
from backend.graphql.utils.permission_checker import (
    check_company_access,
    get_current_user,
)


@strawberry.type
class HRMutation:
    @strawberry.mutation
    async def create_employment_contract(
        self,
        input: inputs.EmploymentContractCreateInput,
        info: strawberry.Info
    ) -> types.EmploymentContract:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)
        
        from backend.database.models import ContractTemplate, EmploymentContract
        
        company_id = input.company_id
        if not company_id and current_user.company_id:
            company_id = current_user.company_id
        
        if not company_id:
            raise ValidationException.required_field("ID на фирмата")
        
        template = None
        template_clauses = []
        if input.template_id:
            template = await db.get(ContractTemplate, input.template_id)
            if template:
                from backend.database.models import ContractTemplateClause
                clauses_result = await db.execute(
                    select(ContractTemplateClause).where(ContractTemplateClause.template_id == input.template_id)
                )
                template_clauses = [c.clause_id for c in clauses_result.scalars().all()]
        
        final_clause_ids = input.clause_ids
        if not final_clause_ids and template_clauses:
            final_clause_ids = json.dumps(template_clauses) if template_clauses else None
        
        contract = EmploymentContract(
            employee_name=input.employee_name,
            employee_egn=input.employee_egn,
            company_id=company_id,
            department_id=input.department_id,
            position_id=input.position_id,
            template_id=input.template_id,
            user_id=None,
            contract_type=input.contract_type,
            contract_number=input.contract_number,
            start_date=input.start_date,
            end_date=input.end_date,
            base_salary=input.base_salary,
            work_hours_per_week=input.work_hours_per_week,
            status="draft",
            clause_ids=final_clause_ids,
            probation_months=input.probation_months if input.probation_months is not None else (template.probation_months if template else None),
            salary_calculation_type=input.salary_calculation_type or (template.salary_calculation_type if template else 'gross'),
            payment_day=input.payment_day if input.payment_day is not None else (template.payment_day if template else 25),
            night_work_rate=input.night_work_rate if input.night_work_rate is not None else (template.night_work_rate if template else 0.5),
            overtime_rate=input.overtime_rate if input.overtime_rate is not None else (template.overtime_rate if template else 1.5),
            holiday_rate=input.holiday_rate if input.holiday_rate is not None else (template.holiday_rate if template else 2.0),
            work_class=input.work_class or (template.work_class if template else None),
        )
        
        db.add(contract)
        await db.commit()
        await db.refresh(contract, ["company", "position", "department"])
        
        return types.EmploymentContract.from_pydantic(schemas.EmploymentContract.model_validate(contract))

    @strawberry.mutation
    async def generate_contract_number(
        self,
        company_id: int,
        info: strawberry.Info
    ) -> str:
        db = info.context["db"]
        
        from backend.database.models import Company, EmploymentContract
        
        company = await db.get(Company, company_id)
        if not company:
            raise NotFoundException.resource("Фирма")
        
        current_year = datetime.datetime.now().year
        
        result = await db.execute(
            select(EmploymentContract).where(
                EmploymentContract.company_id == company_id
            )
        )
        all_contracts = result.scalars().all()
        
        year_contracts = [c for c in all_contracts if c.created_at and c.created_at.year == current_year]
        sequence = len(year_contracts) + 1
        
        company_code = company.eik if company.eik else str(company_id)
        contract_number = f"TRZ-{company_code}-{current_year}-{sequence:04d}"
        
        return contract_number

    @strawberry.mutation
    async def get_contract_pdf_url(
        self,
        contract_id: int,
        info: strawberry.Info
    ) -> str:
        from backend.config import settings
        
        db = info.context["db"]
        current_user = get_current_user(info)
        check_company_access(db, current_user, "EmploymentContract", contract_id)
        
        from backend.database.models import EmploymentContract
        
        contract = await db.get(EmploymentContract, contract_id)
        if not contract:
            raise NotFoundException.record("Договор")
        
        base_url = settings.API_URL
        return f"{base_url}/export/contract/{contract_id}/pdf"

    @strawberry.mutation
    async def create_contract_template(
        self,
        name: str,
        description: str | None,
        contract_type: str,
        work_hours_per_week: int,
        probation_months: int,
        salary_calculation_type: str,
        payment_day: int,
        night_work_rate: float,
        overtime_rate: float,
        holiday_rate: float,
        work_class: str | None,
        position_id: int | None = None,
        department_id: int | None = None,
        base_salary: float | None = None,
        clause_ids: str | None = None,
        info: strawberry.Info | None = None
    ) -> types.ContractTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import (
            ContractTemplate,
            ContractTemplateClause,
            ContractTemplateSection,
            ContractTemplateVersion,
        )

        template = ContractTemplate(
            company_id=current_user.company_id,
            name=name,
            description=description,
            contract_type=contract_type,
            work_hours_per_week=work_hours_per_week,
            probation_months=probation_months,
            salary_calculation_type=salary_calculation_type,
            payment_day=payment_day,
            night_work_rate=Decimal(str(night_work_rate)),
            overtime_rate=Decimal(str(overtime_rate)),
            holiday_rate=Decimal(str(holiday_rate)),
            work_class=work_class,
            position_id=position_id,
            department_id=department_id,
            base_salary=Decimal(str(base_salary)) if base_salary else None,
            is_active=True,
        )
        db.add(template)
        await db.flush()

        if clause_ids:
            try:
                clause_id_list = json.loads(clause_ids)
                for idx, clause_id in enumerate(clause_id_list):
                    clause_assoc = ContractTemplateClause(
                        template_id=template.id,
                        clause_id=clause_id,
                        order_index=idx
                    )
                    db.add(clause_assoc)
            except Exception:
                pass

        version = ContractTemplateVersion(
            template_id=template.id,
            version=1,
            contract_type=contract_type,
            work_hours_per_week=work_hours_per_week,
            probation_months=probation_months,
            salary_calculation_type=salary_calculation_type,
            payment_day=payment_day,
            night_work_rate=Decimal(str(night_work_rate)),
            overtime_rate=Decimal(str(overtime_rate)),
            holiday_rate=Decimal(str(holiday_rate)),
            work_class=work_class,
            position_id=position_id,
            department_id=department_id,
            base_salary=Decimal(str(base_salary)) if base_salary else None,
            is_current=True,
            created_by=f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
            change_note="Първоначална версия"
        )
        db.add(version)
        await db.flush()

        default_sections = [
            {"title": "Предмет на договора", "content": "Работодателят предоставя на Работника работата на длъжността.", "order_index": 0, "is_required": True},
            {"title": "Работно време и почивки", "content": f"Работникът изпълнява работата си в рамките на {work_hours_per_week} часа седмично.", "order_index": 1, "is_required": True},
            {"title": "Права и задължения на работодателя", "content": "Работодателят е длъжен да осигури на Работника работата и необходимите условия.", "order_index": 2, "is_required": True},
            {"title": "Права и задължения на работника", "content": "Работникът е длъжен да изпълнява работата лично и да спазва реда в предприятието.", "order_index": 3, "is_required": True},
            {"title": "Заплащане", "content": "За извършената работа Работодателят заплаща трудовото възнаграждение.", "order_index": 4, "is_required": True},
            {"title": "Конфиденциалност", "content": "Работникът се задължава да не разкрива на трети лица информация, станала му известна.", "order_index": 5, "is_required": False},
        ]

        for section_data in default_sections:
            section = ContractTemplateSection(
                template_id=template.id,
                version_id=version.id,
                title=section_data["title"],
                content=section_data["content"],
                order_index=section_data["order_index"],
                is_required=section_data["is_required"],
            )
            db.add(section)

        await db.commit()
        await db.refresh(template)
        return types.ContractTemplate(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            contract_type=template.contract_type,
            work_hours_per_week=template.work_hours_per_week,
            probation_months=template.probation_months,
            salary_calculation_type=template.salary_calculation_type,
            payment_day=template.payment_day,
            night_work_rate=float(template.night_work_rate),
            overtime_rate=float(template.overtime_rate),
            holiday_rate=float(template.holiday_rate),
            work_class=template.work_class,
            is_active=template.is_active,
            created_at=template.created_at
        )

    @strawberry.mutation
    async def update_contract_template(
        self,
        id: int,
        name: str,
        description: str | None,
        contract_type: str,
        work_hours_per_week: int,
        probation_months: int,
        salary_calculation_type: str,
        payment_day: int,
        night_work_rate: float,
        overtime_rate: float,
        holiday_rate: float,
        work_class: str | None,
        change_note: str,
        info: strawberry.Info | None = None
    ) -> types.ContractTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import ContractTemplate, ContractTemplateVersion

        template = await db.get(ContractTemplate, id)
        if not template:
            raise NotFoundException.resource("Template")

        template.name = name
        template.description = description
        template.contract_type = contract_type
        template.work_hours_per_week = work_hours_per_week
        template.probation_months = probation_months
        template.salary_calculation_type = salary_calculation_type
        template.payment_day = payment_day
        template.night_work_rate = Decimal(str(night_work_rate))
        template.overtime_rate = Decimal(str(overtime_rate))
        template.holiday_rate = Decimal(str(holiday_rate))
        template.work_class = work_class

        stmt = select(ContractTemplateVersion).where(
            ContractTemplateVersion.template_id == id,
            ContractTemplateVersion.is_current
        )
        result = await db.execute(stmt)
        current_version = result.scalar_one_or_none()

        if current_version:
            current_version.is_current = False

        new_version = ContractTemplateVersion(
            template_id=template.id,
            version=current_version.version + 1 if current_version else 1,
            contract_type=contract_type,
            work_hours_per_week=work_hours_per_week,
            probation_months=probation_months,
            salary_calculation_type=salary_calculation_type,
            payment_day=payment_day,
            night_work_rate=Decimal(str(night_work_rate)),
            overtime_rate=Decimal(str(overtime_rate)),
            holiday_rate=Decimal(str(holiday_rate)),
            work_class=work_class,
            is_current=True,
            created_by=f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
            change_note=change_note
        )
        db.add(new_version)

        await db.commit()
        await db.refresh(template)
        return types.ContractTemplate(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            contract_type=template.contract_type,
            work_hours_per_week=template.work_hours_per_week,
            probation_months=template.probation_months,
            salary_calculation_type=template.salary_calculation_type,
            payment_day=template.payment_day,
            night_work_rate=float(template.night_work_rate),
            overtime_rate=float(template.overtime_rate),
            holiday_rate=float(template.holiday_rate),
            work_class=template.work_class,
            is_active=template.is_active,
            created_at=template.created_at
        )

    @strawberry.mutation
    async def delete_contract_template(
        self,
        id: int,
        info: strawberry.Info | None = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import ContractTemplate

        template = await db.get(ContractTemplate, id)
        if not template:
            raise NotFoundException.resource("Template")

        template.is_active = False
        await db.commit()
        return True

    @strawberry.mutation
    async def create_clause_template(
        self,
        title: str,
        content: str,
        category: str,
        info: strawberry.Info | None = None
    ) -> types.ClauseTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import ClauseTemplate

        clause = ClauseTemplate(
            company_id=current_user.company_id,
            title=title,
            content=content,
            category=category,
            is_active=True,
        )
        db.add(clause)
        await db.commit()
        await db.refresh(clause)
        return types.ClauseTemplate(
            id=clause.id,
            company_id=clause.company_id,
            title=clause.title,
            content=clause.content,
            category=clause.category,
            is_active=clause.is_active,
            created_at=clause.created_at
        )

    @strawberry.mutation
    async def update_clause_template(
        self,
        id: int,
        title: str,
        content: str,
        category: str,
        info: strawberry.Info | None = None
    ) -> types.ClauseTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import ClauseTemplate

        clause = await db.get(ClauseTemplate, id)
        if not clause:
            raise NotFoundException.resource("Clause")

        clause.title = title
        clause.content = content
        clause.category = category

        await db.commit()
        await db.refresh(clause)
        return types.ClauseTemplate(
            id=clause.id,
            company_id=clause.company_id,
            title=clause.title,
            content=clause.content,
            category=clause.category,
            is_active=clause.is_active,
            created_at=clause.created_at
        )

    @strawberry.mutation
    async def delete_clause_template(
        self,
        id: int,
        info: strawberry.Info | None = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import ClauseTemplate

        clause = await db.get(ClauseTemplate, id)
        if not clause:
            raise NotFoundException.resource("Clause")

        clause.is_active = False
        await db.commit()
        return True

    @strawberry.mutation
    async def create_annex_template(
        self,
        name: str,
        description: str | None,
        change_type: str,
        new_base_salary: float | None,
        new_work_hours_per_week: int | None,
        new_night_work_rate: float | None,
        new_overtime_rate: float | None,
        new_holiday_rate: float | None,
        info: strawberry.Info | None = None
    ) -> types.AnnexTemplate:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.database.models import (
            AnnexTemplate,
            AnnexTemplateSection,
            AnnexTemplateVersion,
        )

        template = AnnexTemplate(
            company_id=current_user.company_id,
            name=name,
            description=description,
            change_type=change_type,
            new_base_salary=Decimal(str(new_base_salary)) if new_base_salary else None,
            new_work_hours_per_week=new_work_hours_per_week,
            new_night_work_rate=Decimal(str(new_night_work_rate)) if new_night_work_rate else None,
            new_overtime_rate=Decimal(str(new_overtime_rate)) if new_overtime_rate else None,
            new_holiday_rate=Decimal(str(new_holiday_rate)) if new_holiday_rate else None,
            is_active=True,
        )
        db.add(template)
        await db.flush()

        version = AnnexTemplateVersion(
            template_id=template.id,
            version=1,
            change_type=change_type,
            new_base_salary=Decimal(str(new_base_salary)) if new_base_salary else None,
            new_work_hours_per_week=new_work_hours_per_week,
            new_night_work_rate=Decimal(str(new_night_work_rate)) if new_night_work_rate else None,
            new_overtime_rate=Decimal(str(new_overtime_rate)) if new_overtime_rate else None,
            new_holiday_rate=Decimal(str(new_holiday_rate)) if new_holiday_rate else None,
            is_current=True,
            created_by=f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
            change_note="Първоначална версия"
        )
        db.add(version)
        await db.flush()

        default_sections = [
            {"title": "Описание на промените", "content": "С настоящето споразумение се променят следните условия от трудовия договор:", "order_index": 0, "is_required": True},
            {"title": "Основание", "content": "Настоящето споразумение се сключва на основание чл. 119, ал. 1 от Кодекса на труда.", "order_index": 1, "is_required": False},
        ]

        for section_data in default_sections:
            section = AnnexTemplateSection(
                template_id=template.id,
                version_id=version.id,
                title=section_data["title"],
                content=section_data["content"],
                order_index=section_data["order_index"],
                is_required=section_data["is_required"],
            )
            db.add(section)

        await db.commit()
        await db.refresh(template)
        return types.AnnexTemplate(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            description=template.description,
            change_type=template.change_type,
            new_base_salary=float(template.new_base_salary) if template.new_base_salary else None,
            new_work_hours_per_week=template.new_work_hours_per_week,
            new_night_work_rate=float(template.new_night_work_rate) if template.new_night_work_rate else None,
            new_overtime_rate=float(template.new_overtime_rate) if template.new_overtime_rate else None,
            new_holiday_rate=float(template.new_holiday_rate) if template.new_holiday_rate else None,
            is_active=template.is_active,
            created_at=template.created_at
        )

    @strawberry.mutation
    async def update_section_in_annex_template(
        self,
        section_id: int,
        section: inputs.AnnexTemplateSectionUpdateInput,
        info: strawberry.Info | None = None
    ) -> types.AnnexTemplateSection:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import AnnexTemplateSection
        
        db_section = await db.get(AnnexTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        if section.title is not None:
            db_section.title = section.title
        if section.content is not None:
            db_section.content = section.content
        if section.order_index is not None:
            db_section.order_index = section.order_index
        if section.is_required is not None:
            db_section.is_required = section.is_required
        
        await db.commit()
        await db.refresh(db_section)
        
        return types.AnnexTemplateSection(
            id=db_section.id,
            template_id=db_section.template_id,
            version_id=db_section.version_id,
            title=db_section.title,
            content=db_section.content,
            order_index=db_section.order_index,
            is_required=db_section.is_required
        )

    @strawberry.mutation
    async def delete_section_from_annex_template(
        self,
        section_id: int,
        info: strawberry.Info | None = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import AnnexTemplateSection
        
        db_section = await db.get(AnnexTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        await db.delete(db_section)
        await db.commit()
        return True

    @strawberry.mutation
    async def delete_annex_template(
        self,
        id: int,
        info: strawberry.Info | None = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import AnnexTemplate

        template = await db.get(AnnexTemplate, id)
        if not template:
            raise NotFoundException.resource("Template")

        template.is_active = False
        await db.commit()
        return True

    @strawberry.mutation
    async def get_annex_pdf_url(
        self,
        annex_id: int,
        info: strawberry.Info
    ) -> str:
        from backend.config import settings
         
        db = info.context["db"]
        current_user = get_current_user(info)
        check_company_access(db, current_user, "ContractAnnex", annex_id)
        
        from backend.database.models import ContractAnnex
        
        annex = await db.get(ContractAnnex, annex_id)
        if not annex:
            raise NotFoundException.record("Споразумение")
        
        base_url = settings.API_URL
        return f"{base_url}/export/annex/{annex_id}/pdf"

    @strawberry.mutation
    async def create_contract_annex(
        self,
        contract_id: int,
        effective_date: datetime.date,
        annex_number: str | None = None,
        base_salary: Decimal | None = None,
        position_id: int | None = None,
        work_hours_per_week: int | None = None,
        night_work_rate: float | None = None,
        overtime_rate: float | None = None,
        holiday_rate: float | None = None,
        info: strawberry.Info | None = None
    ) -> types.ContractAnnex:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import ContractAnnex
        
        annex = ContractAnnex(
            contract_id=contract_id,
            annex_number=annex_number,
            effective_date=effective_date,
            base_salary=base_salary,
            position_id=position_id,
            work_hours_per_week=work_hours_per_week,
            night_work_rate=Decimal(str(night_work_rate)) if night_work_rate is not None else None,
            overtime_rate=Decimal(str(overtime_rate)) if overtime_rate is not None else None,
            holiday_rate=Decimal(str(holiday_rate)) if holiday_rate is not None else None,
            is_signed=False
        )
        db.add(annex)
        await db.commit()
        await db.refresh(annex)
        return types.ContractAnnex.from_pydantic(schemas.ContractAnnex.model_validate(annex))

    @strawberry.mutation
    async def update_section_in_contract_template(
        self,
        section_id: int,
        section: inputs.ContractTemplateSectionUpdateInput,
        info: strawberry.Info | None = None
    ) -> types.ContractTemplateSection:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import ContractTemplateSection
        
        db_section = await db.get(ContractTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        if section.title is not None:
            db_section.title = section.title
        if section.content is not None:
            db_section.content = section.content
        if section.order_index is not None:
            db_section.order_index = section.order_index
        if section.is_required is not None:
            db_section.is_required = section.is_required
        
        await db.commit()
        await db.refresh(db_section)
        
        return types.ContractTemplateSection(
            id=db_section.id,
            template_id=db_section.template_id,
            version_id=db_section.version_id,
            title=db_section.title,
            content=db_section.content,
            order_index=db_section.order_index,
            is_required=db_section.is_required
        )

    @strawberry.mutation
    async def delete_section_from_contract_template(
        self,
        section_id: int,
        info: strawberry.Info | None = None
    ) -> bool:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]

        from backend.database.models import ContractTemplateSection
        
        db_section = await db.get(ContractTemplateSection, section_id)
        if not db_section:
            raise NotFoundException.resource("Section")
        
        await db.delete(db_section)
        await db.commit()
        return True
