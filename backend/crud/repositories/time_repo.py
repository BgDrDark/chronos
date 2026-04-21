from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete as sql_delete
from sqlalchemy.orm import selectinload
from backend.database.models import TimeLog, Shift, WorkSchedule, LeaveRequest, LeaveBalance, Role, ScheduleTemplate, ScheduleTemplateItem, ShiftSwapRequest
from backend.schemas import RoleCreate
from .base import BaseRepository


class TimeTrackingRepository(BaseRepository):
    """Repository за проследяване на работно време"""
    
    model = TimeLog
    
    async def get_active_timelog(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[TimeLog]:
        """Връща активния TimeLog за потребител"""
        result = await db.execute(
            select(TimeLog)
            .where(TimeLog.user_id == user_id)
            .where(TimeLog.end_time == None)
        )
        return result.scalar_one_or_none()
    
    async def get_user_timelogs(
        self, 
        db: AsyncSession, 
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        limit: int = 100
    ) -> List[TimeLog]:
        """Връща всички TimeLog за потребител"""
        query = select(TimeLog).where(TimeLog.user_id == user_id)
        
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(TimeLog.start_time >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.where(TimeLog.start_time <= end_dt)
        
        query = query.order_by(TimeLog.start_time.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_schedule_for_date(
        self,
        db: AsyncSession,
        user_id: int,
        schedule_date: date
    ) -> Optional[WorkSchedule]:
        """Връща график за конкретна дата"""
        result = await db.execute(
            select(WorkSchedule)
            .where(WorkSchedule.user_id == user_id)
            .where(WorkSchedule.date == schedule_date)
        )
        return result.scalar_one_or_none()
    
    async def get_shift_by_id(self, db: AsyncSession, shift_id: int) -> Optional[Shift]:
        """Връща смяна по ID"""
        result = await db.execute(
            select(Shift).where(Shift.id == shift_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_shifts(
        self, 
        db: AsyncSession, 
        company_id: int = None
    ) -> List[Shift]:
        """Връща всички смени"""
        query = select(Shift)
        if company_id:
            query = query.where(Shift.company_id == company_id)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_user_leave_requests(
        self,
        db: AsyncSession,
        user_id: int,
        status: str = None
    ) -> List[LeaveRequest]:
        """Връща заявки за отпуска на потребител"""
        query = select(LeaveRequest).where(LeaveRequest.user_id == user_id)
        if status:
            query = query.where(LeaveRequest.status == status)
        query = query.order_by(LeaveRequest.start_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_leave_balance(
        self,
        db: AsyncSession,
        user_id: int,
        year: int = None
    ) -> List[LeaveBalance]:
        """Връща баланс на отпуски"""
        query = select(LeaveBalance).where(LeaveBalance.user_id == user_id)
        if year:
            query = query.where(LeaveBalance.year == year)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def create_shift(
        self,
        db: AsyncSession,
        name: str,
        start_time: datetime.time,
        end_time: datetime.time,
        tolerance_minutes: int = 15,
        break_duration_minutes: int = 0,
        pay_multiplier: float = 1.0,
        shift_type: str = "regular"
    ) -> Shift:
        """Създава нова смяна"""
        shift = Shift(
            name=name,
            start_time=start_time,
            end_time=end_time,
            tolerance_minutes=tolerance_minutes,
            break_duration_minutes=break_duration_minutes,
            pay_multiplier=pay_multiplier,
            shift_type=shift_type
        )
        db.add(shift)
        await db.flush()
        await db.refresh(shift)
        return shift
    
    async def update_shift(
        self,
        db: AsyncSession,
        shift_id: int,
        name: str = None,
        start_time: datetime.time = None,
        end_time: datetime.time = None,
        tolerance_minutes: int = None,
        break_duration_minutes: int = None,
        pay_multiplier: float = None,
        shift_type: str = None
    ) -> Optional[Shift]:
        """Обновява смяна"""
        shift = await self.get_shift_by_id(db, shift_id)
        if not shift:
            return None
        
        if name is not None:
            shift.name = name
        if start_time is not None:
            shift.start_time = start_time
        if end_time is not None:
            shift.end_time = end_time
        if tolerance_minutes is not None:
            shift.tolerance_minutes = tolerance_minutes
        if break_duration_minutes is not None:
            shift.break_duration_minutes = break_duration_minutes
        if pay_multiplier is not None:
            shift.pay_multiplier = pay_multiplier
        if shift_type is not None:
            shift.shift_type = shift_type
        
        await db.flush()
        await db.refresh(shift)
        return shift
    
    async def delete_shift(self, db: AsyncSession, shift_id: int) -> bool:
        """Изтрива смяна"""
        shift = await self.get_shift_by_id(db, shift_id)
        if shift:
            await db.delete(shift)
            await db.flush()
            return True
        return False
    
    async def get_all_roles(self, db: AsyncSession) -> List[Role]:
        """Връща всички роли"""
        result = await db.execute(select(Role))
        return list(result.scalars().all())
    
    async def get_role_by_id(self, db: AsyncSession, role_id: int) -> Optional[Role]:
        """Връща роля по ID"""
        result = await db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()
    
    async def create_role(self, db: AsyncSession, role_data: RoleCreate) -> Role:
        """Създава нова роля"""
        role = Role(name=role_data.name, description=role_data.description)
        db.add(role)
        await db.flush()
        await db.refresh(role)
        return role
    
    async def update_role(
        self,
        db: AsyncSession,
        role_id: int,
        name: str = None,
        description: str = None
    ) -> Optional[Role]:
        """Обновява роля"""
        role = await self.get_role_by_id(db, role_id)
        if not role:
            return None
        
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        
        await db.flush()
        await db.refresh(role)
        return role
    
    async def delete_role(self, db: AsyncSession, role_id: int) -> bool:
        """Изтрива роля"""
        role = await self.get_role_by_id(db, role_id)
        if role:
            await db.delete(role)
            await db.flush()
            return True
        return False
    
    async def create_schedule_template(
        self,
        db: AsyncSession,
        name: str,
        company_id: int,
        description: str = None,
        items: List[dict] = None
    ) -> ScheduleTemplate:
        """Създава шаблон за график"""
        template = ScheduleTemplate(name=name, company_id=company_id, description=description)
        db.add(template)
        await db.flush()
        
        if items:
            for item in items:
                tmpl_item = ScheduleTemplateItem(
                    template_id=template.id,
                    day_index=item.get("day_index"),
                    shift_id=item.get("shift_id")
                )
                db.add(tmpl_item)
        
        await db.flush()
        await db.refresh(template)
        return template
    
    async def delete_schedule_template(
        self,
        db: AsyncSession,
        template_id: int,
        company_id: int = None
    ) -> bool:
        """Изтрива шаблон за график"""
        template = await db.get(ScheduleTemplate, template_id)
        if template:
            if company_id and template.company_id != company_id:
                return False
            await db.delete(template)
            await db.flush()
            return True
        return False
    
    async def get_leave_requests(
        self,
        db: AsyncSession,
        user_id: int = None,
        status: str = None
    ) -> List[LeaveRequest]:
        """Връща заявки за отпуска"""
        query = select(LeaveRequest).options(selectinload(LeaveRequest.user)).order_by(LeaveRequest.created_at.desc())
        if user_id:
            query = query.where(LeaveRequest.user_id == user_id)
        if status:
            query = query.where(LeaveRequest.status == status)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def create_manual_time_log(
        self,
        db: AsyncSession,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        break_duration_minutes: int = 0,
        notes: str = None,
        is_manual: bool = True
    ) -> TimeLog:
        """Създава ръчен запис за време"""
        log = TimeLog(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            break_duration_minutes=break_duration_minutes,
            notes=notes,
            is_manual=is_manual
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log
    
    async def update_time_log(
        self,
        db: AsyncSession,
        log_id: int,
        start_time: datetime = None,
        end_time: datetime = None,
        is_manual: bool = False,
        break_duration_minutes: int = 0,
        notes: str = None
    ) -> Optional[TimeLog]:
        """Обновява запис за време"""
        log = await db.get(TimeLog, log_id)
        if not log:
            return None
        
        if start_time is not None:
            log.start_time = start_time
        if end_time is not None:
            log.end_time = end_time
        if is_manual is not None:
            log.is_manual = is_manual
        if break_duration_minutes is not None:
            log.break_duration_minutes = break_duration_minutes
        if notes is not None:
            log.notes = notes
        
        await db.flush()
        await db.refresh(log)
        return log
    
    async def delete_time_log(self, db: AsyncSession, log_id: int) -> bool:
        """Изтрива запис за време"""
        log = await db.get(TimeLog, log_id)
        if log:
            await db.delete(log)
            await db.flush()
            return True
        return False
    
    async def start_time_log(
        self,
        db: AsyncSession,
        user_id: int,
        latitude: float = None,
        longitude: float = None,
        custom_time: datetime = None
    ) -> TimeLog:
        """Започва работно време"""
        from backend.config import settings
        from datetime import timezone
        from zoneinfo import ZoneInfo
        
        sofia_tz = ZoneInfo(settings.TIMEZONE)
        
        if custom_time:
            start_time = custom_time
        else:
            start_time = datetime.now(sofia_tz).replace(tzinfo=None)
        
        log = TimeLog(
            user_id=user_id,
            start_time=start_time,
            latitude=latitude,
            longitude=longitude
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log
    
    async def end_time_log(
        self,
        db: AsyncSession,
        user_id: int,
        latitude: float = None,
        longitude: float = None,
        notes: str = None,
        custom_time: datetime = None
    ) -> Optional[TimeLog]:
        """Приключва работно време"""
        from backend.config import settings
        from datetime import timezone
        from zoneinfo import ZoneInfo
        
        active_log = await self.get_active_timelog(db, user_id)
        if not active_log:
            return None
        
        sofia_tz = ZoneInfo(settings.TIMEZONE)
        
        if custom_time:
            end_time = custom_time
        else:
            end_time = datetime.now(sofia_tz).replace(tzinfo=None)
        
        active_log.end_time = end_time
        active_log.latitude = latitude or active_log.latitude
        active_log.longitude = longitude or active_log.longitude
        active_log.notes = notes
        
        await db.flush()
        await db.refresh(active_log)
        return active_log
    
    async def get_leave_request_by_id(self, db: AsyncSession, request_id: int) -> Optional[LeaveRequest]:
        """Връща заявка за отпуск по ID"""
        result = await db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def update_leave_request_status(
        self,
        db: AsyncSession,
        request_id: int,
        status: str,
        admin_comment: str = None,
        employer_top_up: bool = False
    ) -> Optional[LeaveRequest]:
        """Обновява статуса на заявка за отпуск"""
        req = await self.get_leave_request_by_id(db, request_id)
        if not req:
            return None
        
        req.status = status
        if admin_comment is not None:
            req.admin_comment = admin_comment
        req.employer_top_up = employer_top_up
        
        await db.flush()
        await db.refresh(req)
        return req
    
    async def delete_leave_request(
        self,
        db: AsyncSession,
        request_id: int,
        current_user_id: int,
        is_admin: bool = False
    ) -> bool:
        """Изтрива заявка за отпуск"""
        req = await self.get_leave_request_by_id(db, request_id)
        if not req:
            return False
        
        if req.user_id != current_user_id and not is_admin:
            return False
        
        if req.status != "pending":
            return False
        
        await db.delete(req)
        await db.flush()
        return True
    
    async def get_schedules_by_period(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date,
        company_id: int = None
    ) -> List[WorkSchedule]:
        """Връща графици за период"""
        query = select(WorkSchedule).options(selectinload(WorkSchedule.shift)).where(
            WorkSchedule.date >= start_date,
            WorkSchedule.date <= end_date
        )
        if company_id:
            from backend.database.models import User
            query = query.join(User).where(User.company_id == company_id)
        result = await db.execute(query.order_by(WorkSchedule.date))
        return list(result.scalars().all())
    
    async def get_schedule_by_id(self, db: AsyncSession, schedule_id: int) -> Optional[WorkSchedule]:
        """Връща график по ID"""
        result = await db.execute(
            select(WorkSchedule).where(WorkSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update_schedule(
        self,
        db: AsyncSession,
        user_id: int,
        shift_id: int,
        schedule_date: date
    ) -> WorkSchedule:
        """Създава или обновява график"""
        result = await db.execute(
            select(WorkSchedule).where(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date == schedule_date
            )
        )
        schedule = result.scalar_one_or_none()
        
        if schedule:
            schedule.shift_id = shift_id
            await db.flush()
            await db.refresh(schedule)
        else:
            schedule = WorkSchedule(user_id=user_id, shift_id=shift_id, date=schedule_date)
            db.add(schedule)
            await db.flush()
            await db.refresh(schedule)
        
        return schedule
    
    async def delete_schedule(self, db: AsyncSession, schedule_id: int) -> bool:
        """Изтрива график"""
        schedule = await self.get_schedule_by_id(db, schedule_id)
        if schedule:
            await db.delete(schedule)
            await db.flush()
            return True
        return False
    
    async def create_bulk_schedules(
        self,
        db: AsyncSession,
        user_ids: List[int],
        shift_id: int,
        start_date: date,
        end_date: date,
        days_of_week: List[int] = None
    ) -> int:
        """Създава масово графици"""
        from datetime import timedelta
        
        count = 0
        current = start_date
        while current <= end_date:
            if days_of_week is None or current.weekday() in days_of_week:
                for user_id in user_ids:
                    schedule = await self.create_or_update_schedule(db, user_id, shift_id, current)
                    count += 1
            current += timedelta(days=1)
        
        return count
    
    async def get_swap_request(self, db: AsyncSession, swap_id: int) -> Optional[ShiftSwapRequest]:
        """Връща заявка за размяна"""
        stmt = select(ShiftSwapRequest).where(ShiftSwapRequest.id == swap_id).options(
            selectinload(ShiftSwapRequest.requestor),
            selectinload(ShiftSwapRequest.target_user),
            selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
            selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
        )
        res = await db.execute(stmt)
        return res.scalars().first()
    
    async def create_swap_request(
        self,
        db: AsyncSession,
        requestor_id: int,
        requestor_schedule_id: int,
        target_user_id: int,
        target_schedule_id: int
    ) -> ShiftSwapRequest:
        """Създава заявка за размяна"""
        req_sched = await db.get(WorkSchedule, requestor_schedule_id)
        tar_sched = await db.get(WorkSchedule, target_schedule_id)
        
        if not req_sched or req_sched.user_id != requestor_id:
            raise ValueError("Вашата избрана смяна е невалидна.")
        if not tar_sched or tar_sched.user_id != target_user_id:
            raise ValueError("Избраната смяна на колегата е невалидна.")
        
        stmt = select(ShiftSwapRequest).where(
            ShiftSwapRequest.requestor_schedule_id == requestor_schedule_id,
            ShiftSwapRequest.status == "pending"
        )
        res = await db.execute(stmt)
        if res.scalars().first():
            raise ValueError("Вече има активна заявка за тази смяна.")
        
        swap = ShiftSwapRequest(
            requestor_id=requestor_id,
            requestor_schedule_id=requestor_schedule_id,
            target_user_id=target_user_id,
            target_schedule_id=target_schedule_id,
            status="pending"
        )
        db.add(swap)
        await db.flush()
        await db.refresh(swap)
        return swap
    
    async def update_swap_status(
        self,
        db: AsyncSession,
        swap_id: int,
        new_status: str,
        admin_user_id: int = None
    ) -> Optional[ShiftSwapRequest]:
        """Обновява статуса на размяна"""
        swap = await self.get_swap_request(db, swap_id)
        if not swap:
            return None
        
        swap.status = new_status
        
        if new_status == "approved":
            req_sched = swap.requestor_schedule
            tar_sched = swap.target_schedule
            
            old_req_shift_id = req_sched.shift_id
            req_sched.shift_id = tar_sched.shift_id
            tar_sched.shift_id = old_req_shift_id
        
        await db.flush()
        await db.refresh(swap)
        return swap
    
    async def get_my_swap_requests(self, db: AsyncSession, user_id: int) -> List[ShiftSwapRequest]:
        """Връща моите заявки за размяна"""
        stmt = select(ShiftSwapRequest).where(
            (ShiftSwapRequest.requestor_id == user_id) | 
            (ShiftSwapRequest.target_user_id == user_id)
        ).options(
            selectinload(ShiftSwapRequest.requestor),
            selectinload(ShiftSwapRequest.target_user),
            selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
            selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
        ).order_by(ShiftSwapRequest.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
    
    async def get_all_pending_swaps(self, db: AsyncSession) -> List[ShiftSwapRequest]:
        """Връща всички чакащи размени"""
        stmt = select(ShiftSwapRequest).where(
            ShiftSwapRequest.status == "pending"
        ).options(
            selectinload(ShiftSwapRequest.requestor),
            selectinload(ShiftSwapRequest.target_user),
            selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
            selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
        ).order_by(ShiftSwapRequest.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
    
    async def get_schedule_templates(
        self,
        db: AsyncSession,
        company_id: int = None
    ) -> List[ScheduleTemplate]:
        """Връща шаблони за графици"""
        stmt = select(ScheduleTemplate).options(
            selectinload(ScheduleTemplate.items).selectinload(ScheduleTemplateItem.shift)
        )
        if company_id:
            stmt = stmt.where(ScheduleTemplate.company_id == company_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())
    
    async def get_schedule_template(
        self,
        db: AsyncSession,
        template_id: int,
        company_id: int = None
    ) -> Optional[ScheduleTemplate]:
        """Връща шаблон по ID"""
        stmt = select(ScheduleTemplate).where(ScheduleTemplate.id == template_id).options(
            selectinload(ScheduleTemplate.items).selectinload(ScheduleTemplateItem.shift)
        )
        if company_id:
            stmt = stmt.where(ScheduleTemplate.company_id == company_id)
        res = await db.execute(stmt)
        return res.scalars().first()
    
    async def get_leave_balance(
        self,
        db: AsyncSession,
        user_id: int,
        year: int
    ) -> LeaveBalance:
        """Връща баланс на отпуски"""
        stmt = select(LeaveBalance).where(
            LeaveBalance.user_id == user_id,
            LeaveBalance.year == year
        )
        res = await db.execute(stmt)
        balance = res.scalars().first()
        
        if not balance:
            balance = LeaveBalance(user_id=user_id, year=year, total_days=20, used_days=0)
            db.add(balance)
            await db.flush()
            await db.refresh(balance)
        
        return balance
    
    async def get_shift_by_id(self, db: AsyncSession, shift_id: int) -> Optional[Shift]:
        """Връща смяна по ID"""
        result = await db.execute(select(Shift).where(Shift.id == shift_id))
        return result.scalars().first()
    
    async def get_all_shifts(self, db: AsyncSession) -> List[Shift]:
        """Връща всички смени"""
        result = await db.execute(select(Shift))
        return list(result.scalars().all())
    
    async def apply_schedule_template(
        self,
        db: AsyncSession,
        template_id: int,
        user_id: int,
        start_date: date,
        end_date: date,
        admin_id: int
    ) -> bool:
        """Прилага шаблон за график"""
        template = await self.get_schedule_template(db, template_id)
        if not template or not template.items:
            raise ValueError("Шаблонът не съществува или е празен.")
        
        sorted_items = sorted(template.items, key=lambda x: x.day_index)
        rotation_length = len(sorted_items)
        
        current_date = start_date
        days_processed = 0
        
        from datetime import timedelta
        
        while current_date <= end_date:
            item_index = days_processed % rotation_length
            target_item = sorted_items[item_index]
            
            stmt = select(WorkSchedule).where(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date == current_date
            )
            res = await db.execute(stmt)
            existing = res.scalars().first()
            
            if target_item.shift_id:
                if existing:
                    existing.shift_id = target_item.shift_id
                else:
                    new_sched = WorkSchedule(
                        user_id=user_id,
                        date=current_date,
                        shift_id=target_item.shift_id
                    )
                    db.add(new_sched)
            else:
                if existing:
                    await db.delete(existing)
            
            current_date += timedelta(days=1)
            days_processed += 1
        
        await db.flush()
        return True


time_repo = TimeTrackingRepository()