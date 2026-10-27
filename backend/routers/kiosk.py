import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import crud
from backend.auth import jwt_utils
from backend.auth.limiter import limiter
from backend.auth.module_guard import require_module
from backend.config import settings
from backend.database.database import get_db

router = APIRouter(prefix="/kiosk", tags=["kiosk"])


@router.get("/config")
async def get_kiosk_config(db: AsyncSession = Depends(get_db)):
    """Публична конфигурация за терминала (фон и др.)"""
    bg_image = await crud.get_global_setting(db, "kiosk_background_image")
    return {
        "background_image": bg_image,
    }


class CodeValidationRequest(BaseModel):
    code: str
    terminal_hardware_uuid: str


async def validate_access_code(
    db: AsyncSession, code: str, terminal_hardware_uuid: str
) -> dict:
    """Валидира код от клавиатурата"""
    import datetime

    from sqlalchemy import select

    from backend.database.models import AccessCode, AccessDoor

    # Намери вратата за този терминал
    stmt = select(AccessDoor).where(
        AccessDoor.terminal_id == terminal_hardware_uuid,
        AccessDoor.is_active,
    )
    result = await db.execute(stmt)
    door = result.scalars().first()

    if not door:
        return {"valid": False, "reason": "Терминалът не е свързан с врата"}

    # Намери кода
    stmt = select(AccessCode).where(
        AccessCode.code == code,
        AccessCode.is_active,
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
        "user": None,
    }


_validate_code_limiter = None


@router.post("/terminal/validate-code")
@require_module("kiosk")
async def validate_code(
    request: Request,
    validation: CodeValidationRequest,
    db: AsyncSession = Depends(get_db),
    x_kiosk_secret: str = Header(..., alias="X-KiosK-Secret"),
):
    """Валидира код от клавиатурата (без да отваря врата)"""
    if x_kiosk_secret != getattr(
        settings, "KIOSK_DEVICE_SECRET", "super-secret-kiosk-key"
    ):
        raise HTTPException(status_code=403, detail="Неоторизиран терминал")

    from backend.auth.limiter import APIKeyRateLimiter
    from backend.crud import get_global_setting

    global _validate_code_limiter

    key = f"validate_code:{request.client.host if request.client else 'unknown'}"

    limit_raw = await get_global_setting(db, "kiosk_validate_code_rate_limit")
    if limit_raw:
        import re

        match = re.match(r"^(\d+)/(minute|hour|second|day)$", limit_raw)
        if match:
            count = int(match.group(1))
            unit = match.group(2)
            window = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}.get(
                unit, 60
            )
            limiter = APIKeyRateLimiter(max_requests=count, window_seconds=window)
        else:
            if _validate_code_limiter is None:
                _validate_code_limiter = APIKeyRateLimiter(
                    max_requests=5, window_seconds=60
                )
            limiter = _validate_code_limiter
    else:
        if _validate_code_limiter is None:
            _validate_code_limiter = APIKeyRateLimiter(
                max_requests=5, window_seconds=60
            )
        limiter = _validate_code_limiter

    if not limiter.is_allowed(key):
        raise HTTPException(status_code=429, detail="Твърде много опити. Изчакайте.")

    result = await validate_access_code(
        db, validation.code, validation.terminal_hardware_uuid
    )
    return result


def _default_terminal_config() -> dict:
    return {
        "display": {
            "clock_size": "large",
            "show_date": True,
            "show_weather": False,
            "background": {"type": "color", "value": "#1a1a2e"},
            "logo_url": None,
        },
        "colors": {
            "primary": "#1976d2",
            "secondary": "#dc004e",
            "background": "#1a1a2e",
            "surface": "#16213e",
            "text": "#ffffff",
            "error": "#ff5252",
            "success": "#4caf50",
        },
        "timeouts": {
            "inactivity_reset": 120,
            "screensaver_delay": 30,
            "screensaver_idle_action": "reset",
        },
        "screensaver": {
            "type": "logo",
            "image_url": None,
        },
        "sounds": {
            "enabled": True,
            "scan_success": "default",
            "scan_error": "default",
            "keypress": "default",
        },
        "text": {
            "title": None,
            "welcome_message": None,
            "scan_placeholder": "Поставете карта или QR код",
            "scanning_text": "Сканиране...",
            "success_message": "Достъпът е разрешен",
            "error_message": "Достъпът е отказан",
        },
        "tts": {
            "enabled": False,
            "language": "bg-BG",
            "scan_success": True,
            "scan_error": True,
        },
        "security": {
            "exit_method": "pin",
            "exit_pin_required": True,
        },
        "mode": "both",  # qr, nfc, both
    }


# === UNIFIED KIOSK TERMINAL ENDPOINTS ===


class TerminalScanRequest(BaseModel):
    qr_token: str | None = None
    card_number: str | None = None
    action: str | None = "auto"  # auto, in, out, access
    terminal_hardware_uuid: str | None = None


class TerminalSyncRequest(BaseModel):
    offline_logs: list = []


@router.get("/terminal")
@router.get("/terminals")
@require_module("kiosk")
async def get_terminals_list(
    db: AsyncSession = Depends(get_db),
):
    """Списък на всички регистрирани терминали"""
    from sqlalchemy import select

    from backend.database.models import Terminal

    stmt = select(Terminal)
    result = await db.execute(stmt)
    terminals = result.scalars().all()

    return terminals


@router.get("/terminal/{hwid}/config")
async def get_terminal_config(
    hwid: str,
    db: AsyncSession = Depends(get_db),
    x_kiosk_secret: str = Header(None, alias="X-Kiosk-Secret"),
):
    """Връща конфигурацията на терминала (режим на работа)
    Terminals are auto-registered on first access.
    """
    from backend.database.models import Terminal

    stmt = select(Terminal).where(Terminal.hardware_uuid == hwid)
    result = await db.execute(stmt)
    terminal = result.scalar_one_or_none()

    if not terminal:
        # Проверка на secret само за нови (нерегистрирани) терминали
        expected_secret = getattr(settings, "KIOSK_DEVICE_SECRET", "super-secret-kiosk-key")
        if x_kiosk_secret != expected_secret:
            raise HTTPException(status_code=403, detail="Неоторизиран терминал")
        # Автоматично регистриране на нов терминал
        terminal = Terminal(
            hardware_uuid=hwid,
            device_name=f"New Terminal {hwid[:8]}",
            device_type="tablet",
            mode="both",
            is_active=True,
            last_seen=datetime.datetime.now(),
        )
        db.add(terminal)
        await db.commit()
        await db.refresh(terminal)

        return {
            "mode": "both",
            "registered": True,
            "terminal_id": terminal.id,
            "alias": None,
            "is_active": True,
            "new_registration": True,
        }

    merged = {**_default_terminal_config(), **(terminal.config or {})}
    return {
        "mode": terminal.mode or "both",
        "registered": True,
        "terminal_id": terminal.id,
        "alias": terminal.alias,
        "is_active": terminal.is_active,
        "config": merged,
    }


@router.put("/terminal/{hwid}/config")
async def update_terminal_config(
    hwid: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(jwt_utils.get_current_user),
):
    """Обновява конфигурацията на терминала (partial merge)"""
    from backend.database.models import Terminal

    stmt = select(Terminal).where(Terminal.hardware_uuid == hwid)
    result = await db.execute(stmt)
    terminal = result.scalar_one_or_none()
    if not terminal:
        raise HTTPException(status_code=404, detail="Терминалът не е намерен")
    existing = terminal.config or {}
    for key, value in body.items():
        if key in existing and isinstance(existing[key], dict) and isinstance(value, dict):
            existing[key] = {**existing[key], **value}
        else:
            existing[key] = value
    terminal.config = existing
    await db.commit()
    return {"ok": True}


@router.post("/terminal/{hwid}/verify-pin")
async def verify_admin_pin(
    hwid: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Проверява PIN код за администраторски изход от терминала.
    Търси потребители с роля super_admin или admin и проверява PIN-а им.
    """
    from sqlalchemy import select

    from backend.database.models import CompanyRoleAssignment, Role, User

    pin = body.get("pin")
    if not pin:
        raise HTTPException(status_code=400, detail="Липсва PIN код")

    # Намиране на admin роли
    role_result = await db.execute(
        select(Role.id).where(Role.name.in_(["super_admin", "admin"]))
    )
    admin_role_ids = [r[0] for r in role_result.all()]
    if not admin_role_ids:
        raise HTTPException(status_code=400, detail="Няма конфигуриран администратор")

    # Намиране на потребители с тези роли
    assignment_result = await db.execute(
        select(CompanyRoleAssignment.user_id).where(
            CompanyRoleAssignment.role_id.in_(admin_role_ids),
            CompanyRoleAssignment.is_active,
        )
    )
    admin_user_ids = list({r[0] for r in assignment_result.all()})

    # Ако няма company_role_assignments, провери role_id директно в User
    if not admin_user_ids:
        user_result = await db.execute(
            select(User.id).where(
                User.role_id.in_(admin_role_ids),
                User.is_active,
            )
        )
        admin_user_ids = [r[0] for r in user_result.all()]

    if not admin_user_ids:
        raise HTTPException(status_code=400, detail="Няма конфигуриран администратор")

    from backend.utils.pin_utils import verify_pin as verify_pin_hash

    user_result = await db.execute(
        select(User).where(
            User.id.in_(admin_user_ids),
            User.pin_sha256.is_not(None),
            User.is_active,
        )
    )
    user = next(
        (
            candidate
            for candidate in user_result.scalars().all()
            if verify_pin_hash(pin, candidate.pin_sha256)
        ),
        None,
    )
    if not user:
        raise HTTPException(status_code=400, detail="Невалиден PIN код")

    return {
        "ok": True,
        "user_id": user.id,
        "name": user.display_name or f"{user.first_name} {user.last_name}",
    }


@router.post("/terminal/{hwid}/scan")
@require_module("kiosk")
@limiter.limit("20/minute")
async def unified_terminal_scan(
    request: Request,
    hwid: str,
    scan: TerminalScanRequest,
    db: AsyncSession = Depends(get_db),
):
    """Обработва сканиране от обединения терминал (Clock In/Out + Access)"""
    from sqlalchemy import select

    from backend import crud
    from backend.auth.qr_utils import verify_dynamic_qr_token
    from backend.database.models import Terminal

    # 1. Get terminal config
    stmt = select(Terminal).where(Terminal.hardware_uuid == hwid)
    result = await db.execute(stmt)
    terminal = result.scalar_one_or_none()

    mode = terminal.mode if terminal else "both"

    # 2. Find user by QR token or card_number
    user = None
    if scan.qr_token:
        if ":" in scan.qr_token:
            try:
                user_id_str, token = scan.qr_token.split(":")
                user_id = int(user_id_str)
                user = await crud.get_user_by_id(db, user_id)
                if (
                    user
                    and user.qr_secret
                    and not verify_dynamic_qr_token(user.qr_secret, token)
                ):
                    user = None
            except Exception:
                user = None

        if not user:
            user = await crud.get_user_by_qr_token(db, scan.qr_token)

    if not user and scan.card_number:
        from sqlalchemy import select

        from backend.database.models import User as DbUser
        stmt = select(DbUser).where(DbUser.card_number == scan.card_number)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        return {
            "status": "error",
            "message": "Невалиден QR код или карта",
            "success": False,
            "card_number": scan.card_number,
        }

    if not user.is_active:
        return {
            "status": "error",
            "message": "Акаунтът е деактивиран",
            "success": False,
        }

    response = {
        "status": "ok",
        "user": user.first_name,
        "success": True,
        "card_number": scan.card_number,
    }

    # 3. Handle Clock In/Out
    if mode in ["clock", "both"] and scan.action in ["auto", "in", "out"]:
        from backend.crud import end_time_log, get_active_time_log, start_time_log

        active_log = await get_active_time_log(db, user.id)
        action = (
            scan.action if scan.action != "auto" else ("out" if active_log else "in")
        )

        if action == "in" and not active_log:
            await start_time_log(db, user.id)
            response["clock_action"] = "in"
            response["message"] = f"Добър ден, {user.first_name}!"
        else:
            if active_log:
                await end_time_log(db, user.id)
            response["clock_action"] = "out"
            response["message"] = f"Довиждане, {user.first_name}!"

    # 4. Handle Access (Door)
    if mode in ["access", "both"] and scan.action == "access" or scan.action == "auto":
        # Find doors associated with this terminal
        from sqlalchemy.orm import joinedload

        from backend.database.models import AccessDoor

        stmt = (
            select(AccessDoor)
            .where(
                AccessDoor.terminal_id == hwid,
                AccessDoor.is_active,
            )
            .options(joinedload(AccessDoor.zone))
        )
        result = await db.execute(stmt)
        doors = result.scalars().all()

        if doors:
            door = doors[0]  # Use first door

            # Check access rights directly via association table
            from datetime import datetime

            from sqlalchemy import and_

            from backend.database.models import AccessLog, user_access_zones

            stmt = select(user_access_zones).where(
                and_(
                    user_access_zones.c.user_id == user.id,
                    user_access_zones.c.zone_id == door.zone_db_id,
                ),
            )
            res = await db.execute(stmt)
            has_access = res.first() is not None or user.role.name == "super_admin"

            log_entry = AccessLog(
                timestamp=datetime.now(),
                user_id=str(user.id),
                user_name=f"{user.first_name} {user.last_name}",
                zone_id=door.zone.zone_id if door.zone else "unknown",
                zone_name=door.zone.name if door.zone else "Unknown Zone",
                door_id=door.door_id,
                door_name=door.name,
                action="entry",
                method="qr" if scan.qr_token else "code",
                terminal_id=hwid,
                gateway_id=door.gateway_id,
            )

            if has_access:
                # ... (trigger door logic)
                try:
                    import aiohttp

                    from backend.database.models import Gateway

                    gw = await db.get(Gateway, door.gateway_id)
                    if gw and gw.ip_address:
                        url = f"http://{gw.ip_address}:{gw.web_port}/access/doors/{door.door_id}/trigger"
                        async with aiohttp.ClientSession() as session:
                            async with session.post(url, timeout=3) as r:
                                if r.status == 200:
                                    response["door_opened"] = True
                                else:
                                    response["door_opened"] = False
                    else:
                        response["door_opened"] = False
                except Exception:
                    response["door_opened"] = False

                response["door_name"] = door.name
                response["access_granted"] = True

                log_entry.result = "granted"
                log_entry.reason = "Authorized"
            else:
                response["door_opened"] = False
                response["access_granted"] = False
                response["message"] = "Нямате достъп до тази зона"

                log_entry.result = "denied"
                log_entry.reason = "No Zone Permission"

            db.add(log_entry)
            await db.commit()
        else:
            response["door_opened"] = False
            response["access_granted"] = None
            response["message"] = "Няма конфигурирана врата за този терминал"

    # 5. Update terminal last_seen
    if terminal:
        from datetime import datetime

        terminal.last_seen = datetime.now()
        terminal.total_scans = (terminal.total_scans or 0) + 1
        await db.commit()

    return response


@router.post("/terminal/{hwid}/sync")
@require_module("kiosk")
async def sync_offline_data(
    request: Request,
    hwid: str,
    sync_data: TerminalSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """Синхронизира офлайн данни от терминала"""
    from datetime import datetime

    from sqlalchemy import select

    from backend.database.models import AccessLog, Terminal, TimeLog

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
                    company_id=1,  # Would get from terminal config
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
                    result="granted"
                    if log_entry.get("result") == "granted"
                    else "denied",
                    method="qr",
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
        terminal.last_seen = datetime.now()
        await db.commit()

    return {
        "status": "ok",
        "synced": synced_count,
    }
