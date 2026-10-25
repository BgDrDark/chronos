"""Delete permission audit entries older than the retention window.

The permission audit log grows on every permission decision, so it must be
pruned. Retention follows ``AUTH_KEY_RETENTION_DAYS``-style policy for audit
data (audit 23.10, R15/D12).
"""

import logging
from datetime import timedelta

from sqlalchemy import delete

from backend.database.database import AsyncSessionLocal
from backend.database.models import PermissionAuditLog, sofia_now

logger = logging.getLogger(__name__)

RETENTION_DAYS = 90


async def purge_old_audit_entries() -> int:
    """Remove audit rows older than ``RETENTION_DAYS``. Returns rows deleted."""
    cutoff = sofia_now() - timedelta(days=RETENTION_DAYS)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(PermissionAuditLog).where(PermissionAuditLog.created_at < cutoff)
        )
        await db.commit()
        deleted = result.rowcount or 0
    if deleted:
        logger.info(
            "Purged %s permission audit entries older than %s days",
            deleted,
            RETENTION_DAYS,
        )
    return deleted
