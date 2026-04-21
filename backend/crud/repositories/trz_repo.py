from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.models import EmploymentContract, ContractAnnex, ContractTemplate, ContractTemplateVersion
from .base import BaseRepository


class TRZRepository(BaseRepository):
    """Repository за TRZ (Трудови договори)"""
    
    model = EmploymentContract
    
    async def get_user_contracts(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[EmploymentContract]:
        """Връща договорите на потребител"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.user_id == user_id)
            .order_by(EmploymentContract.start_date.desc())
        )
        return list(result.scalars().all())
    
    async def get_active_contract(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[EmploymentContract]:
        """Връща активния договор на потребител"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.user_id == user_id)
            .where(EmploymentContract.status == "active")
            .order_by(EmploymentContract.start_date.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_contract_annexes(
        self,
        db: AsyncSession,
        contract_id: int
    ) -> List[ContractAnnex]:
        """Връща анексите на договор"""
        result = await db.execute(
            select(ContractAnnex)
            .where(ContractAnnex.contract_id == contract_id)
            .order_by(ContractAnnex.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_contract_with_relations(
        self,
        db: AsyncSession,
        contract_id: int
    ) -> Optional[EmploymentContract]:
        """Връща договор с потребител и компания"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.id == contract_id)
            .options(
                selectinload(EmploymentContract.user),
                selectinload(EmploymentContract.company),
                selectinload(EmploymentContract.position),
                selectinload(EmploymentContract.department)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_contracts_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        status: str = None,
        limit: int = 100
    ) -> List[EmploymentContract]:
        """Връща договорите на компания"""
        query = select(EmploymentContract).where(EmploymentContract.company_id == company_id)
        if status:
            query = query.where(EmploymentContract.status == status)
        query = query.order_by(EmploymentContract.start_date.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


trz_repo = TRZRepository()