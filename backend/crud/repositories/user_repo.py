import secrets
from datetime import datetime, timedelta
from typing import cast
from sqlalchemy.engine import CursorResult
from zoneinfo import ZoneInfo

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database.models import AuthKey, Role, User, UserSession
from backend.graphql.utils.pagination import cached_count, invalidate_count_cache
from backend.schemas import UserCreate, UserUpdate

from .base import BaseRepository


class UserRepository(BaseRepository):
    """Repository за потребители"""

    model = User

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Връща потребител по email"""
        result = await db.execute(
            select(User).where(User.email == email),
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        """Връща потребител по username"""
        result = await db.execute(
            select(User).where(User.username == username),
        )
        return result.scalar_one_or_none()

    async def get_with_relations(self, db: AsyncSession, user_id: int) -> User | None:
        """Връща потребител с role и company"""
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role), selectinload(User.company)),
        )
        return result.scalar_one_or_none()

    async def get_active_sessions(self, db: AsyncSession, user_id: int) -> list[UserSession]:
        """Връща активните сесии на потребителя"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_active),
        )
        return list(result.scalars().all())

    async def get_auth_keys(self, db: AsyncSession, user_id: int) -> list[AuthKey]:
        """Връща auth ключовете на потребителя"""
        result = await db.execute(
            select(AuthKey)
            .where(AuthKey.user_id == user_id)
            .order_by(AuthKey.created_at.desc()),
        )
        return list(result.scalars().all())

    async def get_users_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Връща потребителите на компания"""
        result = await db.execute(
            select(User)
            .where(User.company_id == company_id)
            .limit(limit)
            .offset(offset),
        )
        return list(result.scalars().all())

    async def search_users(
        self,
        db: AsyncSession,
        company_id: int,
        search: str,
        limit: int = 50,
    ) -> list[User]:
        """Търси потребители по име или email"""
        search_pattern = f"%{search}%"
        result = await db.execute(
            select(User)
            .where(User.company_id == company_id)
            .where(
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern)),
            )
            .limit(limit),
        )
        return list(result.scalars().all())

    async def create_user(
        self,
        db: AsyncSession,
        user_data: UserCreate,
        role_id: int | None = None,
        **kwargs,
    ) -> User:
        """Създава нов потребител"""
        from backend.auth.security import hash_password
        contract_fields = {
            "contract_type", "contract_number", "contract_start_date", "contract_end_date",
            "base_salary", "work_hours_per_week", "probation_months", "salary_calculation_type",
            "salary_installments_count", "monthly_advance_amount", "tax_resident",
            "insurance_contributor", "has_income_tax", "payment_day", "experience_start_date",
            "night_work_rate", "overtime_rate", "holiday_rate", "work_class", "dangerous_work",
        }
        user_dict = user_data.model_dump(exclude_unset=True, exclude={"password"} | contract_fields)
        if user_data.password:
            user_dict["hashed_password"] = hash_password(user_data.password)
        if role_id:
            user_dict["role_id"] = role_id
        user_dict.update(kwargs)

        if "created_at" not in user_dict:
            user_dict["created_at"] = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)

        user = User(**user_dict)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        invalidate_count_cache("users")
        return user

    async def update_user(
        self,
        db: AsyncSession,
        user_id: int,
        user_in: UserUpdate | None = None,
        **kwargs,
    ) -> User | None:
        """Обновява потребител"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None

        if user_in:
            update_data = user_in.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await db.flush()
        await db.refresh(user)
        invalidate_count_cache("users")
        return user

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """Изтрива потребител"""
        user = await self.get_by_id(db, user_id)
        if user:
            await db.delete(user)
            await db.flush()
            invalidate_count_cache("users")
            return True
        return False

    async def get_user_session_by_id(self, db: AsyncSession, session_id: int) -> UserSession | None:
        """Връща сесия по ID"""
        result = await db.execute(
            select(UserSession).where(UserSession.id == session_id),
        )
        return result.scalar_one_or_none()

    async def get_all_active_sessions(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserSession]:
        """Връща активните сесии"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.is_active)
            .order_by(UserSession.created_at.desc())
            .offset(skip)
            .limit(limit),
        )
        return list(result.scalars().all())

    async def invalidate_user_session(self, db: AsyncSession, jti: str) -> bool:
        """Инвалидира сесия по JTI"""
        result = await db.execute(
            select(UserSession).where(UserSession.refresh_token_jti == jti),
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await db.commit()
            return True
        return False

    async def get_users(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        company_id: int | None = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> list[User]:
        """Връща потребители с филтриране"""
        query = select(User).options(selectinload(User.role), selectinload(User.company_rel))

        if company_id:
            query = query.where(User.company_id == company_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern)),
            )

        if sort_by:
            order_col = getattr(User, sort_by, User.id)
            if sort_order == "desc":
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_users(
        self,
        db: AsyncSession,
        search: str | None = None,
        company_id: int | None = None,
    ) -> int:
        """Брои потребители с кеширане"""
        query = select(User.id)

        if company_id:
            query = query.where(User.company_id == company_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern)),
            )

        cache_key = f"users:{company_id}:{search}"
        return await cached_count(db, query, cache_key)

    # --- User additional methods ---

    async def get_by_email_or_username(self, db: AsyncSession, email_or_username: str) -> User | None:
        """Търси потребител по email или username"""
        result = await db.execute(
            select(User).where(
                (User.email == email_or_username) | (User.username == email_or_username),
            ),
        )
        return result.scalar_one_or_none()

    async def get_by_qr_token(self, db: AsyncSession, qr_token: str) -> User | None:
        """Връща потребител по QR token"""
        result = await db.execute(
            select(User).where(User.qr_token == qr_token),
        )
        return result.scalar_one_or_none()

    async def regenerate_qr_token(self, db: AsyncSession, user_id: int) -> User | None:
        """Генерира нов QR token за потребител"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
        user.qr_token = secrets.token_urlsafe(32)
        await db.flush()
        await db.refresh(user)
        return user

    async def update_last_login(self, db: AsyncSession, user_id: int) -> User | None:
        """Обновява last_login timestamp на потребител"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
        user.last_login = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        await db.flush()
        await db.refresh(user)
        return user

    # --- Role methods ---

    async def get_role_by_id(self, db: AsyncSession, id: int) -> Role | None:
        """Връща роля по ID"""
        result = await db.execute(
            select(Role).where(Role.id == id),
        )
        return result.scalar_one_or_none()

    async def get_role_by_name(self, db: AsyncSession, name: str) -> Role | None:
        """Връща роля по име"""
        result = await db.execute(
            select(Role).where(Role.name == name),
        )
        return result.scalar_one_or_none()

    async def get_roles(self, db: AsyncSession) -> list[Role]:
        """Връща всички роли"""
        result = await db.execute(select(Role))
        return list(result.scalars().all())

    async def create_role(self, db: AsyncSession, name: str, **kwargs) -> Role:
        """Създава нова роля"""
        role = Role(name=name, **kwargs)
        db.add(role)
        await db.flush()
        await db.refresh(role)
        return role

    async def update_role(self, db: AsyncSession, id: int, **kwargs) -> Role | None:
        """Обновява роля"""
        role = await self.get_role_by_id(db, id)
        if not role:
            return None
        for key, value in kwargs.items():
            if hasattr(role, key):
                setattr(role, key, value)
        await db.flush()
        await db.refresh(role)
        return role

    async def delete_role(self, db: AsyncSession, id: int) -> bool:
        """Изтрива роля"""
        role = await self.get_role_by_id(db, id)
        if not role:
            return False
        await db.delete(role)
        await db.flush()
        return True

    # --- AuthKey methods ---

    async def create_auth_key(self, db: AsyncSession, user_id: int, **kwargs) -> AuthKey:
        """Създава нов auth ключ за потребител"""
        auth_key = AuthKey(user_id=user_id, **kwargs)
        db.add(auth_key)
        await db.flush()
        await db.refresh(auth_key)
        return auth_key

    async def get_auth_key_by_id(self, db: AsyncSession, id: int) -> AuthKey | None:
        """Връща auth ключ по ID"""
        result = await db.execute(
            select(AuthKey).where(AuthKey.id == id),
        )
        return result.scalar_one_or_none()

    async def delete_auth_key(self, db: AsyncSession, id: int) -> bool:
        """Изтрива auth ключ по ID"""
        auth_key = await self.get_auth_key_by_id(db, id)
        if not auth_key:
            return False
        await db.delete(auth_key)
        await db.commit()
        return True

    # --- UserSession additional methods ---

    async def create_user_session(self, db: AsyncSession, **kwargs) -> UserSession:
        """Създава нова потребителска сесия"""
        session = UserSession(**kwargs)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_user_session_by_jti(self, db: AsyncSession, jti: str) -> UserSession | None:
        """Връща сесия по refresh_token_jti"""
        result = await db.execute(
            select(UserSession).where(UserSession.refresh_token_jti == jti),
        )
        return result.scalar_one_or_none()

    async def invalidate_all_user_sessions(self, db: AsyncSession, user_id: int) -> int:
        """Инвалидира всички активни сесии на потребител"""
        result = await db.execute(
            update(UserSession)
            .where(and_(UserSession.user_id == user_id, UserSession.is_active))
            .values(is_active=False),
        )
        await db.commit()
        return cast(CursorResult, result).rowcount

    async def cleanup_expired_sessions(self, db: AsyncSession, retention_days: int) -> int:
        """Изтрива сесии по-стари от retention_days"""
        cutoff = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None) - timedelta(days=retention_days)
        result = await db.execute(
            delete(UserSession).where(UserSession.expires_at < cutoff),
        )
        await db.commit()
        return cast(CursorResult, result).rowcount

    async def terminate_stale_sessions(self, db: AsyncSession, max_age_hours: int = 12) -> int:
        """Терминира активни сесии по-стари от max_age_hours"""
        cutoff = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None) - timedelta(hours=max_age_hours)
        result = await db.execute(
            update(UserSession)
            .where(UserSession.is_active)
            .where(UserSession.created_at < cutoff)
            .values(is_active=False),
        )
        await db.commit()
        return cast(CursorResult, result).rowcount


user_repo = UserRepository()
