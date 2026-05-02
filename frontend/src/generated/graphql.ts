/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  Date: { input: unknown; output: unknown; }
  DateTime: { input: unknown; output: unknown; }
  Decimal: { input: unknown; output: unknown; }
  JSONScalar: { input: unknown; output: unknown; }
  Time: { input: unknown; output: unknown; }
  Upload: { input: unknown; output: unknown; }
};

export type ApiKey = {
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  keyPrefix: Scalars['String']['output'];
  lastUsedAt?: Maybe<Scalars['DateTime']['output']>;
  name: Scalars['String']['output'];
  permissions: Array<Scalars['String']['output']>;
};

export type AccessCode = {
  code: Scalars['String']['output'];
  codeType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  expiresAt?: Maybe<Scalars['DateTime']['output']>;
  gatewayId?: Maybe<Scalars['Int']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  lastUsedAt?: Maybe<Scalars['DateTime']['output']>;
  usesRemaining: Scalars['Int']['output'];
  zones: Array<Scalars['String']['output']>;
};

export type AccessCodeInput = {
  code?: InputMaybe<Scalars['String']['input']>;
  codeType?: Scalars['String']['input'];
  expiresHours?: InputMaybe<Scalars['Int']['input']>;
  gatewayId?: InputMaybe<Scalars['Int']['input']>;
  usesRemaining?: Scalars['Int']['input'];
  zones?: Array<Scalars['String']['input']>;
};

export type AccessDoor = {
  description?: Maybe<Scalars['String']['output']>;
  deviceId: Scalars['String']['output'];
  doorId: Scalars['String']['output'];
  gateway?: Maybe<Gateway>;
  gatewayId: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  isOnline: Scalars['Boolean']['output'];
  lastCheck?: Maybe<Scalars['DateTime']['output']>;
  name: Scalars['String']['output'];
  relayNumber: Scalars['Int']['output'];
  terminalId?: Maybe<Scalars['String']['output']>;
  terminalMode?: Maybe<Scalars['String']['output']>;
  zone?: Maybe<AccessZone>;
  zoneDbId: Scalars['Int']['output'];
};

export type AccessDoorInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  deviceId: Scalars['String']['input'];
  doorId: Scalars['String']['input'];
  gatewayId: Scalars['Int']['input'];
  name: Scalars['String']['input'];
  relayNumber?: Scalars['Int']['input'];
  terminalId?: InputMaybe<Scalars['String']['input']>;
  zoneDbId: Scalars['Int']['input'];
};

export type AccessLog = {
  action: Scalars['String']['output'];
  doorId?: Maybe<Scalars['String']['output']>;
  doorName?: Maybe<Scalars['String']['output']>;
  gatewayId: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  method: Scalars['String']['output'];
  reason?: Maybe<Scalars['String']['output']>;
  result: Scalars['String']['output'];
  terminalId?: Maybe<Scalars['String']['output']>;
  timestamp: Scalars['DateTime']['output'];
  userId?: Maybe<Scalars['String']['output']>;
  userName?: Maybe<Scalars['String']['output']>;
  zoneId?: Maybe<Scalars['String']['output']>;
  zoneName?: Maybe<Scalars['String']['output']>;
};

export type AccessZone = {
  antiPassbackEnabled: Scalars['Boolean']['output'];
  antiPassbackTimeout: Scalars['Int']['output'];
  antiPassbackType: Scalars['String']['output'];
  authorizedUsers: Array<User>;
  dependsOn: Array<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  level: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  requiredHoursEnd: Scalars['String']['output'];
  requiredHoursStart: Scalars['String']['output'];
  zoneId: Scalars['String']['output'];
};

export type AccessZoneInput = {
  antiPassbackEnabled?: Scalars['Boolean']['input'];
  antiPassbackTimeout?: Scalars['Int']['input'];
  antiPassbackType?: Scalars['String']['input'];
  dependsOn?: Array<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  level?: Scalars['Int']['input'];
  name: Scalars['String']['input'];
  requiredHoursEnd?: Scalars['String']['input'];
  requiredHoursStart?: Scalars['String']['input'];
  zoneId: Scalars['String']['input'];
};

export type Account = {
  closingBalance: Scalars['Decimal']['output'];
  code: Scalars['String']['output'];
  companyId: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  openingBalance: Scalars['Decimal']['output'];
  parentId?: Maybe<Scalars['Int']['output']>;
  type: Scalars['String']['output'];
};

export type AccountInput = {
  code: Scalars['String']['input'];
  companyId: Scalars['Int']['input'];
  name: Scalars['String']['input'];
  openingBalance?: Scalars['Decimal']['input'];
  parentId?: InputMaybe<Scalars['Int']['input']>;
  type: Scalars['String']['input'];
};

export type AccountUpdateInput = {
  code?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  openingBalance?: InputMaybe<Scalars['Decimal']['input']>;
  parentId?: InputMaybe<Scalars['Int']['input']>;
  type?: InputMaybe<Scalars['String']['input']>;
};

export type AccountingEntry = {
  amount: Scalars['Decimal']['output'];
  bankTransactionId?: Maybe<Scalars['Int']['output']>;
  cashJournalId?: Maybe<Scalars['Int']['output']>;
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  creator?: Maybe<User>;
  creditAccount?: Maybe<Account>;
  creditAccountId: Scalars['Int']['output'];
  date: Scalars['Date']['output'];
  debitAccount?: Maybe<Account>;
  debitAccountId: Scalars['Int']['output'];
  description?: Maybe<Scalars['String']['output']>;
  entryNumber: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  invoice?: Maybe<Invoice>;
  invoiceId?: Maybe<Scalars['Int']['output']>;
  vatAmount: Scalars['Decimal']['output'];
};

export type AccountingEntryInput = {
  amount: Scalars['Decimal']['input'];
  bankTransactionId?: InputMaybe<Scalars['Int']['input']>;
  cashJournalId?: InputMaybe<Scalars['Int']['input']>;
  companyId: Scalars['Int']['input'];
  creditAccountId: Scalars['Int']['input'];
  date: Scalars['Date']['input'];
  debitAccountId: Scalars['Int']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  entryNumber: Scalars['String']['input'];
  invoiceId?: InputMaybe<Scalars['Int']['input']>;
  vatAmount?: Scalars['Decimal']['input'];
};

export type AdvancePayment = {
  amount: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isProcessed: Scalars['Boolean']['output'];
  paymentDate: Scalars['Date']['output'];
  userId: Scalars['Int']['output'];
};

export type AnnexTemplate = {
  changeType: Scalars['String']['output'];
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  currentVersion?: Maybe<AnnexTemplateVersion>;
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  newBaseSalary?: Maybe<Scalars['Float']['output']>;
  newHolidayRate?: Maybe<Scalars['Float']['output']>;
  newNightWorkRate?: Maybe<Scalars['Float']['output']>;
  newOvertimeRate?: Maybe<Scalars['Float']['output']>;
  newWorkHoursPerWeek?: Maybe<Scalars['Int']['output']>;
};

export type AnnexTemplateSection = {
  content?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isRequired: Scalars['Boolean']['output'];
  orderIndex: Scalars['Int']['output'];
  templateId: Scalars['Int']['output'];
  title: Scalars['String']['output'];
  versionId: Scalars['Int']['output'];
};

export type AnnexTemplateSectionInput = {
  content: Scalars['String']['input'];
  isRequired?: Scalars['Boolean']['input'];
  orderIndex?: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};

export type AnnexTemplateSectionUpdateInput = {
  content?: InputMaybe<Scalars['String']['input']>;
  isRequired?: InputMaybe<Scalars['Boolean']['input']>;
  orderIndex?: InputMaybe<Scalars['Int']['input']>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export type AnnexTemplateVersion = {
  changeNote?: Maybe<Scalars['String']['output']>;
  changeType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isCurrent: Scalars['Boolean']['output'];
  newBaseSalary?: Maybe<Scalars['Float']['output']>;
  newHolidayRate?: Maybe<Scalars['Float']['output']>;
  newNightWorkRate?: Maybe<Scalars['Float']['output']>;
  newOvertimeRate?: Maybe<Scalars['Float']['output']>;
  newWorkHoursPerWeek?: Maybe<Scalars['Int']['output']>;
  sections: Array<AnnexTemplateSection>;
  templateId: Scalars['Int']['output'];
  version: Scalars['Int']['output'];
};

export type AuditLog = {
  action: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  details?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  targetId?: Maybe<Scalars['Int']['output']>;
  targetType?: Maybe<Scalars['String']['output']>;
  user?: Maybe<User>;
  userId?: Maybe<Scalars['Int']['output']>;
};

export type AutoMatchResult = {
  matchedCount: Scalars['Int']['output'];
  unmatchedCount: Scalars['Int']['output'];
};

export type BankAccount = {
  accountType: Scalars['String']['output'];
  bankName: Scalars['String']['output'];
  bic?: Maybe<Scalars['String']['output']>;
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  currency: Scalars['String']['output'];
  iban: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  isDefault: Scalars['Boolean']['output'];
};

export type BankAccountInput = {
  accountType?: Scalars['String']['input'];
  bankName: Scalars['String']['input'];
  bic?: InputMaybe<Scalars['String']['input']>;
  companyId: Scalars['Int']['input'];
  currency?: Scalars['String']['input'];
  iban: Scalars['String']['input'];
  isActive?: Scalars['Boolean']['input'];
  isDefault?: Scalars['Boolean']['input'];
};

export type BankAccountUpdateInput = {
  accountType?: InputMaybe<Scalars['String']['input']>;
  bankName?: InputMaybe<Scalars['String']['input']>;
  bic?: InputMaybe<Scalars['String']['input']>;
  currency?: InputMaybe<Scalars['String']['input']>;
  iban?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  isDefault?: InputMaybe<Scalars['Boolean']['input']>;
};

export type BankTransaction = {
  amount: Scalars['Decimal']['output'];
  bankAccountId: Scalars['Int']['output'];
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  date: Scalars['Date']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  invoiceId?: Maybe<Scalars['Int']['output']>;
  matched: Scalars['Boolean']['output'];
  reference?: Maybe<Scalars['String']['output']>;
  type: Scalars['String']['output'];
};

export type BankTransactionInput = {
  amount: Scalars['Decimal']['input'];
  bankAccountId: Scalars['Int']['input'];
  companyId: Scalars['Int']['input'];
  date: Scalars['Date']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  invoiceId?: InputMaybe<Scalars['Int']['input']>;
  reference?: InputMaybe<Scalars['String']['input']>;
  type: Scalars['String']['input'];
};

export type BankTransactionUpdateInput = {
  amount?: InputMaybe<Scalars['Decimal']['input']>;
  date?: InputMaybe<Scalars['Date']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  invoiceId?: InputMaybe<Scalars['Int']['input']>;
  matched?: InputMaybe<Scalars['Boolean']['input']>;
  reference?: InputMaybe<Scalars['String']['input']>;
  type?: InputMaybe<Scalars['String']['input']>;
};

export type Batch = {
  availableStock: Scalars['Decimal']['output'];
  batchNumber?: Maybe<Scalars['String']['output']>;
  daysUntilExpiry: Scalars['Int']['output'];
  expiryDate: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  ingredient: Ingredient;
  ingredientId: Scalars['Int']['output'];
  invoiceNumber?: Maybe<Scalars['String']['output']>;
  isExpired: Scalars['Boolean']['output'];
  quantity: Scalars['Decimal']['output'];
  receivedAt: Scalars['DateTime']['output'];
  status: Scalars['String']['output'];
  storageZone?: Maybe<StorageZone>;
  storageZoneId?: Maybe<Scalars['Int']['output']>;
  supplier?: Maybe<Supplier>;
  supplierId?: Maybe<Scalars['Int']['output']>;
};

export type BatchInput = {
  batchNumber?: InputMaybe<Scalars['String']['input']>;
  expiryDate: Scalars['Date']['input'];
  id?: InputMaybe<Scalars['Int']['input']>;
  ingredientId: Scalars['Int']['input'];
  invoiceDate?: InputMaybe<Scalars['Date']['input']>;
  invoiceNumber?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Decimal']['input'];
  storageZoneId?: InputMaybe<Scalars['Int']['input']>;
  supplierId?: InputMaybe<Scalars['Int']['input']>;
};

export type Bonus = {
  amount: Scalars['Decimal']['output'];
  date: Scalars['Date']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  user: User;
  userId: Scalars['Int']['output'];
};

export type BonusCreateInput = {
  amount: Scalars['Decimal']['input'];
  date: Scalars['Date']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  userId: Scalars['Int']['input'];
};

export type BusinessTrip = {
  accommodation: Scalars['Decimal']['output'];
  approvedAt?: Maybe<Scalars['DateTime']['output']>;
  approvedBy?: Maybe<User>;
  approvedById?: Maybe<Scalars['Int']['output']>;
  approvedNotes?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  dailyAllowance: Scalars['Decimal']['output'];
  departmentId?: Maybe<Scalars['Int']['output']>;
  destination: Scalars['String']['output'];
  endDate: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  otherExpenses: Scalars['Decimal']['output'];
  periodId?: Maybe<Scalars['Int']['output']>;
  startDate: Scalars['Date']['output'];
  status: BusinessTripStatus;
  totalAmount: Scalars['Decimal']['output'];
  transport: Scalars['Decimal']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  user: User;
  userId: Scalars['Int']['output'];
};

export type BusinessTripStatus =
  | 'APPROVED'
  | 'PAID'
  | 'PENDING'
  | 'REJECTED';

export type CashJournalEntryInput = {
  amount: Scalars['Decimal']['input'];
  companyId: Scalars['Int']['input'];
  date: Scalars['Date']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  operationType: Scalars['String']['input'];
  referenceId?: InputMaybe<Scalars['Int']['input']>;
  referenceType?: InputMaybe<Scalars['String']['input']>;
};

export type CashJournalEntryType = {
  amount: Scalars['Float']['output'];
  createdAt?: Maybe<Scalars['String']['output']>;
  createdBy?: Maybe<Scalars['Int']['output']>;
  creator?: Maybe<User>;
  date?: Maybe<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  operationType: Scalars['String']['output'];
  referenceId?: Maybe<Scalars['Int']['output']>;
  referenceType?: Maybe<Scalars['String']['output']>;
};

export type CashReceipt = {
  amount: Scalars['Decimal']['output'];
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  date: Scalars['Date']['output'];
  fiscalPrinterId?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  itemsJson?: Maybe<Scalars['String']['output']>;
  paymentType: Scalars['String']['output'];
  receiptNumber: Scalars['String']['output'];
  vatAmount: Scalars['Decimal']['output'];
};

export type CashReceiptInput = {
  amount: Scalars['Decimal']['input'];
  companyId: Scalars['Int']['input'];
  date: Scalars['Date']['input'];
  fiscalPrinterId?: InputMaybe<Scalars['String']['input']>;
  itemsJson?: InputMaybe<Scalars['String']['input']>;
  paymentType: Scalars['String']['input'];
  receiptNumber: Scalars['String']['input'];
  vatAmount?: Scalars['Decimal']['input'];
};

export type CashReceiptUpdateInput = {
  amount?: InputMaybe<Scalars['Decimal']['input']>;
  date?: InputMaybe<Scalars['Date']['input']>;
  fiscalPrinterId?: InputMaybe<Scalars['String']['input']>;
  itemsJson?: InputMaybe<Scalars['String']['input']>;
  paymentType?: InputMaybe<Scalars['String']['input']>;
  receiptNumber?: InputMaybe<Scalars['String']['input']>;
  vatAmount?: InputMaybe<Scalars['Decimal']['input']>;
};

export type ClauseTemplate = {
  category: Scalars['String']['output'];
  companyId: Scalars['Int']['output'];
  content?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  title: Scalars['String']['output'];
};

export type Company = {
  address?: Maybe<Scalars['String']['output']>;
  bulstat?: Maybe<Scalars['String']['output']>;
  defaultBankAccount?: Maybe<Account>;
  defaultBankAccountId?: Maybe<Scalars['Int']['output']>;
  defaultCashAccount?: Maybe<Account>;
  defaultCashAccountId?: Maybe<Scalars['Int']['output']>;
  defaultCustomerAccount?: Maybe<Account>;
  defaultCustomerAccountId?: Maybe<Scalars['Int']['output']>;
  defaultExpenseAccount?: Maybe<Account>;
  defaultExpenseAccountId?: Maybe<Scalars['Int']['output']>;
  defaultSalesAccount?: Maybe<Account>;
  defaultSalesAccountId?: Maybe<Scalars['Int']['output']>;
  defaultSupplierAccount?: Maybe<Account>;
  defaultSupplierAccountId?: Maybe<Scalars['Int']['output']>;
  defaultVatAccount?: Maybe<Account>;
  defaultVatAccountId?: Maybe<Scalars['Int']['output']>;
  eik?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  molName?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  vatNumber?: Maybe<Scalars['String']['output']>;
};

export type CompanyAccountingSettingsInput = {
  companyId: Scalars['Int']['input'];
  defaultBankAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultCashAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultCustomerAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultExpenseAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultSalesAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultSupplierAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultVatAccountId?: InputMaybe<Scalars['Int']['input']>;
};

export type CompanyCreateInput = {
  address?: InputMaybe<Scalars['String']['input']>;
  bulstat?: InputMaybe<Scalars['String']['input']>;
  eik?: InputMaybe<Scalars['String']['input']>;
  molName?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  vatNumber?: InputMaybe<Scalars['String']['input']>;
};

export type CompanyUpdateInput = {
  address?: InputMaybe<Scalars['String']['input']>;
  bulstat?: InputMaybe<Scalars['String']['input']>;
  defaultBankAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultCashAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultCustomerAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultExpenseAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultSalesAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultSupplierAccountId?: InputMaybe<Scalars['Int']['input']>;
  defaultVatAccountId?: InputMaybe<Scalars['Int']['input']>;
  eik?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  molName?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  vatNumber?: InputMaybe<Scalars['String']['input']>;
};

export type ContractAnnex = {
  annexNumber?: Maybe<Scalars['String']['output']>;
  baseSalary?: Maybe<Scalars['Decimal']['output']>;
  changeDescription?: Maybe<Scalars['String']['output']>;
  changeType?: Maybe<Scalars['String']['output']>;
  contractId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  effectiveDate: Scalars['Date']['output'];
  holidayRate?: Maybe<Scalars['Decimal']['output']>;
  id: Scalars['Int']['output'];
  isSigned: Scalars['Boolean']['output'];
  nightWorkRate?: Maybe<Scalars['Decimal']['output']>;
  overtimeRate?: Maybe<Scalars['Decimal']['output']>;
  position?: Maybe<Position>;
  positionId?: Maybe<Scalars['Int']['output']>;
  rejectionReason?: Maybe<Scalars['String']['output']>;
  signatureRequestedAt?: Maybe<Scalars['DateTime']['output']>;
  signedAt?: Maybe<Scalars['DateTime']['output']>;
  signedByEmployee: Scalars['Boolean']['output'];
  signedByEmployeeAt?: Maybe<Scalars['DateTime']['output']>;
  signedByEmployer: Scalars['Boolean']['output'];
  signedByEmployerAt?: Maybe<Scalars['DateTime']['output']>;
  status: Scalars['String']['output'];
  templateId?: Maybe<Scalars['Int']['output']>;
  workHoursPerWeek?: Maybe<Scalars['Int']['output']>;
};

export type ContractTemplate = {
  companyId: Scalars['Int']['output'];
  contractType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  currentVersion?: Maybe<ContractTemplateVersion>;
  description?: Maybe<Scalars['String']['output']>;
  holidayRate: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  nightWorkRate: Scalars['Float']['output'];
  overtimeRate: Scalars['Float']['output'];
  paymentDay: Scalars['Int']['output'];
  probationMonths: Scalars['Int']['output'];
  salaryCalculationType: Scalars['String']['output'];
  workClass?: Maybe<Scalars['String']['output']>;
  workHoursPerWeek: Scalars['Int']['output'];
};

export type ContractTemplateSection = {
  content?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isRequired: Scalars['Boolean']['output'];
  orderIndex: Scalars['Int']['output'];
  templateId: Scalars['Int']['output'];
  title: Scalars['String']['output'];
  versionId: Scalars['Int']['output'];
};

export type ContractTemplateSectionInput = {
  content: Scalars['String']['input'];
  isRequired?: Scalars['Boolean']['input'];
  orderIndex?: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};

export type ContractTemplateSectionUpdateInput = {
  content?: InputMaybe<Scalars['String']['input']>;
  isRequired?: InputMaybe<Scalars['Boolean']['input']>;
  orderIndex?: InputMaybe<Scalars['Int']['input']>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export type ContractTemplateVersion = {
  changeNote?: Maybe<Scalars['String']['output']>;
  contractType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['String']['output']>;
  holidayRate: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  isCurrent: Scalars['Boolean']['output'];
  nightWorkRate: Scalars['Float']['output'];
  overtimeRate: Scalars['Float']['output'];
  paymentDay: Scalars['Int']['output'];
  probationMonths: Scalars['Int']['output'];
  salaryCalculationType: Scalars['String']['output'];
  sections: Array<ContractTemplateSection>;
  templateId: Scalars['Int']['output'];
  version: Scalars['Int']['output'];
  workClass?: Maybe<Scalars['String']['output']>;
  workHoursPerWeek: Scalars['Int']['output'];
};

export type CostCenterInput = {
  companyId: Scalars['Int']['input'];
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  name: Scalars['String']['input'];
};

export type DailyStat = {
  actualArrival?: Maybe<Scalars['DateTime']['output']>;
  actualDeparture?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['Date']['output'];
  isWorkDay: Scalars['Boolean']['output'];
  overtimeHours: Scalars['Float']['output'];
  regularHours: Scalars['Float']['output'];
  shiftName?: Maybe<Scalars['String']['output']>;
  totalWorkedHours: Scalars['Float']['output'];
};

export type DailySummaryType = {
  cashBalance: Scalars['Float']['output'];
  cashExpense: Scalars['Float']['output'];
  cashIncome: Scalars['Float']['output'];
  date?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  incomingInvoicesCount: Scalars['Int']['output'];
  incomingInvoicesTotal: Scalars['Float']['output'];
  invoicesCount: Scalars['Int']['output'];
  invoicesTotal: Scalars['Float']['output'];
  outgoingInvoicesCount: Scalars['Int']['output'];
  outgoingInvoicesTotal: Scalars['Float']['output'];
  overdueInvoicesCount: Scalars['Int']['output'];
  paidInvoicesCount: Scalars['Int']['output'];
  unpaidInvoicesCount: Scalars['Int']['output'];
  vatCollected: Scalars['Float']['output'];
  vatPaid: Scalars['Float']['output'];
};

export type Department = {
  company?: Maybe<Company>;
  companyId?: Maybe<Scalars['Int']['output']>;
  id: Scalars['Int']['output'];
  manager?: Maybe<User>;
  managerId?: Maybe<Scalars['Int']['output']>;
  name: Scalars['String']['output'];
};

export type DepartmentCreateInput = {
  companyId: Scalars['Int']['input'];
  managerId?: InputMaybe<Scalars['Int']['input']>;
  name: Scalars['String']['input'];
};

export type DepartmentForecast = {
  amount: Scalars['Float']['output'];
  departmentName: Scalars['String']['output'];
};

export type DepartmentUpdateInput = {
  id: Scalars['Int']['input'];
  managerId?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};

export type EmploymentContract = {
  annexes: Array<ContractAnnex>;
  baseSalary?: Maybe<Scalars['Decimal']['output']>;
  company?: Maybe<Company>;
  companyId: Scalars['Int']['output'];
  contractNumber?: Maybe<Scalars['String']['output']>;
  contractType: Scalars['String']['output'];
  dangerousWork: Scalars['Boolean']['output'];
  department?: Maybe<Department>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  employeeEgn?: Maybe<Scalars['String']['output']>;
  employeeName?: Maybe<Scalars['String']['output']>;
  endDate?: Maybe<Scalars['Date']['output']>;
  experienceStartDate?: Maybe<Scalars['Date']['output']>;
  hasIncomeTax: Scalars['Boolean']['output'];
  holidayRate?: Maybe<Scalars['Decimal']['output']>;
  id: Scalars['Int']['output'];
  insuranceContributor: Scalars['Boolean']['output'];
  isActive: Scalars['Boolean']['output'];
  monthlyAdvanceAmount: Scalars['Decimal']['output'];
  nightWorkRate?: Maybe<Scalars['Decimal']['output']>;
  overtimeRate?: Maybe<Scalars['Decimal']['output']>;
  paymentDay: Scalars['Int']['output'];
  position?: Maybe<Position>;
  positionId?: Maybe<Scalars['Int']['output']>;
  positionTitle?: Maybe<Scalars['String']['output']>;
  probationMonths: Scalars['Int']['output'];
  salaryCalculationType: Scalars['String']['output'];
  salaryInstallmentsCount: Scalars['Int']['output'];
  signedAt?: Maybe<Scalars['DateTime']['output']>;
  startDate: Scalars['Date']['output'];
  status: Scalars['String']['output'];
  taxResident: Scalars['Boolean']['output'];
  userId?: Maybe<Scalars['Int']['output']>;
  workClass?: Maybe<Scalars['String']['output']>;
  workHoursPerWeek: Scalars['Int']['output'];
};

export type EmploymentContractCreateInput = {
  baseSalary?: InputMaybe<Scalars['Float']['input']>;
  clauseIds?: InputMaybe<Scalars['String']['input']>;
  companyId?: InputMaybe<Scalars['Int']['input']>;
  contractNumber?: InputMaybe<Scalars['String']['input']>;
  contractType: Scalars['String']['input'];
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  employeeEgn: Scalars['String']['input'];
  employeeName: Scalars['String']['input'];
  endDate?: InputMaybe<Scalars['Date']['input']>;
  holidayRate?: InputMaybe<Scalars['Float']['input']>;
  jobDescription?: InputMaybe<Scalars['String']['input']>;
  nightWorkRate?: InputMaybe<Scalars['Float']['input']>;
  overtimeRate?: InputMaybe<Scalars['Float']['input']>;
  paymentDay?: InputMaybe<Scalars['Int']['input']>;
  positionId?: InputMaybe<Scalars['Int']['input']>;
  probationMonths?: InputMaybe<Scalars['Int']['input']>;
  salaryCalculationType?: InputMaybe<Scalars['String']['input']>;
  startDate: Scalars['Date']['input'];
  templateId?: InputMaybe<Scalars['Int']['input']>;
  workClass?: InputMaybe<Scalars['String']['input']>;
  workHoursPerWeek?: Scalars['Int']['input'];
};

export type FefoSuggestion = {
  availableQuantity: Scalars['Decimal']['output'];
  batchId: Scalars['Int']['output'];
  batchNumber: Scalars['String']['output'];
  daysUntilExpiry: Scalars['Int']['output'];
  expiryDate: Scalars['Date']['output'];
  quantityToTake: Scalars['Decimal']['output'];
};

export type FuelType =
  | 'BENZIN'
  | 'CNG'
  | 'DIZEL'
  | 'ELECTRIC'
  | 'HYBRID'
  | 'LNG';

export type Gateway = {
  alias?: Maybe<Scalars['String']['output']>;
  companyId?: Maybe<Scalars['Int']['output']>;
  hardwareUuid: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  ipAddress?: Maybe<Scalars['String']['output']>;
  isActive: Scalars['Boolean']['output'];
  lastHeartbeat?: Maybe<Scalars['DateTime']['output']>;
  localHostname?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  registeredAt: Scalars['DateTime']['output'];
  terminalPort: Scalars['Int']['output'];
  webPort: Scalars['Int']['output'];
};

export type GatewayStats = {
  activeGateways: Scalars['Int']['output'];
  activePrinters: Scalars['Int']['output'];
  activeTerminals: Scalars['Int']['output'];
  inactiveGateways: Scalars['Int']['output'];
  totalGateways: Scalars['Int']['output'];
  totalPrinters: Scalars['Int']['output'];
  totalTerminals: Scalars['Int']['output'];
};

export type GlobalPayrollConfig = {
  annualLeaveDays: Scalars['Int']['output'];
  currency: Scalars['String']['output'];
  hasHealthInsurance: Scalars['Boolean']['output'];
  hasTaxDeduction: Scalars['Boolean']['output'];
  healthInsurancePercent: Scalars['Decimal']['output'];
  hourlyRate: Scalars['Decimal']['output'];
  id: Scalars['String']['output'];
  monthlySalary: Scalars['Decimal']['output'];
  overtimeMultiplier: Scalars['Decimal']['output'];
  qrRegenIntervalMinutes: Scalars['Int']['output'];
  standardHoursPerDay: Scalars['Int']['output'];
  taxPercent: Scalars['Decimal']['output'];
};

export type GlobalSetting = {
  key: Scalars['String']['output'];
  value: Scalars['String']['output'];
};

export type GoogleCalendarAccount = {
  email: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  syncSettings?: Maybe<GoogleCalendarSyncSettings>;
};

export type GoogleCalendarSyncSettings = {
  calendarId: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  privacyLevel: Scalars['String']['output'];
  syncDirection: Scalars['String']['output'];
  syncFrequencyMinutes: Scalars['Int']['output'];
  syncLeaveRequests: Scalars['Boolean']['output'];
  syncPublicHolidays: Scalars['Boolean']['output'];
  syncTimeLogs: Scalars['Boolean']['output'];
  syncWorkSchedules: Scalars['Boolean']['output'];
};

export type Ingredient = {
  allergens: Array<Scalars['String']['output']>;
  barcode?: Maybe<Scalars['String']['output']>;
  baselineMinStock: Scalars['Decimal']['output'];
  companyId: Scalars['Int']['output'];
  currentPrice?: Maybe<Scalars['Decimal']['output']>;
  currentStock: Scalars['Decimal']['output'];
  expiryWarningDays: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  isPerishable: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  productType: Scalars['String']['output'];
  storageZone?: Maybe<StorageZone>;
  storageZoneId?: Maybe<Scalars['Int']['output']>;
  unit: Scalars['String']['output'];
};

export type IngredientInput = {
  allergens?: Array<Scalars['String']['input']>;
  barcode?: InputMaybe<Scalars['String']['input']>;
  baselineMinStock?: Scalars['Decimal']['input'];
  companyId: Scalars['Int']['input'];
  currentPrice?: InputMaybe<Scalars['Decimal']['input']>;
  expiryWarningDays?: Scalars['Int']['input'];
  id?: InputMaybe<Scalars['Int']['input']>;
  isPerishable?: Scalars['Boolean']['input'];
  name: Scalars['String']['input'];
  productType?: Scalars['String']['input'];
  storageZoneId?: InputMaybe<Scalars['Int']['input']>;
  unit: Scalars['String']['input'];
};

export type InspectionResult =
  | 'FAILED'
  | 'PASSED'
  | 'PENDING';

export type InsuranceType =
  | 'BORDER'
  | 'CIVIL'
  | 'KASKO';

export type InventoryItem = {
  adjusted: Scalars['Boolean']['output'];
  difference?: Maybe<Scalars['Decimal']['output']>;
  foundQuantity?: Maybe<Scalars['Decimal']['output']>;
  id: Scalars['Int']['output'];
  ingredientId: Scalars['Int']['output'];
  ingredientName?: Maybe<Scalars['String']['output']>;
  ingredientUnit?: Maybe<Scalars['String']['output']>;
  sessionId: Scalars['Int']['output'];
  systemQuantity?: Maybe<Scalars['Decimal']['output']>;
};

export type InventorySession = {
  companyId: Scalars['Int']['output'];
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  items: Array<InventoryItem>;
  notes?: Maybe<Scalars['String']['output']>;
  protocolNumber?: Maybe<Scalars['String']['output']>;
  startedAt: Scalars['DateTime']['output'];
  startedBy?: Maybe<Scalars['Int']['output']>;
  status: Scalars['String']['output'];
};

export type Invoice = {
  batch?: Maybe<Batch>;
  batchId?: Maybe<Scalars['Int']['output']>;
  clientAddress?: Maybe<Scalars['String']['output']>;
  clientEik?: Maybe<Scalars['String']['output']>;
  clientName?: Maybe<Scalars['String']['output']>;
  company?: Maybe<Company>;
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  creator?: Maybe<User>;
  date: Scalars['Date']['output'];
  deliveryMethod?: Maybe<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  discountAmount: Scalars['Decimal']['output'];
  discountPercent: Scalars['Decimal']['output'];
  documentType?: Maybe<Scalars['String']['output']>;
  dueDate?: Maybe<Scalars['Date']['output']>;
  griff?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  items: Array<InvoiceItem>;
  notes?: Maybe<Scalars['String']['output']>;
  number: Scalars['String']['output'];
  paymentDate?: Maybe<Scalars['Date']['output']>;
  paymentMethod?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  subtotal: Scalars['Decimal']['output'];
  supplier?: Maybe<Supplier>;
  supplierId?: Maybe<Scalars['Int']['output']>;
  total: Scalars['Decimal']['output'];
  type: Scalars['String']['output'];
  vatAmount: Scalars['Decimal']['output'];
  vatRate: Scalars['Decimal']['output'];
};

export type InvoiceCorrection = {
  clientEik?: Maybe<Scalars['String']['output']>;
  clientName?: Maybe<Scalars['String']['output']>;
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  date: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  number: Scalars['String']['output'];
  originalInvoiceId?: Maybe<Scalars['Int']['output']>;
  reason?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  subtotal: Scalars['Decimal']['output'];
  total: Scalars['Decimal']['output'];
  type: Scalars['String']['output'];
  vatAmount: Scalars['Decimal']['output'];
  vatRate: Scalars['Decimal']['output'];
};

export type InvoiceInput = {
  batchId?: InputMaybe<Scalars['Int']['input']>;
  clientAddress?: InputMaybe<Scalars['String']['input']>;
  clientEik?: InputMaybe<Scalars['String']['input']>;
  clientName?: InputMaybe<Scalars['String']['input']>;
  companyId: Scalars['Int']['input'];
  date: Scalars['Date']['input'];
  deliveryMethod?: InputMaybe<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  discountPercent?: Scalars['Decimal']['input'];
  documentType?: InputMaybe<Scalars['String']['input']>;
  dueDate?: InputMaybe<Scalars['Date']['input']>;
  griff?: InputMaybe<Scalars['String']['input']>;
  items: Array<InvoiceItemInput>;
  notes?: InputMaybe<Scalars['String']['input']>;
  paymentDate?: InputMaybe<Scalars['Date']['input']>;
  paymentMethod?: InputMaybe<Scalars['String']['input']>;
  status?: Scalars['String']['input'];
  supplierId?: InputMaybe<Scalars['Int']['input']>;
  type: Scalars['String']['input'];
  vatRate?: Scalars['Decimal']['input'];
};

export type InvoiceItem = {
  batch?: Maybe<Batch>;
  batchId?: Maybe<Scalars['Int']['output']>;
  batchNumber?: Maybe<Scalars['String']['output']>;
  discountPercent: Scalars['Decimal']['output'];
  expirationDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['Int']['output'];
  ingredient?: Maybe<Ingredient>;
  ingredientId?: Maybe<Scalars['Int']['output']>;
  invoiceId: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  quantity: Scalars['Decimal']['output'];
  total: Scalars['Decimal']['output'];
  unit: Scalars['String']['output'];
  unitPrice: Scalars['Decimal']['output'];
  unitPriceWithVat?: Maybe<Scalars['Decimal']['output']>;
};

export type InvoiceItemInput = {
  batchId?: InputMaybe<Scalars['Int']['input']>;
  batchNumber?: InputMaybe<Scalars['String']['input']>;
  discountPercent?: Scalars['Decimal']['input'];
  expirationDate?: InputMaybe<Scalars['String']['input']>;
  ingredientId?: InputMaybe<Scalars['Int']['input']>;
  name: Scalars['String']['input'];
  quantity: Scalars['Decimal']['input'];
  unit?: Scalars['String']['input'];
  unitPrice: Scalars['Decimal']['input'];
  unitPriceWithVat?: InputMaybe<Scalars['Decimal']['input']>;
};

export type KioskSecuritySettings = {
  requireGps: Scalars['Boolean']['output'];
  requireSameNetwork: Scalars['Boolean']['output'];
};

export type LabelData = {
  allergens: Array<Scalars['String']['output']>;
  batchNumber: Scalars['String']['output'];
  expiryDate: Scalars['Date']['output'];
  productName: Scalars['String']['output'];
  productionDate: Scalars['DateTime']['output'];
  qrCodeContent: Scalars['String']['output'];
  quantity: Scalars['String']['output'];
  storageConditions?: Maybe<Scalars['String']['output']>;
};

export type LatenessStat = {
  count: Scalars['Int']['output'];
  userName: Scalars['String']['output'];
};

export type LeaveBalance = {
  id: Scalars['Int']['output'];
  totalDays: Scalars['Int']['output'];
  usedDays: Scalars['Int']['output'];
  user: User;
  userId: Scalars['Int']['output'];
  year: Scalars['Int']['output'];
};

export type LeaveRequest = {
  adminComment?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  endDate: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  leaveType: Scalars['String']['output'];
  reason?: Maybe<Scalars['String']['output']>;
  startDate: Scalars['Date']['output'];
  status: Scalars['String']['output'];
  user: User;
  userId: Scalars['Int']['output'];
};

export type LeaveRequestInput = {
  endDate: Scalars['Date']['input'];
  leaveType: Scalars['String']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
  startDate: Scalars['Date']['input'];
};

export type ManagementStats = {
  latenessByUser: Array<LatenessStat>;
  overtimeByMonth: Array<OvertimeStat>;
};

export type Module = {
  code: Scalars['String']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isEnabled: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type MonthlySummaryType = {
  cashBalance: Scalars['Float']['output'];
  cashExpense: Scalars['Float']['output'];
  cashIncome: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  incomingInvoicesCount: Scalars['Int']['output'];
  incomingInvoicesTotal: Scalars['Float']['output'];
  invoicesCount: Scalars['Int']['output'];
  invoicesTotal: Scalars['Float']['output'];
  month: Scalars['Int']['output'];
  outgoingInvoicesCount: Scalars['Int']['output'];
  outgoingInvoicesTotal: Scalars['Float']['output'];
  overdueInvoicesCount: Scalars['Int']['output'];
  paidInvoicesCount: Scalars['Int']['output'];
  unpaidInvoicesCount: Scalars['Int']['output'];
  vatCollected: Scalars['Float']['output'];
  vatPaid: Scalars['Float']['output'];
  year: Scalars['Int']['output'];
};

export type MonthlyWorkDays = {
  daysCount: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  month: Scalars['Int']['output'];
  year: Scalars['Int']['output'];
};

export type MonthlyWorkDaysInput = {
  daysCount: Scalars['Int']['input'];
  month: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};

export type Mutation = {
  addBatch: Batch;
  addBonus: Bonus;
  addInventoryItem: InventoryItem;
  addSectionToAnnexTemplate: AnnexTemplateSection;
  addSectionToContractTemplate: ContractTemplateSection;
  adminClockIn: TimeLog;
  adminClockOut: TimeLog;
  applyScheduleTemplate: Scalars['Boolean']['output'];
  approveBusinessTrip: BusinessTrip;
  approveLeave: LeaveRequest;
  approveSwap: ShiftSwapRequest;
  assignRoleToUser: Scalars['Boolean']['output'];
  assignZoneToUser: Scalars['Boolean']['output'];
  attachLeaveDocument: LeaveRequest;
  autoConsumeFefo: Array<StockConsumptionLog>;
  autoMatchBankTransactions: AutoMatchResult;
  bulkAddBatches: Array<Batch>;
  bulkEmergencyAction: Scalars['Boolean']['output'];
  bulkMarkPayslipsAsPaid: Array<Payslip>;
  bulkSetSchedule: Scalars['Boolean']['output'];
  bulkUpdateUserAccess: Scalars['Boolean']['output'];
  calculateRecipeCost: RecipeCostResult;
  changePassword: Scalars['Boolean']['output'];
  clockIn: TimeLog;
  clockOut: TimeLog;
  completeInventorySession: InventorySession;
  confirmProductionOrder: ProductionOrder;
  consumeFromBatch: Batch;
  convertProformaToInvoice: Invoice;
  createAccessCode: AccessCode;
  createAccessDoor: AccessDoor;
  createAccessZone: AccessZone;
  createAccount: Account;
  createAccountingEntry: AccountingEntry;
  createAdvancePayment: AdvancePayment;
  createAnnexTemplate: AnnexTemplate;
  createBankAccount: BankAccount;
  createBankTransaction: BankTransaction;
  createBusinessTrip: BusinessTrip;
  createCashJournalEntry: CashJournalEntryType;
  createCashReceipt: CashReceipt;
  createClauseTemplate: ClauseTemplate;
  createCompany: Company;
  createContractAnnex: ContractAnnex;
  createContractTemplate: ContractTemplate;
  createCostCenter: VehicleCostCenter;
  createCreditNote: InvoiceCorrection;
  createDepartment: Department;
  createEmploymentContract: EmploymentContract;
  createIngredient: Ingredient;
  createInvoice: Invoice;
  createInvoiceCorrection: InvoiceCorrection;
  createInvoiceFromBatch: Invoice;
  createManualTimeLog: TimeLog;
  createNightWorkBonus: NightWorkBonus;
  createOvertimeWork: OvertimeWork;
  createPosition: Position;
  createProductionOrder: ProductionOrder;
  createProformaInvoice: ProformaInvoice;
  createQuickSale: ProductionOrder;
  createRecipe: Recipe;
  createRole: Role;
  createScheduleTemplate: ScheduleTemplate;
  createServiceLoan: ServiceLoan;
  createShift: Shift;
  createStorageZone: StorageZone;
  createSupplier: Supplier;
  createSwapRequest: ShiftSwapRequest;
  createTimeLog: TimeLog;
  createUser: User;
  createVehicle: Vehicle;
  createVehicleDriver: VehicleDriver;
  createVehicleFuel: VehicleFuel;
  createVehicleInspection: VehicleInspection;
  createVehicleInsurance: VehicleInsurance;
  createVehicleMileage: VehicleMileage;
  createVehicleRepair: VehicleRepair;
  createVehicleTrip: VehicleTrip;
  createWorkExperience: WorkExperience;
  createWorkstation: Workstation;
  deleteAccessCode: Scalars['Boolean']['output'];
  deleteAccessDoor: Scalars['Boolean']['output'];
  deleteAccessZone: Scalars['Boolean']['output'];
  deleteAccount: Scalars['Boolean']['output'];
  deleteAccountingEntry: Scalars['Boolean']['output'];
  deleteAnnexTemplate: Scalars['Boolean']['output'];
  deleteBankAccount: Scalars['Boolean']['output'];
  deleteBankTransaction: Scalars['Boolean']['output'];
  deleteCashJournalEntry: Scalars['Boolean']['output'];
  deleteCashReceipt: Scalars['Boolean']['output'];
  deleteClauseTemplate: Scalars['Boolean']['output'];
  deleteContractTemplate: Scalars['Boolean']['output'];
  deleteCostCenter: Scalars['Boolean']['output'];
  deleteInvoice: Scalars['Boolean']['output'];
  deleteLeaveRequest: Scalars['Boolean']['output'];
  deletePosition: Scalars['Boolean']['output'];
  deleteRecipe: Scalars['Boolean']['output'];
  deleteRole: Scalars['Boolean']['output'];
  deleteScheduleTemplate: Scalars['Boolean']['output'];
  deleteSectionFromAnnexTemplate: Scalars['Boolean']['output'];
  deleteSectionFromContractTemplate: Scalars['Boolean']['output'];
  deleteShift: Scalars['Boolean']['output'];
  deleteTerminal: Scalars['Boolean']['output'];
  deleteTimeLog: Scalars['Boolean']['output'];
  deleteUser: Scalars['Boolean']['output'];
  deleteVehicle: Scalars['Boolean']['output'];
  deleteVehicleDriver: Scalars['Boolean']['output'];
  deleteVehicleFuel: Scalars['Boolean']['output'];
  deleteVehicleInspection: Scalars['Boolean']['output'];
  deleteVehicleInsurance: Scalars['Boolean']['output'];
  deleteVehicleMileage: Scalars['Boolean']['output'];
  deleteVehicleRepair: Scalars['Boolean']['output'];
  deleteVehicleTrip: Scalars['Boolean']['output'];
  deleteWorkSchedule: Scalars['Boolean']['output'];
  disconnectGoogleCalendar: Scalars['Boolean']['output'];
  generateAnnualInsuranceReport: Scalars['JSONScalar']['output'];
  generateContractNumber: Scalars['String']['output'];
  generateDailySummary: DailySummaryType;
  generateIncomeReportByType: Scalars['JSONScalar']['output'];
  generateLabel: LabelData;
  generateMonthlyDeclaration: Scalars['JSONScalar']['output'];
  generateMonthlySummary: MonthlySummaryType;
  generateMyPayslip: Payslip;
  generatePayslip: Payslip;
  generateSaftFile: SaftFileResult;
  generateSepaXml: Scalars['String']['output'];
  generateServiceBookExport: Scalars['JSONScalar']['output'];
  generateVatRegister: VatRegister;
  generateYearlySummary: YearlySummaryType;
  getAnnexPdfUrl: Scalars['String']['output'];
  getContractPdfUrl: Scalars['String']['output'];
  getInvoicePdfUrl: Scalars['String']['output'];
  getScrapLogs: Array<ProductionScrapLog>;
  invalidateUserSession: Scalars['Boolean']['output'];
  linkEmploymentContractToUser: EmploymentContract;
  markPayslipAsPaid: Payslip;
  markTaskScrap: ProductionTask;
  matchBankTransaction?: Maybe<BankTransaction>;
  openDoor: Scalars['Boolean']['output'];
  reassignTaskWorkstation: ProductionTask;
  recalculateAllRecipeCosts: Array<RecalculateResult>;
  recalculateProductionDeadline: ProductionOrder;
  regenerateMyQrCode: Scalars['String']['output'];
  rejectContractAnnex: ContractAnnex;
  rejectLeave: LeaveRequest;
  removeBonus: Scalars['Boolean']['output'];
  removeZoneFromUser: Scalars['Boolean']['output'];
  requestLeave: LeaveRequest;
  respondToSwap: ShiftSwapRequest;
  restoreContractTemplateVersion: ContractTemplate;
  revokeAccessCode: Scalars['Boolean']['output'];
  saveNotificationSetting: NotificationSetting;
  scrapTask: ProductionTask;
  setGlobalSetting: GlobalSetting;
  setMonthlyWorkDays: MonthlyWorkDays;
  setWorkSchedule: WorkSchedule;
  signContractAnnex: ContractAnnex;
  signEmploymentContract: EmploymentContract;
  startInventorySession: InventorySession;
  syncGatewayConfig: Scalars['Boolean']['output'];
  syncHolidays: Scalars['Int']['output'];
  syncOrthodoxHolidays: Scalars['Int']['output'];
  testNotification: Scalars['Boolean']['output'];
  triggerDoorRemote: Scalars['Boolean']['output'];
  unmatchBankTransaction?: Maybe<BankTransaction>;
  updateAccessZone: AccessZone;
  updateAccount?: Maybe<Account>;
  updateBankAccount?: Maybe<BankAccount>;
  updateBankTransaction?: Maybe<BankTransaction>;
  updateBatch: Batch;
  updateBatchStatus: Batch;
  updateCashReceipt?: Maybe<CashReceipt>;
  updateClauseTemplate: ClauseTemplate;
  updateCompany: Company;
  updateCompanyAccountingSettings: Company;
  updateContractTemplate: ContractTemplate;
  updateCostCenter: VehicleCostCenter;
  updateDepartment: Department;
  updateDoorTerminal: AccessDoor;
  updateGateway: Gateway;
  updateGlobalPayrollConfig: GlobalPayrollConfig;
  updateGoogleCalendarSettings: Scalars['Boolean']['output'];
  updateIngredient: Ingredient;
  updateInvoice: Invoice;
  updateKioskSecuritySettings: Scalars['Boolean']['output'];
  updateLeaveRequestStatus: LeaveRequest;
  updateOfficeLocation: OfficeLocation;
  updatePasswordSettings: PasswordSettings;
  updatePayrollLegalSettings: PayrollLegalSettings;
  updatePosition: Position;
  updateProductionOrderQuantity: ProductionOrder;
  updateProductionOrderStatus: ProductionOrder;
  updateProductionTaskStatus: ProductionTask;
  updateRecipePrice: Recipe;
  updateRole: Role;
  updateSectionInAnnexTemplate: AnnexTemplateSection;
  updateSectionInContractTemplate: ContractTemplateSection;
  updateSecurityConfig: Scalars['Boolean']['output'];
  updateShift: Shift;
  updateSmtpSettings: SmtpSettings;
  updateStorageZone: StorageZone;
  updateSupplier: Supplier;
  updateTerminal: Terminal;
  updateTimeLog: TimeLog;
  updateUser: User;
  updateVehicle: Vehicle;
  updateVehicleDriver: VehicleDriver;
  updateVehicleFuel: VehicleFuel;
  updateVehicleInspection: VehicleInspection;
  updateVehicleInsurance: VehicleInsurance;
  updateVehicleMileage: VehicleMileage;
  updateVehicleRepair: VehicleRepair;
  updateVehicleTrip: VehicleTrip;
  validateSaftXml: SaftValidationResult;
};


export type MutationAddBatchArgs = {
  input: BatchInput;
};


export type MutationAddBonusArgs = {
  input: BonusCreateInput;
};


export type MutationAddInventoryItemArgs = {
  foundQuantity: Scalars['Float']['input'];
  ingredientId: Scalars['Int']['input'];
  sessionId: Scalars['Int']['input'];
};


export type MutationAddSectionToAnnexTemplateArgs = {
  section: AnnexTemplateSectionInput;
  templateId: Scalars['Int']['input'];
};


export type MutationAddSectionToContractTemplateArgs = {
  section: ContractTemplateSectionInput;
  templateId: Scalars['Int']['input'];
};


export type MutationAdminClockInArgs = {
  customTime?: InputMaybe<Scalars['DateTime']['input']>;
  userId: Scalars['Int']['input'];
};


export type MutationAdminClockOutArgs = {
  customTime?: InputMaybe<Scalars['DateTime']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  userId: Scalars['Int']['input'];
};


export type MutationApplyScheduleTemplateArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
  templateId: Scalars['Int']['input'];
  userIds: Array<Scalars['Int']['input']>;
};


export type MutationApproveBusinessTripArgs = {
  approved: Scalars['Boolean']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  tripId: Scalars['Int']['input'];
};


export type MutationApproveLeaveArgs = {
  adminComment: Scalars['String']['input'];
  employerTopUp?: Scalars['Boolean']['input'];
  requestId: Scalars['Int']['input'];
};


export type MutationApproveSwapArgs = {
  approve: Scalars['Boolean']['input'];
  swapId: Scalars['Int']['input'];
};


export type MutationAssignRoleToUserArgs = {
  companyId: Scalars['Int']['input'];
  roleId: Scalars['Int']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationAssignZoneToUserArgs = {
  userId: Scalars['Int']['input'];
  zoneId: Scalars['Int']['input'];
};


export type MutationAttachLeaveDocumentArgs = {
  file: Scalars['Upload']['input'];
  requestId: Scalars['Int']['input'];
};


export type MutationAutoConsumeFefoArgs = {
  ingredientId: Scalars['Int']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Decimal']['input'];
  reason: Scalars['String']['input'];
};


export type MutationAutoMatchBankTransactionsArgs = {
  bankAccountId: Scalars['Int']['input'];
};


export type MutationBulkAddBatchesArgs = {
  createInvoice: Scalars['Boolean']['input'];
  date: Scalars['Date']['input'];
  invoiceNumber: Scalars['String']['input'];
  items: Array<BatchInput>;
  supplierId: Scalars['Int']['input'];
};


export type MutationBulkEmergencyActionArgs = {
  action: Scalars['String']['input'];
};


export type MutationBulkMarkPayslipsAsPaidArgs = {
  paymentDate?: InputMaybe<Scalars['DateTime']['input']>;
  paymentMethod?: Scalars['String']['input'];
  payslipIds: Array<Scalars['Int']['input']>;
};


export type MutationBulkSetScheduleArgs = {
  daysOfWeek: Array<Scalars['Int']['input']>;
  endDate: Scalars['Date']['input'];
  shiftId: Scalars['Int']['input'];
  startDate: Scalars['Date']['input'];
  userIds: Array<Scalars['Int']['input']>;
};


export type MutationBulkUpdateUserAccessArgs = {
  action: Scalars['String']['input'];
  userIds: Array<Scalars['Int']['input']>;
  zoneIds: Array<Scalars['Int']['input']>;
};


export type MutationCalculateRecipeCostArgs = {
  recipeId: Scalars['Int']['input'];
};


export type MutationChangePasswordArgs = {
  newPassword: Scalars['String']['input'];
  oldPassword: Scalars['String']['input'];
};


export type MutationClockInArgs = {
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
};


export type MutationClockOutArgs = {
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
};


export type MutationCompleteInventorySessionArgs = {
  sessionId: Scalars['Int']['input'];
};


export type MutationConfirmProductionOrderArgs = {
  id: Scalars['Int']['input'];
};


export type MutationConsumeFromBatchArgs = {
  batchId: Scalars['Int']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Decimal']['input'];
  reason: Scalars['String']['input'];
};


export type MutationConvertProformaToInvoiceArgs = {
  invoiceType: Scalars['String']['input'];
  proformaId: Scalars['Int']['input'];
};


export type MutationCreateAccessCodeArgs = {
  input: AccessCodeInput;
};


export type MutationCreateAccessDoorArgs = {
  input: AccessDoorInput;
};


export type MutationCreateAccessZoneArgs = {
  input: AccessZoneInput;
};


export type MutationCreateAccountArgs = {
  input: AccountInput;
};


export type MutationCreateAccountingEntryArgs = {
  input: AccountingEntryInput;
};


export type MutationCreateAdvancePaymentArgs = {
  amount: Scalars['Float']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  paymentDate: Scalars['Date']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationCreateAnnexTemplateArgs = {
  changeType: Scalars['String']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  newBaseSalary?: InputMaybe<Scalars['Float']['input']>;
  newHolidayRate?: InputMaybe<Scalars['Float']['input']>;
  newNightWorkRate?: InputMaybe<Scalars['Float']['input']>;
  newOvertimeRate?: InputMaybe<Scalars['Float']['input']>;
  newWorkHoursPerWeek?: InputMaybe<Scalars['Int']['input']>;
};


export type MutationCreateBankAccountArgs = {
  input: BankAccountInput;
};


export type MutationCreateBankTransactionArgs = {
  input: BankTransactionInput;
};


export type MutationCreateBusinessTripArgs = {
  accommodation?: Scalars['Float']['input'];
  dailyAllowance?: Scalars['Float']['input'];
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  destination: Scalars['String']['input'];
  endDate: Scalars['Date']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  otherExpenses?: Scalars['Float']['input'];
  periodId?: InputMaybe<Scalars['Int']['input']>;
  startDate: Scalars['Date']['input'];
  transport?: Scalars['Float']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationCreateCashJournalEntryArgs = {
  input: CashJournalEntryInput;
};


export type MutationCreateCashReceiptArgs = {
  input: CashReceiptInput;
};


export type MutationCreateClauseTemplateArgs = {
  category: Scalars['String']['input'];
  content: Scalars['String']['input'];
  title: Scalars['String']['input'];
};


export type MutationCreateCompanyArgs = {
  input: CompanyCreateInput;
};


export type MutationCreateContractAnnexArgs = {
  annexNumber?: InputMaybe<Scalars['String']['input']>;
  baseSalary?: InputMaybe<Scalars['Decimal']['input']>;
  contractId: Scalars['Int']['input'];
  effectiveDate: Scalars['Date']['input'];
  holidayRate?: InputMaybe<Scalars['Float']['input']>;
  nightWorkRate?: InputMaybe<Scalars['Float']['input']>;
  overtimeRate?: InputMaybe<Scalars['Float']['input']>;
  positionId?: InputMaybe<Scalars['Int']['input']>;
  workHoursPerWeek?: InputMaybe<Scalars['Int']['input']>;
};


export type MutationCreateContractTemplateArgs = {
  baseSalary?: InputMaybe<Scalars['Float']['input']>;
  clauseIds?: InputMaybe<Scalars['String']['input']>;
  contractType: Scalars['String']['input'];
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  holidayRate: Scalars['Float']['input'];
  name: Scalars['String']['input'];
  nightWorkRate: Scalars['Float']['input'];
  overtimeRate: Scalars['Float']['input'];
  paymentDay: Scalars['Int']['input'];
  positionId?: InputMaybe<Scalars['Int']['input']>;
  probationMonths: Scalars['Int']['input'];
  salaryCalculationType: Scalars['String']['input'];
  workClass?: InputMaybe<Scalars['String']['input']>;
  workHoursPerWeek: Scalars['Int']['input'];
};


export type MutationCreateCostCenterArgs = {
  input: CostCenterInput;
};


export type MutationCreateCreditNoteArgs = {
  correctionDate: Scalars['Date']['input'];
  originalInvoiceId: Scalars['Int']['input'];
  reason: Scalars['String']['input'];
};


export type MutationCreateDepartmentArgs = {
  input: DepartmentCreateInput;
};


export type MutationCreateEmploymentContractArgs = {
  input: EmploymentContractCreateInput;
};


export type MutationCreateIngredientArgs = {
  input: IngredientInput;
};


export type MutationCreateInvoiceArgs = {
  invoiceData: InvoiceInput;
};


export type MutationCreateInvoiceCorrectionArgs = {
  correctionDate: Scalars['Date']['input'];
  correctionType: Scalars['String']['input'];
  createNewInvoice?: Scalars['Boolean']['input'];
  originalInvoiceId: Scalars['Int']['input'];
  reason: Scalars['String']['input'];
};


export type MutationCreateInvoiceFromBatchArgs = {
  batchId: Scalars['Int']['input'];
};


export type MutationCreateManualTimeLogArgs = {
  breakDurationMinutes?: Scalars['Int']['input'];
  endTime: Scalars['DateTime']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  startTime: Scalars['DateTime']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationCreateNightWorkBonusArgs = {
  date: Scalars['Date']['input'];
  hourlyRate: Scalars['Float']['input'];
  hours: Scalars['Float']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  periodId?: InputMaybe<Scalars['Int']['input']>;
  userId: Scalars['Int']['input'];
};


export type MutationCreateOvertimeWorkArgs = {
  date: Scalars['Date']['input'];
  hourlyRate: Scalars['Float']['input'];
  hours: Scalars['Float']['input'];
  multiplier?: Scalars['Float']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  periodId?: InputMaybe<Scalars['Int']['input']>;
  userId: Scalars['Int']['input'];
};


export type MutationCreatePositionArgs = {
  departmentId: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};


export type MutationCreateProductionOrderArgs = {
  input: ProductionOrderInput;
};


export type MutationCreateProformaInvoiceArgs = {
  clientAddress?: InputMaybe<Scalars['String']['input']>;
  clientEik?: InputMaybe<Scalars['String']['input']>;
  clientName: Scalars['String']['input'];
  date: Scalars['Date']['input'];
  discountPercent: Scalars['Float']['input'];
  items: Array<InvoiceItemInput>;
  notes?: InputMaybe<Scalars['String']['input']>;
  vatRate: Scalars['Float']['input'];
};


export type MutationCreateQuickSaleArgs = {
  input: QuickSaleInput;
};


export type MutationCreateRecipeArgs = {
  input: RecipeInput;
};


export type MutationCreateRoleArgs = {
  input: RoleCreateInput;
};


export type MutationCreateScheduleTemplateArgs = {
  description?: InputMaybe<Scalars['String']['input']>;
  items: Array<ScheduleTemplateItemInput>;
  name: Scalars['String']['input'];
};


export type MutationCreateServiceLoanArgs = {
  description: Scalars['String']['input'];
  installmentsCount: Scalars['Int']['input'];
  startDate: Scalars['Date']['input'];
  totalAmount: Scalars['Float']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationCreateShiftArgs = {
  endTime: Scalars['Time']['input'];
  name: Scalars['String']['input'];
  startTime: Scalars['Time']['input'];
};


export type MutationCreateStorageZoneArgs = {
  input: StorageZoneInput;
};


export type MutationCreateSupplierArgs = {
  input: SupplierInput;
};


export type MutationCreateSwapRequestArgs = {
  requestorScheduleId: Scalars['Int']['input'];
  targetScheduleId: Scalars['Int']['input'];
  targetUserId: Scalars['Int']['input'];
};


export type MutationCreateTimeLogArgs = {
  breakDurationMinutes?: Scalars['Int']['input'];
  endTime?: InputMaybe<Scalars['DateTime']['input']>;
  isManual?: Scalars['Boolean']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  startTime: Scalars['DateTime']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationCreateUserArgs = {
  userInput: UserCreateInput;
};


export type MutationCreateVehicleArgs = {
  input: VehicleCreateInput;
};


export type MutationCreateVehicleDriverArgs = {
  input: VehicleDriverInput;
};


export type MutationCreateVehicleFuelArgs = {
  input: VehicleFuelInput;
};


export type MutationCreateVehicleInspectionArgs = {
  input: VehicleInspectionInput;
};


export type MutationCreateVehicleInsuranceArgs = {
  input: VehicleInsuranceInput;
};


export type MutationCreateVehicleMileageArgs = {
  input: VehicleMileageInput;
};


export type MutationCreateVehicleRepairArgs = {
  input: VehicleRepairInput;
};


export type MutationCreateVehicleTripArgs = {
  input: VehicleTripInput;
};


export type MutationCreateWorkExperienceArgs = {
  classLevel?: InputMaybe<Scalars['String']['input']>;
  companyName: Scalars['String']['input'];
  endDate?: InputMaybe<Scalars['Date']['input']>;
  isCurrent?: Scalars['Boolean']['input'];
  months?: Scalars['Int']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  position?: InputMaybe<Scalars['String']['input']>;
  startDate: Scalars['Date']['input'];
  userId: Scalars['Int']['input'];
  years?: Scalars['Int']['input'];
};


export type MutationCreateWorkstationArgs = {
  companyId: Scalars['Int']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
};


export type MutationDeleteAccessCodeArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteAccessDoorArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteAccessZoneArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteAccountArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteAccountingEntryArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteAnnexTemplateArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteBankAccountArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteBankTransactionArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteCashJournalEntryArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteCashReceiptArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteClauseTemplateArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteContractTemplateArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteCostCenterArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteInvoiceArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteLeaveRequestArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeletePositionArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteRecipeArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteRoleArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteScheduleTemplateArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteSectionFromAnnexTemplateArgs = {
  sectionId: Scalars['Int']['input'];
};


export type MutationDeleteSectionFromContractTemplateArgs = {
  sectionId: Scalars['Int']['input'];
};


export type MutationDeleteShiftArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteTerminalArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteTimeLogArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteUserArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleDriverArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleFuelArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleInspectionArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleInsuranceArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleMileageArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleRepairArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteVehicleTripArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteWorkScheduleArgs = {
  id: Scalars['Int']['input'];
};


export type MutationGenerateAnnualInsuranceReportArgs = {
  companyId: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type MutationGenerateContractNumberArgs = {
  companyId: Scalars['Int']['input'];
};


export type MutationGenerateDailySummaryArgs = {
  date: Scalars['String']['input'];
};


export type MutationGenerateIncomeReportByTypeArgs = {
  companyId: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type MutationGenerateLabelArgs = {
  orderId: Scalars['Int']['input'];
};


export type MutationGenerateMonthlyDeclarationArgs = {
  companyId: Scalars['Int']['input'];
  month: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type MutationGenerateMonthlySummaryArgs = {
  month: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type MutationGenerateMyPayslipArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
};


export type MutationGeneratePayslipArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationGenerateSaftFileArgs = {
  companyId: Scalars['Int']['input'];
  month: Scalars['Int']['input'];
  saftType?: InputMaybe<Scalars['String']['input']>;
  year: Scalars['Int']['input'];
};


export type MutationGenerateSepaXmlArgs = {
  companyId: Scalars['Int']['input'];
  executionDate?: InputMaybe<Scalars['Date']['input']>;
  periodEnd: Scalars['Date']['input'];
  periodStart: Scalars['Date']['input'];
};


export type MutationGenerateServiceBookExportArgs = {
  companyId: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type MutationGenerateVatRegisterArgs = {
  input: VatRegisterInput;
};


export type MutationGenerateYearlySummaryArgs = {
  year: Scalars['Int']['input'];
};


export type MutationGetAnnexPdfUrlArgs = {
  annexId: Scalars['Int']['input'];
};


export type MutationGetContractPdfUrlArgs = {
  contractId: Scalars['Int']['input'];
};


export type MutationGetInvoicePdfUrlArgs = {
  invoiceId: Scalars['Int']['input'];
};


export type MutationGetScrapLogsArgs = {
  taskId: Scalars['Int']['input'];
};


export type MutationInvalidateUserSessionArgs = {
  sessionId: Scalars['Int']['input'];
};


export type MutationLinkEmploymentContractToUserArgs = {
  contractId: Scalars['Int']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationMarkPayslipAsPaidArgs = {
  paymentDate?: InputMaybe<Scalars['DateTime']['input']>;
  paymentMethod?: Scalars['String']['input'];
  payslipId: Scalars['Int']['input'];
};


export type MutationMarkTaskScrapArgs = {
  id: Scalars['Int']['input'];
};


export type MutationMatchBankTransactionArgs = {
  invoiceId: Scalars['Int']['input'];
  transactionId: Scalars['Int']['input'];
};


export type MutationOpenDoorArgs = {
  id: Scalars['Int']['input'];
};


export type MutationReassignTaskWorkstationArgs = {
  newWorkstationId: Scalars['Int']['input'];
  taskId: Scalars['Int']['input'];
};


export type MutationRecalculateProductionDeadlineArgs = {
  orderId: Scalars['Int']['input'];
};


export type MutationRejectContractAnnexArgs = {
  annexId: Scalars['Int']['input'];
  reason: Scalars['String']['input'];
};


export type MutationRejectLeaveArgs = {
  adminComment: Scalars['String']['input'];
  requestId: Scalars['Int']['input'];
};


export type MutationRemoveBonusArgs = {
  id: Scalars['Int']['input'];
};


export type MutationRemoveZoneFromUserArgs = {
  userId: Scalars['Int']['input'];
  zoneId: Scalars['Int']['input'];
};


export type MutationRequestLeaveArgs = {
  leaveInput: LeaveRequestInput;
};


export type MutationRespondToSwapArgs = {
  accept: Scalars['Boolean']['input'];
  swapId: Scalars['Int']['input'];
};


export type MutationRestoreContractTemplateVersionArgs = {
  versionId: Scalars['Int']['input'];
};


export type MutationRevokeAccessCodeArgs = {
  id: Scalars['Int']['input'];
};


export type MutationSaveNotificationSettingArgs = {
  settingData: NotificationSettingInput;
};


export type MutationScrapTaskArgs = {
  input: ScrapTaskInput;
};


export type MutationSetGlobalSettingArgs = {
  key: Scalars['String']['input'];
  value: Scalars['String']['input'];
};


export type MutationSetMonthlyWorkDaysArgs = {
  input: MonthlyWorkDaysInput;
};


export type MutationSetWorkScheduleArgs = {
  date: Scalars['Date']['input'];
  shiftId: Scalars['Int']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationSignContractAnnexArgs = {
  annexId: Scalars['Int']['input'];
  role?: Scalars['String']['input'];
};


export type MutationSignEmploymentContractArgs = {
  id: Scalars['Int']['input'];
};


export type MutationSyncGatewayConfigArgs = {
  direction: Scalars['String']['input'];
  id: Scalars['Int']['input'];
};


export type MutationSyncHolidaysArgs = {
  year: Scalars['Int']['input'];
};


export type MutationSyncOrthodoxHolidaysArgs = {
  year: Scalars['Int']['input'];
};


export type MutationTestNotificationArgs = {
  eventType: Scalars['String']['input'];
};


export type MutationTriggerDoorRemoteArgs = {
  id: Scalars['Int']['input'];
};


export type MutationUnmatchBankTransactionArgs = {
  transactionId: Scalars['Int']['input'];
};


export type MutationUpdateAccessZoneArgs = {
  id: Scalars['Int']['input'];
  input: AccessZoneInput;
};


export type MutationUpdateAccountArgs = {
  id: Scalars['Int']['input'];
  input: AccountUpdateInput;
};


export type MutationUpdateBankAccountArgs = {
  id: Scalars['Int']['input'];
  input: BankAccountUpdateInput;
};


export type MutationUpdateBankTransactionArgs = {
  id: Scalars['Int']['input'];
  input: BankTransactionUpdateInput;
};


export type MutationUpdateBatchArgs = {
  input: BatchInput;
};


export type MutationUpdateBatchStatusArgs = {
  id: Scalars['Int']['input'];
  status: Scalars['String']['input'];
};


export type MutationUpdateCashReceiptArgs = {
  id: Scalars['Int']['input'];
  input: CashReceiptUpdateInput;
};


export type MutationUpdateClauseTemplateArgs = {
  category: Scalars['String']['input'];
  content: Scalars['String']['input'];
  id: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};


export type MutationUpdateCompanyArgs = {
  input: CompanyUpdateInput;
};


export type MutationUpdateCompanyAccountingSettingsArgs = {
  input: CompanyAccountingSettingsInput;
};


export type MutationUpdateContractTemplateArgs = {
  changeNote: Scalars['String']['input'];
  contractType: Scalars['String']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  holidayRate: Scalars['Float']['input'];
  id: Scalars['Int']['input'];
  name: Scalars['String']['input'];
  nightWorkRate: Scalars['Float']['input'];
  overtimeRate: Scalars['Float']['input'];
  paymentDay: Scalars['Int']['input'];
  probationMonths: Scalars['Int']['input'];
  salaryCalculationType: Scalars['String']['input'];
  workClass?: InputMaybe<Scalars['String']['input']>;
  workHoursPerWeek: Scalars['Int']['input'];
};


export type MutationUpdateCostCenterArgs = {
  input: UpdateCostCenterInput;
};


export type MutationUpdateDepartmentArgs = {
  input: DepartmentUpdateInput;
};


export type MutationUpdateDoorTerminalArgs = {
  id: Scalars['Int']['input'];
  terminalId?: InputMaybe<Scalars['String']['input']>;
  terminalMode?: InputMaybe<Scalars['String']['input']>;
};


export type MutationUpdateGatewayArgs = {
  alias?: InputMaybe<Scalars['String']['input']>;
  companyId?: InputMaybe<Scalars['Int']['input']>;
  id: Scalars['Int']['input'];
};


export type MutationUpdateGlobalPayrollConfigArgs = {
  annualLeaveDays: Scalars['Int']['input'];
  currency: Scalars['String']['input'];
  hasHealthInsurance: Scalars['Boolean']['input'];
  hasTaxDeduction: Scalars['Boolean']['input'];
  healthInsurancePercent: Scalars['Decimal']['input'];
  hourlyRate: Scalars['Decimal']['input'];
  monthlySalary: Scalars['Decimal']['input'];
  overtimeMultiplier: Scalars['Decimal']['input'];
  qrRegenIntervalMinutes: Scalars['Int']['input'];
  standardHoursPerDay: Scalars['Int']['input'];
  taxPercent: Scalars['Decimal']['input'];
};


export type MutationUpdateGoogleCalendarSettingsArgs = {
  privacyLevel: Scalars['String']['input'];
  syncLeaveRequests: Scalars['Boolean']['input'];
  syncPublicHolidays: Scalars['Boolean']['input'];
  syncTimeLogs: Scalars['Boolean']['input'];
  syncWorkSchedules: Scalars['Boolean']['input'];
};


export type MutationUpdateIngredientArgs = {
  input: IngredientInput;
};


export type MutationUpdateInvoiceArgs = {
  id: Scalars['Int']['input'];
  invoiceData: InvoiceInput;
};


export type MutationUpdateKioskSecuritySettingsArgs = {
  requireGps: Scalars['Boolean']['input'];
  requireSameNetwork: Scalars['Boolean']['input'];
};


export type MutationUpdateLeaveRequestStatusArgs = {
  input: UpdateLeaveRequestStatusInput;
};


export type MutationUpdateOfficeLocationArgs = {
  entryEnabled: Scalars['Boolean']['input'];
  exitEnabled: Scalars['Boolean']['input'];
  latitude: Scalars['Float']['input'];
  longitude: Scalars['Float']['input'];
  radius: Scalars['Int']['input'];
};


export type MutationUpdatePasswordSettingsArgs = {
  settings: PasswordSettingsInput;
};


export type MutationUpdatePayrollLegalSettingsArgs = {
  civilContractCostsRate: Scalars['Float']['input'];
  defaultTaxResident: Scalars['Boolean']['input'];
  employeeInsuranceRate: Scalars['Float']['input'];
  employerPaidSickDays: Scalars['Int']['input'];
  incomeTaxRate: Scalars['Float']['input'];
  maxInsuranceBase: Scalars['Float']['input'];
  noiCompensationPercent: Scalars['Float']['input'];
  trzComplianceStrictMode: Scalars['Boolean']['input'];
};


export type MutationUpdatePositionArgs = {
  departmentId: Scalars['Int']['input'];
  id: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};


export type MutationUpdateProductionOrderQuantityArgs = {
  orderId: Scalars['Int']['input'];
  quantity: Scalars['Float']['input'];
};


export type MutationUpdateProductionOrderStatusArgs = {
  id: Scalars['Int']['input'];
  status: Scalars['String']['input'];
};


export type MutationUpdateProductionTaskStatusArgs = {
  id: Scalars['Int']['input'];
  status: Scalars['String']['input'];
};


export type MutationUpdateRecipePriceArgs = {
  input: RecipePriceUpdateInput;
  recipeId: Scalars['Int']['input'];
};


export type MutationUpdateRoleArgs = {
  description?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  name?: InputMaybe<Scalars['String']['input']>;
};


export type MutationUpdateSectionInAnnexTemplateArgs = {
  section: AnnexTemplateSectionUpdateInput;
  sectionId: Scalars['Int']['input'];
};


export type MutationUpdateSectionInContractTemplateArgs = {
  section: ContractTemplateSectionUpdateInput;
  sectionId: Scalars['Int']['input'];
};


export type MutationUpdateSecurityConfigArgs = {
  lockoutMinutes: Scalars['Int']['input'];
  maxLoginAttempts: Scalars['Int']['input'];
};


export type MutationUpdateShiftArgs = {
  breakDurationMinutes?: InputMaybe<Scalars['Int']['input']>;
  endTime: Scalars['Time']['input'];
  id: Scalars['Int']['input'];
  name: Scalars['String']['input'];
  payMultiplier?: InputMaybe<Scalars['Decimal']['input']>;
  shiftType?: InputMaybe<Scalars['String']['input']>;
  startTime: Scalars['Time']['input'];
  toleranceMinutes?: InputMaybe<Scalars['Int']['input']>;
};


export type MutationUpdateSmtpSettingsArgs = {
  settings: SmtpSettingsInput;
};


export type MutationUpdateStorageZoneArgs = {
  input: UpdateStorageZoneInput;
};


export type MutationUpdateSupplierArgs = {
  input: UpdateSupplierInput;
};


export type MutationUpdateTerminalArgs = {
  alias?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  mode?: InputMaybe<Scalars['String']['input']>;
};


export type MutationUpdateTimeLogArgs = {
  breakDurationMinutes?: Scalars['Int']['input'];
  endTime?: InputMaybe<Scalars['DateTime']['input']>;
  id: Scalars['Int']['input'];
  isManual?: Scalars['Boolean']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  startTime: Scalars['DateTime']['input'];
};


export type MutationUpdateUserArgs = {
  userInput: UpdateUserInput;
};


export type MutationUpdateVehicleArgs = {
  id: Scalars['Int']['input'];
  input: VehicleUpdateInput;
};


export type MutationUpdateVehicleDriverArgs = {
  id: Scalars['Int']['input'];
  input: VehicleDriverUpdateInput;
};


export type MutationUpdateVehicleFuelArgs = {
  id: Scalars['Int']['input'];
  input: VehicleFuelUpdateInput;
};


export type MutationUpdateVehicleInspectionArgs = {
  id: Scalars['Int']['input'];
  input: VehicleInspectionUpdateInput;
};


export type MutationUpdateVehicleInsuranceArgs = {
  id: Scalars['Int']['input'];
  input: VehicleInsuranceUpdateInput;
};


export type MutationUpdateVehicleMileageArgs = {
  id: Scalars['Int']['input'];
  input: VehicleMileageUpdateInput;
};


export type MutationUpdateVehicleRepairArgs = {
  id: Scalars['Int']['input'];
  input: VehicleRepairUpdateInput;
};


export type MutationUpdateVehicleTripArgs = {
  id: Scalars['Int']['input'];
  input: VehicleTripUpdateInput;
};


export type MutationValidateSaftXmlArgs = {
  xmlContent: Scalars['String']['input'];
};

export type NightWorkBonus = {
  amount: Scalars['Decimal']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['Date']['output'];
  hourlyRate: Scalars['Decimal']['output'];
  hours: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  isPaid: Scalars['Boolean']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  periodId?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  user: User;
  userId: Scalars['Int']['output'];
};

export type NotificationSetting = {
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  emailEnabled: Scalars['Boolean']['output'];
  emailTemplate?: Maybe<Scalars['String']['output']>;
  enabled: Scalars['Boolean']['output'];
  eventType: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  intervalMinutes: Scalars['Int']['output'];
  lastSentAt?: Maybe<Scalars['DateTime']['output']>;
  pushEnabled: Scalars['Boolean']['output'];
  recipients?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type NotificationSettingInput = {
  companyId: Scalars['Int']['input'];
  emailEnabled?: Scalars['Boolean']['input'];
  emailTemplate?: InputMaybe<Scalars['String']['input']>;
  enabled?: Scalars['Boolean']['input'];
  eventType: Scalars['String']['input'];
  id?: InputMaybe<Scalars['Int']['input']>;
  intervalMinutes?: Scalars['Int']['input'];
  pushEnabled?: Scalars['Boolean']['input'];
  recipients?: InputMaybe<Scalars['String']['input']>;
};

export type OfficeLocation = {
  entryEnabled?: Maybe<Scalars['Boolean']['output']>;
  exitEnabled?: Maybe<Scalars['Boolean']['output']>;
  latitude?: Maybe<Scalars['Float']['output']>;
  longitude?: Maybe<Scalars['Float']['output']>;
  radius?: Maybe<Scalars['Int']['output']>;
};

export type OperationLogType = {
  changes?: Maybe<Scalars['String']['output']>;
  entityId: Scalars['Int']['output'];
  entityType: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  operation: Scalars['String']['output'];
  timestamp?: Maybe<Scalars['String']['output']>;
  user?: Maybe<User>;
  userId?: Maybe<Scalars['Int']['output']>;
};

export type OrthodoxHoliday = {
  date: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  isFixed: Scalars['Boolean']['output'];
  localName?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
};

export type OvertimeStat = {
  amount: Scalars['Decimal']['output'];
  month: Scalars['String']['output'];
};

export type OvertimeWork = {
  amount: Scalars['Decimal']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['Date']['output'];
  hourlyRate: Scalars['Decimal']['output'];
  hours: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  isPaid: Scalars['Boolean']['output'];
  multiplier: Scalars['Decimal']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  periodId?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  user: User;
  userId: Scalars['Int']['output'];
};

export type PaginatedUsers = {
  totalCount: Scalars['Int']['output'];
  users: Array<User>;
};

export type PasswordSettings = {
  maxLength: Scalars['Int']['output'];
  minLength: Scalars['Int']['output'];
  requireDigit: Scalars['Boolean']['output'];
  requireLower: Scalars['Boolean']['output'];
  requireSpecial: Scalars['Boolean']['output'];
  requireUpper: Scalars['Boolean']['output'];
};

export type PasswordSettingsInput = {
  currentPassword: Scalars['String']['input'];
  newPassword: Scalars['String']['input'];
};

export type Payroll = {
  annualLeaveDays: Scalars['Int']['output'];
  currency: Scalars['String']['output'];
  hasHealthInsurance: Scalars['Boolean']['output'];
  hasTaxDeduction: Scalars['Boolean']['output'];
  healthInsurancePercent: Scalars['Decimal']['output'];
  hourlyRate: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  monthlySalary?: Maybe<Scalars['Decimal']['output']>;
  overtimeMultiplier: Scalars['Decimal']['output'];
  positionId?: Maybe<Scalars['Int']['output']>;
  standardHoursPerDay: Scalars['Int']['output'];
  taxPercent: Scalars['Decimal']['output'];
  user?: Maybe<User>;
  userId?: Maybe<Scalars['Int']['output']>;
};

export type PayrollForecast = {
  byDepartment: Array<DepartmentForecast>;
  totalAmount: Scalars['Float']['output'];
};

export type PayrollLegalSettings = {
  civilContractCostsRate: Scalars['Float']['output'];
  defaultTaxResident: Scalars['Boolean']['output'];
  employeeInsuranceRate: Scalars['Float']['output'];
  employerPaidSickDays: Scalars['Int']['output'];
  incomeTaxRate: Scalars['Float']['output'];
  maxInsuranceBase: Scalars['Float']['output'];
  noiCompensationPercent: Scalars['Float']['output'];
  trzComplianceStrictMode: Scalars['Boolean']['output'];
};

export type PayrollSummaryItem = {
  advances: Scalars['Float']['output'];
  bonusAmount: Scalars['Float']['output'];
  contractType: Scalars['String']['output'];
  email: Scalars['String']['output'];
  fullName: Scalars['String']['output'];
  grossAmount: Scalars['Float']['output'];
  installments?: Maybe<SalaryInstallments>;
  insuranceAmount: Scalars['Float']['output'];
  loanDeductions: Scalars['Float']['output'];
  netAmount: Scalars['Float']['output'];
  netPayable: Scalars['Float']['output'];
  taxAmount: Scalars['Float']['output'];
  totalDeductions: Scalars['Float']['output'];
  userId: Scalars['Int']['output'];
};

export type Payslip = {
  actualPaymentDate?: Maybe<Scalars['DateTime']['output']>;
  benefitAmount: Scalars['Decimal']['output'];
  bonusAmount: Scalars['Decimal']['output'];
  dooEmployee: Scalars['Decimal']['output'];
  dooEmployer: Scalars['Decimal']['output'];
  dzpoEmployee: Scalars['Decimal']['output'];
  dzpoEmployer: Scalars['Decimal']['output'];
  generatedAt: Scalars['DateTime']['output'];
  grossSalary: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  incomeTax: Scalars['Decimal']['output'];
  insuranceAmount: Scalars['Decimal']['output'];
  leaveDays: Scalars['Int']['output'];
  nightWorkAmount: Scalars['Decimal']['output'];
  overtimeAmount: Scalars['Decimal']['output'];
  paymentMethod: Scalars['String']['output'];
  paymentStatus: Scalars['String']['output'];
  periodEnd: Scalars['DateTime']['output'];
  periodStart: Scalars['DateTime']['output'];
  regularAmount: Scalars['Decimal']['output'];
  sickDays: Scalars['Int']['output'];
  sickLeaveAmount: Scalars['Decimal']['output'];
  standardDeduction: Scalars['Decimal']['output'];
  taxAmount: Scalars['Decimal']['output'];
  taxableBase: Scalars['Decimal']['output'];
  totalAmount: Scalars['Decimal']['output'];
  totalOvertimeHours: Scalars['Decimal']['output'];
  totalRegularHours: Scalars['Decimal']['output'];
  tripAmount: Scalars['Decimal']['output'];
  tzpbEmployer: Scalars['Decimal']['output'];
  user: User;
  userId: Scalars['Int']['output'];
  voucherAmount: Scalars['Decimal']['output'];
  zoEmployee: Scalars['Decimal']['output'];
  zoEmployer: Scalars['Decimal']['output'];
};

export type Position = {
  department?: Maybe<Department>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  id: Scalars['Int']['output'];
  payrolls: Array<Payroll>;
  title: Scalars['String']['output'];
};

export type PresenceStatus =
  | 'ABSENT'
  | 'LATE'
  | 'OFF_DUTY'
  | 'ON_DUTY'
  | 'PAID_LEAVE'
  | 'SICK_LEAVE';

export type PriceHistory = {
  changedAt: Scalars['DateTime']['output'];
  changedBy: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  newCost?: Maybe<Scalars['Decimal']['output']>;
  newMarkup?: Maybe<Scalars['Decimal']['output']>;
  newPremium?: Maybe<Scalars['Decimal']['output']>;
  newPrice?: Maybe<Scalars['Decimal']['output']>;
  oldCost?: Maybe<Scalars['Decimal']['output']>;
  oldMarkup?: Maybe<Scalars['Decimal']['output']>;
  oldPremium?: Maybe<Scalars['Decimal']['output']>;
  oldPrice?: Maybe<Scalars['Decimal']['output']>;
  reason?: Maybe<Scalars['String']['output']>;
  recipe?: Maybe<Recipe>;
  recipeId: Scalars['Int']['output'];
  user?: Maybe<User>;
};

export type Printer = {
  gatewayId: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  ipAddress?: Maybe<Scalars['String']['output']>;
  isActive: Scalars['Boolean']['output'];
  isDefault: Scalars['Boolean']['output'];
  lastError?: Maybe<Scalars['String']['output']>;
  lastTest?: Maybe<Scalars['DateTime']['output']>;
  manufacturer?: Maybe<Scalars['String']['output']>;
  model?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  port: Scalars['Int']['output'];
  printerType?: Maybe<Scalars['String']['output']>;
  protocol?: Maybe<Scalars['String']['output']>;
  windowsShareName?: Maybe<Scalars['String']['output']>;
};

export type ProductionOrder = {
  companyId: Scalars['Int']['output'];
  confirmedAt?: Maybe<Scalars['DateTime']['output']>;
  confirmedBy?: Maybe<Scalars['Int']['output']>;
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  dueDate: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  productionDeadline?: Maybe<Scalars['DateTime']['output']>;
  quantity: Scalars['Decimal']['output'];
  recipe: Recipe;
  recipeId: Scalars['Int']['output'];
  status: Scalars['String']['output'];
  tasks: Array<ProductionTask>;
};

export type ProductionOrderInput = {
  companyId: Scalars['Int']['input'];
  dueDate: Scalars['DateTime']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Decimal']['input'];
  recipeId: Scalars['Int']['input'];
};

export type ProductionRecord = {
  confirmedAt?: Maybe<Scalars['DateTime']['output']>;
  confirmedBy?: Maybe<Scalars['Int']['output']>;
  createdAt: Scalars['DateTime']['output'];
  expiryDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['Int']['output'];
  ingredients: Array<ProductionRecordIngredient>;
  notes?: Maybe<Scalars['String']['output']>;
  orderId: Scalars['Int']['output'];
  workers: Array<ProductionRecordWorker>;
};

export type ProductionRecordIngredient = {
  batchNumber: Scalars['String']['output'];
  expiryDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['Int']['output'];
  ingredientId: Scalars['Int']['output'];
  ingredientName?: Maybe<Scalars['String']['output']>;
  quantityUsed: Scalars['Decimal']['output'];
  unit?: Maybe<Scalars['String']['output']>;
};

export type ProductionRecordWorker = {
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  startedAt?: Maybe<Scalars['DateTime']['output']>;
  userId: Scalars['Int']['output'];
  userName?: Maybe<Scalars['String']['output']>;
  workstationId?: Maybe<Scalars['Int']['output']>;
  workstationName?: Maybe<Scalars['String']['output']>;
};

export type ProductionScrapLog = {
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  quantity: Scalars['Decimal']['output'];
  reason?: Maybe<Scalars['String']['output']>;
  taskId: Scalars['Int']['output'];
  userId: Scalars['Int']['output'];
};

export type ProductionTask = {
  assignedUser?: Maybe<User>;
  assignedUserId?: Maybe<Scalars['Int']['output']>;
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  orderId: Scalars['Int']['output'];
  startedAt?: Maybe<Scalars['DateTime']['output']>;
  status: Scalars['String']['output'];
  stepId?: Maybe<Scalars['Int']['output']>;
  workstation: Workstation;
  workstationId: Scalars['Int']['output'];
};

export type ProformaInvoice = {
  clientAddress?: Maybe<Scalars['String']['output']>;
  clientEik?: Maybe<Scalars['String']['output']>;
  clientName?: Maybe<Scalars['String']['output']>;
  company?: Maybe<Company>;
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  creator?: Maybe<User>;
  date: Scalars['Date']['output'];
  deliveryMethod?: Maybe<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  discountAmount: Scalars['Decimal']['output'];
  discountPercent: Scalars['Decimal']['output'];
  documentType?: Maybe<Scalars['String']['output']>;
  dueDate?: Maybe<Scalars['Date']['output']>;
  griff?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  items: Array<InvoiceItem>;
  notes?: Maybe<Scalars['String']['output']>;
  number: Scalars['String']['output'];
  paymentDate?: Maybe<Scalars['Date']['output']>;
  paymentMethod?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  subtotal: Scalars['Decimal']['output'];
  total: Scalars['Decimal']['output'];
  type: Scalars['String']['output'];
  vatAmount: Scalars['Decimal']['output'];
  vatRate: Scalars['Decimal']['output'];
};

export type PublicHoliday = {
  date: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  localName?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
};

export type Query = {
  accessCodes: Array<AccessCode>;
  accessDoors: Array<AccessDoor>;
  accessLogs: Array<AccessLog>;
  accessZones: Array<AccessZone>;
  account?: Maybe<Account>;
  accountByCode?: Maybe<Account>;
  accountingEntries: Array<AccountingEntry>;
  accountingEntry?: Maybe<AccountingEntry>;
  accounts: Array<Account>;
  activeSessions: Array<UserSession>;
  activeTimeLog?: Maybe<TimeLog>;
  allLeaveRequests: Array<LeaveRequest>;
  allUsers: Array<User>;
  annexTemplate?: Maybe<AnnexTemplate>;
  annexTemplateVersions: Array<AnnexTemplateVersion>;
  annexTemplates: Array<AnnexTemplate>;
  annexes: Array<ContractAnnex>;
  apiKeys: Array<ApiKey>;
  auditLogs: Array<AuditLog>;
  bankAccount?: Maybe<BankAccount>;
  bankAccounts: Array<BankAccount>;
  bankTransaction?: Maybe<BankTransaction>;
  bankTransactions: Array<BankTransaction>;
  batches: Array<Batch>;
  cashJournalEntries: Array<CashJournalEntryType>;
  cashReceipt?: Maybe<CashReceipt>;
  cashReceipts: Array<CashReceipt>;
  clauseTemplates: Array<ClauseTemplate>;
  companies: Array<Company>;
  contractTemplate?: Maybe<ContractTemplate>;
  contractTemplateVersions: Array<ContractTemplateVersion>;
  contractTemplates: Array<ContractTemplate>;
  costCenter?: Maybe<VehicleCostCenter>;
  costCenters: Array<VehicleCostCenter>;
  dailySummaries: Array<DailySummaryType>;
  departments: Array<Department>;
  employmentContract?: Maybe<EmploymentContract>;
  employmentContracts: Array<EmploymentContract>;
  gateway?: Maybe<Gateway>;
  gatewayStats: GatewayStats;
  gateways: Array<Gateway>;
  getFefoSuggestion: Array<FefoSuggestion>;
  globalPayrollConfig: GlobalPayrollConfig;
  googleCalendarAccount?: Maybe<GoogleCalendarAccount>;
  hello: Scalars['String']['output'];
  ingredientBatchesWithStock: Array<Batch>;
  ingredients: Array<Ingredient>;
  inventoryByBarcode?: Maybe<InventoryItem>;
  inventorySessionItems: Array<InventoryItem>;
  inventorySessions: Array<InventorySession>;
  invoice?: Maybe<Invoice>;
  invoiceByNumber?: Maybe<Invoice>;
  invoiceCorrection?: Maybe<InvoiceCorrection>;
  invoiceCorrections: Array<InvoiceCorrection>;
  invoices: Array<Invoice>;
  kioskSecuritySettings: KioskSecuritySettings;
  leaveBalance: LeaveBalance;
  managementStats: ManagementStats;
  me?: Maybe<User>;
  modules: Array<Module>;
  monthlySummaries: Array<MonthlySummaryType>;
  monthlyWorkDays?: Maybe<MonthlyWorkDays>;
  myDailyStats: Array<DailyStat>;
  myLeaveRequests: Array<LeaveRequest>;
  mySchedules: Array<WorkSchedule>;
  mySwapRequests: Array<ShiftSwapRequest>;
  notificationSetting?: Maybe<NotificationSetting>;
  notificationSettings: Array<NotificationSetting>;
  officeLocation?: Maybe<OfficeLocation>;
  operationLogs: Array<OperationLogType>;
  orthodoxHolidays: Array<OrthodoxHoliday>;
  overdueProductionOrders: Array<ProductionOrder>;
  passwordSettings: PasswordSettings;
  payrollForecast: PayrollForecast;
  payrollLegalSettings: PayrollLegalSettings;
  payrollSummary: Array<PayrollSummaryItem>;
  pendingAdminSwaps: Array<ShiftSwapRequest>;
  pendingLeaveRequests: Array<LeaveRequest>;
  positions: Array<Position>;
  priceHistory: Array<PriceHistory>;
  printers: Array<Printer>;
  productionOrders: Array<ProductionOrder>;
  productionOrdersForDay: Array<ProductionOrder>;
  productionRecordByOrder?: Maybe<ProductionRecord>;
  productionRecords: Array<ProductionRecord>;
  proformaInvoices: Array<ProformaInvoice>;
  publicHolidays: Array<PublicHoliday>;
  recipes: Array<Recipe>;
  recipesWithPrices: Array<Recipe>;
  role?: Maybe<Role>;
  roles: Array<Role>;
  scheduleTemplate?: Maybe<ScheduleTemplate>;
  scheduleTemplates: Array<ScheduleTemplate>;
  shifts: Array<Shift>;
  smtpSettings?: Maybe<SmtpSettings>;
  stockConsumptionLogs: Array<StockConsumptionLog>;
  storageZones: Array<StorageZone>;
  suppliers: Array<Supplier>;
  terminal?: Maybe<Terminal>;
  terminalOrders: Array<TerminalOrder>;
  terminals: Array<Terminal>;
  timeLogs: Array<TimeLog>;
  user?: Maybe<User>;
  userDailyStats: Array<DailyStat>;
  userPresences: Array<UserPresence>;
  users: PaginatedUsers;
  vapidPublicKey?: Maybe<Scalars['String']['output']>;
  vatRegister?: Maybe<VatRegister>;
  vatRegisters: Array<VatRegister>;
  vehicle?: Maybe<Vehicle>;
  vehicleDocuments: Array<VehicleDocument>;
  vehicleDrivers: Array<VehicleDriver>;
  vehicleFuelLogs: Array<VehicleFuel>;
  vehicleInspections: Array<VehicleInspection>;
  vehicleInsurances: Array<VehicleInsurance>;
  vehicleMileage: Array<VehicleMileage>;
  vehicleRepairs: Array<VehicleRepair>;
  vehicleTrips: Array<VehicleTrip>;
  vehicleTypes: Array<VehicleType>;
  vehicles: Array<Vehicle>;
  webhooks: Array<Webhook>;
  weeklySummary?: Maybe<WeeklySummary>;
  workSchedules: Array<WorkSchedule>;
  workstations: Array<Workstation>;
  yearlySummaries: Array<YearlySummaryType>;
};


export type QueryAccessCodesArgs = {
  gatewayId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryAccessDoorsArgs = {
  gatewayId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryAccessLogsArgs = {
  gatewayId?: InputMaybe<Scalars['Int']['input']>;
  limit?: Scalars['Int']['input'];
};


export type QueryAccountArgs = {
  id: Scalars['Int']['input'];
};


export type QueryAccountByCodeArgs = {
  code: Scalars['String']['input'];
};


export type QueryAccountingEntriesArgs = {
  accountId?: InputMaybe<Scalars['Int']['input']>;
  endDate?: InputMaybe<Scalars['String']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['String']['input']>;
};


export type QueryAccountingEntryArgs = {
  id: Scalars['Int']['input'];
};


export type QueryAccountsArgs = {
  parentId?: InputMaybe<Scalars['Int']['input']>;
  type?: InputMaybe<Scalars['String']['input']>;
};


export type QueryActiveSessionsArgs = {
  limit?: Scalars['Int']['input'];
  skip?: Scalars['Int']['input'];
};


export type QueryAllLeaveRequestsArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
};


export type QueryAllUsersArgs = {
  search?: InputMaybe<Scalars['String']['input']>;
};


export type QueryAnnexTemplateArgs = {
  id: Scalars['Int']['input'];
};


export type QueryAnnexTemplateVersionsArgs = {
  templateId: Scalars['Int']['input'];
};


export type QueryAnnexesArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
};


export type QueryAuditLogsArgs = {
  action?: InputMaybe<Scalars['String']['input']>;
  limit?: Scalars['Int']['input'];
  skip?: Scalars['Int']['input'];
};


export type QueryBankAccountArgs = {
  id: Scalars['Int']['input'];
};


export type QueryBankAccountsArgs = {
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
};


export type QueryBankTransactionArgs = {
  id: Scalars['Int']['input'];
};


export type QueryBankTransactionsArgs = {
  bankAccountId?: InputMaybe<Scalars['Int']['input']>;
  endDate?: InputMaybe<Scalars['String']['input']>;
  matched?: InputMaybe<Scalars['Boolean']['input']>;
  startDate?: InputMaybe<Scalars['String']['input']>;
};


export type QueryBatchesArgs = {
  ingredientId?: InputMaybe<Scalars['Int']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
};


export type QueryCashJournalEntriesArgs = {
  endDate?: InputMaybe<Scalars['String']['input']>;
  operationType?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['String']['input']>;
};


export type QueryCashReceiptArgs = {
  id: Scalars['Int']['input'];
};


export type QueryCashReceiptsArgs = {
  endDate?: InputMaybe<Scalars['String']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['String']['input']>;
};


export type QueryClauseTemplatesArgs = {
  category?: InputMaybe<Scalars['String']['input']>;
};


export type QueryContractTemplateArgs = {
  id: Scalars['Int']['input'];
};


export type QueryContractTemplateVersionsArgs = {
  templateId: Scalars['Int']['input'];
};


export type QueryCostCenterArgs = {
  id: Scalars['Int']['input'];
};


export type QueryCostCentersArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryDailySummariesArgs = {
  endDate?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['String']['input']>;
};


export type QueryDepartmentsArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryEmploymentContractArgs = {
  id: Scalars['Int']['input'];
};


export type QueryEmploymentContractsArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryGatewayArgs = {
  id: Scalars['Int']['input'];
};


export type QueryGatewaysArgs = {
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
};


export type QueryGetFefoSuggestionArgs = {
  ingredientId: Scalars['Int']['input'];
  quantity: Scalars['Decimal']['input'];
};


export type QueryIngredientBatchesWithStockArgs = {
  ingredientId: Scalars['Int']['input'];
};


export type QueryIngredientsArgs = {
  search?: InputMaybe<Scalars['String']['input']>;
};


export type QueryInventoryByBarcodeArgs = {
  barcode: Scalars['String']['input'];
};


export type QueryInventorySessionItemsArgs = {
  sessionId: Scalars['Int']['input'];
};


export type QueryInventorySessionsArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
};


export type QueryInvoiceArgs = {
  id: Scalars['Int']['input'];
};


export type QueryInvoiceByNumberArgs = {
  number: Scalars['String']['input'];
};


export type QueryInvoiceCorrectionArgs = {
  id: Scalars['Int']['input'];
};


export type QueryInvoiceCorrectionsArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
  type?: InputMaybe<Scalars['String']['input']>;
};


export type QueryInvoicesArgs = {
  search?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
  type?: InputMaybe<Scalars['String']['input']>;
};


export type QueryLeaveBalanceArgs = {
  userId: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type QueryMonthlySummariesArgs = {
  endYear?: InputMaybe<Scalars['Int']['input']>;
  startYear?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryMonthlyWorkDaysArgs = {
  month: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type QueryMyDailyStatsArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
};


export type QueryMySchedulesArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
};


export type QueryNotificationSettingArgs = {
  companyId: Scalars['Int']['input'];
  eventType: Scalars['String']['input'];
};


export type QueryNotificationSettingsArgs = {
  companyId: Scalars['Int']['input'];
};


export type QueryOperationLogsArgs = {
  endDate?: InputMaybe<Scalars['String']['input']>;
  entityType?: InputMaybe<Scalars['String']['input']>;
  operation?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['String']['input']>;
};


export type QueryOrthodoxHolidaysArgs = {
  year?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryPayrollForecastArgs = {
  month: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
};


export type QueryPayrollSummaryArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
  userIds?: InputMaybe<Array<Scalars['Int']['input']>>;
};


export type QueryPositionsArgs = {
  departmentId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryPriceHistoryArgs = {
  limit?: Scalars['Int']['input'];
  recipeId: Scalars['Int']['input'];
};


export type QueryPrintersArgs = {
  gatewayId: Scalars['Int']['input'];
};


export type QueryProductionOrdersArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
};


export type QueryProductionOrdersForDayArgs = {
  date?: InputMaybe<Scalars['String']['input']>;
};


export type QueryProductionRecordByOrderArgs = {
  orderId: Scalars['Int']['input'];
};


export type QueryProductionRecordsArgs = {
  orderId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryProformaInvoicesArgs = {
  search?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
};


export type QueryPublicHolidaysArgs = {
  year?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryRecipesWithPricesArgs = {
  categoryId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryRoleArgs = {
  id: Scalars['Int']['input'];
};


export type QueryScheduleTemplateArgs = {
  id: Scalars['Int']['input'];
};


export type QueryStockConsumptionLogsArgs = {
  batchId?: InputMaybe<Scalars['Int']['input']>;
  endDate?: InputMaybe<Scalars['Date']['input']>;
  ingredientId?: InputMaybe<Scalars['Int']['input']>;
  startDate?: InputMaybe<Scalars['Date']['input']>;
};


export type QueryTerminalArgs = {
  id: Scalars['Int']['input'];
};


export type QueryTerminalOrdersArgs = {
  workstationId: Scalars['Int']['input'];
};


export type QueryTerminalsArgs = {
  gatewayId?: InputMaybe<Scalars['Int']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
};


export type QueryTimeLogsArgs = {
  endDate: Scalars['DateTime']['input'];
  startDate: Scalars['DateTime']['input'];
};


export type QueryUserArgs = {
  id?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryUserDailyStatsArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
  userId: Scalars['Int']['input'];
};


export type QueryUserPresencesArgs = {
  date: Scalars['Date']['input'];
  status?: InputMaybe<PresenceStatus>;
};


export type QueryUsersArgs = {
  limit?: Scalars['Int']['input'];
  search?: InputMaybe<Scalars['String']['input']>;
  skip?: Scalars['Int']['input'];
  sortBy?: Scalars['String']['input'];
  sortOrder?: Scalars['String']['input'];
};


export type QueryVatRegisterArgs = {
  id: Scalars['Int']['input'];
};


export type QueryVatRegistersArgs = {
  month?: InputMaybe<Scalars['Int']['input']>;
  year?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryVehicleArgs = {
  id: Scalars['Int']['input'];
};


export type QueryVehicleDocumentsArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleDriversArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleFuelLogsArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleInspectionsArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleInsurancesArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleMileageArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleRepairsArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleTripsArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehiclesArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryWeeklySummaryArgs = {
  date?: InputMaybe<Scalars['Date']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryWorkSchedulesArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
};


export type QueryYearlySummariesArgs = {
  endYear?: InputMaybe<Scalars['Int']['input']>;
  startYear?: InputMaybe<Scalars['Int']['input']>;
};

export type QuickSaleInput = {
  clientName?: InputMaybe<Scalars['String']['input']>;
  clientPhone?: InputMaybe<Scalars['String']['input']>;
  companyId: Scalars['Int']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  paymentMethod?: Scalars['String']['input'];
  price?: InputMaybe<Scalars['Decimal']['input']>;
  quantity: Scalars['Decimal']['input'];
  recipeId: Scalars['Int']['input'];
};

export type RecalculateResult = {
  costPrice: Scalars['Decimal']['output'];
  finalPrice: Scalars['Decimal']['output'];
  markupAmount: Scalars['Decimal']['output'];
  portionPrice: Scalars['Decimal']['output'];
  recipeId: Scalars['Int']['output'];
  recipeName: Scalars['String']['output'];
};

export type Recipe = {
  category?: Maybe<Scalars['String']['output']>;
  companyId: Scalars['Int']['output'];
  costPrice?: Maybe<Scalars['Decimal']['output']>;
  defaultPieces: Scalars['Int']['output'];
  description?: Maybe<Scalars['String']['output']>;
  finalPrice: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  ingredients: Array<RecipeIngredient>;
  instructions?: Maybe<Scalars['String']['output']>;
  lastPriceUpdate?: Maybe<Scalars['DateTime']['output']>;
  markupAmount: Scalars['Decimal']['output'];
  markupPercentage: Scalars['Decimal']['output'];
  name: Scalars['String']['output'];
  portionPrice?: Maybe<Scalars['Decimal']['output']>;
  portions: Scalars['Int']['output'];
  premiumAmount: Scalars['Decimal']['output'];
  priceCalculatedAt?: Maybe<Scalars['DateTime']['output']>;
  productionDeadlineDays?: Maybe<Scalars['Int']['output']>;
  productionTimeDays: Scalars['Int']['output'];
  sections: Array<RecipeSection>;
  sellingPrice?: Maybe<Scalars['Decimal']['output']>;
  shelfLifeDays: Scalars['Int']['output'];
  shelfLifeFrozenDays: Scalars['Int']['output'];
  standardQuantity: Scalars['Decimal']['output'];
  steps: Array<RecipeStep>;
  yieldQuantity: Scalars['Decimal']['output'];
  yieldUnit: Scalars['String']['output'];
};

export type RecipeCostResult = {
  costPrice: Scalars['Decimal']['output'];
  finalPrice: Scalars['Decimal']['output'];
  markupAmount: Scalars['Decimal']['output'];
  portionPrice: Scalars['Decimal']['output'];
  premiumAmount: Scalars['Decimal']['output'];
  recipeId: Scalars['Int']['output'];
  recipeName: Scalars['String']['output'];
};

export type RecipeIngredient = {
  id: Scalars['Int']['output'];
  ingredient: Ingredient;
  ingredientId: Scalars['Int']['output'];
  quantityGross: Scalars['Decimal']['output'];
  quantityNet: Scalars['Decimal']['output'];
  recipeId: Scalars['Int']['output'];
  sectionId?: Maybe<Scalars['Int']['output']>;
  wastePercentage: Scalars['Decimal']['output'];
  workstation?: Maybe<Workstation>;
  workstationId?: Maybe<Scalars['Int']['output']>;
};

export type RecipeIngredientInput = {
  ingredientId: Scalars['Int']['input'];
  quantityGross: Scalars['Decimal']['input'];
  quantityNet?: InputMaybe<Scalars['Decimal']['input']>;
  wastePercentage?: InputMaybe<Scalars['Decimal']['input']>;
  workstationId?: InputMaybe<Scalars['Int']['input']>;
};

export type RecipeInput = {
  companyId: Scalars['Int']['input'];
  defaultPieces?: Scalars['Int']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  ingredients?: Array<RecipeIngredientInput>;
  instructions?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  productionTimeDays?: Scalars['Int']['input'];
  sections: Array<RecipeSectionInput>;
  shelfLifeDays?: Scalars['Int']['input'];
  shelfLifeFrozenDays?: Scalars['Int']['input'];
  standardQuantity?: Scalars['Decimal']['input'];
  steps?: Array<RecipeStepInput>;
  yieldQuantity?: Scalars['Decimal']['input'];
  yieldUnit?: Scalars['String']['input'];
};

export type RecipePriceUpdateInput = {
  markupPercentage?: InputMaybe<Scalars['Decimal']['input']>;
  portions?: InputMaybe<Scalars['Int']['input']>;
  premiumAmount?: InputMaybe<Scalars['Decimal']['input']>;
  reason?: InputMaybe<Scalars['String']['input']>;
};

export type RecipeSection = {
  id: Scalars['Int']['output'];
  ingredients: Array<RecipeIngredient>;
  name: Scalars['String']['output'];
  recipeId: Scalars['Int']['output'];
  sectionOrder: Scalars['Int']['output'];
  sectionType: Scalars['String']['output'];
  shelfLifeDays?: Maybe<Scalars['Int']['output']>;
  steps: Array<RecipeStep>;
  wastePercentage: Scalars['Float']['output'];
};

export type RecipeSectionInput = {
  bruttoG?: InputMaybe<Scalars['Float']['input']>;
  ingredients: Array<RecipeIngredientInput>;
  name: Scalars['String']['input'];
  netG?: InputMaybe<Scalars['Float']['input']>;
  sectionOrder?: Scalars['Int']['input'];
  sectionType: Scalars['String']['input'];
  shelfLifeDays?: InputMaybe<Scalars['Int']['input']>;
  steps: Array<RecipeStepInput>;
  wastePercentage?: Scalars['Decimal']['input'];
};

export type RecipeStep = {
  estimatedDurationMinutes?: Maybe<Scalars['Int']['output']>;
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  recipeId?: Maybe<Scalars['Int']['output']>;
  sectionId?: Maybe<Scalars['Int']['output']>;
  stepOrder: Scalars['Int']['output'];
  workstation: Workstation;
  workstationId: Scalars['Int']['output'];
};

export type RecipeStepInput = {
  estimatedDurationMinutes?: InputMaybe<Scalars['Int']['input']>;
  name: Scalars['String']['input'];
  stepOrder?: Scalars['Int']['input'];
  workstationId: Scalars['Int']['input'];
};

export type Role = {
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
};

export type RoleCreateInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
};

export type SaftFileResult = {
  fileName: Scalars['String']['output'];
  fileSize: Scalars['Int']['output'];
  periodEnd: Scalars['Date']['output'];
  periodStart: Scalars['Date']['output'];
  validationResult: SaftValidationResult;
  xmlContent: Scalars['String']['output'];
};

export type SaftValidationResult = {
  errors: Array<Scalars['String']['output']>;
  isValid: Scalars['Boolean']['output'];
  status: Scalars['String']['output'];
  warnings: Array<Scalars['String']['output']>;
};

export type SalaryInstallments = {
  amountPerInstallment: Scalars['Float']['output'];
  count: Scalars['Int']['output'];
};

export type ScheduleTemplate = {
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  items: Array<ScheduleTemplateItem>;
  name: Scalars['String']['output'];
};

export type ScheduleTemplateItem = {
  dayIndex: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  shift?: Maybe<Shift>;
  shiftId?: Maybe<Scalars['Int']['output']>;
};

export type ScheduleTemplateItemInput = {
  breakMinutes?: Scalars['Int']['input'];
  dayOfWeek: Scalars['Int']['input'];
  endTime: Scalars['String']['input'];
  startTime: Scalars['String']['input'];
};

export type ScrapTaskInput = {
  quantity: Scalars['Float']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
  taskId: Scalars['Int']['input'];
};

export type ServiceLoan = {
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  installmentAmount: Scalars['Decimal']['output'];
  installmentsCount: Scalars['Int']['output'];
  installmentsPaid: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  remainingAmount: Scalars['Decimal']['output'];
  startDate: Scalars['Date']['output'];
  totalAmount: Scalars['Decimal']['output'];
  userId: Scalars['Int']['output'];
};

export type Shift = {
  breakDurationMinutes: Scalars['Int']['output'];
  endTime: Scalars['Time']['output'];
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  payMultiplier: Scalars['Decimal']['output'];
  shiftType: Scalars['String']['output'];
  startTime: Scalars['Time']['output'];
  toleranceMinutes: Scalars['Int']['output'];
};

export type ShiftSwapRequest = {
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  requestor: User;
  requestorId: Scalars['Int']['output'];
  requestorSchedule: WorkSchedule;
  requestorScheduleId: Scalars['Int']['output'];
  status: Scalars['String']['output'];
  targetSchedule: WorkSchedule;
  targetScheduleId: Scalars['Int']['output'];
  targetUser: User;
  targetUserId: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type SmtpSettings = {
  senderEmail: Scalars['String']['output'];
  smtpPassword?: Maybe<Scalars['String']['output']>;
  smtpPort: Scalars['Int']['output'];
  smtpServer: Scalars['String']['output'];
  smtpUsername: Scalars['String']['output'];
  useTls: Scalars['Boolean']['output'];
};

export type SmtpSettingsInput = {
  senderEmail: Scalars['String']['input'];
  smtpPassword: Scalars['String']['input'];
  smtpPort: Scalars['Int']['input'];
  smtpServer: Scalars['String']['input'];
  smtpUsername: Scalars['String']['input'];
  useTls: Scalars['Boolean']['input'];
};

export type StockConsumptionLog = {
  batch: Batch;
  batchId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy: Scalars['Int']['output'];
  creator: User;
  id: Scalars['Int']['output'];
  ingredient: Ingredient;
  ingredientId: Scalars['Int']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  productionOrderId?: Maybe<Scalars['Int']['output']>;
  quantity: Scalars['Decimal']['output'];
  reason: Scalars['String']['output'];
};

export type StorageZone = {
  assetType: Scalars['String']['output'];
  companyId: Scalars['Int']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  tempMax?: Maybe<Scalars['Float']['output']>;
  tempMin?: Maybe<Scalars['Float']['output']>;
  zoneType: Scalars['String']['output'];
};

export type StorageZoneInput = {
  assetType?: InputMaybe<Scalars['String']['input']>;
  companyId: Scalars['Int']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  name: Scalars['String']['input'];
  tempMax?: InputMaybe<Scalars['Float']['input']>;
  tempMin?: InputMaybe<Scalars['Float']['input']>;
  zoneType?: InputMaybe<Scalars['String']['input']>;
};

export type Supplier = {
  address?: Maybe<Scalars['String']['output']>;
  companyId: Scalars['Int']['output'];
  contactPerson?: Maybe<Scalars['String']['output']>;
  eik?: Maybe<Scalars['String']['output']>;
  email?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  phone?: Maybe<Scalars['String']['output']>;
  vatNumber?: Maybe<Scalars['String']['output']>;
};

export type SupplierInput = {
  address?: InputMaybe<Scalars['String']['input']>;
  companyId: Scalars['Int']['input'];
  contactPerson?: InputMaybe<Scalars['String']['input']>;
  eik?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  phone?: InputMaybe<Scalars['String']['input']>;
  vatNumber?: InputMaybe<Scalars['String']['input']>;
};

export type Terminal = {
  alias?: Maybe<Scalars['String']['output']>;
  deviceModel?: Maybe<Scalars['String']['output']>;
  deviceName?: Maybe<Scalars['String']['output']>;
  deviceType?: Maybe<Scalars['String']['output']>;
  gatewayId?: Maybe<Scalars['Int']['output']>;
  hardwareUuid: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  lastSeen?: Maybe<Scalars['DateTime']['output']>;
  mode: Scalars['String']['output'];
  osVersion?: Maybe<Scalars['String']['output']>;
  totalScans: Scalars['Int']['output'];
};

export type TerminalOrder = {
  id: Scalars['Int']['output'];
  instructions?: Maybe<Scalars['String']['output']>;
  orderNumber: Scalars['String']['output'];
  productName: Scalars['String']['output'];
  quantity: Scalars['Int']['output'];
  recipeName: Scalars['String']['output'];
  status: Scalars['String']['output'];
  tasks: Array<TerminalTask>;
};

export type TerminalTask = {
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  quantity: Scalars['Int']['output'];
  status: Scalars['String']['output'];
};

export type TimeLog = {
  breakDurationMinutes: Scalars['Int']['output'];
  endTime?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  isManual: Scalars['Boolean']['output'];
  startTime: Scalars['DateTime']['output'];
  user?: Maybe<User>;
  userId: Scalars['Int']['output'];
};

export type UpdateCostCenterInput = {
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  id: Scalars['Int']['input'];
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateLeaveRequestStatusInput = {
  adminComment?: InputMaybe<Scalars['String']['input']>;
  employerTopUp?: InputMaybe<Scalars['Boolean']['input']>;
  requestId: Scalars['Int']['input'];
  status: Scalars['String']['input'];
};

export type UpdateStorageZoneInput = {
  assetType?: InputMaybe<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  managerId?: InputMaybe<Scalars['Int']['input']>;
  name: Scalars['String']['input'];
  tempMax?: InputMaybe<Scalars['Float']['input']>;
  tempMin?: InputMaybe<Scalars['Float']['input']>;
  zoneType?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateSupplierInput = {
  address?: InputMaybe<Scalars['String']['input']>;
  contactPerson?: InputMaybe<Scalars['String']['input']>;
  eik?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  name: Scalars['String']['input'];
  phone?: InputMaybe<Scalars['String']['input']>;
  vatNumber?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateUserInput = {
  address?: InputMaybe<Scalars['String']['input']>;
  baseSalary?: InputMaybe<Scalars['Decimal']['input']>;
  birthDate?: InputMaybe<Scalars['Date']['input']>;
  companyId?: InputMaybe<Scalars['Int']['input']>;
  contractEndDate?: InputMaybe<Scalars['Date']['input']>;
  contractNumber?: InputMaybe<Scalars['String']['input']>;
  contractStartDate?: InputMaybe<Scalars['Date']['input']>;
  contractType?: InputMaybe<Scalars['String']['input']>;
  dangerousWork?: InputMaybe<Scalars['Boolean']['input']>;
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  egn?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  experienceStartDate?: InputMaybe<Scalars['Date']['input']>;
  firstName?: InputMaybe<Scalars['String']['input']>;
  hasIncomeTax?: InputMaybe<Scalars['Boolean']['input']>;
  holidayRate?: InputMaybe<Scalars['Float']['input']>;
  iban?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  insuranceContributor?: InputMaybe<Scalars['Boolean']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  lastName?: InputMaybe<Scalars['String']['input']>;
  monthlyAdvanceAmount?: InputMaybe<Scalars['Decimal']['input']>;
  nightWorkRate?: InputMaybe<Scalars['Float']['input']>;
  overtimeRate?: InputMaybe<Scalars['Float']['input']>;
  password?: InputMaybe<Scalars['String']['input']>;
  passwordForceChange?: InputMaybe<Scalars['Boolean']['input']>;
  paymentDay?: InputMaybe<Scalars['Int']['input']>;
  phoneNumber?: InputMaybe<Scalars['String']['input']>;
  positionId?: InputMaybe<Scalars['Int']['input']>;
  probationMonths?: InputMaybe<Scalars['Int']['input']>;
  roleId?: InputMaybe<Scalars['Int']['input']>;
  salaryCalculationType?: InputMaybe<Scalars['String']['input']>;
  salaryInstallmentsCount?: InputMaybe<Scalars['Int']['input']>;
  surname?: InputMaybe<Scalars['String']['input']>;
  taxResident?: InputMaybe<Scalars['Boolean']['input']>;
  username?: InputMaybe<Scalars['String']['input']>;
  workClass?: InputMaybe<Scalars['String']['input']>;
  workHoursPerWeek?: InputMaybe<Scalars['Int']['input']>;
};

export type User = {
  accessibleZones: Array<AccessZone>;
  activeContract?: Maybe<EmploymentContract>;
  address?: Maybe<Scalars['String']['output']>;
  birthDate?: Maybe<Scalars['Date']['output']>;
  bonuses: Array<Bonus>;
  company?: Maybe<Company>;
  companyId?: Maybe<Scalars['Int']['output']>;
  /** @deprecated Use company relation */
  companyLegacy?: Maybe<Scalars['String']['output']>;
  companyName?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  currentSchedule?: Maybe<WorkSchedule>;
  department?: Maybe<Department>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  /** @deprecated Use department relation */
  departmentLegacy?: Maybe<Scalars['String']['output']>;
  departmentName?: Maybe<Scalars['String']['output']>;
  egn?: Maybe<Scalars['String']['output']>;
  email?: Maybe<Scalars['String']['output']>;
  employmentContract?: Maybe<EmploymentContract>;
  failedLoginAttempts: Scalars['Int']['output'];
  firstName?: Maybe<Scalars['String']['output']>;
  iban?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  isSmtpConfigured: Scalars['Boolean']['output'];
  jobTitle?: Maybe<Scalars['String']['output']>;
  /** @deprecated Use position relation */
  jobTitleLegacy?: Maybe<Scalars['String']['output']>;
  lastLogin?: Maybe<Scalars['DateTime']['output']>;
  lastName?: Maybe<Scalars['String']['output']>;
  leaveBalance?: Maybe<LeaveBalance>;
  lockedUntil?: Maybe<Scalars['DateTime']['output']>;
  passwordForceChange: Scalars['Boolean']['output'];
  payrolls: Array<Payroll>;
  payslips: Array<Payslip>;
  phoneNumber?: Maybe<Scalars['String']['output']>;
  /** @deprecated Use egn instead */
  pin?: Maybe<Scalars['String']['output']>;
  position?: Maybe<Position>;
  positionId?: Maybe<Scalars['Int']['output']>;
  profilePicture?: Maybe<Scalars['String']['output']>;
  qrToken?: Maybe<Scalars['String']['output']>;
  role: Role;
  roleId: Scalars['Int']['output'];
  surname?: Maybe<Scalars['String']['output']>;
  timelogs: Array<TimeLog>;
  username?: Maybe<Scalars['String']['output']>;
};


export type UserLeaveBalanceArgs = {
  year?: InputMaybe<Scalars['Int']['input']>;
};


export type UserTimelogsArgs = {
  endDate?: InputMaybe<Scalars['Date']['input']>;
  startDate?: InputMaybe<Scalars['Date']['input']>;
};

export type UserCreateInput = {
  address?: InputMaybe<Scalars['String']['input']>;
  baseSalary?: InputMaybe<Scalars['Decimal']['input']>;
  birthDate?: InputMaybe<Scalars['Date']['input']>;
  companyId?: InputMaybe<Scalars['Int']['input']>;
  contractEndDate?: InputMaybe<Scalars['Date']['input']>;
  contractNumber?: InputMaybe<Scalars['String']['input']>;
  contractStartDate?: InputMaybe<Scalars['Date']['input']>;
  contractType?: InputMaybe<Scalars['String']['input']>;
  dangerousWork?: InputMaybe<Scalars['Boolean']['input']>;
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  egn?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  experienceStartDate?: InputMaybe<Scalars['Date']['input']>;
  firstName?: InputMaybe<Scalars['String']['input']>;
  hasIncomeTax?: InputMaybe<Scalars['Boolean']['input']>;
  holidayRate?: InputMaybe<Scalars['Decimal']['input']>;
  iban?: InputMaybe<Scalars['String']['input']>;
  insuranceContributor?: InputMaybe<Scalars['Boolean']['input']>;
  lastName?: InputMaybe<Scalars['String']['input']>;
  monthlyAdvanceAmount?: InputMaybe<Scalars['Decimal']['input']>;
  nightWorkRate?: InputMaybe<Scalars['Decimal']['input']>;
  overtimeRate?: InputMaybe<Scalars['Decimal']['input']>;
  password: Scalars['String']['input'];
  passwordForceChange?: InputMaybe<Scalars['Boolean']['input']>;
  paymentDay?: InputMaybe<Scalars['Int']['input']>;
  phoneNumber?: InputMaybe<Scalars['String']['input']>;
  positionId?: InputMaybe<Scalars['Int']['input']>;
  probationMonths?: InputMaybe<Scalars['Int']['input']>;
  roleId?: InputMaybe<Scalars['Int']['input']>;
  salaryCalculationType?: InputMaybe<Scalars['String']['input']>;
  salaryInstallmentsCount?: InputMaybe<Scalars['Int']['input']>;
  surname?: InputMaybe<Scalars['String']['input']>;
  taxResident?: InputMaybe<Scalars['Boolean']['input']>;
  username?: InputMaybe<Scalars['String']['input']>;
  workClass?: InputMaybe<Scalars['String']['input']>;
  workHoursPerWeek?: InputMaybe<Scalars['Int']['input']>;
};

export type UserPresence = {
  actualArrival?: Maybe<Scalars['DateTime']['output']>;
  actualDeparture?: Maybe<Scalars['DateTime']['output']>;
  isOnDuty: Scalars['Boolean']['output'];
  shiftEnd?: Maybe<Scalars['Time']['output']>;
  shiftStart?: Maybe<Scalars['Time']['output']>;
  status: PresenceStatus;
  user: User;
};

export type UserSession = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  deviceType?: Maybe<Scalars['String']['output']>;
  expiresAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  ipAddress?: Maybe<Scalars['String']['output']>;
  isActive: Scalars['Boolean']['output'];
  lastUsedAt?: Maybe<Scalars['DateTime']['output']>;
  refreshTokenJti: Scalars['String']['output'];
  user: User;
  userAgent?: Maybe<Scalars['String']['output']>;
  userId: Scalars['Int']['output'];
};

export type VatRegister = {
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  periodMonth: Scalars['Int']['output'];
  periodYear: Scalars['Int']['output'];
  vatAdjustment: Scalars['Decimal']['output'];
  vatCollected0: Scalars['Decimal']['output'];
  vatCollected9: Scalars['Decimal']['output'];
  vatCollected20: Scalars['Decimal']['output'];
  vatCredit: Scalars['Decimal']['output'];
  vatDue: Scalars['Decimal']['output'];
  vatPaid0: Scalars['Decimal']['output'];
  vatPaid9: Scalars['Decimal']['output'];
  vatPaid20: Scalars['Decimal']['output'];
};

export type VatRegisterInput = {
  companyId: Scalars['Int']['input'];
  periodMonth: Scalars['Int']['input'];
  periodYear: Scalars['Int']['input'];
};

export type Vehicle = {
  chassisNumber?: Maybe<Scalars['String']['output']>;
  color?: Maybe<Scalars['String']['output']>;
  companyId: Scalars['Int']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  engineNumber?: Maybe<Scalars['String']['output']>;
  fuelType: FuelType;
  id: Scalars['Int']['output'];
  initialMileage?: Maybe<Scalars['Int']['output']>;
  isCompany?: Maybe<Scalars['Boolean']['output']>;
  make: Scalars['String']['output'];
  model: Scalars['String']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  ownerName?: Maybe<Scalars['String']['output']>;
  registrationNumber: Scalars['String']['output'];
  status: VehicleStatus;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicleTypeId?: Maybe<Scalars['Int']['output']>;
  vin?: Maybe<Scalars['String']['output']>;
  year?: Maybe<Scalars['Int']['output']>;
};

export type VehicleCostCenter = {
  companyId: Scalars['Int']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  id: Scalars['Int']['output'];
  isActive?: Maybe<Scalars['Boolean']['output']>;
  name: Scalars['String']['output'];
};

export type VehicleCreateInput = {
  color?: InputMaybe<Scalars['String']['input']>;
  companyId?: InputMaybe<Scalars['Int']['input']>;
  fuelType?: InputMaybe<Scalars['String']['input']>;
  initialMileage?: InputMaybe<Scalars['Int']['input']>;
  isCompanyVehicle?: InputMaybe<Scalars['Boolean']['input']>;
  make: Scalars['String']['input'];
  model?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  registrationNumber: Scalars['String']['input'];
  status?: InputMaybe<Scalars['String']['input']>;
  vehicleType?: InputMaybe<Scalars['String']['input']>;
  vin?: InputMaybe<Scalars['String']['input']>;
  year?: InputMaybe<Scalars['Int']['input']>;
};

export type VehicleDocument = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentType: VehicleDocumentType;
  expiryDate?: Maybe<Scalars['Date']['output']>;
  fileUrl?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  issueDate?: Maybe<Scalars['Date']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  title: Scalars['String']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleDocumentType =
  | 'CONTRACT'
  | 'INSPECTION'
  | 'INVOICE'
  | 'OTHER'
  | 'POLICY';

export type VehicleDriver = {
  assignedFrom: Scalars['Date']['output'];
  assignedTo?: Maybe<Scalars['Date']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  isPrimary?: Maybe<Scalars['Boolean']['output']>;
  userId: Scalars['Int']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleDriverInput = {
  category?: InputMaybe<Scalars['String']['input']>;
  isPrimary?: InputMaybe<Scalars['Boolean']['input']>;
  licenseExpiry: Scalars['DateTime']['input'];
  licenseNumber: Scalars['String']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  phone?: InputMaybe<Scalars['String']['input']>;
  userId: Scalars['Int']['input'];
  vehicleId: Scalars['Int']['input'];
};

export type VehicleDriverUpdateInput = {
  category?: InputMaybe<Scalars['String']['input']>;
  isPrimary?: InputMaybe<Scalars['Boolean']['input']>;
  licenseExpiry?: InputMaybe<Scalars['DateTime']['input']>;
  licenseNumber?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  phone?: InputMaybe<Scalars['String']['input']>;
};

export type VehicleFuel = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['DateTime']['output'];
  driverId?: Maybe<Scalars['Int']['output']>;
  fuelCardId?: Maybe<Scalars['Int']['output']>;
  fuelType?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  invoiceNumber?: Maybe<Scalars['String']['output']>;
  location?: Maybe<Scalars['String']['output']>;
  mileage?: Maybe<Scalars['Int']['output']>;
  pricePerLiter: Scalars['Float']['output'];
  quantity: Scalars['Float']['output'];
  totalAmount: Scalars['Float']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleFuelInput = {
  date: Scalars['DateTime']['input'];
  fuelType?: InputMaybe<Scalars['String']['input']>;
  liters: Scalars['Float']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  price: Scalars['Float']['input'];
  total: Scalars['Float']['input'];
  vehicleId: Scalars['Int']['input'];
};

export type VehicleFuelUpdateInput = {
  date?: InputMaybe<Scalars['DateTime']['input']>;
  fuelType?: InputMaybe<Scalars['String']['input']>;
  liters?: InputMaybe<Scalars['Float']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  price?: InputMaybe<Scalars['Float']['input']>;
  total?: InputMaybe<Scalars['Float']['input']>;
};

export type VehicleInspection = {
  certificateNumber?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  inspectionDate: Scalars['Date']['output'];
  inspector?: Maybe<Scalars['String']['output']>;
  mileage?: Maybe<Scalars['Int']['output']>;
  nextInspectionDate?: Maybe<Scalars['Date']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  result: InspectionResult;
  validUntil: Scalars['Date']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleInspectionInput = {
  cost?: InputMaybe<Scalars['Float']['input']>;
  date: Scalars['DateTime']['input'];
  nextDate?: InputMaybe<Scalars['DateTime']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  protocolNumber?: InputMaybe<Scalars['String']['input']>;
  result?: InputMaybe<Scalars['String']['input']>;
  vehicleId: Scalars['Int']['input'];
};

export type VehicleInspectionUpdateInput = {
  cost?: InputMaybe<Scalars['Float']['input']>;
  date?: InputMaybe<Scalars['DateTime']['input']>;
  nextDate?: InputMaybe<Scalars['DateTime']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  protocolNumber?: InputMaybe<Scalars['String']['input']>;
  result?: InputMaybe<Scalars['String']['input']>;
};

export type VehicleInsurance = {
  coverageAmount?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentUrl?: Maybe<Scalars['String']['output']>;
  endDate: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  insuranceCompany?: Maybe<Scalars['String']['output']>;
  insuranceType: InsuranceType;
  notes?: Maybe<Scalars['String']['output']>;
  paymentType?: Maybe<Scalars['String']['output']>;
  policyNumber: Scalars['String']['output'];
  premium?: Maybe<Scalars['Float']['output']>;
  startDate: Scalars['Date']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleInsuranceInput = {
  endDate: Scalars['DateTime']['input'];
  insuranceType?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  policyNumber: Scalars['String']['input'];
  premium?: InputMaybe<Scalars['Float']['input']>;
  provider: Scalars['String']['input'];
  startDate: Scalars['DateTime']['input'];
  vehicleId: Scalars['Int']['input'];
};

export type VehicleInsuranceUpdateInput = {
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  insuranceType?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  policyNumber?: InputMaybe<Scalars['String']['input']>;
  premium?: InputMaybe<Scalars['Float']['input']>;
  provider?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['DateTime']['input']>;
};

export type VehicleMileage = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  mileage: Scalars['Int']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  source?: Maybe<Scalars['String']['output']>;
  vehicleId: Scalars['Int']['output'];
};

export type VehicleMileageInput = {
  date: Scalars['DateTime']['input'];
  mileage: Scalars['Int']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  vehicleId: Scalars['Int']['input'];
};

export type VehicleMileageUpdateInput = {
  date?: InputMaybe<Scalars['DateTime']['input']>;
  mileage?: InputMaybe<Scalars['Int']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
};

export type VehicleRepair = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  laborCost?: Maybe<Scalars['Float']['output']>;
  laborHours?: Maybe<Scalars['Float']['output']>;
  mileage?: Maybe<Scalars['Int']['output']>;
  nextServiceKm?: Maybe<Scalars['Int']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  parts?: Maybe<Scalars['JSONScalar']['output']>;
  partsCost?: Maybe<Scalars['Float']['output']>;
  repairDate: Scalars['DateTime']['output'];
  repairType?: Maybe<Scalars['String']['output']>;
  totalCost?: Maybe<Scalars['Float']['output']>;
  vehicleId: Scalars['Int']['output'];
  vehicleServiceId?: Maybe<Scalars['Int']['output']>;
  warrantyMonths?: Maybe<Scalars['Int']['output']>;
};

export type VehicleRepairInput = {
  cost?: InputMaybe<Scalars['Float']['input']>;
  date: Scalars['DateTime']['input'];
  description: Scalars['String']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  repairType?: InputMaybe<Scalars['String']['input']>;
  vehicleId: Scalars['Int']['input'];
};

export type VehicleRepairUpdateInput = {
  cost?: InputMaybe<Scalars['Float']['input']>;
  date?: InputMaybe<Scalars['DateTime']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  repairType?: InputMaybe<Scalars['String']['input']>;
};

export type VehicleStatus =
  | 'ACTIVE'
  | 'IN_REPAIR'
  | 'OUT_OF_SERVICE'
  | 'SOLD';

export type VehicleTrip = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  deliveryId?: Maybe<Scalars['Int']['output']>;
  distanceKm?: Maybe<Scalars['Int']['output']>;
  driverId: Scalars['Int']['output'];
  endAddress?: Maybe<Scalars['String']['output']>;
  endTime?: Maybe<Scalars['DateTime']['output']>;
  expenses?: Maybe<Scalars['Float']['output']>;
  id: Scalars['Int']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  purpose?: Maybe<Scalars['String']['output']>;
  startAddress?: Maybe<Scalars['String']['output']>;
  startTime?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicleId: Scalars['Int']['output'];
};

export type VehicleTripInput = {
  distance?: InputMaybe<Scalars['Float']['input']>;
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  endLocation?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  startDate: Scalars['DateTime']['input'];
  startLocation?: InputMaybe<Scalars['String']['input']>;
  tripType?: InputMaybe<Scalars['String']['input']>;
  userId: Scalars['Int']['input'];
  vehicleId: Scalars['Int']['input'];
};

export type VehicleTripUpdateInput = {
  distance?: InputMaybe<Scalars['Float']['input']>;
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  endLocation?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['DateTime']['input']>;
  startLocation?: InputMaybe<Scalars['String']['input']>;
  tripType?: InputMaybe<Scalars['String']['input']>;
};

export type VehicleType = {
  code?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
};

export type VehicleUpdateInput = {
  color?: InputMaybe<Scalars['String']['input']>;
  fuelType?: InputMaybe<Scalars['String']['input']>;
  initialMileage?: InputMaybe<Scalars['Int']['input']>;
  isCompanyVehicle?: InputMaybe<Scalars['Boolean']['input']>;
  make?: InputMaybe<Scalars['String']['input']>;
  model?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  registrationNumber?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
  vehicleType?: InputMaybe<Scalars['String']['input']>;
  vin?: InputMaybe<Scalars['String']['input']>;
  year?: InputMaybe<Scalars['Int']['input']>;
};

export type Webhook = {
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  events: Array<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  url: Scalars['String']['output'];
};

export type WeeklySummary = {
  debtHours: Scalars['Decimal']['output'];
  endDate: Scalars['Date']['output'];
  startDate: Scalars['Date']['output'];
  statusMessage: Scalars['String']['output'];
  surplusHours: Scalars['Decimal']['output'];
  targetHours: Scalars['Decimal']['output'];
  totalOvertimeHours: Scalars['Decimal']['output'];
  totalRegularHours: Scalars['Decimal']['output'];
};

export type WorkExperience = {
  classLevel?: Maybe<Scalars['String']['output']>;
  companyId?: Maybe<Scalars['Int']['output']>;
  companyName: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  endDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['Int']['output'];
  isCurrent: Scalars['Boolean']['output'];
  months: Scalars['Int']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  position?: Maybe<Scalars['String']['output']>;
  startDate: Scalars['Date']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  user: User;
  userId: Scalars['Int']['output'];
  years: Scalars['Int']['output'];
};

export type WorkSchedule = {
  date: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  shift?: Maybe<Shift>;
  shiftId: Scalars['Int']['output'];
  user: User;
  userId: Scalars['Int']['output'];
};

export type Workstation = {
  companyId: Scalars['Int']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
};

export type YearlySummaryType = {
  cashBalance: Scalars['Float']['output'];
  cashExpense: Scalars['Float']['output'];
  cashIncome: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  incomingInvoicesCount: Scalars['Int']['output'];
  incomingInvoicesTotal: Scalars['Float']['output'];
  invoicesCount: Scalars['Int']['output'];
  invoicesTotal: Scalars['Float']['output'];
  outgoingInvoicesCount: Scalars['Int']['output'];
  outgoingInvoicesTotal: Scalars['Float']['output'];
  overdueInvoicesCount: Scalars['Int']['output'];
  paidInvoicesCount: Scalars['Int']['output'];
  unpaidInvoicesCount: Scalars['Int']['output'];
  vatCollected: Scalars['Float']['output'];
  vatPaid: Scalars['Float']['output'];
  year: Scalars['Int']['output'];
};
