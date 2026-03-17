export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  
  if (typeof error === 'object' && error !== null) {
    const err = error as { 
      response?: { data?: { detail?: string | { message?: string } } }; 
      message?: string;
      graphQLErrors?: Array<{ message?: string }>;
      networkError?: { message?: string };
    };
    
    if (err.graphQLErrors && err.graphQLErrors.length > 0) {
      return err.graphQLErrors[0].message || 'Грешка от сървъра';
    }
    
    if (err.networkError) {
      return 'Няма връзка със сървъра';
    }
    
    if (err.response?.data?.detail) {
      if (typeof err.response.data.detail === 'string') return err.response.data.detail;
      if (err.response.data.detail.message) return err.response.data.detail.message;
    }
    if (err.message) return err.message;
  }
  
  return 'Неизвестна грешка';
}

export interface Role {
  id: number;
  name: string;
  description?: string | null;
}

export interface Module {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  isEnabled: boolean;
  isPremium?: boolean;
}

export interface Company {
  id: number;
  name: string;
  eik?: string | null;
  bulstat?: string | null;
  vatNumber?: string | null;
  address?: string | null;
  molName?: string | null;
}

export interface Department {
  id: number;
  name: string;
  companyId?: number | null;
  company?: Company | null;
  manager?: User | null;
}

export interface Position {
  id: number;
  title: string;
  departmentId?: number | null;
  department?: Department | null;
}

export interface EmploymentContract {
  id: number;
  contractNumber?: string | null;
  contractType: string;
  startDate: string;
  endDate?: string | null;
  isActive?: boolean;
  baseSalary?: string | number | null;
  workHoursPerWeek?: number | null;
  probationMonths?: number | null;
  salaryCalculationType?: string | null;
  salaryInstallmentsCount?: number | null;
  monthlyAdvanceAmount?: string | number | null;
  taxResident?: boolean;
  insuranceContributor?: boolean;
  hasIncomeTax?: boolean;
  nightWorkRate?: string | number | null;
  overtimeRate?: string | number | null;
  holidayRate?: string | number | null;
  workClass?: string | null;
  dangerousWork?: boolean;
  position?: Position | null;
  paymentDay?: number | null;
}

export interface UpdateUserInput {
  id?: number;
  email?: string | null;
  username?: string | null;
  firstName?: string | null;
  surname?: string | null;
  lastName?: string | null;
  phoneNumber?: string | null;
  address?: string | null;
  egn?: string | null;
  pin?: string | null;
  birthDate?: string | null;
  iban?: string | null;
  companyId?: number | null;
  departmentId?: number | null;
  positionId?: number | null;
  roleId?: number | null;
  isActive?: boolean;
  passwordForceChange?: boolean;
  password?: string | null;
  contractType?: string | null;
  contractNumber?: string | null;
  contractStartDate?: string | null;
  contractEndDate?: string | null;
  baseSalary?: number | string | null;
  workHoursPerWeek?: number | null;
  probationMonths?: number | null;
  salaryCalculationType?: string | null;
  hasIncomeTax?: boolean;
  insuranceContributor?: boolean;
  salaryInstallmentsCount?: number | null;
  monthlyAdvanceAmount?: number | string | null;
  taxResident?: boolean;
  paymentDay?: number | null;
  nightWorkRate?: number | string | null;
  overtimeRate?: number | string | null;
  holidayRate?: number | string | null;
  workClass?: string | null;
  dangerousWork?: boolean;
}

export interface ContractTemplateSection {
  id: number;
  templateId: number;
  versionId: number;
  title: string;
  content: string | null;
  orderIndex: number;
  isRequired: boolean;
}

export interface ContractTemplateVersion {
  id: number;
  templateId: number;
  version: number;
  contractType: string;
  workHoursPerWeek: number;
  probationMonths: number;
  salaryCalculationType: string;
  paymentDay: number;
  nightWorkRate: number;
  overtimeRate: number;
  holidayRate: number;
  workClass: string | null;
  isCurrent: boolean;
  createdBy: string | null;
  createdAt: string;
  changeNote: string | null;
  sections?: ContractTemplateSection[];
}

export interface ContractTemplate {
  id: number;
  companyId: number;
  name: string;
  description: string | null;
  contractType: string;
  workHoursPerWeek: number;
  probationMonths: number;
  salaryCalculationType: string;
  paymentDay: number;
  nightWorkRate: number;
  overtimeRate: number;
  holidayRate: number;
  workClass: string | null;
  isActive: boolean;
  createdAt: string;
  currentVersion?: ContractTemplateVersion | null;
}

export interface AnnexTemplateSection {
  id: number;
  templateId: number;
  versionId: number;
  title: string;
  content: string | null;
  orderIndex: number;
  isRequired: boolean;
}

export interface AnnexTemplateVersion {
  id: number;
  templateId: number;
  version: number;
  changeType: string;
  newBaseSalary: number | null;
  newWorkHoursPerWeek: number | null;
  newNightWorkRate: number | null;
  newOvertimeRate: number | null;
  newHolidayRate: number | null;
  isCurrent: boolean;
  createdBy: string | null;
  createdAt: string;
  changeNote: string | null;
  sections?: AnnexTemplateSection[];
}

export interface AnnexTemplate {
  id: number;
  companyId: number;
  name: string;
  description: string | null;
  changeType: string;
  newBaseSalary: number | null;
  newWorkHoursPerWeek: number | null;
  newNightWorkRate: number | null;
  newOvertimeRate: number | null;
  newHolidayRate: number | null;
  isActive: boolean;
  createdAt: string;
  currentVersion?: AnnexTemplateVersion | null;
}

export interface ClauseTemplate {
  id: number;
  companyId: number;
  title: string;
  content: string | null;
  category: string;
  isActive: boolean;
  createdAt: string;
}

export interface ContractAnnex {
  id: number;
  contractId: number;
  annexNumber: string | null;
  effectiveDate: string;
  baseSalary: number | null;
  positionId: number | null;
  workHoursPerWeek: number | null;
  nightWorkRate: number | null;
  overtimeRate: number | null;
  holidayRate: number | null;
  isSigned: boolean;
  signedAt: string | null;
  status: string;
  templateId: number | null;
  changeType: string | null;
  changeDescription: string | null;
  signatureRequestedAt: string | null;
  signedByEmployee: boolean;
  signedByEmployeeAt: string | null;
  signedByEmployer: boolean;
  signedByEmployerAt: string | null;
  rejectionReason: string | null;
  createdAt: string;
  position?: Position | null;
}

export interface User {
  id: number;
  email: string;
  username?: string | null;
  firstName?: string | null;
  surname?: string | null;
  lastName?: string | null;
  phoneNumber?: string | null;
  address?: string | null;
  egn?: string | null;
  pin?: string | null;
  birthDate?: string | null;
  iban?: string | null;
  isActive: boolean;
  passwordForceChange: boolean;
  createdAt?: string | null;
  lastLogin?: string | null;
  company?: Company | null;
  department?: Department | null;
  position?: Position | null;
  role?: Role | null;
  employmentContract?: EmploymentContract | null;
}

export interface Shift {
  id: number;
  name: string;
  startTime: string;
  endTime: string;
  toleranceMinutes: number;
  breakDurationMinutes: number;
  payMultiplier: number;
  shiftType: 'regular' | 'night' | 'weekend' | 'holiday' | 'missing' | 'public_holiday' | 'paid_leave' | 'day_off';
}

export interface WorkSchedule {
  id: number;
  date: string;
  user: User;
  shift?: Shift | null;
  name?: string | null;
  startTime?: string | null;
  endTime?: string | null;
}

export interface PaginatedUsers {
  users: User[];
  totalCount: number;
}

export interface Workstation {
  id: number;
  name: string;
  description?: string | null;
}

export interface Recipe {
  id: number;
  name: string;
}

export interface RecipeIngredient {
  id: number;
  ingredient: Ingredient;
  ingredientId?: number | string | null;
  quantityGross: number;
  quantityNet?: number | null;
  wastePercentage?: number | null;
  originalQuantity?: number | null;
  barcode?: string | null;
  workstation?: Workstation | null;
}

export interface RecipeStep {
  id: number;
  name: string;
  stepOrder: number;
  estimatedDurationMinutes?: number | null;
  workstation: Workstation;
  workstationId?: number;
}

export interface RecipeSection {
  id: number;
  name: string;
  type?: string | null;
  sectionType?: string | null;
  shelfLifeDays?: number | null;
  wastePercentage: number;
  sectionOrder: number;
  ingredients: RecipeIngredient[];
  steps: RecipeStep[];
}

export interface FullRecipe extends Recipe {
  description?: string | null;
  category?: string | null;
  isBase: boolean;
  yieldQuantity?: number | null;
  yieldUnit?: string | null;
  shelfLifeDays?: number | null;
  shelfLifeFrozenDays?: number | null;
  productionDeadlineDays?: number | null;
  defaultPieces?: number | null;
  standardQuantity?: number | null;
  instructions?: string | null;
  ingredients?: RecipeIngredient[];
  steps?: RecipeStep[];
  sections: RecipeSection[];
}

export interface PayrollLegalSettings {
  maxInsuranceBase: number;
  employeeInsuranceRate: number;
  incomeTaxRate: number;
  civilContractCostsRate: number;
  noiCompensationPercent: number;
  employerPaidSickDays: number;
  defaultTaxResident: boolean;
  targetId?: string | null;
  hourlyRate?: number | null;
  monthlySalary?: number | null;
  currency?: string | null;
  annualLeaveDays?: number | null;
  overtimeMultiplier?: number | null;
  standardHoursWeekly?: number | null;
  standardHoursPerDay?: number | null;
  taxPercent?: number | null;
  healthInsurancePercent?: number | null;
  hasTaxDeduction?: boolean | null;
  hasHealthInsurance?: boolean | null;
}

export interface PayrollSummaryInstallment {
  count: number;
  amountPerInstallment: number;
}

export interface PayrollSummaryItem {
  userId: number;
  email: string;
  fullName: string;
  grossAmount: number;
  netAmount: number;
  taxAmount: number;
  insuranceAmount: number;
  bonusAmount: number;
  advances: number;
  loanDeductions: number;
  totalDeductions: number;
  netPayable: number;
  contractType: string;
  installments: PayrollSummaryInstallment[];
}

export interface PayrollConfig {
  hourlyRate: number;
  monthlySalary?: number | null;
  currency: string;
  annualLeaveDays: number;
  overtimeMultiplier: number;
  standardHoursPerDay: number;
  taxPercent: number;
  healthInsurancePercent: number;
  hasTaxDeduction: boolean;
  hasHealthInsurance: boolean;
}

export interface UserWithPayroll extends User {
  payrolls?: PayrollConfig[] | null;
}

export interface PositionWithPayroll extends Position {
  payrolls?: PayrollConfig[] | null;
}

export interface AdvancePayment {
  id: number;
  userId: number;
  amount: number;
  paymentDate: string;
  description?: string | null;
  status: string;
}

export interface ServiceLoan {
  id: number;
  userId: number;
  totalAmount: number;
  remainingAmount: number;
  installmentsCount: number;
  installmentsPaid: number;
  startDate: string;
  description?: string | null;
  status: string;
}

export interface Bonus {
  id: number;
  amount: number;
  date: string;
  description?: string | null;
}

export interface ApiKey {
  id: number;
  name: string;
  keyPrefix: string;
  isActive: boolean;
  createdAt: string;
  lastUsedAt?: string | null;
  permissions?: string[] | null;
}

export interface AuditLog {
  id: number;
  action: string;
  targetType: string;
  targetId?: number | null;
  details?: string | null;
  createdAt: string;
  user?: User | null;
}

export interface Employee {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  qrToken?: string | null;
}

export interface UserDocument {
  id: number;
  filename: string;
  file_type: string;
  is_locked: boolean;
  created_at: string;
}

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
  supplier?: Supplier | null;
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
  batch?: Batch | null;
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

export interface SwapRequest {
  id: number;
  status: string;
  createdAt: string;
  requestor: User;
  targetUser: User;
  requestorScheduleId: number;
  targetScheduleId: number;
  requestorSchedule: WorkSchedule;
  targetSchedule: WorkSchedule;
}

export interface ProductionTask {
  id: number;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'scrap';
  workstation: Workstation;
  startedAt?: string | null;
  completedAt?: string | null;
  quantity?: number;
  instructions?: string | null;
}

export interface ProductionOrder {
  id: number;
  recipe: Recipe;
  quantity: number;
  dueDate: string;
  productionDeadline?: string | null;
  status: string;
  notes?: string | null;
  tasks?: ProductionTask[];
}

export interface TerminalOrder {
  id: number;
  orderNumber: string;
  productName: string;
  quantity: number;
  status: string;
  recipeName?: string | null;
  instructions?: string | null;
  tasks?: ProductionTask[];
}

export interface PublicHoliday {
  id: number;
  date: string;
  name: string;
  localName: string;
  isOrthodox?: boolean;
}

export interface TimeLog {
  id: number;
  startTime: string;
  endTime?: string | null;
  isManual: boolean;
  user: User;
}

export interface ScheduleTemplate {
  id: number;
  name: string;
  description?: string | null;
  items?: ScheduleTemplateItem[];
}

export interface ScheduleTemplateItem {
  dayIndex: number;
  shiftId?: number | null;
  shift?: { name: string } | null;
}

export interface Webhook {
  id: number;
  url: string;
  description?: string | null;
  isActive: boolean;
  events?: string[];
}

export interface UserPresence {
  user: {
    id: number;
    firstName?: string | null;
    lastName?: string | null;
    email: string;
  };
  shiftStart?: string | null;
  shiftEnd?: string | null;
  actualArrival?: string | null;
  actualDeparture?: string | null;
  status: string;
}

export interface StorageZone {
  id: number;
  name: string;
  description?: string | null;
  tempMin?: number | null;
  tempMax?: number | null;
  isActive?: boolean | null;
  assetType?: string | null;
  zoneType?: string | null;
}

export interface Supplier {
  id: number;
  name: string;
  eik?: string | null;
  vatNumber?: string | null;
  address?: string | null;
  contactPerson?: string | null;
  email?: string | null;
  phone?: string | null;
}

export interface Batch {
  id: number;
  ingredientId: number;
  supplierId?: number | null;
  quantity: number;
  originalQuantity: number;
  batchNumber?: string | null;
  invoiceNumber?: string | null;
  expiryDate?: string | null;
  receivedDate: string;
  cost?: number | null;
  status: string;
  storageZone?: StorageZone | null;
  storageZoneId?: number | null;
  ingredient?: Ingredient | null;
  supplier?: Supplier | null;
}

export interface Ingredient {
  id: number;
  name: string;
  barcode?: string | null;
  unit: string;
  currentStock: number;
  baselineMinStock: number;
  isPerishable: boolean;
  expiryWarningDays: number;
  productType: string;
  currentPrice?: number | null;
  storageZone?: StorageZone | null;
  batches?: Batch[];
}

export interface InventorySession {
  id: number;
  startedAt: string;
  completedAt?: string | null;
  status: 'active' | 'completed' | 'cancelled';
  protocolNumber?: string | null;
}

export interface InventorySessionItem {
  id: number;
  ingredientId: number;
  ingredientName: string;
  ingredientUnit: string;
  foundQuantity: number;
  systemQuantity: number;
  difference: number;
  adjusted: boolean;
}

export interface ActiveSession {
  id: string;
  user: { email: string };
  ipAddress?: string | null;
  userAgent?: string | null;
  expiresAt: string;
  lastUsedAt?: string | null;
}

export interface OfficeLocation {
  latitude: number;
  longitude: number;
  radius: number;
  entryEnabled: boolean;
  exitEnabled: boolean;
}

export interface UserDailyStat {
  date: string;
  shiftName?: string | null;
  actualArrival?: string | null;
  actualDeparture?: string | null;
  regularHours: number;
  overtimeHours: number;
  totalWorkedHours: number;
  isWorkDay: boolean;
}

export interface PayrollForecastItem {
  departmentName: string;
  amount: number;
}

export interface LabelData {
  barcode: string;
  productName: string;
  quantity?: number;
}

export interface CalendarEvent {
  title: string;
  start: string | Date;
  end?: string | Date;
  allDay?: boolean;
  extendedProps?: {
    isHoliday?: boolean;
    isLog?: boolean;
    isManual?: boolean;
    shiftName?: string;
    userId?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface ActiveTimeLog {
  id: number;
  startTime: string;
  endTime?: string | null;
  userId: number;
}

export interface WebAuthnCredential {
  id: string;
  type: string;
  transports?: string[];
}

export interface WebAuthnOptions {
  challenge: string;
  rpId?: string;
  allowCredentials?: WebAuthnCredential[];
  timeout?: number;
  userVerification?: 'required' | 'preferred' | 'discouraged';
}

export interface BiometricError {
  message: string;
  code?: string;
}

export interface OrderStatus {
  id: number;
  name: string;
  color?: string;
}

export interface Order {
  id: number;
  dueDate?: string;
  notes?: string;
  quantity?: number;
  tasks?: { id: number; name: string }[];
  status?: string;
  clientName?: string;
  clientPhone?: string;
  total?: number;
  createdAt?: string;
  productionDeadline?: string | null;
  recipe?: { 
    id: number; 
    name: string;
    ingredients?: { 
      ingredient: { name: string; unit: string; currentStock: number | null }; 
      quantityNet: number 
    }[] 
  };
  productionRecordByOrder?: {
    workers?: { id: number; name: string }[];
    ingredients?: { id: number; name: string; quantity: number }[];
  };
}

export interface ScheduleLog {
  id: number;
  logId?: number;
  userId: number;
  date: string;
  shiftName?: string;
  startTime?: string;
  endTime?: string;
  start?: string | Date;
  end?: string | Date;
  isManual?: boolean;
}

export interface SaftResult {
  xmlContent?: string;
  fileName?: string;
  validationResult?: unknown;
}

export interface Terminal {
  id: number;
  hardwareUuid: string;
  alias?: string;
  mode?: string;
  isActive?: boolean;
  deviceName?: string;
  deviceModel?: string;
  osVersion?: string;
  lastSeen?: string;
  [key: string]: unknown;
}

export interface Gateway {
  id: number;
  name: string;
  ipAddress?: string;
  isActive?: boolean;
  alias?: string;
  lastHeartbeat?: string;
  [key: string]: unknown;
}

export interface AccessZone {
  id: number;
  name: string;
  zoneId?: number;
  authorizedUsers?: { id: number; firstName?: string; lastName?: string }[];
  level?: number;
  requiredHoursStart?: string;
  requiredHours_end?: string;
  antiPassbackEnabled?: boolean;
  antiPassbackType?: string;
  [key: string]: unknown;
}

export interface AccessDoor {
  id: number;
  name: string;
  terminalId?: string;
  zoneId?: number;
  isOnline?: boolean;
  zone?: string;
  zoneDbId?: number;
  deviceId?: string;
  relayNumber?: number;
  doorId?: number;
  [key: string]: unknown;
}

export interface LabelData {
  barcode: string;
  productName: string;
  quantity?: number;
  expiryDate?: string;
  qrCodeContent?: string;
  batchNumber?: string;
}

export interface AccessDoor {
  id: number;
  name: string;
  terminalId?: string;
  zoneId?: number;
  isOnline?: boolean;
  zone?: string;
  zoneDbId?: number;
  deviceId?: string;
  relayNumber?: number;
}

export interface AccessCode {
  id: number;
  code: string;
  zoneId?: number;
  isActive?: boolean;
  usesRemaining?: number;
  codeType?: string;
  [key: string]: unknown;
}

export interface AccessLog {
  id: number;
  timestamp: string;
  userId?: number;
  doorId?: number;
  userName?: string;
  zoneName?: string;
  result?: string;
}

export interface Company {
  id: number;
  name: string;
}
