from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Module
import logging

logger = logging.getLogger(__name__)

class ModuleService:
    _cache: Dict[str, bool] = {}
    
    @classmethod
    async def is_enabled(cls, db: AsyncSession, module_code: str) -> bool:
        """Check if a module is enabled. Uses internal cache."""
        # Core modules are always enabled
        core_modules = ["shifts", "accounting", "confectionery", "cost_centers"]
        if module_code in core_modules:
            return True
        
        if module_code in cls._cache:
            return cls._cache[module_code]
        
        # If not in cache, fetch from DB
        result = await db.execute(select(Module.is_enabled).where(Module.code == module_code))
        is_enabled = result.scalar()
        
        if is_enabled is None:
            # Module not found, assume disabled or handle as error
            logger.warning(f"Module '{module_code}' not found in database.")
            return False
        
        # Update cache
        cls._cache[module_code] = is_enabled
        return is_enabled

    @classmethod
    def clear_cache(cls):
        """Clear the module status cache."""
        cls._cache = {}

    @classmethod
    async def toggle_module(cls, db: AsyncSession, module_code: str, enabled: bool) -> bool:
        """Enable or disable a module."""
        logger.info(f"toggle_module called: {module_code}, enabled: {enabled}")
        
        # Safety: NEVER allow disabling core modules
        core_modules = ["shifts", "accounting", "confectionery", "cost_centers"]
        if module_code in core_modules and not enabled:
            logger.warning(f"Attempted to disable core '{module_code}' module. Operation denied.")
            return True

        result = await db.execute(select(Module).where(Module.code == module_code))
        module = result.scalar_one_or_none()
        
        if module:
            logger.info(f"Found module: {module.code}, current is_enabled: {module.is_enabled}")
            # If it's a core module, force it to be enabled
            core_modules = ["shifts", "accounting", "confectionery", "cost_centers"]
            if module_code in core_modules:
                module.is_enabled = True
            else:
                module.is_enabled = enabled
                
            await db.commit()
            logger.info(f"Committed module: {module.code}, new is_enabled: {module.is_enabled}")
            # Invalidate entire cache to be safe
            cls.clear_cache()
            return True
        logger.warning(f"Module not found: {module_code}")
        return False

    @classmethod
    async def get_all_modules(cls, db: AsyncSession) -> list[Module]:
        """Get list of all modules and their status."""
        result = await db.execute(select(Module).order_by(Module.id))
        modules = result.scalars().all()
        logger.info(f"get_all_modules: found {len(modules)} modules: {[m.code for m in modules]}")
        return modules
