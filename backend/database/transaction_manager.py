"""
Transaction Manager for Atomic Database Operations

Provides atomic transaction context managers and utilities to ensure
data consistency and prevent race conditions in critical operations.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any, Callable
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession, AsyncTransaction
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import select, text

from backend.database.session_proxy import LockedSession

logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """Base exception for transaction-related errors"""
    pass


class DeadlockError(TransactionError):
    """Raised when a deadlock is detected"""
    pass


class ConcurrentModificationError(TransactionError):
    """Raised when concurrent modification is detected"""
    pass


@asynccontextmanager
async def atomic_transaction(
    db: AsyncSession,
    isolation_level: Optional[str] = None,
    readonly: bool = False,
    deferrable: bool = False
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide atomic transaction context with automatic rollback on errors.
    
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
    
    # Check if there's already a transaction in progress
    in_transaction = session.in_transaction()
    
    transaction: Optional[AsyncTransaction] = None
    should_commit = False
    
    try:
        if not in_transaction:
            # Begin new transaction only if one doesn't exist
            transaction = await session.begin()
            should_commit = True
            logger.debug(f"Transaction started: {transaction}")
        else:
            logger.debug("Using existing transaction")
        
        # Yield session for operations
        yield session
        
        # Commit only if we started the transaction
        if should_commit and transaction:
            await transaction.commit()
            logger.debug(f"Transaction committed: {transaction}")
        
    except IntegrityError as e:
        # Handle integrity constraint violations
        if should_commit and transaction:
            await transaction.rollback()
        logger.error(f"Integrity error in transaction: {e}")
        raise TransactionError(f"Data integrity violation: {str(e)}") from e
        
    except OperationalError as e:
        # Handle deadlocks and other operational errors
        if should_commit and transaction:
            await transaction.rollback()
            
        error_str = str(e).lower()
        if "deadlock" in error_str:
            logger.error(f"Deadlock detected in transaction: {e}")
            raise DeadlockError(f"Database deadlock: {str(e)}") from e
        else:
            logger.error(f"Operational error in transaction: {e}")
            raise TransactionError(f"Database operational error: {str(e)}") from e
            
    except SQLAlchemyError as e:
        # Handle other SQLAlchemy errors
        if should_commit and transaction:
            await transaction.rollback()
        logger.error(f"SQLAlchemy error in transaction: {e}")
        raise TransactionError(f"Database error: {str(e)}") from e
        
    except Exception as e:
        # Handle any other errors
        if should_commit and transaction:
            await transaction.rollback()
        logger.error(f"Unexpected error in transaction: {e}")
        raise TransactionError(f"Transaction failed: {str(e)}") from e
        
    finally:
        # In SQLAlchemy 2.0 Async, transaction is closed by the context manager 
        # or when session is closed.
        pass


@asynccontextmanager
async def locked_transaction(
    db: AsyncSession,
    lock_timeout: int = 30,
    nowait: bool = False
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide transaction with row-level locking for preventing race conditions.
    
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
        # Set lock timeout
        await tx.execute(text(f"SET lock_timeout = {lock_timeout * 1000}"))
        
        yield tx


def atomic(
    isolation_level: Optional[str] = None,
    readonly: bool = False,
    max_retries: int = 3,
    retry_delay: float = 0.1
) -> Callable:
    """
    Decorator to make functions atomic with automatic transaction management.
    
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
                        readonly=readonly
                    ):
                        return await func(*args, **kwargs)
                        
                except DeadlockError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Deadlock detected, retrying (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
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
    """
    Decorator for read-only operations with repeatable read isolation.
    
    Args:
        max_retries: Maximum retry attempts
        
    Returns:
        Decorated function with read-only transaction
    """
    return atomic(
        isolation_level="READ COMMITTED",
        readonly=True,
        max_retries=max_retries
    )


async def with_row_lock(
    db: AsyncSession,
    query,
    lock_timeout: int = 30,
    nowait: bool = False
):
    """
    Execute query with row-level locking.
    
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
    
    # Set lock timeout
    await session.execute(text(f"SET lock_timeout = {lock_timeout * 1000}"))
    
    # Execute query with row lock
    locked_query = query.with_for_update(nowait=nowait)
    result = await session.execute(locked_query)
    
    return result


class TransactionMonitor:
    """Monitor and log transaction statistics"""
    
    def __init__(self):
        self.stats = {
            'total_transactions': 0,
            'committed_transactions': 0,
            'rolled_back_transactions': 0,
            'deadlocks': 0,
            'concurrent_modifications': 0
        }
    
    def record_transaction_start(self):
        """Record transaction start"""
        self.stats['total_transactions'] += 1
        
    def record_commit(self):
        """Record successful commit"""
        self.stats['committed_transactions'] += 1
        
    def record_rollback(self):
        """Record rollback"""
        self.stats['rolled_back_transactions'] += 1
        
    def record_deadlock(self):
        """Record deadlock"""
        self.stats['deadlocks'] += 1
        
    def record_concurrent_modification(self):
        """Record concurrent modification"""
        self.stats['concurrent_modifications'] += 1
        
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
    isolation_level: Optional[str] = None
) -> Any:
    """
    Execute multiple operations atomically.
    
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
    'atomic_transaction',
    'locked_transaction', 
    'atomic',
    'read_committed',
    'with_row_lock',
    'TransactionError',
    'DeadlockError',
    'ConcurrentModificationError',
    'TransactionMonitor',
    'transaction_monitor',
    'execute_atomic'
]