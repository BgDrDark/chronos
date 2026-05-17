"""Background job за проверка на насрочени актуализации"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.database.database import AsyncSessionLocal
from backend.database.models import UpdateSchedule
from backend.services.update_service import update_service
from sqlalchemy import select

logger = logging.getLogger(__name__)

_update_check_count = 0


async def check_scheduled_update():
    """Проверява дали е време за насрочена актуализация.
    
    Работи само ако enabled=True в UpdateSchedule.
    """
    global _update_check_count
    _update_check_count += 1

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UpdateSchedule)
                .where(UpdateSchedule.enabled == True)
                .order_by(UpdateSchedule.id.desc())
                .limit(1)
            )
            schedule = result.scalar_one_or_none()

            if not schedule:
                return

            now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
            should_run = False

            if schedule.schedule_type == "once":
                if schedule.scheduled_at and schedule.scheduled_at <= now:
                    should_run = True
            elif schedule.schedule_type == "weekly":
                if schedule.day_of_week is not None:
                    current_day = now.weekday()
                    if (current_day == schedule.day_of_week and
                            now.hour == schedule.hour and
                            now.minute == schedule.minute):
                        should_run = True

            if not should_run:
                if _update_check_count % 120 == 0:
                    logger.debug(f"Update scheduler check OK (not yet time)")
                return

            logger.warning(f"🔄 Scheduled auto-update triggered (type={schedule.schedule_type})")

            service = update_service(db)
            result = await service.execute_update()

            schedule.last_run_at = now
            schedule.last_run_status = result.get("status", "failed")
            schedule.last_run_output = result.get("output", "")

            if schedule.schedule_type == "once":
                schedule.enabled = False

            await db.commit()
            logger.info(f"Auto-update completed: status={result.get('status')}")

    except Exception as e:
        logger.error(f"Error checking scheduled update: {e}")
