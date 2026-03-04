# ПЛАН ЗА РАЗРАБОТКА НА СЧЕТОВОДНИЯ МОДУЛ
## Съответствие с българското законодателство (2024/2025/2026)

---

## ВКЛЮЧЕНИ КОМПОНЕНТИ

1. **Счетоводство** - Фактури, каса, банка, сметкоплан
2. **SAF-T Генератор** - Задължително от Януари 2026
3. **Payroll** - Заплати, осигуровки, данъци (отделен план)

---

## ЧАСТ 1: ИМА В CHRONOS

### 1.1 Фактури ✅
| Поле | Състояние |
|------|-----------|
| Номер на фактура | ✅ |
| Тип (входяща/изходяща) | ✅ |
| Дата | ✅ |
| Доставчик (субект) | ✅ |
| Клиент (име, ЕИК, адрес) | ✅ |
| Суми (субтотал, отстъпка, ДДС, общо) | ✅ |
| Метод на плащане | ✅ |
| Срок за плащане | ✅ |
| Дата на плащане | ✅ |
| Статус | ✅ |
| Свързани артикули | ✅ |

### 1.2 Касов Журнал ✅
| Поле | Състояние |
|------|-----------|
| Дата | ✅ |
| Тип операция (приход/разход) | ✅ |
| Сума | ✅ |
| Описание | ✅ |
| Референция (фактура/друго) | ✅ |

### 1.3 Дневни/Месечни Справки ✅
| Поле | Състояние |
|------|-----------|
| Брой фактури | ✅ |
| Суми фактури | ✅ |
| ДДС приход/разход | ✅ |
| Касови операции | ✅ |
| Статуси на плащане | ✅ |

### 1.4 Доставчици ✅
| Поле | Състояние |
|------|-----------|
| Име | ✅ |
| ЕИК | ✅ |
| ДДС номер | ✅ |
| Адрес | ✅ |
| Контакти | ✅ |

---

## ЧАСТ 2: ИЗИСКВАНИЯ ПО БЪЛГАРСКО ЗАКОНОДАТЕЛСТВО

### 2.1 SAF-T (Задължително от 2026)

#### График на въвеждане
| Дата | Задължени предприятия |
|------|----------------------|
| Януари 2026 | Големи предприятия (>300 млн. лв. оборот или >3.5 млн. лв. данъци) |
| Януари 2028 | Средни предприятия (>15 млн. лв. оборот или >1.5 млн. лв. данъци) |
| Януари 2030 | Всички останали данъкоплатци |

#### Видове SAF-T файлове
| Тип | Срок за подаване | Съдържание |
|-----|------------------|-------------|
| **Месечен SAF-T** | До 14-то число на следващия месец | Главна книга, фактури, вземания и задължения |
| **Годишен SAF-T** | До 30 юни следващата година | Активи, инвентар |
| **По заявка** | При поискване от НАП | Пълен SAF-T |

#### Задължителни елементи в XML
1. **Header** - информация за файла
2. **MasterFiles** - сметкоплан, контрагенти
3. **GeneralLedgerEntries** - всички счетоводни операции
4. **Invoices** - входящи и изходящи фактури
5. **Payments** - плащания
6. **TaxTable** - данъчни ставки

### 2.2 Задължителни Реквизити на Фактура (ЗДДС)

| Реквизит | Законова основа |
|----------|-----------------|
| Наименование на документа | ЗДДС чл. 102 |
| Пореден номер (уникален) | ЗДДС чл. 102, ал. 1 |
| Дата на издаване | ЗДДС чл. 102, ал. 1 |
| Дата на данъчно събитие | ЗДДС чл. 102, ал. 1 |
| Наименование на доставчик | ЗДДС чл. 102, ал. 1 |
| Адрес на доставчик | ЗДДС чл. 102, ал. 1 |
| ДДС номер на доставчик | ЗДДС чл. 102, ал. 1 |
| Наименование на получател | ЗДДС чл. 102, ал. 1 |
| Адрес на получател | ЗДДС чл. 102, ал. 1 |
| ДДС номер на получател | ЗДДС чл. 102, ал. 1 |
| Количество и вид на стоката/услугата | ЗДДС чл. 102, ал. 1 |
| Единична цена без ДДС | ЗДДС чл. 102, ал. 1 |
| Основа на доставката | ЗДДС чл. 102, ал. 1 |
| Ставка на ДДС | ЗДДС чл. 102, ал. 1 |
| Размер на ДДС | ЗДДС чл. 102, ал. 1 |
| Сума за плащане | ЗДДС чл. 102, ал. 1 |

### 2.3 Видове Документи

| Документ | Описание | Има в Chronos |
|----------|----------|---------------|
| Фактура | Основен счетоводен документ | ✅ |
| Проформа фактура | Предварителна фактура (без данъчно събитие) | ❌ Липсва |
| Корекционна фактура (Credit Note) | При намаление на сумата | ❌ Липсва |
| Дебитно известие (Debit Note) | При увеличение на сумата | ❌ Липсва |
| Протокол | При обратно начисляване (reverse charge) | ⚠️ Частично |
| Касова бележка | При продажби в брой | ❌ Липсва |
| Фискален бон | От фискален апарат | ❌ Липсва |
| Авансово плащане | При авансово плащане | ⚠️ Частично |
| Стокова разписка | При получаване на стоки | ⚠️ Има (Batch) |
| Опис (инвентаризация) | При инвентаризация | ⚠️ Има |

### 2.4 Счетоводни Регистри (ЗСч)

| Регистър | Описание | Има в Chronos |
|----------|----------|---------------|
| Главна книга | Всички счетоводни операции | ❌ Липсва |
| Дневник | Хронологичен запис на операциите | ❌ Липсва |
| Касова книга | Касови операции | ⚠️ Частично |
| Банкова книга | Банкови операции | ❌ Липсва |
| Регистър на фактурите | Входящи и изходящи | ⚠️ Частично |
| ДДС регистър | ДДС приход/разход | ❌ Липсва |

---

## ЧАСТ 3: GAP АНАЛИЗ

### 3.1 Липсващи Основни Функционалности

| Изискване | Проблем | Приоритет |
|-----------|---------|-----------|
| **SAF-T Генератор** | ❌ Предишно: Нямаше генератор | ✅ ИЗПЪЛНЕНО |
| **SAF-T Валидатор** | ❌ Предишно: Нямаше валидация | ✅ ИЗПЪЛНЕНО |
| **Проформа фактури** | ❌ Предишно: Нямаше тип документ | ✅ ИЗПЪЛНЕНО |
| **Корекционни фактури (Credit/Debit Notes)** | ❌ Предишно: Нямаше логика за корекция | ✅ ИЗПЪЛНЕНО |
| **Касови бележки** | Няма генератор | Висок |
| **Банкови операции** | ❌ Предишно: Нямаше банкова сметка/операции | ✅ Моделът е създаден |
| **ДДС регистър** | Няма експорт за НАП | Висок |
| **Главна книга** | Няма сметкоплан | Среден |
| **Авансови плащания** | Липсва проследяване | Среден |
| **Интеграция с фискален апарат** | Няма връзка | Нисък |

### 3.2 Липсващи Атрибути по Фактура

| Атрибут | Липсващ | Законово изискване |
|----------|----------|---------------------|
| Дата на данъчно събитие | ❌ | Дата на издаване ≠ дата на събитие |
| МОЛ (материално отговорно лице) | ❌ | За стокови документи |
| Начин на плащане | ⚠️ | Има, но не е детайлизиран |
| Основание за освобождаване от ДДС | ❌ | При нулева ставка |
| Референция към договор | ❌ | За проследяемост |
| IBAN на доставчик/клиент | ❌ | За банково плащане |
| Място на доставка | ❌ | При различни локации |

---

## ЧАСТ 4: ПЛАН ЗА РАЗРАБОТКА

### ФАЗА 1: Проформа и Корекционни Фактури (Седмица 1-2)

#### 1.1 Проформа Фактура
```
Модел: Invoice
Поле: type = "proforma"
Статус: винаги "draft" или "final"
Без ДДС задължение
```

#### 1.2 Корекционни Фактури
```python
class InvoiceCorrection(Base):
    __tablename__ = "invoice_corrections"
    
    id = Column(Integer, primary_key=True)
    original_invoice_id = Column(Integer, ForeignKey('invoices.id'))
    correction_type = Column(String(20))  # 'credit', 'debit'
    reason = Column(Text)  # Причина за корекцията
    amount_diff = Column(Numeric(12, 2))
    vat_diff = Column(Numeric(12, 2))
    correction_date = Column(Date)
    new_invoice_id = Column(Integer, ForeignKey('invoices.id'))  # За нова коректна фактура
    
    # Автоматично генериране на нова фактура при Credit Note
    # Автоматично анулиране при пълна корекция
```

---

### ФАЗА 2: Касови Бележки и Банка (Седмица 2-3)

#### 2.1 Касова Бележка
```python
class CashReceipt(Base):
    __tablename__ = "cash_receipts"
    
    id = Column(Integer, primary_key=True)
    receipt_number = Column(String(50), unique=True)  # Пореден номер
    date = Column(Date)
    payment_type = Column(String(20))  # 'cash', 'card'
    amount = Column(Numeric(12, 2))
    vat_amount = Column(Numeric(12, 2))
    items_json = Column(JSON)  # Детайли на артикулите
    fiscal_printer_id = Column(String(50))  # Ако е от фискален апарат
    company_id = Column(Integer, ForeignKey('companies.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
```

#### 2.2 Банкови Сметки
```python
class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    iban = Column(String(34), unique=True)
    bic = Column(String(11))
    bank_name = Column(String(255))
    account_type = Column(String(20))  # 'current', 'escrow'
    is_default = Column(Boolean, default=False)
    currency = Column(String(3), default='BGN')
    is_active = Column(Boolean, default=True)
```

#### 2.3 Банкови Операции
```python
class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    
    id = Column(Integer, primary_key=True)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'))
    date = Column(Date)
    amount = Column(Numeric(12, 2))
    type = Column(String(20))  # 'credit', 'debit'
    description = Column(Text)
    reference = Column(String(100))  # Номер на плащане
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True)
    matched = Column(Boolean, default=False)
    company_id = Column(Integer, ForeignKey('companies.id'))
    
    # Автоматично свързване с фактура по номер/сума
```

---

### ФАЗА 3: SAF-T Генератор (Седмица 3-4) ⭐ КРИТИЧНО

#### 3.1 SAF-T XML Структура

```python
class SAFTGenerator:
    """Генератор на SAF-T XML файлове за НАП"""
    
    def __init__(self, db: AsyncSession, company_id: int, period_start: date, period_end: date):
        self.db = db
        self.company_id = company_id
        self.period_start = period_start
        self.period_end = period_end
    
    async def generate_monthly_saft(self) -> str:
        """Генерира месечен SAF-T файл"""
        
        xml_elements = {
            'Header': self._generate_header(),
            'MasterFiles': await self._generate_master_files(),
            'GeneralLedgerEntries': await self._generate_gl_entries(),
            'Invoices': await self._generate_invoices(),
            'TaxTable': self._generate_tax_table()
        }
        
        return self._build_xml(xml_elements)
    
    def _generate_header(self) -> dict:
        """Header - информация за файла"""
        return {
            'AuditFileCountry': 'BG',
            'AuditFileVersion': '2.0',
            'CompanyName': self.company.name,
            'CompanyID': self.company.eik,
            'TaxRegistrationID': self.company.vat_number,
            'FiscalYear': self.period_start.year,
            'FiscalPeriod': self.period_start.month,
            'StartDate': self.period_start.isoformat(),
            'EndDate': self.period_end.isoformat(),
            'CurrencyCode': 'BGN',
            'DateCreated': datetime.now().isoformat(),
            'Signature': None  # За електронен подпис
        }
    
    async def _generate_master_files(self) -> dict:
        """MasterFiles - сметкоплан и контрагенти"""
        
        # Chart of Accounts
        accounts = await self._get_accounts()
        account_entries = []
        for acc in accounts:
            account_entries.append({
                'AccountID': acc.code,
                'AccountName': acc.name,
                'AccountType': acc.type,  # 'Asset', 'Liability', 'Equity', 'Revenue', 'Expense'
                'OpeningBalanceDecimal': acc.opening_balance,
                'ClosingBalanceDecimal': acc.closing_balance
            })
        
        # Customers/Suppliers
        parties = await self._get_parties()
        party_entries = []
        for party in parties:
            party_entries.append({
                'PartyID': party.id,
                'PartyName': party.name,
                'PartyType': party.type,  # 'Customer', 'Supplier'
                'TIN': party.eik,
                'VATID': party.vat_number,
                'Address': party.address
            })
        
        return {
            'ChartOfAccounts': {'Account': account_entries},
            'Customers': {'Customer': party_entries},
            'Suppliers': {'Supplier': party_entries}
        }
    
    async def _generate_gl_entries(self) -> dict:
        """GeneralLedgerEntries - всички счетоводни операции"""
        
        entries = await self._get_accounting_entries()
        gl_entries = []
        
        for entry in entries:
            journal_entry = {
                'EntryNo': entry.entry_number,
                'Date': entry.date.isoformat(),
                'Description': entry.description,
                'SystemID': 'CHRONOS',
                'UserID': entry.created_by_user.username if entry.created_by_user else 'system',
                'DebitLine': {
                    'AccountID': entry.debit_account.code,
                    'Amount': float(entry.amount)
                },
                'CreditLine': {
                    'AccountID': entry.credit_account.code,
                    'Amount': float(entry.amount)
                }
            }
            
            if entry.vat_amount > 0:
                journal_entry['TaxLine'] = {
                    'TaxType': 'VAT',
                    'TaxAmount': float(entry.vat_amount),
                    'TaxCode': '20'  # или 9%, 0%
                }
            
            gl_entries.append(journal_entry)
        
        return {
            'Journal': gl_entries,
            'TotalDebit': sum(e['DebitLine']['Amount'] for e in gl_entries),
            'TotalCredit': sum(e['CreditLine']['Amount'] for e in gl_entries)
        }
    
    async def _generate_invoices(self) -> dict:
        """Invoices - входящи и изходящи фактури"""
        
        invoices = await self._get_invoices()
        invoice_entries = []
        
        for inv in invoices:
            lines = []
            for item in inv.items:
                lines.append({
                    'LineNo': item.line_number,
                    'InvoiceLine': {
                        'ItemName': item.name,
                        'Quantity': float(item.quantity),
                        'UnitCode': item.unit,
                        'UnitPrice': float(item.unit_price),
                        'LineTotalAmount': float(item.total),
                        'TaxLine': {
                            'TaxType': 'VAT',
                            'TaxAmount': float(item.vat_amount),
                            'TaxPercentage': float(inv.vat_rate)
                        }
                    }
                })
            
            invoice_entry = {
                'InvoiceNo': inv.number,
                'IssueDate': inv.date.isoformat(),
                'InvoiceType': 'Outgoing' if inv.type == 'outgoing' else 'Incoming',
                'SupplierPartyID': inv.supplier_id,
                'CustomerPartyID': inv.client_eik,
                'DocumentCurrencyCode': 'BGN',
                'TaxBasisTotalAmount': float(inv.subtotal),
                'TaxTotalAmount': float(inv.vat_amount),
                'InvoiceTotalAmount': float(inv.total),
                'PaymentTerms': {
                    'DueDate': inv.due_date.isoformat() if inv.due_date else None
                },
                'Lines': lines
            }
            
            invoice_entries.append(invoice_entry)
        
        return {'Invoice': invoice_entries}
    
    def _generate_tax_table(self) -> dict:
        """TaxTable - данъчните ставки"""
        return {
            'TaxTableEntry': [
                {
                    'TaxType': 'VAT',
                    'TaxCode': '20',
                    'TaxPercentage': '20.00',
                    'TaxDescription': 'Standard VAT rate'
                },
                {
                    'TaxType': 'VAT',
                    'TaxCode': '9',
                    'TaxPercentage': '9.00',
                    'TaxDescription': 'Reduced VAT rate'
                },
                {
                    'TaxType': 'VAT',
                    'TaxCode': '0',
                    'TaxPercentage': '0.00',
                    'TaxDescription': 'Zero VAT rate'
                }
            ]
        }
    
    def _build_xml(self, elements: dict) -> str:
        """Генерира XML файл"""
        # Използва lxml за генериране на валиден XML
        from lxml import etree
        
        root = etree.Element('AuditFile')
        
        # Build XML от елементите
        ...
        
        return etree.tostring(root, pretty_print=True, encoding='UTF-8').decode()
```

#### 3.2 SAF-T GraphQL Mutation

```python
@strawberry.mutation
async def generate_saft_file(
    info: strawberry.Info,
    company_id: int,
    year: int,
    month: int,
    saft_type: str = 'monthly'  # 'monthly', 'annual', 'on_demand'
) -> SAFTFileResult:
    """Генерира SAF-T XML файл за НАП"""
    
    period_start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    period_end = date(year, month, last_day)
    
    generator = SAFTGenerator(info.db, company_id, period_start, period_end)
    
    if saft_type == 'monthly':
        xml_content = await generator.generate_monthly_saft()
    elif saft_type == 'annual':
        xml_content = await generator.generate_annual_saft()
    else:
        xml_content = await generator.generate_full_saft()
    
    # Валидация на XML
    validation_result = await validator.validate_saft_xml(xml_content)
    
    return SAFTFileResult(
        xml_content=xml_content,
        validation_status=validation_result.status,
        errors=validation_result.errors,
        period_start=period_start,
        period_end=period_end,
        file_size=len(xml_content)
    )
```

#### 3.3 SAF-T Валидатор

```python
class SAFTValidator:
    """Валидатор на SAF-T XML"""
    
    REQUIRED_FIELDS = {
        'Header': ['AuditFileCountry', 'CompanyName', 'CompanyID', 'FiscalYear', 'StartDate', 'EndDate'],
        'Invoices': ['InvoiceNo', 'IssueDate', 'InvoiceType', 'InvoiceTotalAmount'],
        'GeneralLedgerEntries': ['EntryNo', 'Date', 'DebitLine', 'CreditLine']
    }
    
    def validate_saft_xml(self, xml_content: str) -> ValidationResult:
        """Валидира XML срещу схемата"""
        
        errors = []
        
        # 1. Парсиране на XML
        try:
            root = etree.fromstring(xml_content)
        except Exception as e:
            return ValidationResult(status='error', errors=[f'Invalid XML: {e}'])
        
        # 2. Проверка на задължителните полета
        for field in self.REQUIRED_FIELDS.get('Header', []):
            if not root.find(f'.//{field}'):
                errors.append(f'Missing required field: {field}')
        
        # 3. Проверка на суми (баланс дебит = кредит)
        total_debit = root.find('.//TotalDebit')
        total_credit = root.find('.//TotalCredit')
        if total_debit is not None and total_credit is not None:
            if float(total_debit.text) != float(total_credit.text):
                errors.append('General ledger is not balanced')
        
        return ValidationResult(
            status='valid' if not errors else 'invalid',
            errors=errors
        )
```

---

### ФАЗА 4: Счетоводни Регистри (Седмица 4-5)

#### 4.1 Сметкоплан
```python
class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True)  # напр. 401, 501, 611
    name = Column(String(255))
    type = Column(String(20))  # 'asset', 'liability', 'equity', 'revenue', 'expense'
    parent_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    
    # Стандартен сметкоплан за България:
    # 401 - Доставчици
    # 402 - Персонал
    # 411 - ДДС
    # 501 - Каса
    # 502 - Банка
    # 611 - Разходи за суровини
    # 701 - Приходи от продажби
```

#### 4.2 Счетоводни Операции
```python
class AccountingEntry(Base):
    __tablename__ = "accounting_entries"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    entry_number = Column(String(50))
    description = Column(Text)
    
    # Детайли
    debit_account_id = Column(Integer, ForeignKey('accounts.id'))
    credit_account_id = Column(Integer, ForeignKey('accounts.id'))
    amount = Column(Numeric(12, 2))
    vat_amount = Column(Numeric(12, 2), default=0)
    
    # Референции
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey('bank_transactions.id'), nullable=True)
    cash_journal_id = Column(Integer, ForeignKey('cash_journal_entries.id'), nullable=True)
    
    company_id = Column(Integer, ForeignKey('companies.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Автоматично генериране при издаване/плащане на фактура
```

---

### ФАЗА 5: ДДС и Справки (Седмица 5-6)

#### 5.1 ДДС Регистър
```python
class VATRegister(Base):
    __tablename__ = "vat_registers"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    period_month = Column(Integer)
    period_year = Column(Integer)
    
    # ДДС приход
    vat_collected_20 = Column(Numeric(12, 2))
    vat_collected_9 = Column(Numeric(12, 2))
    vat_collected_0 = Column(Numeric(12, 2))
    
    # ДДС разход
    vat_paid_20 = Column(Numeric(12, 2))
    vat_paid_9 = Column(Numeric(12, 2))
    vat_paid_0 = Column(Numeric(12, 2))
    
    # Корекции
    vat_adjustment = Column(Numeric(12, 2))
    
    # Крайна сума
    vat_due = Column(Numeric(12, 2))  # ДДС за внасяне
    vat_credit = Column(Numeric(12, 2))  # ДДС за възстановяване
    
    # Автоматично попълване от фактурите
```

#### 5.2 Генератор на ДДС Декларация
- Експорт в XML формат за НАП
- Справка по чл. 124 от ЗДДС
- Вътрешнообщностни доставки (VIES)

---

### ФАЗА 6: Стокови Документи (Седмица 6-7)

#### 6.1 Стокова Разписка
```python
class StockReceipt(Base):
    __tablename__ = "stock_receipts"
    
    id = Column(Integer, primary_key=True)
    receipt_number = Column(String(50), unique=True)
    date = Column(Date)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True)
    
    # Детайли
    items = Column(JSON)  # Списък с артикулите
    
    # Статус
    status = Column(String(20))  # 'pending', 'received', 'checked'
    
    company_id = Column(Integer, ForeignKey('companies.id'))
```

#### 6.2 Опис (Инвентаризация)
```python
class InventoryDocument(Base):
    __tablename__ = "inventory_documents"
    
    id = Column(Integer, primary_key=True)
    document_number = Column(String(50))
    date = Column(Date)
    type = Column(String(20))  # 'opening', 'closing', 'periodic'
    
    # Резултати
    items = Column(JSON)  # Очаквано vs намерено
    
    # Одобрение
    approved_by = Column(Integer, ForeignKey('users.id'))
    approval_date = Column(DateTime)
    
    company_id = Column(Integer, ForeignKey('companies.id'))
```

---

## ЧАСТ 5: ПРИОРИТЕТИ

| Приоритет | Задача | Седмици |
|-----------|--------|---------|
| **1 (КРИТИЧЕН)** | **SAF-T Генератор** ⭐ | 3-4 |
| **1 (КРИТИЧЕН)** | **SAF-T Валидатор** ⭐ | 3-4 |
| **1** | Проформа фактури | 1 |
| **1** | Корекционни фактури (Credit/Debit) | 1-2 |
| **1** | Касови бележки | 2 |
| **2** | Банкови сметки и операции | 2-3 |
| **2** | Сметкоплан и счетоводни операции | 4-5 |
| **2** | ДДС регистър и декларация | 5 |
| **2** | Подобряване на стокови документи | 6-7 |
| **3** | Интеграция с фискален апарат | 7-8 |
| **3** | Интрастат справка | 8 |

---

## ЧАСТ 6: ГРАФИК API РАЗШИРЕНИЯ

### 6.1 Нови GraphQL Types

```python
@strawberry.type
class ProformaInvoice:
    id: int
    number: str
    date: date
    client_name: str
    client_eik: str
    items: List[InvoiceItem]
    subtotal: float
    vat_amount: float
    total: float

@strawberry.type
class InvoiceCorrection:
    id: int
    original_invoice: Invoice
    correction_type: str
    reason: str
    amount_diff: float
    vat_diff: float

@strawberry.type
class CashReceipt:
    id: int
    receipt_number: str
    date: date
    amount: float
    vat_amount: float
    items: List[CashReceiptItem]

@strawberry.type
class BankAccount:
    id: int
    iban: str
    bic: str
    bank_name: str
    balance: float

@strawberry.type
class VATRegister:
    period_month: int
    period_year: int
    vat_collected: float
    vat_paid: float
    vat_due: float

@strawberry.type
class SAFTFileResult:
    xml_content: str
    validation_status: str
    errors: List[str]
    period_start: date
    period_end: date
    file_size: int
```

### 6.2 Нови GraphQL Mutations

```python
@strawberry.mutation
async def create_proforma_invoice(
    client_name: str,
    client_eik: str,
    items: List[InvoiceItemInput],
    date: date
) -> ProformaInvoice:
    pass

@strawberry.mutation
async def create_credit_note(
    original_invoice_id: int,
    reason: str,
    items: List[CreditNoteItemInput]
) -> InvoiceCorrection:
    pass

@strawberry.mutation
async def create_cash_receipt(
    amount: float,
    items: List[CashReceiptItemInput]
) -> CashReceipt:
    pass

@strawberry.mutation
async def create_bank_account(
    iban: str,
    bic: str,
    bank_name: str,
    account_type: str
) -> BankAccount:
    pass

@strawberry.mutation
async def match_bank_transaction(
    transaction_id: int,
    invoice_id: int
) -> bool:
    pass

@strawberry.mutation
async def generate_saft_file(
    company_id: int,
    year: int,
    month: int,
    saft_type: str
) -> SAFTFileResult:
    pass

@strawberry.mutation
async def generate_vat_declaration(
    year: int,
    month: int,
    company_id: int,
    format: str  # 'json', 'xml'
) -> VATDeclarationResult:
    pass
```

---

## ЧАСТ 7: ТЕСТВАНЕ

### 7.1 Тестове за Съответствие

```python
def test_invoice_required_fields():
    """Тест за задължителни полета"""
    required = ['number', 'date', 'client_name', 'client_eik', 'items']
    for field in required:
        assert field in invoice_schema

def test_vat_calculation():
    """Тест за коректно изчисление на ДДС"""
    # 100 лв. + 20% = 120 лв.
    assert calculate_vat(100, 20) == 20

def test_credit_note_generates_new_invoice():
    """Тест, че корекция генерира нова фактура"""
    credit_note = create_credit_note(original, -20)
    assert credit_note.new_invoice.total == original.total - 20

def test_saft_xml_structure():
    """Тест за SAF-T XML структура"""
    saft = SAFTGenerator(db, company_id, start_date, end_date)
    xml = await saft.generate_monthly_saft()
    
    # Проверка на коректност
    assert '<AuditFile' in xml
    assert '<Header>' in xml
    assert '<Invoices>' in xml
    assert '<GeneralLedgerEntries>' in xml

def test_saft_validation():
    """Тест за валидация на SAF-T"""
    validator = SAFTValidator()
    result = validator.validate_saft_xml(saft_xml)
    
    assert result.status in ['valid', 'invalid']
```

---

## ЧАСТ 9: ИЗПЪЛНЕНИ ЗАДАЧИ (Февруари 2026)

### ✅ Инсталирани Dependencies
- `lxml==5.3.0` - За XML генерация
- `defusedxml==0.7.1` - За валидация

### ✅ SAF-T Генератор (`backend/services/saft_generator.py`)
- `SAFTGenerator` клас - генерира XML за месечни/годишни SAF-T отчети
- Поддържа: Header, MasterFiles, GeneralLedgerEntries, Invoices, Payments, TaxTable
- `SAFValidator` клас - валидира XML структура

### ✅ Database Models (`backend/database/models.py`)
- `InvoiceCorrection` - Корекционни фактури (Credit/Debit)
- `CashReceipt` - Касови бележки
- `BankAccount` - Банкови сметки
- `BankTransaction` - Банкови операции
- `Account` - Сметкоплан
- `AccountingEntry` - Счетоводни операции
- `VATRegister` - ДДС регистри

### ✅ GraphQL Types (`backend/graphql/types.py`)
- `SAFTValidationResult` - Резултат от валидация
- `SAFTTFileResult` - SAF-T файл с метаданни
- `ProformaInvoice` - Проформа фактура
- `InvoiceCorrection` - Корекционна фактура
- `CashReceipt` - Касова бележка
- `BankAccount` - Банкова сметка
- `BankTransaction` - Банкова операция
- `Account` - Сметка от сметкоплан
- `AccountingEntry` - Счетоводна операция
- `VATRegister` - ДДС регистър

### ✅ GraphQL Queries (`backend/graphql/queries.py`)
- `proforma_invoices` - Списък проформа фактури
- `invoice_corrections` / `invoice_correction` - Корекционни фактури
- `cash_receipts` / `cash_receipt` - Касови бележки
- `bank_accounts` / `bank_account` - Банкови сметки
- `bank_transactions` / `bank_transaction` - Банкови операции
- `accounts` / `account` / `account_by_code` - Сметкоплан
- `accounting_entries` / `accounting_entry` - Счетоводни операции
- `vat_registers` / `vat_register` - ДДС регистри

### ✅ GraphQL Mutations (`backend/graphql/mutations.py`)
- `generate_saft_file` - Генерира SAF-T XML
- `validate_saft_xml` - Валидира XML
- `create_proforma_invoice` - Създава проформа фактура
- `convert_proforma_to_invoice` - Конвертира проформа към фактура
- `create_credit_note` - Създава кредитно известие
- `create_cash_receipt` / `update_cash_receipt` / `delete_cash_receipt` - Касови бележки
- `create_bank_account` / `update_bank_account` / `delete_bank_account` - Банкови сметки
- `create_bank_transaction` / `update_bank_transaction` / `delete_bank_transaction` - Банкови операции
- `match_bank_transaction` - Свързва трансакция с фактура
- `create_account` / `update_account` / `delete_account` - Сметкоплан
- `create_accounting_entry` / `delete_accounting_entry` - Счетоводни операции
- `generate_vat_register` - Генерира ДДС регистър

### ✅ Database Tables (създадени)
- `invoice_corrections`
- `cash_receipts`
- `bank_accounts`
- `bank_transactions`
- `accounts`
- `accounting_entries`
- `vat_registers`

### ✅ GraphQL Inputs (`backend/graphql/inputs.py`)
- `CashReceiptInput` / `CashReceiptUpdateInput`
- `BankAccountInput` / `BankAccountUpdateInput`
- `BankTransactionInput` / `BankTransactionUpdateInput`
- `AccountInput` / `AccountUpdateInput`
- `AccountingEntryInput` / `AccountingEntryUpdateInput`
- `VATRegisterInput`

### ✅ Поправени грешки
- Поправени импорти в `saft_generator.py` и `models.py` за директно изпълнение
- Поправена синтактична грешка в `mutations.py` (ред 2773 - параметърът `info`)
- Поправен SAF-T валидатор за работа с XML namespaces

### ✅ SAF-T Integration Test (Февруари 2026)
- Генерирани 10,689 bytes XML
- Валидация: 0 errors, 0 warnings
- 3 фактури включени (2 изходящи, 1 входяща)
- ДДС ставки: 20%, 9%, 0%, EX

### ✅ Frontend Имплементация (`frontend/src/pages/AccountingPage.tsx`)
Нови табове:
- **Проформа фактури** - списък и създаване
- **Корекции** - Credit/Debit notes
- **Банка** - сметки и транзакции
- **Сметкоплан** -.chart of accounts
- **ДДС регистри** - генериране и преглед
- **SAF-T** - генератор с XML download

GraphQL заявки добавени:
- `GET_PROFORMA_INVOICES`, `CREATE_PROFORMA_INVOICE`
- `GET_INVOICE_CORRECTIONS`
- `GET_BANK_ACCOUNTS`, `CREATE_BANK_ACCOUNT`
- `GET_BANK_TRANSACTIONS`, `CREATE_BANK_TRANSACTION`
- `GET_ACCOUNTS`, `CREATE_ACCOUNT`
- `GET_VAT_REGISTERS`, `GENERATE_VAT_REGISTER`
- `GENERATE_SAFT_FILE`

---

## ЧАСТ 10: СЛЕДВАЩИ СТЪПКИ

| Приоритет | Задача | Статус |
|-----------|--------|--------|
| 1 | Тестване на SAF-T генератор с реални данни | ✅ ИЗПЪЛНЕНО |
| 2 | GraphQL queries за новите модели | ✅ ИЗПЪЛНЕНО |
| 3 | CRUD за Касови бележки | ✅ ИЗПЪЛНЕНО |
| 4 | CRUD за Банкови операции | ✅ ИЗПЪЛНЕНО |
| 5 | ДДС регистър - автоматично попълване | ✅ ИЗПЪЛНЕНО |
| 6 | SAF-T integration tests | ✅ ИЗПЪЛНЕНО |
| 7 | Фикс на AccountingPage.tsx - премахнати дублиращи се функции | ✅ ИЗПЪЛНЕНО |
| 8 | Fix build errors - добавен useMutation за deleteInvoice | ✅ ИЗПЪЛНЕНО |
| 9 | Build минава успешно | ✅ ИЗПЪЛНЕНО |
| 10 | Почистване на неизползван код (Collapse, ExpandLessIcon, etc.) | ✅ ИЗПЪЛНЕНО |
| 11 | Анализ на RecipesPage.tsx за ValidatedTextField | ✅ ИЗПЪЛНЕНО |
| 12 | Прилагане на валидация с тултипи в Счетоводство менюто | ✅ ИЗПЪЛНЕНО |

---

## ЧАСТ 11: ПРЕДСТОЯЩИ ЗАДАЧИ

| Приоритет | Задача |
|-----------|--------|
| 1 | Тестване на новите счетоводни страници |
| 2 | Интеграция на всички нови модули |

---

*План създаден: Февруари 2026*
*Версия: 1.3 - Добавена валидация с тултипи*
