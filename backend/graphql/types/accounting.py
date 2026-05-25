import datetime
from decimal import Decimal
from typing import Optional

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas
from backend.database import models
from backend.graphql.types import Company, User
from backend.graphql.types.logistics import Batch, Ingredient, Supplier
from backend.utils.json_type import JSONScalar


@sp.type(schemas.InvoiceItem)
class InvoiceItem:
    id: strawberry.auto
    invoice_id: strawberry.auto
    ingredient_id: strawberry.auto
    batch_id: strawberry.auto
    name: strawberry.auto
    quantity: strawberry.auto
    unit: strawberry.auto
    unit_price: strawberry.auto
    unit_price_with_vat: strawberry.auto
    discount_percent: strawberry.auto
    total: strawberry.auto
    expiration_date: strawberry.auto
    batch_number: strawberry.auto

    @strawberry.field
    async def ingredient(self, info: strawberry.Info) -> Ingredient | None:
        if not self.ingredient_id: return None
        db = info.context["db"]
        res = await db.get(models.Ingredient, self.ingredient_id)
        return Ingredient.from_pydantic(res) if res else None

    @strawberry.field
    async def batch(self, info: strawberry.Info) -> Batch | None:
        if not self.batch_id: return None
        db = info.context["db"]
        res = await db.get(models.Batch, self.batch_id)
        return Batch.from_pydantic(res) if res else None


@sp.type(schemas.Invoice)
class Invoice:
    id: strawberry.auto
    number: strawberry.auto
    type: strawberry.auto
    date: strawberry.auto
    subtotal: strawberry.auto
    discount_percent: strawberry.auto
    discount_amount: strawberry.auto
    vat_rate: strawberry.auto
    vat_amount: strawberry.auto
    total: strawberry.auto
    status: strawberry.auto
    company_id: strawberry.auto
    created_at: strawberry.auto
    document_type: strawberry.auto
    griff: strawberry.auto
    description: strawberry.auto
    supplier_id: strawberry.auto
    batch_id: strawberry.auto
    client_name: strawberry.auto
    client_eik: strawberry.auto
    client_address: strawberry.auto
    payment_method: strawberry.auto
    delivery_method: strawberry.auto
    due_date: strawberry.auto
    payment_date: strawberry.auto
    notes: strawberry.auto
    created_by: strawberry.auto

    @strawberry.field
    async def supplier(self, info: strawberry.Info) -> Supplier | None:
        if not self.supplier_id: return None
        result = await info.context["dataloaders"]["supplier_by_id"].load(self.supplier_id)
        return Supplier.from_pydantic(result) if result else None

    @strawberry.field
    async def batch(self, info: strawberry.Info) -> Batch | None:
        if not self.batch_id: return None
        result = await info.context["dataloaders"]["batch_by_id"].load(self.batch_id)
        return Batch.from_pydantic(result) if result else None

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Company | None:
        result = await info.context["dataloaders"]["company_by_id"].load(self.company_id)
        return Company.from_pydantic(result) if result else None

    @strawberry.field
    async def items(self, info: strawberry.Info) -> list[InvoiceItem]:
        results = await info.context["dataloaders"]["invoice_items_by_invoice_id"].load(self.id)
        return [InvoiceItem.from_pydantic(t) for t in results]

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> User | None:
        if not self.created_by: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.created_by)


@sp.type(schemas.CashJournalEntry)
class CashJournalEntryType:
    id: strawberry.auto
    date: strawberry.auto
    operation_type: strawberry.auto
    amount: strawberry.auto
    description: strawberry.auto
    reference_type: strawberry.auto
    reference_id: strawberry.auto
    created_at: strawberry.auto
    created_by: strawberry.auto

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> User | None:
        if not self.created_by: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.created_by)


@sp.type(schemas.OperationLog)
class OperationLogType:
    id: strawberry.auto
    timestamp: strawberry.auto
    operation: strawberry.auto
    entity_type: strawberry.auto
    entity_id: strawberry.auto
    changes: JSONScalar | None = None
    user_id: strawberry.auto

    @strawberry.field
    async def user(self, info: strawberry.Info) -> User | None:
        if not self.user_id: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.user_id)


@sp.type(schemas.DailySummary)
class DailySummaryType:
    id: strawberry.auto
    date: strawberry.auto
    invoices_count: strawberry.auto
    incoming_invoices_count: strawberry.auto
    outgoing_invoices_count: strawberry.auto
    invoices_total: strawberry.auto
    incoming_invoices_total: strawberry.auto
    outgoing_invoices_total: strawberry.auto
    cash_income: strawberry.auto
    cash_expense: strawberry.auto
    cash_balance: strawberry.auto
    vat_collected: strawberry.auto
    vat_paid: strawberry.auto
    paid_invoices_count: strawberry.auto
    unpaid_invoices_count: strawberry.auto
    overdue_invoices_count: strawberry.auto


@sp.type(schemas.MonthlySummary)
class MonthlySummaryType:
    id: strawberry.auto
    year: strawberry.auto
    month: strawberry.auto
    invoices_count: strawberry.auto
    incoming_invoices_count: strawberry.auto
    outgoing_invoices_count: strawberry.auto
    invoices_total: strawberry.auto
    incoming_invoices_total: strawberry.auto
    outgoing_invoices_total: strawberry.auto
    cash_income: strawberry.auto
    cash_expense: strawberry.auto
    cash_balance: strawberry.auto
    vat_collected: strawberry.auto
    vat_paid: strawberry.auto
    paid_invoices_count: strawberry.auto
    unpaid_invoices_count: strawberry.auto
    overdue_invoices_count: strawberry.auto


@sp.type(schemas.YearlySummary)
class YearlySummaryType:
    id: strawberry.auto
    year: strawberry.auto
    invoices_count: strawberry.auto
    incoming_invoices_count: strawberry.auto
    outgoing_invoices_count: strawberry.auto
    invoices_total: strawberry.auto
    incoming_invoices_total: strawberry.auto
    outgoing_invoices_total: strawberry.auto
    cash_income: strawberry.auto
    cash_expense: strawberry.auto
    cash_balance: strawberry.auto
    vat_collected: strawberry.auto
    vat_paid: strawberry.auto
    paid_invoices_count: strawberry.auto
    unpaid_invoices_count: strawberry.auto
    overdue_invoices_count: strawberry.auto


@strawberry.type
class SAFTValidationResult:
    status: str
    errors: list[str]
    warnings: list[str]
    is_valid: bool


@strawberry.type
class SAFTFileResult:
    xml_content: str
    validation_result: SAFTValidationResult
    period_start: datetime.date
    period_end: datetime.date
    file_size: int
    file_name: str


# ProformaInvoice uses same model as Invoice — manual
@strawberry.type
class ProformaInvoice:
    id: int
    number: str
    type: str = "proforma"
    date: datetime.date
    client_name: str | None
    client_eik: str | None
    client_address: str | None
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    status: str
    notes: str | None
    company_id: int
    created_by: int | None
    created_at: datetime.datetime
    document_type: str | None = "ПРОФОРМА"
    griff: str | None = "ОРИГИНАЛ"
    description: str | None = None
    payment_method: str | None = None
    delivery_method: str | None = "Доставка до адрес"
    due_date: datetime.date | None = None
    payment_date: datetime.date | None = None

    @strawberry.field
    async def items(self, info: strawberry.Info) -> list[InvoiceItem]:
        results = await info.context["dataloaders"]["invoice_items_by_invoice_id"].load(self.id)
        return [InvoiceItem.from_pydantic(t) for t in results]

    @strawberry.field
    async def company(self, info: strawberry.Info) -> Company | None:
        result = await info.context["dataloaders"]["company_by_id"].load(self.company_id)
        return Company.from_pydantic(result) if result else None

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> User | None:
        if not self.created_by: return None
        return await info.context["dataloaders"]["user_by_id"].load(self.created_by)

    @classmethod
    def from_instance(cls, instance: models.Invoice) -> "ProformaInvoice":
        return cls(
            id=instance.id,
            number=instance.number,
            type=instance.type or "proforma",
            date=instance.date,
            client_name=instance.client_name,
            client_eik=instance.client_eik,
            client_address=instance.client_address,
            subtotal=instance.subtotal or Decimal(0),
            discount_percent=instance.discount_percent or Decimal(0),
            discount_amount=instance.discount_amount or Decimal(0),
            vat_rate=instance.vat_rate or Decimal("20.0"),
            vat_amount=instance.vat_amount or Decimal(0),
            total=instance.total or Decimal(0),
            status=instance.status or "proforma",
            notes=instance.notes,
            company_id=instance.company_id,
            created_by=instance.created_by,
            created_at=instance.created_at,
            document_type=instance.document_type or "ПРОФОРМА",
            griff=instance.griff or "ОРИГИНАЛ",
            description=instance.description,
            payment_method=instance.payment_method,
            delivery_method=instance.delivery_method or "Доставка до адрес",
            due_date=instance.due_date,
            payment_date=instance.payment_date,
        )


@sp.type(schemas.InvoiceCorrection)
class InvoiceCorrection:
    id: strawberry.auto
    number: strawberry.auto
    type: strawberry.auto
    date: strawberry.auto
    original_invoice_id: strawberry.auto
    reason: strawberry.auto
    status: strawberry.auto
    company_id: strawberry.auto
    created_by: strawberry.auto
    created_at: strawberry.auto

    @strawberry.field
    async def original_invoice(self, info: strawberry.Info) -> "Invoice | None":
        if not self.original_invoice_id: return None
        db = info.context["db"]
        from backend.database.models import Invoice as DbInvoice
        res = await db.get(DbInvoice, self.original_invoice_id)
        return Invoice.from_pydantic(res) if res else None

    @strawberry.field
    async def client_name(self, info: strawberry.Info) -> str | None:
        db = info.context["db"]
        from backend.database.models import Invoice as DbInvoice
        if not self.original_invoice_id: return None
        orig = await db.get(DbInvoice, self.original_invoice_id)
        return orig.client_name if orig else None

    @strawberry.field
    async def client_eik(self, info: strawberry.Info) -> str | None:
        db = info.context["db"]
        from backend.database.models import Invoice as DbInvoice
        if not self.original_invoice_id: return None
        orig = await db.get(DbInvoice, self.original_invoice_id)
        return orig.client_eik if orig else None

    @strawberry.field
    def subtotal(self) -> Decimal:
        return getattr(self, "amount_diff", None) or Decimal(0)

    @strawberry.field
    async def vat_rate(self, info: strawberry.Info) -> Decimal:
        db = info.context["db"]
        from backend.database.models import Invoice as DbInvoice
        if not self.original_invoice_id: return Decimal("20.0")
        orig = await db.get(DbInvoice, self.original_invoice_id)
        return orig.vat_rate if orig else Decimal("20.0")

    @strawberry.field
    def vat_amount(self) -> Decimal:
        return getattr(self, "vat_diff", None) or Decimal(0)

    @strawberry.field
    def total(self) -> Decimal:
        return (getattr(self, "amount_diff", None) or Decimal(0)) + (getattr(self, "vat_diff", None) or Decimal(0))


@sp.type(schemas.CashReceipt)
class CashReceipt:
    id: strawberry.auto
    receipt_number: strawberry.auto
    date: strawberry.auto
    payment_type: strawberry.auto
    amount: strawberry.auto
    vat_amount: strawberry.auto
    items_json: JSONScalar | None = None
    fiscal_printer_id: strawberry.auto
    company_id: strawberry.auto
    created_by: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.BankAccount)
class BankAccount:
    id: strawberry.auto
    company_id: strawberry.auto
    iban: strawberry.auto
    bic: strawberry.auto
    bank_name: strawberry.auto
    account_type: strawberry.auto
    is_default: strawberry.auto
    currency: strawberry.auto
    is_active: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.BankTransaction)
class BankTransaction:
    id: strawberry.auto
    bank_account_id: strawberry.auto
    date: strawberry.auto
    amount: strawberry.auto
    type: strawberry.auto
    description: strawberry.auto
    reference: strawberry.auto
    invoice_id: strawberry.auto
    matched: strawberry.auto
    company_id: strawberry.auto
    created_at: strawberry.auto


@sp.type(schemas.Account)
class Account:
    id: strawberry.auto
    code: strawberry.auto
    name: strawberry.auto
    type: strawberry.auto
    parent_id: strawberry.auto
    company_id: strawberry.auto
    opening_balance: strawberry.auto
    closing_balance: strawberry.auto


@strawberry.type
class AutoMatchResult:
    matched_count: int
    unmatched_count: int


@sp.type(schemas.AccountingEntry)
class AccountingEntry:
    id: strawberry.auto
    date: strawberry.auto
    entry_number: strawberry.auto
    description: strawberry.auto
    debit_account_id: strawberry.auto
    credit_account_id: strawberry.auto
    amount: strawberry.auto
    vat_amount: strawberry.auto
    invoice_id: strawberry.auto
    bank_transaction_id: strawberry.auto
    cash_journal_id: strawberry.auto
    company_id: strawberry.auto
    created_by: strawberry.auto
    created_at: strawberry.auto

    @strawberry.field
    async def debit_account(self, info: strawberry.Info) -> Account | None:
        if not self.debit_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.debit_account_id)
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def credit_account(self, info: strawberry.Info) -> Account | None:
        if not self.credit_account_id:
            return None
        result = await info.context["dataloaders"]["account_by_id"].load(self.credit_account_id)
        return Account.from_pydantic(result) if result else None

    @strawberry.field
    async def invoice(self, info: strawberry.Info) -> Optional["Invoice"]:
        if not self.invoice_id:
            return None
        from backend.database.models import Invoice as DbInvoice
        db = info.context["db"]
        result = await db.get(DbInvoice, self.invoice_id)
        return Invoice.from_pydantic(result) if result else None

    @strawberry.field
    async def creator(self, info: strawberry.Info) -> User | None:
        if not self.created_by:
            return None
        result = await info.context["dataloaders"]["user_by_id"].load(self.created_by)
        return User.from_pydantic(result) if result else None


@sp.type(schemas.VATRegister)
class VATRegister:
    id: strawberry.auto
    company_id: strawberry.auto
    period_month: strawberry.auto
    period_year: strawberry.auto
    vat_collected_20: strawberry.auto
    vat_collected_9: strawberry.auto
    vat_collected_0: strawberry.auto
    vat_paid_20: strawberry.auto
    vat_paid_9: strawberry.auto
    vat_paid_0: strawberry.auto
    vat_adjustment: strawberry.auto
    vat_due: strawberry.auto
    vat_credit: strawberry.auto
    created_at: strawberry.auto
