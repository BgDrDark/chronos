import datetime
from typing import Optional

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.graphql.types import User


@sp.type(schemas.Notification)
class Notification:
    id: strawberry.auto
    user_id: strawberry.auto
    message: strawberry.auto
    is_read: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.SmtpSettings)
class SmtpSettings:
    smtp_server: strawberry.auto
    smtp_port: strawberry.auto
    smtp_username: strawberry.auto
    smtp_password: strawberry.auto
    sender_email: strawberry.auto
    use_tls: strawberry.auto


@sp.type(schemas.NotificationSetting)
class NotificationSetting:
    id: strawberry.auto
    company_id: strawberry.auto
    event_type: strawberry.auto
    email_enabled: strawberry.auto
    push_enabled: strawberry.auto
    email_template: strawberry.auto
    recipients: strawberry.auto
    interval_minutes: strawberry.auto
    enabled: strawberry.auto
    last_sent_at: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry.type
class MaintenanceStatus:
    enabled: bool
    scheduled_at: datetime.datetime | None
    reason: str
    minutes_until: int | None
    updated_by: Optional["User"] = None

    @classmethod
    def from_instance(cls, instance, minutes_until: int | None = None, updated_by_user=None) -> "MaintenanceStatus":
        return cls(
            enabled=instance.enabled,
            scheduled_at=instance.scheduled_at,
            reason=instance.reason,
            minutes_until=minutes_until,
            updated_by=updated_by_user,
        )


@strawberry.type
class UpdateScheduleType:
    id: int
    enabled: bool
    schedule_type: str
    scheduled_at: datetime.datetime | None
    day_of_week: int | None
    hour: int
    minute: int
    notify_email: str
    last_run_at: datetime.datetime | None
    last_run_status: str | None
    last_run_output: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_instance(cls, instance) -> "UpdateScheduleType":
        return cls(
            id=instance.id,
            enabled=instance.enabled,
            schedule_type=instance.schedule_type,
            scheduled_at=instance.scheduled_at,
            day_of_week=instance.day_of_week,
            hour=instance.hour,
            minute=instance.minute,
            notify_email=instance.notify_email,
            last_run_at=instance.last_run_at,
            last_run_status=instance.last_run_status,
            last_run_output=instance.last_run_output,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


__all__ = [
    "MaintenanceStatus",
    "Notification",
    "NotificationSetting",
    "SmtpSettings",
    "UpdateScheduleType",
]
