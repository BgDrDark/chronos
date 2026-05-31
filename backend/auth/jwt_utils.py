import base64
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from authlib.jose import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend import crud, schemas
from backend.auth.limiter import api_key_limiter
from backend.config import settings
from backend.database.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def create_tokens(db: AsyncSession, user_id: int, email: str, ip_address: str = None, user_agent: str = None) -> tuple[str, str]:
    """Creates a pair of Access and Refresh tokens.
    Saves the Refresh token JTI to the database (Whitelist).
    JWT timestamps are always UTC per RFC 7519.
    DB datetimes are naive (TIMESTAMP WITHOUT TIME ZONE).
    """
    key = await crud.get_active_auth_key(db)
    now_utc = datetime.now(UTC)

    # Access Token (Stateless, short-lived)
    access_jti = str(uuid.uuid4())
    access_payload = {
        "iss": "chronos-api",
        "sub": email,
        "iat": int(now_utc.timestamp()),
        "exp": int((now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "jti": access_jti,
        "type": "access",
        "uid": user_id,
    }
    header = {"alg": key.algorithm, "typ": "JWT", "kid": key.kid}
    access_token = jwt.encode(header, access_payload, key.secret).decode("utf-8")

    # Refresh Token (Stateful, long-lived)
    refresh_jti = str(uuid.uuid4())
    refresh_exp_utc = now_utc + timedelta(days=7)
    refresh_payload = {
        "iss": "chronos-api",
        "sub": email,
        "iat": int(now_utc.timestamp()),
        "exp": int(refresh_exp_utc.timestamp()),
        "jti": refresh_jti,
        "type": "refresh",
        "uid": user_id,
    }
    refresh_token = jwt.encode(header, refresh_payload, key.secret).decode("utf-8")

    # Save session to DB - strip timezone info for TIMESTAMP WITHOUT TIME ZONE
    await crud.create_user_session(
        db,
        user_id=user_id,
        refresh_token_jti=refresh_jti,
        expires_at=refresh_exp_utc.replace(tzinfo=None),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return access_token, refresh_token

# Simple in-memory cache for auth keys to reduce DB load and avoid session conflicts
# Cache stores dicts: {"kid": ..., "secret": ..., "algorithm": ...}
_AUTH_KEYS_CACHE: dict[str, dict] = {}

ALLOWED_ALGORITHMS = {"HS256", "HS384", "HS512", "RS256", "ES256"}

async def verify_and_decode_token(db: AsyncSession, token: str) -> dict | None:
    """Decodes a token using the key identified by 'kid' in the header.
    Validates algorithm and standard claims with algorithm pinning.
    """
    try:
        # Manually extract kid and alg from header
        header_segment = token.split(".", maxsplit=1)[0]
        header_data = base64.urlsafe_b64decode(header_segment + "==").decode("utf-8")
        header = json.loads(header_data)

        kid = header.get("kid")
        if not kid:
            logging.error("Token missing 'kid' in header")
            return None

        token_alg = header.get("alg")
        if not token_alg:
            logging.error("Token missing 'alg' in header")
            return None

        # Algorithm pinning - reject any algorithm not explicitly allowed
        if token_alg not in ALLOWED_ALGORITHMS:
            logging.error(f"Algorithm not allowed: {token_alg}")
            return None

        # Try cache first
        key_data = _AUTH_KEYS_CACHE.get(kid)

        if not key_data:
            # Retrieve the specific key from DB
            key_obj = await crud.get_auth_key_by_kid(db, kid)
            if not key_obj:
                logging.error(f"Auth key not found for kid: {kid}")
                return None
            # Cache the values directly to avoid DetachedInstanceError
            key_data = {
                "kid": key_obj.kid,
                "secret": key_obj.secret,
                "algorithm": key_obj.algorithm,
            }
            _AUTH_KEYS_CACHE[kid] = key_data

        # Verify algorithm matches the key's algorithm
        if token_alg != key_data["algorithm"]:
            logging.error(f"Algorithm mismatch: expected {key_data['algorithm']}, got {token_alg}")
            return None

        # Decode and validate with strict options
        claims = jwt.decode(token, key_data["secret"])

        # Standard validation with 10s leeway for clock skew
        claims.validate(leeway=10)

        # Custom validation: ensure issuer
        if claims.get("iss") != "chronos-api":
            logging.error(f"Token issuer mismatch: {claims.get('iss')}")
            return None

        return claims
    except Exception as e:
        logging.exception(f"Token verification failed: {type(e).__name__}: {e!s}")
        return None

async def get_current_user(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)],
) -> schemas.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None

    # --- 1. Try API Key Header (X-API-Key) ---
    api_key = request.headers.get("X-API-Key")
    if api_key:
        if not api_key_limiter.is_allowed(api_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API key rate limit exceeded. Try again later.",
            )
        key_obj = await crud.verify_api_key(db, api_key)
        if key_obj:
            user = await crud.get_user_by_id(db, key_obj.user_id)
            if user and user.is_active:
                return schemas.User.model_validate(user)
        raise credentials_exception

    # --- 2. Try JWT from cookies or Bearer ---
    # Query parameter tokens are a security risk - removed.
    # Use Authorization header or cookies instead.
    token = request.cookies.get("access_token")
    if not token:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]

    if not token:
        raise credentials_exception

    payload = await verify_and_decode_token(db, token)
    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = await crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Check maintenance mode - block non-admin users
    from sqlalchemy import select as sa_select

    from backend.database.models import MaintenanceSettings, Role
    maint_result = await db.execute(sa_select(MaintenanceSettings).order_by(MaintenanceSettings.id.desc()).limit(1))
    maint_setting = maint_result.scalar_one_or_none()
    if maint_setting and maint_setting.enabled:
        role_result = await db.execute(sa_select(Role).where(Role.id == user.role_id))
        role = role_result.scalar_one_or_none()
        if not role or role.name not in ["admin", "super_admin"]:
            reason = maint_setting.reason or "Системата е в режим поддръжка"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"MAINTENANCE_MODE: {reason}",
            )

    return schemas.User.model_validate(user)

async def get_optional_current_user(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)],
) -> schemas.User | None:
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
