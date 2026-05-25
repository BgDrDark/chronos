import datetime

import strawberry
from sqlalchemy import select

from backend.crud.repositories import user_repo
from backend.exceptions import AuthenticationException, PermissionDeniedException
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class UserQuery:
    @strawberry.field
    async def me(self, info: strawberry.Info) -> types.User:
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        return types.User.from_pydantic(current_user)

    @strawberry.field
    async def users(
        self,
        info: strawberry.Info,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> types.PaginatedUsers:
        db = info.context["db"]
        current_user = info.context["current_user"]
        allowed_roles = ["admin", "super_admin", "accountant", "manager"]
        if current_user is None or current_user.role is None or current_user.role.name not in allowed_roles:
            raise PermissionDeniedException()

        # Isolation: Non-super_admin sees only their company
        company_id = None
        if current_user.role.name != "super_admin":
            company_id = current_user.company_id

        db_users = await user_repo.get_users(db, skip=skip, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order, company_id=company_id)
        total_count = await user_repo.count_users(db, search=search, company_id=company_id)

        return types.PaginatedUsers(
            users=[types.User.from_pydantic(user) for user in db_users],
            total_count=total_count or 0,
        )

    @strawberry.field
    async def all_users(
        self,
        info: strawberry.Info,
        search: str | None = None,
    ) -> list[types.User]:
        """Връща всички потребители като плосък списък (за старите компоненти)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin", "accountant", "manager"]:
            raise PermissionDeniedException.for_action("view records")

        company_id = current_user.company_id if current_user.role.name != "super_admin" else None
        db_users = await user_repo.get_users(db, skip=0, limit=1000, search=search, company_id=company_id)
        return [types.User.from_pydantic(u) for u in db_users]

    @strawberry.field
    async def user(self, info: strawberry.Info, id: int | None = None) -> types.User | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise AuthenticationException()

        target_id = id if id is not None else current_user.id

        if current_user.role.name not in ["admin", "super_admin"] and current_user.id != target_id:
            raise PermissionDeniedException.for_action("access")

        db_user = await user_repo.get_by_id(db, target_id)
        if db_user:
            return types.User.from_pydantic(db_user)
        return None

    @strawberry.field
    async def user_presences(
        self,
        info: strawberry.Info,
        date: datetime.date,
        status: types.PresenceStatus | None = None,
    ) -> list[types.UserPresence]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from sqlalchemy import and_, or_
        from sqlalchemy.orm import selectinload

        from backend.database.models import (
            LeaveRequest,
            TimeLog,
            User,
            WorkSchedule,
            sofia_now,
        )

        # 1. Fetch all active users from the current company only
        users_result = await db.execute(
            select(User).where(
                User.is_active,
                User.company_id == current_user.company_id,
            ),
        )
        users = users_result.scalars().all()

        # 2. Fetch all schedules for the date
        schedules_result = await db.execute(
            select(WorkSchedule)
            .where(WorkSchedule.date == date)
            .options(selectinload(WorkSchedule.shift)),
        )
        schedules_map = {s.user_id: s for s in schedules_result.scalars().all()}

        # 3. Fetch logs
        start_dt = datetime.datetime.combine(date, datetime.time.min)
        end_dt = datetime.datetime.combine(date, datetime.time.max)

        logs_result = await db.execute(
            select(TimeLog)
            .where(or_(
                and_(TimeLog.start_time >= start_dt, TimeLog.start_time <= end_dt),
                and_(TimeLog.start_time < start_dt, TimeLog.end_time.is_(None)),
            ))
            .order_by(TimeLog.start_time.asc()),
        )
        user_logs = {}
        for log in logs_result.scalars().all():
            if log.user_id not in user_logs: user_logs[log.user_id] = []
            user_logs[log.user_id].append(log)

        # 4. Fetch Approved Leaves for the date
        leaves_result = await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.status == "approved")
            .where(LeaveRequest.start_date <= date)
            .where(LeaveRequest.end_date >= date),
        )
        leaves_map = {l.user_id: l for l in leaves_result.scalars().all()}

        results = []
        now = sofia_now()
        is_today = (date == now.date())
        current_time = now.time() if is_today else datetime.time(23, 59, 59)

        for u in users:
            schedule = schedules_map.get(u.id)
            logs = user_logs.get(u.id, [])
            leave = leaves_map.get(u.id)

            shift_start = None
            shift_end = None

            # --- Determine Status ---
            p_status = types.PresenceStatus.OFF_DUTY  # Default

            # 1. Determine Shift Times (needed for UI even if logs exist)
            if schedule and schedule.shift:
                shift_start = schedule.shift.start_time
                shift_end = schedule.shift.end_time

            # 2. Check Active Presence (Highest Priority)
            is_present = False
            has_logs = bool(logs)

            if has_logs:
                last_log = logs[-1]
                if last_log.end_time is None:
                    p_status = types.PresenceStatus.ON_DUTY
                    is_present = True
                else:
                    p_status = types.PresenceStatus.OFF_DUTY  # Finished work

            # 3. Check Leave (If NOT present)
            if not is_present and leave:
                if leave.leave_type == "sick_leave":
                    p_status = types.PresenceStatus.SICK_LEAVE
                else:
                    p_status = types.PresenceStatus.PAID_LEAVE

            # 4. Check Schedule Logic (If NOT present and NOT on leave)
            if not is_present and not leave:
                if schedule and schedule.shift:
                    if is_today and shift_start and shift_end:
                        if current_time < shift_start:
                            p_status = types.PresenceStatus.OFF_DUTY
                        elif current_time >= shift_start and current_time <= shift_end:
                            p_status = types.PresenceStatus.LATE
                        elif current_time > shift_end:
                            p_status = types.PresenceStatus.ABSENT
                    else:
                        p_status = types.PresenceStatus.ABSENT
                else:
                    p_status = types.PresenceStatus.OFF_DUTY

            first_log = logs[0] if logs else None
            last_log = logs[-1] if logs else None
            actual_arrival = first_log.start_time if first_log else None
            actual_departure = last_log.end_time if last_log else None
            is_on_duty = bool(last_log and last_log.end_time is None)

            if status and p_status != status:
                continue

            results.append(types.UserPresence(
                user=types.User.from_pydantic(u),
                shift_start=shift_start,
                shift_end=shift_end,
                actual_arrival=actual_arrival,
                actual_departure=actual_departure,
                status=p_status,
                is_on_duty=is_on_duty,
            ))

        return results

    @strawberry.field
    async def active_sessions(self, info: strawberry.Info, skip: int = 0, limit: int = 100) -> list[types.UserSession]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view active sessions")

        sessions = await user_repo.get_active_sessions(db, skip=skip, limit=limit)
        return [types.UserSession.from_pydantic(s) for s in sessions]
