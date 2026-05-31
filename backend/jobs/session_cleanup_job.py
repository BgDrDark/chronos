import logging

from backend.config import settings
from backend.crud.repositories import settings_repo
from backend.crud.repositories.user_repo import user_repo
from backend.database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def terminate_stale_sessions():
    """Periodic job to terminate active sessions older than configured max age."""
    logger.info("Starting stale session cleanup...")

    async with AsyncSessionLocal() as db:
        try:
            max_age_str = await settings_repo.get_setting(db, "session_max_age_hours")
            max_age_hours = int(max_age_str) if max_age_str else settings.SESSION_MAX_AGE_HOURS

            terminated = await user_repo.terminate_stale_sessions(db, max_age_hours=max_age_hours)
            if terminated > 0:
                logger.info(f"Terminated {terminated} stale sessions (older than {max_age_hours} hours)")
            else:
                logger.info("No stale sessions found")
        except Exception as e:
            logger.error(f"Error during stale session cleanup: {e}")
