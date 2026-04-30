from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import (
    Payroll, Payslip, User, GlobalSetting, sofia_now
)
from backend.services.payroll_calculator import PayrollCalculator


class PayrollService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_global_config(self) -> Dict[str, Any]:
        """Get global payroll configuration"""
        hourly_rate = await self._get_setting("global_hourly_rate")
        monthly_salary = await self._get_setting("global_monthly_salary")
        overtime_multiplier = await self._get_setting("global_overtime_multiplier")
        standard_hours_per_day = await self._get_setting("global_standard_hours_per_day")
        currency = await self._get_setting("global_currency")
        annual_leave_days = await self._get_setting("global_annual_leave_days")
        tax_percent = await self._get_setting("global_tax_percent")
        health_insurance_percent = await self._get_setting("global_health_insurance_percent")
        has_tax_deduction = await self._get_setting("global_has_tax_deduction")
        has_health_insurance = await self._get_setting("global_has_health_insurance")

        return {
            "hourly_rate": float(hourly_rate) if hourly_rate else 0.0,
            "monthly_salary": float(monthly_salary) if monthly_salary else 0.0,
            "overtime_multiplier": float(overtime_multiplier) if overtime_multiplier else 1,
            "standard_hours_per_day": int(standard_hours_per_day) if standard_hours_per_day else 8,
            "currency": currency or "EUR",
            "annual_leave_days": int(annual_leave_days) if annual_leave_days else 20,
            "tax_percent": float(tax_percent) if tax_percent else 10.00,
            "health_insurance_percent": float(health_insurance_percent) if health_insurance_percent else 13.78,
            "has_tax_deduction": (has_tax_deduction == "True") if has_tax_deduction is not None else True,
            "has_health_insurance": (has_health_insurance == "True") if has_health_insurance is not None else True
        }

    async def update_global_config(
        self,
        hourly_rate: float,
        overtime_multiplier: float,
        standard_hours_per_day: int,
        monthly_salary: float,
        currency: str,
        annual_leave_days: int,
        tax_percent: float,
        health_insurance_percent: float,
        has_tax_deduction: bool,
        has_health_insurance: bool,
        admin_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update global payroll configuration"""
        await self._set_setting("global_hourly_rate", str(hourly_rate))
        await self._set_setting("global_monthly_salary", str(monthly_salary))
        await self._set_setting("global_overtime_multiplier", str(overtime_multiplier))
        await self._set_setting("global_standard_hours_per_day", str(standard_hours_per_day))
        await self._set_setting("global_currency", currency)
        await self._set_setting("global_annual_leave_days", str(annual_leave_days))
        await self._set_setting("global_tax_percent", str(tax_percent))
        await self._set_setting("global_health_insurance_percent", str(health_insurance_percent))
        await self._set_setting("global_has_tax_deduction", str(has_tax_deduction))
        await self._set_setting("global_has_health_insurance", str(has_health_insurance))

        return await self.get_global_config()

    async def calculate_payroll(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate payroll for a user"""
        calculator = PayrollCalculator(self.db)
        return await calculator.calculate(user_id, start_date, end_date)

    async def create_payslip(
        self,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        gross_amount: Decimal,
        net_amount: Decimal,
        deductions: Dict[str, Decimal],
        tax_amount: Decimal = Decimal("0"),
        insurance_amount: Decimal = Decimal("0"),
        bonus_amount: Decimal = Decimal("0"),
        bonus_description: str = None
    ) -> Payslip:
        """Create a payslip for a user"""
        payslip = Payslip(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            gross_amount=gross_amount,
            net_amount=net_amount,
            tax_amount=tax_amount,
            insurance_amount=insurance_amount,
            bonus_amount=bonus_amount,
            bonus_description=bonus_description,
            deductions=deductions if deductions else {},
            generated_at=sofia_now(),
            is_locked=False,
            is_paid=False,
            payment_date=None
        )
        self.db.add(payslip)
        await self.db.commit()
        await self.db.refresh(payslip)
        return payslip

    async def mark_payslip_as_paid(
        self,
        payslip_id: int,
        payment_date: datetime = None,
        payment_method: str = "bank"
    ) -> Optional[Payslip]:
        """Mark a payslip as paid"""
        stmt = select(Payslip).where(Payslip.id == payslip_id)
        result = await self.db.execute(stmt)
        payslip = result.scalars().first()

        if payslip:
            payslip.is_paid = True
            payslip.payment_date = payment_date or sofia_now()
            self.db.add(payslip)
            await self.db.commit()
            await self.db.refresh(payslip)

        return payslip

    async def set_monthly_work_days(
        self,
        year: int,
        month: int,
        days_count: int
    ) -> Any:
        """Set custom work days for a month"""
        from backend.database.models import MonthlyWorkDays

        stmt = select(MonthlyWorkDays).where(
            MonthlyWorkDays.year == year,
            MonthlyWorkDays.month == month
        )
        result = await self.db.execute(stmt)
        existing = result.scalars().first()

        if existing:
            existing.days_count = days_count
            self.db.add(existing)
        else:
            new_record = MonthlyWorkDays(
                year=year,
                month=month,
                days_count=days_count
            )
            self.db.add(new_record)

        await self.db.commit()
        return existing

    async def _get_setting(self, key: str) -> Optional[str]:
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()
        return setting.value if setting else None

    async def _set_setting(self, key: str, value: str) -> None:
        stmt = select(GlobalSetting).where(GlobalSetting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalars().first()

        if setting:
            setting.value = value
            self.db.add(setting)
        else:
            new_setting = GlobalSetting(key=key, value=value)
            self.db.add(new_setting)

        await self.db.flush()


payroll_service = PayrollService