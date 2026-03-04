import logging
from datetime import timedelta
from backend.database.database import AsyncSessionLocal
from backend import crud
from backend.database.models import sofia_now
from backend.config import settings

logger = logging.getLogger(__name__)

async def check_and_rotate_keys():
    """
    Periodic job to check key age and rotate if necessary.
    Also cleans up very old legacy keys.
    """
    logger.info("Starting scheduled AuthKey rotation check...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Check Active Key Age
            active_key = await crud.get_active_auth_key(db)
            
            if active_key:
                # Calculate age using localized time
                age = sofia_now() - active_key.created_at.replace(tzinfo=None) # Ensure naive for comparison if needed
                
                if age > timedelta(days=settings.AUTH_KEY_ROTATION_DAYS):
                    logger.info(f"Active key {active_key.kid} is {age.days} days old. Rotating...")
                    new_key = await crud.rotate_auth_key(db)
                    logger.info(f"Key rotated. New active key: {new_key.kid}")
                else:
                    logger.info(f"Active key is fresh ({age.days} days). No rotation needed.")
            else:
                # Should not happen if app initialized correctly, but safe fallback
                logger.warning("No active key found during check. Creating one.")
                await crud.rotate_auth_key(db)

            # 2. Cleanup Old Keys
            deleted = await crud.cleanup_old_auth_keys(db, retention_days=settings.AUTH_KEY_RETENTION_DAYS)
            if deleted:
                logger.info("Cleanup of old legacy keys completed.")
                
        except Exception as e:
            logger.error(f"Error during key rotation job: {e}")
            # Don't re-raise, let the scheduler continue next time
