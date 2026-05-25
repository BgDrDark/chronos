from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud.repositories import settings_repo


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = settings_repo

    async def get_setting(self, key: str) -> str | None:
        return await self.repo.get_setting(self.db, key)

    async def set_setting(self, key: str, value: str) -> Any:
        return await self.repo.set_setting(self.db, key, value)

    async def delete_setting(self, key: str) -> bool:
        return await self.repo.delete_setting(self.db, key)

    async def get_all_settings(self) -> dict[str, str]:
        settings = await self.repo.get_all(self.db)
        return {s.key: s.value for s in settings}

    async def get_settings_by_category(self, category: str) -> dict[str, str]:
        settings = await self.repo.get_settings_by_prefix(self.db, category)
        return {s.key: s.value for s in settings}

    async def set_multiple_settings(self, settings: dict[str, str]) -> dict[str, str]:
        for key, value in settings.items():
            await self.repo.set_setting(self.db, key, value)
        return settings


settings_service = SettingsService
