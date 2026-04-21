from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.models import Company, Department, Position, GlobalSetting
from .base import BaseRepository


class SettingsRepository(BaseRepository):
    """Repository за глобални настройки"""
    
    model = GlobalSetting
    
    async def get_setting(self, db: AsyncSession, key: str) -> Optional[str]:
        """Връща стойността на настройка по ключ"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None
    
    async def set_setting(self, db: AsyncSession, key: str, value: str) -> GlobalSetting:
        """Създава или обновява настройка"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
            await db.flush()
            await db.refresh(setting)
        else:
            setting = GlobalSetting(key=key, value=value)
            db.add(setting)
            await db.flush()
            await db.refresh(setting)
        
        return setting
    
    async def get_settings_by_prefix(self, db: AsyncSession, prefix: str) -> List[GlobalSetting]:
        """Връща всички настройки с даден префикс"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key.like(f"{prefix}%"))
        )
        return list(result.scalars().all())
    
    async def delete_setting(self, db: AsyncSession, key: str) -> bool:
        """Изтрива настройка"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting:
            await db.delete(setting)
            await db.flush()
            return True
        return False
    
    async def get_api_keys(self, db: AsyncSession) -> List:
        """Връща всички активни API ключове"""
        from backend.database.models import APIKey
        result = await db.execute(
            select(APIKey).where(APIKey.is_active == True)
        )
        return list(result.scalars().all())
    
    async def get_webhooks(self, db: AsyncSession) -> List:
        """Връща всички уебхукове"""
        from backend.database.models import Webhook
        result = await db.execute(select(Webhook))
        return list(result.scalars().all())
    
    async def is_smtp_configured(self, db: AsyncSession) -> bool:
        """Проверява дали SMTP е конфигуриран"""
        smtp_server = await self.get_setting(db, "smtp_server")
        smtp_username = await self.get_setting(db, "smtp_username")
        smtp_password = await self.get_setting(db, "smtp_password")
        
        return bool(smtp_server and smtp_username and smtp_password)


settings_repo = SettingsRepository()