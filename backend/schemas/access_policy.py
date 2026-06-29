from datetime import datetime

from backend.config import settings
from backend.schemas.base import CustomBaseModel


class AccessLevel(CustomBaseModel):
    id: int
    name: str
    description: str | None = None
    company_id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class AccessLevelZone(CustomBaseModel):
    id: int
    access_level_id: int
    zone_id: int
    schedule_id: int | None = None
    out_of_hours_behavior: str = "deny"
    priority: int = 0


class AccessSchedule(CustomBaseModel):
    id: int
    name: str
    company_id: int
    timezone: str = settings.TIMEZONE
    config: dict = {}
    holiday_override_auto: bool = True
    is_active: bool = True
    created_at: datetime
