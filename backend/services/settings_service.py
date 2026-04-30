from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import GlobalSetting


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_setting(self, key: str) -> Optional[str]:
        """Get a global setting by key"""
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()
        return setting.value if setting else None

    async def set_setting(self, key: str, value: str) -> GlobalSetting:
        """Set a global setting"""
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()

        if setting:
            setting.value = value
            self.db.add(setting)
        else:
            setting = GlobalSetting(key=key, value=value)
            self.db.add(setting)

        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def delete_setting(self, key: str) -> bool:
        """Delete a global setting"""
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()

        if setting:
            await self.db.delete(setting)
            await self.db.commit()
            return True
        return False

    async def get_all_settings(self) -> Dict[str, str]:
        """Get all global settings as a dictionary"""
        stmt = select(GlobalSetting)
        result = await self.db.execute(stmt)
        settings = result.scalars().all()
        return {s.key: s.value for s in settings}

    async def get_settings_by_category(self, category: str) -> Dict[str, str]:
        """Get settings filtered by category prefix (e.g., 'payroll_', 'smtp_')"""
        stmt = select(GlobalSetting).where(GlobalSetting.key.startswith(category))
        result = await self.db.execute(stmt)
        settings = result.scalars().all()
        return {s.key: s.value for s in settings}

    async def set_multiple_settings(self, settings: Dict[str, str]) -> Dict[str, str]:
        """Set multiple settings at once"""
        for key, value in settings.items():
            await self.set_setting(key, value)
        return settings


settings_service = SettingsService