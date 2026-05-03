from datetime import timedelta
from typing import Annotated, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from itsdangerous import URLSafeTimedSerializer

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend import crud, schemas
from backend.auth import security, jwt_utils
from backend.auth.security import validate_password_complexity
from backend.database.database import get_db
from backend.database.models import User
from backend.auth.qr_utils import get_dynamic_qr_token, generate_qr_secret

from backend.auth.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


# Serializer for password reset tokens
pwd_reset_serializer = URLSafeTimedSerializer(settings.JWT_SECRET_KEY)

# Mail configuration
mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME or "",
    MAIL_PASSWORD=settings.MAIL_PASSWORD or "",
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=True
)

@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = await crud.create_user(db=db, user=user)
    return new_user

@router.post("/token", response_model=schemas.LoginResponse)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from backend.database.models import sofia_now
    
    user = await crud.get_user_by_email_or_username(db, form_data.username)
    
    # 1. Check if user exists
    if not user:
        # Avoid timing attacks by simulating work? 
        # For simplicity, just return error.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check Lockout
    if user.locked_until:
        if user.locked_until > sofia_now():
            remaining = (user.locked_until - sofia_now()).seconds // 60
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Акаунтът е временно заключен поради твърде много неуспешни опити. Опитайте отново след {remaining + 1} минути."
            )
        else:
            # Lock expired, reset automatically (lazy reset)
            await crud.reset_login_attempts(db, user.id)

    # 3. Check Password
    if not security.verify_password(form_data.password, user.hashed_password):
        await crud.increment_login_attempts(db, user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. Success - Reset attempts
    await crud.reset_login_attempts(db, user.id)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Get metadata using helper for real IP
    ip_address = security.get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    # Create tokens and session
    access_token, refresh_token = await jwt_utils.create_tokens(
        db, user.id, user.email, ip_address=ip_address, user_agent=user_agent
    )
    
    # Update last login
    await crud.update_last_login(db, user.id)
    
    response_content = {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "password_force_change": user.password_force_change # Include the flag
    }

    response = JSONResponse(content=response_content)
    
    # Set Access Token Cookie - HttpOnly, Secure, None
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
        samesite="none" if settings.COOKIE_SECURE else "lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    # Set Refresh Token Cookie - HttpOnly, Secure, None
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7 * 24 * 3600, # 7 days
        samesite="none" if settings.COOKIE_SECURE else "lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return response

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    payload = await jwt_utils.verify_and_decode_token(db, refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    jti = payload.get("jti")
    session = await crud.get_user_session_by_jti(db, jti)
    if not session or not session.is_active:
        raise HTTPException(status_code=401, detail="Session invalidated or not found")
        
    # Invalidate OLD session (Rotation)
    await crud.invalidate_user_session(db, jti)
    
    # Check if user is still valid
    user = await crud.get_user_by_id(db, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")
        
    # Create NEW tokens and session
    ip_address = security.get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    new_access, new_refresh = await jwt_utils.create_tokens(
        db, user.id, user.email, ip_address=ip_address, user_agent=user_agent
    )
    
    response = JSONResponse(content={
        "access_token": new_access, 
        "refresh_token": new_refresh,
        "token_type": "bearer"
    })
    
    response.set_cookie(key="access_token", value=new_access, httponly=True, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite="none" if settings.COOKIE_SECURE else "lax", secure=settings.COOKIE_SECURE, path="/")
    response.set_cookie(key="refresh_token", value=new_refresh, httponly=True, max_age=7 * 24 * 3600, samesite="none" if settings.COOKIE_SECURE else "lax", secure=settings.COOKIE_SECURE, path="/")
    
    return response

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Try to invalidate the session in DB
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        payload = await jwt_utils.verify_and_decode_token(db, refresh_token)
        if payload and payload.get("jti"):
            await crud.invalidate_user_session(db, payload.get("jti"))

    # Delete all auth cookies
    response.delete_cookie(key="access_token", httponly=True, samesite="none" if settings.COOKIE_SECURE else "lax", secure=settings.COOKIE_SECURE, path="/")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="none" if settings.COOKIE_SECURE else "lax", secure=settings.COOKIE_SECURE, path="/")
    response.delete_cookie(key="csrf_token", httponly=True, samesite="none" if settings.COOKIE_SECURE else "lax", secure=settings.COOKIE_SECURE, path="/")
    
    return {"message": "Successfully logged out"}

@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    request_data: schemas.ForgotPasswordRequest, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await crud.get_user_by_email(db, request_data.email)
    if not user:
        return {"message": "If an account with this email exists, a password reset link has been sent."}
    
    token = pwd_reset_serializer.dumps(user.email, salt="password-reset-salt")
    # In production, this should point to the frontend reset page
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
        message = MessageSchema(
            subject="Chronos - Смяна на парола",
            recipients=[user.email],
            body=f"Здравейте, {user.first_name or 'потребител'},\n\nЗа да смените паролата си, натиснете следния линк:\n{reset_link}\n\nЛинкът е валиден за 30 минути.",
            subtype=MessageType.plain
        )
        fm = FastMail(mail_conf)
        await fm.send_message(message)
    else:
        # Fallback for development: print to console
        print(f"\n\n--- PASSWORD RESET DEBUG ---\nUser: {user.email}\nLink: {reset_link}\n----------------------------\n\n")
        
    return {"message": "If an account with this email exists, a password reset link has been sent."}

@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
    try:
        # Check if token is valid and not expired (max_age=1800 seconds = 30 minutes)
        pwd_reset_serializer.loads(token, salt="password-reset-salt", max_age=1800)
        return {"message": "Token is valid"}
    except Exception:
        raise HTTPException(status_code=400, detail="Невалиден или изтекъл линк за смяна на парола")

@router.post("/reset-password")
@limiter.limit("5/hour")
async def reset_password(
    request: Request,
    request_data: schemas.ResetPasswordRequest, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        # Token expires in 30 minutes
        email = pwd_reset_serializer.loads(request_data.token, salt="password-reset-salt", max_age=1800)
    except Exception:
        raise HTTPException(status_code=400, detail="Невалиден или изтекъл токен")
        
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Потребителят не е намерен")
        
    await validate_password_complexity(db, request_data.new_password)
    
    user.hashed_password = security.hash_password(request_data.new_password)
    user.password_force_change = False # Reset the flag
    db.add(user)
    await db.commit()
    
    return {"message": "Паролата е променена успешно"}

@router.post("/verify-admin-kiosk")
async def verify_admin_kiosk(
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    email = payload.get("email")
    password = payload.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Имейл и парола са задължителни")

    user = await crud.get_user_by_email(db, email)
    if not user or user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Невалиден администратор")
        
    if not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Грешна парола")
        
    return {"message": "Verified"}

from backend.auth.qr_utils import get_dynamic_qr_token, generate_qr_secret
...
@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: Annotated[schemas.User, Depends(jwt_utils.get_current_user)]):
    return current_user

from backend.database.models import User, KioskDevice
from math import cos, asin, sqrt, pi

def haversine_distance(lat1, lon1, lat2, lon2):
    """Изчислява разстоянието между две точки в метри"""
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon1-lon2)*p))/2
    return 12742 * asin(sqrt(a)) * 1000

@router.get("/qr-token")
async def get_my_qr_token(
    request: Request,
    current_user: Annotated[User, Depends(jwt_utils.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """Връща динамичен токен за QR кода на потребителя"""
    
    # 1. Проверка на близост (Proximity Check)
    client_ip = security.get_client_ip(request)
    
    # Вземане на глобални настройки за сигурност (Disabled by default)
    require_gps = await crud.get_global_setting(db, "kiosk_require_gps") == "true"
    require_net = await crud.get_global_setting(db, "kiosk_require_same_network") == "true"
    
    stmt = select(KioskDevice).where(KioskDevice.is_active == True)
    result = await db.execute(stmt)
    kiosks = result.scalars().all()
    
    is_near = False
    # Ако няма регистрирани терминали, позволяваме генериране (за първоначална настройка)
    if not kiosks:
        is_near = True
    else:
        for kiosk in kiosks:
            # IP Check (Optional based on setting)
            ip_valid = True
            if require_net:
                ip_valid = (kiosk.ip_address == client_ip) if kiosk.ip_address else False
            
            # GPS Check (Optional based on setting)
            gps_valid = True
            if require_gps:
                if lat and lon and kiosk.latitude and kiosk.longitude:
                    gps_valid = haversine_distance(lat, lon, kiosk.latitude, kiosk.longitude) <= 50
                else:
                    gps_valid = False
            
            if ip_valid and gps_valid:
                is_near = True
                break

    # Максимална сигурност: Админите винаги могат, служителите само ако са близо (според настройките)
    if not is_near and current_user.role.name not in ["admin", "super_admin"]:
        detail = "Трябва да сте физически до терминала"
        if require_gps and not require_net: detail += " (GPS верификация)"
        if require_net and not require_gps: detail += " (в същата мрежа)"
        if require_net and require_gps: detail += " (GPS + мрежа)"
        
        raise HTTPException(status_code=403, detail=detail)

    if not current_user.qr_secret:
        current_user.qr_secret = generate_qr_secret()
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        
    token = get_dynamic_qr_token(current_user.qr_secret)
    # Форматът е ID:TOKEN за бърза проверка в бекенда
    return {"qr_token": f"{current_user.id}:{token}"}

import shutil
import uuid
import os
from PIL import Image
import io

@router.post("/users/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(jwt_utils.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Качване на профилна снимка"""
    from backend.database.models import User as DbUser
    
    db_user = await db.get(DbUser, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Потребителят не е намерен")
    
    # 1. Валидация на файл
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файлът трябва да бъде изображение.")

    # 2. Обработка с Pillow (Оразмеряване до 400x400)
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Square crop and resize
    width, height = image.size
    min_dim = min(width, height)
    left = (width - min_dim)/2
    top = (height - min_dim)/2
    right = (width + min_dim)/2
    bottom = (height + min_dim)/2
    
    image = image.crop((left, top, right, bottom))
    image.thumbnail((400, 400))

    # 3. Save
    from backend.routers.documents import UPLOAD_DIR
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
        
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.webp"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Convert to WebP for optimization
    image.save(file_path, "WEBP", quality=85)

    # 4. Update user record
    # Remove old avatar if exists
    if db_user.profile_picture:
        old_path = os.path.join(UPLOAD_DIR, db_user.profile_picture)
        if os.path.exists(old_path):
            try: os.remove(old_path)
            except: pass

    db_user.profile_picture = filename
    db.add(db_user)
    await db.commit()
    
    return {"status": "success", "profile_picture": filename}
