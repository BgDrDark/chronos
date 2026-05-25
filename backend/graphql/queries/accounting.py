import datetime

import strawberry
from sqlalchemy import select

from backend.exceptions import (
    AuthenticationException,
)
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class AccountingQuery:
    @strawberry.field
    async def invoices(
        self,
        info: strawberry.Info,
        type: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[types.Invoice]:
        """Get all invoices, optionally filtered by type and status"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        stmt = select(Invoice)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Invoice.company_id == current_user.company_id)

        if type:
            stmt = stmt.where(Invoice.type == type)
        if status:
            stmt = stmt.where(Invoice.status == status)
        if search:
            stmt = stmt.where(
                (Invoice.number.ilike(f"%{search}%")) |
                (Invoice.client_name.ilike(f"%{search}%")),
            )

        stmt = stmt.order_by(Invoice.date.desc(), Invoice.id.desc())

        res = await db.execute(stmt)
        return [types.Invoice.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def invoice(self, info: strawberry.Info, id: int) -> types.Invoice | None:
        """Get a single invoice by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        invoice = await db.get(Invoice, id)
        if not invoice:
            return None

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            return None

        return types.Invoice.from_pydantic(invoice)

    @strawberry.field
    async def invoice_by_number(self, info: strawberry.Info, number: str) -> types.Invoice | None:
        """Get a single invoice by number"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        stmt = select(Invoice).where(Invoice.number == number)
        res = await db.execute(stmt)
        invoice = res.scalars().first()
        if not invoice:
            return None

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            return None

        return types.Invoice.from_pydantic(invoice)

    @strawberry.field
    async def cash_journal_entries(
        self,
        info: strawberry.Info,
        start_date: str | None = None,
        end_date: str | None = None,
        operation_type: str | None = None,
    ) -> list[types.CashJournalEntryType]:
        """Get cash journal entries, optionally filtered"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        import datetime

        from backend.database.models import CashJournalEntry
        stmt = select(CashJournalEntry)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(CashJournalEntry.company_id == current_user.company_id)

        if start_date:
            stmt = stmt.where(CashJournalEntry.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(CashJournalEntry.date <= datetime.date.fromisoformat(end_date))
        if operation_type:
            stmt = stmt.where(CashJournalEntry.operation_type == operation_type)

        stmt = stmt.order_by(CashJournalEntry.date.desc(), CashJournalEntry.id.desc())

        res = await db.execute(stmt)
        return [types.CashJournalEntryType.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def operation_logs(
        self,
        info: strawberry.Info,
        start_date: str | None = None,
        end_date: str | None = None,
        operation: str | None = None,
        entity_type: str | None = None,
    ) -> list[types.OperationLogType]:
        """Get operation logs, optionally filtered"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        import datetime

        from backend.database.models import OperationLog
        stmt = select(OperationLog)

        if start_date:
            start_dt = datetime.datetime.fromisoformat(start_date)
            stmt = stmt.where(OperationLog.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.datetime.fromisoformat(end_date)
            stmt = stmt.where(OperationLog.timestamp <= end_dt)
        if operation:
            stmt = stmt.where(OperationLog.operation == operation)
        if entity_type:
            stmt = stmt.where(OperationLog.entity_type == entity_type)

        stmt = stmt.order_by(OperationLog.timestamp.desc())

        res = await db.execute(stmt)
        return [types.OperationLogType.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def daily_summaries(
        self,
        info: strawberry.Info,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[types.DailySummaryType]:
        """Get daily summaries, optionally filtered by date range"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        import datetime

        from backend.database.models import DailySummary
        stmt = select(DailySummary)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(DailySummary.company_id == current_user.company_id)

        if start_date:
            stmt = stmt.where(DailySummary.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(DailySummary.date <= datetime.date.fromisoformat(end_date))

        stmt = stmt.order_by(DailySummary.date.desc())

        res = await db.execute(stmt)
        return [types.DailySummaryType.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def monthly_summaries(
        self,
        info: strawberry.Info,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[types.MonthlySummaryType]:
        """Get monthly summaries, optionally filtered by year range"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import MonthlySummary
        stmt = select(MonthlySummary)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(MonthlySummary.company_id == current_user.company_id)

        if start_year:
            stmt = stmt.where(MonthlySummary.year >= start_year)
        if end_year:
            stmt = stmt.where(MonthlySummary.year <= end_year)

        stmt = stmt.order_by(MonthlySummary.year.desc(), MonthlySummary.month.desc())

        res = await db.execute(stmt)
        return [types.MonthlySummaryType.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def yearly_summaries(
        self,
        info: strawberry.Info,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[types.YearlySummaryType]:
        """Get yearly summaries, optionally filtered by year range"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import YearlySummary
        stmt = select(YearlySummary)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(YearlySummary.company_id == current_user.company_id)

        if start_year:
            stmt = stmt.where(YearlySummary.year >= start_year)
        if end_year:
            stmt = stmt.where(YearlySummary.year <= end_year)

        stmt = stmt.order_by(YearlySummary.year.desc())

        res = await db.execute(stmt)
        return [types.YearlySummaryType.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def proforma_invoices(
        self,
        info: strawberry.Info,
        status: str | None = None,
        search: str | None = None,
    ) -> list[types.ProformaInvoice]:
        """Get all proforma invoices"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice
        stmt = select(Invoice).where(Invoice.type == "proforma")

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Invoice.company_id == current_user.company_id)

        if status:
            stmt = stmt.where(Invoice.status == status)
        if search:
            stmt = stmt.where(
                (Invoice.number.ilike(f"%{search}%")) |
                (Invoice.client_name.ilike(f"%{search}%")),
            )

        stmt = stmt.order_by(Invoice.date.desc(), Invoice.id.desc())

        res = await db.execute(stmt)
        return [types.ProformaInvoice.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def invoice_corrections(
        self,
        info: strawberry.Info,
        type: str | None = None,
        status: str | None = None,
    ) -> list[types.InvoiceCorrection]:
        """Get all invoice corrections (credit/debit notes)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from sqlalchemy.orm import selectinload

        from backend.database.models import InvoiceCorrection
        stmt = select(InvoiceCorrection).options(selectinload(InvoiceCorrection.original_invoice))

        if current_user.role.name != "super_admin":
            stmt = stmt.where(InvoiceCorrection.company_id == current_user.company_id)

        if type:
            stmt = stmt.where(InvoiceCorrection.type == type)
        if status:
            stmt = stmt.where(InvoiceCorrection.status == status)

        stmt = stmt.order_by(InvoiceCorrection.correction_date.desc(), InvoiceCorrection.id.desc())

        res = await db.execute(stmt)
        return [types.InvoiceCorrection.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def invoice_correction(self, info: strawberry.Info, id: int) -> types.InvoiceCorrection | None:
        """Get a single invoice correction by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from sqlalchemy.orm import selectinload

        from backend.database.models import InvoiceCorrection
        stmt = select(InvoiceCorrection).options(
            selectinload(InvoiceCorrection.original_invoice),
        ).where(InvoiceCorrection.id == id)
        res = await db.execute(stmt)
        correction = res.scalar_one_or_none()

        if not correction:
            return None

        if current_user.role.name != "super_admin" and correction.company_id != current_user.company_id:
            return None

        return types.InvoiceCorrection.from_pydantic(correction)

    @strawberry.field
    async def cash_receipts(
        self,
        info: strawberry.Info,
        start_date: str | None = None,
        end_date: str | None = None,
        search: str | None = None,
    ) -> list[types.CashReceipt]:
        """Get all cash receipts"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import CashReceipt
        stmt = select(CashReceipt)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(CashReceipt.company_id == current_user.company_id)

        if start_date:
            stmt = stmt.where(CashReceipt.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(CashReceipt.date <= datetime.date.fromisoformat(end_date))
        if search:
            stmt = stmt.where(CashReceipt.receipt_number.ilike(f"%{search}%"))

        stmt = stmt.order_by(CashReceipt.date.desc(), CashReceipt.id.desc())

        res = await db.execute(stmt)
        return [types.CashReceipt.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def cash_receipt(self, info: strawberry.Info, id: int) -> types.CashReceipt | None:
        """Get a single cash receipt by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import CashReceipt
        receipt = await db.get(CashReceipt, id)
        if not receipt:
            return None

        if current_user.role.name != "super_admin" and receipt.company_id != current_user.company_id:
            return None

        return types.CashReceipt.from_pydantic(receipt)

    @strawberry.field
    async def accounts(
        self,
        info: strawberry.Info,
        type: str | None = None,
        parent_id: int | None = None,
    ) -> list[types.Account]:
        """Get all accounts (chart of accounts)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Account
        stmt = select(Account)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Account.company_id == current_user.company_id)

        if type:
            stmt = stmt.where(Account.type == type)
        if parent_id is not None:
            stmt = stmt.where(Account.parent_id == parent_id)

        stmt = stmt.order_by(Account.code.asc())

        res = await db.execute(stmt)
        return [types.Account.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def account(self, info: strawberry.Info, id: int) -> types.Account | None:
        """Get a single account by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Account
        account = await db.get(Account, id)
        if not account:
            return None

        if current_user.role.name != "super_admin" and account.company_id != current_user.company_id:
            return None

        return types.Account.from_pydantic(account)

    @strawberry.field
    async def account_by_code(self, info: strawberry.Info, code: str) -> types.Account | None:
        """Get a single account by code"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Account
        stmt = select(Account).where(Account.code == code)
        res = await db.execute(stmt)
        account = res.scalars().first()
        if not account:
            return None

        if current_user.role.name != "super_admin" and account.company_id != current_user.company_id:
            return None

        return types.Account.from_pydantic(account)

    @strawberry.field
    async def accounting_entries(
        self,
        info: strawberry.Info,
        account_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        search: str | None = None,
    ) -> list[types.AccountingEntry]:
        """Get all accounting entries"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import AccountingEntry
        stmt = select(AccountingEntry)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(AccountingEntry.company_id == current_user.company_id)

        if account_id:
            stmt = stmt.where(
                (AccountingEntry.debit_account_id == account_id) |
                (AccountingEntry.credit_account_id == account_id),
            )
        if start_date:
            stmt = stmt.where(AccountingEntry.date >= datetime.date.fromisoformat(start_date))
        if end_date:
            stmt = stmt.where(AccountingEntry.date <= datetime.date.fromisoformat(end_date))
        if search:
            stmt = stmt.where(AccountingEntry.description.ilike(f"%{search}%"))

        stmt = stmt.order_by(AccountingEntry.date.desc(), AccountingEntry.id.desc())

        res = await db.execute(stmt)
        return [types.AccountingEntry.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def accounting_entry(self, info: strawberry.Info, id: int) -> types.AccountingEntry | None:
        """Get a single accounting entry by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import AccountingEntry
        entry = await db.get(AccountingEntry, id)
        if not entry:
            return None

        if current_user.role.name != "super_admin" and entry.company_id != current_user.company_id:
            return None

        return types.AccountingEntry.from_pydantic(entry)

    @strawberry.field
    async def vat_registers(
        self,
        info: strawberry.Info,
        year: int | None = None,
        month: int | None = None,
    ) -> list[types.VATRegister]:
        """Get all VAT registers"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import VATRegister
        stmt = select(VATRegister)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(VATRegister.company_id == current_user.company_id)

        if year:
            stmt = stmt.where(VATRegister.period_year == year)
        if month:
            stmt = stmt.where(VATRegister.period_month == month)

        stmt = stmt.order_by(VATRegister.period_year.desc(), VATRegister.period_month.desc())

        res = await db.execute(stmt)
        return [types.VATRegister.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def vat_register(self, info: strawberry.Info, id: int) -> types.VATRegister | None:
        """Get a single VAT register by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import VATRegister
        vat_register = await db.get(VATRegister, id)
        if not vat_register:
            return None

        if current_user.role.name != "super_admin" and vat_register.company_id != current_user.company_id:
            return None

        return types.VATRegister.from_pydantic(vat_register)
