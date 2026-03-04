import asyncio
import sqlalchemy as sa
from backend.database.database import engine

async def check_accounting():
    async with engine.begin() as conn:
        print("Checking modules table...")
        res = await conn.execute(sa.text("SELECT code, is_enabled FROM modules WHERE code = 'accounting'"))
        row = res.fetchone()
        if row:
            print(f"Module 'accounting' exists: code={row[0]}, is_enabled={row[1]}")
        else:
            print("Module 'accounting' NOT FOUND in database.")

if __name__ == "__main__":
    asyncio.run(check_accounting())
