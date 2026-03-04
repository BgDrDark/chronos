import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

class LockedSession:
    """
    A proxy for AsyncSession that uses an asyncio.Lock to serialize access
    to all async methods.
    
    This prevents 'InterfaceError: cannot perform operation: another operation is in progress'
    which occurs when Strawberry GraphQL executes multiple resolvers concurrently 
    using the same database connection.
    """
    def __init__(self, session: AsyncSession, lock: asyncio.Lock):
        self.session = session
        self.lock = lock

    async def execute(self, *args, **kwargs):
        async with self.lock:
            return await self.session.execute(*args, **kwargs)

    async def scalar(self, *args, **kwargs):
        async with self.lock:
            return await self.session.scalar(*args, **kwargs)

    async def scalars(self, *args, **kwargs):
        async with self.lock:
            return await self.session.scalars(*args, **kwargs)

    async def get(self, *args, **kwargs):
        async with self.lock:
            return await self.session.get(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        async with self.lock:
            return await self.session.delete(*args, **kwargs)

    async def commit(self):
        async with self.lock:
            return await self.session.commit()

    async def rollback(self):
        async with self.lock:
            return await self.session.rollback()

    async def refresh(self, *args, **kwargs):
        async with self.lock:
            return await self.session.refresh(*args, **kwargs)
            
    async def flush(self, *args, **kwargs):
        async with self.lock:
            return await self.session.flush(*args, **kwargs)
            
    async def close(self):
        async with self.lock:
            return await self.session.close()

    async def begin(self, *args, **kwargs):
        async with self.lock:
            return await self.session.begin(*args, **kwargs)

    async def begin_nested(self, *args, **kwargs):
        async with self.lock:
            return await self.session.begin_nested(*args, **kwargs)

    async def merge(self, *args, **kwargs):
        async with self.lock:
            return await self.session.merge(*args, **kwargs)

    async def run_sync(self, *args, **kwargs):
        async with self.lock:
            return await self.session.run_sync(*args, **kwargs)

    async def stream(self, *args, **kwargs):
        async with self.lock:
            return await self.session.stream(*args, **kwargs)

    async def scalars_stream(self, *args, **kwargs):
        async with self.lock:
            return await self.session.scalars_stream(*args, **kwargs)

    # Context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # Synchronous methods don't need locking as they only affect identity map
    def add(self, *args, **kwargs):
        return self.session.add(*args, **kwargs)

    def add_all(self, *args, **kwargs):
        return self.session.add_all(*args, **kwargs)

    def expunge(self, *args, **kwargs):
        return self.session.expunge(*args, **kwargs)

    def expunge_all(self, *args, **kwargs):
        return self.session.expunge_all(*args, **kwargs)
        
    def __getattr__(self, name):
        return getattr(self.session, name)
