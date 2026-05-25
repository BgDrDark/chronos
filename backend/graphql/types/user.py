import datetime
from typing import TYPE_CHECKING, Annotated

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.graphql import types
from backend.graphql.types import Company, Department, Position, Role

if TYPE_CHECKING:
    from backend.graphql.types.contract import EmploymentContract


@sp.type(schemas.User)
class User:
    id: strawberry.auto
    email: strawberry.auto
    username: strawberry.auto
    first_name: strawberry.auto
    surname: strawberry.auto
    last_name: strawberry.auto
    phone_number: strawberry.auto
    address: strawberry.auto
    egn: strawberry.auto
    birth_date: strawberry.auto
    iban: strawberry.auto
    is_active: strawberry.auto
    role_id: strawberry.auto
    company_id: strawberry.auto
    department_id: strawberry.auto
    position_id: strawberry.auto
    created_at: strawberry.auto
    last_login: strawberry.auto
    qr_token: strawberry.auto
    password_force_change: strawberry.auto
    profile_picture: strawberry.auto

    @strawberry.field
    async def role(self, info: strawberry.Info) -> Role | None:
        if not self.role_id:
            return None
        result = await info.context["dataloaders"]["role_by_id"].load(self.role_id)
        return Role.from_pydantic(result) if result else None

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Company | None:
        if not self.company_id:
            return None
        from backend.database.models import Company as DbCompany
        db = info.context["db"]
        res = await db.get(DbCompany, self.company_id)
        return Company.from_pydantic(res) if res else None

    @strawberry.field
    async def department(self, info: strawberry.Info) -> Department | None:
        if not self.department_id:
            return None
        from backend.database.models import Department as DbDepartment
        db = info.context["db"]
        res = await db.get(DbDepartment, self.department_id)
        return Department.from_pydantic(res) if res else None

    @strawberry.field
    async def position(self, info: strawberry.Info) -> Position | None:
        if not self.position_id:
            return None
        from backend.database.models import Position as DbPosition
        db = info.context["db"]
        res = await db.get(DbPosition, self.position_id)
        return Position.from_pydantic(res) if res else None

    @strawberry.field
    async def company_name(self, info: strawberry.Info) -> str | None:
        if not self.company_id:
            return None
        from backend.database.models import Company as DbCompany
        db = info.context["db"]
        res = await db.get(DbCompany, self.company_id)
        return res.name if res else None

    @strawberry.field
    async def department_name(self, info: strawberry.Info) -> str | None:
        if not self.department_id:
            return None
        from backend.database.models import Department as DbDepartment
        db = info.context["db"]
        res = await db.get(DbDepartment, self.department_id)
        return res.name if res else None

    @strawberry.field
    async def job_title(self, info: strawberry.Info) -> str | None:
        if not self.position_id:
            return None
        from backend.database.models import Position as DbPosition
        db = info.context["db"]
        res = await db.get(DbPosition, self.position_id)
        return res.title if res else None

    @strawberry.field
    async def employment_contract(self, info: strawberry.Info) -> Annotated["EmploymentContract", strawberry.lazy("backend.graphql.types.contract")] | None:
        from backend.graphql.types.contract import EmploymentContract
        db = info.context["db"]
        from sqlalchemy import select

        from backend.database.models import EmploymentContract as DbEmploymentContract
        stmt = select(DbEmploymentContract).where(
            DbEmploymentContract.user_id == self.id,
            DbEmploymentContract.is_active,
        )
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()
        return EmploymentContract.from_pydantic(contract) if contract else None

    @strawberry.field
    async def is_smtp_configured(self, info: strawberry.Info) -> bool:
        from backend.services.email_service import is_smtp_configured
        db = info.context["db"]
        return await is_smtp_configured(db)


@strawberry.type
class UserPresence:
    user: "User"
    shift_start: datetime.time | None
    shift_end: datetime.time | None
    actual_arrival: datetime.datetime | None
    actual_departure: datetime.datetime | None
    status: types.PresenceStatus
    is_on_duty: bool


@sp.type(schemas.UserSession)
class UserSession:
    id: strawberry.auto
    user_id: strawberry.auto
    ip_address: strawberry.auto
    user_agent: strawberry.auto
    device_type: strawberry.auto
    is_active: strawberry.auto


@strawberry.type
class PaginatedUsers:
    users: list[User]
    total_count: int
