from datetime import datetime
from decimal import Decimal

from backend.schemas.base import CustomBaseModel


class TimeLogBase(CustomBaseModel):
    start_time: datetime
    end_time: datetime | None = None
    is_manual: bool
    break_duration_minutes: int
    type: str = "work"
    notes: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    user_id: int


class TimeLog(TimeLogBase):
    id: int
