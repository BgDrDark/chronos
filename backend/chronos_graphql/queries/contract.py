import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.exceptions import AuthenticationException, PermissionDeniedException
from backend.chronos_graphql import types
from backend.chronos_graphql.types.contract import ContractTemplateClauseGQL

authenticate_msg = "Трябва да се автентикирате"


def _build_template_cache(info: strawberry.Info):
    return info.context.setdefault("_tmpl", {})


def _preload_contract_templates(info: strawberry.Info, templates: list):
    cache = _build_template_cache(info)
    for t in templates:
        current = (
            next((v for v in t.versions if v.is_current), None) if t.versions else None
        )
        if current:
            cache[f"ct_ver:{t.id}"] = current
            cache[f"ver_sec:{current.id}"] = (
                list(current.sections) if current.sections else []
            )
        cache[f"ct_cl:{t.id}"] = [
            ContractTemplateClauseGQL(
                id=c.id,
                template_id=c.template_id,
                clause_id=c.clause_id,
                order_index=c.order_index,
            )
            for c in (t.clauses or [])
        ]
        for c in t.clauses or []:
            if c.clause:
                cache[f"cl:{c.clause_id}"] = c.clause


def _preload_annex_templates(info: strawberry.Info, templates: list):
    cache = _build_template_cache(info)
    for t in templates:
        current = (
            next((v for v in t.versions if v.is_current), None) if t.versions else None
        )
        if current:
            cache[f"at_ver:{t.id}"] = current
            cache[f"aver_sec:{current.id}"] = (
                list(current.sections) if current.sections else []
            )


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
        from backend.database.models import EmploymentContract

        db = info.context["db"]
        current_user = info.context["current_user"]

        if current_user is None or current_user.role.name not in [
            "admin",
            "super_admin",
        ]:
            raise AuthenticationException(
                detail="Трябва да сте администратор за достъп до договорите"
            )

        stmt = select(EmploymentContract).options(
            selectinload(EmploymentContract.company),
            selectinload(EmploymentContract.position),
            selectinload(EmploymentContract.department),
        )

        if user_id:
            stmt = stmt.where(EmploymentContract.user_id == user_id)
        elif company_id:
            stmt = stmt.where(EmploymentContract.company_id == company_id)
        elif current_user.role.name != "super_admin":
            stmt = stmt.where(EmploymentContract.company_id == current_user.company_id)

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
        from backend.database.models import EmploymentContract

        db = info.context["db"]

        stmt = (
            select(EmploymentContract)
            .options(
                selectinload(EmploymentContract.company),
                selectinload(EmploymentContract.position),
                selectinload(EmploymentContract.department),
            )
            .where(EmploymentContract.id == id)
        )
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()

        if contract:
            return types.EmploymentContract.from_pydantic(contract)
        return None

    @strawberry.field
    async def contract_templates(
        self, info: strawberry.Info
    ) -> list[types.ContractTemplate]:
        from backend.database.models import (
            ContractTemplate,
            ContractTemplateClause,
            ContractTemplateVersion,
        )

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        company_id = (
            current_user.company_id if current_user.role.name != "super_admin" else None
        )

        stmt = select(ContractTemplate).options(
            selectinload(ContractTemplate.versions).selectinload(
                ContractTemplateVersion.sections
            ),
            selectinload(ContractTemplate.clauses).selectinload(
                ContractTemplateClause.clause
            ),
        )
        if company_id:
            stmt = stmt.where(ContractTemplate.company_id == company_id)
        stmt = stmt.where(ContractTemplate.is_active).order_by(ContractTemplate.name)

        result = await db.execute(stmt)
        templates = result.scalars().all()
        _preload_contract_templates(info, templates)
        return [types.ContractTemplate.from_pydantic(t) for t in templates]

    @strawberry.field
    async def contract_template(
        self, info: strawberry.Info, id: int
    ) -> types.ContractTemplate | None:
        from backend.database.models import (
            ContractTemplate,
            ContractTemplateClause,
            ContractTemplateVersion,
        )

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        stmt = (
            select(ContractTemplate)
            .options(
                selectinload(ContractTemplate.versions).selectinload(
                    ContractTemplateVersion.sections
                ),
                selectinload(ContractTemplate.clauses).selectinload(
                    ContractTemplateClause.clause
                ),
            )
            .where(ContractTemplate.id == id)
        )
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()
        if not template:
            return None
        _preload_contract_templates(info, [template])
        return types.ContractTemplate.from_pydantic(template)

    @strawberry.field
    async def contract_template_versions(
        self, info: strawberry.Info, template_id: int
    ) -> list[types.ContractTemplateVersion]:
        from backend.database.models import ContractTemplateVersion

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        stmt = (
            select(ContractTemplateVersion)
            .options(
                selectinload(ContractTemplateVersion.sections),
            )
            .where(
                ContractTemplateVersion.template_id == template_id,
            )
            .order_by(ContractTemplateVersion.version.desc())
        )

        result = await db.execute(stmt)
        versions = result.scalars().all()

        cache = _build_template_cache(info)
        for v in versions:
            cache[f"ver_sec:{v.id}"] = list(v.sections) if v.sections else []

        return [types.ContractTemplateVersion.from_pydantic(v) for v in versions]

    @strawberry.field
    async def annex_templates(self, info: strawberry.Info) -> list[types.AnnexTemplate]:
        from backend.database.models import AnnexTemplate, AnnexTemplateVersion

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("access")

        company_id = (
            current_user.company_id if current_user.role.name != "super_admin" else None
        )

        stmt = select(AnnexTemplate).options(
            selectinload(AnnexTemplate.versions).selectinload(
                AnnexTemplateVersion.sections
            ),
        )
        if company_id:
            stmt = stmt.where(AnnexTemplate.company_id == company_id)
        stmt = stmt.where(AnnexTemplate.is_active).order_by(AnnexTemplate.name)

        result = await db.execute(stmt)
        templates = result.scalars().all()
        _preload_annex_templates(info, templates)
        return [types.AnnexTemplate.from_pydantic(t) for t in templates]

    @strawberry.field
    async def annex_template(
        self, info: strawberry.Info, id: int
    ) -> types.AnnexTemplate | None:
        from backend.database.models import AnnexTemplate, AnnexTemplateVersion

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)

        stmt = (
            select(AnnexTemplate)
            .options(
                selectinload(AnnexTemplate.versions).selectinload(
                    AnnexTemplateVersion.sections
                ),
            )
            .where(AnnexTemplate.id == id)
        )
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()
        if not template:
            return None
        _preload_annex_templates(info, [template])
        return types.AnnexTemplate.from_pydantic(template)

    @strawberry.field
    async def annex_template_versions(
        self, info: strawberry.Info, template_id: int
    ) -> list[types.AnnexTemplateVersion]:
        from backend.database.models import AnnexTemplateVersion

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)

        stmt = (
            select(AnnexTemplateVersion)
            .options(
                selectinload(AnnexTemplateVersion.sections),
            )
            .where(
                AnnexTemplateVersion.template_id == template_id,
            )
            .order_by(AnnexTemplateVersion.version.desc())
        )

        result = await db.execute(stmt)
        versions = result.scalars().all()

        cache = _build_template_cache(info)
        for v in versions:
            cache[f"aver_sec:{v.id}"] = list(v.sections) if v.sections else []

        return [types.AnnexTemplateVersion.from_pydantic(v) for v in versions]

    @strawberry.field
    async def annexes(
        self, info: strawberry.Info, status: str | None = None
    ) -> list[types.ContractAnnex]:
        from backend.database.models import ContractAnnex, EmploymentContract, User

        db = info.context["db"]
        current_user = info.context["current_user"]
        if (
            current_user is None
            or current_user.role is None
            or current_user.role.name not in ["admin", "super_admin"]
        ):
            raise AuthenticationException(detail="Трябва да се автентикирате")

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
    async def clause_templates(
        self, info: strawberry.Info, category: str | None = None
    ) -> list[types.ClauseTemplate]:
        from backend.database.models import ClauseTemplate

        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail=authenticate_msg)

        company_id = (
            current_user.company_id if current_user.role.name != "super_admin" else None
        )

        stmt = select(ClauseTemplate)
        if company_id:
            stmt = stmt.where(ClauseTemplate.company_id == company_id)
        if category:
            stmt = stmt.where(ClauseTemplate.category == category)
        stmt = stmt.where(ClauseTemplate.is_active).order_by(ClauseTemplate.title)

        result = await db.execute(stmt)
        templates = result.scalars().all()
        return [types.ClauseTemplate.from_pydantic(t) for t in templates]
