export interface InvoiceItem {
  id: number;
  ingredientId?: number | null;
  batchId?: number | null;
  name: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  unitPriceWithVat?: number | null;
  discountPercent?: number | null;
  discountAmount?: number | null;
  vatRate: number;
  vatAmount: number;
  total: number;
  batchNumber?: string | null;
  expirationDate?: string | null;
}

export interface Invoice {
  id: number;
  number: string;
  type: string;
  documentType: string;
  griff?: string | null;
  description?: string | null;
  deliveryMethod?: string | null;
  date: string;
  clientName?: string | null;
  clientEik?: string | null;
  clientAddress?: string | null;
  subtotal: number;
  discountPercent?: number | null;
  discountAmount?: number | null;
  vatRate: number;
  vatAmount: number;
  total: number;
  paymentMethod: string;
  paymentDate?: string | null;
  dueDate?: string | null;
  status: string;
  notes?: string | null;
  isCorrected?: boolean;
  originalInvoiceId?: number | null;
  items?: InvoiceItem[];
}

export interface AccountingSummary {
  period: string;
  totalIncome: number;
  totalExpense: number;
  netProfit: number;
  vatCollected: number;
  vatPaid: number;
  cashIncome: number;
  cashExpense: number;
  cashBalance: number;
  year?: number;
  month?: number;
  invoicesCount?: number;
  incomingInvoicesCount?: number;
  outgoingInvoicesCount?: number;
  invoicesTotal?: number;
  date?: string;
  id?: number;
}

export interface Account {
  id: number;
  name: string;
  code: string;
  balance: number;
  type?: string;
  isDefault?: boolean;
  isActive?: boolean;
  iban?: string;
  bankName?: string;
  bic?: string;
  accountType?: string;
  currency?: string;
}

export interface Transaction {
  id: number;
  date: string;
  description: string;
  amount: number;
  accountId: number;
  type?: string;
  reference?: string;
  matched?: boolean;
  invoiceId?: number | null;
  bankAccountId?: number | null;
}

export interface Register {
  id: number;
  name: string;
  balance: number;
  periodMonth: number;
  periodYear: number;
  vatDue: number;
  vatCredit: number;
  vatCollected20?: number;
  vatCollected9?: number;
  vatPaid20?: number;
  vatPaid9?: number;
}

export interface AccountingLog {
  id: number;
  action: string;
  user: { firstName?: string; lastName?: string } | string;
  timestamp: string;
  details?: string;
  operation?: string;
  entityType?: string;
  entityId?: number;
  changes?: string;
}

export interface ChartOfAccount {
  id: number;
  code: string;
  name: string;
  type: string;
  balance: number;
}

export interface BankTransaction {
  id: number;
  date: string;
  amount: number;
  description?: string | null;
  partnerName?: string | null;
  partnerIban?: string | null;
  reference?: string | null;
  status: string;
}

export interface CashJournalEntry {
  id: number;
  date: string;
  number: string;
  type: string;
  amount: number;
  description?: string | null;
  personName?: string | null;
  operationType?: string | null;
  creator?: {
    firstName: string;
    lastName: string;
  } | null;
}

export interface AccountingOperation {
  id: number;
  date: string;
  number: string;
  description?: string | null;
  totalAmount: number;
}

export interface Payslip {
  id: number;
  periodStart: string;
  periodEnd: string;
  totalAmount: number;
  regularAmount: number;
  overtimeAmount: number;
  bonusAmount: number;
  taxAmount: number;
  insuranceAmount: number;
  totalRegularHours: number;
  totalOvertimeHours: number;
  sickDays: number;
  leaveDays: number;
}