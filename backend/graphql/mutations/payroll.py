import datetime
import logging
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend import crud, schemas
from backend.crud.repositories.settings_repo import settings_repo
from backend.database import models
from backend.exceptions import NotFoundException, ValidationException
from backend.graphql import types
from backend.graphql import inputs
from backend.graphql.inputs.payroll import BonusCreateInput
from backend.graphql.utils.permission_checker import (
    get_current_user,
    require_permission,
)

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
        current_user = get_current_user(info)
        
        await require_permission(info, "payroll:read")

        target_date = datetime.date.fromisoformat(date)
        company_id = current_user.company_id

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
        current_user = get_current_user(info)
        
        await require_permission(info, "payroll:read")

        company_id = current_user.company_id

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
        current_user = get_current_user(info)
        
        await require_permission(info, "payroll:read")

        company_id = current_user.company_id

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
            info: strawberry.Info,
            input: BonusCreateInput | None = None,
            user_id: int | None = None,
            amount: float | None = None,
            date: datetime.date | None = None,
            description: str | None = None,
    ) -> types.Bonus:
        db = info.context["db"]
        get_current_user(info)

        await require_permission(info, "payroll:update")

        if input:
            uid, amt, dt, desc = input.user_id, input.amount, input.date, input.description
        else:
            uid, amt, dt, desc = user_id, amount, date, description

        if uid is None or amt is None or dt is None:
            raise ValidationException.field("input", "Липсват задължителни полета")

        bonus = models.Bonus(
            user_id=uid,
            amount=amt,
            date=dt,
            description=desc,
        )
        db.add(bonus)
        await db.commit()
        await db.refresh(bonus)

        return types.Bonus.from_pydantic(schemas.Bonus.model_validate(bonus))

    @strawberry.mutation
    async def remove_bonus(
            self,
            id: int,
            info: strawberry.Info
    ) -> bool:
        db = info.context["db"]
        get_current_user(info)

        await require_permission(info, "payroll:update")

        bonus = await db.get(models.Bonus, id)
        if not bonus:
            raise NotFoundException(f"Бонус {id} не е намерен")

        await db.delete(bonus)
        await db.commit()

        return True

    @strawberry.mutation
    async def generate_payslip(
            self,
            user_id: int,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info
    ) -> types.Payslip:
        db = info.context["db"]
        current_user = get_current_user(info)

        await require_permission(info, "payroll:create")

        from backend.services.payroll_service import PayrollService

        svc = PayrollService(db)
        payslip = await svc.generate_payslip(
            user_id, start_date, end_date, current_user.id
        )

        return types.Payslip.from_pydantic(schemas.Payslip.model_validate(payslip))

    @strawberry.mutation
    async def generate_my_payslip(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info
    ) -> types.Payslip:
        db = info.context["db"]
        current_user = get_current_user(info)

        await require_permission(info, "payroll:create_own")

        from backend.services.payroll_service import PayrollService

        svc = PayrollService(db)
        payslip = await svc.generate_payslip(
            current_user.id, start_date, end_date, current_user.id
        )

        return types.Payslip.from_pydantic(schemas.Payslip.model_validate(payslip))

    @strawberry.mutation
    async def generate_all_payslips(
            self,
            start_date: datetime.date,
            end_date: datetime.date,
            info: strawberry.Info
    ) -> list[types.Payslip]:
        db = info.context["db"]
        current_user = get_current_user(info)

        await require_permission(info, "payroll:create")

        from backend.services.payroll_service import PayrollService

        svc = PayrollService(db)
        payslips = await svc.generate_all_payslips(
            current_user.company_id, start_date, end_date, current_user.id
        )

        return [types.Payslip.from_pydantic(schemas.Payslip.model_validate(p)) for p in payslips]

    @strawberry.mutation
    async def mark_payslip_as_paid(
            self,
            payslip_id: int,
            info: strawberry.Info
    ) -> types.Payslip:
        """Mark a payslip as paid"""
        db = info.context["db"]
        get_current_user(info)
        
        await require_permission(info, "payroll:update")

        payslip = await db.get(models.Payslip, payslip_id)
        if not payslip:
            raise Exception(f"Payslip {payslip_id} not found")

        payslip.payment_status = "paid"
        payslip.actual_payment_date = datetime.datetime.now()

        await db.commit()
        await db.refresh(payslip)

        return types.Payslip.from_pydantic(schemas.Payslip.model_validate(payslip))

    @strawberry.mutation
    async def bulk_mark_payslips_as_paid(
            self,
            payslip_ids: list[int],
            info: strawberry.Info
    ) -> list[types.Payslip]:
        """Mark multiple payslips as paid"""
        db = info.context["db"]
        get_current_user(info)
        
        await require_permission(info, "payroll:update")

        payslips = []
        for payslip_id in payslip_ids:
            payslip = await db.get(models.Payslip, payslip_id)
            if payslip:
                payslip.payment_status = "paid"
                payslip.actual_payment_date = datetime.datetime.now()
                payslips.append(payslip)

        await db.commit()
        for p in payslips:
            await db.refresh(p)

        return [types.Payslip.from_pydantic(schemas.Payslip.model_validate(p)) for p in payslips]

    @strawberry.mutation
    async def create_payment_batch(
        self,
        info: strawberry.Info,
        input: inputs.CreatePaymentBatchInput,
    ) -> types.SalaryPaymentBatchType:
        from backend.services.salary_payment_service import SalaryPaymentService
        db = info.context["db"]
        user = get_current_user(info)
        await require_permission(info, "payroll:update")

        company_id = input.company_id or user.company_id
        if not company_id:
            from backend.exceptions import ValidationException
            raise ValidationException("Не е зададена фирма")

        service = SalaryPaymentService(db)
        batch = await service.create_batch(
            company_id=company_id,
            period_start=input.period_start,
            period_end=input.period_end,
            payment_date=input.payment_date,
            payment_method=input.payment_method,
            paid_by=user.id,
            payment_reference=input.payment_reference,
            notes=input.notes,
        )
        await db.commit()
        return types.SalaryPaymentBatchType(
            id=batch.id,
            company_id=batch.company_id,
            period_start=batch.period_start,
            period_end=batch.period_end,
            payment_date=batch.payment_date,
            total_amount=float(batch.total_amount),
            status=batch.status,
            payment_method=batch.payment_method,
            payment_reference=batch.payment_reference,
            notes=batch.notes,
            created_at=batch.created_at,
            paid_by=batch.paid_by,
        )

    @strawberry.mutation
    async def add_items_to_batch(
        self,
        info: strawberry.Info,
        input: inputs.AddItemsToBatchInput,
    ) -> types.SalaryPaymentBatchType:
        from backend.services.salary_payment_service import SalaryPaymentService
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "payroll:update")

        service = SalaryPaymentService(db)
        batch = await service.add_items(batch_id=input.batch_id, user_ids=input.user_ids)
        await db.commit()
        return types.SalaryPaymentBatchType(
            id=batch.id,
            company_id=batch.company_id,
            period_start=batch.period_start,
            period_end=batch.period_end,
            payment_date=batch.payment_date,
            total_amount=float(batch.total_amount),
            status=batch.status,
            payment_method=batch.payment_method,
            payment_reference=batch.payment_reference,
            notes=batch.notes,
            created_at=batch.created_at,
            paid_by=batch.paid_by,
        )

    @strawberry.mutation
    async def complete_payment_batch(
        self,
        info: strawberry.Info,
        batch_id: int,
    ) -> types.SalaryPaymentBatchType:
        from backend.services.salary_payment_service import SalaryPaymentService
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "payroll:update")

        service = SalaryPaymentService(db)
        batch = await service.complete_batch(batch_id)
        await db.commit()
        return types.SalaryPaymentBatchType(
            id=batch.id,
            company_id=batch.company_id,
            period_start=batch.period_start,
            period_end=batch.period_end,
            payment_date=batch.payment_date,
            total_amount=float(batch.total_amount),
            status=batch.status,
            payment_method=batch.payment_method,
            payment_reference=batch.payment_reference,
            notes=batch.notes,
            created_at=batch.created_at,
            paid_by=batch.paid_by,
        )

    @strawberry.mutation
    async def cancel_payment_batch(
        self,
        info: strawberry.Info,
        batch_id: int,
    ) -> types.SalaryPaymentBatchType:
        from backend.services.salary_payment_service import SalaryPaymentService
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "payroll:update")

        service = SalaryPaymentService(db)
        batch = await service.cancel_batch(batch_id)
        await db.commit()
        return types.SalaryPaymentBatchType(
            id=batch.id,
            company_id=batch.company_id,
            period_start=batch.period_start,
            period_end=batch.period_end,
            payment_date=batch.payment_date,
            total_amount=float(batch.total_amount),
            status=batch.status,
            payment_method=batch.payment_method,
            payment_reference=batch.payment_reference,
            notes=batch.notes,
            created_at=batch.created_at,
            paid_by=batch.paid_by,
        )

    @strawberry.mutation
    async def generate_sepa_xml(
            self,
            payslip_ids: list[int],
            info: strawberry.Info
    ) -> str:
        """Generate SEPA XML file for payslips"""
        db = info.context["db"]
        get_current_user(info)
        
        await require_permission(info, "payroll:export")

        from backend.services.payroll_service import PayrollService

        svc = PayrollService(db)
        xml_content = await svc.generate_sepa_xml(payslip_ids)

        return xml_content

    @strawberry.mutation
    async def update_payroll_legal_settings(
        self,
        info: strawberry.Info,
        max_insurance_base: float,
        employee_insurance_rate: float,
        income_tax_rate: float,
        civil_contract_costs_rate: float,
        noi_compensation_percent: float,
        employer_paid_sick_days: int,
        default_tax_resident: bool,
        trz_compliance_strict_mode: bool,
    ) -> types.PayrollLegalSettings:
        db = info.context["db"]
        get_current_user(info)
        await require_permission(info, "system:manage_settings")

        await settings_repo.set_setting(db, "payroll_max_insurance_base", str(max_insurance_base))
        await settings_repo.set_setting(db, "payroll_employee_insurance_rate", str(employee_insurance_rate))
        await settings_repo.set_setting(db, "payroll_income_tax_rate", str(income_tax_rate))
        await settings_repo.set_setting(db, "payroll_civil_contract_costs_rate", str(civil_contract_costs_rate))
        await settings_repo.set_setting(db, "payroll_noi_compensation_percent", str(noi_compensation_percent))
        await settings_repo.set_setting(db, "payroll_employer_paid_sick_days", str(employer_paid_sick_days))
        await settings_repo.set_setting(db, "payroll_default_tax_resident", str(default_tax_resident).lower())
        await settings_repo.set_setting(db, "trz_compliance_strict_mode", str(trz_compliance_strict_mode).lower())

        await db.commit()

        return types.PayrollLegalSettings(
            max_insurance_base=max_insurance_base,
            employee_insurance_rate=employee_insurance_rate,
            income_tax_rate=income_tax_rate,
            civil_contract_costs_rate=civil_contract_costs_rate,
            noi_compensation_percent=noi_compensation_percent,
            employer_paid_sick_days=employer_paid_sick_days,
            default_tax_resident=default_tax_resident,
            trz_compliance_strict_mode=trz_compliance_strict_mode,
        )

    @strawberry.mutation
    async def update_global_payroll_config(
        self,
        info: strawberry.Info,
        hourly_rate: Decimal,
        monthly_salary: Decimal,
        overtime_multiplier: Decimal,
        standard_hours_per_day: int,
        currency: str,
        annual_leave_days: int,
        tax_percent: Decimal,
        health_insurance_percent: Decimal,
        has_tax_deduction: bool,
        has_health_insurance: bool,
        qr_regen_interval_minutes: int,
    ) -> types.GlobalPayrollConfig:
        db = info.context["db"]
        current_user = get_current_user(info)
        await require_permission(info, "system:manage_settings")

        await crud.update_global_payroll_config(
            db,
            hourly_rate=float(hourly_rate),
            monthly_salary=float(monthly_salary),
            overtime_multiplier=float(overtime_multiplier),
            standard_hours_per_day=standard_hours_per_day,
            currency=currency,
            annual_leave_days=annual_leave_days,
            tax_percent=float(tax_percent),
            health_insurance_percent=float(health_insurance_percent),
            has_tax_deduction=has_tax_deduction,
            has_health_insurance=has_health_insurance,
            admin_user_id=current_user.id,
        )

        await db.commit()

        return types.GlobalPayrollConfig(
            hourly_rate=hourly_rate,
            monthly_salary=monthly_salary,
            overtime_multiplier=overtime_multiplier,
            standard_hours_per_day=standard_hours_per_day,
            currency=currency,
            annual_leave_days=annual_leave_days,
            tax_percent=tax_percent,
            health_insurance_percent=health_insurance_percent,
            has_tax_deduction=has_tax_deduction,
            has_health_insurance=has_health_insurance,
            qr_regen_interval_minutes=qr_regen_interval_minutes,
        )
