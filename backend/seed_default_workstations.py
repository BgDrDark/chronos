"""
Seed script to create default workstations for confectionery
Run: python seed_default_workstations.py
"""
import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Workstation, Company
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_WORKSTATIONS = [
    {"name": "Пекарна", "description": "Изпичане на блатове и основи"},
    {"name": "Кремове", "description": "Приготвяне на кремове и пълнежи"},
    {"name": "Декорация", "description": "Украса на готовите изделия"},
]

async def seed_default_workstations():
    async with AsyncSessionLocal() as db:
        try:
            # Get all companies
            result = await db.execute(select(Company))
            companies = result.scalars().all()
            
            for company in companies:
                for ws_data in DEFAULT_WORKSTATIONS:
                    # Check if workstation already exists
                    result = await db.execute(
                        select(Workstation).filter(
                            Workstation.name == ws_data["name"],
                            Workstation.company_id == company.id
                        )
                    )
                    existing = result.scalars().first()
                    
                    if not existing:
                        workstation = Workstation(
                            name=ws_data["name"],
                            description=ws_data["description"],
                            company_id=company.id
                        )
                        db.add(workstation)
                        logger.info(f"Added workstation '{ws_data['name']}' for company {company.id}")
            
            await db.commit()
            logger.info("Default workstations seeded successfully!")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error seeding workstations: {e}")

if __name__ == "__main__":
    asyncio.run(seed_default_workstations())
