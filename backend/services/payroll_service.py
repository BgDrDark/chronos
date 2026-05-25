from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud.repositories import payroll_repo, settings_repo
from backend.database.models import Payslip, sofia_now
from backend.services.payroll_calculator import PayrollCalculator


class PayrollService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = payroll_repo
        self.settings = settings_repo

    async def get_global_config(self) -> dict[str, Any]:
        hourly_rate = await self.settings.get_setting(self.db, "global_hourly_rate")
        monthly_salary = await self.settings.get_setting(self.db, "global_monthly_salary")
        overtime_multiplier = await self.settings.get_setting(self.db, "global_overtime_multiplier")
        standard_hours_per_day = await self.settings.get_setting(self.db, "global_standard_hours_per_day")
        currency = await self.settings.get_setting(self.db, "global_currency")
        annual_leave_days = await self.settings.get_setting(self.db, "global_annual_leave_days")
        tax_percent = await self.settings.get_setting(self.db, "global_tax_percent")
        health_insurance_percent = await self.settings.get_setting(self.db, "global_health_insurance_percent")
        has_tax_deduction = await self.settings.get_setting(self.db, "global_has_tax_deduction")
        has_health_insurance = await self.settings.get_setting(self.db, "global_has_health_insurance")

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
            "has_health_insurance": (has_health_insurance == "True") if has_health_insurance is not None else True,
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
        admin_user_id: int | None = None,
    ) -> dict[str, Any]:
        await self.settings.set_setting(self.db, "global_hourly_rate", str(hourly_rate))
        await self.settings.set_setting(self.db, "global_monthly_salary", str(monthly_salary))
        await self.settings.set_setting(self.db, "global_overtime_multiplier", str(overtime_multiplier))
        await self.settings.set_setting(self.db, "global_standard_hours_per_day", str(standard_hours_per_day))
        await self.settings.set_setting(self.db, "global_currency", currency)
        await self.settings.set_setting(self.db, "global_annual_leave_days", str(annual_leave_days))
        await self.settings.set_setting(self.db, "global_tax_percent", str(tax_percent))
        await self.settings.set_setting(self.db, "global_health_insurance_percent", str(health_insurance_percent))
        await self.settings.set_setting(self.db, "global_has_tax_deduction", str(has_tax_deduction))
        await self.settings.set_setting(self.db, "global_has_health_insurance", str(has_health_insurance))

        return await self.get_global_config()

    async def calculate_payroll(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        calculator = PayrollCalculator(self.db)
        return await calculator.calculate(user_id, start_date, end_date)

    async def create_payslip(
        self,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        gross_amount: Decimal,
        net_amount: Decimal,
        deductions: dict[str, Decimal],
        tax_amount: Decimal = Decimal(0),
        insurance_amount: Decimal = Decimal(0),
        bonus_amount: Decimal = Decimal(0),
        bonus_description: str = None,
    ) -> Payslip:
        return await self.repo.create_payslip(
            self.db,
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            gross_amount=gross_amount,
            net_amount=net_amount,
            tax_amount=tax_amount,
            insurance_amount=insurance_amount,
            bonus_amount=bonus_amount,
            bonus_description=bonus_description,
            deductions=deductions or {},
            generated_at=sofia_now(),
            is_locked=False,
            is_paid=False,
            payment_date=None,
        )

    async def mark_payslip_as_paid(
        self,
        payslip_id: int,
        payment_date: datetime = None,
        payment_method: str = "bank",
    ) -> Payslip | None:
        return await self.repo.update_payslip(
            self.db, payslip_id,
            is_paid=True,
            payment_date=payment_date or sofia_now(),
        )

    async def set_monthly_work_days(
        self,
        year: int,
        month: int,
        days_count: int,
    ) -> Any:
        return await self.repo.set_monthly_work_days(
            self.db, year, month, days_count,
        )


payroll_service = PayrollService
