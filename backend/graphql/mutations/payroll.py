import datetime
import logging
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend.database import models
from backend.exceptions import AuthenticationException
from backend.graphql import inputs, types

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class PayrollMutation:
    @strawberry.mutation
    async def generate_daily_summary(
        self,
        date: str,
        info: strawberry.Info,
    ) -> types.DailySummaryType:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        target_date = datetime.date.fromisoformat(date)

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            raise AuthenticationException(detail=authenticate_msg)

        invoices_stmt = select(models.Invoice).where(
            models.Invoice.date == target_date,
            models.Invoice.company_id == company_id,
        )
        invoices_result = await db.execute(invoices_stmt)
        invoices = invoices_result.scalars().all()

        cash_stmt = select(models.CashJournalEntry).where(
            models.CashJournalEntry.date == target_date,
            models.CashJournalEntry.company_id == company_id,
        )
        cash_result = await db.execute(cash_stmt)
        cash_entries = cash_result.scalars().all()

        invoices_count = len(invoices)
        incoming_invoices_count = sum(1 for i in invoices if i.type == "incoming")
        outgoing_invoices_count = sum(1 for i in invoices if i.type == "outgoing")

        invoices_total = sum(float(i.total or 0) for i in invoices)
        incoming_invoices_total = sum(
            float(i.total or 0) for i in invoices if i.type == "incoming"
        )
        outgoing_invoices_total = sum(
            float(i.total or 0) for i in invoices if i.type == "outgoing"
        )

        cash_income = sum(
            float(c.amount or 0) for c in cash_entries if c.operation_type == "income"
        )
        cash_expense = sum(
            float(c.amount or 0) for c in cash_entries if c.operation_type == "expense"
        )
        cash_balance = cash_income - cash_expense

        vat_collected = sum(
            float(i.vat_amount or 0) for i in invoices if i.type == "outgoing"
        )
        vat_paid = sum(
            float(i.vat_amount or 0) for i in invoices if i.type == "incoming"
        )

        paid_invoices_count = sum(1 for i in invoices if i.status == "paid")
        unpaid_invoices_count = sum(
            1 for i in invoices if i.status in ["draft", "sent"]
        )
        overdue_invoices_count = sum(1 for i in invoices if i.status == "overdue")

        existing_stmt = select(models.DailySummary).where(
            models.DailySummary.date == target_date,
            models.DailySummary.company_id == company_id,
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            existing.invoices_count = invoices_count
            existing.incoming_invoices_count = incoming_invoices_count
            existing.outgoing_invoices_count = outgoing_invoices_count
            existing.invoices_total = Decimal(str(invoices_total))
            existing.incoming_invoices_total = Decimal(str(incoming_invoices_total))
            existing.outgoing_invoices_total = Decimal(str(outgoing_invoices_total))
            existing.cash_income = Decimal(str(cash_income))
            existing.cash_expense = Decimal(str(cash_expense))
            existing.cash_balance = Decimal(str(cash_balance))
            existing.vat_collected = Decimal(str(vat_collected))
            existing.vat_paid = Decimal(str(vat_paid))
            existing.paid_invoices_count = paid_invoices_count
            existing.unpaid_invoices_count = unpaid_invoices_count
            existing.overdue_invoices_count = overdue_invoices_count
            summary = existing
        else:
            summary = models.DailySummary(
                date=target_date,
                invoices_count=invoices_count,
                incoming_invoices_count=incoming_invoices_count,
                outgoing_invoices_count=outgoing_invoices_count,
                invoices_total=Decimal(str(invoices_total)),
                incoming_invoices_total=Decimal(str(incoming_invoices_total)),
                outgoing_invoices_total=Decimal(str(outgoing_invoices_total)),
                cash_income=Decimal(str(cash_income)),
                cash_expense=Decimal(str(cash_expense)),
                cash_balance=Decimal(str(cash_balance)),
                vat_collected=Decimal(str(vat_collected)),
                vat_paid=Decimal(str(vat_paid)),
                paid_invoices_count=paid_invoices_count,
                unpaid_invoices_count=unpaid_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                company_id=company_id,
            )
            db.add(summary)

        await db.commit()
        await db.refresh(summary)
        return types.DailySummaryType.from_instance(summary)

    @strawberry.mutation
    async def generate_monthly_summary(
        self,
        year: int,
        month: int,
        info: strawberry.Info,
    ) -> types.MonthlySummaryType:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            raise AuthenticationException(detail=authenticate_msg)

        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        invoices_stmt = select(models.Invoice).where(
            models.Invoice.date >= start_date,
            models.Invoice.date <= end_date,
            models.Invoice.company_id == company_id,
        )
        invoices_result = await db.execute(invoices_stmt)
        invoices = invoices_result.scalars().all()

        cash_stmt = select(models.CashJournalEntry).where(
            models.CashJournalEntry.date >= start_date,
            models.CashJournalEntry.date <= end_date,
            models.CashJournalEntry.company_id == company_id,
        )
        cash_result = await db.execute(cash_stmt)
        cash_entries = cash_result.scalars().all()

        invoices_count = len(invoices)
        incoming_invoices_count = sum(1 for i in invoices if i.type == "incoming")
        outgoing_invoices_count = sum(1 for i in invoices if i.type == "outgoing")

        invoices_total = sum(float(i.total or 0) for i in invoices)
        incoming_invoices_total = sum(
            float(i.total or 0) for i in invoices if i.type == "incoming"
        )
        outgoing_invoices_total = sum(
            float(i.total or 0) for i in invoices if i.type == "outgoing"
        )

        cash_income = sum(
            float(c.amount or 0) for c in cash_entries if c.operation_type == "income"
        )
        cash_expense = sum(
            float(c.amount or 0) for c in cash_entries if c.operation_type == "expense"
        )
        cash_balance = cash_income - cash_expense

        vat_collected = sum(
            float(i.vat_amount or 0) for i in invoices if i.type == "outgoing"
        )
        vat_paid = sum(
            float(i.vat_amount or 0) for i in invoices if i.type == "incoming"
        )

        paid_invoices_count = sum(1 for i in invoices if i.status == "paid")
        unpaid_invoices_count = sum(
            1 for i in invoices if i.status in ["draft", "sent"]
        )
        overdue_invoices_count = sum(1 for i in invoices if i.status == "overdue")

        existing_stmt = select(models.MonthlySummary).where(
            models.MonthlySummary.year == year,
            models.MonthlySummary.month == month,
            models.MonthlySummary.company_id == company_id,
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            existing.invoices_count = invoices_count
            existing.incoming_invoices_count = incoming_invoices_count
            existing.outgoing_invoices_count = outgoing_invoices_count
            existing.invoices_total = Decimal(str(invoices_total))
            existing.incoming_invoices_total = Decimal(str(incoming_invoices_total))
            existing.outgoing_invoices_total = Decimal(str(outgoing_invoices_total))
            existing.cash_income = Decimal(str(cash_income))
            existing.cash_expense = Decimal(str(cash_expense))
            existing.cash_balance = Decimal(str(cash_balance))
            existing.vat_collected = Decimal(str(vat_collected))
            existing.vat_paid = Decimal(str(vat_paid))
            existing.paid_invoices_count = paid_invoices_count
            existing.unpaid_invoices_count = unpaid_invoices_count
            existing.overdue_invoices_count = overdue_invoices_count
            summary = existing
        else:
            summary = models.MonthlySummary(
                year=year,
                month=month,
                invoices_count=invoices_count,
                incoming_invoices_count=incoming_invoices_count,
                outgoing_invoices_count=outgoing_invoices_count,
                invoices_total=Decimal(str(invoices_total)),
                incoming_invoices_total=Decimal(str(incoming_invoices_total)),
                outgoing_invoices_total=Decimal(str(outgoing_invoices_total)),
                cash_income=Decimal(str(cash_income)),
                cash_expense=Decimal(str(cash_expense)),
                cash_balance=Decimal(str(cash_balance)),
                vat_collected=Decimal(str(vat_collected)),
                vat_paid=Decimal(str(vat_paid)),
                paid_invoices_count=paid_invoices_count,
                unpaid_invoices_count=unpaid_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                company_id=company_id,
            )
            db.add(summary)

        await db.commit()
        await db.refresh(summary)
        return types.MonthlySummaryType.from_instance(summary)

    @strawberry.mutation
    async def generate_yearly_summary(
        self,
        year: int,
        info: strawberry.Info,
    ) -> types.YearlySummaryType:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        if current_user.role.name != "super_admin":
            company_id = current_user.company_id
        else:
            raise AuthenticationException(detail=authenticate_msg)

        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)

        invoices_stmt = select(models.Invoice).where(
            models.Invoice.date >= start_date,
            models.Invoice.date <= end_date,
            models.Invoice.company_id == company_id,
        )
        invoices_result = await db.execute(invoices_stmt)
        invoices = invoices_result.scalars().all()

        cash_stmt = select(models.CashJournalEntry).where(
            models.CashJournalEntry.date >= start_date,
            models.CashJournalEntry.date <= end_date,
            models.CashJournalEntry.company_id == company_id,
        )
        cash_result = await db.execute(cash_stmt)
        cash_entries = cash_result.scalars().all()

        invoices_count = len(invoices)
        incoming_invoices_count = sum(1 for i in invoices if i.type == "incoming")
        outgoing_invoices_count = sum(1 for i in invoices if i.type == "outgoing")

        invoices_total = sum(float(i.total or 0) for i in invoices)
        incoming_invoices_total = sum(
            float(i.total or 0) for i in invoices if i.type == "incoming"
        )
        outgoing_invoices_total = sum(
            float(i.total or 0) for i in invoices if i.type == "outgoing"
        )

        cash_income = sum(
            float(c.amount or 0) for c in cash_entries if c.operation_type == "income"
        )
        cash_expense = sum(
            float(c.amount or 0) for c in cash_entries if c.operation_type == "expense"
        )
        cash_balance = cash_income - cash_expense

        vat_collected = sum(
            float(i.vat_amount or 0) for i in invoices if i.type == "outgoing"
        )
        vat_paid = sum(
            float(i.vat_amount or 0) for i in invoices if i.type == "incoming"
        )

        paid_invoices_count = sum(1 for i in invoices if i.status == "paid")
        unpaid_invoices_count = sum(
            1 for i in invoices if i.status in ["draft", "sent"]
        )
        overdue_invoices_count = sum(1 for i in invoices if i.status == "overdue")

        existing_stmt = select(models.YearlySummary).where(
            models.YearlySummary.year == year,
            models.YearlySummary.company_id == company_id,
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            existing.invoices_count = invoices_count
            existing.incoming_invoices_count = incoming_invoices_count
            existing.outgoing_invoices_count = outgoing_invoices_count
            existing.invoices_total = Decimal(str(invoices_total))
            existing.incoming_invoices_total = Decimal(str(incoming_invoices_total))
            existing.outgoing_invoices_total = Decimal(str(outgoing_invoices_total))
            existing.cash_income = Decimal(str(cash_income))
            existing.cash_expense = Decimal(str(cash_expense))
            existing.cash_balance = Decimal(str(cash_balance))
            existing.vat_collected = Decimal(str(vat_collected))
            existing.vat_paid = Decimal(str(vat_paid))
            existing.paid_invoices_count = paid_invoices_count
            existing.unpaid_invoices_count = unpaid_invoices_count
            existing.overdue_invoices_count = overdue_invoices_count
            summary = existing
        else:
            summary = models.YearlySummary(
                year=year,
                invoices_count=invoices_count,
                incoming_invoices_count=incoming_invoices_count,
                outgoing_invoices_count=outgoing_invoices_count,
                invoices_total=Decimal(str(invoices_total)),
                incoming_invoices_total=Decimal(str(incoming_invoices_total)),
                outgoing_invoices_total=Decimal(str(outgoing_invoices_total)),
                cash_income=Decimal(str(cash_income)),
                cash_expense=Decimal(str(cash_expense)),
                cash_balance=Decimal(str(cash_balance)),
                vat_collected=Decimal(str(vat_collected)),
                vat_paid=Decimal(str(vat_paid)),
                paid_invoices_count=paid_invoices_count,
                unpaid_invoices_count=unpaid_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                company_id=company_id,
            )
            db.add(summary)

        await db.commit()
        await db.refresh(summary)
        return types.YearlySummaryType.from_instance(summary)

    @strawberry.mutation
    async def add_bonus(
            self,
            employee_id: int,
            amount: Decimal,
            description: str,
            info: strawberry.Info
    ) -> types.Bonus:
        """Add a bonus to an employee"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        bonus = models.Bonus(
            employee_id=employee_id,
            amount=amount,
            description=description,
            created_by=current_user.id
        )
        db.add(bonus)
        await db.commit()
        await db.refresh(bonus)

        return types.Bonus.from_instance(bonus)

    @strawberry.mutation
    async def remove_bonus(
            self,
            bonus_id: int,
            info: strawberry.Info
    ) -> bool:
        """Remove a bonus"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        bonus = await db.get(models.Bonus, bonus_id)
        if not bonus:
            raise Exception(f"Bonus {bonus_id} not found")

        await db.delete(bonus)
        await db.commit()

        return True

    @strawberry.mutation
    async def generate_payslip(
            self,
            employee_id: int,
            period_start: datetime.date,
            period_end: datetime.date,
            info: strawberry.Info
    ) -> types.Payslip:
        """Generate a payslip for an employee"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.services import payroll_service

        payslip = await payroll_service.generate_payslip(
            db, employee_id, period_start, period_end, current_user.id
        )

        return types.Payslip.from_instance(payslip)

    @strawberry.mutation
    async def generate_my_payslip(
            self,
            period_start: datetime.date,
            period_end: datetime.date,
            info: strawberry.Info
    ) -> types.Payslip:
        """Generate payslip for current user"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.services import payroll_service

        payslip = await payroll_service.generate_payslip(
            db, current_user.id, period_start, period_end, current_user.id
        )

        return types.Payslip.from_instance(payslip)

    @strawberry.mutation
    async def mark_payslip_as_paid(
            self,
            payslip_id: int,
            info: strawberry.Info
    ) -> types.Payslip:
        """Mark a payslip as paid"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        payslip = await db.get(models.Payslip, payslip_id)
        if not payslip:
            raise Exception(f"Payslip {payslip_id} not found")

        payslip.status = "paid"
        payslip.paid_at = datetime.datetime.now()

        await db.commit()
        await db.refresh(payslip)

        return types.Payslip.from_instance(payslip)

    @strawberry.mutation
    async def bulk_mark_payslips_as_paid(
            self,
            payslip_ids: list[int],
            info: strawberry.Info
    ) -> list[types.Payslip]:
        """Mark multiple payslips as paid"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        payslips = []
        for payslip_id in payslip_ids:
            payslip = await db.get(models.Payslip, payslip_id)
            if payslip:
                payslip.status = "paid"
                payslip.paid_at = datetime.datetime.now()
                payslips.append(payslip)

        await db.commit()
        for p in payslips:
            await db.refresh(p)

        return [types.Payslip.from_instance(p) for p in payslips]

    @strawberry.mutation
    async def generate_sepa_xml(
            self,
            payslip_ids: list[int],
            info: strawberry.Info
    ) -> str:
        """Generate SEPA XML file for payslips"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.services import payroll_service

        xml_content = await payroll_service.generate_sepa_xml(db, payslip_ids)

        return xml_content
