import asyncio
from sqlalchemy import text
from backend.database.database import engine
from backend.database.models import Base

async def sync_schema():
    async with engine.begin() as conn:
        # 1. Check/Add qr_token to users
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'"))
        columns = [row[0] for row in result.fetchall()]
        if 'qr_token' not in columns:
            print("Adding qr_token column to users...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN qr_token VARCHAR UNIQUE"))
            await conn.execute(text("CREATE INDEX ix_users_qr_token ON users (qr_token)"))
        
        # 2. Check/Add preferences to push_subscriptions
        try:
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='push_subscriptions'"))
            sub_cols = [row[0] for row in result.fetchall()]
            if 'preferences' not in sub_cols and sub_cols: # Only if table exists
                print("Adding preferences column to push_subscriptions...")
                await conn.execute(text("ALTER TABLE push_subscriptions ADD COLUMN preferences JSON DEFAULT '{}'"))
            
            # Check user_documents
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='user_documents'"))
            doc_cols = [row[0] for row in result.fetchall()]
            if 'is_locked' not in doc_cols and doc_cols:
                print("Adding is_locked column to user_documents...")
                await conn.execute(text("ALTER TABLE user_documents ADD COLUMN is_locked BOOLEAN DEFAULT FALSE"))
        except Exception as e:
            print(f"Skipping tables check: {e}")

        # 3. Create new tables if they don't exist
        print("Checking for new tables (schedule_templates, etc.)...")
        await conn.run_sync(Base.metadata.create_all)
        print("Schema sync complete.")

if __name__ == "__main__":
    asyncio.run(sync_schema())
