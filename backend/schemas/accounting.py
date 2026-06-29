import datetime
import re
from decimal import Decimal
from typing import Any

from pydantic import field_validator

from backend.schemas.base import CustomBaseModel


class InvoiceItem(CustomBaseModel):
    id: int
    invoice_id: int
    ingredient_id: int | None = None
    batch_id: int | None = None
    name: str
    quantity: Decimal
    unit: str | None = "br"
    unit_price: Decimal
    unit_price_with_vat: Decimal | None = None
    discount_percent: Decimal = Decimal(0)
    total: Decimal
    expiration_date: datetime.date | None = None
    batch_number: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v) < 1 or len(v) > 200:
            raise ValueError("Името на артикула трябва да е между 1 и 200 символа")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Количеството трябва да бъде положително")
        return v

    @field_validator("unit_price")
    @classmethod
    def validate_unit_price(cls, v):
        if v < 0:
            raise ValueError("Единичната цена не може да бъде отрицателна")
        return v

    @field_validator("discount_percent")
    @classmethod
    def validate_discount_percent(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Процентът отстъпка трябва да е между 0 и 100")
        return v


class Invoice(CustomBaseModel):
    id: int
    number: str
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
    subtotal: Decimal = Decimal(0)
    discount_percent: Decimal = Decimal(0)
    discount_amount: Decimal = Decimal(0)
    vat_rate: Decimal = Decimal("20.0")
    vat_amount: Decimal = Decimal(0)
    total: Decimal = Decimal(0)
    payment_method: str | None = None
    delivery_method: str | None = "Доставка до адрес"
    due_date: datetime.date | None = None
    payment_date: datetime.date | None = None
    status: str = "draft"
    notes: str | None = None
    company_id: int
    created_by: int | None = None
    created_at: datetime.datetime

    @field_validator("number")
    @classmethod
    def validate_number(cls, v):
        if len(v) < 1 or len(v) > 50:
            raise ValueError("Номерът на фактурата трябва да е между 1 и 50 символа")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed = ["incoming", "outgoing"]
        if v not in allowed:
            raise ValueError(f"Типът трябва да е един от: {', '.join(allowed)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = ["draft", "sent", "paid", "cancelled"]
        if v not in allowed:
            raise ValueError(f"Статусът трябва да е един от: {', '.join(allowed)}")
        return v

    @field_validator("vat_rate")
    @classmethod
    def validate_vat_rate(cls, v):
        if v < 0 or v > 100:
            raise ValueError("ДДС ставката трябва да е между 0 и 100")
        return v

    @field_validator("discount_percent")
    @classmethod
    def validate_discount_percent(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Процентът отстъпка трябва да е между 0 и 100")
        return v

    @field_validator("subtotal", "discount_amount", "vat_amount", "total")
    @classmethod
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError("Сумите не могат да бъдат отрицателни")
        return v

    @field_validator("client_eik", mode="before")
    @classmethod
    def validate_client_eik(cls, v):
        if v is None or v == "":
            return None
        v = v.strip()
        if not re.match(r"^\d{9,13}$", v):
            raise ValueError("ЕИК на клиента трябва да съдържа между 9 и 13 цифри")
        return v


class CashJournalEntry(CustomBaseModel):
    id: int
    date: datetime.date
    operation_type: str
    amount: Decimal
    description: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    payment_method: str | None = None
    created_at: datetime.datetime
    created_by: int | None = None

    @field_validator("operation_type")
    @classmethod
    def validate_operation_type(cls, v):
        allowed = ["income", "expense", "transfer"]
        if v not in allowed:
            raise ValueError(f"Типът операция трябва да е един от: {', '.join(allowed)}")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Сумата трябва да бъде положителна")
        return v


class OperationLog(CustomBaseModel):
    id: int
    timestamp: datetime.datetime
    operation: str
    entity_type: str
    entity_id: int
    user_id: int | None = None
    changes: dict | None = None


class DailySummary(CustomBaseModel):
    id: int
    date: datetime.date
    invoices_count: int = 0
    incoming_invoices_count: int = 0
    outgoing_invoices_count: int = 0
    invoices_total: Decimal = Decimal(0)
    incoming_invoices_total: Decimal = Decimal(0)
    outgoing_invoices_total: Decimal = Decimal(0)
    cash_income: Decimal = Decimal(0)
    cash_expense: Decimal = Decimal(0)
    cash_balance: Decimal = Decimal(0)
    vat_collected: Decimal = Decimal(0)
    vat_paid: Decimal = Decimal(0)
    paid_invoices_count: int = 0
    unpaid_invoices_count: int = 0
    overdue_invoices_count: int = 0


class MonthlySummary(CustomBaseModel):
    id: int
    year: int
    month: int
    invoices_count: int = 0
    incoming_invoices_count: int = 0
    outgoing_invoices_count: int = 0
    invoices_total: Decimal = Decimal(0)
    incoming_invoices_total: Decimal = Decimal(0)
    outgoing_invoices_total: Decimal = Decimal(0)
    cash_income: Decimal = Decimal(0)
    cash_expense: Decimal = Decimal(0)
    cash_balance: Decimal = Decimal(0)
    vat_collected: Decimal = Decimal(0)
    vat_paid: Decimal = Decimal(0)
    paid_invoices_count: int = 0
    unpaid_invoices_count: int = 0
    overdue_invoices_count: int = 0


class YearlySummary(CustomBaseModel):
    id: int
    year: int
    invoices_count: int = 0
    incoming_invoices_count: int = 0
    outgoing_invoices_count: int = 0
    invoices_total: Decimal = Decimal(0)
    incoming_invoices_total: Decimal = Decimal(0)
    outgoing_invoices_total: Decimal = Decimal(0)
    cash_income: Decimal = Decimal(0)
    cash_expense: Decimal = Decimal(0)
    cash_balance: Decimal = Decimal(0)
    vat_collected: Decimal = Decimal(0)
    vat_paid: Decimal = Decimal(0)
    paid_invoices_count: int = 0
    unpaid_invoices_count: int = 0
    overdue_invoices_count: int = 0


class InvoiceCorrection(CustomBaseModel):
    id: int
    number: str
    type: str
    original_invoice_id: int
    reason: str | None = None
    amount_diff: Decimal = Decimal(0)
    vat_diff: Decimal = Decimal(0)
    date: datetime.date
    status: str = "draft"
    company_id: int
    created_by: int | None = None
    created_at: datetime.datetime


class CashReceipt(CustomBaseModel):
    id: int
    receipt_number: str
    date: datetime.date
    payment_type: str = "cash"
    amount: Decimal
    vat_amount: Decimal = Decimal(0)
    items_json: Any | None = None
    fiscal_printer_id: str | None = None
    company_id: int
    created_by: int | None = None
    created_at: datetime.datetime


class BankAccount(CustomBaseModel):
    id: int
    company_id: int
    iban: str
    bic: str | None = None
    bank_name: str
    account_type: str = "current"
    is_default: bool = False
    currency: str = "EUR"
    is_active: bool = True
    created_at: datetime.datetime

    @field_validator("iban")
    @classmethod
    def validate_iban(cls, v):
        v = v.replace(" ", "").upper()
        if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{4,}$", v):
            raise ValueError("Невалиден IBAN формат")
        return v

    @field_validator("bic", mode="before")
    @classmethod
    def validate_bic(cls, v):
        if v is None or v == "":
            return None
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$", v):
            raise ValueError("Невалиден BIC/SWIFT формат")
        return v

    @field_validator("bank_name")
    @classmethod
    def validate_bank_name(cls, v):
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Името на банката трябва да е между 2 и 200 символа")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("Валутата трябва да е 3-буквен ISO код (напр. BGN, EUR, USD)")
        return v


class BankTransaction(CustomBaseModel):
    id: int
    bank_account_id: int
    date: datetime.date
    amount: Decimal
    type: str
    description: str | None = None
    reference: str | None = None
    invoice_id: int | None = None
    matched: bool = False
    company_id: int
    created_at: datetime.datetime


class Account(CustomBaseModel):
    id: int
    code: str
    name: str
    type: str
    parent_id: int | None = None
    company_id: int
    opening_balance: Decimal = Decimal(0)
    closing_balance: Decimal = Decimal(0)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not re.match(r"^\d{2,6}$", v):
            raise ValueError("Кодът на сметката трябва да съдържа 2-6 цифри")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Името на сметката трябва да е между 2 и 200 символа")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed = ["asset", "liability", "equity", "income", "expense"]
        if v not in allowed:
            raise ValueError(f"Типът трябва да е един от: {', '.join(allowed)}")
        return v


class AccountingEntry(CustomBaseModel):
    id: int
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
    created_by: int | None = None
    created_at: datetime.datetime

    @field_validator("entry_number")
    @classmethod
    def validate_entry_number(cls, v):
        if len(v) < 1 or len(v) > 50:
            raise ValueError("Номерът на записването трябва да е между 1 и 50 символа")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Сумата трябва да бъде положителна")
        return v

    @field_validator("vat_amount")
    @classmethod
    def validate_vat_amount(cls, v):
        if v < 0:
            raise ValueError("ДДС сумата не може да бъде отрицателна")
        return v


class VATRegister(CustomBaseModel):
    id: int
    company_id: int
    period_month: int
    period_year: int
    vat_collected_20: Decimal = Decimal(0)
    vat_collected_9: Decimal = Decimal(0)
    vat_collected_0: Decimal = Decimal(0)
    vat_paid_20: Decimal = Decimal(0)
    vat_paid_9: Decimal = Decimal(0)
    vat_paid_0: Decimal = Decimal(0)
    vat_adjustment: Decimal = Decimal(0)
    vat_due: Decimal = Decimal(0)
    vat_credit: Decimal = Decimal(0)
    created_at: datetime.datetime
