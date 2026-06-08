"""Transaction Manager for Atomic Database Operations

Provides atomic transaction context managers and utilities to ensure
data consistency and prevent race conditions in critical operations.
"""

import asyncio
import logging
import random
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncTransaction

from backend.database.session_proxy import LockedSession

logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """Base exception for transaction-related errors"""



class DeadlockError(TransactionError):
    """Raised when a deadlock is detected"""



class ConcurrentModificationError(TransactionError):
    """Raised when concurrent modification is detected"""



@asynccontextmanager
async def atomic_transaction(
    db: AsyncSession,
    isolation_level: str | None = None,
    readonly: bool = False,
    deferrable: bool = False,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide atomic transaction context with automatic rollback on errors.
    
    Args:
        db: Database session (AsyncSession or LockedSession)
        isolation_level: Transaction isolation level (not supported in AsyncSession.begin())
        readonly: Whether transaction is read-only (not supported in AsyncSession.begin())
        deferrable: Whether transaction is deferrable (not supported in AsyncSession.begin())
        
    Yields:
        Database session within transaction context
        
    Raises:
        TransactionError: If transaction fails
        DeadlockError: If deadlock is detected
        ConcurrentModificationError: If concurrent modification detected

    """
    # Get underlying session if LockedSession
    if isinstance(db, LockedSession):
        session = db.session
    else:
        session = db

    # Track nesting depth to handle SQLAlchemy's auto-started transactions.
    # SQLAlchemy begins a transaction implicitly on the first query, so
    # in_transaction() is unreliable for deciding who should commit.
    depth = getattr(session, "_atomic_depth", 0)
    is_outermost = (depth == 0)
    session._atomic_depth = depth + 1

    transaction: AsyncTransaction | None = None
    should_commit = False

    try:
        if not session.in_transaction():
            await session.begin()
            should_commit = is_outermost
            logger.info("Transaction started (depth=%d)", depth + 1)
        else:
            should_commit = is_outermost
            logger.info("Using existing transaction (depth=%d)", depth + 1)

        # Yield session for operations
        yield session

        if should_commit and session.in_transaction():
            logger.info("Attempting to commit transaction...")
            await session.commit()
            logger.info("Transaction committed")

    except IntegrityError as e:
        if should_commit and session.in_transaction():
            await session.rollback()
        logger.error(f"Integrity error in transaction: {e}")
        raise TransactionError(f"Data integrity violation: {e!s}") from e

    except OperationalError as e:
        if should_commit and session.in_transaction():
            await session.rollback()

        error_str = str(e).lower()
        if "deadlock" in error_str:
            logger.error(f"Deadlock detected in transaction: {e}")
            raise DeadlockError(f"Database deadlock: {e!s}") from e
        else:
            logger.error(f"Operational error in transaction: {e}")
            raise TransactionError(f"Database operational error: {e!s}") from e

    except SQLAlchemyError as e:
        if should_commit and session.in_transaction():
            await session.rollback()
        logger.error(f"SQLAlchemy error in transaction: {e}")
        raise TransactionError(f"Database error: {e!s}") from e

    except Exception as e:
        if should_commit and session.in_transaction():
            await session.rollback()
        logger.error(f"Unexpected error in transaction: {e}, should_commit={should_commit}")
        raise TransactionError(f"Transaction failed: {e!s}") from e

    finally:
        session._atomic_depth = max(0, getattr(session, "_atomic_depth", 1) - 1)


@asynccontextmanager
async def locked_transaction(
    db: AsyncSession,
    lock_timeout: int = 30,
    nowait: bool = False,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide transaction with row-level locking for preventing race conditions.
    
    Args:
        db: Database session
        lock_timeout: Lock timeout in seconds
        nowait: Whether to fail immediately if lock cannot be acquired
        
    Yields:
        Database session with locking capabilities

    """
    # Get underlying session if LockedSession
    if isinstance(db, LockedSession):
        session = db.session
    else:
        session = db

    async with atomic_transaction(session) as tx:
        # Set lock timeout (validate and convert to prevent SQL injection)
        lock_timeout_ms = int(lock_timeout) * 1000
        if lock_timeout_ms < 0 or lock_timeout_ms > 3600000:  # Max 1 hour
            raise ValueError("lock_timeout must be between 0 and 3600 seconds")
        await tx.execute(text(f"SET lock_timeout = {lock_timeout_ms}"))

        yield tx


def atomic(
    isolation_level: str | None = None,
    readonly: bool = False,
    max_retries: int = 3,
    retry_delay: float = 0.1,
) -> Callable:
    """Decorator to make functions atomic with automatic transaction management.
    
    Args:
        isolation_level: Transaction isolation level
        readonly: Whether transaction is read-only
        max_retries: Maximum retry attempts for deadlocks
        retry_delay: Delay between retries in seconds
        
    Returns:
        Decorated function with atomic transaction

    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Find database session in arguments
            db = None
            for arg in args:
                if isinstance(arg, (AsyncSession, LockedSession)):
                    db = arg
                    break

            if not db:
                raise ValueError("No database session found in function arguments")

            # Retry logic for deadlocks
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    async with atomic_transaction(
                        db,
                        isolation_level=isolation_level,
                        readonly=readonly,
                    ):
                        return await func(*args, **kwargs)

                except DeadlockError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Deadlock detected, retrying (attempt {attempt + 1}/{max_retries})")
                        delay = retry_delay * (2 ** attempt)
                        jitter = delay * 0.2 * random.random()
                        await asyncio.sleep(delay + jitter)  # Exponential backoff with jitter
                    else:
                        logger.error(f"Max retries exceeded for deadlock: {e}")
                        raise

                except TransactionError:
                    # Don't retry other transaction errors
                    raise

            # Should not reach here
            raise last_exception

        return wrapper
    return decorator


def read_committed(max_retries: int = 3) -> Callable:
    """Decorator for read-only operations with repeatable read isolation.
    
    Args:
        max_retries: Maximum retry attempts
        
    Returns:
        Decorated function with read-only transaction

    """
    return atomic(
        isolation_level="READ COMMITTED",
        readonly=True,
        max_retries=max_retries,
    )


@asynccontextmanager
async def atomic_with_savepoint(db: AsyncSession, name: str = "sp1"):
    """Context manager for savepoint within a transaction.
    
    Allows partial rollback to a specific point without rolling back
    the entire transaction. Useful for complex operations where
    some steps are critical and others are optional.
    
    Args:
        db: Database session
        name: Savepoint name (must be unique within transaction)
    
    Example:
        async with atomic_transaction(db):
            await create_user(...)
            async with atomic_with_savepoint(db, "user_created"):
                await send_welcome_email(...)  # If fails, user remains

    """
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
    if not safe_name:
        raise ValueError("Savepoint name must contain at least one alphanumeric character, underscore, or hyphen")
    await db.execute(text(f"SAVEPOINT {safe_name}"))
    try:
        yield
    except Exception as e:
        await db.execute(text(f"ROLLBACK TO SAVEPOINT {safe_name}"))
        logger.info(f"Rolled back to savepoint {safe_name}: {e}")
        raise
    finally:
        try:
            await db.execute(text(f"RELEASE SAVEPOINT {safe_name}"))
        except Exception:
            pass  # Already released or no active savepoint


async def with_row_lock(
    db: AsyncSession,
    query,
    lock_timeout: int = 30,
    nowait: bool = False,
):
    """Execute query with row-level locking.
    
    Args:
        db: Database session
        query: SQLAlchemy query to execute
        lock_timeout: Lock timeout in seconds
        nowait: Whether to fail immediately if lock cannot be acquired
        
    Returns:
        Query result with locked rows

    """
    # Get underlying session if LockedSession
    if isinstance(db, LockedSession):
        session = db.session
    else:
        session = db

    # Set lock timeout (validate and convert to prevent SQL injection)
    lock_timeout_ms = int(lock_timeout) * 1000
    if lock_timeout_ms < 0 or lock_timeout_ms > 3600000:  # Max 1 hour
        raise ValueError("lock_timeout must be between 0 and 3600 seconds")
    await session.execute(text(f"SET lock_timeout = {lock_timeout_ms}"))

    # Execute query with row lock
    locked_query = query.with_for_update(nowait=nowait)
    result = await session.execute(locked_query)

    return result


class TransactionMonitor:
    """Monitor and log transaction statistics"""

    def __init__(self):
        self.stats = {
            "total_transactions": 0,
            "committed_transactions": 0,
            "rolled_back_transactions": 0,
            "deadlocks": 0,
            "concurrent_modifications": 0,
        }

    def record_transaction_start(self):
        """Record transaction start"""
        self.stats["total_transactions"] += 1

    def record_commit(self):
        """Record successful commit"""
        self.stats["committed_transactions"] += 1

    def record_rollback(self):
        """Record rollback"""
        self.stats["rolled_back_transactions"] += 1

    def record_deadlock(self):
        """Record deadlock"""
        self.stats["deadlocks"] += 1

    def record_concurrent_modification(self):
        """Record concurrent modification"""
        self.stats["concurrent_modifications"] += 1

    def get_stats(self) -> dict:
        """Get transaction statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics"""
        for key in self.stats:
            self.stats[key] = 0


# Global transaction monitor instance
transaction_monitor = TransactionMonitor()


# Utility functions for common transaction patterns
async def execute_atomic(
    db: AsyncSession,
    operations: list,
    isolation_level: str | None = None,
) -> Any:
    """Execute multiple operations atomically.
    
    Args:
        db: Database session
        operations: List of async operations to execute
        isolation_level: Transaction isolation level
        
    Returns:
        Results from operations

    """
    async with atomic_transaction(db, isolation_level=isolation_level) as tx:
        results = []
        for operation in operations:
            if callable(operation):
                result = await operation(tx)
                results.append(result)
            else:
                raise ValueError("Operation must be callable")
        return results


# Export main utilities
__all__ = [
    "ConcurrentModificationError",
    "DeadlockError",
    "TransactionError",
    "TransactionMonitor",
    "atomic",
    "atomic_transaction",
    "atomic_with_savepoint",
    "execute_atomic",
    "locked_transaction",
    "read_committed",
    "transaction_monitor",
    "with_row_lock",
]
