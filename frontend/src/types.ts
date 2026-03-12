export interface Role {
  id: number;
  name: string;
  description?: string | null;
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
  contractType: string;
  startDate: string;
  endDate?: string | null;
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
}

export interface User {
  id: number;
  email: string;
  username?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  phoneNumber?: string | null;
  address?: string | null;
  egn?: string | null;
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
  shiftType: 'regular' | 'night' | 'weekend' | 'holiday' | 'missing';
}

export interface WorkSchedule {
  id: number;
  date: string;
  user: User;
  shift?: Shift | null;
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
  quantityGross: number;
  workstation?: Workstation | null;
}

export interface RecipeStep {
  id: number;
  name: string;
  stepOrder: number;
  estimatedDurationMinutes?: number | null;
  workstation: Workstation;
}

export interface RecipeSection {
  id: number;
  name: string;
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
  status: string;
  isCorrected?: boolean;
  batch?: Batch | null;
  items?: InvoiceItem[];
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
}

export interface StorageZone {
  id: number;
  name: string;
  description?: string | null;
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
  expiryDate?: string | null;
  receivedDate: string;
  cost?: number | null;
  status: string;
  storageZone?: StorageZone | null;
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
}

export interface OfficeLocation {
  latitude: number;
  longitude: number;
  radius: number;
  entryEnabled: boolean;
  exitEnabled: boolean;
}
