from typing import Optional, List
from datetime import datetime, timedelta
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.database.models import User, UserSession, AuthKey, GlobalSetting
from backend.database.models import sofia_now


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def increment_login_attempts(self, user_id: int) -> Optional[User]:
        """Increment failed login attempts and lock user if needed"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            max_attempts_str = await self._get_setting("security_max_login_attempts")
            max_attempts = int(max_attempts_str) if max_attempts_str else 5

            lockout_mins_str = await self._get_setting("security_lockout_minutes")
            lockout_mins = int(lockout_mins_str) if lockout_mins_str else 15

            if user.failed_login_attempts >= max_attempts:
                user.locked_until = sofia_now() + timedelta(minutes=lockout_mins)

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        
        return user

    async def reset_login_attempts(self, user_id: int) -> Optional[User]:
        """Reset failed login attempts after successful login"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if user:
            if user.failed_login_attempts != 0 or user.locked_until is not None:
                user.failed_login_attempts = 0
                user.locked_until = None
                self.db.add(user)
                await self.db.commit()
        
        return user

    async def check_account_locked(self, user_id: int) -> bool:
        """Check if account is currently locked"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return False
        
        if user.locked_until and user.locked_until > sofia_now():
            return True
        
        return False

    async def create_user_session(
        self,
        user_id: int,
        refresh_token_jti: str,
        expires_at: datetime,
        ip_address: str = None,
        user_agent: str = None
    ) -> UserSession:
        """Create a new user session"""
        session = UserSession(
            user_id=user_id,
            refresh_token_jti=refresh_token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_active_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for user"""
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > sofia_now()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def invalidate_session(self, session_id: int) -> bool:
        """Invalidate a specific session"""
        stmt = select(UserSession).where(UserSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalars().first()
        
        if session:
            session.is_active = False
            self.db.add(session)
            await self.db.commit()
            return True
        
        return False

    async def invalidate_all_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user (logout everywhere)"""
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()
        
        count = 0
        for session in sessions:
            session.is_active = False
            self.db.add(session)
            count += 1
        
        if count > 0:
            await self.db.commit()
        
        return count

    async def cleanup_expired_sessions(self, retention_days: int = 30) -> int:
        """Clean up expired sessions older than retention_days"""
        cutoff_date = sofia_now() - timedelta(days=retention_days)
        
        result = await self.db.execute(
            delete(UserSession).where(
                UserSession.expires_at < cutoff_date
            )
        )
        await self.db.commit()
        
        return result.rowcount

    async def cleanup_old_auth_keys(self, retention_days: int = 90) -> int:
        """Delete legacy auth keys older than retention_days"""
        cutoff_date = sofia_now() - timedelta(days=retention_days)
        
        result = await self.db.execute(
            delete(AuthKey).where(
                AuthKey.state == "legacy",
                AuthKey.created_at < cutoff_date
            )
        )
        await self.db.commit()
        
        return result.rowcount

    async def force_password_change_for_all_users(self) -> int:
        """Force all users to change password on next login"""
        stmt = select(User)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        count = 0
        for user in users:
            user.must_change_password = True
            self.db.add(user)
            count += 1
        
        if count > 0:
            await self.db.commit()
        
        return count

    async def regenerate_qr_token(self, user_id: int) -> str:
        """Regenerate QR token for a user"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        user.qr_token = str(uuid.uuid4())
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user.qr_token

    async def _get_setting(self, key: str) -> Optional[str]:
        """Get global setting value"""
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()
        return setting.value if setting else None


auth_service = AuthService


async def force_password_change_for_all_users(db: AsyncSession) -> int:
    """Force password change for all users"""
    service = AuthService(db)
    return await service.force_password_change_for_all()


async def regenerate_user_qr_token(db: AsyncSession, user_id: int) -> str:
    """Regenerate QR token for a user"""
    service = AuthService(db)
    return await service.regenerate_qr_token(user_id)