import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Module
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_modules():
    async with AsyncSessionLocal() as db:
        modules_to_add = [
            {
                "code": "shifts",
                "name": "Работно време и Смени",
                "description": "Управление на графици, присъствие и закъснения."
            },
            {
                "code": "salaries",
                "name": "Заплати и Хонорари",
                "description": "Изчисляване на възнаграждения, осигуровки и генериране на фишове."
            },
            {
                "code": "kiosk",
                "name": "Киоск Терминал",
                "description": "Интерфейс за терминали на входа, QR достъп и GPS проверка."
            },
            {
                "code": "integrations",
                "name": "Интеграции",
                "description": "Синхронизация с външни системи и API достъп."
            },
            {
                "code": "confectionery",
                "name": "Сладкарско производство и Склад",
                "description": "Управление на склад (FEFO), Рецептурник и Производствени станции."
            },
            {
                "code": "accounting",
                "name": "Счетоводство и Фактуриране",
                "description": "Управление на фактури, доставчици и разплащания."
            },
            {
                "code": "notifications",
                "name": "Уведомления и Кореспонденция",
                "description": "SMTP настройки, имейл справки и автоматични известия за наличности."
            }
        ]

        try:
            for mod_data in modules_to_add:
                result = await db.execute(select(Module).filter(Module.code == mod_data["code"]))
                existing_mod = result.scalars().first()
                if not existing_mod:
                    new_mod = Module(
                        code=mod_data["code"],
                        name=mod_data["name"],
                        description=mod_data["description"],
                        is_enabled=(mod_data["code"] in ["shifts", "accounting", "confectionery", "notifications"])
                    )
                    db.add(new_mod)
                    logger.info(f"Added module: {mod_data['code']}")
                else:
                    existing_mod.name = mod_data["name"]
                    existing_mod.description = mod_data["description"]
                    # Optionally force enable some core modules even if they exist
                    if mod_data["code"] in ["shifts", "accounting", "confectionery", "notifications"]:
                        existing_mod.is_enabled = True
                    logger.info(f"Updated description for module: {mod_data['code']}")
            
            await db.commit()
            logger.info("Modules seeding updated.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error seeding modules: {e}")

if __name__ == "__main__":
    asyncio.run(seed_modules())
