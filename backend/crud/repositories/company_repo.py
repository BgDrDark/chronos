from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from backend.database.models import Company, Department, Position
from .base import BaseRepository


class CompanyRepository(BaseRepository):
    """Repository за компания"""
    
    model = Company
    
    async def get_with_departments(self, db: AsyncSession, company_id: int) -> Optional[Company]:
        """Връща компания с департаменти"""
        result = await db.execute(
            select(Company)
            .where(Company.id == company_id)
            .options(selectinload(Company.departments))
        )
        return result.scalar_one_or_none()
    
    async def get_departments(self, db: AsyncSession, company_id: int) -> List[Department]:
        """Връща департаментите на компанията"""
        result = await db.execute(
            select(Department).where(Department.company_id == company_id)
        )
        return list(result.scalars().all())
    
    async def get_positions(self, db: AsyncSession, department_id: int) -> List[Position]:
        """Връща позициите в департамента"""
        result = await db.execute(
            select(Position).where(Position.department_id == department_id)
        )
        return list(result.scalars().all())
    
    async def get_department_by_id(self, db: AsyncSession, department_id: int) -> Optional[Department]:
        """Връща департамент по ID"""
        result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalar_one_or_none()
    
    async def get_position_by_id(self, db: AsyncSession, position_id: int) -> Optional[Position]:
        """Връща позиция по ID"""
        result = await db.execute(
            select(Position).where(Position.id == position_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_companies(
        self, 
        db: AsyncSession, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Company]:
        """Връща всички компании"""
        result = await db.execute(
            select(Company).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_eik(self, db: AsyncSession, eik: str) -> Optional[Company]:
        """Връща компания по ЕИК"""
        result = await db.execute(
            select(Company).where(Company.eik == eik)
        )
        return result.scalar_one_or_none()
    
    async def create_company(
        self,
        db: AsyncSession,
        name: str,
        eik: str = None,
        vat_number: str = None,
        **kwargs
    ) -> Company:
        """Създава нова компания"""
        company = Company(name=name, eik=eik, vat_number=vat_number, **kwargs)
        db.add(company)
        await db.flush()
        await db.refresh(company)
        return company
    
    async def update_company(
        self,
        db: AsyncSession,
        company_id: int,
        **kwargs
    ) -> Optional[Company]:
        """Обновява компания"""
        company = await self.get_by_id(db, company_id)
        if not company:
            return None
        
        for key, value in kwargs.items():
            if hasattr(company, key):
                setattr(company, key, value)
        
        await db.flush()
        await db.refresh(company)
        return company
    
    async def create_department(
        self,
        db: AsyncSession,
        name: str,
        company_id: int,
        manager_id: int = None,
        **kwargs
    ) -> Department:
        """Създава нов департамент"""
        department = Department(name=name, company_id=company_id, manager_id=manager_id, **kwargs)
        db.add(department)
        await db.flush()
        await db.refresh(department)
        return department
    
    async def update_department(
        self,
        db: AsyncSession,
        department_id: int,
        **kwargs
    ) -> Optional[Department]:
        """Обновява департамент"""
        department = await self.get_department_by_id(db, department_id)
        if not department:
            return None
        
        for key, value in kwargs.items():
            if hasattr(department, key):
                setattr(department, key, value)
        
        await db.flush()
        await db.refresh(department)
        return department
    
    async def create_position(
        self,
        db: AsyncSession,
        title: str,
        department_id: int,
        **kwargs
    ) -> Position:
        """Създава нова позиция"""
        position = Position(title=title, department_id=department_id, **kwargs)
        db.add(position)
        await db.flush()
        await db.refresh(position)
        return position
    
    async def update_position(
        self,
        db: AsyncSession,
        position_id: int,
        **kwargs
    ) -> Optional[Position]:
        """Обновява позиция"""
        position = await self.get_position_by_id(db, position_id)
        if not position:
            return None
        
        for key, value in kwargs.items():
            if hasattr(position, key):
                setattr(position, key, value)
        
        await db.flush()
        await db.refresh(position)
        return position
    
    async def delete_position(self, db: AsyncSession, position_id: int) -> bool:
        """Изтрива позиция"""
        position = await self.get_position_by_id(db, position_id)
        if position:
            await db.delete(position)
            await db.flush()
            return True
        return False


company_repo = CompanyRepository()