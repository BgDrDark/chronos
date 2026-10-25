"""Auth hardening tests (audit 23.10, Phase 3)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import backend.crud  # noqa: F401  (import the package first: crud_legacy needs it)
import pytest
from backend import crud_legacy
from backend.auth.rbac_service import api_key_allows
from backend.auth.security import hash_password
from backend.exceptions import PermissionDeniedException


class _Scalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _Result:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _Scalars(self._items)


@pytest.mark.asyncio
async def test_verify_api_key_accepts_matching_key():
    raw = "abcdefgh12345678"
    candidate = MagicMock()
    candidate.hashed_key = hash_password(raw)
    candidate.is_active = True
    db = MagicMock()
    db.execute = AsyncMock(return_value=_Result([candidate]))
    db.commit = AsyncMock()

    result = await crud_legacy.verify_api_key(db, raw)

    assert result is candidate
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_api_key_rejects_wrong_key():
    candidate = MagicMock()
    candidate.hashed_key = hash_password("correct-horse-battery")
    db = MagicMock()
    db.execute = AsyncMock(return_value=_Result([candidate]))

    assert await crud_legacy.verify_api_key(db, "wrong-key-value") is None


@pytest.mark.asyncio
async def test_verify_api_key_rejects_short_key():
    db = MagicMock()

    assert await crud_legacy.verify_api_key(db, "short") is None


def test_api_key_without_scopes_allows_everything():
    assert api_key_allows(set(), "users:delete") is True


def test_api_key_wildcard_allows_everything():
    assert api_key_allows({"*"}, "users:delete") is True


def test_read_all_scope_allows_only_reads():
    assert api_key_allows({"read:all"}, "users:read") is True
    assert api_key_allows({"read:all"}, "users:read_own") is True
    assert api_key_allows({"read:all"}, "users:delete") is False


def test_exact_scope_allows_matching_permission():
    assert api_key_allows({"payroll:read"}, "payroll:read") is True
    assert api_key_allows({"payroll:read"}, "payroll:create") is False


def test_legacy_read_resource_scope_is_accepted():
    assert api_key_allows({"read:payroll"}, "payroll:read") is True
    assert api_key_allows({"read:payroll"}, "payroll:create") is False


class _Info:
    def __init__(self, field_name, operation, context):
        self.field_name = field_name
        self.operation = SimpleNamespace(operation=operation)
        self.context = context


async def _next_resolver(*_args, **_kwargs):
    return "ok"


def _context(scopes):
    request = SimpleNamespace(state=SimpleNamespace(api_key_permissions=scopes))
    return {
        "current_user": SimpleNamespace(id=1, company_id=1),
        "db": MagicMock(),
        "request": request,
    }


@pytest.mark.asyncio
async def test_api_key_scope_blocks_mutation_outside_scope(monkeypatch):
    from backend.auth.rbac_service import PermissionService
    from backend.chronos_graphql.permission_middleware import PermissionGuardMiddleware
    from graphql import OperationType

    monkeypatch.setattr(
        PermissionService, "check_permission", AsyncMock(return_value=True)
    )
    monkeypatch.setattr(
        PermissionService, "log_permission_decision", AsyncMock(return_value=None)
    )
    info = _Info("createUser", OperationType.MUTATION, _context({"read:all"}))

    with pytest.raises(PermissionDeniedException):
        await PermissionGuardMiddleware().resolve(_next_resolver, None, info, [], {})


@pytest.mark.asyncio
async def test_api_key_scope_allows_mutation_inside_scope(monkeypatch):
    from backend.auth.rbac_service import PermissionService
    from backend.chronos_graphql.permission_middleware import PermissionGuardMiddleware
    from graphql import OperationType

    monkeypatch.setattr(
        PermissionService, "check_permission", AsyncMock(return_value=True)
    )
    monkeypatch.setattr(
        PermissionService, "log_permission_decision", AsyncMock(return_value=None)
    )
    info = _Info("createUser", OperationType.MUTATION, _context({"users:create"}))

    assert (
        await PermissionGuardMiddleware().resolve(_next_resolver, None, info, [], {})
        == "ok"
    )


@pytest.mark.asyncio
async def test_jwt_session_has_no_api_key_scope_ceiling(monkeypatch):
    from backend.auth.rbac_service import PermissionService
    from backend.chronos_graphql.permission_middleware import PermissionGuardMiddleware
    from graphql import OperationType

    monkeypatch.setattr(
        PermissionService, "check_permission", AsyncMock(return_value=True)
    )
    monkeypatch.setattr(
        PermissionService, "log_permission_decision", AsyncMock(return_value=None)
    )
    context = _context(None)
    context["request"] = None
    info = _Info("createUser", OperationType.MUTATION, context)

    assert (
        await PermissionGuardMiddleware().resolve(_next_resolver, None, info, [], {})
        == "ok"
    )
