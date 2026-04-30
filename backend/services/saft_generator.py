"""
SAF-T Generator Service
Standard Audit File for Tax - XML Generator for Bulgarian NRA

Generates SAF-T XML files compliant with Bulgarian tax authority requirements.
Required for mandatory reporting from January 2026.
"""

import calendar
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from lxml import etree

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Company, User, Invoice, InvoiceItem, Supplier, 
    CashJournalEntry, BankAccount, BankTransaction,
    AccountingEntry, Account, VATRegister
)
from backend.database.models import sofia_now


class SAFTGenerator:
    """
    Generates SAF-T (Standard Audit File for Tax) XML files for Bulgarian NRA.
    
    Supports:
    - Monthly SAF-T reports (deadline: 14th of following month)
    - Annual SAF-T reports (deadline: 30th June)
    - On-demand SAF-T reports
    
    Reference: Bulgarian NRA Order for SAF-T implementation (January 2026)
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        company_id: int, 
        period_start: date, 
        period_end: date
    ):
        self.db = db
        self.company_id = company_id
        self.period_start = period_start
        self.period_end = period_end
        self.company: Optional[Company] = None
    
    async def initialize(self) -> None:
        """Load company data"""
        result = await self.db.execute(
            select(Company).where(Company.id == self.company_id)
        )
        self.company = result.scalar_one_or_none()
        if not self.company:
            raise ValueError(f"Company with id {self.company_id} not found")
    
    async def generate_monthly_saft(self) -> str:
        """Generate monthly SAF-T XML file"""
        await self.initialize()
        
        root = self._create_root_element()
        
        # Add header
        header = self._generate_header_element()
        root.append(header)
        
        # Add master files
        master_files = await self._generate_master_files_element()
        root.append(master_files)
        
        # Add general ledger entries
        gl_entries = await self._generate_gl_entries_element()
        root.append(gl_entries)
        
        # Add invoices
        invoices = await self._generate_invoices_element()
        root.append(invoices)
        
        # Add payments
        payments = await self._generate_payments_element()
        root.append(payments)
        
        # Add tax table
        tax_table = self._generate_tax_table_element()
        root.append(tax_table)
        
        return etree.tostring(
            root, 
            pretty_print=True, 
            encoding='UTF-8',
            xml_declaration=True
        ).decode('utf-8')
    
    async def generate_annual_saft(self) -> str:
        """Generate annual SAF-T XML file with assets and inventory"""
        await self.initialize()
        
        root = self._create_root_element()
        
        # Add header
        header = self._generate_header_element()
        root.append(header)
        
        # Add master files
        master_files = await self._generate_master_files_element()
        root.append(master_files)
        
        # Add general ledger entries (annual)
        gl_entries = await self._generate_gl_entries_element()
        root.append(gl_entries)
        
        # Add invoices (if applicable for annual)
        # invoices = await self._generate_invoices_element()
        # root.append(invoices)
        
        # Add assets
        assets = await self._generate_assets_element()
        root.append(assets)
        
        # Add inventory
        inventory = await self._generate_inventory_element()
        root.append(inventory)
        
        # Add tax table
        tax_table = self._generate_tax_table_element()
        root.append(tax_table)
        
        return etree.tostring(
            root,
            pretty_print=True,
            encoding='UTF-8',
            xml_declaration=True
        ).decode('utf-8')
    
    def _create_root_element(self) -> etree.Element:
        """Create root AuditFile element"""
        root = etree.Element('AuditFile')
        root.set('xmlns', 'http://www.bulstat.bg/saft')
        return root
    
    def _generate_header_element(self) -> etree.Element:
        """Generate Header element"""
        header = etree.Element('Header')
        
        # Audit file identification
        etree.SubElement(header, 'AuditFileCountry').text = 'BG'
        etree.SubElement(header, 'AuditFileVersion').text = '2.01'
        etree.SubElement(header, 'AuditFileType').text = 'Standard'
        
        # Company information
        etree.SubElement(header, 'CompanyName').text = self.company.name or ''
        
        # Company ID (EIK)
        etree.SubElement(header, 'CompanyID').text = self.company.eik or ''
        
        # Tax registration (VAT number)
        etree.SubElement(header, 'TaxRegistrationID').text = self.company.vat_number or ''
        
        # Accounting information
        etree.SubElement(header, 'FiscalYear').text = str(self.period_start.year)
        etree.SubElement(header, 'FiscalPeriod').text = str(self.period_start.month)
        
        # Period dates
        etree.SubElement(header, 'StartDate').text = self.period_start.isoformat()
        etree.SubElement(header, 'EndDate').text = self.period_end.isoformat()
        
        # Currency
        etree.SubElement(header, 'CurrencyCode').text = 'BGN'
        etree.SubElement(header, 'BaseCurrency').text = 'BGN'
        
        # Software information
        etree.SubElement(header, 'ProductCompanyName').text = 'Chronos'
        etree.SubElement(header, 'ProductName').text = 'Chronos ERP'
        etree.SubElement(header, 'ProductVersion').text = '1.0'
        
        # Date created
        etree.SubElement(header, 'DateCreated').text = sofia_now().isoformat()
        
        # Signature (placeholder for electronic signature)
        # In production, this would be populated with qualified electronic signature
        
        return header
    
    async def _generate_master_files_element(self) -> etree.Element:
        """Generate MasterFiles element with chart of accounts and parties"""
        master_files = etree.Element('MasterFiles')
        
        # Chart of Accounts
        coa = await self._generate_chart_of_accounts_element()
        master_files.append(coa)
        
        # Customers
        customers = await self._generate_customers_element()
        master_files.append(customers)
        
        # Suppliers
        suppliers = await self._generate_suppliers_element()
        master_files.append(suppliers)
        
        return master_files
    
    async def _generate_chart_of_accounts_element(self) -> etree.Element:
        """Generate Chart of Accounts element"""
        coa = etree.Element('ChartOfAccounts')
        
        # Get all accounts for the company
        result = await self.db.execute(
            select(Account)
            .where(Account.company_id == self.company_id)
            .order_by(Account.code)
        )
        accounts = result.scalars().all()
        
        # If no accounts, create default Bulgarian chart of accounts
        if not accounts:
            accounts = self._get_default_chart_of_accounts()
        
        for acc in accounts:
            # Handle both dict and object types
            if isinstance(acc, dict):
                acc_code = acc.get('code', '')
                acc_name = acc.get('name', '')
                acc_type = acc.get('type', 'Expense')
            else:
                acc_code = acc.code
                acc_name = acc.name
                acc_type = acc.type
            
            account = etree.SubElement(coa, 'Account')
            etree.SubElement(account, 'AccountID').text = acc_code
            etree.SubElement(account, 'AccountName').text = acc_name
            etree.SubElement(account, 'AccountType').text = acc_type
            
            # Opening balance (simplified - would need full GL for actual)
            etree.SubElement(account, 'OpeningBalanceDecimal').text = '0.00'
            etree.SubElement(account, 'ClosingBalanceDecimal').text = '0.00'
        
        return coa
    
    def _get_default_chart_of_accounts(self) -> List[Dict]:
        """Get default Bulgarian chart of accounts"""
        return [
            {'code': '401', 'name': 'Доставчици', 'type': 'Liability'},
            {'code': '402', 'name': 'Персонал', 'type': 'Liability'},
            {'code': '403', 'name': 'Други задължения', 'type': 'Liability'},
            {'code': '411', 'name': 'ДДС', 'type': 'Liability'},
            {'code': '412', 'name': 'Данъци и такси', 'type': 'Liability'},
            {'code': '421', 'name': 'Осигурителни задължения', 'type': 'Liability'},
            {'code': '431', 'name': 'Задължения по заеми', 'type': 'Liability'},
            {'code': '501', 'name': 'Каса', 'type': 'Asset'},
            {'code': '502', 'name': 'Разплащателни сметки', 'type': 'Asset'},
            {'code': '503', 'name': 'Други сметки в лева', 'type': 'Asset'},
            {'code': '601', 'name': 'Разходи за материали', 'type': 'Expense'},
            {'code': '602', 'name': 'Разходи за външни услуги', 'type': 'Expense'},
            {'code': '603', 'name': 'Разходи за амортизации', 'type': 'Expense'},
            {'code': '604', 'name': 'Разходи за заплати', 'type': 'Expense'},
            {'code': '605', 'name': 'Разходи за осигуровки', 'type': 'Expense'},
            {'code': '609', 'name': 'Други разходи', 'type': 'Expense'},
            {'code': '611', 'name': 'Разходи за суровини и материали', 'type': 'Expense'},
            {'code': '701', 'name': 'Приходи от продажби', 'type': 'Revenue'},
            {'code': '702', 'name': 'Приходи от услуги', 'type': 'Revenue'},
            {'code': '703', 'name': 'Приходи от финансирания', 'type': 'Revenue'},
            {'code': '704', 'name': 'Други приходи', 'type': 'Revenue'},
            {'code': '101', 'name': 'Основен капитал', 'type': 'Equity'},
            {'code': '102', 'name': 'Резерви', 'type': 'Equity'},
            {'code': '120', 'name': 'Неразпределена печалба', 'type': 'Equity'},
        ]
    
    async def _generate_customers_element(self) -> etree.Element:
        """Generate Customers element"""
        customers = etree.Element('Customers')
        
        # Query customers from invoices (unique)
        result = await self.db.execute(
            select(Invoice.client_eik, Invoice.client_name)
            .where(Invoice.company_id == self.company_id)
            .where(Invoice.type == 'outgoing')
            .where(Invoice.date >= self.period_start)
            .where(Invoice.date <= self.period_end)
            .distinct()
        )
        customer_data = result.all()
        
        for idx, (eik, name) in enumerate(customer_data, 1):
            if not eik:
                continue
            customer = etree.SubElement(customers, 'Customer')
            etree.SubElement(customer, 'CustomerID').text = str(idx)
            etree.SubElement(customer, 'CustomerName').text = name or ''
            etree.SubElement(customer, 'TIN').text = eik
            # VAT ID would be extracted if available
            etree.SubElement(customer, 'Address').text = ''
        
        return customers
    
    async def _generate_suppliers_element(self) -> etree.Element:
        """Generate Suppliers element"""
        suppliers = etree.Element('Suppliers')
        
        # Query suppliers
        result = await self.db.execute(
            select(Supplier)
            .where(Supplier.company_id == self.company_id)
        )
        supplier_list = result.scalars().all()
        
        for sup in supplier_list:
            supplier = etree.SubElement(suppliers, 'Supplier')
            etree.SubElement(supplier, 'SupplierID').text = str(sup.id)
            etree.SubElement(supplier, 'SupplierName').text = sup.name or ''
            etree.SubElement(supplier, 'TIN').text = sup.eik or ''
            etree.SubElement(supplier, 'VATID').text = sup.vat_number or ''
            etree.SubElement(supplier, 'Address').text = sup.address or ''
        
        return suppliers
    
    async def _generate_gl_entries_element(self) -> etree.Element:
        """Generate GeneralLedgerEntries element"""
        gl_entries = etree.Element('GeneralLedgerEntries')
        
        # Journal
        journal = etree.SubElement(gl_entries, 'Journal')
        
        # Get accounting entries for period
        result = await self.db.execute(
            select(AccountingEntry)
            .where(AccountingEntry.company_id == self.company_id)
            .where(AccountingEntry.date >= self.period_start)
            .where(AccountingEntry.date <= self.period_end)
            .order_by(AccountingEntry.date, AccountingEntry.entry_number)
            .options(
                selectinload(AccountingEntry.debit_account),
                selectinload(AccountingEntry.credit_account)
            )
        )
        entries = result.scalars().all()
        
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for entry in entries:
            je = etree.SubElement(journal, 'JournalEntry')
            etree.SubElement(je, 'EntryNo').text = entry.entry_number or str(entry.id)
            etree.SubElement(je, 'Date').text = entry.date.isoformat()
            etree.SubElement(je, 'Description').text = entry.description or ''
            etree.SubElement(je, 'SystemID').text = 'CHRONOS'
            
            # Debit line
            debit_line = etree.SubElement(je, 'DebitLine')
            etree.SubElement(debit_line, 'AccountID').text = (
                entry.debit_account.code if entry.debit_account else '000'
            )
            etree.SubElement(debit_line, 'Amount').text = f"{float(entry.amount):.2f}"
            
            # Credit line
            credit_line = etree.SubElement(je, 'CreditLine')
            etree.SubElement(credit_line, 'AccountID').text = (
                entry.credit_account.code if entry.credit_account else '000'
            )
            etree.SubElement(credit_line, 'Amount').text = f"{float(entry.amount):.2f}"
            
            total_debit += entry.amount
            total_credit += entry.amount
        
        # If no entries, add sample for demo
        if not entries:
            # Add zero totals
            pass
        
        # Totals
        etree.SubElement(gl_entries, 'TotalDebit').text = f"{float(total_debit):.2f}"
        etree.SubElement(gl_entries, 'TotalCredit').text = f"{float(total_credit):.2f}"
        
        return gl_entries
    
    async def _generate_invoices_element(self) -> etree.Element:
        """Generate Invoices element"""
        invoices = etree.Element('Invoices')
        
        # Get all invoices for period
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.company_id == self.company_id)
            .where(Invoice.date >= self.period_start)
            .where(Invoice.date <= self.period_end)
            .options(selectinload(Invoice.items))
        )
        invoice_list = result.scalars().all()
        
        for inv in invoice_list:
            invoice = etree.SubElement(invoices, 'Invoice')
            
            # Invoice identification
            etree.SubElement(invoice, 'InvoiceNo').text = inv.number or ''
            etree.SubElement(invoice, 'IssueDate').text = inv.date.isoformat()
            
            # Invoice type
            inv_type = 'Outgoing' if inv.type == 'outgoing' else 'Incoming'
            etree.SubElement(invoice, 'InvoiceType').text = inv_type
            
            # Supplier/Customer
            etree.SubElement(invoice, 'SupplierPartyID').text = str(inv.supplier_id) if inv.supplier_id else ''
            etree.SubElement(invoice, 'CustomerPartyID').text = inv.client_eik or ''
            
            # Currency
            etree.SubElement(invoice, 'DocumentCurrencyCode').text = 'BGN'
            
            # Tax basis
            etree.SubElement(invoice, 'TaxBasisTotalAmount').text = f"{float(inv.subtotal or 0):.2f}"
            etree.SubElement(invoice, 'TaxTotalAmount').text = f"{float(inv.vat_amount or 0):.2f}"
            etree.SubElement(invoice, 'InvoiceTotalAmount').text = f"{float(inv.total or 0):.2f}"
            
            # Payment info
            if inv.due_date:
                payment_terms = etree.SubElement(invoice, 'PaymentTerms')
                etree.SubElement(payment_terms, 'DueDate').text = inv.due_date.isoformat()
            
            # Lines
            for idx, item in enumerate(inv.items or [], 1):
                line = etree.SubElement(invoice, 'Line')
                etree.SubElement(line, 'LineNo').text = str(idx)
                
                invoice_line = etree.SubElement(line, 'InvoiceLine')
                etree.SubElement(invoice_line, 'ItemName').text = item.name or ''
                etree.SubElement(invoice_line, 'Quantity').text = f"{float(item.quantity or 0):.3f}"
                etree.SubElement(invoice_line, 'UnitCode').text = item.unit or 'pcs'
                etree.SubElement(invoice_line, 'UnitPrice').text = f"{float(item.unit_price or 0):.2f}"
                etree.SubElement(invoice_line, 'LineTotalAmount').text = f"{float(item.total or 0):.2f}"
                
                # Tax line
                if inv.vat_rate and inv.vat_rate > 0:
                    tax_line = etree.SubElement(invoice_line, 'TaxLine')
                    etree.SubElement(tax_line, 'TaxType').text = 'VAT'
                    etree.SubElement(tax_line, 'TaxAmount').text = f"{float(item.total * Decimal(str(inv.vat_rate / 100)) or 0):.2f}"
                    etree.SubElement(tax_line, 'TaxPercentage').text = f"{float(inv.vat_rate):.2f}"
        
        return invoices
    
    async def _generate_payments_element(self) -> etree.Element:
        """Generate Payments element"""
        payments = etree.Element('Payments')
        
        # Get cash journal entries for period
        result = await self.db.execute(
            select(CashJournalEntry)
            .where(CashJournalEntry.company_id == self.company_id)
            .where(CashJournalEntry.date >= self.period_start)
            .where(CashJournalEntry.date <= self.period_end)
        )
        cash_entries = result.scalars().all()
        
        for entry in cash_entries:
            payment = etree.SubElement(payments, 'Payment')
            etree.SubElement(payment, 'PaymentNo').text = str(entry.id)
            etree.SubElement(payment, 'PaymentDate').text = entry.date.isoformat()
            etree.SubElement(payment, 'PaymentType').text = entry.operation_type or ''
            etree.SubElement(payment, 'Amount').text = f"{float(entry.amount or 0):.2f}"
            etree.SubElement(payment, 'Description').text = entry.description or ''
        
        return payments
    
    def _generate_tax_table_element(self) -> etree.Element:
        """Generate TaxTable element"""
        tax_table = etree.Element('TaxTable')
        
        # Standard VAT rates in Bulgaria
        tax_rates = [
            {'code': '20', 'name': 'Standard VAT rate', 'rate': '20.00'},
            {'code': '9', 'name': 'Reduced VAT rate', 'rate': '9.00'},
            {'code': '0', 'name': 'Zero VAT rate', 'rate': '0.00'},
            {'code': 'EX', 'name': 'Exempt VAT', 'rate': '0.00'},
        ]
        
        for tax in tax_rates:
            entry = etree.SubElement(tax_table, 'TaxTableEntry')
            etree.SubElement(entry, 'TaxType').text = 'VAT'
            etree.SubElement(entry, 'TaxCode').text = tax['code']
            etree.SubElement(entry, 'TaxPercentage').text = tax['rate']
            etree.SubElement(entry, 'TaxDescription').text = tax['name']
        
        return tax_table
    
    async def _generate_assets_element(self) -> etree.Element:
        """Generate Assets element (for annual SAF-T)"""
        assets = etree.Element('Assets')
        # Placeholder - would need Asset model
        # For now, return empty element
        return assets
    
    async def _generate_inventory_element(self) -> etree.Element:
        """Generate Inventory element (for annual SAF-T)"""
        inventory = etree.Element('Inventory')
        # Placeholder - would need inventory tracking
        # For now, return empty element
        return inventory


class SAFTValidator:
    """
    Validates SAF-T XML files against Bulgarian requirements.
    """
    
    REQUIRED_HEADER_FIELDS = [
        'AuditFileCountry',
        'AuditFileVersion', 
        'CompanyName',
        'CompanyID',
        'FiscalYear',
        'FiscalPeriod',
        'StartDate',
        'EndDate',
        'CurrencyCode'
    ]
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, xml_content: str) -> Dict[str, Any]:
        """
        Validate SAF-T XML content.
        
        Returns:
            dict with 'status', 'errors', 'warnings'
        """
        self.errors = []
        self.warnings = []
        
        # Parse XML
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
        except Exception as e:
            self.errors.append(f"Invalid XML: {str(e)}")
            return self._get_result('error')
        
        # Get namespace
        ns = {'sa': root.nsmap.get(None, '')}
        
        # Validate structure
        self._validate_header(root, ns)
        self._validate_balances(root, ns)
        self._validate_invoices(root, ns)
        
        # Check for required elements
        if not root.find('.//sa:Header', ns):
            self.errors.append("Missing required element: Header")
        
        if not root.find('.//sa:MasterFiles', ns):
            self.errors.append("Missing required element: MasterFiles")
        
        if not root.find('.//sa:GeneralLedgerEntries', ns):
            self.errors.append("Missing required element: GeneralLedgerEntries")
        
        if not root.find('.//sa:Invoices', ns):
            self.warnings.append("Missing element: Invoices (may be empty)")
        
        if not root.find('.//sa:TaxTable', ns):
            self.errors.append("Missing required element: TaxTable")
        
        status = 'valid' if not self.errors else 'invalid'
        return self._get_result(status)
    
    def _validate_header(self, root: etree.Element, ns: dict):
        """Validate header element"""
        header = root.find('.//sa:Header', ns)
        if not header:
            return
        
        for field in self.REQUIRED_HEADER_FIELDS:
            element = header.find(f'sa:{field}', ns)
            if element is None or not element.text:
                self.errors.append(f"Missing required header field: {field}")
        
        # Validate country is Bulgaria
        country = header.find('sa:AuditFileCountry', ns)
        if country is not None and country.text != 'BG':
            self.errors.append(f"Invalid country code: {country.text}. Expected 'BG'")
        
        # Validate dates
        start_date = header.find('sa:StartDate', ns)
        end_date = header.find('sa:EndDate', ns)
        if start_date is not None and end_date is not None:
            if start_date.text and end_date.text and start_date.text > end_date.text:
                self.errors.append("StartDate cannot be after EndDate")
    
    def _validate_balances(self, root: etree.Element, ns: dict):
        """Validate general ledger balances"""
        gl_entries = root.find('.//sa:GeneralLedgerEntries', ns)
        if gl_entries is None:
            return
        
        total_debit = gl_entries.find('sa:TotalDebit', ns)
        total_credit = gl_entries.find('sa:TotalCredit', ns)
        
        if total_debit is not None and total_credit is not None:
            try:
                debit = float(total_debit.text or 0)
                credit = float(total_credit.text or 0)
                if abs(debit - credit) > 0.01:
                    self.errors.append(
                        f"General ledger is not balanced: "
                        f"Debit={debit:.2f}, Credit={credit:.2f}"
                    )
            except (ValueError, AttributeError):
                self.errors.append("Invalid TotalDebit or TotalCredit values")
    
    def _validate_invoices(self, root: etree.Element, ns: dict):
        """Validate invoice entries"""
        invoices = root.findall('.//sa:Invoice', ns)
        
        for invoice in invoices:
            # Check required fields
            invoice_no = invoice.find('sa:InvoiceNo', ns)
            if invoice_no is None or not invoice_no.text:
                self.errors.append("Invoice missing InvoiceNo")
            
            issue_date = invoice.find('sa:IssueDate', ns)
            if issue_date is None or not issue_date.text:
                self.errors.append(f"Invoice {invoice_no.text if invoice_no is not None else 'unknown'} missing IssueDate")
            
            # Check amounts
            total = invoice.find('sa:InvoiceTotalAmount', ns)
            tax_total = invoice.find('sa:TaxTotalAmount', ns)
            tax_basis = invoice.find('sa:TaxBasisTotalAmount', ns)
            
            if total is not None and tax_total is not None and tax_basis is not None:
                try:
                    total_amt = float(total.text or 0)
                    tax_amt = float(tax_total.text or 0)
                    basis_amt = float(tax_basis.text or 0)
                    
                    # Basic validation
                    if tax_amt > total_amt:
                        self.errors.append(
                            f"Invoice {invoice_no.text if invoice_no is not None else ''}: "
                            f"TaxTotalAmount > InvoiceTotalAmount"
                        )
                except (ValueError, AttributeError):
                    pass
    
    def _get_result(self, status: str) -> Dict[str, Any]:
        """Build result dictionary"""
        return {
            'status': status,
            'errors': self.errors,
            'warnings': self.warnings,
            'is_valid': status == 'valid'
        }


async def generate_saft_file(
    db: AsyncSession,
    company_id: int,
    year: int,
    month: int,
    saft_type: Optional[str] = 'monthly'
) -> Dict[str, Any]:
    """
    Main function to generate SAF-T file.
    
    Args:
        db: Database session
        company_id: Company ID
        year: Year
        month: Month
        saft_type: 'monthly', 'annual', or 'on_demand'
    
    Returns:
        dict with 'xml_content', 'validation_result', 'period_start', 'period_end'
    """
    # Calculate period
    period_start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    period_end = date(year, month, last_day)
    
    # Create generator
    generator = SAFTGenerator(db, company_id, period_start, period_end)
    
    # Generate XML
    if saft_type == 'annual':
        xml_content = await generator.generate_annual_saft()
    else:
        xml_content = await generator.generate_monthly_saft()
    
    # Validate
    validator = SAFTValidator()
    validation_result = validator.validate(xml_content)
    
    return {
        'xml_content': xml_content,
        'validation_result': validation_result,
        'period_start': period_start,
        'period_end': period_end,
        'file_size': len(xml_content),
        'file_name': f"SAF-T_{company_id}_{year}_{month:02d}_{saft_type}.xml"
    }
