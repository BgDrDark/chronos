import asyncio
from backend.database.database import AsyncSessionLocal
from backend.database.models import Company, User, Role
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def check_db_state():
    async with AsyncSessionLocal() as db:
        # Check Companies
        res = await db.execute(select(Company))
        companies = res.scalars().all()
        print(f"Companies: {[(c.id, c.name) for c in companies]}")
        
        # Check Users and their company IDs
        res = await db.execute(select(User).options(selectinload(User.role)))
        users = res.scalars().all()
        print(f"Users: {[(u.email, u.company_id, u.role.name) for u in users]}")

if __name__ == "__main__":
    asyncio.run(check_db_state())
