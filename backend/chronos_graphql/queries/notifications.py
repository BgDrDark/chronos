from datetime import datetime
from zoneinfo import ZoneInfo

import strawberry
from sqlalchemy import select

from backend.config import settings
from backend.crud.repositories import settings_repo
from backend.exceptions import PermissionDeniedException
from backend.chronos_graphql import types


@strawberry.type
class NotificationsQuery:
    @strawberry.field
    async def my_notifications(
        self, info: strawberry.Info,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[types.Notification]:
        db = info.context["db"]
        current_user = info.context.get("current_user")
        if not current_user:
            return []

        from backend.services.notification_service import notification_service
        service = notification_service(db)
        notifications = await service.get_notifications(current_user.id, unread_only=unread_only, limit=limit, offset=offset)
        return [types.Notification.from_pydantic(n) for n in notifications]

    @strawberry.field
    async def my_notifications_count(self, info: strawberry.Info, unread_only: bool = False) -> int:
        db = info.context["db"]
        current_user = info.context.get("current_user")
        if not current_user:
            return 0

        from backend.services.notification_service import notification_service
        service = notification_service(db)
        if unread_only:
            return await service.get_unread_count(current_user.id)
        return await service.get_count(current_user.id)

    @strawberry.field
    async def maintenance_status(self, info: strawberry.Info) -> types.MaintenanceStatus:
        from backend.database.models import MaintenanceSettings, User

        db = info.context["db"]
        result = await db.execute(
            select(MaintenanceSettings).order_by(MaintenanceSettings.id.desc()).limit(1),
        )
        setting = result.scalar_one_or_none()

        if not setting:
            return types.MaintenanceStatus(
                enabled=False,
                scheduled_at=None,
                reason="",
                minutes_until=None,
            )

        minutes_until = None
        if setting.scheduled_at and not setting.enabled:
            now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
            diff = setting.scheduled_at - now
            minutes_until = max(0, int(diff.total_seconds() / 60))

        updated_by_user = None
        if setting.updated_by:
            user_result = await db.execute(select(User).where(User.id == setting.updated_by))
            user = user_result.scalar_one_or_none()
            if user:
                updated_by_user = types.User.from_pydantic(user)

        return types.MaintenanceStatus.from_instance(
            setting,
            minutes_until=minutes_until,
            updated_by_user=updated_by_user,
        )

    @strawberry.field
    async def update_schedule(self, info: strawberry.Info) -> types.UpdateScheduleType | None:
        from backend.database.models import UpdateSchedule

        db = info.context["db"]
        result = await db.execute(
            select(UpdateSchedule).order_by(UpdateSchedule.id.desc()).limit(1),
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            return None

        return types.UpdateScheduleType.from_instance(schedule)

    @strawberry.field
    async def smtp_settings(self, info: strawberry.Info) -> types.SmtpSettings | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("view records")

        server = await settings_repo.get_setting(db, "smtp_server")
        port = await settings_repo.get_setting(db, "smtp_port")
        username = await settings_repo.get_setting(db, "smtp_username")
        # Don't return the real password for security, or return it if necessary for editing
        # Usually better to leave blank and only update if provided.
        # But for this simple app, we might return it or a placeholder.
        password = await settings_repo.get_setting(db, "smtp_password")
        sender = await settings_repo.get_setting(db, "sender_email")
        tls = await settings_repo.get_setting(db, "use_tls")

        if not server:
            return None

        return types.SmtpSettings(
            smtp_server=server,
            smtp_port=int(port) if port else 587,
            smtp_username=username or "",
            smtp_password=password or "",
            sender_email=sender or "",
            use_tls=tls == "True",
        )

    @strawberry.field
    async def notification_settings(self, info: strawberry.Info, company_id: int) -> list[types.NotificationSetting]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from backend.database.models import NotificationSetting
        stmt = select(NotificationSetting).where(NotificationSetting.company_id == company_id)
        res = await db.execute(stmt)
        return [types.NotificationSetting.from_pydantic(s) for s in res.scalars().all()]

    @strawberry.field
    async def notification_setting(self, info: strawberry.Info, event_type: str, company_id: int) -> types.NotificationSetting | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view records")

        from backend.database.models import NotificationSetting
        stmt = select(NotificationSetting).where(
            NotificationSetting.event_type == event_type,
            NotificationSetting.company_id == company_id,
        )
        res = await db.execute(stmt)
        setting = res.scalars().first()
        return types.NotificationSetting.from_pydantic(setting) if setting else None

    @strawberry.field
    async def vapid_public_key(self, info: strawberry.Info) -> str | None:
        db = info.context["db"]
        if not info.context["current_user"]:
             return None
        return await settings_repo.get_setting(db, "vapid_public_key")
