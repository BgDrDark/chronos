import { formatDate } from '../utils/dateUtils';
import React, { useState, useEffect } from 'react';
import { Ingredient, getErrorMessage } from '../types';
import { useCurrency, formatCurrencyValue } from '../currencyContext';
import {
  Typography,
  Box,
  Container,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  CircularProgress,
  Alert,
  Select,
  FormControl,
  InputLabel,
  Radio,
  RadioGroup,
  FormControlLabel,
  Checkbox,
  FormLabel,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Divider,
  InputAdornment,
  Tooltip,
  Autocomplete,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  Print as PrintIcon,
  Close as CloseIcon,
  FileCopy as FileCopyIcon,
} from '@mui/icons-material';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import { useQuery, useMutation, useLazyQuery, gql } from '@apollo/client';
import { InfoIcon } from '../components/ui/InfoIcon';
import { useError, extractErrorMessage } from '../context/ErrorContext';
import {
  InvoiceList,
  CashJournalTab,
  OperationLogsTab,
  DailySummaryTab,
  MonthlyReportTab,
  YearlyReportTab,
  ProformaTab,
  CorrectionsTab,
  BankTab,
  AccountsTab,
  VATTab,
  SAFTTab,
  AccountingEntriesTab,
} from '../components/accounting';
import {
  type CashJournalEntry, type Supplier
} from '../types';

interface ValidatedTextFieldProps {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  tooltip?: string;
  placeholder?: string;
  error?: string;
  required?: boolean;
  type?: 'text' | 'number' | 'date';
  select?: boolean;
  children?: React.ReactNode;
  size?: 'small' | 'medium';
  fullWidth?: boolean;
  disabled?: boolean;
  multiline?: boolean;
  rows?: number;
  InputProps?: { sx?: object; endAdornment?: React.ReactNode };
  InputLabelProps?: Record<string, unknown>;
  sx?: Record<string, unknown>;
}

const ValidatedTextField: React.FC<ValidatedTextFieldProps> = ({
  label, value, onChange, tooltip, placeholder, error, required,
  type = 'text', select, children, size = 'small', fullWidth = true,
  disabled, multiline, rows, InputProps, InputLabelProps, sx
}) => {
  const showError = !!error;
  const hasValue = value !== '' && value !== null && value !== undefined;

  const endAdornment = tooltip ? (
    <InputAdornment position="end">
      <InfoIcon helpText={tooltip} />
    </InputAdornment>
  ) : InputProps?.endAdornment;
  
  return (
    <TextField
      label={label}
      value={value}
      onChange={(e) => {
        if (type === 'number') {
          onChange(e.target.value.replace(/[^0-9.]/g, ''));
        } else {
          onChange(e.target.value);
        }
      }}
      placeholder={placeholder}
      error={showError}
      helperText={error}
      required={required}
      type={type}
      select={select}
      size={size}
      fullWidth={fullWidth}
      disabled={disabled}
      multiline={multiline}
      rows={rows}
      InputLabelProps={InputLabelProps}
      sx={sx}
      slotProps={{
        input: { endAdornment }
      }}
      InputProps={{
        sx: {
          ...InputProps?.sx,
          '& .MuiOutlinedInput-root': {
            '&.Mui-error': {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'error.main',
                borderWidth: 2,
              },
            },
            ...(hasValue && !showError && {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'success.main',
                borderWidth: 2,
              },
            }),
          },
        },
      }}
    >
      {children}
    </TextField>
  );
};

// Helper function to get Bulgarian text for invoice status
const getInvoiceStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'draft': 'Чернова',
    'sent': 'Изпратена',
    'paid': 'Платена',
    'overdue': 'Просрочена',
    'cancelled': 'Анулирана'
  };
  return statusMap[status] || status;
};

// Helper function to get Chip color for invoice status
const getInvoiceStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
  const colorMap: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning'> = {
    'draft': 'default',
    'sent': 'info',
    'paid': 'success',
    'overdue': 'warning',
    'cancelled': 'error'
  };
  return colorMap[status] || 'default';
};

const GET_INVOICES = gql`
  query GetInvoices($type: String, $status: String, $search: String) {
    invoices(type: $type, status: $status, search: $search) {
      id
      number
      type
      documentType
      griff
      description
      date
      supplier {
        id
        name
        eik
        vatNumber
        address
      }
      company {
        id
        name
        eik
        vatNumber
        address
      }
      clientName
      clientEik
      clientAddress
      subtotal
      discountPercent
      discountAmount
      vatRate
      vatAmount
      total
      paymentMethod
      deliveryMethod
      dueDate
      paymentDate
      status
      notes
      batch {
        id
        batchNumber
        expiryDate
      }
      items {
        id
        ingredientId
        name
        quantity
        unit
        unitPrice
        discountPercent
        total
        ingredient {
          id
          name
        }
      }
    }
  }
`;

const GET_SUPPLIERS = gql`
  query GetSuppliers {
    suppliers {
      id
      name
      eik
    }
  }
`;

const GET_INGREDIENTS = gql`
  query GetIngredients {
    ingredients {
      id
      name
      unit
      currentPrice
    }
  }
`;

const GET_INGREDIENT_BATCHES_WITH_STOCK = gql`
  query GetIngredientBatchesWithStock($ingredientId: Int!) {
    ingredientBatchesWithStock(ingredientId: $ingredientId) {
      id
      batchNumber
      quantity
      availableStock
      expiryDate
      status
      supplier {
        id
        name
      }
    }
  }
`;

const CREATE_INVOICE = gql`
  mutation CreateInvoice($invoiceData: InvoiceInput!) {
    createInvoice(invoiceData: $invoiceData) {
      id
      number
    }
  }
`;

const CREATE_PROFORMA_INVOICE = gql`
  mutation CreateProformaInvoice($clientName: String!, $clientEik: String, $clientAddress: String, $date: String!, $items: [InvoiceItemInput!]!, $vatRate: Float!, $discountPercent: Float!, $notes: String) {
    createProformaInvoice(clientName: $clientName, clientEik: $clientEik, clientAddress: $clientAddress, date: $date, items: $items, vatRate: $vatRate, discountPercent: $discountPercent, notes: $notes) {
      id
      number
    }
  }
`;

const UPDATE_INVOICE = gql`
  mutation UpdateInvoice($id: Int!, $invoiceData: InvoiceInput!) {
    updateInvoice(id: $id, invoiceData: $invoiceData) {
      id
      number
    }
  }
`;

const DELETE_INVOICE = gql`
  mutation DeleteInvoice($id: Int!) {
    deleteInvoice(id: $id)
  }
`;

const GET_INVOICE_PDF_URL = gql`
  mutation GetInvoicePdfUrl($invoiceId: Int!) {
    getInvoicePdfUrl(invoiceId: $invoiceId)
  }
`;

const GET_CASH_JOURNAL_ENTRIES = gql`
  query GetCashJournalEntries($startDate: String, $endDate: String, $operationType: String) {
    cashJournalEntries(startDate: $startDate, endDate: $endDate, operationType: $operationType) {
      id
      date
      operationType
      amount
      description
      referenceType
      referenceId
      createdAt
      creator {
        firstName
        lastName
      }
    }
  }
`;

const CREATE_CASH_JOURNAL_ENTRY = gql`
  mutation CreateCashJournalEntry($input: CashJournalEntryInput!) {
    createCashJournalEntry(input: $input) {
      id
      date
      operationType
      amount
    }
  }
`;

const DELETE_CASH_JOURNAL_ENTRY = gql`
  mutation DeleteCashJournalEntry($id: Int!) {
    deleteCashJournalEntry(id: $id)
  }
`;

const GET_OPERATION_LOGS = gql`
  query GetOperationLogs($startDate: String, $endDate: String, $operation: String, $entityType: String) {
    operationLogs(startDate: $startDate, endDate: $endDate, operation: $operation, entityType: $entityType) {
      id
      timestamp
      operation
      entityType
      entityId
      changes
      user {
        firstName
        lastName
      }
    }
  }
`;

const GET_DAILY_SUMMARIES = gql`
  query GetDailySummaries($startDate: String, $endDate: String) {
    dailySummaries(startDate: $startDate, endDate: $endDate) {
      id
      date
      invoicesCount
      incomingInvoicesCount
      outgoingInvoicesCount
      invoicesTotal
      incomingInvoicesTotal
      outgoingInvoicesTotal
      cashIncome
      cashExpense
      cashBalance
      vatCollected
      vatPaid
      paidInvoicesCount
      unpaidInvoicesCount
      overdueInvoicesCount
    }
  }
`;

const GENERATE_DAILY_SUMMARY = gql`
  mutation GenerateDailySummary($date: String!) {
    generateDailySummary(date: $date) {
      id
      date
      invoicesCount
      invoicesTotal
      cashIncome
      cashExpense
      cashBalance
    }
  }
`;

const GET_MONTHLY_SUMMARIES = gql`
  query GetMonthlySummaries($startYear: Int, $endYear: Int) {
    monthlySummaries(startYear: $startYear, endYear: $endYear) {
      id
      year
      month
      invoicesCount
      incomingInvoicesCount
      outgoingInvoicesCount
      invoicesTotal
      incomingInvoicesTotal
      outgoingInvoicesTotal
      cashIncome
      cashExpense
      cashBalance
      vatCollected
      vatPaid
      paidInvoicesCount
      unpaidInvoicesCount
      overdueInvoicesCount
    }
  }
`;

const GENERATE_MONTHLY_SUMMARY = gql`
  mutation GenerateMonthlySummary($year: Int!, $month: Int!) {
    generateMonthlySummary(year: $year, month: $month) {
      id
      year
      month
      invoicesCount
      invoicesTotal
      cashIncome
      cashExpense
      cashBalance
    }
  }
`;

const GET_YEARLY_SUMMARIES = gql`
  query GetYearlySummaries($startYear: Int, $endYear: Int) {
    yearlySummaries(startYear: $startYear, endYear: $endYear) {
      id
      year
      invoicesCount
      incomingInvoicesCount
      outgoingInvoicesCount
      invoicesTotal
      incomingInvoicesTotal
      outgoingInvoicesTotal
      cashIncome
      cashExpense
      cashBalance
      vatCollected
      vatPaid
      paidInvoicesCount
      unpaidInvoicesCount
      overdueInvoicesCount
    }
  }
`;

const GENERATE_YEARLY_SUMMARY = gql`
  mutation GenerateYearlySummary($year: Int!) {
    generateYearlySummary(year: $year) {
      id
      year
      invoicesCount
      invoicesTotal
      cashIncome
      cashExpense
      cashBalance
    }
  }
`;

const GET_ACCOUNTING_ENTRIES = gql`
  query GetAccountingEntries($startDate: String, $endDate: String, $accountId: Int, $search: String) {
    accountingEntries(startDate: $startDate, endDate: $endDate, accountId: $accountId, search: $search) {
      id
      date
      entryNumber
      description
      debitAccountId
      creditAccountId
      debitAccount {
        id
        code
        name
      }
      creditAccount {
        id
        code
        name
      }
      amount
      vatAmount
      invoiceId
      invoice {
        id
        number
      }
      createdAt
    }
  }
`;

// ============== NEW ACCOUNTING QUERIES ==============

const GET_PROFORMA_INVOICES = gql`
  query GetProformaInvoices($status: String, $search: String) {
    proformaInvoices(status: $status, search: $search) {
      id
      number
      date
      clientName
      clientEik
      subtotal
      vatRate
      vatAmount
      total
      status
    }
  }
`;

const GET_INVOICE_CORRECTIONS = gql`
  query GetInvoiceCorrections($type: String, $status: String) {
    invoiceCorrections(type: $type, status: $status) {
      id
      number
      type
      date
      originalInvoiceId
      clientName
      clientEik
      reason
      subtotal
      vatAmount
      total
      status
    }
  }
`;

const CREATE_INVOICE_CORRECTION = gql`
  mutation CreateInvoiceCorrection(
    $originalInvoiceId: Int!
    $correctionType: String!
    $reason: String!
    $correctionDate: Date!
    $createNewInvoice: Boolean
  ) {
    createInvoiceCorrection(
      originalInvoiceId: $originalInvoiceId
      correctionType: $correctionType
      reason: $reason
      correctionDate: $correctionDate
      createNewInvoice: $createNewInvoice
    ) {
      id
      number
      type
      date
      originalInvoiceId
      clientName
      reason
      subtotal
      vatAmount
      total
      status
    }
  }
`;

// These queries/mutations are available for future use:
/*
const GET_CASH_RECEIPTS = gql`...
const GET_ACCOUNTING_ENTRIES = gql`...
const CREATE_CASH_RECEIPT = gql`...
const CREATE_ACCOUNTING_ENTRY = gql`...
const MATCH_BANK_TRANSACTION = gql`...
*/

const GET_BANK_ACCOUNTS = gql`
  query GetBankAccounts($isActive: Boolean) {
    bankAccounts(isActive: $isActive) {
      id
      iban
      bic
      bankName
      accountType
      isDefault
      currency
      isActive
    }
  }
`;

const GET_BANK_TRANSACTIONS = gql`
  query GetBankTransactions($bankAccountId: Int, $startDate: String, $endDate: String, $matched: Boolean) {
    bankTransactions(bankAccountId: $bankAccountId, startDate: $startDate, endDate: $endDate, matched: $matched) {
      id
      bankAccountId
      date
      amount
      type
      description
      reference
      invoiceId
      matched
    }
  }
`;

const MATCH_BANK_TRANSACTION = gql`
  mutation MatchBankTransaction($transactionId: Int!, $invoiceId: Int!) {
    matchBankTransaction(transactionId: $transactionId, invoiceId: $invoiceId) {
      id
      matched
      invoiceId
    }
  }
`;

const UNMATCH_BANK_TRANSACTION = gql`
  mutation UnmatchBankTransaction($transactionId: Int!) {
    unmatchBankTransaction(transactionId: $transactionId) {
      id
      matched
      invoiceId
    }
  }
`;

const AUTO_MATCH_BANK_TRANSACTIONS = gql`
  mutation AutoMatchBankTransactions($bankAccountId: Int!) {
    autoMatchBankTransactions(bankAccountId: $bankAccountId) {
      matchedCount
      unmatchedCount
    }
  }
`;

const GET_ACCOUNTS = gql`
  query GetAccounts($type: String, $parentId: Int) {
    accounts(type: $type, parentId: $parentId) {
      id
      code
      name
      type
      parentId
      openingBalance
      closingBalance
    }
  }
`;

// These queries/mutations are available for future use:
/*
const GET_CASH_RECEIPTS = gql`...
const GET_ACCOUNTING_ENTRIES = gql`...
const CREATE_CASH_RECEIPT = gql`...
const CREATE_ACCOUNTING_ENTRY = gql`...
const MATCH_BANK_TRANSACTION = gql`...
*/

const GET_VAT_REGISTERS = gql`
  query GetVATRegisters($year: Int, $month: Int) {
    vatRegisters(year: $year, month: $month) {
      id
      periodMonth
      periodYear
      vatCollected20
      vatCollected9
      vatPaid20
      vatPaid9
      vatDue
      vatCredit
    }
  }
`;

const GENERATE_SAFT_FILE = gql`
  mutation GenerateSAFTFile($companyId: Int!, $year: Int!, $month: Int!, $saftType: String) {
    generateSAFTFile(companyId: $companyId, year: $year, month: $month, saftType: $saftType) {
      xmlContent
      fileSize
      fileName
      periodStart
      periodEnd
      validationResult {
        status
        errors
        warnings
      }
    }
  }
 `;

/*
const CREATE_CASH_RECEIPT = gql`...
*/

const CREATE_BANK_ACCOUNT = gql`
  mutation CreateBankAccount($input: BankAccountInput!) {
    createBankAccount(input: $input) {
      id
      iban
    }
  }
`;

const CREATE_BANK_TRANSACTION = gql`
  mutation CreateBankTransaction($input: BankTransactionInput!) {
    createBankTransaction(input: $input) {
      id
      reference
    }
  }
`;

const CREATE_ACCOUNT = gql`
  mutation CreateAccount($input: AccountInput!) {
    createAccount(input: $input) {
      id
      code
    }
  }
`;

/*
const CREATE_ACCOUNTING_ENTRY = gql`...
const MATCH_BANK_TRANSACTION = gql`...
*/

const GENERATE_VAT_REGISTER = gql`
  mutation GenerateVATRegister($input: VATRegisterInput!) {
    generateVATRegister(input: $input) {
      id
      periodMonth
      periodYear
      vatDue
      vatCredit
    }
  }
`;

/* Future use:
const MATCH_BANK_TRANSACTION = gql`...
*/

interface InvoiceItem {
  id?: number;
  ingredientId?: number | null;
  batchId?: number | null;
  batch?: {
    id: number;
    batchNumber?: string | null;
    expiryDate?: string | null;
    availableStock?: number;
    supplier?: { id: number; name: string } | null;
  } | null;
  batchNumber?: string | null;
  expirationDate?: string | null;
  name: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  unitPriceWithVat?: number | null;
  discountPercent: number;
}

interface Invoice {
  id: number;
  number: string;
  type: string;
  documentType?: string | null;
  griff?: string | null;
  description?: string | null;
  deliveryMethod?: string | null;
  date: string;
  supplier?: { id: number; name: string; eik?: string; vatNumber?: string; address?: string } | null;
  company?: { id: number; name: string; eik?: string; vatNumber?: string; address?: string } | null;
  clientName?: string | null;
  clientEik?: string | null;
  clientAddress?: string | null;
  subtotal: number;
  discountPercent?: number | null;
  discountAmount?: number | null;
  vatRate: number;
  vatAmount: number;
  total: number;
  paymentMethod?: string | null;
  dueDate?: string | null;
  paymentDate?: string | null;
  status: string;
  notes?: string | null;
  isCorrected?: boolean;
  items: InvoiceItem[];
  originalInvoiceId?: number | null;
  batch?: string | null;
}

interface Props {
  tab?: string;
}

export default function AccountingPage({ tab }: Props) {
  const activeTab = tab ?? 'incoming';
  const { currency } = useCurrency();
  const { showError, showSuccess } = useError();

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };
  
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null);
  const [itemBatches, setItemBatches] = useState<Record<number, Array<{
    id: number;
    batchNumber: string | null;
    expiryDate: string | null;
    availableStock: number;
    supplier: { id: number; name: string } | null;
  }>>>({});
  const [loadingBatchItemIndex, setLoadingBatchItemIndex] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    type: 'incoming',
    documentType: 'ФАКТУРА',
    griff: 'ОРИГИНАЛ',
    description: '',
    date: new Date().toISOString().split('T')[0],
    supplierId: null as number | null,
    clientName: '',
    clientEik: '',
    clientAddress: '',
    discountPercent: 0,
    vatRate: 20,
    paymentMethod: '',
    deliveryMethod: '',
    dueDate: '',
    paymentDate: '',
    status: 'draft',
    notes: '',
    items: [] as InvoiceItem[],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const invoiceType = activeTab === 'incoming' ? 'incoming' : 'outgoing';

  const { refetch } = useQuery(GET_INVOICES, {
    variables: { type: invoiceType, search: search || undefined },
  });

  const { data: suppliersData } = useQuery(GET_SUPPLIERS);
  const { data: ingredientsData } = useQuery(GET_INGREDIENTS);

  const [loadIngredientBatches, { data: batchesData }] = useLazyQuery(GET_INGREDIENT_BATCHES_WITH_STOCK);

  useEffect(() => {
    if (batchesData?.ingredientBatchesWithStock && loadingBatchItemIndex !== null) {
      setItemBatches(prev => ({
        ...prev,
        [loadingBatchItemIndex]: batchesData.ingredientBatchesWithStock
      }));
      setLoadingBatchItemIndex(null);
    }
  }, [batchesData, loadingBatchItemIndex]);

  const [createInvoice] = useMutation(CREATE_INVOICE);
  const [createProformaInvoice] = useMutation(CREATE_PROFORMA_INVOICE);
  const [updateInvoice] = useMutation(UPDATE_INVOICE);
  const [deleteInvoice] = useMutation(DELETE_INVOICE);
  const [getInvoicePdfUrl] = useMutation(GET_INVOICE_PDF_URL);

  const handleOpenDetailsDialog = (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setDetailsDialogOpen(true);
  };

  const handleCloseDetailsDialog = () => {
    setDetailsDialogOpen(false);
    setSelectedInvoice(null);
  };

  const handlePrintInvoice = async (invoiceId: number) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'https://dev.oblak24.org';
      const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrf_token='))?.split('=')[1];
      
      const response = await fetch(`${apiUrl}/export/invoice/${invoiceId}/pdf`, {
        headers: {
          'X-CSRFToken': csrfToken || '',
        },
        credentials: 'include'
      });
      
      if (response.status === 401 || response.status === 403) {
        window.location.href = '/login';
        return;
      }
      
      if (!response.ok) {
        throw new Error(`Failed to load PDF: ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const printWindow = window.open(url, '_blank');
      
      if (printWindow) {
        printWindow.focus();
      }
    } catch (err) {
      alert('Грешка при принтиране на фактура: ' + getErrorMessage(err));
    }
  };

  const calculateTotals = () => {
    let subtotal = 0;
    formData.items.forEach(item => {
      const itemTotal = item.quantity * item.unitPrice;
      const itemDiscount = itemTotal * (item.discountPercent / 100);
      subtotal += itemTotal - itemDiscount;
    });
    const discountAmount = subtotal * (formData.discountPercent / 100);
    const subtotalAfterDiscount = subtotal - discountAmount;
    const vatAmount = subtotalAfterDiscount * (formData.vatRate / 100);
    const total = subtotalAfterDiscount + vatAmount;
    return { subtotal, discountAmount, vatAmount, total };
  };

// ============== NEW TAB COMPONENTS ==============

  const handleOpenDialog = (invoice?: Invoice) => {
    // Determine the invoice type - default based on current tab, or from invoice
    const defaultType = invoiceType;
    
    if (invoice) {
      // READONLY check: paid, cancelled, corrected, converted invoices cannot be edited
      const readonlyStatuses = ['paid', 'cancelled', 'corrected', 'converted'];
      if (readonlyStatuses.includes(invoice.status)) {
        showError(`Фактура с статус '${invoice.status}' е в READONLY режим и не може да се редактира.`);
        return;
      }
      
      setEditingInvoice(invoice);
      // Handle proforma type - set type to outgoing by default
      const invoiceDataType = invoice.type === 'proforma' ? 'outgoing' : invoice.type;
      setFormData({
        type: invoiceDataType,
        documentType: invoice.documentType || 'ФАКТУРА',
        griff: invoice.griff || 'ОРИГИНАЛ',
        description: invoice.description || '',
        date: invoice.date.split('T')[0],
        supplierId: invoice.supplier?.id || null,
        clientName: invoice.clientName || '',
        clientEik: invoice.clientEik || '',
        clientAddress: invoice.clientAddress || '',
        discountPercent: Number(invoice.discountPercent) || 0,
        vatRate: Number(invoice.vatRate) || 20,
        paymentMethod: invoice.paymentMethod || '',
        deliveryMethod: invoice.deliveryMethod || '',
        dueDate: invoice.dueDate?.split('T')[0] || '',
        paymentDate: invoice.paymentDate?.split('T')[0] || '',
        status: invoice.status || 'draft',
        notes: invoice.notes || '',
        items: invoice.items || [],
      });
    } else {
      setEditingInvoice(null);
      const isProforma = activeTab === 'proforma';
      setFormData({
        type: isProforma ? 'proforma' : invoiceType,
        documentType: isProforma ? 'ПРОФОРМА' : 'ФАКТУРА',
        griff: 'ОРИГИНАЛ',
        description: '',
        date: new Date().toISOString().split('T')[0],
        supplierId: null,
        clientName: '',
        clientEik: '',
        clientAddress: '',
        discountPercent: 0,
        vatRate: 20,
        paymentMethod: '',
        deliveryMethod: '',
        dueDate: '',
        paymentDate: '',
        status: 'draft',
        notes: '',
        items: [],
      });
    }
    setErrors({});
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingInvoice(null);
  };

  const handleAddItem = () => {
    setFormData({
      ...formData,
      items: [
        ...formData.items,
        { name: '', quantity: 1, unit: 'br', unitPrice: 0, unitPriceWithVat: null, batchNumber: '', expirationDate: '', discountPercent: 0 },
      ],
    });
  };

  const handleRemoveItem = (index: number) => {
    const newItems = [...formData.items];
    newItems.splice(index, 1);
    const newBatches = { ...itemBatches };
    delete newBatches[index];
    setItemBatches(newBatches);
    setFormData({ ...formData, items: newItems });
  };

  const loadBatchesForIngredient = (ingredientId: number, itemIndex: number) => {
    if (!ingredientId) return;
    setLoadingBatchItemIndex(itemIndex);
    loadIngredientBatches({ variables: { ingredientId } }).catch((err: unknown) => {
      console.error('Грешка при зареждане на партиди:', getErrorMessage(err));
    });
  };

  const handleItemChange = (index: number, field: keyof InvoiceItem, value: string | number | null) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };

    if (field === 'ingredientId' && value) {
      const ingredient = ingredientsData?.ingredients?.find((i: Ingredient) => i.id === value);
      if (ingredient) {
        newItems[index].name = ingredient.name;
        newItems[index].unit = ingredient.unit;
        newItems[index].unitPrice = Number(ingredient.currentPrice) || 0;
        newItems[index].unitPriceWithVat = Number(ingredient.currentPrice) ? Number(ingredient.currentPrice) * 1.20 : null;
        newItems[index].batchId = null;
        newItems[index].batch = null;
        loadBatchesForIngredient(Number(value), index);
      }
    }

    if (field === 'batchId' && value) {
      const batches = itemBatches[index];
      if (batches) {
        const selectedBatch = batches.find(b => b.id === Number(value));
        if (selectedBatch) {
          newItems[index].batch = selectedBatch;
          newItems[index].batchNumber = selectedBatch.batchNumber;
          newItems[index].expirationDate = selectedBatch.expiryDate;
        }
      }
    }

    if (field === 'unitPrice' && value) {
      const priceWithoutVat = typeof value === 'string' ? parseFloat(value) || 0 : value;
      newItems[index].unitPriceWithVat = Number(priceWithoutVat) * (1 + formData.vatRate / 100);
    }

    if (field === 'unitPriceWithVat' && value) {
      const priceWithVat = typeof value === 'string' ? parseFloat(value) || 0 : value;
      newItems[index].unitPrice = Number(priceWithVat) / (1 + formData.vatRate / 100);
    }

    setFormData({ ...formData, items: newItems });
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.date) {
      newErrors.date = 'Датата е задължителна';
    }
    
    if (formData.type === 'incoming' && !formData.supplierId) {
      newErrors.supplierId = 'Доставчикът е задължителен';
    }
    
    if (formData.type === 'outgoing') {
      if (!formData.clientName) {
        newErrors.clientName = 'Името на клиента е задължително';
      }
      if (!formData.clientEik) {
        newErrors.clientEik = 'ЕИК е задължителен';
      }
    }
    
    if (formData.items.length === 0) {
      newErrors.items = 'Трябва да добавите поне един артикул';
    }
    
    formData.items.forEach((item, index) => {
      if (!item.name && !item.ingredientId) {
        newErrors[`item_${index}`] = 'Артикулът е задължителен';
      }
      if (item.quantity <= 0) {
        newErrors[`quantity_${index}`] = 'Количеството трябва да е по-голямо от 0';
      }
      if (item.unitPrice < 0) {
        newErrors[`price_${index}`] = 'Цената не може да е отрицателна';
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }
    
    // Warning when cancelling a paid invoice
    if (editingInvoice && editingInvoice.status === 'paid' && formData.status === 'cancelled') {
      const confirmed = window.confirm(
        '⚠️ ВНИМАНИЕ!\n\n' +
        'Вие анулирате платена фактура!\n\n' +
        'Тази фактура има свързани записи в:\n' +
        '• Касовата книга\n' +
        '• Счетоводните записи\n\n' +
        'Моля, анулирайте ги ръчно преди да продължите.\n\n' +
        'Желаете ли да продължите?'
      );
      if (!confirmed) {
        return;
      }
    }
    
    try {
      const invoiceData = {
        type: formData.type,
        documentType: formData.documentType,
        griff: formData.griff,
        description: formData.description,
        date: formData.date,
        supplierId: formData.supplierId,
        batchId: null,
        clientName: formData.clientName || null,
        clientEik: formData.clientEik || null,
        clientAddress: formData.clientAddress || null,
        discountPercent: formData.discountPercent,
        vatRate: formData.vatRate,
        paymentMethod: formData.paymentMethod || null,
        deliveryMethod: formData.deliveryMethod || null,
        dueDate: formData.dueDate || null,
        paymentDate: formData.paymentDate || null,
        status: formData.status,
        notes: formData.notes || null,
        companyId: 1,
        items: formData.items.map(item => ({
          ingredientId: item.ingredientId,
          batchId: item.batchId,
          batchNumber: item.batchNumber || null,
          expirationDate: item.expirationDate || null,
          name: item.name,
          quantity: item.quantity,
          unit: item.unit,
          unitPrice: item.unitPrice,
          unitPriceWithVat: item.unitPriceWithVat,
          discountPercent: item.discountPercent,
        })),
      };

      if (editingInvoice) {
        await updateInvoice({ variables: { id: editingInvoice.id, invoiceData } });
      } else if (formData.type === 'proforma') {
        await createProformaInvoice({
          variables: {
            clientName: formData.clientName,
            clientEik: formData.clientEik || null,
            clientAddress: formData.clientAddress || null,
            date: formData.date,
            items: formData.items.map(item => ({
              name: item.name,
              quantity: item.quantity,
              unit: item.unit,
              unitPrice: item.unitPrice,
              unitPriceWithVat: item.unitPriceWithVat,
              batchNumber: item.batchNumber || null,
              expirationDate: item.expirationDate || null,
              discountPercent: item.discountPercent || 0,
            })),
            vatRate: formData.vatRate,
            discountPercent: formData.discountPercent,
            notes: formData.notes || null,
          },
        });
      } else {
        await createInvoice({ variables: { invoiceData } });
      }

      handleCloseDialog();
      // Refresh both regular invoices and proforma invoices
      refetch();
      // Also refresh proforma invoices if we created one
      if (formData.type === 'proforma') {
        // The proforma query should be refetched automatically via cache
      }
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async (id: number) => {
    // DELETION IS ALWAYS BLOCKED - Show message
    showError('Създадена фактура не може да се изтрие. Може само да се анулира.');
  };

  const { subtotal, discountAmount, vatAmount, total } = calculateTotals();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ width: '100%', mb: 2, p: 2 }}>
        {activeTab === 'incoming' && (
          <InvoiceList
            invoiceType="incoming"
            onAdd={() => handleOpenDialog()}
            onEdit={(inv) => handleOpenDialog(inv as Parameters<typeof handleOpenDialog>[0])}
            onView={(inv) => handleOpenDetailsDialog(inv as Parameters<typeof handleOpenDetailsDialog>[0])}
            onPrint={handlePrintInvoice}
            onDelete={(inv) => handleDelete((inv as { id: number }).id)}
          />
        )}
        {activeTab === 'outgoing' && (
          <InvoiceList
            invoiceType="outgoing"
            onAdd={() => handleOpenDialog()}
            onEdit={(inv) => handleOpenDialog(inv as Parameters<typeof handleOpenDialog>[0])}
            onView={(inv) => handleOpenDetailsDialog(inv as Parameters<typeof handleOpenDetailsDialog>[0])}
            onPrint={handlePrintInvoice}
            onDelete={(inv) => handleDelete((inv as { id: number }).id)}
          />
        )}
        {activeTab === 'cash-journal' && <CashJournalTab />}
        {activeTab === 'operations' && <OperationLogsTab />}
        {activeTab === 'daily' && <DailySummaryTab />}
        {activeTab === 'monthly' && <MonthlyReportTab />}
        {activeTab === 'yearly' && <YearlyReportTab />}
        {activeTab === 'proforma' && <ProformaTab handleOpenDialog={handleOpenDialog as (invoice?: unknown) => void} />}
        {activeTab === 'corrections' && <CorrectionsTab />}
        {activeTab === 'bank' && <BankTab />}
        {activeTab === 'accounts' && <AccountsTab />}
        {activeTab === 'vat' && <VATTab />}
        {activeTab === 'saft' && <SAFTTab />}
        {activeTab === 'accounting-entries' && <AccountingEntriesTab />}
      </Paper>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingInvoice 
            ? (editingInvoice.type === 'proforma' ? 'Редактирай проформа' : 'Редактирай фактура') 
            : (formData.documentType === 'ПРОФОРМА' ? 'Нова проформа' : 'Нова фактура')}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <FormControl fullWidth>
                <InputLabel>Тип документ</InputLabel>
                <Select value={formData.documentType} label="Тип документ" onChange={(e) => setFormData({...formData, documentType: e.target.value})}>
                  <MenuItem value="ФАКТУРА">ФАКТУРА</MenuItem>
                  <MenuItem value="ПРОФОРМА">ПРОФОРМА</MenuItem>
                  <MenuItem value="КОРЕКЦИЯ">КОРЕКЦИЯ</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <FormControl fullWidth>
                <InputLabel>Гриф</InputLabel>
                <Select value={formData.griff} label="Гриф" onChange={(e) => setFormData({...formData, griff: e.target.value})}>
                  <MenuItem value="ОРИГИНАЛ">ОРИГИНАЛ</MenuItem>
                  <MenuItem value="КОПИЕ">КОПИЕ</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <ValidatedTextField
                label="Дата"
                type="date"
                value={formData.date}
                onChange={(value) => setFormData({...formData, date: value})}
                tooltip="Дата на издаване на фактурата"
                required
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ValidatedTextField
                label="Основание за сделката"
                value={formData.description}
                onChange={(value) => setFormData({...formData, description: value})}
                tooltip="Описание на стоката/услугата"
                multiline
                rows={2}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Начин на плащане</InputLabel>
                <Select value={formData.paymentMethod} label="Начин на плащане" onChange={(e) => setFormData({...formData, paymentMethod: e.target.value})}>
                  <MenuItem value="Банков превод">Банков превод</MenuItem>
                  <MenuItem value="В брой">В брой</MenuItem>
                  <MenuItem value="Карта">Карта</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ValidatedTextField
                label="Дата на плащане"
                type="date"
                value={formData.dueDate}
                onChange={(value) => setFormData({...formData, dueDate: value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Статус</InputLabel>
                <Select value={formData.status} label="Статус" onChange={(e) => setFormData({...formData, status: e.target.value})}>
                  <MenuItem value="draft">Чернова</MenuItem>
                  <MenuItem value="sent">Изпратена</MenuItem>
                  <MenuItem value="paid">Платена</MenuItem>
                  <MenuItem value="cancelled">Анулирана</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Доставка</InputLabel>
                <Select value={formData.deliveryMethod} label="Доставка" onChange={(e) => setFormData({...formData, deliveryMethod: e.target.value})}>
                  <MenuItem value="Доставка до адрес">Доставка до адрес</MenuItem>
                  <MenuItem value="Взимане от склад">Взимане от склад</MenuItem>
                  <MenuItem value="Куриер">Куриер</MenuItem>
                  <MenuItem value="Еконт">Еконт</MenuItem>
                  <MenuItem value="Спиди">Спиди</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {formData.type === 'outgoing' && (
              <>
                <Grid size={{ xs: 12 }}>
                  <ValidatedTextField
                    label="Клиент"
                    value={formData.clientName}
                    onChange={(value) => setFormData({...formData, clientName: value})}
                    tooltip="Име на клиента"
                    required
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <ValidatedTextField
                    label="ЕИК"
                    value={formData.clientEik}
                    onChange={(value) => setFormData({...formData, clientEik: value})}
                    tooltip="Единен идентификационен код (ЕИК)"
                    required
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <ValidatedTextField
                    label="Адрес"
                    value={formData.clientAddress}
                    onChange={(value) => setFormData({...formData, clientAddress: value})}
                    tooltip="Адрес на клиента"
                  />
                </Grid>
              </>
            )}
            {formData.type === 'incoming' && (
              <Grid size={{ xs: 12 }}>
                <FormControl fullWidth>
                  <InputLabel>Доставчик</InputLabel>
                  <Select value={formData.supplierId || ''} label="Доставчик" onChange={(e) => setFormData({...formData, supplierId: e.target.value as number})}>
                    {suppliersData?.suppliers?.map((s: Supplier) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
            )}
            <Grid size={{ xs: 12, sm: 6 }}>
              <ValidatedTextField
                label="ДДС %"
                type="number"
                value={formData.vatRate}
                onChange={(value) => setFormData({...formData, vatRate: parseFloat(value) || 0})}
                tooltip="Данък добавена стойност в проценти"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ValidatedTextField
                label="Отстъпка %"
                type="number"
                value={formData.discountPercent}
                onChange={(value) => setFormData({...formData, discountPercent: parseFloat(value) || 0})}
                tooltip="Отстъпка в проценти"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Box sx={{ mt: 1, p: 2, bgcolor: 'primary.light', color: 'primary.contrastText', borderRadius: 1 }}>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Typography variant="caption" display="block">Сума без ДДС</Typography>
                    <Typography variant="h6">{formatPrice(subtotal)}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Typography variant="caption" display="block">Отстъпка</Typography>
                    <Typography variant="h6">{formatPrice(discountAmount)}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Typography variant="caption" display="block">ДДС ({formData.vatRate}%)</Typography>
                    <Typography variant="h6">{formatPrice(vatAmount)}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Typography variant="caption" display="block">ОБЩО</Typography>
                    <Typography variant="h5" fontWeight="bold">{formatPrice(total)}</Typography>
                  </Grid>
                </Grid>
              </Box>
            </Grid>

            {/* Артикули */}
            <Grid size={{ xs: 12 }}>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Артикули</Typography>
                  <Button size="small" startIcon={<AddIcon />} onClick={handleAddItem}>Добави артикул</Button>
                </Box>
                
                {errors.items && <Alert severity="error" sx={{ mb: 2 }}>{errors.items}</Alert>}
                
                {formData.items.map((item, index) => {
                  const batchesForItem = itemBatches[index] || [];
                  return (
                  <Paper key={index} sx={{ p: 2, mb: 2 }}>
                    <Grid container spacing={2} alignItems="center">
                      <Grid size={{ xs: 12, sm: 3 }}>
                        {editingInvoice ? (
                          <TextField
                            fullWidth
                            size="small"
                            label="Артикул"
                            value={item.name || '-'}
                            disabled
                            InputProps={{ readOnly: true }}
                          />
                        ) : (
                          <FormControl fullWidth size="small">
                            <InputLabel>Артикул</InputLabel>
                            <Select
                              value={item.ingredientId || ''}
                              label="Артикул"
                              onChange={(e) => handleItemChange(index, 'ingredientId', e.target.value)}
                              error={!!errors[`item_${index}`]}
                            >
                              {ingredientsData?.ingredients?.map((ing: Ingredient) => (
                                <MenuItem key={ing.id} value={ing.id}>
                                  {ing.name} ({ing.unit})
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        )}
                      </Grid>
                      {formData.type === 'incoming' && item.ingredientId && (
                        <Grid size={{ xs: 12, sm: 3 }}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Партида (наличност)</InputLabel>
                            <Select
                              value={item.batchId || ''}
                              label="Партида (наличност)"
                              onChange={(e) => handleItemChange(index, 'batchId', e.target.value)}
                            >
                              <MenuItem value="">
                                <em>Без партида</em>
                              </MenuItem>
                              {batchesForItem.map((batch) => (
                                <MenuItem key={batch.id} value={batch.id}>
                                  {batch.batchNumber || `Партида #${batch.id}`} - 
                                  {batch.availableStock?.toFixed(3)} бр. - 
                                  до {batch.expiryDate ? formatDate(batch.expiryDate) : '-'}
                                  {batch.supplier ? ` (${batch.supplier.name})` : ''}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                          {batchesForItem.length > 0 && (
                            <Typography variant="caption" color="info.main" sx={{ mt: 0.5, display: 'block' }}>
                              Наличност: {batchesForItem.reduce((sum, b) => sum + (b.availableStock || 0), 0).toFixed(3)} {item.unit}
                            </Typography>
                          )}
                        </Grid>
                      )}
                      <Grid size={{ xs: 6, sm: 2 }}>
                        <TextField
                          fullWidth
                          size="small"
                          label="К-во"
                          type="number"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, 'quantity', parseFloat(e.target.value) || 0)}
                          error={!!errors[`quantity_${index}`]}
                          helperText={errors[`quantity_${index}`]}
                        />
                      </Grid>
                      <Grid size={{ xs: 6, sm: 1 }}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Мярка"
                          value={item.unit}
                          onChange={(e) => handleItemChange(index, 'unit', e.target.value)}
                        />
                      </Grid>
                      <Grid size={{ xs: 6, sm: 2 }}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Цена без ДДС"
                          type="number"
                          value={item.unitPrice}
                          onChange={(e) => handleItemChange(index, 'unitPrice', e.target.value)}
                          error={!!errors[`price_${index}`]}
                          helperText={errors[`price_${index}`]}
                        />
                      </Grid>
                      <Grid size={{ xs: 6, sm: 2 }}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Цена със ДДС"
                          type="number"
                          value={item.unitPriceWithVat || ''}
                          onChange={(e) => handleItemChange(index, 'unitPriceWithVat', e.target.value)}
                        />
                      </Grid>
                      <Grid size={{ xs: 6, sm: 1 }}>
                        <IconButton color="error" onClick={() => handleRemoveItem(index)}>
                          <DeleteIcon />
                        </IconButton>
                      </Grid>
                    </Grid>
                    {item.batch && (
                      <Chip 
                        size="small" 
                        label={`Партида: ${item.batch.batchNumber || '#'+item.batch.id} | 
                          ${item.batch.availableStock?.toFixed(3)} ${item.unit} | 
                          до ${item.batch.expiryDate ? formatDate(item.batch.expiryDate) : '-'}`}
                        sx={{ mt: 1 }}
                        color="success"
                        variant="outlined"
                      />
                    )}
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      Общо: {formatPrice(item.quantity * item.unitPrice)} (със ДДС: {formatPrice(item.quantity * (item.unitPriceWithVat || item.unitPrice * 1.2))})
                    </Typography>
                  </Paper>
                );
                })}
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Отказ</Button>
          <Button onClick={handleSave} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Детайли на фактура */}
      <Dialog open={detailsDialogOpen} onClose={handleCloseDetailsDialog} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" fontWeight="bold">ФАКТУРА</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {selectedInvoice && (
              <Button
                variant="contained"
                size="small"
                startIcon={<PrintIcon />}
                onClick={() => handlePrintInvoice(selectedInvoice.id)}
              >
                Принт
              </Button>
            )}
            <IconButton onClick={handleCloseDetailsDialog} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedInvoice && (
            <Grid container spacing={2}>
              {/* Издател и Получател */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>ИЗДАТЕЛ</Typography>
                  {selectedInvoice.type === 'incoming' && selectedInvoice.supplier ? (
                    <>
                      <Typography variant="body2">{selectedInvoice.supplier.name}</Typography>
                      <Typography variant="body2">ЕИК: {(selectedInvoice.supplier as any)?.eik || '-'}</Typography>
                      <Typography variant="body2">ИН по ЗДДС: {(selectedInvoice.supplier as any)?.vatNumber || '-'}</Typography>
                    </>
                  ) : selectedInvoice.company ? (
                    <>
                      <Typography variant="body2">{selectedInvoice.company.name}</Typography>
                      <Typography variant="body2">{(selectedInvoice.company as any)?.address || '-'}</Typography>
                      <Typography variant="body2">ЕИК: {(selectedInvoice.company as any)?.eik || '-'}</Typography>
                      <Typography variant="body2">ИН по ЗДДС: {(selectedInvoice.company as any)?.vatNumber || '-'}</Typography>
                    </>
                  ) : (
                    <Typography variant="body2">-</Typography>
                  )}
                </Box>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>ПОЛУЧАТЕЛ</Typography>
                  {selectedInvoice.type === 'incoming' && selectedInvoice.company ? (
                    <>
                      <Typography variant="body2">{selectedInvoice.company.name}</Typography>
                      <Typography variant="body2">{(selectedInvoice.company as any)?.address || '-'}</Typography>
                      <Typography variant="body2">ЕИК: {(selectedInvoice.company as any)?.eik || '-'}</Typography>
                      <Typography variant="body2">ИН по ЗДДС: {(selectedInvoice.company as any)?.vatNumber || '-'}</Typography>
                    </>
                  ) : (
                    <>
                      <Typography variant="body2">{selectedInvoice.clientName || '-'}</Typography>
                      <Typography variant="body2">ЕИК: {selectedInvoice.clientEik || '-'}</Typography>
                      <Typography variant="body2">{selectedInvoice.clientAddress || '-'}</Typography>
                    </>
                  )}
                </Box>
              </Grid>

              {/* Номер и дата */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h5" fontWeight="bold">№ {selectedInvoice.number}</Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body1">Дата: {formatDate(selectedInvoice.date)}</Typography>
              </Grid>

              {/* Таблица с артикули */}
              <Grid size={{ xs: 12 }}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'grey.200' }}>
                        <TableCell>№</TableCell>
                        <TableCell>Наименование</TableCell>
                        <TableCell align="right">К-во</TableCell>
                        <TableCell>Ед.мярка</TableCell>
                        <TableCell align="right">Цена без ДДС</TableCell>
                        <TableCell align="right">Цена със ДДС</TableCell>
                        <TableCell>Партида</TableCell>
                        <TableCell>Срок годност</TableCell>
                        <TableCell align="right">ДДС %</TableCell>
                        <TableCell align="right">Сума</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedInvoice.items?.map((item: InvoiceItem, index: number) => {
                        const itemTotal = Number(item.quantity) * Number(item.unitPrice);
                        const itemDiscount = itemTotal * (Number(item.discountPercent) / 100);
                        const itemSubtotal = itemTotal - itemDiscount;
                        const itemVat = itemSubtotal * (Number(selectedInvoice.vatRate) / 100);
                        return (
                          <TableRow key={item.id || index}>
                            <TableCell>{index + 1}</TableCell>
                            <TableCell>{item.name}</TableCell>
                            <TableCell align="right">{Number(item.quantity).toFixed(3)}</TableCell>
                            <TableCell>{item.unit}</TableCell>
                            <TableCell align="right">{Number(item.unitPrice).toFixed(2)}</TableCell>
                            <TableCell align="right">{item.unitPriceWithVat ? Number(item.unitPriceWithVat).toFixed(2) : (Number(item.unitPrice) * (1 + Number(selectedInvoice.vatRate)/100)).toFixed(2)}</TableCell>
                            <TableCell>{item.batchNumber || '-'}</TableCell>
                            <TableCell>{item.expirationDate ? formatDate(item.expirationDate) : '-'}</TableCell>
                            <TableCell align="right">{Number(selectedInvoice.vatRate)}%</TableCell>
                            <TableCell align="right">{(itemSubtotal + itemVat).toFixed(2)}</TableCell>
                          </TableRow>
                        );
                      })}
                      <TableRow sx={{ bgcolor: 'grey.100', fontWeight: 'bold' }}>
                        <TableCell colSpan={7} align="right"><strong>Сума:</strong></TableCell>
                        <TableCell align="right"><strong>{Number(selectedInvoice.subtotal).toFixed(2)}</strong></TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow sx={{ bgcolor: 'grey.100' }}>
                        <TableCell colSpan={7} align="right">ДДС {Number(selectedInvoice.vatRate)}%:</TableCell>
                        <TableCell align="right">{Number(selectedInvoice.vatAmount).toFixed(2)}</TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow sx={{ bgcolor: 'grey.200', fontWeight: 'bold' }}>
                        <TableCell colSpan={7} align="right"><strong>ОБЩО:</strong></TableCell>
                        <TableCell align="right"><strong>{Number(selectedInvoice.total).toFixed(2)}</strong></TableCell>
                        <TableCell>€</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              {/* Дати и начин на плащане */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2">Дата на фактура: {formatDate(selectedInvoice.date)}</Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2">Дата на плащане: {selectedInvoice.dueDate ? formatDate(selectedInvoice.dueDate) : '-'}</Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2">Начин на плащане: {selectedInvoice.paymentMethod || '-'}</Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2">Статус: <Chip label={getInvoiceStatusText(selectedInvoice.status)} color={getInvoiceStatusColor(selectedInvoice.status)} size="small" /></Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetailsDialog}>Затвори</Button>
        </DialogActions>
      </Dialog>

    </Container>
  );
}

