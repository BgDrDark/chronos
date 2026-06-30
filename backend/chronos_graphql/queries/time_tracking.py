import datetime

import strawberry
from sqlalchemy import select

from backend.crud.repositories import time_repo
from backend.exceptions import AuthenticationException
from backend.chronos_graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class TimeTrackingQuery:
    @strawberry.field
    async def active_time_log(self, info: strawberry.Info) -> types.TimeLog | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return None
        db_log = await time_repo.get_active_timelog(db, current_user.id)
        if db_log:
            return types.TimeLog.from_pydantic(db_log)
        return None

    @strawberry.field
    async def time_logs(
        self,
        info: strawberry.Info,
        user_id: int | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        limit: int = 50,
    ) -> list[types.TimeLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        target_user_id = current_user.id
        if user_id:
            if current_user.role.name not in ["admin", "super_admin"]:
                target_user_id = current_user.id
            else:
                target_user_id = user_id

        from backend.database.models import TimeLog as DbTimeLog
        stmt = select(DbTimeLog).where(DbTimeLog.user_id == target_user_id)

        if start_date:
            stmt = stmt.where(DbTimeLog.start_time >= datetime.datetime.combine(start_date, datetime.time.min))
        if end_date:
            stmt = stmt.where(DbTimeLog.start_time <= datetime.datetime.combine(end_date, datetime.time.max))

        stmt = stmt.order_by(DbTimeLog.start_time.desc()).limit(limit)
        result = await db.execute(stmt)
        return [types.TimeLog.from_pydantic(item) for item in result.scalars().all()]
