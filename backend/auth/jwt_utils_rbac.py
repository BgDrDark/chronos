from datetime import datetime, timedelta
from typing import Optional, Annotated, Tuple, Dict, Any, List
import uuid
import json
import base64

from authlib.jose import jwt, JoseError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Request, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend import crud, schemas
from backend.database.database import get_db
from backend.database.models import sofia_now
from backend.auth.rbac_service import PermissionService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Simple in-memory cache for auth keys to reduce DB load and avoid session conflicts
_AUTH_KEYS_CACHE = {}

async def create_tokens_with_permissions(
    db: AsyncSession, 
    user_id: int, 
    email: str, 
    ip_address: Optional[str] = None, 
    user_agent: Optional[str] = None
) -> Tuple[str, str]:
    """
    Creates a pair of Access and Refresh tokens with RBAC permissions.
    Saves the Refresh token JTI to the database (Whitelist).
    """
    key = await crud.get_active_auth_key(db)
    now = sofia_now()
    
    # Get user permissions and roles
    permission_service = PermissionService(db)
    user_permissions = await permission_service.get_user_permissions(user_id)
    user_roles = await permission_service.get_user_roles(user_id)
    
    # Get primary company
    primary_company_id = None
    if user_roles:
        primary_company_id = user_roles[0].get('company_id')
    
    # Access Token (Stateless, short-lived with RBAC data)
    access_jti = str(uuid.uuid4())
    access_payload = {
        "iss": "chronos-api",
        "sub": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "jti": access_jti,
        "type": "access",
        "uid": user_id,
        
        # RBAC data
        "permissions": list(user_permissions),
        "roles": user_roles,
        "company_id": primary_company_id,
        "permission_version": 1,  # For cache invalidation
    }
    header = {"alg": key.algorithm, "typ": "JWT", "kid": key.kid}
    access_token = jwt.encode(header, access_payload, key.secret).decode('utf-8')
    
    # Refresh Token (Stateful, long-lived)
    refresh_jti = str(uuid.uuid4())
    refresh_exp_dt = now + timedelta(days=7)
    refresh_payload = {
        "iss": "chronos-api",
        "sub": email,
        "iat": int(now.timestamp()),
        "exp": int(refresh_exp_dt.timestamp()),
        "jti": refresh_jti,
        "type": "refresh",
        "uid": user_id
    }
    refresh_token = jwt.encode(header, refresh_payload, key.secret).decode('utf-8')
    
    # Save session to DB
    await crud.create_user_session(
        db, 
        user_id=user_id, 
        refresh_token_jti=refresh_jti, 
        expires_at=refresh_exp_dt,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return access_token, refresh_token


async def verify_and_decode_token(db: AsyncSession, token: str) -> Optional[dict]:
    """
    Decodes a token using the key identified by 'kid' in the header.
    Validates algorithm and standard claims.
    """
    try:
        # Manually extract kid from header
        header_segment = token.split('.')[0]
        header_data = base64.urlsafe_b64decode(header_segment + "==").decode('utf-8')
        header = json.loads(header_data)
        
        kid = header.get("kid")
        if not kid:
            return None
            
        # Try cache first
        key_obj = _AUTH_KEYS_CACHE.get(kid)
        
        if not key_obj:
            # Retrieve the specific key from DB
            key_obj = await crud.get_auth_key_by_kid(db, kid)
            if not key_obj:
                return None
            # Store in cache
            _AUTH_KEYS_CACHE[kid] = key_obj
            
        # Decode and validate with strict options
        claims = jwt.decode(token, key_obj.secret)
        
        # Standard validation using Sofia time
        now_ts = int(sofia_now().timestamp())
        claims.validate(now=now_ts, leeway=0)
        
        # Custom validation: ensure issuer
        if claims.get("iss") != "chronos-api":
            return None
            
        return claims
    except Exception as e:
        import logging
        logging.error(f"Token verification failed: {str(e)}")
        return None


async def get_current_user_rbac(
    request: Request, 
    db: Annotated[AsyncSession, Depends(get_db)]
) -> schemas.UserWithPermissions:
    """Enhanced current user getter with RBAC data"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # --- 1. Try API Key Header (X-API-Key) ---
    api_key = request.headers.get("X-API-Key")
    if api_key:
        key_obj = await crud.verify_api_key(db, api_key)
        if key_obj:
            # Return the owner of the key with permissions
            user = await crud.get_user_by_id(db, key_obj.user_id)
            if user and user.is_active:
                permission_service = PermissionService(db)
                permissions = await permission_service.get_user_permissions(user.id, user.company_id)
                roles = await permission_service.get_user_roles(user.id)
                
                return schemas.UserWithPermissions(
                    **user.__dict__,
                    permissions=list(permissions),
                    roles=roles,
                    primary_company_id=user.company_id
                )
        raise credentials_exception

    # --- 2. Try JWT (Cookies or Bearer) ---
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
        
    # Ensure it's an access token
    if payload.get("type") != "access":
        raise credentials_exception
        
    email = payload.get("sub")
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
    
    # Get permissions and roles from token or database
    permissions = payload.get("permissions", [])
    roles = payload.get("roles", [])
    
    # If permissions are not in token (old token), get from database
    if not permissions:
        permission_service = PermissionService(db)
        permissions = await permission_service.get_user_permissions(user.id, user.company_id)
        roles = await permission_service.get_user_roles(user.id)
    
    return schemas.UserWithPermissions(
        **user.__dict__,
        permissions=permissions,
        roles=roles,
        primary_company_id=user.company_id
    )


async def get_current_user(
    request: Request, 
    db: Annotated[AsyncSession, Depends(get_db)]
) -> schemas.User:
    """Legacy current user getter for backward compatibility"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # --- 1. Try API Key Header (X-API-Key) ---
    api_key = request.headers.get("X-API-Key")
    if api_key:
        key_obj = await crud.verify_api_key(db, api_key)
        if key_obj:
            # Return the owner of the key
            user = await crud.get_user_by_id(db, key_obj.user_id)
            if user and user.is_active:
                return schemas.User.model_validate(user)
        raise credentials_exception

    # --- 2. Try JWT (Cookies or Bearer) ---
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
        
    # Ensure it's an access token
    if payload.get("type") != "access":
        raise credentials_exception
        
    email = payload.get("sub")
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
        
    return schemas.User.model_validate(user)


async def get_optional_current_user(
    request: Request, 
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Optional[schemas.User]:
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


async def get_optional_current_user_rbac(
    request: Request, 
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Optional[schemas.UserWithPermissions]:
    try:
        return await get_current_user_rbac(request, db)
    except HTTPException:
        return None


async def refresh_token_with_updated_permissions(
    db: AsyncSession, 
    old_refresh_token: str
) -> Tuple[str, str]:
    """Refresh access token with updated permissions"""
    # Verify refresh token
    payload = await verify_and_decode_token(db, old_refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("uid")
    email = payload.get("sub")
    
    # Get user
    user = await crud.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens with updated permissions
    if user_id is None or email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return await create_tokens_with_permissions(db, user_id, email)