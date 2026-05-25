from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    AdvancePayment,
    Bonus,
    InsuranceRateHistory,
    MonthlyWorkDays,
    Payroll,
    PayrollDeduction,
    Payslip,
    ServiceLoan,
    TaxRateHistory,
    User,
)

from .base import BaseRepository


class PayrollRepository(BaseRepository):
    """Repository за Payroll"""

    model = Payroll

    async def get_user_payrolls(
        self,
        db: AsyncSession,
        user_id: int,
        year: int = None,
        month: int = None,
    ) -> list[Payroll]:
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
        payroll_id: int,
    ) -> list[Payslip]:
        """Връща всички Payslip за Payroll"""
        result = await db.execute(
            select(Payslip).where(Payslip.payroll_id == payroll_id),
        )
        return list(result.scalars().all())

    async def get_bonuses(
        self,
        db: AsyncSession,
        user_id: int = None,
        company_id: int = None,
    ) -> list[Bonus]:
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
        status: str = None,
    ) -> list[AdvancePayment]:
        """Връща аванси"""
        query = select(AdvancePayment)
        if user_id:
            query = query.where(AdvancePayment.user_id == user_id)
        if status:
            query = query.where(AdvancePayment.status == status)
        result = await db.execute(query.order_by(AdvancePayment.created_at.desc()))
        return list(result.scalars().all())

    async def get_payroll_by_id(self, db: AsyncSession, payroll_id: int) -> Payroll | None:
        """Връща Payroll по ID с всички Payslips"""
        result = await db.execute(
            select(Payroll)
            .where(Payroll.id == payroll_id)
            .options(selectinload(Payroll.payslips)),
        )
        return result.scalar_one_or_none()

    async def create_bonus(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        date: date,
        description: str = None,
    ) -> Bonus:
        """Създава бонус"""
        bonus = Bonus(
            user_id=user_id,
            amount=amount,
            date=date,
            description=description,
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
        request_date: date = None,
    ) -> AdvancePayment:
        """Създава авансово плащане"""
        advance = AdvancePayment(
            user_id=user_id,
            amount=amount,
            request_date=request_date or date.today(),
            status="pending",
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
        interest_rate: float = 0.0,
    ) -> ServiceLoan:
        """Създава служебна заема"""
        total = amount
        if interest_rate > 0:
            total = amount * (1 + interest_rate / 100)
        installment = total / months if months > 0 else total
        loan = ServiceLoan(
            user_id=user_id,
            total_amount=total,
            installment_amount=installment,
            remaining_amount=total,
            installments_count=months,
            installments_paid=0,
            start_date=datetime.now(),
            description=f"Loan of {amount} for {months} months at {interest_rate}%",
            is_active=True,
        )
        db.add(loan)
        await db.flush()
        await db.refresh(loan)
        return loan

    # === Payslip CRUD ===

    async def create_payslip(self, db: AsyncSession, **kwargs) -> Payslip:
        payslip = Payslip(**kwargs)
        db.add(payslip)
        await db.flush()
        await db.refresh(payslip)
        return payslip

    async def get_payslip_by_id(self, db: AsyncSession, id: int) -> Payslip | None:
        result = await db.execute(
            select(Payslip)
            .where(Payslip.id == id)
            .options(selectinload(Payslip.user)),
        )
        return result.scalar_one_or_none()

    async def get_payslips_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        start_date: date = None,
        end_date: date = None,
    ) -> list[Payslip]:
        query = select(Payslip).where(Payslip.user_id == user_id)
        if start_date:
            query = query.where(Payslip.period_start >= start_date)
        if end_date:
            query = query.where(Payslip.period_end <= end_date)
        query = query.order_by(Payslip.period_start.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_payslips_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        period_start: date = None,
        period_end: date = None,
        status: str = None,
    ) -> list[Payslip]:
        query = (
            select(Payslip)
            .join(User, User.id == Payslip.user_id)
            .where(User.company_id == company_id)
        )
        if period_start:
            query = query.where(Payslip.period_start >= period_start)
        if period_end:
            query = query.where(Payslip.period_end <= period_end)
        if status:
            query = query.where(Payslip.payment_status == status)
        query = query.order_by(Payslip.generated_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_payslip(self, db: AsyncSession, id: int, **kwargs) -> Payslip | None:
        payslip = await db.get(Payslip, id)
        if payslip:
            for key, value in kwargs.items():
                if hasattr(payslip, key):
                    setattr(payslip, key, value)
            await db.flush()
            await db.refresh(payslip)
        return payslip

    async def mark_payslip_as_paid(
        self,
        db: AsyncSession,
        id: int,
        payment_date: datetime = None,
        payment_method: str = "bank",
    ) -> Payslip | None:
        payslip = await db.get(Payslip, id)
        if payslip:
            payslip.payment_status = "paid"
            payslip.actual_payment_date = payment_date
            payslip.payment_method = payment_method
            await db.flush()
            await db.refresh(payslip)
        return payslip

    async def delete_payslip(self, db: AsyncSession, id: int) -> bool:
        payslip = await db.get(Payslip, id)
        if payslip:
            await db.delete(payslip)
            await db.flush()
            return True
        return False

    # === AdvancePayment CRUD ===

    async def get_advance_payment_by_id(self, db: AsyncSession, id: int) -> AdvancePayment | None:
        return await self.get_by_id(db, id)

    async def get_advance_payments_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        status: str = None,
    ) -> list[AdvancePayment]:
        query = select(AdvancePayment).where(AdvancePayment.user_id == user_id)
        if status:
            query = query.where(AdvancePayment.status == status)
        query = query.order_by(AdvancePayment.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_advance_payment(self, db: AsyncSession, id: int, **kwargs) -> AdvancePayment | None:
        advance = await db.get(AdvancePayment, id)
        if advance:
            for key, value in kwargs.items():
                if hasattr(advance, key):
                    setattr(advance, key, value)
            await db.flush()
            await db.refresh(advance)
        return advance

    async def mark_advance_as_processed(self, db: AsyncSession, id: int) -> AdvancePayment | None:
        advance = await db.get(AdvancePayment, id)
        if advance:
            advance.is_processed = True
            await db.flush()
            await db.refresh(advance)
        return advance

    # === ServiceLoan CRUD ===

    async def get_service_loan_by_id(self, db: AsyncSession, id: int) -> ServiceLoan | None:
        return await self.get_by_id(db, id)

    async def get_service_loans_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        is_active: bool = None,
    ) -> list[ServiceLoan]:
        query = select(ServiceLoan).where(ServiceLoan.user_id == user_id)
        if is_active is not None:
            query = query.where(ServiceLoan.is_active == is_active)
        query = query.order_by(ServiceLoan.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_service_loan(self, db: AsyncSession, id: int, **kwargs) -> ServiceLoan | None:
        loan = await db.get(ServiceLoan, id)
        if loan:
            for key, value in kwargs.items():
                if hasattr(loan, key):
                    setattr(loan, key, value)
            await db.flush()
            await db.refresh(loan)
        return loan

    async def delete_service_loan(self, db: AsyncSession, id: int) -> bool:
        loan = await db.get(ServiceLoan, id)
        if loan:
            await db.delete(loan)
            await db.flush()
            return True
        return False

    async def get_all_active_loans(self, db: AsyncSession, company_id: int) -> list[ServiceLoan]:
        result = await db.execute(
            select(ServiceLoan)
            .join(User, User.id == ServiceLoan.user_id)
            .where(
                ServiceLoan.is_active,
                User.company_id == company_id,
            )
            .order_by(ServiceLoan.created_at.desc()),
        )
        return list(result.scalars().all())

    # === InsuranceRate CRUD ===

    async def create_insurance_rate(self, db: AsyncSession, **kwargs) -> InsuranceRateHistory:
        rate = InsuranceRateHistory(**kwargs)
        db.add(rate)
        await db.flush()
        await db.refresh(rate)
        return rate

    async def get_insurance_rate_by_id(self, db: AsyncSession, id: int) -> InsuranceRateHistory | None:
        return await self.get_by_id(db, id)

    async def get_active_insurance_rates(self, db: AsyncSession, year: int) -> list[InsuranceRateHistory]:
        result = await db.execute(
            select(InsuranceRateHistory)
            .where(InsuranceRateHistory.year == year)
            .order_by(InsuranceRateHistory.category, InsuranceRateHistory.month),
        )
        return list(result.scalars().all())

    async def update_insurance_rate(self, db: AsyncSession, id: int, **kwargs) -> InsuranceRateHistory | None:
        rate = await db.get(InsuranceRateHistory, id)
        if rate:
            for key, value in kwargs.items():
                if hasattr(rate, key):
                    setattr(rate, key, value)
            await db.flush()
            await db.refresh(rate)
        return rate

    async def delete_insurance_rate(self, db: AsyncSession, id: int) -> bool:
        rate = await db.get(InsuranceRateHistory, id)
        if rate:
            await db.delete(rate)
            await db.flush()
            return True
        return False

    # === TaxRate CRUD ===

    async def create_tax_rate(self, db: AsyncSession, **kwargs) -> TaxRateHistory:
        rate = TaxRateHistory(**kwargs)
        db.add(rate)
        await db.flush()
        await db.refresh(rate)
        return rate

    async def get_tax_rate_by_id(self, db: AsyncSession, id: int) -> TaxRateHistory | None:
        return await self.get_by_id(db, id)

    async def get_active_tax_rates(self, db: AsyncSession, year: int) -> list[TaxRateHistory]:
        result = await db.execute(
            select(TaxRateHistory)
            .where(TaxRateHistory.year == year)
            .order_by(TaxRateHistory.month),
        )
        return list(result.scalars().all())

    async def update_tax_rate(self, db: AsyncSession, id: int, **kwargs) -> TaxRateHistory | None:
        rate = await db.get(TaxRateHistory, id)
        if rate:
            for key, value in kwargs.items():
                if hasattr(rate, key):
                    setattr(rate, key, value)
            await db.flush()
            await db.refresh(rate)
        return rate

    async def delete_tax_rate(self, db: AsyncSession, id: int) -> bool:
        rate = await db.get(TaxRateHistory, id)
        if rate:
            await db.delete(rate)
            await db.flush()
            return True
        return False

    # === MonthlyWorkDays CRUD ===

    async def set_monthly_work_days(
        self,
        db: AsyncSession,
        year: int,
        month: int,
        days_count: int,
    ) -> MonthlyWorkDays:
        result = await db.execute(
            select(MonthlyWorkDays).where(
                MonthlyWorkDays.year == year,
                MonthlyWorkDays.month == month,
            ),
        )
        entry = result.scalar_one_or_none()
        if entry:
            entry.days_count = days_count
        else:
            entry = MonthlyWorkDays(year=year, month=month, days_count=days_count)
            db.add(entry)
        await db.flush()
        await db.refresh(entry)
        return entry

    async def get_monthly_work_days(
        self,
        db: AsyncSession,
        year: int,
        month: int,
    ) -> MonthlyWorkDays | None:
        result = await db.execute(
            select(MonthlyWorkDays).where(
                MonthlyWorkDays.year == year,
                MonthlyWorkDays.month == month,
            ),
        )
        return result.scalar_one_or_none()

    # === PayrollDeduction CRUD ===

    async def create_deduction(self, db: AsyncSession, **kwargs) -> PayrollDeduction:
        deduction = PayrollDeduction(**kwargs)
        db.add(deduction)
        await db.flush()
        await db.refresh(deduction)
        return deduction

    async def get_deductions_by_payslip(self, db: AsyncSession, payslip_id: int) -> list[PayrollDeduction]:
        payslip = await db.get(Payslip, payslip_id)
        if not payslip:
            return []
        result = await db.execute(
            select(PayrollDeduction)
            .join(User, User.company_id == PayrollDeduction.company_id)
            .where(
                User.id == payslip.user_id,
                PayrollDeduction.is_active,
            )
            .order_by(PayrollDeduction.priority),
        )
        return list(result.scalars().all())


payroll_repo = PayrollRepository()
