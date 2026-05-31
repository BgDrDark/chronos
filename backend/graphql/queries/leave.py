import strawberry
from sqlalchemy import select

from backend.crud.repositories import time_repo
from backend.exceptions import AuthenticationException, PermissionDeniedException
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"

@strawberry.type
class LeaveQuery:
    @strawberry.field
    async def my_leave_requests(self, info: strawberry.Info) -> list[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import LeaveRequest as DbLeaveRequest
        stmt = select(DbLeaveRequest).where(DbLeaveRequest.user_id == current_user.id).order_by(DbLeaveRequest.created_at.desc())
        result = await db.execute(stmt)
        return [types.LeaveRequest.from_pydantic(item) for item in result.scalars().all()]

    @strawberry.field
    async def pending_leave_requests(self, info: strawberry.Info) -> list[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from backend.database.models import LeaveRequest as DbLeaveRequest
        from backend.database.models import User
        stmt = select(DbLeaveRequest).where(DbLeaveRequest.status == "pending").order_by(DbLeaveRequest.created_at.desc())
        if current_user.role.name != "super_admin":
            stmt = stmt.join(User, DbLeaveRequest.user_id == User.id).where(User.company_id == current_user.company_id)
        result = await db.execute(stmt)
        return [types.LeaveRequest.from_pydantic(item) for item in result.scalars().all()]

    @strawberry.field
    async def all_leave_requests(self, info: strawberry.Info, status: str | None = None) -> list[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from backend.database.models import LeaveRequest as DbLeaveRequest
        from backend.database.models import User
        stmt = select(DbLeaveRequest)
        if current_user.role.name != "super_admin":
            stmt = stmt.join(User, DbLeaveRequest.user_id == User.id).where(User.company_id == current_user.company_id)
        if status:
            stmt = stmt.where(DbLeaveRequest.status == status)
        stmt = stmt.order_by(DbLeaveRequest.created_at.desc())
        result = await db.execute(stmt)
        return [types.LeaveRequest.from_pydantic(item) for item in result.scalars().all()]

    @strawberry.field
    async def leave_balance(self, user_id: int, year: int, info: strawberry.Info) -> types.LeaveBalance:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        if current_user.id != user_id and current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        balances = await time_repo.get_leave_balance(db, user_id, year)
        balance = balances[0] if balances else None
        if not balance:
            from backend.database.models import LeaveBalance as DbLeaveBalance
            balance = DbLeaveBalance(user_id=user_id, year=year, total_days=20, used_days=0)
            db.add(balance)
            await db.flush()
        from backend import schemas as sch
        balance_schema = sch.LeaveBalance.model_validate(balance)
        if balance_schema.total_days is None:
            balance_schema.total_days = 20
        if balance_schema.used_days is None:
            balance_schema.used_days = 0
        return types.LeaveBalance.from_pydantic(balance_schema)
