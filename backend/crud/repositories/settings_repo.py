
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import GlobalSetting, User

from .base import BaseRepository


class SettingsRepository(BaseRepository):
    """Repository за глобални настройки"""

    model = GlobalSetting

    async def get_setting(self, db: AsyncSession, key: str) -> str | None:
        """Връща стойността на настройка по ключ"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key == key),
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None

    async def set_setting(self, db: AsyncSession, key: str, value: str) -> GlobalSetting:
        """Създава или обновява настройка"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key == key),
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

    async def get_settings_by_prefix(self, db: AsyncSession, prefix: str) -> list[GlobalSetting]:
        """Връща всички настройки с даден префикс"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key.like(f"{prefix}%")),
        )
        return list(result.scalars().all())

    async def delete_setting(self, db: AsyncSession, key: str) -> bool:
        """Изтрива настройка"""
        result = await db.execute(
            select(GlobalSetting).where(GlobalSetting.key == key),
        )
        setting = result.scalar_one_or_none()
        if setting:
            await db.delete(setting)
            await db.flush()
            return True
        return False

    async def get_api_keys(self, db: AsyncSession, is_active: bool = None) -> list:
        """Връща API ключове, опционално филтрирани по is_active"""
        from backend.database.models import APIKey
        query = select(APIKey)
        if is_active is not None:
            query = query.where(APIKey.is_active == is_active)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_webhooks(self, db: AsyncSession) -> list:
        """Връща всички уебхукове"""
        from backend.database.models import Webhook
        result = await db.execute(select(Webhook))
        return list(result.scalars().all())

    async def is_smtp_configured(self, db: AsyncSession) -> bool:
        """Проверява дали SMTP е конфигуриран (DB + fallback към config.py)"""
        from backend.config import settings

        smtp_server = await self.get_setting(db, "smtp_server") or settings.MAIL_SERVER
        smtp_username = await self.get_setting(db, "smtp_username") or settings.MAIL_USERNAME
        smtp_password = await self.get_setting(db, "smtp_password") or settings.MAIL_PASSWORD

        return bool(smtp_server and smtp_username and smtp_password)

    # ─── APIKey methods ───────────────────────────────────────────────

    async def create_api_key(self, db: AsyncSession, **kwargs):
        """Създава нов API ключ"""
        from backend.database.models import APIKey
        instance = APIKey(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_api_key_by_id(self, db: AsyncSession, id: int):
        """Връща API ключ по ID"""
        from backend.database.models import APIKey
        result = await db.execute(
            select(APIKey).where(APIKey.id == id),
        )
        return result.scalar_one_or_none()

    async def get_api_key_by_value(self, db: AsyncSession, key_value: str):
        """Намира API ключ по key string (hashed_key)"""
        from backend.database.models import APIKey
        result = await db.execute(
            select(APIKey).where(APIKey.hashed_key == key_value),
        )
        return result.scalar_one_or_none()

    async def update_api_key(self, db: AsyncSession, id: int, **kwargs):
        """Обновява API ключ (name, is_active, etc.)"""
        from backend.database.models import APIKey
        instance = await db.get(APIKey, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_api_key(self, db: AsyncSession, id: int) -> bool:
        """Изтрива API ключ"""
        from backend.database.models import APIKey
        instance = await db.get(APIKey, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_api_keys_by_company(self, db: AsyncSession, company_id: int) -> list:
        """Връща API ключове за конкретна компания (join via User)"""
        from backend.database.models import APIKey
        result = await db.execute(
            select(APIKey)
            .join(User, APIKey.user_id == User.id)
            .where(User.company_id == company_id),
        )
        return list(result.scalars().all())

    # ─── Webhook methods ──────────────────────────────────────────────

    async def create_webhook(self, db: AsyncSession, **kwargs):
        """Създава нов уебхук"""
        from backend.database.models import Webhook
        instance = Webhook(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_webhook_by_id(self, db: AsyncSession, id: int):
        """Връща уебхук по ID"""
        from backend.database.models import Webhook
        result = await db.execute(
            select(Webhook).where(Webhook.id == id),
        )
        return result.scalar_one_or_none()

    async def get_webhooks_by_company(self, db: AsyncSession, company_id: int) -> list:
        """Връща уебхукове за конкретна компания"""
        from backend.database.models import Webhook
        result = await db.execute(
            select(Webhook).where(Webhook.company_id == company_id),
        )
        return list(result.scalars().all())

    async def update_webhook(self, db: AsyncSession, id: int, **kwargs):
        """Обновява уебхук"""
        from backend.database.models import Webhook
        instance = await db.get(Webhook, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_webhook(self, db: AsyncSession, id: int) -> bool:
        """Изтрива уебхук"""
        from backend.database.models import Webhook
        instance = await db.get(Webhook, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False


settings_repo = SettingsRepository()
