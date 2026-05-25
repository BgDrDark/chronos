from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud.repositories import settings_repo, user_repo
from backend.database.models import User, UserSession, sofia_now


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = user_repo
        self.settings = settings_repo

    async def increment_login_attempts(self, user_id: int) -> User | None:
        user = await self.repo.get_by_id(self.db, user_id)
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            max_attempts_str = await self.settings.get_setting(self.db, "security_max_login_attempts")
            max_attempts = int(max_attempts_str) if max_attempts_str else 5

            lockout_mins_str = await self.settings.get_setting(self.db, "security_lockout_minutes")
            lockout_mins = int(lockout_mins_str) if lockout_mins_str else 15

            if user.failed_login_attempts >= max_attempts:
                user.locked_until = sofia_now() + timedelta(minutes=lockout_mins)

            await self.db.flush()
            await self.db.refresh(user)
        return user

    async def reset_login_attempts(self, user_id: int) -> User | None:
        user = await self.repo.get_by_id(self.db, user_id)
        if user:
            if user.failed_login_attempts != 0 or user.locked_until is not None:
                user.failed_login_attempts = 0
                user.locked_until = None
                await self.db.flush()
        return user

    async def check_account_locked(self, user_id: int) -> bool:
        user = await self.repo.get_by_id(self.db, user_id)
        if not user:
            return False
        return bool(user.locked_until and user.locked_until > sofia_now())

    async def create_user_session(
        self,
        user_id: int,
        refresh_token_jti: str,
        expires_at: datetime,
        ip_address: str = None,
        user_agent: str = None,
    ) -> UserSession:
        return await self.repo.create_user_session(
            self.db,
            user_id=user_id,
            refresh_token_jti=refresh_token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )

    async def get_active_sessions(self, user_id: int) -> list[UserSession]:
        sessions = await self.repo.get_active_sessions(self.db, user_id)
        return [s for s in sessions if s.expires_at > sofia_now()]

    async def invalidate_session(self, session_id: int) -> bool:
        session = await self.repo.get_user_session_by_id(self.db, session_id)
        if session:
            session.is_active = False
            await self.db.flush()
            return True
        return False

    async def invalidate_all_sessions(self, user_id: int) -> int:
        return await self.repo.invalidate_all_user_sessions(self.db, user_id)

    async def cleanup_expired_sessions(self, retention_days: int = 30) -> int:
        return await self.repo.cleanup_expired_sessions(self.db, retention_days)

    async def cleanup_old_auth_keys(self, retention_days: int = 90) -> int:
        cutoff_date = sofia_now() - timedelta(days=retention_days)
        from sqlalchemy import delete

        from backend.database.models import AuthKey
        result = await self.db.execute(
            delete(AuthKey).where(
                AuthKey.state == "legacy",
                AuthKey.created_at < cutoff_date,
            ),
        )
        await self.db.commit()
        return result.rowcount

    async def force_password_change_for_all_users(self) -> int:
        users = await self.repo.get_all(self.db)
        count = 0
        for user in users:
            user.must_change_password = True
            count += 1
        if count > 0:
            await self.db.flush()
        return count

    async def regenerate_qr_token(self, user_id: int) -> str:
        return await self.repo.regenerate_qr_token(self.db, user_id)


auth_service = AuthService


async def force_password_change_for_all_users(db: AsyncSession) -> int:
    """Force password change for all users"""
    service = AuthService(db)
    return await service.force_password_change_for_all()


async def regenerate_user_qr_token(db: AsyncSession, user_id: int) -> str:
    """Regenerate QR token for a user"""
    service = AuthService(db)
    return await service.regenerate_qr_token(user_id)
