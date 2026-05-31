import logging

from backend.config import settings
from backend.crud.repositories.user_repo import user_repo
from backend.database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def terminate_stale_sessions():
    """Periodic job to terminate active sessions older than 12 hours."""
    logger.info("Starting stale session cleanup...")

    async with AsyncSessionLocal() as db:
        try:
            terminated = await user_repo.terminate_stale_sessions(db, max_age_hours=12)
            if terminated > 0:
                logger.info(f"Terminated {terminated} stale sessions (older than 12 hours)")
            else:
                logger.info("No stale sessions found")
        except Exception as e:
            logger.error(f"Error during stale session cleanup: {e}")
