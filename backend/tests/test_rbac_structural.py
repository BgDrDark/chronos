"""Structural RBAC tests (audit 23.10, Phase 2)."""

from unittest.mock import AsyncMock, MagicMock

from backend.auth.rbac_service import PermissionService
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
