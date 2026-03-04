import asyncio
import sqlalchemy as sa
from backend.database.database import engine

async def list_all_modules():
    async with engine.begin() as conn:
        print("Listing all modules...")
        res = await conn.execute(sa.text("SELECT id, code, is_enabled, name FROM modules"))
        rows = res.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Code: {row[1]}, Enabled: {row[2]}, Name: {row[3]}")

if __name__ == "__main__":
    asyncio.run(list_all_modules())
