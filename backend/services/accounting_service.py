"""
Accounting Service - Автоматично генериране на счетоводни записи при операции с фактури.
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database.models import (
    Company, Invoice, InvoiceItem, AccountingEntry, Account, User
)


class AccountingService:
    """
    Сервиз за автоматично генериране на счетоводни записи.
    
    Логика:
    - При издаване на изходяща фактура (продажба):
        - Дт: 411 Вземания от клиенти
        - Кт: 701 Приходи от продажби
        - Дт: 411 Вземания от клиенти (за ДДС)
        - Кт: 453 ДДС
        
    - При издаване на входяща фактура (покупка):
        - Дт: 601 Разходи за материали/стоки
        - Кт: 401 Задължения към доставчици
        - Дт: 453 ДДС за възстановяване
        - Кт: 401 Задължения към доставчици
        
    - При плащане (банков превод):
        - Дт: 503 Банкова сметка
        - Кт: 411 Вземания от клиенти (или 401 за доставчици)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invoice_entries(
        self,
        invoice: Invoice,
        company: Company,
        created_by: Optional[User] = None
    ) -> List[AccountingEntry]:
        """
        Създава счетоводни записи при издаване на фактура.
        
        Args:
            invoice: Фактурата
            company: Фирмата
            created_by: Потребителят създал записа
            
        Returns:
            List[AccountingEntry]: Списък със счетоводни записи
        """
        entries = []
        
        # Вземаме default сметки от фирмата
        sales_account = company.default_sales_account_id
        expense_account = company.default_expense_account_id
        vat_account = company.default_vat_account_id
        customer_account = company.default_customer_account_id
        supplier_account = company.default_supplier_account_id
        
        if invoice.type == 'outgoing':
            # ИЗХОДЯЩА ФАКТУРА (ПРОДАЖБА)
            if not sales_account or not customer_account:
                return entries  # Няма конфигурирани сметки
            
            # Запис за прихода (без ДДС)
            if invoice.subtotal and float(invoice.subtotal) > 0:
                entries.append(AccountingEntry(
                    date=invoice.date or date.today(),
                    entry_number=f"INV-{invoice.number or invoice.id}",
                    description=f"Приход от продажба - Фактура {invoice.number or invoice.id}",
                    debit_account_id=customer_account,
                    credit_account_id=sales_account,
                    amount=invoice.subtotal,
                    vat_amount=0,
                    invoice_id=invoice.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None
                ))
            
            # Запис за ДДС-то
            if invoice.vat_amount and float(invoice.vat_amount) > 0:
                entries.append(AccountingEntry(
                    date=invoice.date or date.today(),
                    entry_number=f"INV-{invoice.number or invoice.id}-VAT",
                    description=f"ДДС от продажба - Фактура {invoice.number or invoice.id}",
                    debit_account_id=customer_account,
                    credit_account_id=vat_account,
                    amount=invoice.vat_amount,
                    vat_amount=0,
                    invoice_id=invoice.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None
                ))
                
        elif invoice.type == 'incoming':
            # ВХОДЯЩА ФАКТУРА (ПОКУПКА)
            if not expense_account or not supplier_account:
                return entries  # Няма конфигурирани сметки
            
            # Запис за разхода (без ДДС)
            if invoice.subtotal and float(invoice.subtotal) > 0:
                entries.append(AccountingEntry(
                    date=invoice.date or date.today(),
                    entry_number=f"INV-{invoice.number or invoice.id}",
                    description=f"Разход за материали - Фактура {invoice.number or invoice.id}",
                    debit_account_id=expense_account,
                    credit_account_id=supplier_account,
                    amount=invoice.subtotal,
                    vat_amount=0,
                    invoice_id=invoice.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None
                ))
            
            # Запис за ДДС-то (данъчен кредит)
            if invoice.vat_amount and float(invoice.vat_amount) > 0 and vat_account:
                entries.append(AccountingEntry(
                    date=invoice.date or date.today(),
                    entry_number=f"INV-{invoice.number or invoice.id}-VAT",
                    description=f"ДДС за възстановяване - Фактура {invoice.number or invoice.id}",
                    debit_account_id=vat_account,
                    credit_account_id=supplier_account,
                    amount=invoice.vat_amount,
                    vat_amount=0,
                    invoice_id=invoice.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None
                ))
        
        return entries

    async def create_payment_entries(
        self,
        invoice: Invoice,
        payment_amount: float,
        payment_method: str,
        company: Company,
        created_by: Optional[User] = None
    ) -> List[AccountingEntry]:
        """
        Създава счетоводни записи при плащане.
        
        Args:
            invoice: Фактурата
            payment_amount: Сума на плащането
            payment_method: Метод ('bank', 'cash', 'card')
            company: Фирмата
            created_by: Потребителят
            
        Returns:
            List[AccountingEntry]: Списък със счетоводни записи
        """
        entries = []
        
        bank_account = company.default_bank_account_id
        cash_account = company.default_cash_account_id
        customer_account = company.default_customer_account_id
        supplier_account = company.default_supplier_account_id
        
        if not bank_account and not cash_account:
            return entries
        
        # Определяме сметките според типа на фактурата
        if invoice.type == 'outgoing':
            # Плащане от клиент
            receivable_account = customer_account
            if not receivable_account:
                return entries
        else:
            # Плащане към доставчик
            receivable_account = supplier_account
            if not receivable_account:
                return entries
        
        # Избираме сметка според метода
        if payment_method == 'cash' and cash_account:
            bank_or_cash_account = cash_account
        elif bank_account:
            bank_or_cash_account = bank_account
        else:
            return entries
        
        # Запис за плащането
        entries.append(AccountingEntry(
            date=date.today(),
            entry_number=f"PAY-{invoice.number or invoice.id}",
            description=f"Плащане по фактура {invoice.number or invoice.id}",
            debit_account_id=bank_or_cash_account,
            credit_account_id=receivable_account,
            amount=payment_amount,
            vat_amount=0,
            invoice_id=invoice.id,
            company_id=company.id,
            created_by=created_by.id if created_by else None
        ))
        
        return entries

    async def save_entries(self, entries: List[AccountingEntry]) -> None:
        """Записва счетоводните записи в базата."""
        for entry in entries:
            self.db.add(entry)
        await self.db.commit()

    async def get_entry_number(self, company_id: int) -> str:
        """
        Генерира уникален номер за счетоводен запис.
        
        Format: ENTRY-{YYYYMMDD}-{SEQUENCE}
        """
        today = date.today()
        prefix = f"ENTRY-{today.strftime('%Y%m%d')}"
        
        # Броим записите за днес
        result = await self.db.execute(
            select(func.count(AccountingEntry.id))
            .where(AccountingEntry.company_id == company_id)
            .where(AccountingEntry.entry_number.like(f"{prefix}%"))
        )
        count = result.scalar() or 0
        
        return f"{prefix}-{count + 1:04d}"

    async def create_correction_entries(
        self,
        correction,
        invoice: Invoice,
        company: Company,
        created_by: Optional[User] = None
    ) -> List[AccountingEntry]:
        """
        Създава обратни счетоводни записи при корекция на фактура.
        
        При кредитно известие (credit):
            - Обръщаме посоката на записите от оригиналната фактура
            - Ако оригиналът е продажба: Дт: 701 / Кт: 411
            - Ако оригиналът е покупка: Дт: 401 / Кт: 601
            
        При дебитно известие (debit):
            - Записваме отново като положителна сума
            
        Args:
            correction: Корекцията (InvoiceCorrection)
            invoice: Оригиналната фактура
            company: Фирмата
            created_by: Потребителят
            
        Returns:
            List[AccountingEntry]: Списък с обратни счетоводни записи
        """
        from backend.database.models import InvoiceCorrection
        
        entries = []
        correction_date = correction.correction_date if hasattr(correction, 'correction_date') else date.today()
        
        sales_account = company.default_sales_account_id
        expense_account = company.default_expense_account_id
        vat_account = company.default_vat_account_id
        customer_account = company.default_customer_account_id
        supplier_account = company.default_supplier_account_id
        
        amount_diff = float(correction.amount_diff) if correction.amount_diff else 0
        vat_diff = float(correction.vat_diff) if correction.vat_diff else 0
        
        if invoice.type == 'outgoing':
            if not sales_account or not customer_account:
                return entries
            
            if amount_diff != 0:
                entries.append(AccountingEntry(
                    date=correction_date,
                    entry_number=f"REV-{correction.number}",
                    description=f"Обратен запис - Корекция {correction.number}",
                    debit_account_id=sales_account,
                    credit_account_id=customer_account,
                    amount=abs(amount_diff),
                    vat_amount=0,
                    invoice_id=invoice.id,
                    correction_id=correction.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None,
                    is_reversal=True
                ))
            
            if vat_diff != 0:
                entries.append(AccountingEntry(
                    date=correction_date,
                    entry_number=f"REV-{correction.number}-VAT",
                    description=f"Обратен ДДС - Корекция {correction.number}",
                    debit_account_id=vat_account,
                    credit_account_id=customer_account,
                    amount=abs(vat_diff),
                    vat_amount=0,
                    invoice_id=invoice.id,
                    correction_id=correction.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None,
                    is_reversal=True
                ))
                
        elif invoice.type == 'incoming':
            if not expense_account or not supplier_account:
                return entries
            
            if amount_diff != 0:
                entries.append(AccountingEntry(
                    date=correction_date,
                    entry_number=f"REV-{correction.number}",
                    description=f"Обратен запис - Корекция {correction.number}",
                    debit_account_id=supplier_account,
                    credit_account_id=expense_account,
                    amount=abs(amount_diff),
                    vat_amount=0,
                    invoice_id=invoice.id,
                    correction_id=correction.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None,
                    is_reversal=True
                ))
            
            if vat_diff != 0:
                entries.append(AccountingEntry(
                    date=correction_date,
                    entry_number=f"REV-{correction.number}-VAT",
                    description=f"Обратен ДДС - Корекция {correction.number}",
                    debit_account_id=supplier_account,
                    credit_account_id=vat_account,
                    amount=abs(vat_diff),
                    vat_amount=0,
                    invoice_id=invoice.id,
                    correction_id=correction.id,
                    company_id=company.id,
                    created_by=created_by.id if created_by else None,
                    is_reversal=True
                ))
        
        return entries
