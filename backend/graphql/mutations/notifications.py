import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import strawberry
from sqlalchemy import select

from backend.config import settings
from backend.crud.repositories import settings_repo
from backend.database.models import NotificationSetting
from backend.exceptions import (
    ValidationException,
)
from backend.graphql import inputs, types
from backend.graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


@strawberry.type
class NotificationsMutation:
    @strawberry.mutation
    async def mark_notification_read(
        self,
        info: strawberry.Info,
        id: int,
    ) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.services.notification_service import notification_service
        service = notification_service(db)
        await service.mark_as_read(id, current_user.id)
        return True

    @strawberry.mutation(name="subscribeToPush")
    async def subscribe_to_push(
        self,
        info: strawberry.Info,
        subscription_json: str,
        preferences_json: str,
    ) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)

        try:
            sub_data = json.loads(subscription_json)
            prefs = json.loads(preferences_json)
        except json.JSONDecodeError as e:
            raise ValidationException.field("subscription_json", f"Invalid JSON: {e}") from e

        endpoint = sub_data.get("endpoint")
        keys = sub_data.get("keys", {})
        p256dh = keys.get("p256dh")
        auth_key = keys.get("auth")

        if not endpoint or not p256dh or not auth_key:
            raise ValidationException.required_field("endpoint, keys.p256dh, keys.auth")

        try:
            from backend.services.notification_service import notification_service
            service = notification_service(db)
            subscription = await service.subscribe(
                user_id=current_user.id,
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth_key,
            )

            subscription.preferences = prefs
            await db.commit()

            logger.info(f"User {current_user.id} subscribed to push notifications")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to push notifications: {e}")
            await db.rollback()
            raise ValidationException.field("subscription", f"Failed to save subscription: {e}") from e

    @strawberry.mutation
    async def schedule_maintenance(self, info: strawberry.Info, input: inputs.MaintenanceInput) -> bool:
        from backend.database.models import MaintenanceSettings

        db = info.context["db"]
        current_user = get_current_user(info)

        now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        scheduled_at = None
        if input.delay_minutes > 0:
            scheduled_at = now + timedelta(minutes=input.delay_minutes)

        result = await db.execute(select(MaintenanceSettings).order_by(MaintenanceSettings.id.desc()).limit(1))
        setting = result.scalar_one_or_none()

        if setting:
            setting.enabled = input.enabled
            setting.scheduled_at = scheduled_at
            setting.reason = input.reason
            setting.updated_by = current_user.id
            setting.updated_at = now
        else:
            setting = MaintenanceSettings(
                enabled=input.enabled,
                scheduled_at=scheduled_at,
                reason=input.reason,
                updated_by=current_user.id,
                updated_at=now,
            )
            db.add(setting)

        await db.commit()
        return True

    @strawberry.mutation
    async def cancel_maintenance(self, info: strawberry.Info) -> bool:
        from backend.database.models import MaintenanceSettings

        db = info.context["db"]
        current_user = get_current_user(info)

        now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        result = await db.execute(select(MaintenanceSettings).order_by(MaintenanceSettings.id.desc()).limit(1))
        setting = result.scalar_one_or_none()

        if setting:
            setting.enabled = False
            setting.scheduled_at = None
            setting.updated_by = current_user.id
            setting.updated_at = now
            await db.commit()

        return True

    @strawberry.mutation
    async def set_update_schedule(self, info: strawberry.Info, input: inputs.UpdateScheduleInput) -> types.UpdateScheduleType:
        from backend.database.models import UpdateSchedule

        db = info.context["db"]
        get_current_user(info)

        now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)

        result = await db.execute(select(UpdateSchedule).order_by(UpdateSchedule.id.desc()).limit(1))
        schedule = result.scalar_one_or_none()

        if schedule:
            schedule.enabled = input.enabled
            schedule.schedule_type = input.schedule_type
            schedule.scheduled_at = input.scheduled_at
            schedule.day_of_week = input.day_of_week
            schedule.hour = input.hour
            schedule.minute = input.minute
            schedule.notify_email = input.notify_email
            schedule.updated_at = now
        else:
            schedule = UpdateSchedule(
                enabled=input.enabled,
                schedule_type=input.schedule_type,
                scheduled_at=input.scheduled_at,
                day_of_week=input.day_of_week,
                hour=input.hour,
                minute=input.minute,
                notify_email=input.notify_email,
            )
            db.add(schedule)

        await db.commit()
        await db.refresh(schedule)
        return types.UpdateScheduleType.from_instance(schedule)

    @strawberry.mutation
    async def run_update_now(self, info: strawberry.Info) -> str:
        import os

        import httpx

        from backend.database.models import UpdateSchedule
        from backend.services.update_service import update_service

        db = info.context["db"]
        get_current_user(info)

        service = update_service(db)

        update_info = await service.check_for_updates()
        if not update_info.get("has_update"):
            return f"No update available. Current: {update_info.get('current_version')}"

        latest_version = update_info["latest_version"]
        deploy_key = settings.get_deploy_key()

        if not deploy_key:
            return "Deploy API key not configured. Cannot trigger update."

        deploy_url = os.environ.get("DEPLOY_MANAGER_URL") or os.environ.get("DEPLOY_LISTENER_URL") or "http://host.docker.internal:14241"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{deploy_url}/deploy",
                    json={"version": latest_version},
                    headers={"Authorization": f"UpdateKey {deploy_key}"},
                )
                if response.status_code != 200:
                    logger.error(f"Deploy trigger failed: {response.status_code} - {response.text}")
                    return f"Deploy trigger failed: HTTP {response.status_code}"
        except Exception as e:
            logger.error(f"Deploy listener unavailable at {deploy_url}: {e}")
            return f"Deploy listener unavailable at {deploy_url}. Ensure chronos-update-listener is running."

        schedule_result = await db.execute(select(UpdateSchedule).order_by(UpdateSchedule.id.desc()).limit(1))
        schedule = schedule_result.scalar_one_or_none()

        now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        if schedule:
            schedule.last_run_at = now
            schedule.last_run_status = "started"
            schedule.last_run_output = f"Update to {latest_version} triggered at {now.isoformat()}"
            await db.commit()

        return f"Update to {latest_version} started. Check deploy status for progress."

    @strawberry.mutation
    async def update_smtp_settings(
            self,
            settings: inputs.SmtpSettingsInput,
            info: strawberry.Info,
    ) -> types.SmtpSettings:
        db = info.context["db"]
        get_current_user(info)

        if not settings.smtp_server or not settings.sender_email:
            raise ValidationException.required_field("Server and Sender Email")

        await settings_repo.set_setting(db, "smtp_server", settings.smtp_server)
        await settings_repo.set_setting(db, "smtp_port", str(settings.smtp_port))
        await settings_repo.set_setting(db, "smtp_username", settings.smtp_username)
        await settings_repo.set_setting(db, "smtp_password", settings.smtp_password)
        await settings_repo.set_setting(db, "sender_email", settings.sender_email)
        await settings_repo.set_setting(db, "use_tls", str(settings.use_tls))
        await db.commit()

        return types.SmtpSettings(
            smtp_server=settings.smtp_server,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            sender_email=settings.sender_email,
            use_tls=settings.use_tls,
        )

    @strawberry.mutation
    async def save_notification_setting(
            self,
            setting_data: inputs.NotificationSettingInput,
            info: strawberry.Info,
    ) -> types.NotificationSetting:
        db = info.context["db"]
        get_current_user(info)

        # Check if setting exists
        stmt = select(NotificationSetting).where(
            NotificationSetting.event_type == setting_data.event_type,
            NotificationSetting.company_id == setting_data.company_id,
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()

        recipients = None
        if setting_data.recipients:
            try:
                recipients = json.loads(setting_data.recipients)
            except Exception:
                recipients = []

        if existing:
            existing.email_enabled = setting_data.email_enabled
            existing.push_enabled = setting_data.push_enabled
            existing.email_template = setting_data.email_template
            existing.recipients = recipients
            existing.interval_minutes = setting_data.interval_minutes
            existing.enabled = setting_data.enabled
            await db.commit()
            await db.refresh(existing)
            return types.NotificationSetting.from_pydantic(existing)
        new_setting = NotificationSetting(
            company_id=setting_data.company_id,
            event_type=setting_data.event_type,
            email_enabled=setting_data.email_enabled,
            push_enabled=setting_data.push_enabled,
            email_template=setting_data.email_template,
            recipients=recipients,
            interval_minutes=setting_data.interval_minutes,
            enabled=setting_data.enabled,
        )
        db.add(new_setting)
        await db.commit()
        await db.refresh(new_setting)
        return types.NotificationSetting.from_pydantic(new_setting)

    @strawberry.mutation
    async def mark_all_notifications_read(self, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.services.notification_service import notification_service
        service = notification_service(db)
        await service.mark_all_as_read(current_user.id)
        return True

    @strawberry.mutation
    async def delete_notification(self, info: strawberry.Info, id: int) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.services.notification_service import notification_service
        service = notification_service(db)
        return await service.delete_notification(id, current_user.id)

    @strawberry.mutation
    async def test_notification(
            self,
            info: strawberry.Info,
            event_type: str,
            recipient_email: str | None = None,
    ) -> bool:
        """Send a test notification email"""
        db = info.context["db"]
        current_user = get_current_user(info)

        from backend.services.email_service import is_smtp_configured, send_email

        if not await is_smtp_configured(db):
            raise ValidationException.field("smtp", "SMTP is not configured. Please configure SMTP settings first.")

        target_email = recipient_email or current_user.email
        if not target_email:
            raise ValidationException.field("email", "No recipient email provided and current user has no email address.")

        body = (
            f"<h2>Тестово уведомление</h2>"
            f"<p>Това е тест за event type: <strong>{event_type}</strong></p>"
            f"<p>Ако получавате този имейл, SMTP настройките работят правилно.</p>"
            f"<p>Изпратено до: {target_email}</p>"
        )

        try:
            await send_email(
                db=db,
                subject=f"Chronos - Тестово уведомление ({event_type})",
                recipients=[target_email],
                body=body,
                html=body,
            )
            logger.info(f"Test notification sent to {target_email} for event_type: {event_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            raise ValidationException.field("email", f"Failed to send test email: {e}") from e
