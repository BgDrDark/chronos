import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.config import settings
from backend.database.database import AsyncSessionLocal
from backend.database.models import MaintenanceSettings

logger = logging.getLogger(__name__)

_maintenance_check_count = 0

async def check_scheduled_maintenance():
    """Check if any scheduled maintenance should be activated now."""
    global _maintenance_check_count
    _maintenance_check_count += 1

    try:
        async with AsyncSessionLocal() as db:
            now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
            result = await db.execute(
                select(MaintenanceSettings)
                .where(not MaintenanceSettings.enabled)
                .where(MaintenanceSettings.scheduled_at is not None)
                .where(MaintenanceSettings.scheduled_at <= now)
                .order_by(MaintenanceSettings.id.desc())
                .limit(1),
            )
            setting = result.scalar_one_or_none()

            if setting:
                setting.enabled = True
                setting.scheduled_at = None
                await db.commit()
                logger.warning(f"⚠️ Maintenance mode ACTIVATED: {setting.reason}")
            elif _maintenance_check_count % 60 == 0:
                logger.debug("Maintenance check OK (no scheduled activation)")
    except Exception as e:
        logger.error(f"Error checking scheduled maintenance: {e}")
