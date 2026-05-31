from datetime import datetime

from pydantic import field_validator

from backend.schemas.base import CustomBaseModel


class SmtpSettings(CustomBaseModel):

    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: str
    use_tls: bool


class Notification(CustomBaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool = False
    created_at: datetime


class NotificationSetting(CustomBaseModel):
    id: int
    company_id: int
    event_type: str
    email_enabled: bool = True
    push_enabled: bool = True
    email_template: str | None = None
    recipients: str | None = None
    interval_minutes: int = 60
    enabled: bool = True
    last_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @field_validator("recipients", mode="before")
    @classmethod
    def convert_recipients(cls, v):
        import json
        if isinstance(v, list):
            return json.dumps(v) if v else None
        return v
