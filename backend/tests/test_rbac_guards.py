"""Regression tests for RBAC escalation paths (audit 23.10, Phase 1)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from backend.chronos_graphql.permission_middleware import PermissionGuardMiddleware
from backend.exceptions import PermissionDeniedException
from graphql import OperationType


def _info(field_name: str, current_user=..., context: dict | None = None):
    info = MagicMock()
    info.operation.operation = OperationType.MUTATION
    info.field_name = field_name
    if context is None:
        context = {
            "current_user": current_user,
            "db": MagicMock(),
            "ip_address": "127.0.0.1",
        }
    info.context = context
    return info


async def _next_(root, info, *args, **kwargs):
    return "executed"


@pytest.mark.parametrize("field_name", ["someUnmappedMutation", "anotherUnknownField"])
async def test_unmapped_mutation_is_denied(field_name):
    middleware = PermissionGuardMiddleware()
    with pytest.raises(PermissionDeniedException):
        await middleware.resolve(_next_, None, _info(field_name))


async def test_unauthenticated_mapped_mutation_is_denied():
    middleware = PermissionGuardMiddleware()
    with pytest.raises(PermissionDeniedException):
        await middleware.resolve(_next_, None, _info("createUser", current_user=None))


async def test_auth_only_mutation_is_allowed_for_authenticated_user():
    middleware = PermissionGuardMiddleware()
    result = await middleware.resolve(_next_, None, _info("changePassword"))
    assert result == "executed"


async def test_public_query_skips_permission_check():
    middleware = PermissionGuardMiddleware()
    info = _info("me", current_user=None)
    info.operation.operation = OperationType.QUERY
    assert await middleware.resolve(_next_, None, info) == "executed"


async def test_private_query_requires_authentication():
    middleware = PermissionGuardMiddleware()
    info = _info("users", current_user=None)
    info.operation.operation = OperationType.QUERY
    with pytest.raises(PermissionDeniedException):
        await middleware.resolve(_next_, None, info)


class _FakePermissionService:
    """Stub for the middleware tests; no DB access."""

    permissions: set[str] = set()

    def __init__(self, db):
        self.db = db

    async def get_user_permissions(self, user_id, company_id=None):
        return set(self.permissions)

    async def check_permission(
        self, user_id, permission, company_id=None, resource_id=None
    ):
        return permission in self.permissions

    async def log_permission_decision(self, **kwargs):
        return None


def _employee():
    return SimpleNamespace(
        id=7, company_id=1, role=SimpleNamespace(name="employee")
    )


async def test_clock_out_allowed_with_update_own(monkeypatch):
    class Fake(_FakePermissionService):
        permissions = {"timelogs:update_own"}

    monkeypatch.setattr(
        "backend.chronos_graphql.permission_middleware.PermissionService", Fake
    )
    middleware = PermissionGuardMiddleware()

    result = await middleware.resolve(
        _next_, None, _info("clockOut", current_user=_employee())
    )

    assert result == "executed"


async def test_clock_out_denied_with_base_permission_only(monkeypatch):
    class Fake(_FakePermissionService):
        permissions = {"timelogs:update"}

    monkeypatch.setattr(
        "backend.chronos_graphql.permission_middleware.PermissionService", Fake
    )
    middleware = PermissionGuardMiddleware()

    with pytest.raises(PermissionDeniedException):
        await middleware.resolve(
            _next_, None, _info("clockOut", current_user=_employee())
        )


async def test_clock_in_allowed_with_create_own(monkeypatch):
    class Fake(_FakePermissionService):
        permissions = {"timelogs:create_own"}

    monkeypatch.setattr(
        "backend.chronos_graphql.permission_middleware.PermissionService", Fake
    )
    middleware = PermissionGuardMiddleware()

    result = await middleware.resolve(
        _next_, None, _info("clockIn", current_user=_employee())
    )

    assert result == "executed"


async def test_clock_in_denied_with_base_permission_only(monkeypatch):
    class Fake(_FakePermissionService):
        permissions = {"timelogs:create"}

    monkeypatch.setattr(
        "backend.chronos_graphql.permission_middleware.PermissionService", Fake
    )
    middleware = PermissionGuardMiddleware()

    with pytest.raises(PermissionDeniedException):
        await middleware.resolve(
            _next_, None, _info("clockIn", current_user=_employee())
        )
