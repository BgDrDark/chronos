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
    async def pin(self, info: strawberry.Info) -> str | None:
        return self.egn

    @strawberry.field
    async def payrolls(self, info: strawberry.Info) -> list[Annotated["Payroll", strawberry.lazy("backend.graphql.types.payroll")]]:  # noqa: F821
        from backend.graphql.types.payroll import Payroll
        db = info.context["db"]
        from sqlalchemy import select

        from backend.database.models import Payroll as DbPayroll
        stmt = select(DbPayroll).where(DbPayroll.user_id == self.id)
        result = await db.execute(stmt)
        return [Payroll.from_pydantic(schemas.Payroll.model_validate(p)) for p in result.scalars().all()]

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
    async def company_name(self, info: strawberry.Info) -> str | None:
        if not self.company_id:
            return None
        result = await info.context["dataloaders"]["company_by_id"].load(self.company_id)
        return result.name if result else None

    @strawberry.field
    async def department_name(self, info: strawberry.Info) -> str | None:
        if not self.department_id:
            return None
        result = await info.context["dataloaders"]["department_by_id"].load(self.department_id)
        return result.name if result else None

    @strawberry.field
    async def job_title(self, info: strawberry.Info) -> str | None:
        if not self.position_id:
            return None
        result = await info.context["dataloaders"]["position_by_id"].load(self.position_id)
        return result.title if result else None

    @strawberry.field
    async def employment_contract(self, info: strawberry.Info) -> Annotated["EmploymentContract", strawberry.lazy("backend.graphql.types.contract")] | None:
        from backend.graphql.types.contract import EmploymentContract
        result = await info.context["dataloaders"]["contract_by_user_id"].load(self.id)
        return EmploymentContract.from_pydantic(result) if result else None

    @strawberry.field
    async def active_contract(self, info: strawberry.Info) -> Annotated["EmploymentContract", strawberry.lazy("backend.graphql.types.contract")] | None:
        from backend.graphql.types.contract import EmploymentContract
        result = await info.context["dataloaders"]["contract_by_user_id"].load(self.id)
        return EmploymentContract.from_pydantic(result) if result else None

    @strawberry.field
    async def bonuses(self, info: strawberry.Info) -> list[Annotated["Bonus", strawberry.lazy("backend.graphql.types.payroll")]]:  # noqa: F821
        from backend.graphql.types.payroll import Bonus
        db = info.context["db"]
        from sqlalchemy import select

        from backend.database.models import Bonus as DbBonus
        stmt = select(DbBonus).where(DbBonus.user_id == self.id).order_by(DbBonus.date.desc())
        result = await db.execute(stmt)
        return [Bonus.from_pydantic(schemas.Bonus.model_validate(b)) for b in result.scalars().all()]

    @strawberry.field
    async def is_smtp_configured(self, info: strawberry.Info) -> bool:
        from backend.services.email_service import is_smtp_configured
        db = info.context["db"]
        return await is_smtp_configured(db)

    @strawberry.field
    async def leave_balance(self, info: strawberry.Info) -> Annotated["LeaveBalance", strawberry.lazy("backend.graphql.types.leave")] | None:  # noqa: F821
        from backend import schemas
        from backend.crud.repositories import time_repo
        from backend.graphql.types.leave import LeaveBalance
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user.id != self.id and current_user.role.name not in ["admin", "super_admin"]:
            return None
        year = datetime.datetime.now().year
        balances = await time_repo.get_leave_balance(db, self.id, year)
        balance = balances[0] if balances else None
        if not balance:
            return None
        balance_data = schemas.LeaveBalance.model_validate(balance)
        if balance_data.total_days is None:
            balance_data.total_days = 20
        if balance_data.used_days is None:
            balance_data.used_days = 0
        return LeaveBalance.from_pydantic(balance_data)

    @strawberry.field
    async def timelogs(
        self,
        info: strawberry.Info,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> list[Annotated["TimeLog", strawberry.lazy("backend.graphql.types.time_tracking")]]:  # noqa: F821
        from backend import schemas
        from backend.graphql.types.time_tracking import TimeLog
        db = info.context["db"]
        current_user = info.context["current_user"]

        target_user_id = self.id
        if current_user.id != target_user_id and current_user.role.name not in ["admin", "super_admin"]:
            target_user_id = current_user.id

        from sqlalchemy import select

        from backend.database.models import TimeLog as DbTimeLog
        stmt = select(DbTimeLog).where(DbTimeLog.user_id == target_user_id)
        if start_date:
            stmt = stmt.where(DbTimeLog.start_time >= datetime.datetime.combine(start_date, datetime.time.min))
        if end_date:
            stmt = stmt.where(DbTimeLog.start_time <= datetime.datetime.combine(end_date, datetime.time.max))
        stmt = stmt.order_by(DbTimeLog.start_time.desc()).limit(50)
        result = await db.execute(stmt)
        return [TimeLog.from_pydantic(schemas.TimeLog.model_validate(item)) for item in result.scalars().all()]


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
    created_at: strawberry.auto
    expires_at: strawberry.auto
    last_used_at: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User | None:
        if not self.user_id:
            return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@strawberry.type
class PaginatedUsers:
    users: list[User]
    total_count: int
