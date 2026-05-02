import { gql } from '@apollo/client';

export const GET_INVOICES = gql`
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

export const GET_SUPPLIERS = gql`
  query GetSuppliers {
    suppliers {
      id
      name
      eik
    }
  }
`;

export const GET_INGREDIENTS = gql`
  query GetIngredients {
    ingredients {
      id
      name
      unit
      currentPrice
    }
  }
`;

export const GET_INGREDIENT_BATCHES_WITH_STOCK = gql`
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

export const CREATE_INVOICE = gql`
  mutation CreateInvoice($invoiceData: InvoiceInput!) {
    createInvoice(invoiceData: $invoiceData) {
      id
      number
    }
  }
`;

export const CREATE_PROFORMA_INVOICE = gql`
  mutation CreateProformaInvoice($clientName: String!, $clientEik: String, $clientAddress: String, $date: String!, $items: [InvoiceItemInput!]!, $vatRate: Float!, $discountPercent: Float!, $notes: String) {
    createProformaInvoice(clientName: $clientName, clientEik: $clientEik, clientAddress: $clientAddress, date: $date, items: $items, vatRate: $vatRate, discountPercent: $discountPercent, notes: $notes) {
      id
      number
    }
  }
`;

export const UPDATE_INVOICE = gql`
  mutation UpdateInvoice($id: Int!, $invoiceData: InvoiceInput!) {
    updateInvoice(id: $id, invoiceData: $invoiceData) {
      id
      number
    }
  }
`;

export const DELETE_INVOICE = gql`
  mutation DeleteInvoice($id: Int!) {
    deleteInvoice(id: $id)
  }
`;

export const GET_INVOICE_PDF_URL = gql`
  mutation GetInvoicePdfUrl($invoiceId: Int!) {
    getInvoicePdfUrl(invoiceId: $invoiceId)
  }
`;

export const GET_CASH_JOURNAL_ENTRIES = gql`
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

export const CREATE_CASH_JOURNAL_ENTRY = gql`
  mutation CreateCashJournalEntry($input: CashJournalEntryInput!) {
    createCashJournalEntry(input: $input) {
      id
      date
      operationType
      amount
    }
  }
`;

export const DELETE_CASH_JOURNAL_ENTRY = gql`
  mutation DeleteCashJournalEntry($id: Int!) {
    deleteCashJournalEntry(id: $id)
  }
`;

export const GET_OPERATION_LOGS = gql`
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

export const GET_DAILY_SUMMARIES = gql`
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

export const GENERATE_DAILY_SUMMARY = gql`
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

export const GET_MONTHLY_SUMMARIES = gql`
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

export const GENERATE_MONTHLY_SUMMARY = gql`
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

export const GET_YEARLY_SUMMARIES = gql`
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

export const GENERATE_YEARLY_SUMMARY = gql`
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

export const GET_ACCOUNTING_ENTRIES = gql`
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

export const GET_PROFORMA_INVOICES = gql`
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

export const GET_INVOICE_CORRECTIONS = gql`
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

export const CREATE_INVOICE_CORRECTION = gql`
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

export const CONVERT_PROFORMA_TO_INVOICE = gql`
  mutation ConvertProformaToInvoice($proformaId: Int!, $invoiceType: String!) {
    convertProformaToInvoice(proformaId: $proformaId, invoiceType: $invoiceType) {
      id
      number
    }
  }
`;

export const GET_BANK_ACCOUNTS = gql`
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

export const GET_BANK_TRANSACTIONS = gql`
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

export const MATCH_BANK_TRANSACTION = gql`
  mutation MatchBankTransaction($transactionId: Int!, $invoiceId: Int!) {
    matchBankTransaction(transactionId: $transactionId, invoiceId: $invoiceId) {
      id
      matched
      invoiceId
    }
  }
`;

export const UNMATCH_BANK_TRANSACTION = gql`
  mutation UnmatchBankTransaction($transactionId: Int!) {
    unmatchBankTransaction(transactionId: $transactionId) {
      id
      matched
      invoiceId
    }
  }
`;

export const AUTO_MATCH_BANK_TRANSACTIONS = gql`
  mutation AutoMatchBankTransactions($bankAccountId: Int!) {
    autoMatchBankTransactions(bankAccountId: $bankAccountId) {
      matchedCount
      unmatchedCount
    }
  }
`;

export const GET_ACCOUNTS = gql`
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

export const GET_VAT_REGISTERS = gql`
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

export const GENERATE_SAFT_FILE = gql`
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

export const CREATE_BANK_ACCOUNT = gql`
  mutation CreateBankAccount($input: BankAccountInput!) {
    createBankAccount(input: $input) {
      id
      iban
    }
  }
`;

export const CREATE_BANK_TRANSACTION = gql`
  mutation CreateBankTransaction($input: BankTransactionInput!) {
    createBankTransaction(input: $input) {
      id
      reference
    }
  }
`;

export const CREATE_ACCOUNT = gql`
  mutation CreateAccount($input: AccountInput!) {
    createAccount(input: $input) {
      id
      code
    }
  }
`;

export const GENERATE_VAT_REGISTER = gql`
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