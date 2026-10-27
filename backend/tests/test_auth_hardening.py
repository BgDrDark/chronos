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


# --- Task 3.13: salted PIN hashes and password policy on creation ---


def test_pin_hash_roundtrip():
    from backend.utils.pin_utils import hash_pin, verify_pin

    stored = hash_pin("1234")

    assert stored.startswith("pbkdf2$")
    assert verify_pin("1234", stored) is True


def test_pin_hash_rejects_wrong_pin():
    from backend.utils.pin_utils import hash_pin, verify_pin

    assert verify_pin("9999", hash_pin("1234")) is False


def test_pin_hash_is_salted():
    from backend.utils.pin_utils import hash_pin

    assert hash_pin("1234") != hash_pin("1234")


def test_pin_verify_supports_legacy_sha256():
    import hashlib

    from backend.utils.pin_utils import verify_pin

    assert verify_pin("1234", hashlib.sha256(b"1234").hexdigest()) is True
    assert verify_pin("4321", hashlib.sha256(b"1234").hexdigest()) is False


@pytest.mark.asyncio
async def test_set_pin_code_stores_pbkdf2_hash(monkeypatch):
    from backend.crud.repositories.user_repo import UserRepository

    user = SimpleNamespace(
        id=1, pin_code=None, pin_encrypted=None, pin_sha256=None
    )
    repo = UserRepository()
    db = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    monkeypatch.setattr(repo, "get_by_id", AsyncMock(return_value=user))
    monkeypatch.setattr(
        "backend.utils.pin_utils.encrypt_pin", lambda pin: f"enc:{pin}"
    )

    await repo.set_pin_code(db, 1, "1234")

    assert user.pin_sha256.startswith("pbkdf2$")
    assert user.pin_encrypted == "enc:1234"


@pytest.mark.asyncio
async def test_create_user_validates_password_complexity(monkeypatch):
    from backend.crud.repositories.user_repo import UserRepository

    calls: list[str] = []

    async def fake_validate(db, password):
        calls.append(password)

    monkeypatch.setattr(
        "backend.auth.security.validate_password_complexity", fake_validate
    )
    repo = UserRepository()
    db = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    user_data = SimpleNamespace(
        email="new@example.com",
        password="Secret123!",
        model_dump=lambda **_: {},
    )

    await repo.create_user(db, user_data)

    assert calls == ["Secret123!"]


# --- Task 3.3: deploy requires an active access token ---


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FirstResult:
    """Result stub for ``res.scalars().first()``."""

    def __init__(self, value):
        self._value = value

    def scalars(self):
        return SimpleNamespace(first=lambda: self._value)


def _deploy_db(user, role="super_admin"):
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            _ScalarResult(user),
            _ScalarResult(SimpleNamespace(name=role)),
        ]
    )
    return db


@pytest.mark.asyncio
async def test_deploy_rejects_refresh_token(monkeypatch):
    from backend.routers import deploy as deploy_router

    monkeypatch.setattr(
        "backend.auth.jwt_utils.verify_and_decode_token",
        AsyncMock(return_value={"sub": "admin@example.com", "type": "refresh"}),
    )
    user = SimpleNamespace(
        id=1, email="admin@example.com", is_active=True, role_id=1
    )

    with pytest.raises(HTTPException) as exc:
        await deploy_router._verify_super_admin(_deploy_db(user), "refresh-token")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Access token required"


@pytest.mark.asyncio
async def test_deploy_rejects_inactive_user(monkeypatch):
    from backend.routers import deploy as deploy_router

    monkeypatch.setattr(
        "backend.auth.jwt_utils.verify_and_decode_token",
        AsyncMock(return_value={"sub": "admin@example.com", "type": "access"}),
    )
    user = SimpleNamespace(
        id=1, email="admin@example.com", is_active=False, role_id=1
    )

    with pytest.raises(HTTPException) as exc:
        await deploy_router._verify_super_admin(_deploy_db(user), "access-token")

    assert exc.value.status_code == 403
    assert exc.value.detail == "User inactive"


@pytest.mark.asyncio
async def test_deploy_accepts_active_super_admin(monkeypatch):
    from backend.routers import deploy as deploy_router

    monkeypatch.setattr(
        "backend.auth.jwt_utils.verify_and_decode_token",
        AsyncMock(return_value={"sub": "admin@example.com", "type": "access"}),
    )
    user = SimpleNamespace(
        id=1, email="admin@example.com", is_active=True, role_id=1
    )

    await deploy_router._verify_super_admin(_deploy_db(user), "access-token")


@pytest.mark.asyncio
async def test_deploy_key_is_compared_in_constant_time(monkeypatch):
    import hmac as real_hmac

    from backend.routers import deploy as deploy_router

    monkeypatch.setattr(deploy_router.limiter, "enabled", False)
    monkeypatch.setattr(
        deploy_router,
        "settings",
        SimpleNamespace(get_deploy_key=lambda: "secret-key", DEPLOY_API_KEY="secret-key"),
    )
    calls: list[tuple[str, str]] = []
    original = real_hmac.compare_digest

    def spy(a, b):
        calls.append((a, b))
        return original(a, b)

    monkeypatch.setattr(deploy_router.hmac, "compare_digest", spy)
    request = SimpleNamespace(
        headers={"Authorization": "UpdateKey secret-key"}, cookies={}
    )

    # Deployment itself is not reached: the request fails later on missing config.
    with pytest.raises(HTTPException):
        await deploy_router.deploy_update(request, SimpleNamespace(version=None), MagicMock())

    assert calls == [("secret-key", "secret-key")]


def test_deploy_key_is_not_logged_when_generated(monkeypatch, tmp_path, caplog):
    from backend import config

    monkeypatch.delenv("DEPLOY_API_KEY", raising=False)
    monkeypatch.setenv("UPDATE_KEY_FILE", str(tmp_path / "missing.key"))

    with caplog.at_level("WARNING"):
        key = config.settings.get_deploy_key()

    assert len(key) == 64
    assert key[:8] not in caplog.text


# --- Task 3.12: operational endpoints require admin auth ---


def test_operational_deploy_endpoints_require_admin_auth():
    from backend.routers import deploy as deploy_router

    paths = ["/webhook/deploy-status", "/webhook/deploy-log", "/webhook/db-health"]
    guarded = {}
    for route in deploy_router.router.routes:
        path = getattr(route, "path", None)
        if path in paths:
            guarded[path] = any(
                getattr(dep.dependency, "__name__", "") == "require_admin_user"
                for dep in route.dependencies
            )

    assert guarded == dict.fromkeys(paths, True)


def test_public_health_endpoint_stays_open():
    from backend.routers import deploy as deploy_router

    health = next(
        route
        for route in deploy_router.router.routes
        if getattr(route, "path", None) == "/webhook/health"
    )

    assert health.dependencies == []


@pytest.mark.asyncio
async def test_require_admin_user_accepts_admin(monkeypatch):
    from backend.auth import dependencies

    user = SimpleNamespace(role=SimpleNamespace(name="super_admin"))
    monkeypatch.setattr(
        dependencies.jwt_utils, "get_current_user", AsyncMock(return_value=user)
    )

    assert await dependencies.require_admin_user(MagicMock(), MagicMock()) is user


@pytest.mark.asyncio
async def test_require_admin_user_rejects_employee(monkeypatch):
    from backend.auth import dependencies

    user = SimpleNamespace(role=SimpleNamespace(name="employee"))
    monkeypatch.setattr(
        dependencies.jwt_utils, "get_current_user", AsyncMock(return_value=user)
    )

    with pytest.raises(HTTPException) as exc:
        await dependencies.require_admin_user(MagicMock(), MagicMock())

    assert exc.value.status_code == 403
    assert exc.value.detail == "Administrator access required"


@pytest.mark.asyncio
async def test_require_admin_user_rejects_user_without_role(monkeypatch):
    from backend.auth import dependencies

    monkeypatch.setattr(
        dependencies.jwt_utils,
        "get_current_user",
        AsyncMock(return_value=SimpleNamespace(role=None)),
    )

    with pytest.raises(HTTPException) as exc:
        await dependencies.require_admin_user(MagicMock(), MagicMock())

    assert exc.value.status_code == 403


# --- Task 3.9: GraphQL requires a CSRF token ---


def test_graphql_requires_csrf_token():
    from backend.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post("/graphql", json={"query": "{ me { id } }"})

    assert response.status_code == 403


def test_graphql_accepts_matching_csrf_token():
    import re

    from backend.config import settings
    from backend.main import app
    from fastapi.testclient import TestClient
    from itsdangerous.url_safe import URLSafeSerializer

    client = TestClient(app)
    # A safe request issues the double-submit cookie.
    client.get("/webhook/health")
    token = client.cookies.get("csrf_token")
    assert token

    # A forged header must be rejected before the query is executed.
    forged = URLSafeSerializer(settings.CSRF_SECRET_KEY, "csrftoken").dumps("forged")
    response = client.post(
        "/graphql",
        json={"query": "{ __typename }"},
        headers={"X-CSRFToken": forged},
    )

    assert response.status_code == 403
    assert re.search("CSRF", response.text)


@pytest.mark.asyncio
async def test_csrf_token_endpoint_echoes_the_cookie():
    from backend.routers import auth as auth_router

    request = SimpleNamespace(cookies={"csrf_token": "signed-token"})

    assert await auth_router.read_csrf_token(request) == {"csrf_token": "signed-token"}


def test_default_cors_origins_are_https_only():
    from backend.main import DEFAULT_CORS_ORIGINS

    assert DEFAULT_CORS_ORIGINS == [
        "https://chronos.oblak24.org",
        "https://dev.oblak24.org",
    ]


# --- Task 3.10: WebAuthn challenges are bound to a user ---


@pytest.mark.asyncio
async def test_webauthn_login_options_require_email(monkeypatch):
    from backend.routers import webauthn as webauthn_router

    monkeypatch.setattr(webauthn_router.limiter, "enabled", False)

    with pytest.raises(HTTPException) as exc:
        await webauthn_router.get_login_options(MagicMock(), {}, MagicMock())

    assert exc.value.status_code == 400
    assert exc.value.detail == "Email is required"


@pytest.mark.asyncio
async def test_webauthn_login_options_store_the_user_id(monkeypatch):
    from backend.routers import webauthn as webauthn_router

    monkeypatch.setattr(webauthn_router.limiter, "enabled", False)
    monkeypatch.setattr(
        webauthn_router,
        "generate_authentication_options",
        MagicMock(return_value=SimpleNamespace(challenge=b"\x00\x00\x00")),
    )
    monkeypatch.setattr(webauthn_router, "options_to_json", MagicMock(return_value="{}"))
    monkeypatch.setattr(webauthn_router, "bytes_to_base64url", lambda _: "AAAA")
    user = SimpleNamespace(id=7, email="user@example.com")
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[_FirstResult(user), _Result([]), _FirstResult(None)]
    )
    db.commit = AsyncMock()

    await webauthn_router.get_login_options(MagicMock(), {"email": user.email}, db)

    created = db.add.call_args[0][0]
    assert created.user_id == 7
    assert created.challenge == "AAAA"


@pytest.mark.asyncio
async def test_webauthn_login_rejects_credential_of_another_user(monkeypatch):
    from backend.routers import webauthn as webauthn_router

    monkeypatch.setattr(webauthn_router.limiter, "enabled", False)
    challenge = SimpleNamespace(user_id=2, challenge="AAAA")
    credential = SimpleNamespace(user_id=1, credential_id=b"id")
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[_FirstResult(challenge), _FirstResult(credential)]
    )

    with pytest.raises(HTTPException) as exc:
        await webauthn_router.verify_login(MagicMock(), {"id": "AAAA"}, db)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Credential does not belong to this challenge"


@pytest.mark.asyncio
async def test_webauthn_login_rejects_inactive_user(monkeypatch):
    from backend.routers import webauthn as webauthn_router

    monkeypatch.setattr(webauthn_router.limiter, "enabled", False)
    challenge = SimpleNamespace(user_id=1, challenge="AAAA")
    credential = SimpleNamespace(
        user_id=1, credential_id=b"id", sign_count=0, public_key=b"key"
    )
    inactive = SimpleNamespace(id=1, email="user@example.com", is_active=False)
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            _FirstResult(challenge),
            _FirstResult(credential),
            _FirstResult(inactive),
        ]
    )
    monkeypatch.setattr(
        webauthn_router,
        "verify_authentication_response",
        MagicMock(return_value=SimpleNamespace(new_sign_count=1)),
    )

    with pytest.raises(HTTPException) as exc:
        await webauthn_router.verify_login(MagicMock(), {"id": "AAAA"}, db)

    assert exc.value.status_code == 403
    assert exc.value.detail == "User inactive"


# --- Task 3.11: signed Google OAuth state ---


def test_google_oauth_state_roundtrip():
    from backend.routers.google import build_oauth_state, read_oauth_state

    assert read_oauth_state(build_oauth_state(42)) == 42


def test_google_oauth_state_rejects_legacy_value():
    from backend.routers.google import read_oauth_state

    with pytest.raises(ValueError):
        read_oauth_state("user_42")


def test_google_oauth_state_rejects_tampered_value():
    from backend.routers.google import build_oauth_state, read_oauth_state

    state = build_oauth_state(42)

    with pytest.raises(ValueError):
        read_oauth_state(state[:-4] + "AAAA")


@pytest.mark.asyncio
async def test_google_init_signs_the_state(monkeypatch):
    from backend.routers import google as google_router

    captured = {}

    async def fake_get_auth_url(user_id, state=None):
        captured["user_id"] = user_id
        captured["state"] = state
        return "https://accounts.google.com/o/oauth2/auth"

    monkeypatch.setattr(
        google_router.google_calendar_service, "get_auth_url", fake_get_auth_url
    )

    await google_router.google_login_init(
        MagicMock(), SimpleNamespace(id=42), MagicMock()
    )

    assert captured["user_id"] == 42
    assert google_router.read_oauth_state(captured["state"]) == 42


@pytest.mark.asyncio
async def test_google_legacy_login_no_longer_accepts_query_tokens():
    from backend.routers import google as google_router

    request = MagicMock()
    request.cookies = {}

    with pytest.raises(HTTPException) as exc:
        await google_router.google_login(request, MagicMock())

    assert exc.value.status_code == 401
