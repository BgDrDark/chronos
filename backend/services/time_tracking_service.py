from typing import Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database.models import TimeLog, WorkSchedule, Shift, GlobalSetting
from backend.database.models import sofia_now
from backend.utils.geo import calculate_distance
from backend.config import settings
from backend.database.transaction_manager import atomic_transaction, with_row_lock, TransactionError
from zoneinfo import ZoneInfo


class TimeTrackingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_geofence_entry(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Tuple[bool, str]:
        """Validate geofence for clock in. Returns (is_valid, error_message)"""
        entry_enabled = await self._get_setting("geofencing_entry_enabled")

        if entry_enabled != "True":
            return True, ""

        office_lat = await self._get_setting("office_latitude")
        office_lon = await self._get_setting("office_longitude")
        office_rad = await self._get_setting("office_radius")

        if not office_lat or not office_lon or not office_rad:
            return True, ""

        if latitude is None or longitude is None:
            return False, "Изисква се местоположение за стартиране на смяна (Geofencing е активиран)."

        dist = calculate_distance(latitude, longitude, float(office_lat), float(office_lon))
        if dist > float(office_rad):
            return False, f"Вие сте извън офис зоната! Разстояние: {int(dist)}м (Допустимо: {office_rad}м)"

        return True, ""

    async def validate_geofence_exit(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Tuple[bool, str]:
        """Validate geofence for clock out. Returns (is_valid, error_message)"""
        exit_enabled = await self._get_setting("geofencing_exit_enabled")

        if exit_enabled != "True":
            return True, ""

        office_lat = await self._get_setting("office_latitude")
        office_lon = await self._get_setting("office_longitude")
        office_rad = await self._get_setting("office_radius")

        if not office_lat or not office_lon or not office_rad:
            return True, ""

        if latitude is None or longitude is None:
            return False, "Изисква се местоположение за приключване на смяна (Geofencing Exit е активиран)."

        dist = calculate_distance(latitude, longitude, float(office_lat), float(office_lon))
        if dist > float(office_rad):
            return False, f"Трябва да сте в офис зоната за да приключите! Разстояние: {int(dist)}м"

        return True, ""

    async def calculate_working_hours(
        self,
        timelog: TimeLog
    ) -> float:
        """Calculate working hours from a timelog"""
        if not timelog.end_time:
            return 0.0
        
        duration = timelog.end_time - timelog.start_time
        hours = duration.total_seconds() / 3600.0
        return round(hours, 2)

    async def get_schedule_for_date(
        self,
        user_id: int,
        schedule_date: date
    ) -> Optional[WorkSchedule]:
        """Get work schedule for a specific date"""
        stmt = select(WorkSchedule).where(
            WorkSchedule.user_id == user_id,
            WorkSchedule.date == schedule_date
        ).options(selectinload(WorkSchedule.shift))
        
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_matching_shift(
        self,
        user_id: int,
        check_time: datetime
    ) -> Optional[Shift]:
        """Find a shift that matches the given time (within tolerance)"""
        today = check_time.date()
        
        schedule = await self.get_schedule_for_date(user_id, today)
        
        all_shifts = await self._get_all_shifts()
        
        matched_shift = None
        best_diff = float('inf')
        
        shifts_to_check = []
        if schedule and schedule.shift:
            shifts_to_check.append(schedule.shift)
        shifts_to_check.extend([s for s in all_shifts if s not in shifts_to_check])
        
        for shift in shifts_to_check:
            shift_start_dt = datetime.combine(today, shift.start_time)
            tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
            diff_mins = abs((check_time - shift_start_dt).total_seconds()) / 60.0
            
            if diff_mins <= tolerance:
                if diff_mins < best_diff:
                    best_diff = diff_mins
                    matched_shift = shift
        
        return matched_shift

    async def snap_time_to_shift(
        self,
        shift: Shift,
        actual_time: datetime
    ) -> datetime:
        """Snap actual time to shift start/end time within tolerance"""
        today = actual_time.date()
        
        if shift.start_time:
            shift_start_dt = datetime.combine(today, shift.start_time)
            tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
            diff_mins = abs((actual_time - shift_start_dt).total_seconds()) / 60.0
            
            if diff_mins <= tolerance:
                return shift_start_dt
        
        return actual_time

    async def check_time_overlap(
        self,
        user_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if time range overlaps with any existing timelog"""
        stmt = select(TimeLog).where(
            TimeLog.user_id == user_id,
            TimeLog.end_time.is_(None)
        )
        result = await self.db.execute(stmt)
        active = result.scalars().first()
        
        if active:
            if start_time < active.end_time and end_time > active.start_time:
                return True
        
        stmt_overlap = select(TimeLog).where(
            TimeLog.user_id == user_id,
            TimeLog.start_time < end_time,
            TimeLog.end_time > start_time
        )
        result_overlap = await self.db.execute(stmt_overlap)
        return result_overlap.scalars().first() is not None

    async def get_active_timelog(
        self,
        user_id: int
    ) -> Optional[TimeLog]:
        """Get active timelog for user"""
        stmt = select(TimeLog).where(
            TimeLog.user_id == user_id,
            TimeLog.end_time.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_timelogs(
        self,
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        limit: int = 100
    ) -> list[TimeLog]:
        """Get timelogs for user within date range"""
        query = select(TimeLog).where(TimeLog.user_id == user_id)
        
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(TimeLog.start_time >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.where(TimeLog.start_time <= end_dt)
        
        query = query.order_by(TimeLog.start_time.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_setting(self, key: str) -> Optional[str]:
        """Get global setting value"""
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()
        return setting.value if setting else None

    async def _get_all_shifts(self) -> list[Shift]:
        """Get all shifts"""
        stmt = select(Shift)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def clock_in(
        self,
        user_id: int,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        custom_time: Optional[datetime] = None,
        skip_geofence: bool = False
    ) -> TimeLog:
        """Clock in - creates a new time log"""
        async with atomic_transaction(self.db) as tx:
            active_log_query = select(TimeLog).where(
                TimeLog.user_id == user_id,
                TimeLog.end_time.is_(None)
            )

            try:
                active_log_result = await with_row_lock(tx, active_log_query)
                active_log = active_log_result.scalars().first()
            except TransactionError as e:
                if "deadlock" in str(e).lower():
                    raise TransactionError("Конфликт при проверка за активен запис. Моля, опитайте отново.") from e
                raise

            if active_log:
                raise ValueError("Вече имате активно отчитане на времето.")

            if not custom_time and not skip_geofence:
                is_valid, error_msg = await self.validate_geofence_entry(latitude, longitude)
                if not is_valid:
                    raise ValueError(error_msg)

            if custom_time:
                sofia_tz = ZoneInfo(settings.TIMEZONE)
                if custom_time.tzinfo is None:
                    custom_time = custom_time.replace(tzinfo=sofia_tz)
                else:
                    custom_time = custom_time.astimezone(sofia_tz)
                now_local = custom_time.replace(tzinfo=None)
            else:
                now_local = sofia_now()
            today = now_local.date()

            schedule_query = select(WorkSchedule).where(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date == today
            ).options(selectinload(WorkSchedule.shift))

            try:
                schedule_result = await with_row_lock(tx, schedule_query)
                current_schedule = schedule_result.scalars().first()
            except TransactionError as e:
                if "deadlock" in str(e).lower():
                    raise TransactionError("Конфликт при зареждане на графика. Моля, опитайте отново.") from e
                raise

            matched_shift = None

            if current_schedule and current_schedule.shift:
                if self._is_matching_shift(now_local, current_schedule.shift, today):
                    matched_shift = current_schedule.shift

            if not matched_shift:
                all_shifts = await self._get_all_shifts()
                best_diff = float('inf')
                for shift in all_shifts:
                    if self._is_matching_shift(now_local, shift, today):
                        shift_start_dt = datetime.combine(today, shift.start_time)
                        diff_mins = abs((now_local - shift_start_dt).total_seconds()) / 60.0
                        if diff_mins < best_diff:
                            best_diff = diff_mins
                            matched_shift = shift

                if matched_shift:
                    if current_schedule:
                        current_schedule.shift_id = matched_shift.id
                        tx.add(current_schedule)
                    else:
                        new_schedule = WorkSchedule(
                            user_id=user_id,
                            shift_id=matched_shift.id,
                            date=today
                        )
                        tx.add(new_schedule)

            snapped_start_time = now_local
            if matched_shift:
                shift_start_dt = datetime.combine(today, matched_shift.start_time)
                snapped_start_time = shift_start_dt

            db_log = TimeLog(
                user_id=user_id,
                start_time=snapped_start_time,
                latitude=latitude,
                longitude=longitude
            )
            tx.add(db_log)
            await tx.flush()
            await tx.refresh(db_log)

            return db_log

    async def clock_out(
        self,
        user_id: int,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        custom_time: Optional[datetime] = None,
        notes: Optional[str] = None,
        skip_geofence: bool = False
    ) -> TimeLog:
        """Clock out - ends the active time log"""
        async with atomic_transaction(self.db) as tx:
            active_log_query = select(TimeLog).where(
                TimeLog.user_id == user_id,
                TimeLog.end_time.is_(None)
            )

            try:
                active_log_result = await with_row_lock(tx, active_log_query)
                active_log = active_log_result.scalars().first()
            except TransactionError as e:
                if "deadlock" in str(e).lower():
                    raise TransactionError("Конфликт при проверка за активен запис. Моля, опитайте отново.") from e
                raise

            if not active_log:
                raise ValueError("Не е намерено активно отчитане на времето за прекратяване.")

            if not custom_time and not skip_geofence:
                is_valid, error_msg = await self.validate_geofence_exit(latitude, longitude)
                if not is_valid:
                    raise ValueError(error_msg)

            if custom_time:
                sofia_tz = ZoneInfo(settings.TIMEZONE)
                if custom_time.tzinfo is None:
                    custom_time = custom_time.replace(tzinfo=sofia_tz)
                else:
                    custom_time = custom_time.astimezone(sofia_tz)
                now_local = custom_time.replace(tzinfo=None)
            else:
                now_local = sofia_now()

            log_date = active_log.start_time.date()

            schedule_query = select(WorkSchedule).where(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date == log_date
            ).options(selectinload(WorkSchedule.shift))

            try:
                schedule_result = await with_row_lock(tx, schedule_query)
                schedule = schedule_result.scalars().first()
            except TransactionError as e:
                if "deadlock" in str(e).lower():
                    raise TransactionError("Конфликт при зареждане на графика. Моля, опитайте отново.") from e
                raise

            final_end_time = now_local

            if schedule and schedule.shift:
                s = schedule.shift
                shift_end_dt = datetime.combine(log_date, s.end_time)

                if s.end_time < s.start_time:
                    shift_end_dt += timedelta(days=1)

                tolerance = s.tolerance_minutes if s.tolerance_minutes is not None else 15
                diff_mins = abs((now_local - shift_end_dt).total_seconds()) / 60.0

                if diff_mins <= tolerance:
                    final_end_time = shift_end_dt

            active_log.end_time = final_end_time
            if notes:
                from backend.utils.security import sanitize_html
                active_log.notes = sanitize_html(notes)
            tx.add(active_log)
            await tx.flush()
            await tx.refresh(active_log)

            return active_log

    def _is_matching_shift(self, check_time: datetime, shift: Shift, check_date: date) -> bool:
        """Check if time matches shift within tolerance"""
        shift_start_dt = datetime.combine(check_date, shift.start_time)
        tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
        diff_mins = abs((check_time - shift_start_dt).total_seconds()) / 60.0
        return diff_mins <= tolerance


time_tracking_service = TimeTrackingService