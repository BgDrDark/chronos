import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    # Connect to default postgres DB
    url = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(sa.text("SELECT datname FROM pg_database WHERE datistemplate = false"))
        for row in res:
            print(row[0])

if __name__ == "__main__":
    asyncio.run(check())
