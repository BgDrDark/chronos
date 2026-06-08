import datetime
from decimal import Decimal

import strawberry


@strawberry.input
class InvoiceItemInput:
    ingredient_id: int | None = None
    batch_id: int | None = None
    name: str
    quantity: Decimal
    unit: str = "br"
    unit_price: Decimal
    unit_price_with_vat: Decimal | None = None
    discount_percent: Decimal = Decimal(0)
    expiration_date: str | None = None
    batch_number: str | None = None


@strawberry.input
class InvoiceInput:
    type: str
    document_type: str | None = "ФАКТУРА"
    griff: str | None = "ОРИГИНАЛ"
    description: str | None = None
    date: datetime.date
    supplier_id: int | None = None
    batch_id: int | None = None
    client_name: str | None = None
    client_eik: str | None = None
    client_address: str | None = None
    discount_percent: Decimal = Decimal(0)
    vat_rate: Decimal = Decimal("20.0")
    payment_method: str | None = None
    delivery_method: str | None = None
    due_date: datetime.date | None = None
    payment_date: datetime.date | None = None
    status: str = "draft"
    notes: str | None = None
    company_id: int
    items: list[InvoiceItemInput]


@strawberry.input
class CashJournalEntryInput:
    date: datetime.date
    operation_type: str
    amount: Decimal
    description: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    payment_method: str | None = None
    company_id: int


@strawberry.input
class CashReceiptInput:
    receipt_number: str
    date: datetime.date
    payment_type: str
    amount: Decimal
    vat_amount: Decimal = Decimal(0)
    items_json: str | None = None
    fiscal_printer_id: str | None = None
    company_id: int


@strawberry.input
class CashReceiptUpdateInput:
    receipt_number: str | None = None
    date: datetime.date | None = None
    payment_type: str | None = None
    amount: Decimal | None = None
    vat_amount: Decimal | None = None
    items_json: str | None = None
    fiscal_printer_id: str | None = None


@strawberry.input
class BankAccountInput:
    iban: str
    bic: str | None = None
    bank_name: str
    account_type: str = "current"
    is_default: bool = False
    currency: str = "BGN"
    is_active: bool = True
    company_id: int


@strawberry.input
class BankAccountUpdateInput:
    iban: str | None = None
    bic: str | None = None
    bank_name: str | None = None
    account_type: str | None = None
    is_default: bool | None = None
    currency: str | None = None
    is_active: bool | None = None


@strawberry.input
class BankTransactionInput:
    bank_account_id: int
    date: datetime.date
    amount: Decimal
    type: str
    description: str | None = None
    reference: str | None = None
    invoice_id: int | None = None
    company_id: int


@strawberry.input
class BankTransactionUpdateInput:
    date: datetime.date | None = None
    amount: Decimal | None = None
    type: str | None = None
    description: str | None = None
    reference: str | None = None
    invoice_id: int | None = None
    matched: bool | None = None


@strawberry.input
class AccountInput:
    code: str
    name: str
    type: str
    parent_id: int | None = None
    company_id: int
    opening_balance: Decimal = Decimal(0)


@strawberry.input
class AccountUpdateInput:
    code: str | None = None
    name: str | None = None
    type: str | None = None
    parent_id: int | None = None
    opening_balance: Decimal | None = None


@strawberry.input
class AccountingEntryInput:
    date: datetime.date
    entry_number: str
    description: str | None = None
    debit_account_id: int
    credit_account_id: int
    amount: Decimal
    vat_amount: Decimal = Decimal(0)
    invoice_id: int | None = None
    bank_transaction_id: int | None = None
    cash_journal_id: int | None = None
    company_id: int


@strawberry.input
class AccountingEntryUpdateInput:
    date: datetime.date | None = None
    entry_number: str | None = None
    description: str | None = None
    debit_account_id: int | None = None
    credit_account_id: int | None = None
    amount: Decimal | None = None
    vat_amount: Decimal | None = None


@strawberry.input
class VATRegisterInput:
    period_month: int
    period_year: int
    company_id: int
