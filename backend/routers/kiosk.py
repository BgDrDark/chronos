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


class TerminalScanRequest(BaseModel):
    qr_token: Optional[str] = None
    code: Optional[str] = None
    terminal_hardware_uuid: str
    action: Optional[str] = "access"  # "access", "clock", "auto"


class CodeValidationRequest(BaseModel):
    code: str
    terminal_hardware_uuid: str


@router.post("/terminal/scan")
@require_module("kiosk")
async def terminal_scan(
    request: Request,
    scan: TerminalScanRequest,
    db: AsyncSession = Depends(get_db),
    x_kiosk_secret: str = Header(..., alias="X-Kiosk-Secret")
):
    """Сканиране за достъп - QR код или код от клавиатура + отваряне на врата"""
    from backend.config import settings
    if x_kiosk_secret != getattr(settings, "KIOSK_DEVICE_SECRET", "super-secret-kiosk-key"):
        raise HTTPException(status_code=403, detail="Неоторизиран терминал")
    
    from sqlalchemy import select
    from backend.database.models import AccessDoor, Gateway
    import aiohttp
    
    user = None
    user_name = None
    access_granted = False
    denied_reason = None
    
    # 1. Валидиране на QR код или код
    if scan.qr_token:
        # Валидиране на QR токен
        if ":" in scan.qr_token:
            try:
                user_id_str, token = scan.qr_token.split(":")
                user_id = int(user_id_str)
                user = await crud.get_user_by_id(db, user_id)
                if user and user.qr_secret:
                    if not verify_dynamic_qr_token(user.qr_secret, token):
                        user = None
            except:
                user = None
        
        if not user:
            user = await crud.get_user_by_qr_token(db, scan.qr_token)
        
        if user and user.is_active:
            user_name = f"{user.first_name} {user.last_name}"
            access_granted = True
        else:
            denied_reason = "Невалиден или изтекъл QR код"
    
    elif scan.code:
        # Валидиране на код от клавиатурата
        result = await validate_access_code(db, scan.code, scan.terminal_hardware_uuid)
        if result["valid"]:
            access_granted = True
            user_name = result.get("user_name") or "Гост"
            user = result.get("user")
        else:
            denied_reason = result.get("reason", "Невалиден код")
    
    else:
        raise HTTPException(status_code=400, detail="Липсва QR код или код")
    
    if not access_granted:
        return {
            "status": "denied",
            "message": denied_reason,
            "reason": denied_reason,
            "door_opened": False,
            "user": user_name
        }
    
    # 2. Намиране на вратата свързана с този терминал
    stmt = select(AccessDoor).where(
        AccessDoor.terminal_id == scan.terminal_hardware_uuid,
        AccessDoor.is_active == True
    )
    result = await db.execute(stmt)
    door = result.scalars().first()
    
    if not door:
        # Няма свързана врата - може само да отчита часове
        if scan.action == "clock":
            return await handle_clock_in_out(db, user, scan.action)
        return {
            "status": "denied",
            "message": "Терминалът не е свързан с врата",
            "reason": "no_door",
            "door_opened": False,
            "user": user_name
        }
    
    # 3. Проверка на terminal_mode
    terminal_mode = door.terminal_mode or "access"
    
    if scan.action == "clock" and terminal_mode == "access":
        return {
            "status": "denied",
            "message": "Терминалът е само за достъп",
            "reason": "access_only",
            "door_opened": False,
            "user": user_name
        }
    
    # 4. Trigger към gateway
    gateway = await db.get(Gateway, door.gateway_id)
    door_opened = False
    trigger_message = "Достъп разрешен"
    
    if gateway and gateway.ip_address:
        try:
            url = f"http://{gateway.ip_address}:{gateway.terminal_port}/access/doors/{door.door_id}/trigger"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        trigger_result = await resp.json()
                        door_opened = trigger_result.get("success", False)
                        if not door_opened:
                            trigger_message = trigger_result.get("message", "Грешка при отваряне")
                    else:
                        trigger_message = "Gateway недостъпен"
        except Exception as e:
            trigger_message = f"Грешка: {str(e)}"
    
    return {
        "status": "success" if door_opened else "warning",
        "message": f"{user_name}: {trigger_message}",
        "user": user_name,
        "door_opened": door_opened,
        "door_name": door.name,
        "terminal_mode": terminal_mode
    }


async def validate_access_code(db: AsyncSession, code: str, terminal_hardware_uuid: str) -> dict:
    """Валидира код от клавиатурата"""
    from sqlalchemy import select, and_
    from backend.database.models import AccessCode, AccessDoor
    import datetime
    
    # Намери вратата за този терминал
    stmt = select(AccessDoor).where(
        AccessDoor.terminal_id == terminal_hardware_uuid,
        AccessDoor.is_active == True
    )
    result = await db.execute(stmt)
    door = result.scalars().first()
    
    if not door:
        return {"valid": False, "reason": "Терминалът не е свързан с врата"}
    
    # Намери кода
    stmt = select(AccessCode).where(
        AccessCode.code == code,
        AccessCode.is_active == True
    )
    result = await db.execute(stmt)
    access_code = result.scalars().first()
    
    if not access_code:
        return {"valid": False, "reason": "Невалиден код"}
    
    # Провери дали е изтекъл
    if access_code.expires_at and access_code.expires_at < datetime.datetime.now():
        return {"valid": False, "reason": "Кодът е изтекъл"}
    
    # Провери оставащи използвания
    if access_code.uses_remaining and access_code.uses_remaining <= 0:
        return {"valid": False, "reason": "Кодът е използван"}
    
    # Провери зоните
    allowed_zones = access_code.zones or []
    # Вземи зоната на вратата
    from backend.database.models import AccessZone
    zone = await db.get(AccessZone, door.zone_db_id)
    if zone and zone.zone_id not in allowed_zones:
        return {"valid": False, "reason": "Нямате достъп до тази зона"}
    
    return {
        "valid": True,
        "user_name": access_code.code_type,
        "user": None
    }


async def handle_clock_in_out(db: AsyncSession, user, action: str) -> dict:
    """Отчитане на работно време"""
    from backend.crud import get_active_time_log, start_time_log, end_time_log
    
    active_log = await get_active_time_log(db, user.id)
    
    if action == "clock":
        action = "out" if active_log else "in"
    
    try:
        if action == "in":
            if active_log:
                raise ValueError("Вече сте влезли.")
            await start_time_log(db, user.id)
            message = f"Добре дошли, {user.first_name}!"
        else:
            if not active_log:
                raise ValueError("Не сте влезли, за да излезете.")
            await end_time_log(db, user.id)
            message = f"Довиждане, {user.first_name}!"
        
        return {
            "status": "success",
            "message": message,
            "user": f"{user.first_name} {user.last_name}",
            "action": action.upper(),
            "door_opened": False
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e),
            "door_opened": False
        }


@router.post("/terminal/validate-code")
@require_module("kiosk")
async def validate_code(
    request: Request,
    validation: CodeValidationRequest,
    db: AsyncSession = Depends(get_db),
    x_kiosk_secret: str = Header(..., alias="X-KiosK-Secret")
):
    """Валидира код от клавиатурата (без да отваря врата)"""
    from backend.config import settings
    if x_kiosk_secret != getattr(settings, "KIOSK_DEVICE_SECRET", "super-secret-kiosk-key"):
        raise HTTPException(status_code=403, detail="Неоторизиран терминал")
    
    result = await validate_access_code(db, validation.code, validation.terminal_hardware_uuid)
    return result


# === UNIFIED KIOSK TERMINAL ENDPOINTS ===

class TerminalScanRequest(BaseModel):
    qr_token: str
    action: Optional[str] = "auto"  # auto, in, out, access
    terminal_hardware_uuid: Optional[str] = None

class TerminalSyncRequest(BaseModel):
    offline_logs: list = []

@router.get("/terminal/{hwid}/config")
async def get_terminal_config(
    hwid: str,
    db: AsyncSession = Depends(get_db)
):
    """Връща конфигурацията на терминала (режим на работа)"""
    from backend.database.models import Terminal
    from sqlalchemy import select
    
    stmt = select(Terminal).where(Terminal.hardware_uuid == hwid)
    result = await db.execute(stmt)
    terminal = result.scalar_one_or_none()
    
    if not terminal:
        # Ако терминалът не е регистриран, връщаме подразбираща конфигурация
        return {
            "mode": "both",  # clock, access, both
            "registered": False,
            "terminal_id": None,
            "alias": None
        }
    
    return {
        "mode": terminal.mode or "both",
        "registered": True,
        "terminal_id": terminal.id,
        "alias": terminal.alias,
        "is_active": terminal.is_active
    }


@router.post("/terminal/{hwid}/scan")
@require_module("kiosk")
@limiter.limit("20/minute")
async def unified_terminal_scan(
    request: Request,
    hwid: str,
    scan: TerminalScanRequest,
    db: AsyncSession = Depends(get_db)
):
    """Обработва сканиране от обединения терминал (Clock In/Out + Access)"""
    from backend.database.models import Terminal
    from backend.auth.qr_utils import verify_dynamic_qr_token
    from sqlalchemy import select
    from backend import crud
    from backend.config import settings
    
    # 1. Get terminal config
    stmt = select(Terminal).where(Terminal.hardware_uuid == hwid)
    result = await db.execute(stmt)
    terminal = result.scalar_one_or_none()
    
    mode = terminal.mode if terminal else "both"
    
    # 2. Find user by QR token
    user = None
    if ":" in scan.qr_token:
        try:
            user_id_str, token = scan.qr_token.split(":")
            user_id = int(user_id_str)
            user = await crud.get_user_by_id(db, user_id)
            if user and user.qr_secret:
                if not verify_dynamic_qr_token(user.qr_secret, token):
                    user = None
        except:
            user = None
    
    if not user:
        user = await crud.get_user_by_qr_token(db, scan.qr_token)
    
    if not user:
        return {"status": "error", "message": "Невалиден QR код", "success": False}
    
    if not user.is_active:
        return {"status": "error", "message": "Акаунтът е деактивиран", "success": False}
    
    response = {
        "status": "ok",
        "user": user.first_name,
        "success": True
    }
    
    # 3. Handle Clock In/Out
    if mode in ["clock", "both"]:
        if scan.action in ["auto", "in", "out"]:
            from backend.crud import get_active_time_log, create_time_log
            
            active_log = await get_active_time_log(db, user.id)
            action = scan.action if scan.action != "auto" else ("out" if active_log else "in")
            
            if action == "in":
                new_log = await create_time_log(db, user.id, "in")
                response["clock_action"] = "in"
                response["message"] = f"Добър ден, {user.first_name}!"
            else:
                # Close the active log
                if active_log:
                    active_log.time_out = datetime.datetime.now()
                    await db.commit()
                response["clock_action"] = "out"
                response["message"] = f"Довиждане, {user.first_name}!"
    
    # 4. Handle Access (Door)
    if mode in ["access", "both"]:
        if scan.action == "access" or scan.action == "auto":
            # Find doors associated with this terminal
            from backend.database.models import AccessDoor
            
            stmt = select(AccessDoor).where(
                AccessDoor.terminal_id == hwid,
                AccessDoor.is_active == True
            )
            result = await db.execute(stmt)
            doors = result.scalars().all()
            
            if doors:
                door = doors[0]  # Use first door
                
                # Check access rights
                from backend.routers.access import check_user_access_to_zone
                has_access = await check_user_access_to_zone(db, user.id, door.zone_db_id)
                
                if has_access:
                    # Trigger door (would need gateway for actual hardware)
                    response["door_opened"] = True
                    response["door_name"] = door.name
                    response["access_granted"] = True
                else:
                    response["door_opened"] = False
                    response["access_granted"] = False
                    response["message"] = "Нямате достъп до тази зона"
            else:
                response["door_opened"] = False
                response["access_granted"] = None
                response["message"] = "Няма конфигурирана врата за този терминал"
    
    # 5. Update terminal last_seen
    if terminal:
        terminal.last_seen = datetime.datetime.now()
        terminal.total_scans = (terminal.total_scans or 0) + 1
        await db.commit()
    
    return response


@router.post("/terminal/{hwid}/sync")
@require_module("kiosk")
async def sync_offline_data(
    request: Request,
    hwid: str,
    sync_data: TerminalSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """Синхронизира офлайн данни от терминала"""
    from backend.database.models import Terminal, AccessLog, TimeLog
    from sqlalchemy import select
    from datetime import datetime
    
    synced_count = 0
    
    for log_entry in sync_data.offline_logs:
        try:
            log_type = log_entry.get("type")
            
            if log_type == "clock":
                # Create time log
                time_log = TimeLog(
                    user_id=log_entry.get("user_id"),
                    date=datetime.now().date(),
                    time_in=log_entry.get("timestamp"),
                    time_out=None,
                    company_id=1  # Would get from terminal config
                )
                db.add(time_log)
                synced_count += 1
                
            elif log_type == "access":
                # Create access log
                access_log = AccessLog(
                    timestamp=log_entry.get("timestamp"),
                    user_id=log_entry.get("user_id"),
                    zone_id=log_entry.get("zone_id"),
                    door_id=log_entry.get("door_id"),
                    result="granted" if log_entry.get("result") == "granted" else "denied",
                    method="qr"
                )
                db.add(access_log)
                synced_count += 1
        
        except Exception as e:
            print(f"Error syncing log: {e}")
    
    await db.commit()
    
    # Update terminal last_seen
    stmt = select(Terminal).where(Terminal.hardware_uuid == hwid)
    result = await db.execute(stmt)
    terminal = result.scalar_one_or_none()
    if terminal:
        terminal.last_seen = datetime.datetime.now()
        await db.commit()
    
    return {
        "status": "ok",
        "synced": synced_count
    }
