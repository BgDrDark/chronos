"""Regression tests for RBAC escalation paths (audit 23.10, Phase 1)."""

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


async def test_query_is_not_permission_checked():
    middleware = PermissionGuardMiddleware()
    info = _info("users", current_user=None)
    info.operation.operation = OperationType.QUERY
    assert await middleware.resolve(_next_, None, info) == "executed"
