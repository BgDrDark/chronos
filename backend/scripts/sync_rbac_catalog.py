"""Idempotently sync DEFAULT_PERMISSIONS / DEFAULT_ROLES into the database.

Run after deploying a catalog change:
    docker compose exec backend python -m backend.scripts.sync_rbac_catalog
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.auth.rbac_service import DEFAULT_PERMISSIONS, DEFAULT_ROLES
from backend.database.database import AsyncSessionLocal
from backend.database.models import Permission, Role, RolePermission
from sqlalchemy import select


async def sync_catalog() -> dict[str, int]:
    created_permissions = 0
    created_links = 0
    created_roles = 0

    async with AsyncSessionLocal() as db:
        existing_permissions = {
            row.name: row
            for row in (await db.execute(select(Permission))).scalars()
        }
        for name, data in DEFAULT_PERMISSIONS.items():
            if name not in existing_permissions:
                db.add(
                    Permission(
                        name=name,
                        resource=data["resource"],
                        action=data["action"],
                        description=data["description"],
                    )
                )
                created_permissions += 1
        await db.flush()

        permissions_by_name = {
            row.name: row
            for row in (await db.execute(select(Permission))).scalars()
        }
        roles_by_name = {
            row.name: row
            for row in (await db.execute(select(Role))).scalars()
        }

        for role_name, role_data in DEFAULT_ROLES.items():
            role = roles_by_name.get(role_name)
            if role is None:
                role = Role(
                    name=role_name,
                    description=role_data["description"],
                    priority=role_data["priority"],
                    is_system_role=role_data.get("is_system_role", False),
                )
                db.add(role)
                await db.flush()
                roles_by_name[role_name] = role
                created_roles += 1

            existing_links = {
                link.permission_id
                for link in (
                    await db.execute(
                        select(RolePermission).where(RolePermission.role_id == role.id)
                    )
                ).scalars()
            }
            for permission_name in role_data.get("permissions", []):
                permission = permissions_by_name.get(permission_name)
                if permission and permission.id not in existing_links:
                    db.add(
                        RolePermission(
                            role_id=role.id,
                            permission_id=permission.id,
                        )
                    )
                    created_links += 1

        await db.commit()

    return {
        "permissions_created": created_permissions,
        "roles_created": created_roles,
        "role_permissions_created": created_links,
    }


async def main() -> None:
    result = await sync_catalog()
    print(
        "RBAC sync complete: "
        f"{result['permissions_created']} permissions, "
        f"{result['roles_created']} roles, "
        f"{result['role_permissions_created']} role links created."
    )


if __name__ == "__main__":
    asyncio.run(main())
