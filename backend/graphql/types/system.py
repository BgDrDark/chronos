import datetime

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas


@sp.type(schemas.GoogleCalendarSyncSettings)
class GoogleCalendarSyncSettings:
    id: strawberry.auto
    account_id: strawberry.auto
    calendar_id: strawberry.auto
    sync_work_schedules: strawberry.auto
    sync_time_logs: strawberry.auto
    sync_leave_requests: strawberry.auto
    sync_public_holidays: strawberry.auto
    sync_direction: strawberry.auto
    sync_frequency_minutes: strawberry.auto
    privacy_level: strawberry.auto

@strawberry.type
class KioskSecuritySettings:
    require_gps: bool
    require_same_network: bool

@sp.type(schemas.GoogleCalendarAccount)
class GoogleCalendarAccount:
    id: strawberry.auto
    email: strawberry.auto
    is_active: strawberry.auto

    @strawberry.field
    async def sync_settings(self, info: strawberry.Info) -> GoogleCalendarSyncSettings | None:
        db = info.context["db"]
        from backend.database.models import GoogleCalendarAccount as DbAccount
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        stmt = select(DbAccount).where(DbAccount.id == self.id).options(selectinload(DbAccount.sync_settings))
        res = await db.execute(stmt)
        account = res.scalar_one_or_none()
        return GoogleCalendarSyncSettings.from_pydantic(account.sync_settings) if account and account.sync_settings else None

@sp.type(schemas.AuditLog)
class AuditLog:
    id: strawberry.auto
    user_id: strawberry.auto
    action: strawberry.auto
    target_type: strawberry.auto
    target_id: strawberry.auto
    details: strawberry.auto
    created_at: strawberry.auto


@strawberry.type
class AuditLogEdge:
    node: AuditLog
    cursor: str


@strawberry.type
class AuditLogConnection:
    edges: list[AuditLogEdge]
    page_info: "PageInfo"
    total_count: int


@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None


@sp.type(schemas.APIKey)
class APIKey:
    id: strawberry.auto
    user_id: strawberry.auto
    name: strawberry.auto
    key_prefix: strawberry.auto
    permissions: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto
    last_used_at: strawberry.auto


@sp.type(schemas.Webhook)
class Webhook:
    id: strawberry.auto
    url: strawberry.auto
    description: strawberry.auto
    events: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.Module)
class Module:
    id: strawberry.auto
    code: strawberry.auto
    is_enabled: strawberry.auto
    name: strawberry.auto
    description: strawberry.auto


@sp.type(schemas.PasswordSettings)
class PasswordSettings:
    min_length: strawberry.auto
    max_length: strawberry.auto
    require_upper: strawberry.auto
    require_lower: strawberry.auto
    require_digit: strawberry.auto
    require_special: strawberry.auto


@strawberry.type
class DeployStatus:
    is_deploying: bool
    status: str
    progress: str
    version: str | None
    output: str | None


import enum


@strawberry.enum
class PresenceStatus(enum.Enum):
    OFF_DUTY = "off_duty"
    ON_DUTY = "on_duty"
    SICK_LEAVE = "sick_leave"
    PAID_LEAVE = "paid_leave"
    LATE = "late"
    ABSENT = "absent"


@strawberry.type
class OfficeLocation:
    latitude: float
    longitude: float
    radius: int
    entry_enabled: bool
    exit_enabled: bool


@sp.type(schemas.GlobalSetting)
class GlobalSetting:
    key: strawberry.auto
    value: strawberry.auto
