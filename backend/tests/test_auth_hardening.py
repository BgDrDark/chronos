"""Auth hardening tests (audit 23.10, Phase 3)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import backend.crud  # noqa: F401  (import the package first: crud_legacy needs it)
import pytest
from backend import crud_legacy
from backend.auth.rbac_service import api_key_allows
from backend.auth.security import hash_password
from backend.exceptions import PermissionDeniedException
from fastapi import HTTPException


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


class _Client:
    def __init__(self, host):
        self.host = host


class _Request:
    def __init__(self, host, headers):
        self.client = _Client(host)
        self.headers = headers


def test_client_ip_ignores_forwarded_header_from_untrusted_peer(monkeypatch):
    from backend.auth.security import get_client_ip
    from backend.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_IPS", "10.0.0.1")
    request = _Request("203.0.113.9", {"x-forwarded-for": "1.2.3.4"})
    assert get_client_ip(request) == "203.0.113.9"


def test_client_ip_uses_forwarded_header_from_trusted_peer(monkeypatch):
    from backend.auth.security import get_client_ip
    from backend.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_IPS", "10.0.0.1")
    request = _Request("10.0.0.1", {"x-forwarded-for": "1.2.3.4, 10.0.0.1"})
    assert get_client_ip(request) == "1.2.3.4"


def test_client_ip_falls_back_to_peer(monkeypatch):
    from backend.auth.security import get_client_ip
    from backend.config import settings

    monkeypatch.setattr(settings, "TRUSTED_PROXY_IPS", "")
    request = _Request("203.0.113.9", {})
    assert get_client_ip(request) == "203.0.113.9"


# --- Task 3.2: token version, forced password change, auth key state ---


def _sign_token(payload: dict, secret: str, kid: str = "kid-1") -> str:
    from authlib.jose import jwt as authlib_jwt

    header = {"alg": "HS256", "typ": "JWT", "kid": kid}
    return authlib_jwt.encode(header, payload, secret).decode("utf-8")


def test_token_version_matches_helper():
    from backend.auth.jwt_utils import token_version_matches

    assert token_version_matches({"ver": 3}, SimpleNamespace(token_version=3)) is True
    assert token_version_matches({"ver": 2}, SimpleNamespace(token_version=3)) is False
    assert token_version_matches({}, SimpleNamespace(token_version=1)) is True
    assert token_version_matches({}, SimpleNamespace(token_version=None)) is True


def test_create_tokens_embeds_user_token_version(monkeypatch):
    from authlib.jose import jwt as authlib_jwt
    from backend.auth import jwt_utils

    secret = "test-secret-for-token-version-tests"
    monkeypatch.setattr(
        jwt_utils.crud,
        "get_active_auth_key",
        AsyncMock(
            return_value=SimpleNamespace(kid="kid-1", secret=secret, algorithm="HS256")
        ),
    )
    monkeypatch.setattr(
        jwt_utils.crud,
        "get_user_by_id",
        AsyncMock(return_value=SimpleNamespace(token_version=7)),
    )
    monkeypatch.setattr(
        jwt_utils.crud, "create_user_session", AsyncMock(return_value=None)
    )

    import asyncio

    access, refresh = asyncio.run(
        jwt_utils.create_tokens(MagicMock(), 1, "user@example.com")
    )

    assert authlib_jwt.decode(access, secret)["ver"] == 7
    assert authlib_jwt.decode(refresh, secret)["ver"] == 7


def test_expired_auth_key_is_rejected(monkeypatch):
    import asyncio

    from backend.auth import jwt_utils

    secret = "expired-key-secret"
    token = _sign_token(
        {"iss": "chronos-api", "sub": "a@b.c", "exp": 4102444800}, secret
    )
    monkeypatch.setitem(
        jwt_utils._AUTH_KEYS_CACHE,
        "kid-1",
        {"kid": "kid-1", "secret": secret, "algorithm": "HS256", "state": "expired"},
    )

    assert asyncio.run(jwt_utils.verify_and_decode_token(MagicMock(), token)) is None


def test_legacy_auth_key_still_verifies(monkeypatch):
    import asyncio

    from backend.auth import jwt_utils

    secret = "legacy-key-secret"
    token = _sign_token(
        {"iss": "chronos-api", "sub": "a@b.c", "exp": 4102444800}, secret
    )
    monkeypatch.setitem(
        jwt_utils._AUTH_KEYS_CACHE,
        "kid-1",
        {"kid": "kid-1", "secret": secret, "algorithm": "HS256", "state": "legacy"},
    )

    claims = asyncio.run(jwt_utils.verify_and_decode_token(MagicMock(), token))

    assert claims is not None and claims["sub"] == "a@b.c"


@pytest.mark.asyncio
async def test_mutation_blocked_while_password_change_required(monkeypatch):
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
    context["current_user"] = SimpleNamespace(
        id=1, company_id=1, password_force_change=True
    )
    info = _Info("createUser", OperationType.MUTATION, context)

    with pytest.raises(PermissionDeniedException):
        await PermissionGuardMiddleware().resolve(_next_resolver, None, info, [], {})


@pytest.mark.asyncio
async def test_change_password_allowed_while_password_change_required():
    from backend.chronos_graphql.permission_middleware import PermissionGuardMiddleware
    from graphql import OperationType

    context = _context(None)
    context["current_user"] = SimpleNamespace(
        id=1, company_id=1, password_force_change=True
    )
    info = _Info("changePassword", OperationType.MUTATION, context)

    assert (
        await PermissionGuardMiddleware().resolve(_next_resolver, None, info, [], {})
        == "ok"
    )


# --- Task 3.6: refresh token reuse detection ---


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_session_family(monkeypatch):
    from backend.routers import auth as auth_router

    invalidate = AsyncMock(return_value=None)
    user = SimpleNamespace(token_version=3)
    db = MagicMock()
    db.commit = AsyncMock()
    monkeypatch.setattr(auth_router.crud, "invalidate_all_user_sessions", invalidate)
    monkeypatch.setattr(
        auth_router.crud, "get_user_by_id", AsyncMock(return_value=user)
    )

    await auth_router._revoke_token_family(db, {"uid": 5, "jti": "j-1"})

    invalidate.assert_awaited_once_with(db, 5)
    assert user.token_version == 4
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_reuse_without_uid_is_a_noop(monkeypatch):
    from backend.routers import auth as auth_router

    invalidate = AsyncMock(return_value=None)
    monkeypatch.setattr(auth_router.crud, "invalidate_all_user_sessions", invalidate)
    db = MagicMock()
    db.commit = AsyncMock()

    await auth_router._revoke_token_family(db, {})

    invalidate.assert_not_awaited()
    db.commit.assert_not_awaited()


# --- Task 3.7: reset token binding and unified login errors ---


def test_password_reset_token_is_bound_to_current_password():
    from backend.routers.auth import (
        build_password_reset_token,
        read_password_reset_token,
    )

    user = SimpleNamespace(email="user@example.com", hashed_password="h" * 60)

    payload = read_password_reset_token(build_password_reset_token(user))

    assert payload["email"] == "user@example.com"
    assert payload["pwd"] == "h" * 16


def test_legacy_password_reset_token_is_rejected():
    from backend.routers.auth import (
        RESET_SALT,
        pwd_reset_serializer,
        read_password_reset_token,
    )

    legacy = pwd_reset_serializer.dumps("user@example.com", salt=RESET_SALT)

    with pytest.raises(ValueError):
        read_password_reset_token(legacy)


@pytest.mark.asyncio
async def test_login_for_unknown_user_returns_generic_401(monkeypatch):
    from backend.routers import auth as auth_router

    monkeypatch.setattr(auth_router.limiter, "enabled", False)
    monkeypatch.setattr(
        auth_router.crud,
        "get_user_by_email_or_username",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_router.login_for_access_token(
            MagicMock(),
            SimpleNamespace(username="nobody", password="whatever"),
            MagicMock(),
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Incorrect username or password"


@pytest.mark.asyncio
async def test_login_lockout_returns_429(monkeypatch):
    from datetime import timedelta

    from backend.database.models import sofia_now
    from backend.routers import auth as auth_router

    monkeypatch.setattr(auth_router.limiter, "enabled", False)
    user = SimpleNamespace(
        id=1,
        locked_until=sofia_now() + timedelta(minutes=10),
        hashed_password="x",
        is_active=True,
    )
    monkeypatch.setattr(
        auth_router.crud,
        "get_user_by_email_or_username",
        AsyncMock(return_value=user),
    )

    with pytest.raises(HTTPException) as exc:
        await auth_router.login_for_access_token(
            MagicMock(),
            SimpleNamespace(username="someone", password="whatever"),
            MagicMock(),
        )

    assert exc.value.status_code == 429


# --- Task 3.8: self-registration is closed by default ---


def test_registration_disabled_by_default():
    from backend.config import settings

    assert settings.ALLOW_SELF_REGISTRATION is False


@pytest.mark.asyncio
async def test_register_endpoint_refuses_when_disabled(monkeypatch):
    from backend.routers import auth as auth_router

    monkeypatch.setattr(auth_router.limiter, "enabled", False)

    with pytest.raises(HTTPException) as exc:
        await auth_router.register_user(
            MagicMock(), SimpleNamespace(email="new@example.com"), MagicMock()
        )

    assert exc.value.status_code == 403


# --- Task 3.4: kiosk admin verification is rate limited ---


def test_verify_admin_kiosk_is_rate_limited():
    from backend.routers import auth as auth_router

    # slowapi wraps the endpoint; the wrapper keeps the original name.
    assert auth_router.verify_admin_kiosk.__name__ == "verify_admin_kiosk"
    assert getattr(auth_router.verify_admin_kiosk, "__wrapped__", None) is not None


@pytest.mark.asyncio
async def test_verify_admin_kiosk_sleeps_on_wrong_password(monkeypatch):
    import asyncio as real_asyncio

    from backend.routers import auth as auth_router

    monkeypatch.setattr(auth_router.limiter, "enabled", False)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda *_: False)
    monkeypatch.setattr(
        auth_router.crud,
        "get_user_by_email",
        AsyncMock(
            return_value=SimpleNamespace(
                role=SimpleNamespace(name="admin"), hashed_password="x"
            )
        ),
    )
    calls: list[float] = []

    async def fake_sleep(seconds):
        calls.append(seconds)

    monkeypatch.setattr(real_asyncio, "sleep", fake_sleep)

    with pytest.raises(HTTPException) as exc:
        await auth_router.verify_admin_kiosk(
            MagicMock(), {"email": "a@b.c", "password": "wrong"}, MagicMock()
        )

    assert exc.value.status_code == 401
    assert calls == [0.5]
