import asyncio
import sqlalchemy as sa
from backend.database.database import engine
from backend.config import settings

async def update_schema():
    async with engine.begin() as conn:
        print("Checking invoices table columns...")
        
        # Check if columns exist
        res = await conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'invoices'
        """))
        existing_columns = [row[0] for row in res.fetchall()]
        print(f"Existing columns: {existing_columns}")

        new_columns = [
            ("document_type", "VARCHAR(50)", "'ФАКТУРА'"),
            ("griff", "VARCHAR(20)", "'ОРИГИНАЛ'"),
            ("description", "TEXT", "NULL"),
            ("delivery_method", "VARCHAR(50)", "'Доставка до адрес'")
        ]

        for col_name, col_type, default_val in new_columns:
            if col_name not in existing_columns:
                print(f"Adding column {col_name}...")
                await conn.execute(sa.text(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"))
            else:
                print(f"Column {col_name} already exists.")

if __name__ == "__main__":
    asyncio.run(update_schema())
