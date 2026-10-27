"""Reusable FastAPI auth dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import jwt_utils
from backend.database.database import get_db

ADMIN_ROLES = ("admin", "super_admin")


async def require_admin_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Require an authenticated admin or super_admin (JWT, cookie or API key).

    The role comes from the effective role resolver, so admins granted through
    ``company_role_assignments`` are recognised too (audit 23.10, A6).
    """
    user = await jwt_utils.get_current_user(request, db)

    role_name = user.role.name if user.role else None
    if role_name not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user
