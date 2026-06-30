import datetime

import strawberry


@strawberry.input
class SmtpSettingsInput:
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: str
    use_tls: bool


@strawberry.input
class NotificationSettingInput:
    id: int | None = None
    event_type: str
    email_enabled: bool = True
    push_enabled: bool = True
    email_template: str | None = None
    recipients: str | None = None
    interval_minutes: int = 60
    enabled: bool = True
    company_id: int


@strawberry.input
class MaintenanceInput:
    enabled: bool
    delay_minutes: int = 0
    reason: str = ""


@strawberry.input
class UpdateScheduleInput:
    enabled: bool = False
    schedule_type: str = "once"
    scheduled_at: datetime.datetime | None = None
    day_of_week: int | None = None
    hour: int = 3
    minute: int = 0
    notify_email: str = ""
