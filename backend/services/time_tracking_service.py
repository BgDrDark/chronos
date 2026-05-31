import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.crud.repositories import settings_repo, time_repo
from backend.database.models import Shift, TimeLog, WorkSchedule, sofia_now
from backend.database.transaction_manager import (
    TransactionError,
    atomic_transaction,
    with_row_lock,
)
from backend.utils.geo import calculate_distance

logger = logging.getLogger(__name__)


class TimeTrackingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = time_repo
        self.settings_repo = settings_repo

    async def validate_geofence_entry(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> tuple[bool, str]:
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
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> tuple[bool, str]:
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
        timelog: TimeLog,
    ) -> float:
        if not timelog.end_time:
            return 0.0

        duration = timelog.end_time - timelog.start_time
        hours = duration.total_seconds() / 3600.0
        return round(hours, 2)

    async def get_schedule_for_date(
        self,
        user_id: int,
        schedule_date: date,
    ) -> WorkSchedule | None:
        return await self.repo.get_schedule_for_date(self.db, user_id, schedule_date)

    async def get_matching_shift(
        self,
        user_id: int,
        check_time: datetime,
    ) -> Shift | None:
        today = check_time.date()

        schedule = await self.get_schedule_for_date(user_id, today)

        all_shifts = await self.repo.get_all_shifts(self.db)

        matched_shift = None
        best_diff = float("inf")

        shifts_to_check = []
        if schedule and schedule.shift:
            shifts_to_check.append(schedule.shift)
        shifts_to_check.extend([s for s in all_shifts if s not in shifts_to_check])

        for shift in shifts_to_check:
            shift_start_dt = datetime.combine(today, shift.start_time)
            tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
            diff_mins = abs((check_time - shift_start_dt).total_seconds()) / 60.0

            if diff_mins <= tolerance and diff_mins < best_diff:
                best_diff = diff_mins
                matched_shift = shift

        return matched_shift

    async def snap_time_to_shift(
        self,
        shift: Shift,
        actual_time: datetime,
    ) -> datetime:
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
        end_time: datetime,
    ) -> bool:
        if start_time.tzinfo is not None:
            start_time = start_time.replace(tzinfo=None)
        if end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)

        active = await self.repo.get_active_timelog(self.db, user_id)
        if active and start_time < active.end_time and end_time > active.start_time:
            return True

        stmt_overlap = select(TimeLog).where(
            TimeLog.user_id == user_id,
            TimeLog.start_time < end_time,
            TimeLog.end_time > start_time,
        )
        result_overlap = await self.db.execute(stmt_overlap)
        return result_overlap.scalars().first() is not None

    async def get_active_timelog(
        self,
        user_id: int,
    ) -> TimeLog | None:
        return await self.repo.get_active_timelog(self.db, user_id)

    async def get_user_timelogs(
        self,
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        limit: int = 100,
    ) -> list[TimeLog]:
        return await self.repo.get_user_timelogs(self.db, user_id, start_date, end_date, limit)

    async def _get_setting(self, key: str) -> str | None:
        return await self.settings_repo.get_setting(self.db, key)

    async def _get_all_shifts(self) -> list[Shift]:
        return await self.repo.get_all_shifts(self.db)

    async def clock_in(
        self,
        user_id: int,
        latitude: float | None = None,
        longitude: float | None = None,
        custom_time: datetime | None = None,
        skip_geofence: bool = False,
    ) -> TimeLog:
        async with atomic_transaction(self.db) as tx:
            active_log_query = select(TimeLog).where(
                TimeLog.user_id == user_id,
                TimeLog.end_time.is_(None),
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
                WorkSchedule.date == today,
            ).options(selectinload(WorkSchedule.shift))

            try:
                schedule_result = await with_row_lock(tx, schedule_query)
                current_schedule = schedule_result.scalars().first()
            except TransactionError as e:
                if "deadlock" in str(e).lower():
                    raise TransactionError("Конфликт при зареждане на графика. Моля, опитайте отново.") from e
                raise

            matched_shift = None

            if current_schedule and current_schedule.shift and self._is_matching_shift(now_local, current_schedule.shift, today):
                matched_shift = current_schedule.shift

            if not matched_shift:
                all_shifts = await self._get_all_shifts()
                best_diff = float("inf")
                for shift in all_shifts:
                    if self._is_matching_shift(now_local, shift, today):
                        shift_start_dt = datetime.combine(today, shift.start_time)
                        diff_mins = abs((now_local - shift_start_dt).total_seconds()) / 60.0
                        if diff_mins < best_diff:
                            best_diff = diff_mins
                            matched_shift = shift

                if matched_shift and current_schedule:
                    current_schedule.shift_id = matched_shift.id
                    tx.add(current_schedule)
                elif matched_shift:
                    new_schedule = WorkSchedule(
                        user_id=user_id,
                        shift_id=matched_shift.id,
                        date=today,
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
                longitude=longitude,
            )
            tx.add(db_log)
            await tx.flush()
            await tx.refresh(db_log)

            return db_log

    async def clock_out(
        self,
        user_id: int,
        latitude: float | None = None,
        longitude: float | None = None,
        custom_time: datetime | None = None,
        notes: str | None = None,
        skip_geofence: bool = False,
    ) -> TimeLog:
        async with atomic_transaction(self.db) as tx:
            active_log_query = select(TimeLog).where(
                TimeLog.user_id == user_id,
                TimeLog.end_time.is_(None),
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
                WorkSchedule.date == log_date,
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

            try:
                from backend.modules.behavioral_analysis.triggered_events import (
                    TriggeredEventProcessor,
                )
                from backend.services.module_service import ModuleService

                is_enabled = await ModuleService.is_enabled(tx, "behavioral_analysis")
                if is_enabled:
                    processor = TriggeredEventProcessor(tx)
                    await processor.handle_clock_out(active_log)
            except Exception as e:
                logger.error(f"Behavioral analysis triggered event failed: {e}")

            return active_log

    def _is_matching_shift(self, check_time: datetime, shift: Shift, check_date: date) -> bool:
        shift_start_dt = datetime.combine(check_date, shift.start_time)
        tolerance = shift.tolerance_minutes if shift.tolerance_minutes is not None else 15
        diff_mins = abs((check_time - shift_start_dt).total_seconds()) / 60.0
        return diff_mins <= tolerance


time_tracking_service = TimeTrackingService
