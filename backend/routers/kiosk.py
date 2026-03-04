from fastapi import APIRouter, Depends, HTTPException, Header, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import get_db
from backend import crud
from backend.database.models import User
from pydantic import BaseModel
from typing import Optional
import datetime
from backend.auth.limiter import limiter

router = APIRouter(prefix="/kiosk", tags=["kiosk"])

@router.get("/config")
async def get_kiosk_config(db: AsyncSession = Depends(get_db)):
    """Публична конфигурация за терминала (фон и др.)"""
    bg_image = await crud.get_global_setting(db, "kiosk_background_image")
    return {
        "background_image": bg_image
    }

class KioskScan(BaseModel):
    qr_token: str
    action: Optional[str] = "auto" # auto, in, out

from backend.auth.qr_utils import verify_dynamic_qr_token
from sqlalchemy import or_

from backend.auth.module_guard import require_module

@router.post("/scan")
@require_module("kiosk")
@limiter.limit("10/minute")
async def kiosk_scan(
    request: Request,
    scan: KioskScan,
    db: AsyncSession = Depends(get_db),
    x_kiosk_secret: str = Header(..., alias="X-Kiosk-Secret")
):
    # 0. Валидация на терминала
    from backend.config import settings
    if x_kiosk_secret != getattr(settings, "KIOSK_DEVICE_SECRET", "super-secret-kiosk-key"):
        raise HTTPException(status_code=403, detail="Неоторизиран терминал")

    # 1. Търсим потребителя
    # Първо пробваме динамично (Max Security)
    # Понеже не знаем кой е потребителя само по 8 цифри, трябва да проверим всички активни 
    # или да подадем UserID в QR кода. За по-добра сигурност и скорост, 
    # QR кодът ще бъде във формат: "UserID:DynamicToken"
    
    user = None
    if ":" in scan.qr_token:
        try:
            user_id_str, token = scan.qr_token.split(":")
            user_id = int(user_id_str)
            user = await crud.get_user_by_id(db, user_id)
            if user and user.qr_secret:
                if not verify_dynamic_qr_token(user.qr_secret, token):
                    user = None # Невалиден динамичен токен
        except:
            user = None
            
    # Fallback към статичен токен (за съвместимост, докато всички минат на динамични)
    if not user:
        user = await crud.get_user_by_qr_token(db, scan.qr_token)
        
    if not user:
        raise HTTPException(status_code=404, detail="Невалиден или изтекъл QR код")
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Акаунтът е деактивиран")

    # 2. Determine Action
    from backend.crud import get_active_time_log
    active_log = await get_active_time_log(db, user.id)
    
    action = scan.action
    if action == "auto":
        action = "out" if active_log else "in"
    
    # 3. Execute
    try:
        if action == "in":
            if active_log:
                raise ValueError("Вече сте влезли.")
            await crud.start_time_log(db, user.id)
            message = f"Добре дошли, {user.first_name}!"
            action_code = "IN"
        else:
            if not active_log:
                raise ValueError("Не сте влезли, за да излезете.")
            await crud.end_time_log(db, user.id)
            message = f"Довиждане, {user.first_name}!"
            action_code = "OUT"
            
        profile_pic = user.profile_picture
        if profile_pic and not profile_pic.startswith('http') and not profile_pic.startswith('/'):
            profile_pic = f"/uploads/{profile_pic}"
            
        return {
            "status": "success", 
            "message": message, 
            "user": f"{user.first_name} {user.last_name}", 
            "action": action_code,
            "profile_picture": profile_pic
        }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
