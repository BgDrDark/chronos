from datetime import datetime

from backend.schemas.base import CustomBaseModel


class AccessZone(CustomBaseModel):
    id: int
    zone_id: str
    name: str
    level: int
    depends_on: list[str] = []
    required_hours_start: str = "00:00"
    required_hours_end: str = "23:59"
    anti_passback_enabled: bool = False
    anti_passback_type: str = "soft"
    anti_passback_timeout: int = 5
    description: str | None = None
    is_active: bool = True
    company_id: int


class AccessDoor(CustomBaseModel):
    id: int
    door_id: str
    name: str
    zone_db_id: int
    gateway_id: int
    device_id: str
    relay_number: int = 1
    terminal_id: str | None = None
    terminal_mode: str = "access"
    description: str | None = None
    is_active: bool = True
    is_online: bool = False
    last_check: datetime | None = None


class AccessCode(CustomBaseModel):
    id: int
    code: str
    code_type: str = "one_time"
    zones: list[str] = []
    uses_remaining: int = 1
    expires_at: datetime | None = None
    created_at: datetime
    last_used_at: datetime | None = None
    created_by: int | None = None
    is_active: bool = True
    gateway_id: int | None = None


class AccessLog(CustomBaseModel):
    id: int
    timestamp: datetime
    user_id: str | None = None
    user_name: str | None = None
    zone_id: str | None = None
    zone_name: str | None = None
    door_id: str | None = None
    door_name: str | None = None
    action: str
    result: str
    reason: str | None = None
    method: str
    terminal_id: str | None = None
    gateway_id: int
