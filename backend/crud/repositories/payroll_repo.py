from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.models import Payroll, Payslip, Bonus, AdvancePayment, PayrollDeduction, PayrollPaymentSchedule
from .base import BaseRepository


class PayrollRepository(BaseRepository):
    """Repository за Payroll"""
    
    model = Payroll
    
    async def get_user_payrolls(
        self,
        db: AsyncSession,
        user_id: int,
        year: int = None,
        month: int = None
    ) -> List[Payroll]:
        """Връща Payroll записи за потребител"""
        query = select(Payroll).where(Payroll.user_id == user_id)
        
        if year:
            query = query.where(Payroll.year == year)
        if month:
            query = query.where(Payroll.month == month)
        
        query = query.order_by(Payroll.year.desc(), Payroll.month.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_payslips(
        self,
        db: AsyncSession,
        payroll_id: int
    ) -> List[Payslip]:
        """Връща всички Payslip за Payroll"""
        result = await db.execute(
            select(Payslip).where(Payslip.payroll_id == payroll_id)
        )
        return list(result.scalars().all())
    
    async def get_bonuses(
        self,
        db: AsyncSession,
        user_id: int = None,
        company_id: int = None
    ) -> List[Bonus]:
        """Връща бонуси"""
        query = select(Bonus)
        if user_id:
            query = query.where(Bonus.user_id == user_id)
        if company_id:
            query = query.where(Bonus.company_id == company_id)
        result = await db.execute(query.order_by(Bonus.created_at.desc()))
        return list(result.scalars().all())
    
    async def get_advance_payments(
        self,
        db: AsyncSession,
        user_id: int = None,
        status: str = None
    ) -> List[AdvancePayment]:
        """Връща аванси"""
        query = select(AdvancePayment)
        if user_id:
            query = query.where(AdvancePayment.user_id == user_id)
        if status:
            query = query.where(AdvancePayment.status == status)
        result = await db.execute(query.order_by(AdvancePayment.created_at.desc()))
        return list(result.scalars().all())
    
    async def get_payroll_by_id(self, db: AsyncSession, payroll_id: int) -> Optional[Payroll]:
        """Връща Payroll по ID с всички Payslips"""
        result = await db.execute(
            select(Payroll)
            .where(Payroll.id == payroll_id)
            .options(selectinload(Payroll.payslips))
        )
        return result.scalar_one_or_none()
    
    async def create_bonus(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        date: date,
        description: str = None
    ) -> Bonus:
        """Създава бонус"""
        bonus = Bonus(
            user_id=user_id,
            amount=amount,
            date=date,
            description=description
        )
        db.add(bonus)
        await db.flush()
        await db.refresh(bonus)
        return bonus
    
    async def delete_bonus(self, db: AsyncSession, bonus_id: int) -> bool:
        """Изтрива бонус"""
        bonus = await db.get(Bonus, bonus_id)
        if bonus:
            await db.delete(bonus)
            await db.flush()
            return True
        return False
    
    async def create_advance_payment(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        request_date: date = None
    ) -> AdvancePayment:
        """Създава авансово плащане"""
        advance = AdvancePayment(
            user_id=user_id,
            amount=amount,
            request_date=request_date or date.today(),
            status="pending"
        )
        db.add(advance)
        await db.flush()
        await db.refresh(advance)
        return advance
    
    async def create_service_loan(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        months: int,
        interest_rate: float = 0.0
    ) -> dict:
        """Създава служебна заема"""
        loan = {
            "user_id": user_id,
            "amount": amount,
            "months": months,
            "interest_rate": interest_rate
        }
        return loan


payroll_repo = PayrollRepository()