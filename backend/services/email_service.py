"""
Email service for Chronos ERP.

Provides SMTP configuration from DB GlobalSettings with fallback to config.py,
and email sending functionality used across the application.
"""

import logging
from typing import Optional, List

from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import GlobalSetting
from backend.config import settings

logger = logging.getLogger(__name__)


async def get_mail_config(db: AsyncSession) -> ConnectionConfig:
    """
    Get SMTP config from DB GlobalSettings.
    Falls back to config.py settings if DB values are missing.
    """
    stmt = select(GlobalSetting)
    result = await db.execute(stmt)
    db_settings = {s.key: s.value for s in result.scalars().all()}

    server = db_settings.get("smtp_server") or settings.MAIL_SERVER
    port = int(db_settings.get("smtp_port") or settings.MAIL_PORT)
    username = db_settings.get("smtp_username") or settings.MAIL_USERNAME
    password = db_settings.get("smtp_password") or settings.MAIL_PASSWORD
    sender = db_settings.get("sender_email") or settings.MAIL_FROM
    use_tls = db_settings.get("use_tls", "True").lower() == "true"

    return ConnectionConfig(
        MAIL_USERNAME=username or "",
        MAIL_PASSWORD=password or "",
        MAIL_FROM=sender,
        MAIL_PORT=port,
        MAIL_SERVER=server,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=use_tls,
        MAIL_SSL_TLS=not use_tls,
        USE_CREDENTIALS=bool(username and password),
        VALIDATE_CERTS=True,
    )


async def send_email(
    db: AsyncSession,
    subject: str,
    recipients: List[str],
    body: str,
    html: Optional[str] = None,
) -> bool:
    """
    Send email using DB SMTP config.

    Args:
        db: Database session
        subject: Email subject
        recipients: List of recipient email addresses
        body: Plain text body
        html: Optional HTML body (if provided, used instead of body)

    Returns:
        True if email was sent successfully, False otherwise.
    """
    try:
        config = await get_mail_config(db)
        fm = FastMail(config)

        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html or body,
            subtype=MessageType.html if html else MessageType.plain,
        )
        await fm.send_message(message)
        logger.info(f"Email sent to {recipients}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {e}")
        return False


async def is_smtp_configured(db: AsyncSession) -> bool:
    """Check if SMTP is configured (either in DB or config.py)."""
    stmt = select(GlobalSetting)
    result = await db.execute(stmt)
    db_settings = {s.key: s.value for s in result.scalars().all()}

    server = db_settings.get("smtp_server") or settings.MAIL_SERVER
    username = db_settings.get("smtp_username") or settings.MAIL_USERNAME
    password = db_settings.get("smtp_password") or settings.MAIL_PASSWORD

    return bool(server and username and password)
