export interface TimeLog {
  id: number;
  startTime: string;
  endTime?: string | null;
  isManual: boolean;
  userId: number;
  user?: { id: number; firstName?: string | null; lastName?: string | null; email: string } | null;
}

export interface Workstation {
  id: number;
  name: string;
  description?: string | null;
}

export interface ActiveTimeLog {
  id: number;
  startTime: string;
  endTime?: string | null;
  userId: number;
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

export interface PublicHoliday {
  id: number;
  date: string;
  name: string;
  localName: string;
  isOrthodox?: boolean;
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

export interface SwapRequest {
  id: number;
  status: string;
  createdAt: string;
  requestorId: number;
  targetUserId: number;
  requestorScheduleId: number;
  targetScheduleId: number;
}

export interface PaginatedUsers {
  users: { id: number; email: string; firstName?: string | null; lastName?: string | null }[];
  totalCount: number;
}

export interface LabelData {
  barcode: string;
  productName: string;
  quantity?: number;
  expiryDate?: string;
  qrCodeContent?: string;
  batchNumber?: string;
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

export interface UserWithPayroll {
  id: number;
  email: string;
  firstName?: string | null;
  lastName?: string | null;
  payrolls?: PayrollConfig[] | null;
}

export interface PositionWithPayroll {
  id: number;
  title: string;
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