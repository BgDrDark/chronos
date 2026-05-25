"""Notification Dispatcher for Chronos ERP.

Dispatches notifications based on NotificationSettings for each event type.
Handles email, push, and in-app notifications with interval throttling.
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import NotificationSetting, Role, User
from backend.services.email_service import send_email
from backend.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """Dispatches notifications based on company NotificationSettings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def dispatch(
        self,
        event_type: str,
        company_id: int,
        event_details: str,
        user_id: int | None = None,
    ) -> dict[str, int]:
        """Dispatch notification based on settings for the given event type.

        Args:
            event_type: The type of event (e.g., 'leave_approved', 'shift_swap')
            company_id: The company ID to look up settings for
            event_details: Human-readable description of the event
            user_id: Optional specific user to notify (in addition to settings recipients)

        Returns:
            Dict with counts: {'emails_sent': int, 'pushes_sent': int, 'in_app_created': int}

        """
        result = {"emails_sent": 0, "pushes_sent": 0, "in_app_created": 0}

        setting = await self._get_setting(event_type, company_id)
        if not setting or not setting.enabled:
            logger.debug(f"No enabled setting for event_type={event_type}, company_id={company_id}")
            return result

        if not await self._check_interval(setting):
            logger.debug(f"Interval throttled for event_type={event_type}")
            return result

        recipients = await self._get_recipients(setting, company_id, user_id)
        if not recipients["emails"] and not recipients["user_ids"]:
            logger.debug(f"No recipients for event_type={event_type}")
            return result

        if setting.email_enabled and setting.email_template and recipients["emails"]:
            body = self._render_template(setting.email_template, event_type, event_details)
            for email in recipients["emails"]:
                try:
                    sent = await send_email(
                        db=self.db,
                        subject=f"Chronos - {event_type}",
                        recipients=[email],
                        body=body,
                        html=body,
                    )
                    if sent:
                        result["emails_sent"] += 1
                except Exception as e:
                    logger.error(f"Email failed for {event_type} to {email}: {e}")

        if setting.push_enabled and recipients["user_ids"]:
            service = notification_service(self.db)
            for uid in recipients["user_ids"]:
                try:
                    sent = await service.send(
                        user_id=uid,
                        title=f"Chronos - {event_type}",
                        body=event_details,
                    )
                    result["pushes_sent"] += sent
                except Exception as e:
                    logger.error(f"Push failed for {event_type} to user {uid}: {e}")

        for uid in recipients["user_ids"]:
            try:
                service = notification_service(self.db)
                await service.create_notification(
                    user_id=uid,
                    message=f"{event_type}: {event_details}",
                )
                result["in_app_created"] += 1
            except Exception as e:
                logger.error(f"In-app notification failed for {event_type} to user {uid}: {e}")

        setting.last_sent_at = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        await self.db.commit()

        logger.info(
            f"Dispatched {event_type}: {result['emails_sent']} emails, "
            f"{result['pushes_sent']} pushes, {result['in_app_created']} in-app",
        )
        return result

    async def _get_setting(
        self, event_type: str, company_id: int,
    ) -> NotificationSetting | None:
        """Get notification setting for event type and company."""
        stmt = select(NotificationSetting).where(
            NotificationSetting.event_type == event_type,
            NotificationSetting.company_id == company_id,
            NotificationSetting.enabled,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _check_interval(self, setting: NotificationSetting) -> bool:
        """Check if enough time has passed since last notification."""
        if setting.last_sent_at:
            now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
            elapsed = now - setting.last_sent_at
            if elapsed < timedelta(minutes=setting.interval_minutes):
                return False
        return True

    async def _get_recipients(
        self,
        setting: NotificationSetting,
        company_id: int,
        user_id: int | None = None,
    ) -> dict[str, list]:
        """Resolve recipients from setting configuration."""
        emails: list[str] = []
        user_ids: list[int] = []

        if setting.recipients:
            for recipient in setting.recipients:
                r_type = recipient.get("type")
                r_value = recipient.get("value")
                if not r_value:
                    continue

                if r_type == "email":
                    emails.append(r_value)
                elif r_type == "role":
                    role_users = await self._get_users_by_role(r_value, company_id)
                    for user in role_users:
                        user_ids.append(user.id)
                        if user.email:
                            emails.append(user.email)
        else:
            all_users = await self._get_all_active_users(company_id)
            for user in all_users:
                user_ids.append(user.id)
                if user.email:
                    emails.append(user.email)

        if user_id and user_id not in user_ids:
            user_ids.append(user_id)
            user_res = await self.db.execute(
                select(User).where(User.id == user_id),
            )
            user = user_res.scalars().first()
            if user and user.email:
                emails.append(user.email)

        return {
            "emails": list(set(emails)),
            "user_ids": list(set(user_ids)),
        }

    async def _get_users_by_role(self, role_name: str, company_id: int) -> list[User]:
        """Get active users with a specific role in a company."""
        stmt = select(User).where(
            User.company_id == company_id,
            User.is_active,
            User.role_id.in_(
                select(Role.id).where(Role.name == role_name),
            ),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_all_active_users(self, company_id: int) -> list[User]:
        """Get all active users in a company."""
        stmt = select(User).where(
            User.company_id == company_id,
            User.is_active,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _render_template(template: str, event_type: str, event_details: str) -> str:
        """Render email template with variables."""
        return (
            template
            .replace("{{event_type}}", event_type)
            .replace("{{event_details}}", event_details)
        )
