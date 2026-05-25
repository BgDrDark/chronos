from datetime import datetime

from pydantic import EmailStr

from backend.schemas.base import CustomBaseModel


class ModuleBase(CustomBaseModel):
    code: str
    is_enabled: bool
    name: str
    description: str | None = None


class ModuleUpdate(CustomBaseModel):
    is_enabled: bool


class Module(ModuleBase):
    id: int
    updated_at: datetime | None = None


class PasswordSettings(CustomBaseModel):
    min_length: int
    max_length: int
    require_upper: bool
    require_lower: bool
    require_digit: bool
    require_special: bool


class PasswordSettingsUpdate(PasswordSettings):
    pass


class ForgotPasswordRequest(CustomBaseModel):
    email: EmailStr


class ResetPasswordRequest(CustomBaseModel):
    token: str
    new_password: str


class WorkplaceLocationBase(CustomBaseModel):
    company_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    radius_meters: int


class WorkplaceLocationCreate(WorkplaceLocationBase):
    pass


class AuditLog(CustomBaseModel):
    id: int
    user_id: int | None = None
    action: str
    target_type: str | None = None
    target_id: int | None = None
    details: str | None = None
    created_at: datetime


class APIKey(CustomBaseModel):
    id: int
    user_id: int
    name: str
    key_prefix: str
    permissions: list[str] = []
    is_active: bool = True
    created_at: datetime
    last_used_at: datetime | None = None


class Webhook(CustomBaseModel):
    id: int
    url: str
    description: str | None = None
    events: list[str] = []
    is_active: bool = True
    created_at: datetime


class GoogleCalendarSyncSettings(CustomBaseModel):
    id: int
    account_id: int
    calendar_id: str = "primary"
    sync_work_schedules: bool = True
    sync_time_logs: bool = False
    sync_leave_requests: bool = True
    sync_public_holidays: bool = True
    sync_direction: str = "to_google"
    sync_frequency_minutes: int = 15
    privacy_level: str = "title_only"


class GoogleCalendarAccount(CustomBaseModel):
    id: int
    email: str
    is_active: bool = True
    sync_settings: GoogleCalendarSyncSettings | None = None
