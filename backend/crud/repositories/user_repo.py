from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from sqlalchemy.orm import selectinload
from backend.database.models import User, UserSession, AuthKey, Role
from backend.schemas import UserCreate, UserUpdate
from datetime import datetime
from .base import BaseRepository


class UserRepository(BaseRepository):
    """Repository за потребители"""
    
    model = User
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Връща потребител по email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Връща потребител по username"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_with_relations(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Връща потребител с role и company"""
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role), selectinload(User.company))
        )
        return result.scalar_one_or_none()
    
    async def get_active_sessions(self, db: AsyncSession, user_id: int) -> List[UserSession]:
        """Връща активните сесии на потребителя"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_active == True)
        )
        return list(result.scalars().all())
    
    async def get_auth_keys(self, db: AsyncSession, user_id: int) -> List[AuthKey]:
        """Връща auth ключовете на потребителя"""
        result = await db.execute(
            select(AuthKey)
            .where(AuthKey.user_id == user_id)
            .order_by(AuthKey.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_users_by_company(
        self, 
        db: AsyncSession, 
        company_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """Връща потребителите на компания"""
        result = await db.execute(
            select(User)
            .where(User.company_id == company_id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def search_users(
        self,
        db: AsyncSession,
        company_id: int,
        search: str,
        limit: int = 50
    ) -> List[User]:
        """Търси потребители по име или email"""
        search_pattern = f"%{search}%"
        result = await db.execute(
            select(User)
            .where(User.company_id == company_id)
            .where(
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
            )
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create_user(
        self,
        db: AsyncSession,
        user_data: UserCreate,
        role_id: int = None,
        **kwargs
    ) -> User:
        """Създава нов потребител"""
        from backend.auth.security import hash_password
        contract_fields = {
            "contract_type", "contract_number", "contract_start_date", "contract_end_date",
            "base_salary", "work_hours_per_week", "probation_months", "salary_calculation_type",
            "salary_installments_count", "monthly_advance_amount", "tax_resident",
            "insurance_contributor", "has_income_tax", "payment_day", "experience_start_date",
            "night_work_rate", "overtime_rate", "holiday_rate", "work_class", "dangerous_work"
        }
        user_dict = user_data.model_dump(exclude_unset=True, exclude={"password"} | contract_fields)
        if user_data.password:
            user_dict["hashed_password"] = hash_password(user_data.password)
        if role_id:
            user_dict["role_id"] = role_id
        user_dict.update(kwargs)
        
        if "created_at" not in user_dict:
            user_dict["created_at"] = datetime.utcnow()
        
        user = User(**user_dict)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def update_user(
        self,
        db: AsyncSession,
        user_id: int,
        user_in: UserUpdate = None,
        **kwargs
    ) -> Optional[User]:
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
        return user
    
    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """Изтрива потребител"""
        user = await self.get_by_id(db, user_id)
        if user:
            await db.delete(user)
            await db.flush()
            return True
        return False
    
    async def get_user_session_by_id(self, db: AsyncSession, session_id: int) -> Optional[UserSession]:
        """Връща сесия по ID"""
        result = await db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_sessions(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserSession]:
        """Връща активните сесии"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.is_active == True)
            .order_by(UserSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def invalidate_user_session(self, db: AsyncSession, jti: str) -> bool:
        """Инвалидира сесия по JTI"""
        result = await db.execute(
            select(UserSession).where(UserSession.refresh_token_jti == jti)
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
        search: str = None,
        company_id: int = None,
        sort_by: str = "id",
        sort_order: str = "asc"
    ) -> List[User]:
        """Връща потребители с филтриране"""
        query = select(User).options(selectinload(User.role), selectinload(User.company_rel))
        
        if company_id:
            query = query.where(User.company_id == company_id)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
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
        search: str = None,
        company_id: int = None
    ) -> int:
        """Брои потребители"""
        query = select(func.count(User.id))
        
        if company_id:
            query = query.where(User.company_id == company_id)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
            )
        
        result = await db.execute(query)
        return result.scalar() or 0


user_repo = UserRepository()