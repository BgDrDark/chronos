import React, { useState, useEffect } from 'react';
import { AccountingSummary, Account, Transaction, Register, AccountingLog, Ingredient, AccountingEntry, getErrorMessage } from '../types';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
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
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  Print as PrintIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import { useQuery, useMutation, useLazyQuery, gql } from '@apollo/client';
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
  
  return (
    <Tooltip title={tooltip || ''} arrow placement="top">
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
        InputProps={{
          ...InputProps,
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
    </Tooltip>
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
  date: string;
  supplier?: { id: number; name: string; eik?: string; vatNumber?: string; address?: string } | null;
  company?: { id: number; name: string; eik?: string; vatNumber?: string; address?: string } | null;
  clientName?: string | null;
  clientEik?: string | null;
  clientAddress?: string | null;
  subtotal: number;
  discountPercent: number;
  discountAmount: number;
  vatRate: number;
  vatAmount: number;
  total: number;
  paymentMethod?: string | null;
  dueDate?: string | null;
  paymentDate?: string | null;
  status: string;
  notes?: string | null;
  items: InvoiceItem[];
  originalInvoiceId?: number | null;
  batch?: string | null;
}

interface Props {
  tab?: string;
}

const tabMap: Record<string, number> = {
  'incoming': 0,
  'outgoing': 1,
  'cash-journal': 2,
  'operations': 3,
  'daily': 4,
  'monthly': 5,
  'yearly': 6,
  'proforma': 7,
  'corrections': 8,
  'bank': 9,
  'accounts': 10,
  'vat': 11,
  'saft': 12,
  'accounting-entries': 13,
};

export default function AccountingPage({ tab }: Props) {
  const initialTab = tab ? (tabMap[tab] ?? 0) : 0;
  const [tabValue, setTabValue] = useState(initialTab);
  
  useEffect(() => {
    const newTab = tab ? (tabMap[tab] ?? 0) : 0;
    setTabValue(newTab);
  }, [tab]);
  
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

  const invoiceType = tabValue === 0 ? 'incoming' : 'outgoing';

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
      
      if (!response.ok) {
        throw new Error('Failed to load PDF');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const printWindow = window.open(url, '_blank');
      
      if (printWindow) {
        printWindow.focus();
      }
    } catch (err) {
      console.error('Error printing invoice:', err);
      alert('Грешка при принтиране на фактура');
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

// Cash Journal Tab Component
function CashJournalTab() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [operationType, setOperationType] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [cashForm, setCashForm] = useState({
    date: new Date().toISOString().split('T')[0],
    operationType: 'income',
    amount: '',
    description: '',
  });

  const { data, loading, refetch } = useQuery(GET_CASH_JOURNAL_ENTRIES, {
    variables: { startDate: startDate || undefined, endDate: endDate || undefined, operationType: operationType || undefined },
  });

  const { data: invoicesData } = useQuery(GET_INVOICES, {
    variables: { type: undefined, status: 'paid' },
  });

  const [createCashEntry] = useMutation(CREATE_CASH_JOURNAL_ENTRY);
  const [deleteCashEntry] = useMutation(DELETE_CASH_JOURNAL_ENTRY);

  const handleAddEntry = async () => {
    try {
      await createCashEntry({
        variables: {
          input: {
            date: cashForm.date,
            operationType: cashForm.operationType,
            amount: parseFloat(cashForm.amount),
            description: cashForm.description,
            referenceType: 'manual',
            companyId: 1,
          },
        },
      });
      setOpenDialog(false);
      setCashForm({ date: new Date().toISOString().split('T')[0], operationType: 'income', amount: '', description: '' });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Сигурен ли си, че искаш да изтриеш тази операция?')) {
      try {
        await deleteCashEntry({ variables: { id } });
        refetch();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const entries = data?.cashJournalEntries || [];
  const allInvoices = invoicesData?.invoices || [];
  
  // Филтриране на платените фактури
  const paidInvoices = allInvoices.filter((inv: Invoice) => inv.status === 'paid');
  const incomingInvoices = paidInvoices.filter((inv: Invoice) => inv.type === 'incoming');
  const outgoingInvoices = paidInvoices.filter((inv: Invoice) => inv.type === 'outgoing');

  // Общи суми
  // Входящи фактури = Разход (плащаме на доставчик)
  // Изходящи фактури = Приход (получаваме от клиент)
  const totalIncoming = incomingInvoices.reduce((sum: number, inv: Invoice) => sum + Number(inv.total), 0);
  const totalOutgoing = outgoingInvoices.reduce((sum: number, inv: Invoice) => sum + Number(inv.total), 0);

  return (
    <Box>
      {/* Обобщение на фактурите */}
      <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Фактури (платени)</Typography>
        <Box sx={{ display: 'flex', gap: 4 }}>
          <Box sx={{ p: 2, bgcolor: '#ffebee', borderRadius: 1, flex: 1 }}>
            <Typography variant="subtitle2">Входящи фактури (Разход)</Typography>
            <Typography variant="h5" color="error.main">{totalIncoming.toFixed(2)} лв.</Typography>
            <Typography variant="body2" color="text.secondary">{incomingInvoices.length} бр.</Typography>
          </Box>
          <Box sx={{ p: 2, bgcolor: '#e8f5e9', borderRadius: 1, flex: 1 }}>
            <Typography variant="subtitle2">Изходящи фактури (Приход)</Typography>
            <Typography variant="h5" color="success.main">{totalOutgoing.toFixed(2)} лв.</Typography>
            <Typography variant="body2" color="text.secondary">{outgoingInvoices.length} бр.</Typography>
          </Box>
        </Box>
      </Box>

      {/* Детайли входящи фактури */}
      {incomingInvoices.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Входящи фактури (Разход)</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#ffebee' }}>
                  <TableCell>№</TableCell>
                  <TableCell>дата</TableCell>
                  <TableCell>Доставчик</TableCell>
                  <TableCell>Сума</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {incomingInvoices.map((inv: Invoice) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.number}</TableCell>
                    <TableCell>{new Date(inv.date).toLocaleDateString('bg-BG')}</TableCell>
                    <TableCell>{inv.supplier?.name || '-'}</TableCell>
                    <TableCell align="right" sx={{ color: 'error.main' }}>{Number(inv.total).toFixed(2)} лв.</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Детайли изходящи фактури */}
      {outgoingInvoices.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Изходящи фактури (Приход)</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                  <TableCell>№</TableCell>
                  <TableCell>дата</TableCell>
                  <TableCell>Клиент</TableCell>
                  <TableCell>Сума</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {outgoingInvoices.map((inv: Invoice) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.number}</TableCell>
                    <TableCell>{new Date(inv.date).toLocaleDateString('bg-BG')}</TableCell>
                    <TableCell>{inv.clientName || '-'}</TableCell>
                    <TableCell align="right" sx={{ color: 'success.main' }}>{Number(inv.total).toFixed(2)} лв.</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Детайли изходящи фактури */}
      {outgoingInvoices.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Изходящи фактури (Разход)</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#ffebee' }}>
                  <TableCell>№</TableCell>
                  <TableCell>Дата</TableCell>
                  <TableCell>Клиент</TableCell>
                  <TableCell>Сума</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {outgoingInvoices.map((inv: Invoice) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.number}</TableCell>
                    <TableCell>{new Date(inv.date).toLocaleDateString('bg-BG')}</TableCell>
                    <TableCell>{inv.clientName || '-'}</TableCell>
                    <TableCell align="right" sx={{ color: 'error.main' }}>{Number(inv.total).toFixed(2)} лв.</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            size="small"
            label="От дата"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            size="small"
            label="До дата"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <Select
            size="small"
            value={operationType}
            onChange={(e) => setOperationType(e.target.value)}
            displayEmpty
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">Всички типове</MenuItem>
            <MenuItem value="income">Приход</MenuItem>
            <MenuItem value="expense">Разход</MenuItem>
          </Select>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenDialog(true)}>
          Добави операция
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>Описание</TableCell>
                <TableCell>Създал</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((entry: CashJournalEntry) => (
                <TableRow key={entry.id} sx={{ backgroundColor: entry.operationType === 'income' ? '#e8f5e9' : '#ffebee' }}>
                  <TableCell>{new Date(entry.date).toLocaleDateString('bg-BG')}</TableCell>
                  <TableCell>
                    <Chip label={entry.operationType === 'income' ? 'Приход' : 'Разход'} color={entry.operationType === 'income' ? 'success' : 'error'} size="small" />
                  </TableCell>
                  <TableCell align="right">{Number(entry.amount).toFixed(2)} лв.</TableCell>
                  <TableCell>{entry.description}</TableCell>
                  <TableCell>{entry.creator?.firstName} {entry.creator?.lastName}</TableCell>
                  <TableCell>
                    <IconButton size="small" color="error" onClick={() => handleDelete(entry.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова касова операция</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ValidatedTextField
                label="Дата"
                type="date"
                value={cashForm.date}
                onChange={(value) => setCashForm({ ...cashForm, date: value })}
                tooltip="Дата на операцията"
                required
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Тип</InputLabel>
                <Select
                  value={cashForm.operationType}
                  label="Тип"
                  onChange={(e) => setCashForm(() => ({ ...cashForm, operationType: e.target.value as string }))}
                >
                  <MenuItem value="income">Приход</MenuItem>
                  <MenuItem value="expense">Разход</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ValidatedTextField
                label="Сума"
                type="number"
                value={cashForm.amount}
                onChange={(value) => setCashForm({ ...cashForm, amount: value })}
                tooltip="Сума в лева"
                required
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ValidatedTextField
                label="Описание"
                multiline
                rows={2}
                value={cashForm.description}
                onChange={(value) => setCashForm({ ...cashForm, description: value })}
                tooltip="Описание на операцията"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Отказ</Button>
          <Button onClick={handleAddEntry} variant="contained" disabled={!cashForm.amount}>Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// Operation Logs Tab Component
function OperationLogsTab() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [operation, setOperation] = useState('');
  const [entityType, setEntityType] = useState('');

  const { data, loading } = useQuery(GET_OPERATION_LOGS, {
    variables: { startDate: startDate || undefined, endDate: endDate || undefined, operation: operation || undefined, entityType: entityType || undefined },
  });

  const logs = data?.operationLogs || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField size="small" label="От дата" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" label="До дата" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} InputLabelProps={{ shrink: true }} />
        <Select size="small" value={operation} onChange={(e) => setOperation(e.target.value)} displayEmpty sx={{ minWidth: 120 }}>
          <MenuItem value="">Всички</MenuItem>
          <MenuItem value="create">Създаване</MenuItem>
          <MenuItem value="update">Промяна</MenuItem>
          <MenuItem value="delete">Изтриване</MenuItem>
        </Select>
        <Select size="small" value={entityType} onChange={(e) => setEntityType(e.target.value)} displayEmpty sx={{ minWidth: 150 }}>
          <MenuItem value="">Всички обекти</MenuItem>
          <MenuItem value="invoice">Фактура</MenuItem>
          <MenuItem value="cash_journal">Касов дневник</MenuItem>
        </Select>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата/Час</TableCell>
                <TableCell>Операция</TableCell>
                <TableCell>Обект</TableCell>
                <TableCell>ID</TableCell>
                <TableCell>Потребител</TableCell>
                <TableCell>Промени</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log: AccountingLog) => (
                <TableRow key={log.id}>
                  <TableCell>{new Date(log.timestamp).toLocaleString('bg-BG')}</TableCell>
                  <TableCell>
                    <Chip label={log.operation === 'create' ? 'Създадено' : log.operation === 'update' ? 'Променено' : 'Изтрито'} color={log.operation === 'create' ? 'success' : log.operation === 'update' ? 'warning' : 'error'} size="small" />
                  </TableCell>
                  <TableCell>{log.entityType}</TableCell>
                  <TableCell>{log.entityId}</TableCell>
                  <TableCell>{typeof log.user === 'object' ? `${log.user.firstName || ''} ${log.user.lastName || ''}` : log.user}</TableCell>
                  <TableCell><pre style={{ fontSize: 11, margin: 0 }}>{JSON.stringify(log.changes, null, 2)}</pre></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

// Daily Summary Tab Component
function DailySummaryTab() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [generateDate, setGenerateDate] = useState(new Date().toISOString().split('T')[0]);
  const [generating, setGenerating] = useState(false);

  const { data, loading, refetch } = useQuery(GET_DAILY_SUMMARIES, {
    variables: { startDate: startDate || undefined, endDate: endDate || undefined },
  });

  const [generateDailySummary] = useMutation(GENERATE_DAILY_SUMMARY);

  const summaries = data?.dailySummaries || [];

  const handleGenerate = async () => {
    if (!generateDate) return;
    setGenerating(true);
    try {
      await generateDailySummary({ variables: { date: generateDate } });
      refetch();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField size="small" label="От дата" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" label="До дата" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} InputLabelProps={{ shrink: true }} />
        <Box sx={{ flexGrow: 1 }} />
        <TextField size="small" label="Генерирай за дата" type="date" value={generateDate} onChange={(e) => setGenerateDate(e.target.value)} InputLabelProps={{ shrink: true }} />
        <Button variant="contained" color="primary" onClick={handleGenerate} disabled={generating} startIcon={generating ? <CircularProgress size={16} color="inherit" /> : null}>
          Генерирай
        </Button>
      </Box>

      {loading ? <CircularProgress /> : summaries.length === 0 ? (
        <Alert severity="info">Няма данни за избрания период</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell align="right">Брой фактури</TableCell>
                <TableCell align="right">Обща сума</TableCell>
                <TableCell align="right">Приход (каса)</TableCell>
                <TableCell align="right">Разход (каса)</TableCell>
                <TableCell align="right">Баланс</TableCell>
                <TableCell align="right">ДДС събран</TableCell>
                <TableCell align="right">ДДС платен</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summaries.map((summary: AccountingSummary) => (
                <TableRow key={summary.id}>
                  <TableCell>{summary.date ? new Date(summary.date).toLocaleDateString('bg-BG') : '-'}</TableCell>
                  <TableCell align="right">{summary.invoicesCount}</TableCell>
                  <TableCell align="right">{(summary.invoicesTotal ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ color: 'success.main' }}>+{(summary.cashIncome ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ color: 'error.main' }}>-{(summary.cashExpense ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold', color: (summary.cashBalance ?? 0) >= 0 ? 'success.main' : 'error.main' }}>{(summary.cashBalance ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{(summary.vatCollected ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{summary.vatPaid.toFixed(2)} лв.</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

function MonthlyReportTab() {
  const currentYear = new Date().getFullYear();
  const [startYear, setStartYear] = useState(currentYear.toString());
  const [endYear, setEndYear] = useState(currentYear.toString());
  const [generateYear, setGenerateYear] = useState(currentYear.toString());
  const [generateMonth, setGenerateMonth] = useState((new Date().getMonth() + 1).toString());
  const [generating, setGenerating] = useState(false);

  const { data, loading, refetch } = useQuery(GET_MONTHLY_SUMMARIES, {
    variables: { startYear: startYear ? parseInt(startYear) : undefined, endYear: endYear ? parseInt(endYear) : undefined },
  });

  const [generateMonthlySummary] = useMutation(GENERATE_MONTHLY_SUMMARY);

  const summaries = data?.monthlySummaries || [];

  const handleGenerate = async () => {
    if (!generateYear || !generateMonth) return;
    setGenerating(true);
    try {
      await generateMonthlySummary({ variables: { year: parseInt(generateYear), month: parseInt(generateMonth) } });
      refetch();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const monthNames = ['Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни', 'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'];

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField size="small" label="От година" type="number" value={startYear} onChange={(e) => setStartYear(e.target.value)} sx={{ width: 120 }} />
        <TextField size="small" label="До година" type="number" value={endYear} onChange={(e) => setEndYear(e.target.value)} sx={{ width: 120 }} />
        <Box sx={{ flexGrow: 1 }} />
        <TextField size="small" label="Генерирай за година" type="number" value={generateYear} onChange={(e) => setGenerateYear(e.target.value)} sx={{ width: 120 }} />
        <TextField size="small" label="Месец" type="number" value={generateMonth} onChange={(e) => setGenerateMonth(e.target.value)} inputProps={{ min: 1, max: 12 }} sx={{ width: 100 }} />
        <Button variant="contained" color="primary" onClick={handleGenerate} disabled={generating} startIcon={generating ? <CircularProgress size={16} color="inherit" /> : null}>
          Генерирай
        </Button>
      </Box>

      {loading ? <CircularProgress /> : summaries.length === 0 ? (
        <Alert severity="info">Няма данни за избрания период</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Период</TableCell>
                <TableCell align="right">Брой фактури</TableCell>
                <TableCell align="right">Входящи</TableCell>
                <TableCell align="right">Изходящи</TableCell>
                <TableCell align="right">Обща сума</TableCell>
                <TableCell align="right">Приход (каса)</TableCell>
                <TableCell align="right">Разход (каса)</TableCell>
                <TableCell align="right">Баланс</TableCell>
                <TableCell align="right">ДДС събран</TableCell>
                <TableCell align="right">ДДС платен</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summaries.map((summary: AccountingSummary) => (
                <TableRow key={summary.id}>
                  <TableCell>{summary.month ? monthNames[summary.month - 1] : '-'} {summary.year}</TableCell>
                  <TableCell align="right">{summary.invoicesCount}</TableCell>
                  <TableCell align="right">{summary.incomingInvoicesCount}</TableCell>
                  <TableCell align="right">{summary.outgoingInvoicesCount}</TableCell>
                  <TableCell align="right">{(summary.invoicesTotal ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ color: 'success.main' }}>+{(summary.cashIncome ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ color: 'error.main' }}>-{(summary.cashExpense ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold', color: (summary.cashBalance ?? 0) >= 0 ? 'success.main' : 'error.main' }}>{(summary.cashBalance ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{(summary.vatCollected ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{(summary.vatPaid ?? 0).toFixed(2)} лв.</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

function YearlyReportTab() {
  const currentYear = new Date().getFullYear();
  const [startYear, setStartYear] = useState(currentYear.toString());
  const [endYear, setEndYear] = useState(currentYear.toString());
  const [generateYear, setGenerateYear] = useState(currentYear.toString());
  const [generating, setGenerating] = useState(false);

  const { data, loading, refetch } = useQuery(GET_YEARLY_SUMMARIES, {
    variables: { startYear: startYear ? parseInt(startYear) : undefined, endYear: endYear ? parseInt(endYear) : undefined },
  });

  const [generateYearlySummary] = useMutation(GENERATE_YEARLY_SUMMARY);

  const summaries = data?.yearlySummaries || [];

  const handleGenerate = async () => {
    if (!generateYear) return;
    setGenerating(true);
    try {
      await generateYearlySummary({ variables: { year: parseInt(generateYear) } });
      refetch();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField size="small" label="От година" type="number" value={startYear} onChange={(e) => setStartYear(e.target.value)} sx={{ width: 120 }} />
        <TextField size="small" label="До година" type="number" value={endYear} onChange={(e) => setEndYear(e.target.value)} sx={{ width: 120 }} />
        <Box sx={{ flexGrow: 1 }} />
        <TextField size="small" label="Генерирай за година" type="number" value={generateYear} onChange={(e) => setGenerateYear(e.target.value)} sx={{ width: 120 }} />
        <Button variant="contained" color="primary" onClick={handleGenerate} disabled={generating} startIcon={generating ? <CircularProgress size={16} color="inherit" /> : null}>
          Генерирай
        </Button>
      </Box>

      {loading ? <CircularProgress /> : summaries.length === 0 ? (
        <Alert severity="info">Няма данни за избрания период</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Година</TableCell>
                <TableCell align="right">Брой фактури</TableCell>
                <TableCell align="right">Входящи</TableCell>
                <TableCell align="right">Изходящи</TableCell>
                <TableCell align="right">Обща сума</TableCell>
                <TableCell align="right">Приход (каса)</TableCell>
                <TableCell align="right">Разход (каса)</TableCell>
                <TableCell align="right">Баланс</TableCell>
                <TableCell align="right">ДДС събран</TableCell>
                <TableCell align="right">ДДС платен</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summaries.map((summary: AccountingSummary) => (
                <TableRow key={summary.id}>
                  <TableCell sx={{ fontWeight: 'bold' }}>{summary.year}</TableCell>
                  <TableCell align="right">{summary.invoicesCount}</TableCell>
                  <TableCell align="right">{summary.incomingInvoicesCount}</TableCell>
                  <TableCell align="right">{summary.outgoingInvoicesCount}</TableCell>
                  <TableCell align="right">{(summary.invoicesTotal ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ color: 'success.main' }}>+{(summary.cashIncome ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ color: 'error.main' }}>-{(summary.cashExpense ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold', color: (summary.cashBalance ?? 0) >= 0 ? 'success.main' : 'error.main' }}>{(summary.cashBalance ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{(summary.vatCollected ?? 0).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{(summary.vatPaid ?? 0).toFixed(2)} лв.</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

// ============== NEW TAB COMPONENTS ==============

// Proforma Invoices Tab
function ProformaTab() {
  const [search, setSearch] = useState('');
  
  const { data, loading } = useQuery(GET_PROFORMA_INVOICES, {
    variables: { search: search || undefined },
  });

  const proformas = data?.proformaInvoices || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <TextField
          size="small"
          label="Търси"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ width: 300 }}
        />
        <Button variant="contained" startIcon={<AddIcon />}>
          Нова проформа
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Номер</TableCell>
                <TableCell>Дата</TableCell>
                <TableCell>Клиент</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>ДДС</TableCell>
                <TableCell>Статус</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {proformas.map((inv: Invoice) => (
                <TableRow key={inv.id}>
                  <TableCell>{inv.number}</TableCell>
                  <TableCell>{new Date(inv.date).toLocaleDateString('bg-BG')}</TableCell>
                  <TableCell>{inv.clientName}</TableCell>
                  <TableCell align="right">{Number(inv.total).toFixed(2)} лв.</TableCell>
                  <TableCell>{inv.vatRate}%</TableCell>
                  <TableCell>
                    <Chip label={getInvoiceStatusText(inv.status)} color={getInvoiceStatusColor(inv.status)} size="small" />
                  </TableCell>
                </TableRow>
              ))}
              {proformas.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">Няма проформа фактури</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

// Invoice Corrections Tab (Credit/Debit Notes)
function CorrectionsTab() {
  const [type, setType] = useState('');
  
  const { data, loading } = useQuery(GET_INVOICE_CORRECTIONS, {
    variables: { type: type || undefined },
  });

  const corrections = data?.invoiceCorrections || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Select
          size="small"
          value={type}
          onChange={(e) => setType(e.target.value)}
          displayEmpty
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">Всички типове</MenuItem>
          <MenuItem value="credit">Кредитно известие</MenuItem>
          <MenuItem value="debit">Дебитно известие</MenuItem>
        </Select>
        <Button variant="contained" startIcon={<AddIcon />}>
          Нова корекция
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Номер</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell>Дата</TableCell>
                <TableCell>Оригинална фактура</TableCell>
                <TableCell>Клиент</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>Статус</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {corrections.map((corr: Invoice) => (
                <TableRow key={corr.id}>
                  <TableCell>{corr.number}</TableCell>
                  <TableCell>
                    <Chip 
                      label={corr.type === 'credit' ? 'Кредитно' : 'Дебитно'} 
                      color={corr.type === 'credit' ? 'warning' : 'info'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{new Date(corr.date).toLocaleDateString('bg-BG')}</TableCell>
                  <TableCell>#{corr.originalInvoiceId}</TableCell>
                  <TableCell>{corr.clientName}</TableCell>
                  <TableCell align="right">{Number(corr.total).toFixed(2)} лв.</TableCell>
                  <TableCell><Chip label={getInvoiceStatusText(corr.status)} color={getInvoiceStatusColor(corr.status)} size="small" /></TableCell>
                </TableRow>
              ))}
              {corrections.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">Няма корекции</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

// Bank Accounts & Transactions Tab
function BankTab() {
  const [activeTab, setActiveTab] = useState(0);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showMatched, setShowMatched] = useState<boolean | undefined>(undefined);
  const [openAccountDialog, setOpenAccountDialog] = useState(false);
  const [openTransactionDialog, setOpenTransactionDialog] = useState(false);
  const [openMatchDialog, setOpenMatchDialog] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  
  const { data: accountsData, loading: loadingAccounts } = useQuery(GET_BANK_ACCOUNTS);
  const { data: transactionsData, loading: loadingTransactions, refetch } = useQuery(GET_BANK_TRANSACTIONS, {
    variables: { bankAccountId: accountId || undefined, startDate: startDate || undefined, endDate: endDate || undefined, matched: showMatched },
  });

  const { data: invoicesData } = useQuery(GET_INVOICES, {
    variables: { type: undefined, status: undefined },
  });

  const [createAccount] = useMutation(CREATE_BANK_ACCOUNT);
  const [createTransaction] = useMutation(CREATE_BANK_TRANSACTION);
  const [matchTransaction] = useMutation(MATCH_BANK_TRANSACTION);
  const [unmatchTransaction] = useMutation(UNMATCH_BANK_TRANSACTION);
  const [autoMatchTransactions] = useMutation(AUTO_MATCH_BANK_TRANSACTIONS);

  const accounts = accountsData?.bankAccounts || [];
  const transactions = transactionsData?.bankTransactions || [];
  const invoices = invoicesData?.invoices || [];

  const [accountForm, setAccountForm] = useState({
    iban: '', bic: '', bankName: '', accountType: 'current', isDefault: false, currency: 'BGN'
  });

  const [transactionForm, setTransactionForm] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: '', type: 'credit', description: '', reference: ''
  });

  const handleSaveAccount = async () => {
    try {
      await createAccount({
        variables: {
          input: { ...accountForm, companyId: 1 }
        }
      });
      setOpenAccountDialog(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveTransaction = async () => {
    if (!accountId) return;
    try {
      await createTransaction({
        variables: {
          input: {
            bankAccountId: accountId,
            date: transactionForm.date,
            amount: parseFloat(transactionForm.amount),
            type: transactionForm.type,
            description: transactionForm.description,
            reference: transactionForm.reference,
            companyId: 1
          }
        }
      });
      setOpenTransactionDialog(false);
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMatchTransaction = async (transactionId: number, invoiceId: number) => {
    try {
      await matchTransaction({ variables: { transactionId, invoiceId } });
      refetch();
      setOpenMatchDialog(false);
      setSelectedTransaction(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUnmatchTransaction = async (transactionId: number) => {
    try {
      await unmatchTransaction({ variables: { transactionId } });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAutoMatch = async () => {
    if (!accountId) return;
    try {
      const result = await autoMatchTransactions({ variables: { bankAccountId: accountId } });
      if (result.data?.autoMatchBankTransactions) {
        alert(`Съпоставени: ${result.data.autoMatchBankTransactions.matchedCount}, Не съпоставени: ${result.data.autoMatchBankTransactions.unmatchedCount}`);
      }
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenMatchDialog = (tx: Transaction) => {
    setSelectedTransaction(tx);
    setOpenMatchDialog(true);
  };

  const matchedCount = transactions.filter((tx: Transaction) => tx.matched).length;
  const unmatchedCount = transactions.filter((tx: Transaction) => !tx.matched).length;

  return (
    <Box>
      <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 2 }}>
        <Tab label="Банкови сметки" />
        <Tab label="Транзакции" />
      </Tabs>

      {activeTab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenAccountDialog(true)}>
              Нова сметка
            </Button>
          </Box>
          {loadingAccounts ? <CircularProgress /> : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>IBAN</TableCell>
                    <TableCell>Банка</TableCell>
                    <TableCell>BIC</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell>Валута</TableCell>
                    <TableCell>По подразбиране</TableCell>
                    <TableCell>Активна</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {accounts.map((acc: Account) => (
                    <TableRow key={acc.id}>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{acc.iban}</TableCell>
                      <TableCell>{acc.bankName}</TableCell>
                      <TableCell>{acc.bic}</TableCell>
                      <TableCell>{acc.accountType}</TableCell>
                      <TableCell>{acc.currency}</TableCell>
                      <TableCell>{acc.isDefault ? '✅' : ''}</TableCell>
                      <TableCell>{acc.isActive ? '✅' : '❌'}</TableCell>
                    </TableRow>
                  ))}
                  {accounts.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} align="center">Няма банкови сметки</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      )}

      {activeTab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Сметка</InputLabel>
              <Select value={accountId || ''} label="Сметка" onChange={(e) => setAccountId(e.target.value as number)}>
                {accounts.map((acc: Account) => (
                  <MenuItem key={acc.id} value={acc.id}>{acc.bankName} - {acc.iban?.slice(-4) || '----'}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField size="small" label="От дата" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} InputLabelProps={{ shrink: true }} />
            <TextField size="small" label="До дата" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} InputLabelProps={{ shrink: true }} />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Съпоставени</InputLabel>
              <Select value={showMatched === undefined ? '' : showMatched ? 'matched' : 'unmatched'} label="Съпоставени" onChange={(e) => {
                const val = e.target.value;
                setShowMatched(val === 'matched' ? true : val === 'unmatched' ? false : undefined);
              }}>
                <MenuItem value="">Всички</MenuItem>
                <MenuItem value="matched">Само съпоставени</MenuItem>
                <MenuItem value="unmatched">Само не съпоставени</MenuItem>
              </Select>
            </FormControl>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenTransactionDialog(true)} disabled={!accountId}>
              Нова транзакция
            </Button>
            <Button variant="outlined" startIcon={<EditIcon />} onClick={handleAutoMatch} disabled={!accountId}>
              Автоматично съпоставяне
            </Button>
          </Box>
          {accountId && (
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip label={`Съпоставени: ${matchedCount}`} color="success" />
              <Chip label={`Не съпоставени: ${unmatchedCount}`} color="warning" />
            </Box>
          )}
          {loadingTransactions ? <CircularProgress /> : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell align="right">Сума</TableCell>
                    <TableCell>Описание</TableCell>
                    <TableCell>Референция</TableCell>
                    <TableCell>Съответства</TableCell>
                    <TableCell>Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.map((tx: Transaction) => (
                    <TableRow key={tx.id} sx={{ backgroundColor: tx.type === 'credit' ? '#e8f5e9' : '#ffebee' }}>
                      <TableCell>{new Date(tx.date).toLocaleDateString('bg-BG')}</TableCell>
                      <TableCell><Chip label={tx.type === 'credit' ? 'Приход' : 'Разход'} color={tx.type === 'credit' ? 'success' : 'error'} size="small" /></TableCell>
                      <TableCell align="right">{Number(tx.amount).toFixed(2)} лв.</TableCell>
                      <TableCell>{tx.description}</TableCell>
                      <TableCell>{tx.reference}</TableCell>
                      <TableCell>
                        {tx.matched ? (
                          <Chip label={`✅ ${tx.invoiceId || ''}`} size="small" color="success" />
                        ) : (
                          <Chip label="❌ Не" size="small" color="warning" variant="outlined" />
                        )}
                      </TableCell>
                      <TableCell>
                        {tx.matched ? (
                          <Button size="small" color="error" onClick={() => handleUnmatchTransaction(tx.id)}>
                            Премахни
                          </Button>
                        ) : (
                          <Button size="small" variant="contained" onClick={() => handleOpenMatchDialog(tx)}>
                            Съпостави
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {transactions.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} align="center">Няма транзакции</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      )}

      {/* Account Dialog */}
      <Dialog open={openAccountDialog} onClose={() => setOpenAccountDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова банкова сметка</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="IBAN" value={accountForm.iban} onChange={(e) => setAccountForm({...accountForm, iban: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Банка" value={accountForm.bankName} onChange={(e) => setAccountForm({...accountForm, bankName: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="BIC" value={accountForm.bic} onChange={(e) => setAccountForm({...accountForm, bic: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Тип</InputLabel>
                <Select value={accountForm.accountType} label="Тип" onChange={(e) => setAccountForm({...accountForm, accountType: e.target.value})}>
                  <MenuItem value="current">Разплащателна</MenuItem>
                  <MenuItem value="escrow">Ескроу</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAccountDialog(false)}>Отказ</Button>
          <Button onClick={handleSaveAccount} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Transaction Dialog */}
      <Dialog open={openTransactionDialog} onClose={() => setOpenTransactionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова транзакция</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Дата" type="date" value={transactionForm.date} onChange={(e) => setTransactionForm({...transactionForm, date: e.target.value})} InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Тип</InputLabel>
                <Select value={transactionForm.type} label="Тип" onChange={(e) => setTransactionForm({...transactionForm, type: e.target.value})}>
                  <MenuItem value="credit">Приход</MenuItem>
                  <MenuItem value="debit">Разход</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Сума" type="number" value={transactionForm.amount} onChange={(e) => setTransactionForm({...transactionForm, amount: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Описание" value={transactionForm.description} onChange={(e) => setTransactionForm({...transactionForm, description: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Референция" value={transactionForm.reference} onChange={(e) => setTransactionForm({...transactionForm, reference: e.target.value})} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTransactionDialog(false)}>Отказ</Button>
          <Button onClick={handleSaveTransaction} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Match Transaction Dialog */}
      <Dialog open={openMatchDialog} onClose={() => setOpenMatchDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Съпостави транзакция #{selectedTransaction?.id}</DialogTitle>
        <DialogContent dividers>
          {selectedTransaction && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary">Транзакция:</Typography>
              <Typography variant="body1">
                {selectedTransaction.type === 'credit' ? 'Приход' : 'Разход'} - {Number(selectedTransaction.amount).toFixed(2)} лв.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Референция: {selectedTransaction.reference || '-'}
              </Typography>
            </Box>
          )}
          <Typography variant="subtitle2" sx={{ mb: 2 }}>Избери фактура:</Typography>
          <FormControl fullWidth size="small">
            <InputLabel>Фактура</InputLabel>
            <Select
              label="Фактура"
              onChange={(e) => {
                if (selectedTransaction && e.target.value) {
                  handleMatchTransaction(selectedTransaction.id, e.target.value as number);
                }
              }}
            >
              {invoices
                .filter((inv: Invoice) => Math.abs(Number(inv.total) - Number(selectedTransaction?.amount)) < 0.01)
                .map((inv: Invoice) => (
                  <MenuItem key={inv.id} value={inv.id}>
                    {inv.number} - {inv.supplier?.name || inv.clientName || '-'} - {Number(inv.total).toFixed(2)} лв.
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
          {invoices.filter((inv: Invoice) => Math.abs(Number(inv.total) - Number(selectedTransaction?.amount)) < 0.01).length === 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Няма намерени фактури със същата сума. Опитайте ръчно да изберете фактура.
            </Alert>
          )}
          <Divider sx={{ my: 2 }} />
          <Typography variant="caption" color="text.secondary">
            Или изберете ръчно от списъка по-долу:
          </Typography>
          <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
            {invoices.slice(0, 10).map((inv: Invoice) => (
              <ListItem 
                key={inv.id} 
                disablePadding
                sx={{ cursor: 'pointer' }}
                onClick={() => selectedTransaction && handleMatchTransaction(selectedTransaction.id, inv.id)}
              >
                <ListItemText
                  primary={`${inv.number} - ${inv.supplier?.name || inv.clientName || '-'}`}
                  secondary={`${Number(inv.total).toFixed(2)} лв. - ${new Date(inv.date).toLocaleDateString('bg-BG')}`}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenMatchDialog(false)}>Затвори</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// Chart of Accounts Tab
function AccountsTab() {
  const [type, setType] = useState('');
  
  const { data, loading, refetch } = useQuery(GET_ACCOUNTS, {
    variables: { type: type || undefined },
  });

  const [createAccount] = useMutation(CREATE_ACCOUNT);

  const accounts = data?.accounts || [];

  const [openDialog, setOpenDialog] = useState(false);
  const [accountForm, setAccountForm] = useState({ code: '', name: '', type: 'expense', parentId: null as number | null });

  const handleSave = async () => {
    try {
      await createAccount({
        variables: {
          input: { ...accountForm, companyId: 1, openingBalance: 0 }
        }
      });
      setOpenDialog(false);
      setAccountForm({ code: '', name: '', type: 'expense', parentId: null });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Select size="small" value={type} onChange={(e) => setType(e.target.value)} displayEmpty sx={{ minWidth: 150 }}>
          <MenuItem value="">Всички типове</MenuItem>
          <MenuItem value="asset">Активи</MenuItem>
          <MenuItem value="liability">Пасиви</MenuItem>
          <MenuItem value="equity">Собствен капитал</MenuItem>
          <MenuItem value="revenue">Приходи</MenuItem>
          <MenuItem value="expense">Разходи</MenuItem>
        </Select>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenDialog(true)}>
          Нова сметка
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Код</TableCell>
                <TableCell>Име</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell align="right">Начално салдо</TableCell>
                <TableCell align="right">Крайно салдо</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {accounts.map((acc: any) => (
                <TableRow key={acc.id}>
                  <TableCell sx={{ fontWeight: 'bold' }}>{acc.code}</TableCell>
                  <TableCell>{acc.name}</TableCell>
                  <TableCell>
                    <Chip label={acc.type} size="small" color={
                      acc.type === 'asset' ? 'success' : 
                      acc.type === 'liability' ? 'error' : 
                      acc.type === 'revenue' ? 'info' : 'default'
                    } />
                  </TableCell>
                  <TableCell align="right">{Number(acc.openingBalance).toFixed(2)}</TableCell>
                  <TableCell align="right">{Number(acc.closingBalance).toFixed(2)}</TableCell>
                </TableRow>
              ))}
              {accounts.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">Няма сметки</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова сметка</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 4 }}>
              <TextField fullWidth label="Код" value={accountForm.code} onChange={(e) => setAccountForm({...accountForm, code: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 8 }}>
              <TextField fullWidth label="Име" value={accountForm.name} onChange={(e) => setAccountForm({...accountForm, name: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Тип</InputLabel>
                <Select value={accountForm.type} label="Тип" onChange={(e) => setAccountForm({...accountForm, type: e.target.value})}>
                  <MenuItem value="asset">Актив</MenuItem>
                  <MenuItem value="liability">Пасив</MenuItem>
                  <MenuItem value="equity">Собствен капитал</MenuItem>
                  <MenuItem value="revenue">Приход</MenuItem>
                  <MenuItem value="expense">Разход</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Отказ</Button>
          <Button onClick={handleSave} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// VAT Registers Tab
function VATTab() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [generating, setGenerating] = useState(false);

  const { data, loading, refetch } = useQuery(GET_VAT_REGISTERS, {
    variables: { year, month },
  });

  const [generateVAT] = useMutation(GENERATE_VAT_REGISTER);

  const registers = data?.vatRegisters || [];

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateVAT({ variables: { input: { periodMonth: month, periodYear: year, companyId: 1 } } });
      refetch();
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const monthNames = ['Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни', 'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'];

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField
          size="small"
          label="Година"
          type="number"
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          sx={{ width: 120 }}
        />
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Месец</InputLabel>
          <Select value={month} label="Месец" onChange={(e) => setMonth(e.target.value as number)}>
            {monthNames.map((m, i) => <MenuItem key={i+1} value={i+1}>{m}</MenuItem>)}
          </Select>
        </FormControl>
        <Button variant="contained" onClick={handleGenerate} disabled={generating}>
          {generating ? 'Генериране...' : 'Генерирай ДДС'}
        </Button>
      </Box>

      {loading ? <CircularProgress /> : registers.length === 0 ? (
        <Alert severity="info">Няма ДДС регистър за този период</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Период</TableCell>
                <TableCell align="right">ДДС приход 20%</TableCell>
                <TableCell align="right">ДДС приход 9%</TableCell>
                <TableCell align="right">ДДС разход 20%</TableCell>
                <TableCell align="right">ДДС разход 9%</TableCell>
                <TableCell align="right">ДДС за внасяне</TableCell>
                <TableCell align="right">ДДС за възстановяване</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {registers.map((reg: Register) => (
                <TableRow key={reg.id}>
                  <TableCell sx={{ fontWeight: 'bold' }}>{monthNames[reg.periodMonth - 1]} {reg.periodYear}</TableCell>
                  <TableCell align="right">{Number(reg.vatCollected20).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{Number(reg.vatCollected9).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{Number(reg.vatPaid20).toFixed(2)} лв.</TableCell>
                  <TableCell align="right">{Number(reg.vatPaid9).toFixed(2)} лв.</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold', color: reg.vatDue > 0 ? 'error.main' : 'success.main' }}>
                    {Number(reg.vatDue).toFixed(2)} лв.
                  </TableCell>
                  <TableCell align="right" sx={{ color: reg.vatCredit > 0 ? 'success.main' : 'text.default' }}>
                    {Number(reg.vatCredit).toFixed(2)} лв.
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

// SAF-T Generator Tab
function SAFTTab() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [saftType, setSaftType] = useState('monthly');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [generateSAFT] = useMutation(GENERATE_SAFT_FILE);

  const monthNames = ['Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни', 'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'];

  const handleGenerate = async () => {
    setGenerating(true);
    setResult(null);
    try {
      const { data } = await generateSAFT({
        variables: {
          companyId: 1,
          year,
          month,
          saftType
        }
      });
      setResult(data?.generateSAFTFile);
    } catch (err) {
      console.error(err);
      setResult({ error: 'Грешка при генериране на SAF-T файл' });
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!result?.xmlContent) return;
    const blob = new Blob([result.xmlContent], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.fileName || `SAFT_${year}_${month}.xml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3, bgcolor: '#f8f9fa' }}>
        <Typography variant="h6" gutterBottom>Генериране на SAF-T файл</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          SAF-T (Standard Audit File for Tax) е задължителен за големи предприятия от Януари 2026.
          Файлът се подава към НАП по електронен път.
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            size="small"
            label="Година"
            type="number"
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
            sx={{ width: 120 }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Месец</InputLabel>
            <Select value={month} label="Месец" onChange={(e) => setMonth(e.target.value as number)}>
              {monthNames.map((m, i) => <MenuItem key={i+1} value={i+1}>{m}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Тип</InputLabel>
            <Select value={saftType} label="Тип" onChange={(e) => setSaftType(e.target.value)}>
              <MenuItem value="monthly">Месечен</MenuItem>
              <MenuItem value="annual">Годишен</MenuItem>
              <MenuItem value="on_demand">По заявка</MenuItem>
            </Select>
          </FormControl>
          <Button 
            variant="contained" 
            color="primary"
            onClick={handleGenerate} 
            disabled={generating}
            startIcon={generating ? <CircularProgress size={16} color="inherit" /> : null}
          >
            {generating ? 'Генериране...' : 'Генерирай SAF-T'}
          </Button>
        </Box>
      </Paper>

      {result && (
        <Box>
          {result.error ? (
            <Alert severity="error">{result.error}</Alert>
          ) : (
            <>
              <Alert severity="success" sx={{ mb: 2 }}>
                SAF-T файлът е генериран успешно! Размер: {result.fileSize} bytes
              </Alert>
              
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Информация за файла:</Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2"><strong>Период:</strong> {result.periodStart} - {result.periodEnd}</Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2"><strong>Име на файл:</strong> {result.fileName}</Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2">
                      <strong>Валидация:</strong> {' '}
                      <Chip 
                        label={result.validationResult?.status === 'valid' ? 'Валиден' : 'Невалиден'} 
                        color={result.validationResult?.status === 'valid' ? 'success' : 'error'} 
                        size="small" 
                      />
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="contained" color="primary" onClick={handleDownload}>
                  Свали XML
                </Button>
              </Box>

              {result.validationResult?.warnings?.length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <strong>Предупреждения:</strong>
                  <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                    {result.validationResult.warnings.map((w: string, i: number) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </Alert>
              )}
            </>
          )}
        </Box>
      )}

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>Информация за SAF-T</Typography>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Задължителни предприятия</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Период</TableCell>
                  <TableCell>Задължени предприятия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Януари 2026</TableCell>
                  <TableCell>Големи (&gt;300 млн. лв. оборот)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Януари 2028</TableCell>
                  <TableCell>Средни (&gt;15 млн. лв. оборот)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Януари 2030</TableCell>
                  <TableCell>Всички останали</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </AccordionDetails>
        </Accordion>
      </Box>
    </Box>
  );
}

  const handleOpenDialog = (invoice?: Invoice) => {
    if (invoice) {
      setEditingInvoice(invoice);
      setFormData({
        type: invoice.type,
        documentType: (invoice as any).documentType || 'ФАКТУРА',
        griff: (invoice as any).griff || 'ОРИГИНАЛ',
        description: (invoice as any).description || '',
        date: invoice.date ? invoice.date.split('T')[0] : '',
        supplierId: invoice.supplier?.id || null,
        clientName: invoice.clientName || '',
        clientEik: invoice.clientEik || '',
        clientAddress: invoice.clientAddress || '',
        discountPercent: Number(invoice.discountPercent),
        vatRate: Number(invoice.vatRate),
        paymentMethod: invoice.paymentMethod || '',
        deliveryMethod: (invoice as any).deliveryMethod || '',
        dueDate: invoice.dueDate ? invoice.dueDate.split('T')[0] : '',
        paymentDate: invoice.paymentDate ? invoice.paymentDate.split('T')[0] : '',
        status: invoice.status,
        notes: invoice.notes || '',
        items: invoice.items.map(item => ({
          id: item.id,
          ingredientId: item.ingredientId,
          batchId: item.batchId,
          batchNumber: (item as any).batchNumber || '',
          expirationDate: (item as any).expirationDate ? (item as any).expirationDate.split('T')[0] : '',
          name: item.name,
          quantity: Number(item.quantity),
          unit: item.unit,
          unitPrice: Number(item.unitPrice),
          unitPriceWithVat: (item as any).unitPriceWithVat ? Number((item as any).unitPriceWithVat) : null,
          discountPercent: Number(item.discountPercent),
        })),
      });
    } else {
      setEditingInvoice(null);
      setFormData({
        type: invoiceType,
        documentType: 'ФАКТУРА',
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
      } else {
        await createInvoice({ variables: { invoiceData } });
      }

      handleCloseDialog();
      refetch();
    } catch (err) {
      console.error('Error saving invoice:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Сигурен ли сте, че искате да изтриете тази фактура?')) {
      try {
        await deleteInvoice({ variables: { id } });
        refetch();
      } catch (err) {
        console.error('Error deleting invoice:', err);
      }
    }
  };

  const { subtotal, discountAmount, vatAmount, total } = calculateTotals();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ width: '100%', mb: 2, p: 2 }}>
        {tabValue === 0 && <IncomingInvoicesTab search={search} setSearch={setSearch} handleOpenDialog={handleOpenDialog} handleOpenDetailsDialog={handleOpenDetailsDialog} handleDelete={handleDelete} handlePrintInvoice={handlePrintInvoice} />}
        {tabValue === 1 && <OutgoingInvoicesTab search={search} setSearch={setSearch} handleOpenDialog={handleOpenDialog} handleDelete={handleDelete} handlePrintInvoice={handlePrintInvoice} />}
        {tabValue === 2 && <CashJournalTab />}
        {tabValue === 3 && <OperationLogsTab />}
        {tabValue === 4 && <DailySummaryTab />}
        {tabValue === 5 && <MonthlyReportTab />}
        {tabValue === 6 && <YearlyReportTab />}
        {tabValue === 7 && <ProformaTab />}
        {tabValue === 8 && <CorrectionsTab />}
        {tabValue === 9 && <BankTab />}
        {tabValue === 10 && <AccountsTab />}
        {tabValue === 11 && <VATTab />}
        {tabValue === 12 && <SAFTTab />}
        {tabValue === 13 && <AccountingEntriesTab />}
      </Paper>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingInvoice ? 'Редактирай фактура' : 'Нова фактура'}</DialogTitle>
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
                    <Typography variant="h6">{subtotal.toFixed(2)} лв.</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Typography variant="caption" display="block">Отстъпка</Typography>
                    <Typography variant="h6">{discountAmount.toFixed(2)} лв.</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Typography variant="caption" display="block">ДДС ({formData.vatRate}%)</Typography>
                    <Typography variant="h6">{vatAmount.toFixed(2)} лв.</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Typography variant="caption" display="block">ОБЩО</Typography>
                    <Typography variant="h5" fontWeight="bold">{total.toFixed(2)} лв.</Typography>
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
                                  до {batch.expiryDate ? new Date(batch.expiryDate).toLocaleDateString('bg-BG') : '-'}
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
                          до ${item.batch.expiryDate ? new Date(item.batch.expiryDate).toLocaleDateString('bg-BG') : '-'}`}
                        sx={{ mt: 1 }}
                        color="success"
                        variant="outlined"
                      />
                    )}
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      Общо: {(item.quantity * item.unitPrice).toFixed(2)} лв. (със ДДС: {(item.quantity * (item.unitPriceWithVat || item.unitPrice * 1.2)).toFixed(2)} лв.)
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
                <Typography variant="body1">Дата: {new Date(selectedInvoice.date).toLocaleDateString('bg-BG')}</Typography>
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
                            <TableCell>{item.expirationDate ? new Date(item.expirationDate).toLocaleDateString('bg-BG') : '-'}</TableCell>
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
                        <TableCell>лв.</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              {/* Дати и начин на плащане */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2">Дата на фактура: {new Date(selectedInvoice.date).toLocaleDateString('bg-BG')}</Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2">Дата на плащане: {selectedInvoice.dueDate ? new Date(selectedInvoice.dueDate).toLocaleDateString('bg-BG') : '-'}</Typography>
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

// Wrapper components for sub-menu pages that need props from main component

function AccountingEntriesTab() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [accountId, setAccountId] = useState<number | null>(null);
  const [search, setSearch] = useState('');

  const { data, loading, error, refetch } = useQuery(GET_ACCOUNTING_ENTRIES, {
    variables: {
      startDate: startDate || undefined,
      endDate: endDate || undefined,
      accountId: accountId || undefined,
      search: search || undefined,
    },
  });

  const { data: accountsData } = useQuery(GET_ACCOUNTS);

  const entries = data?.accountingEntries || [];
  const accounts = accountsData?.accounts || [];

  const totalDebit = entries.reduce((sum: number, entry: AccountingEntry) => sum + Number(entry.amount), 0);
  const totalVat = entries.reduce((sum: number, entry: AccountingEntry) => sum + Number(entry.vatAmount), 0);

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          size="small"
          type="date"
          label="От дата"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ width: 150 }}
        />
        <TextField
          size="small"
          type="date"
          label="До дата"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ width: 150 }}
        />
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Филтрирай по сметка</InputLabel>
          <Select
            value={accountId || ''}
            label="Филтрирай по сметка"
            onChange={(e) => setAccountId(e.target.value as number || null)}
          >
            <MenuItem value="">Всички сметки</MenuItem>
            {accounts.map((acc: Account) => (
              <MenuItem key={acc.id} value={acc.id}>
                {acc.code} - {acc.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          size="small"
          label="Търси"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ width: 200 }}
        />
        <Button
          size="small"
          variant="outlined"
          onClick={() => refetch()}
        >
          Обнови
        </Button>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : error ? (
        <Alert severity="error">Грешка при зареждане на счетоводните записи</Alert>
      ) : (
        <>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Chip label={`Общо записи: ${entries.length}`} />
            <Chip label={`Обща сума: ${totalDebit.toFixed(2)} лв.`} color="primary" />
            <Chip label={`ДДС: ${totalVat.toFixed(2)} лв.`} color="secondary" />
          </Box>

          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.100' }}>
                  <TableCell>№</TableCell>
                  <TableCell>Дата</TableCell>
                  <TableCell>№ на запис</TableCell>
                  <TableCell>Описание</TableCell>
                  <TableCell>Дебит сметка</TableCell>
                  <TableCell>Кредит сметка</TableCell>
                  <TableCell align="right">Сума</TableCell>
                  <TableCell align="right">ДДС</TableCell>
                  <TableCell>Фактура</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {entries.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">Няма счетоводни записи</TableCell>
                  </TableRow>
                ) : (
                  entries.map((entry: AccountingEntry) => (
                    <TableRow key={entry.id} hover>
                      <TableCell>{entry.id}</TableCell>
                      <TableCell>{new Date(entry.date).toLocaleDateString('bg-BG')}</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>{entry.entryNumber}</TableCell>
                      <TableCell>{entry.description || '-'}</TableCell>
                      <TableCell>
                        {entry.debitAccount ? (
                          <Chip
                            size="small"
                            label={`${entry.debitAccount.code} ${entry.debitAccount.name}`}
                            variant="outlined"
                            color="success"
                          />
                        ) : (
                          entry.debitAccountId
                        )}
                      </TableCell>
                      <TableCell>
                        {entry.creditAccount ? (
                          <Chip
                            size="small"
                            label={`${entry.creditAccount.code} ${entry.creditAccount.name}`}
                            variant="outlined"
                            color="warning"
                          />
                        ) : (
                          entry.creditAccountId
                        )}
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                        {Number(entry.amount).toFixed(2)} лв.
                      </TableCell>
                      <TableCell align="right">
                        {Number(entry.vatAmount) > 0 ? (
                          <Typography variant="caption" color="secondary">
                            {Number(entry.vatAmount).toFixed(2)} лв.
                          </Typography>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {entry.invoice ? (
                          <Chip
                            size="small"
                            label={entry.invoice.number}
                            variant="outlined"
                            onClick={() => {}}
                          />
                        ) : entry.invoiceId ? (
                          <Typography variant="caption">#{entry.invoiceId}</Typography>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );
}

function IncomingInvoicesTab({ search, setSearch, handleOpenDialog, handleOpenDetailsDialog, handleDelete, handlePrintInvoice }: { 
  search: string; 
  setSearch: (s: string) => void; 
  handleOpenDialog: (invoice?: Invoice) => void; 
  handleOpenDetailsDialog: (invoice: Invoice) => void;
  handleDelete: (id: number) => void;
  handlePrintInvoice: (id: number) => void;
}) {
  const { data, loading, error } = useQuery(GET_INVOICES, {
    variables: { type: 'incoming', search: search || undefined },
  });
  const invoices: Invoice[] = data?.invoices || [];
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <TextField size="small" label="Търси" value={search} onChange={(e) => setSearch(e.target.value)} sx={{ width: 300 }} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>Нова входяща фактура</Button>
      </Box>
      {loading ? <CircularProgress /> : error ? <Alert severity="error">Грешка при зареждане на фактурите</Alert> : (
        <TableContainer>
          <Table>
            <TableHead><TableRow><TableCell /><TableCell>Номер</TableCell><TableCell>дата</TableCell><TableCell>доставчик</TableCell><TableCell>Партида</TableCell><TableCell>Срок годност</TableCell><TableCell align="right">сума</TableCell><TableCell>ддс</TableCell><TableCell>статус</TableCell><TableCell>действия</TableCell></TableRow></TableHead>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow key={invoice.id} hover onClick={() => handleOpenDetailsDialog(invoice)} sx={{ cursor: 'pointer' }}>
                  <TableCell><IconButton size="small"><ExpandMoreIcon /></IconButton></TableCell>
                  <TableCell>{invoice.number}</TableCell>
                  <TableCell>{new Date(invoice.date).toLocaleDateString('bg-BG')}</TableCell>
                  <TableCell>{invoice.supplier?.name || '-'}</TableCell>
                  <TableCell>{invoice.batch && typeof invoice.batch === 'object' ? (invoice.batch as unknown as { batchNumber?: string }).batchNumber || '-' : '-'}</TableCell>
                  <TableCell>{invoice.batch && typeof invoice.batch === 'object' ? ((invoice.batch as unknown as { expiryDate?: string }).expiryDate ? new Date((invoice.batch as unknown as { expiryDate: string }).expiryDate).toLocaleDateString('bg-BG') : '-') : '-'}</TableCell>
                  <TableCell align="right">{Number(invoice.total).toFixed(2)} лв.</TableCell>
                  <TableCell>{Number(invoice.vatRate)}%</TableCell>
                  <TableCell><Chip label={getInvoiceStatusText(invoice.status)} color={getInvoiceStatusColor(invoice.status)} size="small" /></TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <Tooltip title="PDF"><IconButton size="small" onClick={() => handlePrintInvoice(invoice.id)}><PrintIcon /></IconButton></Tooltip>
                    <Tooltip title="Редактирай"><IconButton size="small" onClick={() => handleOpenDialog(invoice)}><EditIcon /></IconButton></Tooltip>
                    <Tooltip title="Изтрий"><IconButton size="small" onClick={() => handleDelete(invoice.id)}><DeleteIcon /></IconButton></Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

function OutgoingInvoicesTab({ search, setSearch, handleOpenDialog, handleDelete, handlePrintInvoice }: { 
  search: string; 
  setSearch: (s: string) => void; 
  handleOpenDialog: (invoice?: Invoice) => void;
  handleDelete: (id: number) => void;
  handlePrintInvoice: (id: number) => void;
}) {
  const { data, loading, error } = useQuery(GET_INVOICES, {
    variables: { type: 'outgoing', search: search || undefined },
  });
  const invoices: Invoice[] = data?.invoices || [];
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <TextField size="small" label="Търси" value={search} onChange={(e) => setSearch(e.target.value)} sx={{ width: 300 }} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>Нова изходяща фактура</Button>
      </Box>
      {loading ? <CircularProgress /> : error ? <Alert severity="error">Грешка при зареждане на фактурите</Alert> : (
        <TableContainer>
          <Table>
            <TableHead><TableRow><TableCell /><TableCell>Номер</TableCell><TableCell>Дата</TableCell><TableCell>Клиент</TableCell><TableCell>Партида</TableCell><TableCell>Срок годност</TableCell><TableCell align="right">Сума</TableCell><TableCell>ДДС</TableCell><TableCell>Статус</TableCell><TableCell>Действия</TableCell></TableRow></TableHead>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell><IconButton size="small"><ExpandMoreIcon /></IconButton></TableCell>
                  <TableCell>{invoice.number}</TableCell>
                  <TableCell>{new Date(invoice.date).toLocaleDateString('bg-BG')}</TableCell>
                  <TableCell>{invoice.clientName || '-'}</TableCell>
                  <TableCell>{invoice.batch && typeof invoice.batch === 'object' ? (invoice.batch as unknown as { batchNumber?: string }).batchNumber || '-' : '-'}</TableCell>
                  <TableCell>{invoice.batch && typeof invoice.batch === 'object' ? ((invoice.batch as unknown as { expiryDate?: string }).expiryDate ? new Date((invoice.batch as unknown as { expiryDate: string }).expiryDate).toLocaleDateString('bg-BG') : '-') : '-'}</TableCell>
                  <TableCell align="right">{Number(invoice.total).toFixed(2)} лв.</TableCell>
                  <TableCell>{Number(invoice.vatRate)}%</TableCell>
                  <TableCell><Chip label={getInvoiceStatusText(invoice.status)} color={getInvoiceStatusColor(invoice.status)} size="small" /></TableCell>
                  <TableCell>
                    <Tooltip title="PDF"><IconButton size="small" onClick={() => handlePrintInvoice(invoice.id)}><PrintIcon /></IconButton></Tooltip>
                    <Tooltip title="Редактирай"><IconButton size="small" onClick={() => handleOpenDialog(invoice)}><EditIcon /></IconButton></Tooltip>
                    <Tooltip title="Изтрий"><IconButton size="small" onClick={() => handleDelete(invoice.id)}><DeleteIcon /></IconButton></Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

