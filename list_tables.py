import asyncio
import sqlalchemy as sa
from backend.database.database import engine
from backend.config import settings

async def check():
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    async with engine.connect() as conn:
        res = await conn.execute(sa.text("SELECT version_num FROM alembic_version"))
        for row in res:
            print(f"Alembic version: {row[0]}")
        for row in res:
            print(f"{row[0]}.{row[1]}")

if __name__ == "__main__":
    asyncio.run(check())
