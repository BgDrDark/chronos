import logging
from backend.database.database import AsyncSessionLocal
from backend import crud

logger = logging.getLogger(__name__)

async def check_expired_contracts():
    """Проверява за изтекли договори и деактивира съответните потребители"""
    try:
        logger.info("Checking for expired contracts...")
        async with AsyncSessionLocal() as db:
            deactivated_count = await crud.deactivate_expired_contracts(db)
            if deactivated_count > 0:
                logger.info(f"Automatically deactivated {deactivated_count} users with expired contracts.")
    except Exception as e:
        logger.error(f"Error checking expired contracts: {e}")