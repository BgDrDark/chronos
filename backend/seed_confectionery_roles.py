import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Role
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_confectionery_roles():
    async with AsyncSessionLocal() as db:
        roles_to_add = [
            {"name": "Warehouse_Manager", "description": "Управлява склада, фактурите и наличностите."},
            {"name": "Baker", "description": "Отговаря за печенето на блатове и основи."},
            {"name": "Decorator", "description": "Отговаря за сглобяването и декорацията на десертите."},
            {"name": "Sales_Point", "description": "Приема поръчки от клиенти в сладкарниците."}
        ]

        try:
            for role_data in roles_to_add:
                result = await db.execute(select(Role).filter(Role.name == role_data["name"]))
                existing_role = result.scalars().first()
                if not existing_role:
                    new_role = Role(name=role_data["name"], description=role_data["description"])
                    db.add(new_role)
                    logger.info(f"Added role: {role_data['name']}")
                else:
                    logger.info(f"Role already exists: {role_data['name']}")
            
            await db.commit()
            logger.info("Confectionery roles seeding completed.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error seeding roles: {e}")

if __name__ == "__main__":
    asyncio.run(seed_confectionery_roles())