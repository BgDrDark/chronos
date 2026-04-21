import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.database.session_proxy import LockedSession

# Use create_async_engine for async operations
engine = create_async_engine(str(settings.DATABASE_URL))

# AsyncSessionLocal will be used to create new AsyncSession objects
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get a database session
async def get_db():
    session = AsyncSessionLocal()
    lock = asyncio.Lock()
    locked_session = LockedSession(session, lock)
    try:
        yield locked_session
    finally:
        await locked_session.close()
