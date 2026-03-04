from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from backend.database.database import get_db
from backend.database.models import User, GoogleCalendarAccount, GoogleCalendarSyncSettings, sofia_now
from backend.auth import jwt_utils
from backend.services.google_calendar_service import google_calendar_service
from backend.config import settings

from backend.auth.module_guard import require_module_dep

router = APIRouter(
    prefix="/auth/google", 
    tags=["Google Integration"],
    dependencies=[Depends(require_module_dep("integrations"))]
)

@router.get("/login")
async def google_login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Инициализира Google OAuth2 поток"""
    # За макс. сигурност бихме използвали Bearer токен от хедъра, 
    # но понеже това е редирект от браузъра, ще разчитаме на текущата сесия 
    # или ще изискваме потребителят да е логнат в браузъра (cookies).
    
    # Тъй като фронтендът ни ползва localStorage, ще трябва да подадем 
    # токена като query param или да използваме временен state.
    # За простота тук ще приемем, че потребителят се идентифицира чрез state.
    
    token = request.query_params.get("token")
    if not token:
        # В реална ситуация тук трябва да проверим бисквитката 'access_token'
        token = request.cookies.get("access_token")
        
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    payload = await jwt_utils.verify_and_decode_token(db, token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user_email = payload.get("sub")
    stmt = select(User).where(User.email == user_email)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    auth_url = await google_calendar_service.get_auth_url(user.id)
    return RedirectResponse(auth_url)

@router.get("/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Обработва отговора от Google и записва токените"""
    try:
        # Извличане на user_id от state (формат: user_123)
        user_id = int(state.split("_")[1])
        
        # Размяна на кода за токени
        token_data = await google_calendar_service.exchange_code_for_tokens(code)
        
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        
        # Вземане на имейл на Google акаунта
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            resp.raise_for_status()
            user_info = resp.json()
            google_email = user_info.get("email")

        # Проверка за съществуващ акаунт
        stmt = select(GoogleCalendarAccount).where(GoogleCalendarAccount.user_id == user_id)
        res = await db.execute(stmt)
        account = res.scalars().first()
        
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        if account:
            account.email = google_email
            account.access_token = access_token
            if refresh_token: # Google връща refresh_token само при първия consent
                account.refresh_token = refresh_token
            account.token_expires_at = expires_at
            account.is_active = True
        else:
            account = GoogleCalendarAccount(
                user_id=user_id,
                google_user_id=user_info.get("sub"),
                email=google_email,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at
            )
            db.add(account)
            await db.flush() # Вземане на ID
            
            # Създаване на начални настройки за синхронизация
            sync_settings = GoogleCalendarSyncSettings(
                account_id=account.id,
                calendar_id='primary'
            )
            db.add(sync_settings)

        await db.commit()
        
        # Редирект обратно към настройките във фронтенда
        frontend_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "http://localhost:5173"
        return RedirectResponse(f"{frontend_url}/settings?google_sync=success")
        
    except Exception as e:
        print(f"Google Callback Error: {e}")
        frontend_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "http://localhost:5173"
        return RedirectResponse(f"{frontend_url}/settings?google_sync=error&detail={str(e)}")
