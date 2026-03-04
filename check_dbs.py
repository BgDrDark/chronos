import asyncio
import sqlalchemy as sa
from backend.database.database import engine

async def check_dbs():
    # Connect to default 'postgres' db to list others
    from sqlalchemy.ext.asyncio import create_async_engine
    import os
    from backend.config import settings
    
    url = str(settings.DATABASE_URL)
    # Replace db name in URL with 'postgres'
    base_url = url.rsplit('/', 1)[0] + '/postgres'
    
    temp_engine = create_async_engine(base_url)
    async with temp_engine.begin() as conn:
        res = await conn.execute(sa.text("SELECT datname FROM pg_database"))
        dbs = [row[0] for row in res.fetchall()]
        print(f"Databases: {dbs}")
    await temp_engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_dbs())
