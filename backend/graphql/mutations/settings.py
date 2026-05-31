import logging

import strawberry
from sqlalchemy import update

from backend.crud import repositories as crud
from backend.crud.repositories import settings_repo
from backend.database import models
from backend.graphql import inputs, types
from backend.graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


async def force_password_change_for_all_users(db):
    await db.execute(
        update(models.User).values(password_force_change=True)
    )


@strawberry.type
class SettingsMutation:
    @strawberry.mutation
    async def set_global_setting(
        self, key: str, value: str, info: strawberry.Info
    ) -> types.GlobalSetting:
        db = info.context["db"]
        get_current_user(info)

        setting = await settings_repo.set_setting(db, key, value)
        await db.commit()
        return types.GlobalSetting.from_instance(setting)

    @strawberry.mutation
    async def update_password_settings(
        self,
        settings: inputs.PasswordSettingsInput,
        info: strawberry.Info,
    ) -> types.PasswordSettings:
        db = info.context["db"]
        get_current_user(info)

        await settings_repo.set_setting(db, "pwd_min_length", str(settings.min_length))
        await settings_repo.set_setting(db, "pwd_max_length", str(settings.max_length))
        await settings_repo.set_setting(
            db, "pwd_require_upper", "true" if settings.require_upper else "false"
        )
        await settings_repo.set_setting(
            db, "pwd_require_lower", "true" if settings.require_lower else "false"
        )
        await settings_repo.set_setting(
            db, "pwd_require_digit", "true" if settings.require_digit else "false"
        )
        await settings_repo.set_setting(
            db, "pwd_require_special", "true" if settings.require_special else "false"
        )

        current_version = int(
            await settings_repo.get_setting(db, "password_settings_version") or "0"
        )
        await settings_repo.set_setting(
            db, "password_settings_version", str(current_version + 1)
        )

        await force_password_change_for_all_users(db)

        await db.commit()
        return types.PasswordSettings(
            min_length=settings.min_length,
            max_length=settings.max_length,
            require_upper=settings.require_upper,
            require_lower=settings.require_lower,
            require_digit=settings.require_digit,
            require_special=settings.require_special,
        )

    @strawberry.mutation
    async def update_security_config(
        self,
        max_login_attempts: int,
        lockout_minutes: int,
        info: strawberry.Info,
    ) -> bool:
        db = info.context["db"]
        get_current_user(info)

        await settings_repo.set_setting(
            db, "max_login_attempts", str(max_login_attempts)
        )
        await settings_repo.set_setting(db, "lockout_minutes", str(lockout_minutes))
        await db.commit()
        return True

    @strawberry.mutation
    async def update_kiosk_security_settings(
        self,
        require_gps: bool,
        require_same_network: bool,
        info: strawberry.Info,
    ) -> bool:
        db = info.context["db"]
        get_current_user(info)

        await settings_repo.set_setting(
            db, "kiosk_require_gps", "true" if require_gps else "false"
        )
        await settings_repo.set_setting(
            db,
            "kiosk_require_same_network",
            "true" if require_same_network else "false",
        )
        await db.commit()
        return True

    @strawberry.mutation
    async def update_google_calendar_settings(
        self,
        sync_work_schedules: bool,
        sync_time_logs: bool,
        sync_leave_requests: bool,
        sync_public_holidays: bool,
        privacy_level: str,
        info: strawberry.Info,
    ) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)

        await crud.update_google_calendar_sync_settings(
            db,
            user_id=current_user.id,
            sync_work_schedules=sync_work_schedules,
            sync_time_logs=sync_time_logs,
            sync_leave_requests=sync_leave_requests,
            sync_public_holidays=sync_public_holidays,
            privacy_level=privacy_level,
        )
        return True

    @strawberry.mutation
    async def disconnect_google_calendar(self, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)

        await crud.disconnect_google_calendar(db, current_user.id)
        return True

    @strawberry.mutation
    async def bulk_emergency_action(
        self, action: str, info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        current_user = get_current_user(info)

        await db.execute(
            update(models.Gateway)
            .where(models.Gateway.company_id == current_user.company_id)
            .values(system_mode=action)
        )

        log = models.AuditLog(
            user_id=current_user.id,
            action=f"EMERGENCY_{action.upper()}",
            target_type="System",
            details=f"Групово действие: {action}",
        )
        db.add(log)
        await db.commit()
        return True
