import strawberry
from sqlalchemy import desc, extract, select

from backend import schemas
from backend.crud.repositories import settings_repo
from backend.exceptions import PermissionDeniedException
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"

@strawberry.type
class SystemQuery:
    @strawberry.field
    async def kiosk_security_settings(self, info: strawberry.Info) -> types.KioskSecuritySettings:
        db = info.context["db"]
        current_user = info.context["current_user"]

        # Access check
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
             raise PermissionDeniedException.for_action("access")

        gps = await settings_repo.get_setting(db, "kiosk_require_gps") != "false"
        net = await settings_repo.get_setting(db, "kiosk_require_same_network") != "false"

        return types.KioskSecuritySettings(
            require_gps=gps,
            require_same_network=net,
        )

    @strawberry.field
    async def google_calendar_account(self, info: strawberry.Info) -> types.GoogleCalendarAccount | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            return None

        from backend.database.models import GoogleCalendarAccount
        stmt = select(GoogleCalendarAccount).where(GoogleCalendarAccount.user_id == current_user.id)
        result = await db.execute(stmt)
        account = result.scalars().first()

        if account:
            return types.GoogleCalendarAccount(
                id=account.id,
                email=account.email,
                is_active=account.is_active,
                sync_settings=types.GoogleCalendarSyncSettings(
                    id=account.sync_settings.id,
                    calendar_id=account.sync_settings.calendar_id,
                    sync_work_schedules=account.sync_settings.sync_work_schedules,
                    sync_time_logs=account.sync_settings.sync_time_logs,
                    sync_leave_requests=account.sync_settings.sync_leave_requests,
                    sync_public_holidays=account.sync_settings.sync_public_holidays,
                    sync_direction=account.sync_settings.sync_direction,
                    sync_frequency_minutes=account.sync_settings.sync_frequency_minutes,
                    privacy_level=account.sync_settings.privacy_level,
                ) if account.sync_settings else None,
            )
        return None

    @strawberry.field
    async def audit_logs(
        self,
        info: strawberry.Info,
        skip: int = 0,
        limit: int = 100,
        action: str | None = None,
    ) -> list[types.AuditLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view audit logs")

        from backend.database.models import AuditLog as DbAuditLog
        from backend.database.models import User

        stmt = select(DbAuditLog).join(User, DbAuditLog.user_id == User.id).where(
            User.company_id == current_user.company_id
        )
        if action:
            stmt = stmt.where(DbAuditLog.action == action)

        stmt = stmt.order_by(desc(DbAuditLog.created_at), desc(DbAuditLog.id)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        logs = result.scalars().all()

        return [types.AuditLog.from_pydantic(schemas.AuditLog.model_validate(log)) for log in logs]

    @strawberry.field
    async def api_keys(self, info: strawberry.Info) -> list[types.APIKey]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view API keys")

        res = await settings_repo.get_api_keys(db)
        return [types.APIKey.from_pydantic(k) for k in res]

    @strawberry.field
    async def webhooks(self, info: strawberry.Info) -> list[types.Webhook]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view webhooks")

        res = await settings_repo.get_webhooks(db)
        return [types.Webhook.from_pydantic(w) for w in res]

    @strawberry.field
    async def modules(self, info: strawberry.Info) -> list[types.Module]:
        db = info.context["db"]
        # Public query - no auth required (used for login page to show module status)
        from backend.services.module_service import ModuleService
        res = await ModuleService.get_all_modules(db)
        return [types.Module.from_pydantic(m) for m in res]

    @strawberry.field
    async def password_settings(self, info: strawberry.Info) -> types.PasswordSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name != "super_admin":
            raise PermissionDeniedException.for_action("view password settings")

        return types.PasswordSettings(
            min_length=int(await settings_repo.get_setting(db, "pwd_min_length") or "8"),
            max_length=int(await settings_repo.get_setting(db, "pwd_max_length") or "32"),
            require_upper=(await settings_repo.get_setting(db, "pwd_require_upper")) == "true",
            require_lower=(await settings_repo.get_setting(db, "pwd_require_lower")) == "true",
            require_digit=(await settings_repo.get_setting(db, "pwd_require_digit")) == "true",
            require_special=(await settings_repo.get_setting(db, "pwd_require_special")) == "true",
        )


    @strawberry.field
    async def deploy_status(self, info: strawberry.Info) -> types.DeployStatus:
        from backend.routers.deploy import _deploy_status

        return types.DeployStatus(
            is_deploying=_deploy_status["is_deploying"],
            status=_deploy_status.get("status", "idle"),
            progress=_deploy_status.get("progress", ""),
            version=_deploy_status.get("version"),
            output=_deploy_status.get("output"),
        )

    @strawberry.field
    async def office_location(self, info: strawberry.Info) -> types.OfficeLocation | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
             return None

        lat = await settings_repo.get_setting(db, "office_latitude")
        lon = await settings_repo.get_setting(db, "office_longitude")
        rad = await settings_repo.get_setting(db, "office_radius")
        entry_enabled = await settings_repo.get_setting(db, "geofencing_entry_enabled")
        exit_enabled = await settings_repo.get_setting(db, "geofencing_exit_enabled")

        if not lat or not lon:
            return None

        return types.OfficeLocation(
            latitude=float(lat),
            longitude=float(lon),
            radius=int(rad) if rad else 100,
            entry_enabled=(entry_enabled == "True"),
            exit_enabled=(exit_enabled == "True"),
        )

    @strawberry.field
    async def public_holidays(self, info: strawberry.Info, year: int | None = None) -> list[types.PublicHoliday]:
        db = info.context["db"]

        from backend.database.models import PublicHoliday

        stmt = select(PublicHoliday)
        if year:
            stmt = stmt.where(extract("year", PublicHoliday.date) == year)

        result = await db.execute(stmt)
        return [types.PublicHoliday.from_pydantic(h) for h in result.scalars().all()]

    @strawberry.field
    async def orthodox_holidays(self, info: strawberry.Info, year: int | None = None) -> list[types.OrthodoxHoliday]:
        db = info.context["db"]

        from backend.database.models import OrthodoxHoliday

        stmt = select(OrthodoxHoliday)
        if year:
            stmt = stmt.where(extract("year", OrthodoxHoliday.date) == year)

        result = await db.execute(stmt)
        return [types.OrthodoxHoliday.from_pydantic(h) for h in result.scalars().all()]

    @strawberry.field
    async def session_settings(self, info: strawberry.Info) -> types.SessionSettings:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("view session settings")

        from backend.config import settings

        max_age_str = await settings_repo.get_setting(db, "session_max_age_hours")
        max_age_hours = int(max_age_str) if max_age_str else settings.SESSION_MAX_AGE_HOURS

        return types.SessionSettings(
            max_age_hours=max_age_hours,
        )
