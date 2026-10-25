"""Structural RBAC tests (audit 23.10, Phase 2)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from backend.auth.rbac_service import (
    DEFAULT_PERMISSIONS,
    DEFAULT_ROLES,
    PermissionService,
    expand_role_permissions,
)
from backend.auth.role_resolver import (
    get_effective_role,
    get_effective_roles,
    pick_primary_role,
)
from backend.chronos_graphql.permission_middleware import (
    PermissionGuardMiddleware,
    extract_target_company_id,
)
from backend.chronos_graphql.query_permissions import (
    PUBLIC_QUERIES,
    QUERY_PERMISSION_MAPPING,
    QUERY_PERMISSION_PREFIXES,
    resolve_query_permission,
)
from backend.exceptions import PermissionDeniedException
from graphql import OperationType


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


class _Role:
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority


def test_pick_primary_role_prefers_highest_priority():
    roles = [_Role("employee", 20), _Role("admin", 90)]
    assert pick_primary_role(roles).name == "admin"


def test_pick_primary_role_handles_empty_list():
    assert pick_primary_role([]) is None


def test_pick_primary_role_handles_missing_priority():
    roles = [_Role("custom", None), _Role("employee", 20)]
    assert pick_primary_role(roles).name == "employee"


async def test_get_effective_roles_prefers_assignments():
    role = SimpleNamespace(name="manager", priority=50)
    assignments = MagicMock()
    assignments.scalars.return_value.unique.return_value = [role]
    db = MagicMock()
    db.execute = AsyncMock(return_value=assignments)

    assert await get_effective_roles(db, 1, 2) == [role]
    assert db.execute.await_count == 1


async def test_get_effective_roles_falls_back_to_legacy_role():
    role = SimpleNamespace(id=3, name="employee", priority=20)
    empty = MagicMock()
    empty.scalars.return_value.unique.return_value = []
    legacy = MagicMock()
    legacy.scalar_one_or_none.return_value = role
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[empty, legacy])

    assert await get_effective_roles(db, 1, 2) == [role]
    assert db.execute.await_count == 2


async def test_get_effective_role_returns_highest_priority():
    assignments = MagicMock()
    assignments.scalars.return_value.unique.return_value = [
        SimpleNamespace(name="employee", priority=20),
        SimpleNamespace(name="admin", priority=90),
    ]
    db = MagicMock()
    db.execute = AsyncMock(return_value=assignments)

    assert (await get_effective_role(db, 1, 2)).name == "admin"


def test_super_admin_permission_exists():
    assert "system:super_admin" in DEFAULT_PERMISSIONS


def test_only_super_admin_role_has_super_admin_permission():
    for name, data in DEFAULT_ROLES.items():
        if name == "super_admin":
            assert "system:super_admin" in data["permissions"]
        else:
            assert "system:super_admin" not in data["permissions"]


def test_ownership_registry_models_exist():
    from backend.database import models as db_models

    for model_name, owner_column in PermissionService.OWNERSHIP_MODELS.values():
        model = getattr(db_models, model_name)
        assert hasattr(model, owner_column), f"{model_name}.{owner_column}"


async def test_verify_ownership_unknown_resource_is_denied():
    service = PermissionService(MagicMock())

    assert await service._verify_ownership(1, 10, "unknown_resource") is False


def _query_field_names() -> set[str]:
    from backend.chronos_graphql.schema import schema

    query_type = schema._schema.query_type
    assert query_type is not None
    return set(query_type.fields.keys())


def test_every_query_has_a_permission():
    unmapped = sorted(
        field
        for field in _query_field_names()
        if field not in PUBLIC_QUERIES and resolve_query_permission(field) is None
    )
    assert unmapped == [], "Queries без permission: " + ", ".join(unmapped)


def test_query_mapping_targets_exist_in_catalog():
    missing = set(QUERY_PERMISSION_MAPPING.values()) - set(DEFAULT_PERMISSIONS)
    assert missing == set(), f"Липсващи permission-и: {sorted(missing)}"


def test_query_prefix_targets_exist_in_catalog():
    missing = {perm for _prefix, perm in QUERY_PERMISSION_PREFIXES} - set(
        DEFAULT_PERMISSIONS
    )
    assert missing == set(), f"Липсващи permission-и: {sorted(missing)}"


def test_resolve_query_permission_prefers_explicit_mapping():
    assert resolve_query_permission("invoices") == "accounting:read"


def test_public_query_has_no_permission():
    assert resolve_query_permission("me") is None


def _query_info(field_name: str, user=None, db=None):
    info = MagicMock()
    info.operation.operation = OperationType.QUERY
    info.field_name = field_name
    info.context = {"current_user": user, "db": db}
    return info


async def _next_resolver(*_args, **_kwargs):
    return "ok"


async def test_query_guard_allows_public_query():
    middleware = PermissionGuardMiddleware()

    result = await middleware.resolve(
        _next_resolver, None, _query_info("me"), [], {}
    )

    assert result == "ok"


async def test_query_guard_requires_authentication():
    middleware = PermissionGuardMiddleware()

    with pytest.raises(PermissionDeniedException):
        await middleware.resolve(
            _next_resolver, None, _query_info("users"), [], {}
        )


async def test_query_guard_is_log_only_by_default(monkeypatch):
    monkeypatch.setattr(
        PermissionService, "check_permission", AsyncMock(return_value=False)
    )
    middleware = PermissionGuardMiddleware()

    result = await middleware.resolve(
        _next_resolver,
        None,
        _query_info("users", user=SimpleNamespace(id=1, company_id=1), db=MagicMock()),
        [],
        {},
    )

    assert result == "ok"


async def test_query_guard_enforces_when_flag_enabled(monkeypatch):
    monkeypatch.setattr(
        PermissionService, "check_permission", AsyncMock(return_value=False)
    )
    monkeypatch.setattr(
        "backend.config.settings.RBAC_QUERY_ENFORCEMENT", True, raising=False
    )
    middleware = PermissionGuardMiddleware()

    with pytest.raises(PermissionDeniedException):
        await middleware.resolve(
            _next_resolver,
            None,
            _query_info(
                "users", user=SimpleNamespace(id=1, company_id=1), db=MagicMock()
            ),
            [],
            {},
        )


async def test_purge_old_audit_entries_deletes_and_commits(monkeypatch):
    from backend.jobs import audit_retention_job as job

    db = MagicMock()
    db.execute = AsyncMock(return_value=SimpleNamespace(rowcount=7))
    db.commit = AsyncMock()
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=db)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(job, "AsyncSessionLocal", MagicMock(return_value=session_cm))

    assert await job.purge_old_audit_entries() == 7
    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()


async def test_graphql_context_records_client_ip_and_user_agent(monkeypatch):
    from backend import main

    monkeypatch.setattr(main, "create_dataloaders", MagicMock(return_value={}))
    request = MagicMock()
    request.headers = {
        "cf-connecting-ip": "203.0.113.9",
        "user-agent": "pytest-agent",
    }
    db = MagicMock()

    context = await main.get_context(request=request, db=db, current_user=None)

    assert context["ip_address"] == "203.0.113.9"
    assert context["user_agent"] == "pytest-agent"
