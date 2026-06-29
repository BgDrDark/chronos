from datetime import datetime

from backend.schemas.base import CustomBaseModel


class EmergencyEvent(CustomBaseModel):
    id: int
    event_type: str
    scope: str = "all"
    gateway_id: int | None = None
    zone_id: int | None = None
    triggered_by: int | None = None
    triggered_at: datetime | None = None
    resolved_at: datetime | None = None
    resolved_by: int | None = None
    is_active: bool = True
    notes: str | None = None


class EmergencyTriggerInput(CustomBaseModel):
    event_type: str
    scope: str = "all"
    gateway_id: int | None = None
    zone_id: int | None = None
    notes: str | None = None
