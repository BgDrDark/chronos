import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Role, Module
from sqlalchemy import text
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_structure():
    async with AsyncSessionLocal() as db:
        logger.info("--- СТАРТ НА ТЕСТ: ФАЗА 1 ---")
        
        # 1. Проверка на таблиците
        new_tables = [
            "storage_zones", "suppliers", "ingredients", "batches", 
            "recipes", "recipe_ingredients", "workstations", 
            "recipe_steps", "production_orders", "production_tasks"
        ]
        
        logger.info("Проверка на нови таблици...")
        for table in new_tables:
            result = await db.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');"))
            exists = result.scalar()
            if exists:
                logger.info(f"✅ Таблица '{table}' съществува.")
            else:
                logger.error(f"❌ Таблица '{table}' ЛИПСВА!")

        # 2. Проверка на ролите
        new_roles = ["Warehouse_Manager", "Baker", "Decorator", "Sales_Point"]
        logger.info("Проверка на потребителски роли...")
        for role_name in new_roles:
            result = await db.execute(select(Role).filter(Role.name == role_name))
            role = result.scalars().first()
            if role:
                logger.info(f"✅ Роля '{role_name}' е намерена (ID: {role.id}).")
            else:
                logger.error(f"❌ Роля '{role_name}' ЛИПСВА!")

        # 3. Проверка на модула
        logger.info("Проверка на регистрация на модула...")
        result = await db.execute(select(Module).filter(Module.code == "confectionery"))
        module = result.scalars().first()
        if module:
            logger.info(f"✅ Модул '{module.name}' е активен (Status: {module.is_enabled}).")
        else:
            logger.error(f"❌ Модул 'confectionery' НЕ Е регистриран!")

        logger.info("--- КРАЙ НА ТЕСТА ---")

if __name__ == "__main__":
    asyncio.run(test_database_structure())