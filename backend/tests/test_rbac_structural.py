"""Structural RBAC tests (audit 23.10, Phase 2)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from backend.auth.rbac_service import (
    DEFAULT_ROLES,
    PermissionService,
    expand_role_permissions,
)
from backend.chronos_graphql.permission_middleware import (
    extract_target_company_id,
)


def _db_returning(rows):
    """Build a mock session whose execute() yields ``rows`` from scalars().all()."""
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=rows)))
    ))
    db.flush = AsyncMock()
    return db


def test_extract_company_id_from_snake_case_kwarg():
    assert extract_target_company_id({"company_id": 7}) == 7


def test_extract_company_id_from_input_dict():
    assert extract_target_company_id({"input": {"company_id": 9}}) == 9


def test_extract_company_id_from_user_input_dict():
    assert extract_target_company_id({"user_input": {"company_id": 11}}) == 11


def test_extract_company_id_from_camel_case_user_input_dict():
    assert extract_target_company_id({"userInput": {"company_id": 13}}) == 13


def test_extract_company_id_returns_none_when_absent():
    assert extract_target_company_id({}) is None


def test_extract_company_id_prefers_explicit_kwarg():
    assert extract_target_company_id({"company_id": 1, "input": {"company_id": 2}}) == 1


async def test_log_permission_decision_uses_dedicated_writer(monkeypatch):
    db = MagicMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    writer = AsyncMock()
    monkeypatch.setattr(
        "backend.auth.audit_writer.write_permission_audit", writer
    )
    service = PermissionService(db)

    await service.log_permission_decision(
        user_id=1,
        permission="users:update",
        decision=False,
        resource_type="mutation",
        resource_id=2,
        context={"ip_address": "127.0.0.1", "user_agent": "pytest"},
    )

    writer.assert_awaited_once_with(
        user_id=1,
        permission="users:update",
        decision=False,
        resource_type="mutation",
        resource_id=2,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    db.commit.assert_not_awaited()
    db.add.assert_not_called()


def test_cache_key_is_company_scoped():
    assert PermissionService.cache_key(1, 2) == "user_1_company_2"


def test_cache_key_for_global_scope():
    assert PermissionService.cache_key(1, None) == "user_1_company_global"


async def test_read_permission_cache_returns_none_when_empty():
    service = PermissionService(_db_returning([]))

    assert await service._read_permission_cache(1, 2) is None


async def test_read_permission_cache_returns_permissions():
    service = PermissionService(_db_returning(["users:list", "users:update"]))

    assert await service._read_permission_cache(1, 2) == {
        "users:list",
        "users:update",
    }


async def test_write_permission_cache_replaces_entries():
    db = _db_returning([])
    service = PermissionService(db)

    await service._write_permission_cache(1, 2, {"users:list"})

    db.execute.assert_awaited_once()
    db.flush.assert_awaited_once()
    added = [call.args[0] for call in db.add.call_args_list]
    assert len(added) == 1
    assert added[0].user_id == 1
    assert added[0].company_id == 2
    assert added[0].permission_name == "users:list"


async def test_invalidate_user_cache_clears_db_and_memory():
    db = _db_returning([])
    service = PermissionService(db)
    service._permission_cache["user_1_company_2"] = {"permissions": []}

    await service.invalidate_user_cache(1)

    db.execute.assert_awaited_once()
    db.flush.assert_awaited_once()
    assert service._permission_cache == {}


def test_employee_permissions_are_unchanged():
    assert expand_role_permissions(["employee"]) == set(
        DEFAULT_ROLES["employee"]["permissions"]
    )


def test_manager_inherits_employee_permissions():
    manager = expand_role_permissions(["manager"])
    employee = expand_role_permissions(["employee"])
    assert employee <= manager


def test_hr_manager_inherits_manager_permissions():
    assert expand_role_permissions(["manager"]) <= expand_role_permissions(
        ["hr_manager"]
    )


def test_global_accountant_inherits_accountant_permissions():
    assert expand_role_permissions(["accountant"]) <= expand_role_permissions(
        ["global_accountant"]
    )


def test_unknown_role_is_ignored():
    assert expand_role_permissions(["does_not_exist"]) == set()


async def test_get_user_permissions_merges_inherited_and_db_permissions():
    role = SimpleNamespace(id=5, name="manager", priority=50)
    assignment = SimpleNamespace(company_id=1)
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            _db_returning([]).execute.return_value,  # cache miss
            [(role, assignment)],  # roles for the user
            [("custom:extra",)],  # direct DB role_permissions
            MagicMock(),  # cache delete
        ]
    )
    db.flush = AsyncMock()
    service = PermissionService(db)

    permissions = await service.get_user_permissions(1, 1)

    assert "custom:extra" in permissions
    assert expand_role_permissions(["manager"]) <= permissions
