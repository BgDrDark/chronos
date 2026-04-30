from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.database.models import EmploymentContract, User, Notification


class ContractService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        company_id: int,
        contract_type: str,
        start_date: date,
        end_date: Optional[date] = None,
        base_salary: Optional[float] = None,
        work_hours_per_week: int = 40,
        probation_months: int = 0,
        is_active: bool = True,
        salary_calculation_type: str = 'gross',
        salary_installments_count: int = 1,
        monthly_advance_amount: float = 0,
        tax_resident: bool = True,
        insurance_contributor: bool = True,
        has_income_tax: bool = True,
        payment_day: int = 25,
        experience_start_date: Optional[date] = None,
        night_work_rate: float = 0.5,
        overtime_rate: float = 1.5,
        holiday_rate: float = 2.0,
        work_class: Optional[str] = None,
        dangerous_work: bool = False
    ) -> EmploymentContract:
        """Create a new employment contract"""
        contract = EmploymentContract(
            user_id=user_id,
            company_id=company_id,
            contract_type=contract_type,
            start_date=start_date,
            end_date=end_date,
            base_salary=base_salary,
            work_hours_per_week=work_hours_per_week,
            probation_months=probation_months,
            is_active=is_active,
            salary_calculation_type=salary_calculation_type,
            salary_installments_count=salary_installments_count,
            monthly_advance_amount=monthly_advance_amount,
            tax_resident=tax_resident,
            insurance_contributor=insurance_contributor,
            has_income_tax=has_income_tax,
            payment_day=payment_day,
            experience_start_date=experience_start_date,
            night_work_rate=night_work_rate,
            overtime_rate=overtime_rate,
            holiday_rate=holiday_rate,
            work_class=work_class,
            dangerous_work=dangerous_work
        )
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def get_by_id(self, contract_id: int) -> Optional[EmploymentContract]:
        """Get contract by ID"""
        stmt = select(EmploymentContract).where(EmploymentContract.id == contract_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_active_for_user(self, user_id: int) -> Optional[EmploymentContract]:
        """Get active contract for user"""
        stmt = select(EmploymentContract).where(
            EmploymentContract.user_id == user_id,
            EmploymentContract.is_active == True
        ).order_by(EmploymentContract.start_date.desc())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_for_user(self, user_id: int) -> List[EmploymentContract]:
        """Get all contracts for user"""
        stmt = select(EmploymentContract).where(
            EmploymentContract.user_id == user_id
        ).order_by(EmploymentContract.start_date.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_expiring_soon(self, days: int = 30) -> List[EmploymentContract]:
        """Get contracts expiring within given days"""
        from datetime import timedelta
        today = date.today()
        end_date_limit = today + timedelta(days=days)
        
        stmt = select(EmploymentContract).where(
            EmploymentContract.is_active == True,
            EmploymentContract.end_date != None,
            EmploymentContract.end_date <= end_date_limit,
            EmploymentContract.end_date >= today
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def extend(
        self,
        contract_id: int,
        new_end_date: date,
        reason: Optional[str] = None
    ) -> EmploymentContract:
        """Extend contract end date"""
        contract = await self.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contract not found")
        
        old_end_date = contract.end_date
        contract.end_date = new_end_date
        contract.is_active = True
        
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        
        await self._notify_extension(contract, old_end_date, new_end_date, reason)
        
        return contract

    async def terminate(
        self,
        contract_id: int,
        termination_date: Optional[date] = None,
        reason: Optional[str] = None
    ) -> EmploymentContract:
        """Terminate a contract"""
        contract = await self.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contract not found")
        
        term_date = termination_date or date.today()
        contract.end_date = term_date
        contract.is_active = False
        
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        
        await self._notify_termination(contract, term_date, reason)
        
        return contract

    async def deactivate_expired(self) -> int:
        """Deactivate all expired contracts and set users to inactive. Returns count of deactivated users."""
        today = date.today()
        
        stmt = (
            select(User)
            .join(EmploymentContract, User.id == EmploymentContract.user_id)
            .where(User.is_active == True)
            .where(EmploymentContract.is_active == True)
            .where(EmploymentContract.end_date != None)
            .where(EmploymentContract.end_date < today)
        )
        
        result = await self.db.execute(stmt)
        users_to_deactivate = result.scalars().all()
        
        count = 0
        for user in users_to_deactivate:
            user.is_active = False
            count += 1
            
            contract = await self.get_active_for_user(user.id)
            if contract:
                contract.is_active = False
                self.db.add(contract)
            
            await self._notify_expiration(user.id)
        
        if count > 0:
            await self.db.commit()
        
        return count

    async def get_contracts_by_company(
        self,
        company_id: int,
        is_active: Optional[bool] = None
    ) -> List[EmploymentContract]:
        """Get all contracts for a company"""
        stmt = select(EmploymentContract).where(
            EmploymentContract.company_id == company_id
        )
        
        if is_active is not None:
            stmt = stmt.where(EmploymentContract.is_active == is_active)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _notify_extension(
        self,
        contract: EmploymentContract,
        old_end_date: date,
        new_end_date: date,
        reason: Optional[str] = None
    ) -> None:
        """Notify user about contract extension"""
        message = f"Вашият трудов договор беше удължен до {new_end_date}."
        if reason:
            message += f" Причина: {reason}"
        
        notification = Notification(user_id=contract.user_id, message=message)
        self.db.add(notification)
        await self.db.flush()

    async def _notify_termination(
        self,
        contract: EmploymentContract,
        termination_date: date,
        reason: Optional[str] = None
    ) -> None:
        """Notify user about contract termination"""
        message = f"Вашият трудов договор беше прекратен на {termination_date}."
        if reason:
            message += f" Причина: {reason}"
        
        notification = Notification(user_id=contract.user_id, message=message)
        self.db.add(notification)
        await self.db.flush()

    async def _notify_expiration(self, user_id: int) -> None:
        """Notify user about contract expiration"""
        notification = Notification(
            user_id=user_id,
            message="Вашият трудов договор е изтекъл. Моля, свържете се с HR."
        )
        self.db.add(notification)
        await self.db.flush()


contract_service = ContractService