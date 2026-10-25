"""Create missing company_role_assignments from users.role_id.

Idempotent. Run once before enabling single-source authorization:
    docker compose exec backend python -m backend.scripts.backfill_role_assignments
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.database import AsyncSessionLocal
from backend.database.models import CompanyRoleAssignment, User
from sqlalchemy import select


async def backfill() -> int:
    created = 0
    async with AsyncSessionLocal() as db:
        users = (
            await db.execute(
                select(User).where(
                    User.role_id.is_not(None),
                    User.company_id.is_not(None),
                    User.is_active.is_(True),
                )
            )
        ).scalars()

        for user in users:
            exists = await db.execute(
                select(CompanyRoleAssignment.id).where(
                    CompanyRoleAssignment.user_id == user.id,
                    CompanyRoleAssignment.company_id == user.company_id,
                    CompanyRoleAssignment.role_id == user.role_id,
                )
            )
            if exists.scalar_one_or_none() is None:
                db.add(
                    CompanyRoleAssignment(
                        user_id=user.id,
                        company_id=user.company_id,
                        role_id=user.role_id,
                        assigned_by=None,
                        is_active=True,
                    )
                )
                created += 1

        await db.commit()
    return created


async def main() -> None:
    created = await backfill()
    print(f"Backfill complete: {created} company_role_assignments created.")


if __name__ == "__main__":
    asyncio.run(main())
