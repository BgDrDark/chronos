"""Email service for Chronos ERP.

Provides SMTP configuration from DB GlobalSettings with fallback to config.py,
and email sending functionality used across the application.
"""

import asyncio
import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import GlobalSetting

logger = logging.getLogger(__name__)


async def get_mail_config(db: AsyncSession) -> ConnectionConfig:
    """Get SMTP config from DB GlobalSettings.
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
    use_tls_str = db_settings.get("use_tls", "True")

    # Port 465 = implicit SSL (SMTPS), Port 587/25 = STARTTLS
    if port == 465:
        use_starttls = False
        use_ssl_tls = True
    else:
        use_starttls = use_tls_str.lower() == "true"
        use_ssl_tls = not use_starttls

    return ConnectionConfig(
        MAIL_USERNAME=username or "",
        MAIL_PASSWORD=password or "",
        MAIL_FROM=sender,
        MAIL_PORT=port,
        MAIL_SERVER=server,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=use_starttls,
        MAIL_SSL_TLS=use_ssl_tls,
        USE_CREDENTIALS=bool(username and password),
        VALIDATE_CERTS=True,
    )


async def send_email(
    db: AsyncSession,
    subject: str,
    recipients: list[str],
    body: str,
    html: str | None = None,
) -> bool:
    """Send email using DB SMTP config.

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
        await asyncio.wait_for(fm.send_message(message), timeout=15.0)
        logger.info(f"Email sent to {recipients}: {subject}")
        return True
    except asyncio.TimeoutError:
        logger.error(f"Email send timed out for {recipients}")
        raise
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {e}")
        raise


async def is_smtp_configured(db: AsyncSession) -> bool:
    """Check if SMTP is configured (either in DB or config.py)."""
    stmt = select(GlobalSetting)
    result = await db.execute(stmt)
    db_settings = {s.key: s.value for s in result.scalars().all()}

    server = db_settings.get("smtp_server") or settings.MAIL_SERVER
    username = db_settings.get("smtp_username") or settings.MAIL_USERNAME
    password = db_settings.get("smtp_password") or settings.MAIL_PASSWORD

    return bool(server and username and password)
