"""
Optimized Database Configuration with Connection Pooling
Enhanced for production performance and reliability
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, Pool
from sqlalchemy import event
from sqlalchemy.engine import Engine

from backend.config import settings
from backend.database.session_proxy import LockedSession

# Configure logging
logger = logging.getLogger(__name__)

class OptimizedDatabaseConfig:
    """Optimized database configuration with connection pooling and monitoring"""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        
    def create_engine(self) -> AsyncEngine:
        """Create optimized async engine with connection pooling"""
        
        # Connection pool configuration for async engine
        # Note: Async engines use their own pooling mechanism
        pool_config = {
            "pool_size": settings.DB_POOL_SIZE if hasattr(settings, 'DB_POOL_SIZE') else 20,
            "max_overflow": settings.DB_MAX_OVERFLOW if hasattr(settings, 'DB_MAX_OVERFLOW') else 30,
            "pool_timeout": settings.DB_POOL_TIMEOUT if hasattr(settings, 'DB_POOL_TIMEOUT') else 30,
            "pool_recycle": settings.DB_POOL_RECYCLE if hasattr(settings, 'DB_POOL_RECYCLE') else 3600,
            "pool_pre_ping": True,  # Validate connections before use
        }
        
        # Engine configuration
        engine_config = {
            "echo": settings.SQL_DEBUG if hasattr(settings, 'SQL_DEBUG') else False,
            "echo_pool": False,  # Set to True for connection pool debugging
            "future": True,  # Use SQLAlchemy 2.0 style
            "connect_args": {
                "command_timeout": 60,  # Command timeout in seconds
                "server_settings": {
                    "application_name": "workingtime_api",
                    "jit": "off",  # Disable JIT for consistent performance
                }
            }
        }
        
        # Create the engine
        engine = create_async_engine(
            str(settings.DATABASE_URL),
            **engine_config,
            **pool_config
        )
        
        # Add event listeners for monitoring
        self._setup_engine_listeners(engine)
        
        return engine
    
    def _setup_engine_listeners(self, engine: AsyncEngine) -> None:
        """Setup engine event listeners for monitoring and optimization"""
        
        @event.listens_for(engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Called when a new connection is established"""
            logger.debug("Database connection established")
            
            # Set connection-level optimizations for PostgreSQL
            # Note: For asyncpg, we need to handle cursor differently
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("SET statement_timeout = '300s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '5min'")
                cursor.execute("SET lock_timeout = '30s'")
                cursor.close()
            except Exception as e:
                logger.warning(f"Failed to set connection optimizations: {e}")
        
        @event.listens_for(engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when a connection is checked out from the pool"""
            connection_record.info.setdefault("use_count", 0)
            connection_record.info["use_count"] += 1
        
        @event.listens_for(engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Called when a connection is returned to the pool"""
            use_count = connection_record.info.get("use_count", 0)
            if use_count > 100:
                logger.warning(
                    f"Connection used {use_count} times, consider increasing pool size"
                )
    
    @property
    def engine(self) -> AsyncEngine:
        """Lazy initialization of engine"""
        if self._engine is None:
            self._engine = self.create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Lazy initialization of session factory"""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )
        return self._session_factory
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with proper resource management"""
        session = self.session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def get_session_with_lock(self) -> LockedSession:
        """Get a session with lock for specific operations"""
        session = self.session_factory()
        lock = asyncio.Lock()
        return LockedSession(session, lock)
    
    async def health_check(self) -> dict:
        """Perform database health check"""
        try:
            async with self.get_session() as session:
                result = await session.execute("SELECT 1 as health_check")
                row = result.fetchone()
                
                if row and row[0] == 1:
                    pool_status = self.engine.pool.status()
                    return {
                        "status": "healthy",
                        "pool_size": self.engine.pool.size(),
                        "pool_checked_out": pool_status.get("checkedout", 0),
                        "pool_overflow": self.engine.pool.overflow(),
                    }
                else:
                    return {"status": "unhealthy", "error": "Invalid query result"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_connection_pool_stats(self) -> dict:
        """Get detailed connection pool statistics"""
        pool = self.engine.pool
        stats = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
        }
        
        # Add invalid connections if available
        try:
            stats["invalid"] = pool.invalid()
        except (AttributeError, TypeError):
            stats["invalid"] = 0
            
        return stats

    async def close(self) -> None:
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database configuration instance
db_config = OptimizedDatabaseConfig()

# Backward compatibility functions
engine = db_config.engine

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency for FastAPI - optimized version"""
    async with db_config.get_session() as session:
        lock = asyncio.Lock()
        locked_session = LockedSession(session, lock)
        try:
            yield locked_session
        finally:
            pass  # Session is automatically closed by context manager

async def get_db_without_lock() -> AsyncGenerator[AsyncSession, None]:
    """Get database session without lock for non-critical operations"""
    async with db_config.get_session() as session:
        yield session

class DatabaseManager:
    """High-level database management class"""
    
    def __init__(self):
        self.config = db_config
    
    async def execute_query(self, query: str, params: dict = None) -> list:
        """Execute a raw SQL query safely"""
        async with self.config.get_session() as session:
            result = await session.execute(query, params or {})
            return result.fetchall()
    
    async def execute_batch(self, queries: list[tuple[str, dict]]) -> None:
        """Execute multiple queries in a single transaction"""
        async with self.config.get_session() as session:
            try:
                for query, params in queries:
                    await session.execute(query, params or {})
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def get_connection_pool_stats(self) -> dict:
        """Get detailed connection pool statistics"""
        pool = self.config.engine.pool
        stats = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
        }
        
        try:
            stats["invalid"] = pool.invalid()
        except (AttributeError, TypeError):
            stats["invalid"] = 0
            
        return stats
    
    async def warm_up_connections(self, count: int = 5) -> None:
        """Warm up connection pool with initial connections"""
        logger.info(f"Warming up {count} database connections...")
        
        async with self.config.get_session() as session:
            # This will create initial connections
            for i in range(count):
                try:
                    await session.execute("SELECT 1")
                    await session.commit()
                except Exception as e:
                    logger.warning(f"Failed to warm up connection {i+1}: {e}")

# Global database manager instance
db_manager = DatabaseManager()

# Application lifecycle management
async def init_database() -> None:
    """Initialize database connections and warm up pool"""
    logger.info("Initializing database connections...")
    
    # Warm up connections
    await db_manager.warm_up_connections()
    
    # Perform health check
    health = await db_config.health_check()
    if health["status"] == "healthy":
        logger.info(f"Database initialized successfully. Pool stats: {health}")
    else:
        logger.error(f"Database initialization failed: {health}")

async def shutdown_database() -> None:
    """Close database connections"""
    logger.info("Shutting down database connections...")
    await db_config.close()
    logger.info("Database connections closed")

# Export main components
__all__ = [
    "db_config",
    "db_manager", 
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "get_db_without_lock",
    "init_database",
    "shutdown_database",
    "DatabaseManager"
]
