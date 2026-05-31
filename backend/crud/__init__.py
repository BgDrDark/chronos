"""CRUD модул с Repository Pattern

Забележка: Този модул поддържа backward compatibility със стария crud.py
Новият код може да използва repositories директно:
    from backend.crud.repositories import user_repo, company_repo

Също така можете да използвате:
    from backend.crud import user_repo, company_repo
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Import repositories за директен достъп
from backend.crud.repositories import (
    access_repo,
    company_repo,
    payroll_repo,
    production_repo,
    settings_repo,
    time_repo,
    trz_repo,
    user_repo,
    warehouse_repo,
)

# Export на singleton инстанциите
__all__ = [
    # Repositories
    "user_repo",
    "company_repo",
    "time_repo",
    "payroll_repo",
    "trz_repo",
    "production_repo",
    "warehouse_repo",
    "access_repo",
    "settings_repo",
]

# Lazy import for backward compatibility with legacy crud.py
# This allows "from backend import crud; crud.some_function()" to work
import sys as _sys


def __getattr__(name):
    """Dynamic import from legacy crud for backward compatibility"""
    # Import the legacy module
    from backend import crud_legacy as _legacy

    if hasattr(_legacy, name):
        return getattr(_legacy, name)

    raise AttributeError(f"module 'backend.crud' has no attribute '{name}'")

# For direct imports like: from backend.crud import get_user_by_email
# We can also expose specific commonly used functions
from backend.crud_legacy import (
    Payslip,
    create_company,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    get_users,
    sofia_now,
    update_company,
    update_user,
)
