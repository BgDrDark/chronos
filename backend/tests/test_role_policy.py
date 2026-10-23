"""Unit tests for the Phase 1 role-assignment policy (audit 23.10)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from backend.auth.rbac_service import (
    ASSIGNABLE_ROLES,
    can_assign_role,
    resolve_assignable_role,
)
from backend.chronos_graphql.inputs.user import UpdateUserInput, UserCreateInput
from backend.chronos_graphql.mutations.user import UserMutation
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


def _async_db():
    """AsyncSession mock: async methods are AsyncMock, sync ones are MagicMock."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.execute.return_value = MagicMock()
    db.get = AsyncMock()
    db.scalar = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


async def test_create_user_creates_company_role_assignment(monkeypatch):
    db = _async_db()
    db.scalar.return_value = 5  # employee role id
    current_user = SimpleNamespace(
        id=1, company_id=10, role=SimpleNamespace(name="accountant")
    )
    info = MagicMock()
    info.context = {"db": db, "current_user": current_user}

    role = SimpleNamespace(id=5, name="employee")
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.resolve_assignable_role",
        AsyncMock(return_value=role),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.check_company_access",
        AsyncMock(return_value=10),
    )
    db_user = SimpleNamespace(id=42, company_id=10)
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.create_user",
        AsyncMock(return_value=db_user),
    )
    create_assignment = AsyncMock()
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.create_company_role_assignment",
        create_assignment,
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.schemas.User.model_validate",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.types.User.from_pydantic",
        MagicMock(return_value="user"),
    )
    db.execute.return_value.scalar_one.return_value = MagicMock()

    result = await UserMutation().create_user(
        UserCreateInput(password="Secret123!", company_id=10), info
    )

    assert result == "user"
    create_assignment.assert_awaited_once_with(
        db,
        user_id=42,
        company_id=10,
        role_id=5,
        assigned_by=1,
    )
    db.commit.assert_awaited_once()


async def test_create_user_rejects_super_admin_role(monkeypatch):
    db = _async_db()
    current_user = SimpleNamespace(
        id=1, company_id=10, role=SimpleNamespace(name="accountant")
    )
    info = MagicMock()
    info.context = {"db": db, "current_user": current_user}
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.check_company_access",
        AsyncMock(return_value=10),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.resolve_assignable_role",
        AsyncMock(side_effect=PermissionDeniedException(detail="denied")),
    )

    with pytest.raises(PermissionDeniedException):
        await UserMutation().create_user(
            UserCreateInput(password="Secret123!", company_id=10, role_id=1),
            info,
        )

    db.commit.assert_not_awaited()


async def test_update_user_self_role_change_is_denied(monkeypatch):
    db = _async_db()
    current_user = SimpleNamespace(
        id=7, company_id=10, role=SimpleNamespace(name="employee")
    )
    info = MagicMock()
    info.context = {"db": db, "current_user": current_user}
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.check_company_access",
        AsyncMock(return_value=10),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.get_by_id",
        AsyncMock(return_value=SimpleNamespace(id=7, company_id=10)),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.require_permission",
        AsyncMock(return_value=True),
    )

    with pytest.raises(PermissionDeniedException):
        await UserMutation().update_user(UpdateUserInput(id=7, role_id=1), info)

    db.commit.assert_not_awaited()


async def test_update_user_role_change_requires_manage_roles(monkeypatch):
    db = _async_db()
    current_user = SimpleNamespace(
        id=1, company_id=10, role=SimpleNamespace(name="accountant")
    )
    info = MagicMock()
    info.context = {"db": db, "current_user": current_user}
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.check_company_access",
        AsyncMock(return_value=10),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.get_by_id",
        AsyncMock(return_value=SimpleNamespace(id=7, company_id=10)),
    )

    calls = []

    async def fake_require_permission(info, permission, company_id=None, resource_id=None):
        calls.append(permission)
        if permission == "users:manage_roles":
            raise PermissionDeniedException(detail="denied")
        return True

    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.require_permission",
        fake_require_permission,
    )

    with pytest.raises(PermissionDeniedException):
        await UserMutation().update_user(UpdateUserInput(id=7, role_id=1), info)

    assert "users:update" in calls
    assert "users:manage_roles" in calls


async def test_update_user_role_change_rejects_super_admin(monkeypatch):
    db = _async_db()
    current_user = SimpleNamespace(
        id=1, company_id=10, role=SimpleNamespace(name="hr_manager")
    )
    info = MagicMock()
    info.context = {"db": db, "current_user": current_user}
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.check_company_access",
        AsyncMock(return_value=10),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.get_by_id",
        AsyncMock(return_value=SimpleNamespace(id=7, company_id=10)),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.require_permission",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.resolve_assignable_role",
        AsyncMock(side_effect=PermissionDeniedException(detail="denied")),
    )

    with pytest.raises(PermissionDeniedException):
        await UserMutation().update_user(UpdateUserInput(id=7, role_id=1), info)


async def test_update_user_commits(monkeypatch):
    db = _async_db()
    current_user = SimpleNamespace(
        id=1, company_id=10, role=SimpleNamespace(name="admin")
    )
    info = MagicMock()
    info.context = {"db": db, "current_user": current_user}
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.check_company_access",
        AsyncMock(return_value=10),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.require_permission",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.get_by_id",
        AsyncMock(return_value=SimpleNamespace(id=7, company_id=10)),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.update_user",
        AsyncMock(return_value=SimpleNamespace(id=7, company_id=10)),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.schemas.User.model_validate",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.types.User.from_pydantic",
        MagicMock(return_value="user"),
    )
    db.execute.return_value.scalar_one.return_value = MagicMock()

    result = await UserMutation().update_user(
        UpdateUserInput(id=7, first_name="New"), info
    )

    assert result == "user"
    db.commit.assert_awaited_once()


async def test_update_user_role_change_syncs_assignment(monkeypatch):
    db = _async_db()
    current_user = SimpleNamespace(
        id=1, company_id=10, role=SimpleNamespace(name="hr_manager")
    )
    info = MagicMock()
    info.context = {"db": db, "current_user": current_user}
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.check_company_access",
        AsyncMock(return_value=10),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.require_permission",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.get_by_id",
        AsyncMock(return_value=SimpleNamespace(id=7, company_id=10)),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.resolve_assignable_role",
        AsyncMock(return_value=SimpleNamespace(id=6, name="manager")),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.update_user",
        AsyncMock(return_value=SimpleNamespace(id=7, company_id=10)),
    )
    replace_assignment = AsyncMock()
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.user_repo.replace_company_role_assignment",
        replace_assignment,
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.schemas.User.model_validate",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        "backend.chronos_graphql.mutations.user.types.User.from_pydantic",
        MagicMock(return_value="user"),
    )
    db.execute.return_value.scalar_one.return_value = MagicMock()

    result = await UserMutation().update_user(
        UpdateUserInput(id=7, role_id=6), info
    )

    assert result == "user"
    replace_assignment.assert_awaited_once_with(
        db,
        user_id=7,
        company_id=10,
        role_id=6,
        assigned_by=1,
    )
    db.commit.assert_awaited_once()
