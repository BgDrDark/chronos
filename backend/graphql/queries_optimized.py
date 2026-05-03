"""
Optimized GraphQL Queries
Fixed N+1 problems with comprehensive batching and optimized data loading
"""

import strawberry
import datetime
import asyncio
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import select, Time, desc, and_, func, extract, or_

from backend.graphql import types
from backend import crud, schemas
from backend.config import settings
from backend.services.payroll_calculator import PayrollCalculator
from backend.graphql.dataloaders_optimized import (
    create_optimized_dataloaders,
    DataLoaderFactory
)
from backend.database.models import (
    User, TimeLog, WorkSchedule, LeaveRequest, 
    sofia_now, Shift, Payslip, UserSession
)

@strawberry.type
class OptimizedQuery:
    """Optimized GraphQL Query resolver with N+1 problem fixes"""
    
    @strawberry.field
    async def hello(self) -> str:
        return "Hello World - Optimized!"

    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[types.User]:
        current_user = info.context["current_user"]
        if current_user:
            # Use the data loader for consistent loading
            dataloaders = info.context.get("dataloaders")
            if dataloaders:
                user_loader = dataloaders["user_by_id"]
                users = await user_loader.load_many([current_user.id])
                return types.User.from_instance(users[0]) if users[0] else None
            else:
                return types.User.from_instance(current_user)
        return None

    @strawberry.field
    async def active_time_log(self, info: strawberry.Info) -> Optional[types.TimeLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return None
        
        # Use optimized timelog loader for active timelogs
        dataloaders = create_optimized_dataloaders(db)
        timelog_loader = dataloaders["timelog_loader"]
        
        active_timelogs = await timelog_loader.load_active_timelogs([current_user.id])
        active_log = active_timelogs[0] if active_timelogs[0] else None
        
        if active_log:
            return types.TimeLog.from_instance(active_log)
        return None

    @strawberry.field
    async def users(
        self, 
        info: strawberry.Info, 
        skip: int = 0, 
        limit: int = 10, 
        search: Optional[str] = None, 
        sort_by: str = "id", 
        sort_order: str = "asc"
    ) -> types.PaginatedUsers:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise Exception("Operation not permitted")
        
        # Use optimized user loader
        dataloaders = create_optimized_dataloaders(db)
        user_loader = dataloaders["user_by_id"]
        users = await user_loader.load_many([target_id])
        db_user = users[0] if users else None
        
        if db_user:
            return types.User.from_instance(db_user)
        return None

    @strawberry.field
    async def roles(self, info: strawberry.Info) -> List[types.Role]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted for this user role")
        
        # Use optimized role loading
        from backend.graphql.dataloaders_optimized import load_roles_by_ids
        db_roles = await crud.get_roles(db)
        role_ids = [role.id for role in db_roles]
        
        # Load roles with their relationships
        roles_with_users = await load_roles_by_ids(db, role_ids)
        return [types.Role.from_instance(role) for role in roles_with_users if role]
    
    @strawberry.field
    async def role(self, id: int, info: strawberry.Info) -> Optional[types.Role]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted for this user role")
        
        from backend.graphql.dataloaders_optimized import load_roles_by_ids
        roles = await load_roles_by_ids(db, [id])
        db_role = roles[0] if roles else None
        
        if db_role:
            return types.Role.from_instance(db_role)
        return None

    @strawberry.field
    async def shifts(self, info: strawberry.Info) -> List[types.Shift]:
        db = info.context["db"]
        # Use batch loading for shifts
        db_shifts = await crud.get_shifts(db)
        return [types.Shift.from_instance(s) for s in db_shifts]

    @strawberry.field
    async def my_schedules(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        info: strawberry.Info
    ) -> List[types.WorkSchedule]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return []
        
        # Use optimized schedule loader
        dataloaders = create_optimized_dataloaders(db)
        schedule_loader = dataloaders["schedule_loader"]
        
        schedules = await schedule_loader.load_schedules_by_users_date([
            (current_user.id, start_date, end_date)
        ])
        
        return [types.WorkSchedule.from_instance(s) for s in schedules[0]]

    @strawberry.field
    async def work_schedules(
        self, 
        start_date: datetime.date, 
        end_date: datetime.date, 
        info: strawberry.Info
    ) -> List[types.WorkSchedule]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")
        
        # Get all users first, then batch load schedules
        users = await crud.get_users(db, limit=1000)  # Adjust limit as needed
        user_ids = [user.id for user in users]
        
        dataloaders = create_optimized_dataloaders(db)
        schedule_loader = dataloaders["schedule_loader"]
        
        # Batch load schedules for all users
        schedule_keys = [(user_id, start_date, end_date) for user_id in user_ids]
        all_schedules = await schedule_loader.load_schedules_by_users_date(schedule_keys)
        
        # Flatten and return all schedules
        result = []
        for user_schedules in all_schedules:
            result.extend(user_schedules)
        
        return [types.WorkSchedule.from_instance(s) for s in result]

    @strawberry.field
    async def time_logs(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        info: strawberry.Info
    ) -> List[types.TimeLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted for this user role")
        
        # Convert aware to naive UTC to match DB TIMESTAMP WITHOUT TIME ZONE
        query_start = start_date
        if query_start.tzinfo is not None:
            query_start = query_start.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            
        query_end = end_date
        if query_end.tzinfo is not None:
            query_end = query_end.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        
        # Use optimized timelog loader
        dataloaders = create_optimized_dataloaders(db)
        timelog_loader = dataloaders["timelog_loader"]
        
        # Get all users first
        users = await crud.get_users(db, limit=1000)
        user_ids = [user.id for user in users]
        
        # Batch load timelogs for all users
        date_start = query_start.date()
        date_end = query_end.date()
        timelog_keys = [(user_id, date_start, date_end) for user_id in user_ids]
        
        all_timelogs = await timelog_loader.load_timelogs_by_user_date(timelog_keys)
        
        # Filter by exact datetime range and flatten
        result = []
        for user_timelogs in all_timelogs:
            for log in user_timelogs:
                if query_start <= log.start_time <= query_end:
                    result.append(log)
        
        # Load users in batch for the timelogs
        timelog_user_ids = list({log.user_id for log in result})
        if timelog_user_ids:
            user_loader = dataloaders["user_by_id"]
            users_map = {user.id: user for user in await user_loader.load_many(timelog_user_ids)}
        else:
            users_map = {}
        
        return [types.TimeLog.from_instance(l) for l in result]

    @strawberry.field
    async def my_leave_requests(self, info: strawberry.Info) -> List[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return []
        
        # Use optimized leave loader
        dataloaders = create_optimized_dataloaders(db)
        leave_loader = dataloaders["leave_loader"]
        
        # Load leaves for a wide date range (past 2 years to future 1 year)
        start_date = datetime.date.today() - datetime.timedelta(days=730)
        end_date = datetime.date.today() + datetime.timedelta(days=365)
        
        user_leaves = await leave_loader.load_leaves_by_users_date([
            (current_user.id, start_date, end_date)
        ])
        
        return [types.LeaveRequest.from_instance(l) for l in user_leaves[0]]

    @strawberry.field
    async def pending_leave_requests(self, info: strawberry.Info) -> List[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")
        
        # Use optimized leave loader for pending requests
        dataloaders = create_optimized_dataloaders(db)
        leave_loader = dataloaders["leave_loader"]
        
        pending_leaves = await leave_loader.load_pending_leaves()
        return [types.LeaveRequest.from_instance(r) for r in pending_leaves]

    @strawberry.field
    async def all_leave_requests(self, info: strawberry.Info, status: Optional[str] = None) -> List[types.LeaveRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")
        
        # For admin, use the optimized CRUD function
        reqs = await crud.get_leave_requests(db, status=status)
        return [types.LeaveRequest.from_instance(r) for r in reqs]

    @strawberry.field
    async def leave_balance(self, user_id: int, year: int, info: strawberry.Info) -> types.LeaveBalance:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        if current_user is None:
             raise Exception("Not authenticated")
             
        if current_user.id != user_id and current_user.role.name != "admin":
             raise Exception("Operation not permitted")
             
        balance = await crud.get_leave_balance(db, user_id, year)
        return types.LeaveBalance.from_instance(balance)

    @strawberry.field
    async def companies(self, info: strawberry.Info) -> List[types.Company]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise Exception("Not authenticated")
        
        res = await crud.get_companies(db)
        return [types.Company.from_instance(c) for c in res]

    @strawberry.field
    async def departments(self, info: strawberry.Info, company_id: Optional[int] = None) -> List[types.Department]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise Exception("Not authenticated")
            
        res = await crud.get_departments(db, company_id)
        return [types.Department.from_instance(d) for d in res]

    @strawberry.field
    async def positions(self, info: strawberry.Info, department_id: Optional[int] = None) -> List[types.Position]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise Exception("Not authenticated")
            
        res = await crud.get_positions(db, department_id)
        return [types.Position.from_instance(p) for p in res]

    @strawberry.field
    async def public_holidays(self, info: strawberry.Info, year: Optional[int] = None) -> List[types.PublicHoliday]:
        db = info.context["db"]
        from sqlalchemy import select, extract
        from backend.database.models import PublicHoliday
        
        stmt = select(PublicHoliday)
        if year:
            stmt = stmt.where(extract('year', PublicHoliday.date) == year)
        
        result = await db.execute(stmt)
        return [types.PublicHoliday.from_instance(h) for h in result.scalars().all()]

    @strawberry.field
    async def orthodox_holidays(self, info: strawberry.Info, year: Optional[int] = None) -> List[types.OrthodoxHoliday]:
        db = info.context["db"]
        from sqlalchemy import select, extract
        from backend.database.models import OrthodoxHoliday
        
        stmt = select(OrthodoxHoliday)
        if year:
            stmt = stmt.where(extract('year', OrthodoxHoliday.date) == year)
        
        result = await db.execute(stmt)
        return [types.OrthodoxHoliday.from_instance(h) for h in result.scalars().all()]

    @strawberry.field
    async def user_presences(
        self,
        info: strawberry.Info,
        date: datetime.date,
        status: Optional[types.PresenceStatus] = None
    ) -> List[types.UserPresence]:
        """
        OPTIMIZED VERSION: Uses batch loading to eliminate N+1 queries
        """
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")

        # Use the optimized presence data loader
        dataloaders = create_optimized_dataloaders(db)
        presence_loader = dataloaders["presence_loader"]
        
        # Load all presence data in a few optimized queries
        presence_data = await presence_loader.load_presence_data(date)
        
        results = []
        now = sofia_now()
        is_today = (date == now.date())
        current_time = now.time() if is_today else datetime.time(23, 59, 59)

        for user_id, data in presence_data.items():
            user = data['user']
            schedule = data['schedule']
            logs = data['timelogs']
            leave = data['leave']

            shift_start = None
            shift_end = None
            
            # Determine Status
            p_status = types.PresenceStatus.OFF_DUTY  # Default
            
            # Determine Shift Times
            if schedule and schedule.shift:
                shift_start = schedule.shift.start_time
                shift_end = schedule.shift.end_time

            # Check Active Presence (Highest Priority)
            is_present = False
            has_logs = bool(logs)
            
            if has_logs:
                last_log = logs[-1]
                if last_log.end_time is None:
                    p_status = types.PresenceStatus.ON_DUTY
                    is_present = True
                else:
                    p_status = types.PresenceStatus.OFF_DUTY  # Finished work

            # Check Leave (If NOT present)
            if not is_present and leave:
                if leave.leave_type == "sick_leave":
                    p_status = types.PresenceStatus.SICK_LEAVE
                else:
                    p_status = types.PresenceStatus.PAID_LEAVE
            
            # Check Schedule Logic (If NOT present and NOT on leave)
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

            # Map Data
            first_log = logs[0] if logs else None
            last_log = logs[-1] if logs else None
            actual_arrival = first_log.start_time if first_log else None
            actual_departure = last_log.end_time if last_log else None
            is_on_duty = bool(last_log and last_log.end_time is None)

            if status and p_status != status:
                continue
                
            results.append(types.UserPresence(
                user=types.User.from_instance(user),
                shift_start=shift_start,
                shift_end=shift_end,
                actual_arrival=actual_arrival,
                actual_departure=actual_departure,
                status=p_status,
                is_on_duty=is_on_duty
            ))
            
        return results

    @strawberry.field
    async def smtp_settings(self, info: strawberry.Info) -> Optional[types.SmtpSettings]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
             raise Exception("Operation not permitted")

        server = await crud.get_global_setting(db, "smtp_server")
        port = await crud.get_global_setting(db, "smtp_port")
        username = await crud.get_global_setting(db, "smtp_username")
        password = await crud.get_global_setting(db, "smtp_password") 
        sender = await crud.get_global_setting(db, "sender_email")
        tls = await crud.get_global_setting(db, "use_tls")

        if not server:
            return None

        return types.SmtpSettings(
            smtp_server=server,
            smtp_port=int(port) if port else 587,
            smtp_username=username or "",
            smtp_password=password or "",
            sender_email=sender or "",
            use_tls=tls == "True"
        )

    @strawberry.field
    async def user_daily_stats(
        self,
        info: strawberry.Info,
        user_id: int,
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[types.DailyStat]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name != "admin":
             raise Exception("Operation not permitted")

        calculator = PayrollCalculator(db)
        stats = await calculator.get_daily_stats(user_id, start_date, end_date)
        
        return [
            types.DailyStat(
                date=s["date"],
                total_worked_hours=s["total_worked_hours"],
                regular_hours=s["regular_hours"],
                overtime_hours=s["overtime_hours"],
                is_work_day=s["is_work_day"],
                shift_name=s["shift_name"],
                actual_arrival=s.get("actual_arrival"),
                actual_departure=s.get("actual_departure")
            )
            for s in stats
        ]

    @strawberry.field
    async def my_daily_stats(
        self,
        info: strawberry.Info,
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[types.DailyStat]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return []

        calculator = PayrollCalculator(db)
        stats = await calculator.get_daily_stats(current_user.id, start_date, end_date)
        
        return [
            types.DailyStat(
                date=s["date"],
                total_worked_hours=s["total_worked_hours"],
                regular_hours=s["regular_hours"],
                overtime_hours=s["overtime_hours"],
                is_work_day=s["is_work_day"],
                shift_name=s["shift_name"],
                actual_arrival=s.get("actual_arrival"),
                actual_departure=s.get("actual_departure")
            )
            for s in stats
        ]

    @strawberry.field
    async def office_location(self, info: strawberry.Info) -> Optional[types.OfficeLocation]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None

        lat = await crud.get_global_setting(db, "office_latitude")
        lon = await crud.get_global_setting(db, "office_longitude")
        rad = await crud.get_global_setting(db, "office_radius")
        entry_enabled = await crud.get_global_setting(db, "geofencing_entry_enabled")
        exit_enabled = await crud.get_global_setting(db, "geofencing_exit_enabled")
        
        return types.OfficeLocation(
            latitude=float(lat) if lat else 0.0,
            longitude=float(lon) if lon else 0.0,
            radius=int(rad) if rad else 100,
            entry_enabled=(entry_enabled == "True"),
            exit_enabled=(exit_enabled == "True")
        )

    @strawberry.field
    async def global_payroll_config(self, info: strawberry.Info) -> types.GlobalPayrollConfig:
        db = info.context["db"]
        config = await crud.get_global_payroll_config(db)
        
        return types.GlobalPayrollConfig(
            hourly_rate=Decimal(str(config.hourly_rate)),
            monthly_salary=Decimal(str(config.monthly_salary)),
            overtime_multiplier=Decimal(str(config.overtime_multiplier)),
            standard_hours_per_day=config.standard_hours_per_day,
            currency=config.currency,
            annual_leave_days=config.annual_leave_days,
            tax_percent=Decimal(str(config.tax_percent)),
            health_insurance_percent=Decimal(str(config.health_insurance_percent)),
            has_tax_deduction=config.has_tax_deduction,
            has_health_insurance=config.has_health_insurance,
            qr_regen_interval_minutes=settings.QR_TOKEN_REGEN_MINUTES
        )

    @strawberry.field
    async def weekly_summary(
        self, 
        info: strawberry.Info, 
        date: Optional[datetime.date] = None,
        user_id: Optional[int] = None
    ) -> Optional[types.WeeklySummary]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None
        
        target_user_id = current_user.id
        if user_id:
            if current_user.role.name != "admin" and current_user.id != user_id:
                raise Exception("Operation not permitted")
            target_user_id = user_id
            
        ref_date = date if date else datetime.datetime.now().date()
        
        calculator = PayrollCalculator(db)
        
        config = await crud.get_payroll_config(db, target_user_id)
        daily_hours = config.standard_hours_per_day if config and config.standard_hours_per_day else 8
        target = float(daily_hours * 5)
        
        summary = await calculator.get_weekly_summary(target_user_id, ref_date, target)
        
        return types.WeeklySummary(
            start_date=summary["start_date"],
            end_date=summary["end_date"],
            total_regular_hours=Decimal(str(summary["total_regular_hours"])),
            total_overtime_hours=Decimal(str(summary["total_overtime_hours"])),
            target_hours=Decimal(str(summary["target_hours"])),
            debt_hours=Decimal(str(summary["debt_hours"])),
            surplus_hours=Decimal(str(summary["surplus_hours"])),
            status_message=summary["status_message"]
        )

    @strawberry.field
    async def monthly_work_days(
        self,
        info: strawberry.Info,
        year: int,
        month: int
    ) -> Optional[types.MonthlyWorkDays]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None
        
        res = await crud.get_monthly_work_days(db, year, month)
        if res:
            return types.MonthlyWorkDays.from_instance(res)
        return None

    @strawberry.field
    async def active_sessions(self, info: strawberry.Info, skip: int = 0, limit: int = 100) -> List[types.UserSession]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")
        
        sessions = await crud.get_active_sessions(db, skip=skip, limit=limit)
        return [types.UserSession.from_instance(s) for s in sessions]

    @strawberry.field
    async def audit_logs(
        self, 
        info: strawberry.Info, 
        skip: int = 0, 
        limit: int = 100,
        action: Optional[str] = None
    ) -> List[types.AuditLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")
        
        from sqlalchemy import select, desc
        from backend.database.models import AuditLog as DbAuditLog
        
        stmt = select(DbAuditLog).order_by(desc(DbAuditLog.created_at))
        if action:
            stmt = stmt.where(DbAuditLog.action == action)
            
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return [types.AuditLog.from_instance(log) for log in result.scalars().all()]

    # Continue with other optimized field resolvers...
    # (Other methods would follow the same optimization pattern)
    
    @strawberry.field
    async def my_swap_requests(self, info: strawberry.Info) -> List[types.ShiftSwapRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return []
        res = await crud.get_my_swap_requests(db, current_user.id)
        return [types.ShiftSwapRequest.from_instance(s) for s in res]

    @strawberry.field
    async def pending_admin_swaps(self, info: strawberry.Info) -> List[types.ShiftSwapRequest]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")
        res = await crud.get_all_pending_swaps(db)
        return [types.ShiftSwapRequest.from_instance(s) for s in res]

    @strawberry.field
    async def management_stats(self, info: strawberry.Info) -> types.ManagementStats:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "admin":
            raise Exception("Operation not permitted")

        from sqlalchemy import func, extract
        from backend.database.models import Payslip, TimeLog, WorkSchedule, Shift, User
        
        # 1. Overtime by Month (last 12 months)
        stmt_ot = select(
            func.to_char(Payslip.period_start, 'YYYY-MM').label('month'),
            func.sum(Payslip.overtime_amount).label('total_ot')
        ).group_by('month').order_by('month').limit(12)
        
        res_ot = await db.execute(stmt_ot)
        overtime_data = [
            types.OvertimeStat(month=row[0], amount=Decimal(str(row[1])))
            for row in res_ot.all()
        ]

        # 2. Lateness by User (Top 10)
        cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
        
        stmt_late = select(
            User.first_name,
            User.last_name,
            func.count(TimeLog.id).label('late_count')
        ).join(TimeLog, User.id == TimeLog.user_id).join(
            WorkSchedule, (User.id == WorkSchedule.user_id) & (func.date(TimeLog.start_time) == WorkSchedule.date)
        ).join(
            Shift, WorkSchedule.shift_id == Shift.id
        ).where(
            TimeLog.start_time > cutoff,
            func.cast(TimeLog.start_time, Time) > Shift.start_time
        ).group_by(User.id).order_by(desc('late_count')).limit(10)

        res_late = await db.execute(stmt_late)
        lateness_data = [
            types.LatenessStat(user_name=f"{row[0]} {row[1]}", count=row[2])
            for row in res_late.all()
        ]

        return types.ManagementStats(
            overtime_by_month=overtime_data,
            lateness_by_user=lateness_data
        )

# Create optimized query instance
OptimizedQueryInstance = OptimizedQuery

# Export for use in schema
__all__ = ['OptimizedQuery', 'OptimizedQueryInstance']
