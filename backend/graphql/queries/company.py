
import strawberry
from sqlalchemy import select

from backend.crud.repositories import time_repo
from backend.exceptions import AuthenticationException, PermissionDeniedException
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class CompanyQuery:
    @strawberry.field
    async def roles(self, info: strawberry.Info) -> list[types.Role]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        allowed_roles = ["admin", "super_admin", "accountant", "manager"]
        if current_user is None or current_user.role.name not in allowed_roles:
            raise PermissionDeniedException.for_action("access roles")
        db_roles = await time_repo.get_all_roles(db)
        return [types.Role.from_pydantic(role) for role in db_roles]

    @strawberry.field
    async def role(self, id: int, info: strawberry.Info) -> types.Role | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")
        db_role = await time_repo.get_role_by_id(db, id)
        if db_role:
            return types.Role.from_pydantic(db_role)
        return None

    @strawberry.field
    async def companies(self, info: strawberry.Info) -> list[types.Company]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        from backend.database.models import Company as DbCompany
        result = await db.execute(select(DbCompany))
        return [types.Company.from_pydantic(c) for c in result.scalars().all()]

    @strawberry.field
    async def departments(self, info: strawberry.Info, company_id: int | None = None) -> list[types.Department]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        from backend.database.models import Department as DbDepartment
        stmt = select(DbDepartment)
        if company_id:
            stmt = stmt.where(DbDepartment.company_id == company_id)
        result = await db.execute(stmt)
        return [types.Department.from_pydantic(d) for d in result.scalars().all()]

    @strawberry.field
    async def positions(self, info: strawberry.Info, department_id: int | None = None) -> list[types.Position]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        from backend.database.models import Position as DbPosition
        stmt = select(DbPosition)
        if department_id:
            stmt = stmt.where(DbPosition.department_id == department_id)
        result = await db.execute(stmt)
        return [types.Position.from_pydantic(p) for p in result.scalars().all()]
