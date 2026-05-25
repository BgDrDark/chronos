import strawberry
from sqlalchemy import select

from backend.exceptions import AuthenticationException, PermissionDeniedException
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"

@strawberry.type
class ContractQuery:
    @strawberry.field(name="employmentContracts")
    async def employment_contracts(
        self,
        info: strawberry.Info,
        company_id: int | None = None,
        user_id: int | None = None,
        status: str | None = None,
    ) -> list[types.EmploymentContract]:
        """Връща списък с трудови договори"""
        from sqlalchemy import select

        from backend.database.models import EmploymentContract
        db = info.context["db"]
        current_user = info.context["current_user"]

        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail="Трябва да сте администратор за достъп до договорите")

        from sqlalchemy.orm import selectinload
        stmt = select(EmploymentContract).options(
            selectinload(EmploymentContract.company),
            selectinload(EmploymentContract.position),
            selectinload(EmploymentContract.department),
        )

        # Filter by user_id
        if user_id:
            stmt = stmt.where(EmploymentContract.user_id == user_id)
        # Filter by company
        elif company_id:
            stmt = stmt.where(EmploymentContract.company_id == company_id)
        elif current_user.role.name != "super_admin":
            stmt = stmt.where(EmploymentContract.company_id == current_user.company_id)

        # Filter by status
        if status:
            stmt = stmt.where(EmploymentContract.status == status)

        stmt = stmt.order_by(EmploymentContract.created_at.desc())

        result = await db.execute(stmt)
        contracts = result.scalars().all()
        return [types.EmploymentContract.from_pydantic(c) for c in contracts]

    @strawberry.field
    async def employment_contract(
        self,
        info: strawberry.Info,
        id: int,
    ) -> types.EmploymentContract | None:
        """Връща конкретен трудов договор"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from backend.database.models import EmploymentContract
        db = info.context["db"]

        stmt = select(EmploymentContract).options(
            selectinload(EmploymentContract.company),
            selectinload(EmploymentContract.position),
            selectinload(EmploymentContract.department),
        ).where(EmploymentContract.id == id)
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()

        if contract:
            return types.EmploymentContract.from_pydantic(contract)
        return None

    @strawberry.field
    async def contract_templates(self, info: strawberry.Info) -> list[types.ContractTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        company_id = current_user.company_id if current_user.role.name != "super_admin" else None

        from backend.database.models import ContractTemplate
        stmt = select(ContractTemplate)
        if company_id:
            stmt = stmt.where(ContractTemplate.company_id == company_id)
        stmt = stmt.where(ContractTemplate.is_active).order_by(ContractTemplate.name)

        result = await db.execute(stmt)
        templates = result.scalars().all()
        return [types.ContractTemplate.from_pydantic(t) for t in templates]

    @strawberry.field
    async def contract_template(self, info: strawberry.Info, id: int) -> types.ContractTemplate | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplate
        template = await db.get(ContractTemplate, id)
        if not template:
            return None
        return types.ContractTemplate.from_pydantic(template)

    @strawberry.field
    async def contract_template_versions(self, info: strawberry.Info, template_id: int) -> list[types.ContractTemplateVersion]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        from backend.database.models import ContractTemplateVersion
        stmt = select(ContractTemplateVersion).where(
            ContractTemplateVersion.template_id == template_id,
        ).order_by(ContractTemplateVersion.version.desc())

        result = await db.execute(stmt)
        versions = result.scalars().all()
        return [types.ContractTemplateVersion.from_pydantic(v) for v in versions]

    @strawberry.field
    async def annex_templates(self, info: strawberry.Info) -> list[types.AnnexTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        company_id = current_user.company_id if current_user.role.name != "super_admin" else None

        from backend.database.models import AnnexTemplate
        stmt = select(AnnexTemplate)
        if company_id:
            stmt = stmt.where(AnnexTemplate.company_id == company_id)
        stmt = stmt.where(AnnexTemplate.is_active).order_by(AnnexTemplate.name)

        result = await db.execute(stmt)
        templates = result.scalars().all()
        return [types.AnnexTemplate.from_pydantic(t) for t in templates]

    @strawberry.field
    async def annex_template(self, info: strawberry.Info, id: int) -> types.AnnexTemplate | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import AnnexTemplate
        template = await db.get(AnnexTemplate, id)
        if not template:
            return None
        return types.AnnexTemplate.from_pydantic(template)

    @strawberry.field
    async def annex_template_versions(self, info: strawberry.Info, template_id: int) -> list[types.AnnexTemplateVersion]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import AnnexTemplateVersion
        stmt = select(AnnexTemplateVersion).where(
            AnnexTemplateVersion.template_id == template_id,
        ).order_by(AnnexTemplateVersion.version.desc())

        result = await db.execute(stmt)
        versions = result.scalars().all()
        return [types.AnnexTemplateVersion.from_pydantic(v) for v in versions]

    @strawberry.field
    async def annexes(self, info: strawberry.Info, status: str | None = None) -> list[types.ContractAnnex]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role is None or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import ContractAnnex, EmploymentContract, User
        stmt = select(ContractAnnex).join(EmploymentContract).join(User)

        if current_user.role is None or current_user.role.name != "super_admin":
            stmt = stmt.where(User.company_id == current_user.company_id)

        if status:
            stmt = stmt.where(ContractAnnex.status == status)

        stmt = stmt.order_by(ContractAnnex.effective_date.desc())

        result = await db.execute(stmt)
        annexes = result.scalars().all()
        return [types.ContractAnnex.from_pydantic(a) for a in annexes]

    @strawberry.field
    async def clause_templates(self, info: strawberry.Info, category: str | None = None) -> list[types.ClauseTemplate]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)

        company_id = current_user.company_id if current_user.role.name != "super_admin" else None

        from backend.database.models import ClauseTemplate
        stmt = select(ClauseTemplate)
        if company_id:
            stmt = stmt.where(ClauseTemplate.company_id == company_id)
        if category:
            stmt = stmt.where(ClauseTemplate.category == category)
        stmt = stmt.where(ClauseTemplate.is_active).order_by(ClauseTemplate.title)

        result = await db.execute(stmt)
        templates = result.scalars().all()
        return [types.ClauseTemplate.from_pydantic(t) for t in templates]
