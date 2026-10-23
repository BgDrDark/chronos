"""Unit tests for the Phase 1 role-assignment policy (audit 23.10)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from backend.auth.rbac_service import (
    ASSIGNABLE_ROLES,
    can_assign_role,
    resolve_assignable_role,
)
from backend.exceptions import NotFoundException, PermissionDeniedException


@pytest.mark.parametrize(
    ("actor", "target", "expected"),
    [
        # super_admin — всичко, вкл. custom
        ("super_admin", "super_admin", True),
        ("super_admin", "admin", True),
        ("super_admin", "employee", True),
        ("super_admin", "custom_role", True),
        # admin — всичко без super_admin, вкл. custom
        ("admin", "admin", True),
        ("admin", "hr_manager", True),
        ("admin", "employee", True),
        ("admin", "custom_role", True),
        ("admin", "super_admin", False),
        # global_accountant
        ("global_accountant", "accountant", True),
        ("global_accountant", "employee", True),
        ("global_accountant", "viewer", True),
        ("global_accountant", "global_accountant", False),
        ("global_accountant", "hr_manager", False),
        ("global_accountant", "admin", False),
        ("global_accountant", "super_admin", False),
        # accountant
        ("accountant", "employee", True),
        ("accountant", "viewer", True),
        ("accountant", "accountant", False),
        ("accountant", "hr_manager", False),
        ("accountant", "admin", False),
        ("accountant", "super_admin", False),
        # hr_manager
        ("hr_manager", "manager", True),
        ("hr_manager", "driver", True),
        ("hr_manager", "employee", True),
        ("hr_manager", "viewer", True),
        ("hr_manager", "hr_manager", False),
        ("hr_manager", "admin", False),
        ("hr_manager", "super_admin", False),
        # manager / fleet_manager
        ("manager", "employee", True),
        ("manager", "viewer", True),
        ("manager", "manager", False),
        ("fleet_manager", "driver", True),
        ("fleet_manager", "employee", True),
        ("fleet_manager", "admin", False),
        # без права
        ("employee", "employee", False),
        ("driver", "employee", False),
        ("viewer", "employee", False),
        (None, "employee", False),
        ("unknown_role", "employee", False),
    ],
)
def test_can_assign_role(actor, target, expected):
    assert can_assign_role(actor, target) is expected


def test_assignable_roles_does_not_contain_privileged_defaults():
    """super_admin/admin се обработват отделно; не бива да са в allowlist-а."""
    assert "super_admin" not in ASSIGNABLE_ROLES
    assert "admin" not in ASSIGNABLE_ROLES


async def test_resolve_assignable_role_returns_role_when_allowed():
    role = SimpleNamespace(id=5, name="employee")
    db = AsyncMock()
    db.get.return_value = role

    result = await resolve_assignable_role(db, "accountant", 5)

    assert result is role
    assert db.get.await_count == 1
    assert db.get.await_args.args[1] == 5


async def test_resolve_assignable_role_rejects_super_admin_for_accountant():
    db = AsyncMock()
    db.get.return_value = SimpleNamespace(id=1, name="super_admin")

    with pytest.raises(PermissionDeniedException):
        await resolve_assignable_role(db, "accountant", 1)


async def test_resolve_assignable_role_rejects_hr_manager_for_accountant():
    db = AsyncMock()
    db.get.return_value = SimpleNamespace(id=6, name="hr_manager")

    with pytest.raises(PermissionDeniedException):
        await resolve_assignable_role(db, "accountant", 6)


async def test_resolve_assignable_role_missing_role_raises_not_found():
    db = AsyncMock()
    db.get.return_value = None

    with pytest.raises(NotFoundException):
        await resolve_assignable_role(db, "admin", 999)
