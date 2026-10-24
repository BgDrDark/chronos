"""Permission audit writer.

Audit records must survive a business rollback: a denied mutation raises and
rolls the request transaction back, but the denial itself must be recorded.
That is why audit writes use a dedicated short-lived session instead of the
request session (audit 23.10, R8/D6/D12).
"""

import logging

from backend.database.database import AsyncSessionLocal
from backend.database.models import PermissionAuditLog

logger = logging.getLogger(__name__)


async def write_permission_audit(
    *,
    user_id: int | None,
    permission: str,
    decision: bool,
    resource_type: str | None = None,
    resource_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Persist one permission decision. Never raises to the caller."""
    try:
        async with AsyncSessionLocal() as db:
            db.add(
                PermissionAuditLog(
                    user_id=user_id,
                    action="GRANTED" if decision else "DENIED",
                    permission=permission,
                    decision="GRANTED" if decision else "DENIED",
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to write permission audit entry")
