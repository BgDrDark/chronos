"""Effective role resolution.

Single source of truth: ``company_role_assignments``. ``users.role_id`` is
kept as a display/fallback value during the transition (audit 23.10, R5/D1).
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CompanyRoleAssignment, Role, User

logger = logging.getLogger(__name__)


def pick_primary_role(roles: list[Any]) -> Any | None:
    """Return the highest-priority role, or None."""
    if not roles:
        return None
    return max(roles, key=lambda role: role.priority or 0)


async def get_effective_roles(
    db: AsyncSession,
    user_id: int,
    company_id: int | None = None,
) -> list[Role]:
    """Roles assigned to the user in the company (all companies when None)."""
    stmt = (
        select(Role)
        .join(CompanyRoleAssignment, CompanyRoleAssignment.role_id == Role.id)
        .where(
            CompanyRoleAssignment.user_id == user_id,
            CompanyRoleAssignment.is_active.is_(True),
        )
        .order_by(Role.priority.desc())
    )
    if company_id is not None:
        stmt = stmt.where(CompanyRoleAssignment.company_id == company_id)

    roles = list((await db.execute(stmt)).scalars().unique())
    if roles:
        return roles

    # Transition fallback: legacy users.role_id without an assignment.
    fallback = await db.execute(
        select(Role).join(User, User.role_id == Role.id).where(User.id == user_id)
    )
    role = fallback.scalar_one_or_none()
    if role is not None:
        logger.warning(
            "User %s has no company_role_assignment; falling back to users.role_id=%s",
            user_id,
            role.id,
        )
        return [role]
    return []


async def get_effective_role(
    db: AsyncSession,
    user_id: int,
    company_id: int | None = None,
) -> Role | None:
    """Primary (highest-priority) effective role for the user."""
    return pick_primary_role(await get_effective_roles(db, user_id, company_id))
