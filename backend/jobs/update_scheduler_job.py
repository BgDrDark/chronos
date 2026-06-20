"""Background job за проверка на насрочени актуализации"""

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.config import settings
from backend.database.database import AsyncSessionLocal
from backend.database.models import UpdateSchedule
from backend.services.update_service import update_service

logger = logging.getLogger(__name__)

_update_check_count = 0
_weekly_already_run_date: date | None = None
_WEEKLY_WINDOW_MINUTES = 10


async def check_scheduled_update():
    """Проверява дали е време за насрочена актуализация.

    Работи само ако enabled=True в UpdateSchedule.
    """
    global _update_check_count, _weekly_already_run_date
    _update_check_count += 1

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UpdateSchedule)
                .where(UpdateSchedule.enabled)
                .order_by(UpdateSchedule.id.desc())
                .limit(1),
            )
            schedule = result.scalar_one_or_none()

            if not schedule:
                return

            now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
            should_run = False

            if schedule.schedule_type == "once" and schedule.scheduled_at:
                scheduled = schedule.scheduled_at
                if scheduled.tzinfo:
                    scheduled = scheduled.astimezone(
                        ZoneInfo(settings.TIMEZONE)
                    ).replace(tzinfo=None)
                if scheduled <= now:
                    should_run = True

            elif (
                schedule.schedule_type == "weekly" and schedule.day_of_week is not None
            ):
                today = now.date()
                if (
                    _weekly_already_run_date != today
                    and now.weekday() == schedule.day_of_week
                ):
                    target_minutes = schedule.hour * 60 + schedule.minute
                    current_minutes = now.hour * 60 + now.minute
                    if abs(current_minutes - target_minutes) <= _WEEKLY_WINDOW_MINUTES:
                        should_run = True

            if not should_run and _update_check_count % 120 == 0:
                logger.debug("Update scheduler check OK (not yet time)")
                return

            if not should_run:
                return

            logger.warning(
                f"🔄 Scheduled auto-update triggered (type={schedule.schedule_type})"
            )

            service = update_service(db)
            result = await service.execute_update()

            schedule.last_run_at = now
            schedule.last_run_status = result.get("status", "failed")
            schedule.last_run_output = result.get("output", "")

            if schedule.schedule_type == "once":
                schedule.enabled = False
            elif schedule.schedule_type == "weekly":
                _weekly_already_run_date = now.date()

            await db.commit()
            logger.info(f"Auto-update completed: status={result.get('status')}")

    except Exception as e:
        logger.error(f"Error checking scheduled update: {e}")
