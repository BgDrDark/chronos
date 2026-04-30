from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta
import secrets
import logging

from backend.database.database import get_db
from backend.database.models import Gateway, Terminal, Printer, GatewayHeartbeat, AccessZone, AccessDoor, AccessCode, AccessLog, User
from backend.auth.module_guard import require_module
from backend.auth.limiter import limiter
from backend.auth.jwt_utils import get_current_user

router = APIRouter(prefix="/gateways", tags=["gateways"])
logger = logging.getLogger(__name__)

def generate_api_key() -> str:
    return "gw_" + secrets.token_hex(24)

class GatewayCreate(BaseModel):
    hardware_uuid: str
    ip_address: Optional[str] = None
    local_hostname: Optional[str] = None
    terminal_port: int = 8080
    web_port: int = 8888

class GatewayRegisterResponse(BaseModel):
    id: int
    name: str
    hardware_uuid: str
    alias: Optional[str]
    ip_address: Optional[str]
    local_hostname: Optional[str]
    terminal_port: int
    web_port: int
    is_active: bool
    api_key: str
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GatewayUpdate(BaseModel):
    alias: Optional[str] = None
    is_active: Optional[bool] = None


class GatewayResponse(BaseModel):
    id: int
    name: str
    hardware_uuid: str
    alias: Optional[str]
    ip_address: Optional[str]
    local_hostname: Optional[str]
    terminal_port: int
    web_port: int
    is_active: bool
    system_mode: str
    last_heartbeat: Optional[datetime]
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TerminalResponse(BaseModel):
    id: int
    hardware_uuid: str
    device_name: Optional[str]
    device_type: str
    gateway_id: Optional[int]
    is_active: bool
    last_seen: Optional[datetime]
    total_scans: int
    alias: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class GatewayUpdate(BaseModel):
    alias: Optional[str] = None
    is_active: Optional[bool] = None

class GatewayResponse(BaseModel):
    id: int
    name: str
    hardware_uuid: str
    alias: Optional[str]
    ip_address: Optional[str]
    local_hostname: Optional[str]
    terminal_port: int
    web_port: int
    is_active: bool
    system_mode: str
    last_heartbeat: Optional[datetime]
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TerminalResponse(BaseModel):
    id: int
    hardware_uuid: str
    device_name: Optional[str]
    device_type: str
    gateway_id: Optional[int]
    is_active: bool
    last_seen: Optional[datetime]
    total_scans: int
    alias: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PrinterCreate(BaseModel):
    name: str
    printer_type: str
    ip_address: Optional[str] = None
    port: int = 9100
    protocol: str = "raw"
    windows_share_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    is_default: bool = False


class PrinterResponse(BaseModel):
    id: int
    name: str
    printer_type: str
    ip_address: Optional[str]
    port: int
    protocol: str
    gateway_id: int
    is_active: bool
    is_default: bool
    last_test: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class TerminalResponse(BaseModel):
    id: int
    hardware_uuid: str
    device_name: Optional[str]
    device_type: str
    gateway_id: Optional[int]
    is_active: bool
    last_seen: Optional[datetime]
    total_scans: int
    alias: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class PrinterCreate(BaseModel):
    name: str
    printer_type: str
    ip_address: Optional[str] = None
    port: int = 9100
    protocol: str = "raw"
    windows_share_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    is_default: bool = False

class PrinterResponse(BaseModel):
    id: int
    name: str
    printer_type: str
    ip_address: Optional[str]
    port: int
    protocol: str
    gateway_id: int
    is_active: bool
    is_default: bool
    last_test: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class GatewayHeartbeatRequest(BaseModel):
    status: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    terminal_count: int = 0
    printer_count: int = 0

class AccessZoneCreate(BaseModel):
    zone_id: str
    name: str
    level: int = 1
    depends_on: List[str] = []
    required_hours_start: str = "00:00"
    required_hours_end: str = "23:59"
    anti_passback_enabled: bool = False
    anti_passback_type: str = "soft"
    anti_passback_timeout: int = 5
    description: Optional[str] = None

class AccessZoneResponse(BaseModel):
    id: int
    zone_id: str
    name: str
    level: int
    depends_on: List[str]
    required_hours_start: str
    required_hours_end: str
    anti_passback_enabled: bool
    anti_passback_type: str
    anti_passback_timeout: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class AccessDoorCreate(BaseModel):
    door_id: str
    name: str
    zone_db_id: int
    gateway_id: int
    device_id: str
    relay_number: int = 1
    terminal_id: Optional[str] = None

class AccessDoorResponse(BaseModel):
    id: int
    door_id: str
    name: str
    zone_db_id: int
    gateway_id: int
    device_id: str
    relay_number: int
    terminal_id: Optional[str]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class AccessCodeCreate(BaseModel):
    code: Optional[str] = None
    code_type: str = "one_time"
    zones: List[str] = []
    uses_remaining: int = 1
    expires_hours: Optional[int] = 24
    gateway_id: Optional[int] = None

class AccessCodeResponse(BaseModel):
    id: int
    code: str
    code_type: str
    uses_remaining: int
    expires_at: Optional[datetime]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class AccessLogSync(BaseModel):
    timestamp: datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    door_id: Optional[str] = None
    door_name: Optional[str] = None
    action: str
    result: str
    reason: Optional[str] = None
    method: str
    terminal_id: Optional[str] = None

class AccessLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    action: str
    result: str
    method: str
    gateway_id: int
    model_config = ConfigDict(from_attributes=True)

@router.post("/register", response_model=GatewayRegisterResponse)
async def register_gateway(gateway: GatewayCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Gateway).where(Gateway.hardware_uuid == gateway.hardware_uuid))
    existing_gateway = existing.scalar_one_or_none()
    if existing_gateway:
        if not existing_gateway.api_key:
            existing_gateway.api_key = generate_api_key()
            await db.commit()
            await db.refresh(existing_gateway)
        raise HTTPException(status_code=400, detail={"message": "Вече регистриран", "id": existing_gateway.id, "api_key": existing_gateway.api_key})
    
    res = await db.execute(select(Gateway).order_by(Gateway.id.desc()).limit(1))
    last = res.scalar_one_or_none()
    new_name = f"GATEWAY-{(last.id + 1 if last else 1):03d}"
    api_key = generate_api_key()
    new_gw = Gateway(name=new_name, hardware_uuid=gateway.hardware_uuid, api_key=api_key, ip_address=gateway.ip_address, local_hostname=gateway.local_hostname, terminal_port=gateway.terminal_port, web_port=gateway.web_port)
    db.add(new_gw)
    await db.commit()
    await db.refresh(new_gw)
    return new_gw

@router.post("/bulk-emergency-action")
@require_module("kiosk")
async def bulk_emergency_action(action: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if action not in ["normal", "emergency_unlock", "lockdown"]:
        raise HTTPException(status_code=400, detail="Невалидна команда")
    await db.execute(update(Gateway).where(Gateway.company_id == current_user.company_id).values(system_mode=action))
    from backend.database.models import AuditLog
    db.add(AuditLog(user_id=current_user.id, action=f"EMERGENCY_{action.upper()}", target_type="System", details=f"Масово: {action}"))
    await db.commit()
    return {"status": "success", "mode": action}

@router.get("/{gateway_id}/config")
async def get_gateway_config(gateway_id: int, db: AsyncSession = Depends(get_db)):
    gateway = await db.get(Gateway, gateway_id)
    if not gateway: raise HTTPException(status_code=404, detail="Няма такъв gateway")
    doors_res = await db.execute(select(AccessDoor).where(AccessDoor.gateway_id == gateway_id, AccessDoor.is_active == True))
    doors = doors_res.scalars().all()
    zone_ids = list(set([d.zone_db_id for d in doors]))
    zones = []
    if zone_ids:
        zones_res = await db.execute(select(AccessZone).where(AccessZone.id.in_(zone_ids), AccessZone.is_active == True).options(selectinload(AccessZone.authorized_users)))
        zones = zones_res.scalars().all()
    return {
        "gateway_id": gateway.id, "name": gateway.name, "alias": gateway.alias, "system_mode": gateway.system_mode or "normal",
        "access_control": {
            "enabled": True,
            "zones": [{"id": z.zone_id, "name": z.name, "level": z.level, "depends_on": z.depends_on, "authorized_users": [u.id for u in z.authorized_users], "required_hours": {"start": z.required_hours_start, "end": z.required_hours_end}, "anti_passback": {"enabled": z.anti_passback_enabled, "type": z.anti_passback_type, "timeout_minutes": z.anti_passback_timeout}} for z in zones],
            "doors": [{"id": d.door_id, "name": d.name, "zone_id": next((z.zone_id for z in zones if z.id == d.zone_db_id), ""), "device_id": d.device_id, "relay_number": d.relay_number, "terminal_id": d.terminal_id, "terminal_mode": d.terminal_mode} for d in doors]
        }
    }

@router.get("", response_model=List[GatewayResponse])
@require_module("kiosk")
async def list_gateways(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Gateway).order_by(Gateway.registered_at.desc()).offset(skip).limit(limit))
    return res.scalars().all()

@router.get("/stats")
@require_module("kiosk")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(Gateway))
    terminals = await db.scalar(select(Terminal))
    return {"gateways": {"total": total or 0}, "terminals": {"total": terminals or 0}}

@router.get("/{gateway_id}", response_model=GatewayResponse)
@require_module("kiosk")
async def get_gateway(gateway_id: int, db: AsyncSession = Depends(get_db)):
    gw = await db.get(Gateway, gateway_id)
    if not gw: raise HTTPException(status_code=404, detail="Не е намерен")
    return gw

@router.patch("/{gateway_id}", response_model=GatewayResponse)
@require_module("kiosk")
async def update_gw(gateway_id: int, upd: GatewayUpdate, db: AsyncSession = Depends(get_db)):
    gw = await db.get(Gateway, gateway_id)
    if not gw: raise HTTPException(status_code=404, detail="Не е намерен")
    if upd.alias is not None: gw.alias = upd.alias
    if upd.is_active is not None: gw.is_active = upd.is_active
    await db.commit()
    await db.refresh(gw)
    return gw

@router.post("/{gateway_id}/heartbeat")
async def heartbeat(gateway_id: int, hb: GatewayHeartbeatRequest, db: AsyncSession = Depends(get_db)):
    gw = await db.get(Gateway, gateway_id)
    if not gw: raise HTTPException(status_code=404, detail="Не е намерен")
    gw.last_heartbeat = datetime.utcnow()
    db.add(GatewayHeartbeat(gateway_id=gateway_id, status=hb.status, cpu_usage=hb.cpu_usage, memory_usage=hb.memory_usage, terminal_count=hb.terminal_count, printer_count=hb.printer_count))
    await db.commit()
    return {"status": "ok"}

@router.get("/access/zones", response_model=List[AccessZoneResponse])
@require_module("kiosk")
async def list_zones(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(AccessZone).where(AccessZone.company_id == current_user.company_id))
    return res.scalars().all()

@router.post("/access/zones", response_model=AccessZoneResponse)
@require_module("kiosk")
async def create_zone(zone: AccessZoneCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_z = AccessZone(**zone.model_dump(), company_id=current_user.company_id)
    db.add(new_z)
    await db.commit()
    await db.refresh(new_z)
    return new_z

@router.get("/access/doors", response_model=List[AccessDoorResponse])
@require_module("kiosk")
async def list_doors(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(AccessDoor).join(AccessZone).where(AccessZone.company_id == current_user.company_id))
    return res.scalars().all()

@router.post("/access/doors", response_model=AccessDoorResponse)
@require_module("kiosk")
async def create_door(door: AccessDoorCreate, db: AsyncSession = Depends(get_db)):
    new_d = AccessDoor(**door.model_dump())
    db.add(new_d)
    await db.commit()
    await db.refresh(new_d)
    return new_d

@router.get("/access/logs", response_model=List[AccessLogResponse])
@require_module("kiosk")
async def list_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AccessLog).order_by(AccessLog.timestamp.desc()).limit(limit))
    return res.scalars().all()

@router.post("/access/doors/{door_id}/trigger")
@require_module("kiosk")
async def trigger_door(door_id: int, db: AsyncSession = Depends(get_db)):
    import aiohttp
    door = await db.get(AccessDoor, door_id)
    if not door: raise HTTPException(status_code=404, detail="Не е намерена")
    gw = await db.get(Gateway, door.gateway_id)
    if not gw or not gw.ip_address: raise HTTPException(status_code=400, detail="Gateway офлайн")
    url = f"http://{gw.ip_address}:{gw.terminal_port}/access/doors/{door.door_id}/trigger"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, timeout=5) as r:
                if r.status == 200: return await r.json()
                raise HTTPException(status_code=500, detail="Грешка от gateway")
    except: raise HTTPException(status_code=503, detail="Няма връзка")

class GatewayConfigPush(BaseModel):
    zones: List[dict] = []
    doors: List[dict] = []
    devices: List[dict] = []
    terminals: List[dict] = []
    printers: List[dict] = []

class GatewayConfigPushResponse(BaseModel):
    status: str
    zones_synced: int
    doors_synced: int
    devices_synced: int

from backend.auth.gateway_hmac import require_gateway_auth, verify_timestamp, verify_hmac_signature, create_gateway_signature
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

# Rate limit: 10 requests per minute for gateway endpoints
GATEWAY_RATE_LIMIT = "10/minute"


@router.post("/{gateway_id}/push-config")
@limiter.limit(GATEWAY_RATE_LIMIT)
async def push_gateway_config(
    request: Request,
    gateway_id: int, 
    config: GatewayConfigPush, 
    x_signature: str = Header(..., alias="X-Signature"),
    x_timestamp: str = Header(..., alias="X-Timestamp"),
    db: AsyncSession = Depends(get_db)
):
    # Verify gateway and HMAC
    gateway = await require_gateway_auth(x_signature, x_timestamp, request)
    
    # Verify this gateway matches the URL
    if gateway.id != gateway_id:
        raise HTTPException(status_code=403, detail="Gateway ID mismatch")
    
    gw = gateway
    
    logger.info(f"Syncing config for gateway {gateway_id}. Zones: {len(config.zones)}, Doors: {len(config.doors)}")
    
    zones_synced = 0
    for z_data in config.zones:
        zone_id = z_data.get("id") or z_data.get("zone_id")
        if not zone_id: 
            logger.warning(f"Zone skipped: no ID in {z_data}")
            continue
        
        # Map gateway fields to backend fields
        mapped_data = {
            "zone_id": zone_id,
            "name": z_data.get("name"),
            "level": z_data.get("level", 1),
            "depends_on": z_data.get("depends_on", []),
            "description": z_data.get("description"),
            "is_active": z_data.get("active", True)
        }
        
        # Flatten nested structures
        hours = z_data.get("required_hours", {})
        if hours:
            mapped_data["required_hours_start"] = hours.get("start", "00:00")
            mapped_data["required_hours_end"] = hours.get("end", "23:59")
            
        ap = z_data.get("anti_passback", {})
        if ap:
            mapped_data["anti_passback_enabled"] = ap.get("enabled", False)
            mapped_data["anti_passback_type"] = ap.get("type", "soft")
            mapped_data["anti_passback_timeout"] = ap.get("timeout_minutes", 5)

        res = await db.execute(select(AccessZone).where(AccessZone.zone_id == zone_id))
        existing = res.scalar_one_or_none()
        
        if existing:
            for key, value in mapped_data.items():
                setattr(existing, key, value)
        else:
            db.add(AccessZone(**mapped_data, company_id=gw.company_id or 1))
        zones_synced += 1
    
    # Flush to ensure new zones get IDs for the door sync below
    await db.flush()
    
    # Ensure gateway has a company_id if missing
    if gw.company_id is None:
        gw.company_id = 1
        db.add(gw)
        await db.flush()

    doors_synced = 0
    # Map device status for quick lookup
    device_status = {d.get("device_id"): (d.get("is_online") or d.get("online", False)) for d in config.devices}
    
    for d_data in config.doors:
        door_id = d_data.get("id") or d_data.get("door_id")
        if not door_id: 
            logger.warning(f"Door skipped: no ID in {d_data}")
            continue
        
        # Find zone internal ID
        z_id = d_data.get("zone_id")
        z_res = await db.execute(select(AccessZone.id).where(AccessZone.zone_id == z_id))
        zone_db_id = z_res.scalar_one_or_none()
        
        if not zone_db_id: 
            logger.warning(f"Door {door_id} skipped: zone_id {z_id} not found in backend")
            continue

        dev_id = d_data.get("device_id")
        mapped_door = {
            "door_id": door_id,
            "name": d_data.get("name"),
            "zone_db_id": zone_db_id,
            "gateway_id": gateway_id,
            "device_id": dev_id,
            "relay_number": d_data.get("relay_number", 1),
            "terminal_id": d_data.get("terminal_id"),
            "terminal_mode": d_data.get("terminal_mode", "access"),
            "description": d_data.get("description"),
            "is_active": d_data.get("active", True),
            "is_online": device_status.get(dev_id, False),
            "last_check": datetime.now()
        }

        res = await db.execute(select(AccessDoor).where(AccessDoor.door_id == door_id))
        existing = res.scalar_one_or_none()
        if existing:
            for key, value in mapped_door.items():
                setattr(existing, key, value)
        else:
            db.add(AccessDoor(**mapped_door))
        doors_synced += 1
    
    await db.commit()
    logger.info(f"Sync complete. Synced {zones_synced} zones and {doors_synced} doors.")
    return {"status": "synced", "zones_synced": zones_synced, "doors_synced": doors_synced}

@router.post("/{gateway_id}/pull-config")
@limiter.limit(GATEWAY_RATE_LIMIT)
async def pull_gateway_config(
    request: Request,
    gateway_id: int, 
    x_signature: str = Header(..., alias="X-Signature"),
    x_timestamp: str = Header(..., alias="X-Timestamp"),
    db: AsyncSession = Depends(get_db)
):
    # Verify gateway and HMAC
    gateway = await require_gateway_auth(x_signature, x_timestamp, request)
    
    # Verify this gateway matches the URL
    if gateway.id != gateway_id:
        raise HTTPException(status_code=403, detail="Gateway ID mismatch")
    
    gw = gateway
    
    doors_res = await db.execute(select(AccessDoor).where(AccessDoor.gateway_id == gateway_id))
    doors = doors_res.scalars().all()
    zone_ids = list(set([d.zone_db_id for d in doors]))
    zones = []
    if zone_ids:
        # Load zones with authorized users
        from sqlalchemy.orm import selectinload
        zones_res = await db.execute(
            select(AccessZone)
            .where(AccessZone.id.in_(zone_ids))
            .options(selectinload(AccessZone.authorized_users))
        )
        zones = zones_res.scalars().all()
    
    return {
        "status": "ok",
        "zones": [
            {
                "id": z.zone_id, 
                "name": z.name, 
                "level": z.level, 
                "depends_on": z.depends_on, 
                "authorized_users": [u.id for u in z.authorized_users],
                "required_hours_start": z.required_hours_start, 
                "required_hours_end": z.required_hours_end, 
                "anti_passback_enabled": z.anti_passback_enabled, 
                "anti_passback_type": z.anti_passback_type, 
                "anti_passback_timeout": z.anti_passback_timeout
            } for z in zones
        ],
        "doors": [{"id": d.door_id, "name": d.name, "zone_id": d.zone.zone_id if d.zone else None, "device_id": d.device_id, "relay_number": d.relay_number, "terminal_id": d.terminal_id} for d in doors]
    }

@router.post("/{gateway_id}/sync-push")
@require_module("kiosk")
async def trigger_gateway_push(gateway_id: int, db: AsyncSession = Depends(get_db)):
    import aiohttp
    gw = await db.get(Gateway, gateway_id)
    if not gw or not gw.ip_address: raise HTTPException(status_code=400, detail="Gateway офлайн или без IP")
    
    url = f"http://{gw.ip_address}:{gw.web_port}/sync/push"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, timeout=10) as r:
                if r.status == 200: return await r.json()
                return JSONResponse(status_code=r.status, content=await r.json())
    except Exception as e:
        logger.error(f"Sync push error: {e}")
        raise HTTPException(status_code=503, detail="Няма връзка с Gateway")

@router.post("/{gateway_id}/sync-pull")
@require_module("kiosk")
async def trigger_gateway_pull(gateway_id: int, db: AsyncSession = Depends(get_db)):
    import aiohttp
    gw = await db.get(Gateway, gateway_id)
    if not gw or not gw.ip_address: raise HTTPException(status_code=400, detail="Gateway офлайн или без IP")
    
    url = f"http://{gw.ip_address}:{gw.web_port}/sync/pull"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, timeout=10) as r:
                if r.status == 200: return await r.json()
                return JSONResponse(status_code=r.status, content=await r.json())
    except Exception as e:
        logger.error(f"Sync pull error: {e}")
        raise HTTPException(status_code=503, detail="Няма връзка с Gateway")

@router.post("/{gateway_id}/access/sync-logs")
@limiter.limit("5/minute")  # Stricter limit for log sync
async def sync_logs(
    request: Request,
    gateway_id: int, 
    logs: List[AccessLogSync],
    x_signature: str = Header(..., alias="X-Signature"),
    x_timestamp: str = Header(..., alias="X-Timestamp"),
    db: AsyncSession = Depends(get_db)
):
    # Verify gateway and HMAC
    gateway = await require_gateway_auth(x_signature, x_timestamp, request)
    
    # Verify this gateway matches the URL
    if gateway.id != gateway_id:
        raise HTTPException(status_code=403, detail="Gateway ID mismatch")
    
    for l in logs: 
        db.add(AccessLog(**l.model_dump(), gateway_id=gateway_id))
    await db.commit()
    return {"status": "synced", "count": len(logs)}
