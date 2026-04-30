"""Utility functions for GraphQL mutations."""
from typing import Any


def wrap_with_atomic(db_session) -> Any:
    """
    Wrap a database session with atomic_transaction.
    
    Returns a context manager that can be used to wrap mutations.
    
    Usage:
        async def my_mutation(self, info, input):
            db = info.context["db"]
            async with wrap_with_atomic(db) as tx:
                await tx.add(...)
                # Automatic commit on success, rollback on error
                return result
    """
    from backend.database.transaction_manager import atomic_transaction
    return atomic_transaction(db_session)