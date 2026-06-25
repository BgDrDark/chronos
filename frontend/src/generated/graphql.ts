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
  JSON: { input: unknown; output: unknown; }
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
  userId: Scalars['Int']['output'];
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
  terminalMode: Scalars['String']['output'];
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

export type AddItemsToBatchInput = {
  batchId: Scalars['Int']['input'];
  userIds: Array<Scalars['Int']['input']>;
};

export type AdvancePayment = {
  amount: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isProcessed: Scalars['Boolean']['output'];
  paymentDate: Scalars['Date']['output'];
  user: User;
  userId: Scalars['Int']['output'];
};

export type AnnexTemplate = {
  changeType?: Maybe<Scalars['String']['output']>;
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  currentVersion?: Maybe<AnnexTemplateVersion>;
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  newBaseSalary?: Maybe<Scalars['Decimal']['output']>;
  newHolidayRate?: Maybe<Scalars['Decimal']['output']>;
  newNightWorkRate?: Maybe<Scalars['Decimal']['output']>;
  newOvertimeRate?: Maybe<Scalars['Decimal']['output']>;
  newWorkHoursPerWeek?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
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
  changeType?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isCurrent: Scalars['Boolean']['output'];
  newBaseSalary?: Maybe<Scalars['Decimal']['output']>;
  newHolidayRate?: Maybe<Scalars['Decimal']['output']>;
  newNightWorkRate?: Maybe<Scalars['Decimal']['output']>;
  newOvertimeRate?: Maybe<Scalars['Decimal']['output']>;
  newWorkHoursPerWeek?: Maybe<Scalars['Int']['output']>;
  sections: Array<AnnexTemplateSection>;
  templateId: Scalars['Int']['output'];
  version: Scalars['Int']['output'];
};

export type AnnualInsuranceEmployee = {
  baseSalary: Scalars['Float']['output'];
  contractType: Scalars['String']['output'];
  dooEmployee: Scalars['Float']['output'];
  dzpoEmployee: Scalars['Float']['output'];
  egn: Scalars['String']['output'];
  insuranceBase: Scalars['Float']['output'];
  name: Scalars['String']['output'];
  sickDays: Scalars['Int']['output'];
  totalContributions: Scalars['Float']['output'];
  workedMonths: Scalars['Int']['output'];
  zoEmployee: Scalars['Float']['output'];
};

export type AnnualInsuranceReport = {
  companyId: Scalars['Int']['output'];
  employees: Array<AnnualInsuranceEmployee>;
  generatedAt: Scalars['String']['output'];
  reportType: Scalars['String']['output'];
  summary: AnnualInsuranceSummary;
  year: Scalars['Int']['output'];
};

export type AnnualInsuranceSummary = {
  totalContributions: Scalars['Float']['output'];
  totalDoo: Scalars['Float']['output'];
  totalDzpo: Scalars['Float']['output'];
  totalEmployees: Scalars['Int']['output'];
  totalZo: Scalars['Float']['output'];
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

export type BehavioralAnomalyType = {
  actualValue: Scalars['Float']['output'];
  anomalyType: Scalars['String']['output'];
  confidenceScore: Scalars['Float']['output'];
  contextSummary?: Maybe<Scalars['JSONScalar']['output']>;
  description: Scalars['String']['output'];
  detectedAt: Scalars['DateTime']['output'];
  deviation: Scalars['Float']['output'];
  expectedValue: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  metricName: Scalars['String']['output'];
  profileId: Scalars['Int']['output'];
  severity: Scalars['Int']['output'];
  suppressed: Scalars['Boolean']['output'];
  suppressionReason?: Maybe<Scalars['String']['output']>;
  userId: Scalars['Int']['output'];
};

export type BehavioralPersonalityProfileType = {
  agreeableness: Scalars['Int']['output'];
  agreeablenessRaw: Scalars['Float']['output'];
  companyId: Scalars['Int']['output'];
  completedAt: Scalars['DateTime']['output'];
  conscientiousness: Scalars['Int']['output'];
  conscientiousnessRaw: Scalars['Float']['output'];
  extraversion: Scalars['Int']['output'];
  extraversionRaw: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  interpretation?: Maybe<Scalars['String']['output']>;
  neuroticism: Scalars['Int']['output'];
  neuroticismRaw: Scalars['Float']['output'];
  openness: Scalars['Int']['output'];
  opennessRaw: Scalars['Float']['output'];
  templateId: Scalars['Int']['output'];
  userId: Scalars['Int']['output'];
};

export type BehavioralProfileType = {
  attendanceScore: Scalars['Float']['output'];
  burnoutRisk: Scalars['Float']['output'];
  companyId: Scalars['Int']['output'];
  computedAt: Scalars['DateTime']['output'];
  confidenceScore: Scalars['Float']['output'];
  contributionFactors?: Maybe<Scalars['JSONScalar']['output']>;
  dataCompleteness: Scalars['Float']['output'];
  efficiencyScore: Scalars['Float']['output'];
  employeeType: Scalars['String']['output'];
  engagementScore?: Maybe<Scalars['Float']['output']>;
  financialStressScore: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  overtimeScore: Scalars['Float']['output'];
  peerGroupPercentile: Scalars['Float']['output'];
  periodEnd: Scalars['Date']['output'];
  periodStart: Scalars['Date']['output'];
  probationMode: Scalars['Boolean']['output'];
  punctualityScore: Scalars['Float']['output'];
  ruleEngineVersion: Scalars['String']['output'];
  scrapRate: Scalars['Float']['output'];
  status: Scalars['String']['output'];
  tenureDays: Scalars['Int']['output'];
  trendDirection: Scalars['String']['output'];
  userId: Scalars['Int']['output'];
  version: Scalars['Int']['output'];
};

export type BehavioralPulseSurveyType = {
  burnoutFeeling?: Maybe<Scalars['Int']['output']>;
  companyId: Scalars['Int']['output'];
  energyLevel?: Maybe<Scalars['Int']['output']>;
  engagementFeeling?: Maybe<Scalars['Int']['output']>;
  id: Scalars['Int']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  stressLevel?: Maybe<Scalars['Int']['output']>;
  submittedAt: Scalars['DateTime']['output'];
  surveyVersion: Scalars['String']['output'];
  userId: Scalars['Int']['output'];
  workSatisfaction?: Maybe<Scalars['Int']['output']>;
};

export type BehavioralRecommendationType = {
  aggregatedCount: Scalars['Int']['output'];
  anomalyId?: Maybe<Scalars['Int']['output']>;
  autoExecuted: Scalars['Boolean']['output'];
  coachingTips?: Maybe<Scalars['JSONScalar']['output']>;
  confidenceScore: Scalars['Float']['output'];
  createdAt: Scalars['DateTime']['output'];
  description: Scalars['String']['output'];
  disputeNotes?: Maybe<Scalars['String']['output']>;
  disputeReason?: Maybe<Scalars['String']['output']>;
  expiresAt?: Maybe<Scalars['DateTime']['output']>;
  explanation: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  priority: Scalars['String']['output'];
  ruleId: Scalars['Int']['output'];
  status: Scalars['String']['output'];
  suggestedAction: Scalars['String']['output'];
  throttled: Scalars['Boolean']['output'];
  title: Scalars['String']['output'];
  type: Scalars['String']['output'];
  userId: Scalars['Int']['output'];
};

export type BehavioralRuleInput = {
  autoExecute?: Scalars['Boolean']['input'];
  autoExecuteAction?: InputMaybe<Scalars['String']['input']>;
  conditionConfig: Scalars['JSON']['input'];
  conditionType: Scalars['String']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  isActive?: Scalars['Boolean']['input'];
  name: Scalars['String']['input'];
  recommendationTemplate: Scalars['JSON']['input'];
  ruleType?: Scalars['String']['input'];
  shadowMode?: Scalars['Boolean']['input'];
};

export type BehavioralRuleType = {
  acceptedCount: Scalars['Int']['output'];
  autoExecute: Scalars['Boolean']['output'];
  autoExecuteAction?: Maybe<Scalars['String']['output']>;
  companyId: Scalars['Int']['output'];
  conditionConfig: Scalars['JSONScalar']['output'];
  conditionType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy: Scalars['Int']['output'];
  description?: Maybe<Scalars['String']['output']>;
  effectiveCount: Scalars['Int']['output'];
  effectivenessScore: Scalars['Float']['output'];
  falsePositiveCount: Scalars['Int']['output'];
  falsePositiveRate: Scalars['Float']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  isSystem: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  recommendationTemplate: Scalars['JSONScalar']['output'];
  ruleType: Scalars['String']['output'];
  shadowMode: Scalars['Boolean']['output'];
  triggerCount: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type BehavioralSettingsInput = {
  aggregatedProfileMonths?: Scalars['Int']['input'];
  anonymizeInsteadOfDelete?: Scalars['Boolean']['input'];
  auditLogMonths?: Scalars['Int']['input'];
  autoCleanupEnabled?: Scalars['Boolean']['input'];
  cleanupSchedule?: Scalars['String']['input'];
  feedbackMonths?: Scalars['Int']['input'];
  rawProfileDays?: Scalars['Int']['input'];
  recommendationMonths?: Scalars['Int']['input'];
};

export type BehavioralSettingsType = {
  aggregatedProfileMonths: Scalars['Int']['output'];
  anonymizeInsteadOfDelete: Scalars['Boolean']['output'];
  auditLogMonths: Scalars['Int']['output'];
  autoCleanupEnabled: Scalars['Boolean']['output'];
  cleanupSchedule: Scalars['String']['output'];
  companyId: Scalars['Int']['output'];
  feedbackMonths: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  rawProfileDays: Scalars['Int']['output'];
  recommendationMonths: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
  updatedBy: Scalars['Int']['output'];
};

export type BehavioralSystemHealthType = {
  circuitBreakerFailureCount: Scalars['Int']['output'];
  circuitBreakerOpen: Scalars['Boolean']['output'];
  companyId: Scalars['Int']['output'];
  employeesFailed: Scalars['Int']['output'];
  employeesProcessed: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  lastBiasCheck?: Maybe<Scalars['DateTime']['output']>;
  lastComputationAt?: Maybe<Scalars['DateTime']['output']>;
  lastComputationDurationSeconds?: Maybe<Scalars['Int']['output']>;
  lastComputationStatus: Scalars['String']['output'];
  lastSuccessfulProfileDate?: Maybe<Scalars['DateTime']['output']>;
  triggeredAlertsToday: Scalars['Int']['output'];
};

export type BiasReportType = {
  companyId: Scalars['Int']['output'];
  findings: Scalars['JSONScalar']['output'];
  generatedAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  overallBiasDetected: Scalars['Boolean']['output'];
  periodEnd: Scalars['Date']['output'];
  periodStart: Scalars['Date']['output'];
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
  amount: Scalars['Float']['input'];
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
  status: Scalars['String']['output'];
  totalAmount: Scalars['Decimal']['output'];
  transport: Scalars['Decimal']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  user: User;
  userId: Scalars['Int']['output'];
};

export type CashJournalEntryInput = {
  amount: Scalars['Decimal']['input'];
  companyId: Scalars['Int']['input'];
  date: Scalars['Date']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
  operationType: Scalars['String']['input'];
  paymentMethod?: InputMaybe<Scalars['String']['input']>;
  referenceId?: InputMaybe<Scalars['Int']['input']>;
  referenceType?: InputMaybe<Scalars['String']['input']>;
};

export type CashJournalEntryType = {
  amount: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  creator?: Maybe<User>;
  date: Scalars['Date']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  operationType: Scalars['String']['output'];
  paymentMethod?: Maybe<Scalars['String']['output']>;
  referenceId?: Maybe<Scalars['Int']['output']>;
  referenceType?: Maybe<Scalars['String']['output']>;
};

export type CashJournalUnifiedItem = {
  amount: Scalars['Decimal']['output'];
  creator?: Maybe<User>;
  date: Scalars['Date']['output'];
  description: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  invoiceNumber?: Maybe<Scalars['String']['output']>;
  invoiceType?: Maybe<Scalars['String']['output']>;
  operationType: Scalars['String']['output'];
  paymentMethod?: Maybe<Scalars['String']['output']>;
  referenceId?: Maybe<Scalars['Int']['output']>;
  source: Scalars['String']['output'];
};

export type CashJournalUnifiedResult = {
  balance: Scalars['Decimal']['output'];
  items: Array<CashJournalUnifiedItem>;
  totalCount: Scalars['Int']['output'];
  totalExpense: Scalars['Decimal']['output'];
  totalIncome: Scalars['Decimal']['output'];
};

export type CashReceipt = {
  amount: Scalars['Decimal']['output'];
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['Int']['output']>;
  date: Scalars['Date']['output'];
  fiscalPrinterId?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  itemsJson?: Maybe<Scalars['JSONScalar']['output']>;
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
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
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
  probationMonths?: Maybe<Scalars['Int']['output']>;
  rejectionReason?: Maybe<Scalars['String']['output']>;
  signatureRequestedAt?: Maybe<Scalars['DateTime']['output']>;
  signedAt?: Maybe<Scalars['DateTime']['output']>;
  signedByEmployee: Scalars['Boolean']['output'];
  signedByEmployeeAt?: Maybe<Scalars['DateTime']['output']>;
  signedByEmployer: Scalars['Boolean']['output'];
  signedByEmployerAt?: Maybe<Scalars['DateTime']['output']>;
  status: Scalars['String']['output'];
  templateId?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  workClass?: Maybe<Scalars['String']['output']>;
  workHoursPerWeek?: Maybe<Scalars['Int']['output']>;
};

export type ContractTemplate = {
  baseSalary?: Maybe<Scalars['Decimal']['output']>;
  clauses: Array<ContractTemplateClauseGql>;
  companyId: Scalars['Int']['output'];
  contractType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  currentVersion?: Maybe<ContractTemplateVersion>;
  department?: Maybe<Department>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  holidayRate: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  nightWorkRate: Scalars['Decimal']['output'];
  overtimeRate: Scalars['Decimal']['output'];
  paymentDay: Scalars['Int']['output'];
  position?: Maybe<Position>;
  positionId?: Maybe<Scalars['Int']['output']>;
  probationMonths: Scalars['Int']['output'];
  salaryCalculationType: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  workClass?: Maybe<Scalars['String']['output']>;
  workHoursPerWeek: Scalars['Int']['output'];
};

export type ContractTemplateClauseGql = {
  clause?: Maybe<ClauseTemplate>;
  clauseId: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  orderIndex: Scalars['Int']['output'];
  templateId: Scalars['Int']['output'];
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
  baseSalary?: Maybe<Scalars['Decimal']['output']>;
  changeNote?: Maybe<Scalars['String']['output']>;
  contractType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy?: Maybe<Scalars['String']['output']>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  holidayRate: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  isCurrent: Scalars['Boolean']['output'];
  nightWorkRate: Scalars['Decimal']['output'];
  overtimeRate: Scalars['Decimal']['output'];
  paymentDay: Scalars['Int']['output'];
  positionId?: Maybe<Scalars['Int']['output']>;
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

export type CreatePaymentBatchInput = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  paymentDate: Scalars['DateTime']['input'];
  paymentMethod?: Scalars['String']['input'];
  paymentReference?: InputMaybe<Scalars['String']['input']>;
  periodEnd: Scalars['Date']['input'];
  periodStart: Scalars['Date']['input'];
};

export type CreatePersonalityTemplateInput = {
  isActive?: Scalars['Boolean']['input'];
  name: Scalars['String']['input'];
  selectedQuestionIds: Array<Scalars['Int']['input']>;
  shuffle?: Scalars['Boolean']['input'];
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
  cashBalance: Scalars['Decimal']['output'];
  cashExpense: Scalars['Decimal']['output'];
  cashIncome: Scalars['Decimal']['output'];
  date: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  incomingInvoicesCount: Scalars['Int']['output'];
  incomingInvoicesTotal: Scalars['Decimal']['output'];
  invoicesCount: Scalars['Int']['output'];
  invoicesTotal: Scalars['Decimal']['output'];
  outgoingInvoicesCount: Scalars['Int']['output'];
  outgoingInvoicesTotal: Scalars['Decimal']['output'];
  overdueInvoicesCount: Scalars['Int']['output'];
  paidInvoicesCount: Scalars['Int']['output'];
  unpaidInvoicesCount: Scalars['Int']['output'];
  vatCollected: Scalars['Decimal']['output'];
  vatPaid: Scalars['Decimal']['output'];
};

export type Department = {
  company?: Maybe<Company>;
  companyId: Scalars['Int']['output'];
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

export type DeployStatus = {
  isDeploying: Scalars['Boolean']['output'];
  output?: Maybe<Scalars['String']['output']>;
  progress: Scalars['String']['output'];
  status: Scalars['String']['output'];
  version?: Maybe<Scalars['String']['output']>;
};

export type DocumentationArticle = {
  categoryId: Scalars['Int']['output'];
  content: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  order: Scalars['Int']['output'];
  title: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['String']['output']>;
};

export type DocumentationArticleInput = {
  categoryId: Scalars['Int']['input'];
  content?: Scalars['String']['input'];
  isActive?: Scalars['Boolean']['input'];
  order?: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};

export type DocumentationCategory = {
  articles?: Maybe<Array<DocumentationArticle>>;
  icon: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  order: Scalars['Int']['output'];
  title: Scalars['String']['output'];
};

export type DocumentationCategoryInput = {
  icon?: Scalars['String']['input'];
  isActive?: Scalars['Boolean']['input'];
  order?: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};

export type EmploymentContract = {
  annexes: Array<ContractAnnex>;
  baseSalary?: Maybe<Scalars['Decimal']['output']>;
  clauseIds?: Maybe<Scalars['String']['output']>;
  company?: Maybe<Company>;
  companyId: Scalars['Int']['output'];
  contractNumber?: Maybe<Scalars['String']['output']>;
  contractType: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  dangerousWork: Scalars['Boolean']['output'];
  department?: Maybe<Department>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  employeeEgn?: Maybe<Scalars['String']['output']>;
  employeeName?: Maybe<Scalars['String']['output']>;
  endDate?: Maybe<Scalars['Date']['output']>;
  experienceStartDate?: Maybe<Scalars['Date']['output']>;
  hasIncomeTax: Scalars['Boolean']['output'];
  holidayRate: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  insuranceContributor: Scalars['Boolean']['output'];
  isActive: Scalars['Boolean']['output'];
  monthlyAdvanceAmount: Scalars['Decimal']['output'];
  nightWorkRate: Scalars['Decimal']['output'];
  noticePeriodDays?: Maybe<Scalars['Int']['output']>;
  overtimeRate: Scalars['Decimal']['output'];
  paymentDay: Scalars['Int']['output'];
  position?: Maybe<Position>;
  positionId?: Maybe<Scalars['Int']['output']>;
  positionTitle?: Maybe<Scalars['String']['output']>;
  probationBeneficiary?: Maybe<Scalars['String']['output']>;
  probationMonths: Scalars['Int']['output'];
  salaryCalculationType: Scalars['String']['output'];
  salaryInstallmentsCount: Scalars['Int']['output'];
  signedAt?: Maybe<Scalars['DateTime']['output']>;
  startDate: Scalars['Date']['output'];
  status: Scalars['String']['output'];
  taxResident: Scalars['Boolean']['output'];
  templateId?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
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
  noticePeriodDays?: InputMaybe<Scalars['Int']['input']>;
  overtimeRate?: InputMaybe<Scalars['Float']['input']>;
  paymentDay?: InputMaybe<Scalars['Int']['input']>;
  positionId?: InputMaybe<Scalars['Int']['input']>;
  probationBeneficiary?: InputMaybe<Scalars['String']['input']>;
  probationMonths?: InputMaybe<Scalars['Int']['input']>;
  salaryCalculationType?: InputMaybe<Scalars['String']['input']>;
  startDate: Scalars['Date']['input'];
  templateId?: InputMaybe<Scalars['Int']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
  workClass?: InputMaybe<Scalars['String']['input']>;
  workHoursPerWeek?: Scalars['Int']['input'];
};

export type EmploymentContractUpdateInput = {
  baseSalary?: InputMaybe<Scalars['Float']['input']>;
  companyId?: InputMaybe<Scalars['Int']['input']>;
  contractNumber?: InputMaybe<Scalars['String']['input']>;
  contractType?: InputMaybe<Scalars['String']['input']>;
  departmentId?: InputMaybe<Scalars['Int']['input']>;
  employeeEgn?: InputMaybe<Scalars['String']['input']>;
  employeeName?: InputMaybe<Scalars['String']['input']>;
  endDate?: InputMaybe<Scalars['Date']['input']>;
  holidayRate?: InputMaybe<Scalars['Float']['input']>;
  jobDescription?: InputMaybe<Scalars['String']['input']>;
  nightWorkRate?: InputMaybe<Scalars['Float']['input']>;
  noticePeriodDays?: InputMaybe<Scalars['Int']['input']>;
  overtimeRate?: InputMaybe<Scalars['Float']['input']>;
  paymentDay?: InputMaybe<Scalars['Int']['input']>;
  positionId?: InputMaybe<Scalars['Int']['input']>;
  probationBeneficiary?: InputMaybe<Scalars['String']['input']>;
  probationMonths?: InputMaybe<Scalars['Int']['input']>;
  salaryCalculationType?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['Date']['input']>;
  templateId?: InputMaybe<Scalars['Int']['input']>;
  workClass?: InputMaybe<Scalars['String']['input']>;
  workHoursPerWeek?: InputMaybe<Scalars['Int']['input']>;
};

export type FefoSuggestion = {
  availableQuantity: Scalars['Decimal']['output'];
  batchId: Scalars['Int']['output'];
  batchNumber: Scalars['String']['output'];
  daysUntilExpiry: Scalars['Int']['output'];
  expiryDate: Scalars['Date']['output'];
  quantityToTake: Scalars['Decimal']['output'];
};

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
  accountId: Scalars['Int']['output'];
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

export type IncomeEntry = {
  date: Scalars['String']['output'];
  gross: Scalars['Float']['output'];
  net: Scalars['Float']['output'];
  tax: Scalars['Float']['output'];
  type: Scalars['String']['output'];
};

export type IncomeReportByType = {
  companyId: Scalars['Int']['output'];
  employees: Array<IncomeReportEmployee>;
  generatedAt: Scalars['String']['output'];
  reportType: Scalars['String']['output'];
  summary: IncomeReportSummary;
  year: Scalars['Int']['output'];
};

export type IncomeReportEmployee = {
  egn: Scalars['String']['output'];
  incomes: Array<IncomeEntry>;
  name: Scalars['String']['output'];
};

export type IncomeReportSummary = {
  totalEmployees: Scalars['Int']['output'];
  totalGross: Scalars['Float']['output'];
  totalTax: Scalars['Float']['output'];
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
  originalInvoice?: Maybe<Invoice>;
  originalInvoiceId: Scalars['Int']['output'];
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
  unit?: Maybe<Scalars['String']['output']>;
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
  userId: Scalars['Int']['output'];
  year: Scalars['Int']['output'];
};

export type LeaveRequest = {
  adminComment?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  employerTopUp: Scalars['Boolean']['output'];
  endDate: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  leaveType: Scalars['String']['output'];
  reason?: Maybe<Scalars['String']['output']>;
  startDate: Scalars['Date']['output'];
  status: Scalars['String']['output'];
  user?: Maybe<User>;
  userId: Scalars['Int']['output'];
};

export type LeaveRequestInput = {
  endDate: Scalars['Date']['input'];
  leaveType: Scalars['String']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
  startDate: Scalars['Date']['input'];
};

export type MaintenanceInput = {
  delayMinutes?: Scalars['Int']['input'];
  enabled: Scalars['Boolean']['input'];
  reason?: Scalars['String']['input'];
};

export type MaintenanceStatus = {
  enabled: Scalars['Boolean']['output'];
  minutesUntil?: Maybe<Scalars['Int']['output']>;
  reason: Scalars['String']['output'];
  scheduledAt?: Maybe<Scalars['DateTime']['output']>;
  updatedBy?: Maybe<User>;
};

export type ManagementStats = {
  latenessByUser: Array<LatenessStat>;
  overtimeByMonth: Array<OvertimeStat>;
};

export type ManagerEffectivenessType = {
  companyId: Scalars['Int']['output'];
  computedAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  managerEffectivenessScore: Scalars['Float']['output'];
  managerId: Scalars['Int']['output'];
  periodEnd: Scalars['Date']['output'];
  periodStart: Scalars['Date']['output'];
  sentimentScore: Scalars['Float']['output'];
  teamAnomalyCount: Scalars['Int']['output'];
  teamAvgAttendance: Scalars['Float']['output'];
  teamAvgBurnout: Scalars['Float']['output'];
  teamAvgEngagement: Scalars['Float']['output'];
  teamBurnoutVariance: Scalars['Float']['output'];
  teamSize: Scalars['Int']['output'];
  teamTurnoverRate: Scalars['Float']['output'];
  trendDirection: Scalars['String']['output'];
};

export type Module = {
  code: Scalars['String']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isEnabled: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
};

export type MonthlyDeclarationEntry = {
  egn: Scalars['String']['output'];
  gross: Scalars['Float']['output'];
  incomeType: Scalars['String']['output'];
  insurance: Scalars['Float']['output'];
  name: Scalars['String']['output'];
  period: Scalars['String']['output'];
  tax: Scalars['Float']['output'];
};

export type MonthlyDeclarationReport = {
  companyId: Scalars['Int']['output'];
  declarations: Array<MonthlyDeclarationEntry>;
  generatedAt: Scalars['String']['output'];
  month: Scalars['Int']['output'];
  reportType: Scalars['String']['output'];
  summary: MonthlyDeclarationSummary;
  year: Scalars['Int']['output'];
};

export type MonthlyDeclarationSummary = {
  totalGross: Scalars['Float']['output'];
  totalInsurance: Scalars['Float']['output'];
  totalTax: Scalars['Float']['output'];
};

export type MonthlySummaryType = {
  cashBalance: Scalars['Decimal']['output'];
  cashExpense: Scalars['Decimal']['output'];
  cashIncome: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  incomingInvoicesCount: Scalars['Int']['output'];
  incomingInvoicesTotal: Scalars['Decimal']['output'];
  invoicesCount: Scalars['Int']['output'];
  invoicesTotal: Scalars['Decimal']['output'];
  month: Scalars['Int']['output'];
  outgoingInvoicesCount: Scalars['Int']['output'];
  outgoingInvoicesTotal: Scalars['Decimal']['output'];
  overdueInvoicesCount: Scalars['Int']['output'];
  paidInvoicesCount: Scalars['Int']['output'];
  unpaidInvoicesCount: Scalars['Int']['output'];
  vatCollected: Scalars['Decimal']['output'];
  vatPaid: Scalars['Decimal']['output'];
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
  addItemsToBatch: SalaryPaymentBatchType;
  addSectionToAnnexTemplate: AnnexTemplateSection;
  addSectionToContractTemplate: ContractTemplateSection;
  adminClockIn: TimeLog;
  adminClockOut: TimeLog;
  applyScheduleTemplate: Scalars['Boolean']['output'];
  approveBusinessTrip: BusinessTrip;
  approveLeave: LeaveRequest;
  approveSwap: ShiftSwapRequest;
  assignPersonalityTest: Array<PersonalityTestAssignmentType>;
  assignRoleToUser: Scalars['Boolean']['output'];
  assignZoneToUser: Scalars['Boolean']['output'];
  attachLeaveDocument: LeaveRequest;
  autoMatchBankTransactions: AutoMatchResult;
  bulkAddBatches: Array<Batch>;
  bulkDeleteSchedules: Scalars['Int']['output'];
  bulkEmergencyAction: Scalars['Boolean']['output'];
  bulkMarkPayslipsAsPaid: Array<Payslip>;
  bulkSetSchedule: Scalars['Boolean']['output'];
  bulkUpdateUserAccess: Scalars['Boolean']['output'];
  calculateRecipeCost: RecipeCostResult;
  cancelLeaveRequest: LeaveRequest;
  cancelMaintenance: Scalars['Boolean']['output'];
  cancelPaymentBatch: SalaryPaymentBatchType;
  changePassword: Scalars['Boolean']['output'];
  clockIn: TimeLog;
  clockOut: TimeLog;
  completeInventorySession: InventorySession;
  completePaymentBatch: SalaryPaymentBatchType;
  computeBiasReport: BiasReportType;
  computeManagerEffectiveness: ManagerEffectivenessType;
  computeOrganizationalHealth: Array<OrganizationalHealthType>;
  confirmProductionOrder: ProductionOrder;
  consumeFromBatch: Batch;
  convertProformaToInvoice: Invoice;
  copySchedulesFromMonth: Scalars['Int']['output'];
  createAccessCode: AccessCode;
  createAccessDoor: AccessDoor;
  createAccessZone: AccessZone;
  createAccount: Account;
  createAccountingEntry: AccountingEntry;
  createAdvancePayment: AdvancePayment;
  createAnnexTemplate: AnnexTemplate;
  createBankAccount: BankAccount;
  createBankTransaction: BankTransaction;
  createBehavioralRule: BehavioralRuleType;
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
  createDocumentationArticle: DocumentationArticle;
  createDocumentationCategory: DocumentationCategory;
  createEmploymentContract: EmploymentContract;
  createIngredient: Ingredient;
  createInvoice: Invoice;
  createInvoiceCorrection: InvoiceCorrection;
  createInvoiceFromBatch: Invoice;
  createManualTimeLog: TimeLog;
  createNightWorkBonus: NightWorkBonus;
  createOvertimeWork: OvertimeWork;
  createPaymentBatch: SalaryPaymentBatchType;
  createPersonalityTemplate: PersonalityTestTemplateType;
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
  createVehicleAccident: VehicleAccident;
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
  deleteBehavioralRule: Scalars['Boolean']['output'];
  deleteCashJournalEntry: Scalars['Boolean']['output'];
  deleteCashReceipt: Scalars['Boolean']['output'];
  deleteClauseTemplate: Scalars['Boolean']['output'];
  deleteContractTemplate: Scalars['Boolean']['output'];
  deleteCostCenter: Scalars['Boolean']['output'];
  deleteDocumentationArticle: Scalars['Boolean']['output'];
  deleteDocumentationCategory: Scalars['Boolean']['output'];
  deleteInvoice: Scalars['Boolean']['output'];
  deleteLeaveRequest: Scalars['Boolean']['output'];
  deleteNotification: Scalars['Boolean']['output'];
  deletePersonalityTemplate: Scalars['Boolean']['output'];
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
  generateAllPayslips: Array<Payslip>;
  generateAnnualInsuranceReport: AnnualInsuranceReport;
  generateContractNumber: Scalars['String']['output'];
  generateDailySummary: DailySummaryType;
  generateIncomeReportByType: IncomeReportByType;
  generateLabel: LabelData;
  generateMonthlyDeclaration: MonthlyDeclarationReport;
  generateMonthlySummary: MonthlySummaryType;
  generateMyPayslip: Payslip;
  generatePayslip: Payslip;
  generateSaftFile: SaftFileResult;
  generateSepaXml: Scalars['String']['output'];
  generateServiceBookExport: ServiceBookExport;
  generateVatRegister: VatRegister;
  generateYearlySummary: YearlySummaryType;
  getAnnexPdfUrl: Scalars['String']['output'];
  getContractPdfUrl: Scalars['String']['output'];
  getInvoicePdfUrl: Scalars['String']['output'];
  getScrapLogs: Array<ProductionScrapLog>;
  invalidateUserSession: Scalars['Boolean']['output'];
  linkEmploymentContractToUser: EmploymentContract;
  markAllNotificationsRead: Scalars['Boolean']['output'];
  markNotificationRead: Scalars['Boolean']['output'];
  markPayslipAsPaid: Payslip;
  markTaskScrap: ProductionTask;
  matchBankTransaction?: Maybe<BankTransaction>;
  openDoor: Scalars['Boolean']['output'];
  reassignPersonalityTest: PersonalityTestAssignmentType;
  reassignTaskWorkstation: ProductionTask;
  recalculateAllRecipeCosts: Array<RecalculateResult>;
  recalculateProductionDeadline: ProductionOrder;
  recordRecommendationFeedback: RecommendationFeedbackType;
  regenerateMyQrCode: Scalars['String']['output'];
  rejectContractAnnex: ContractAnnex;
  rejectLeave: LeaveRequest;
  removeBonus: Scalars['Boolean']['output'];
  removeZoneFromUser: Scalars['Boolean']['output'];
  requestLeave: LeaveRequest;
  respondToSwap: ShiftSwapRequest;
  restoreContractTemplateVersion: ContractTemplate;
  revokeAccessCode: Scalars['Boolean']['output'];
  runUpdateNow: Scalars['String']['output'];
  saveNotificationSetting: NotificationSetting;
  scheduleMaintenance: Scalars['Boolean']['output'];
  scrapTask: ProductionTask;
  setGlobalSetting: GlobalSetting;
  setMonthlyWorkDays: MonthlyWorkDays;
  setUpdateSchedule: UpdateScheduleType;
  setWorkSchedule?: Maybe<WorkSchedule>;
  signContractAnnex: ContractAnnex;
  signEmploymentContract: EmploymentContract;
  startInventorySession: InventorySession;
  submitPersonalityTest: BehavioralPersonalityProfileType;
  submitPulseSurvey: BehavioralPulseSurveyType;
  subscribeToPush: Scalars['Boolean']['output'];
  syncGatewayConfig: Scalars['String']['output'];
  syncHolidays: Scalars['Int']['output'];
  syncOrthodoxHolidays: Scalars['Int']['output'];
  testNotification: Scalars['Boolean']['output'];
  unmatchBankTransaction?: Maybe<BankTransaction>;
  updateAccessZone: AccessZone;
  updateAccount?: Maybe<Account>;
  updateBankAccount: BankAccount;
  updateBankTransaction?: Maybe<BankTransaction>;
  updateBatch: Batch;
  updateBatchStatus: Batch;
  updateBehavioralRule: BehavioralRuleType;
  updateBehavioralSettings: BehavioralSettingsType;
  updateCashReceipt?: Maybe<CashReceipt>;
  updateClauseTemplate: ClauseTemplate;
  updateCompany: Company;
  updateCompanyAccountingSettings: Company;
  updateContractTemplate: ContractTemplate;
  updateCostCenter: VehicleCostCenter;
  updateDepartment: Department;
  updateDocumentationArticle: DocumentationArticle;
  updateDocumentationCategory: DocumentationCategory;
  updateDoorTerminal: AccessDoor;
  updateEmploymentContract: EmploymentContract;
  updateGateway: Gateway;
  updateGlobalPayrollConfig: GlobalPayrollConfig;
  updateGoogleCalendarSettings: Scalars['Boolean']['output'];
  updateIngredient: Ingredient;
  updateInvoice: Invoice;
  updateKioskSecuritySettings: Scalars['Boolean']['output'];
  updateLeaveRequest: LeaveRequest;
  updateLeaveRequestStatus: LeaveRequest;
  updateOfficeLocation: OfficeLocation;
  updatePasswordSettings: PasswordSettings;
  updatePayrollLegalSettings: PayrollLegalSettings;
  updatePersonalityTemplate: PersonalityTestTemplateType;
  updatePosition: Position;
  updatePositionPayroll: Payroll;
  updateProductionOrderQuantity: ProductionOrder;
  updateProductionOrderStatus: ProductionOrder;
  updateProductionTaskStatus: ProductionTask;
  updateRecipePrice: Recipe;
  updateRecommendationStatus: BehavioralRecommendationType;
  updateRole: Role;
  updateScheduleTemplate: ScheduleTemplate;
  updateSectionInAnnexTemplate: AnnexTemplateSection;
  updateSectionInContractTemplate: ContractTemplateSection;
  updateSecurityConfig: Scalars['Boolean']['output'];
  updateSessionSettings: Scalars['Boolean']['output'];
  updateShift: Shift;
  updateSmtpSettings: SmtpSettings;
  updateStorageZone: StorageZone;
  updateSupplier: Supplier;
  updateTerminal: Terminal;
  updateTimeLog: TimeLog;
  updateUser: User;
  updateUserPayroll: Payroll;
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
  amount?: InputMaybe<Scalars['Float']['input']>;
  date?: InputMaybe<Scalars['Date']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  input?: InputMaybe<BonusCreateInput>;
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type MutationAddInventoryItemArgs = {
  foundQuantity: Scalars['Float']['input'];
  ingredientId: Scalars['Int']['input'];
  sessionId: Scalars['Int']['input'];
};


export type MutationAddItemsToBatchArgs = {
  input: AddItemsToBatchInput;
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
  adminComment?: InputMaybe<Scalars['String']['input']>;
  employerTopUp?: Scalars['Boolean']['input'];
  requestId: Scalars['Int']['input'];
};


export type MutationApproveSwapArgs = {
  approve: Scalars['Boolean']['input'];
  swapId: Scalars['Int']['input'];
};


export type MutationAssignPersonalityTestArgs = {
  dueBy: Scalars['DateTime']['input'];
  templateId: Scalars['Int']['input'];
  userIds: Array<Scalars['Int']['input']>;
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


export type MutationBulkDeleteSchedulesArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
  userIds: Array<Scalars['Int']['input']>;
};


export type MutationBulkEmergencyActionArgs = {
  action: Scalars['String']['input'];
};


export type MutationBulkMarkPayslipsAsPaidArgs = {
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


export type MutationCancelLeaveRequestArgs = {
  requestId: Scalars['Int']['input'];
};


export type MutationCancelPaymentBatchArgs = {
  batchId: Scalars['Int']['input'];
};


export type MutationChangePasswordArgs = {
  newPassword: Scalars['String']['input'];
  oldPassword: Scalars['String']['input'];
};


export type MutationClockInArgs = {
  idempotencyKey?: InputMaybe<Scalars['String']['input']>;
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
};


export type MutationClockOutArgs = {
  idempotencyKey?: InputMaybe<Scalars['String']['input']>;
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
};


export type MutationCompleteInventorySessionArgs = {
  sessionId: Scalars['Int']['input'];
};


export type MutationCompletePaymentBatchArgs = {
  batchId: Scalars['Int']['input'];
};


export type MutationComputeBiasReportArgs = {
  periodEnd?: InputMaybe<Scalars['String']['input']>;
  periodStart?: InputMaybe<Scalars['String']['input']>;
};


export type MutationComputeManagerEffectivenessArgs = {
  managerId: Scalars['Int']['input'];
  periodEnd?: InputMaybe<Scalars['String']['input']>;
  periodStart?: InputMaybe<Scalars['String']['input']>;
};


export type MutationComputeOrganizationalHealthArgs = {
  periodEnd?: InputMaybe<Scalars['String']['input']>;
  periodStart?: InputMaybe<Scalars['String']['input']>;
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


export type MutationCopySchedulesFromMonthArgs = {
  sourceMonth: Scalars['Int']['input'];
  sourceYear: Scalars['Int']['input'];
  targetMonth: Scalars['Int']['input'];
  targetYear: Scalars['Int']['input'];
  userId: Scalars['Int']['input'];
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


export type MutationCreateBehavioralRuleArgs = {
  input: BehavioralRuleInput;
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


export type MutationCreateDocumentationArticleArgs = {
  input: DocumentationArticleInput;
};


export type MutationCreateDocumentationCategoryArgs = {
  input: DocumentationCategoryInput;
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


export type MutationCreatePaymentBatchArgs = {
  input: CreatePaymentBatchInput;
};


export type MutationCreatePersonalityTemplateArgs = {
  input: CreatePersonalityTemplateInput;
};


export type MutationCreatePositionArgs = {
  departmentId?: InputMaybe<Scalars['Int']['input']>;
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
  description?: InputMaybe<Scalars['String']['input']>;
  installmentsCount: Scalars['Int']['input'];
  startDate: Scalars['Date']['input'];
  totalAmount: Scalars['Float']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationCreateShiftArgs = {
  breakDurationMinutes?: InputMaybe<Scalars['Int']['input']>;
  endTime: Scalars['Time']['input'];
  name: Scalars['String']['input'];
  overnight?: InputMaybe<Scalars['Boolean']['input']>;
  payMultiplier?: InputMaybe<Scalars['Decimal']['input']>;
  shiftType?: InputMaybe<Scalars['String']['input']>;
  startTime: Scalars['Time']['input'];
  toleranceMinutes?: InputMaybe<Scalars['Int']['input']>;
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


export type MutationCreateVehicleAccidentArgs = {
  input: VehicleAccidentInput;
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


export type MutationDeleteBehavioralRuleArgs = {
  ruleId: Scalars['Int']['input'];
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


export type MutationDeleteDocumentationArticleArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteDocumentationCategoryArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteInvoiceArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteLeaveRequestArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeleteNotificationArgs = {
  id: Scalars['Int']['input'];
};


export type MutationDeletePersonalityTemplateArgs = {
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


export type MutationGenerateAllPayslipsArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
};


export type MutationGenerateAnnualInsuranceReportArgs = {
  year: Scalars['Int']['input'];
};


export type MutationGenerateContractNumberArgs = {
  companyId: Scalars['Int']['input'];
};


export type MutationGenerateDailySummaryArgs = {
  date: Scalars['String']['input'];
};


export type MutationGenerateIncomeReportByTypeArgs = {
  year: Scalars['Int']['input'];
};


export type MutationGenerateLabelArgs = {
  orderId: Scalars['Int']['input'];
};


export type MutationGenerateMonthlyDeclarationArgs = {
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
  payslipIds: Array<Scalars['Int']['input']>;
};


export type MutationGenerateServiceBookExportArgs = {
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


export type MutationMarkNotificationReadArgs = {
  id: Scalars['Int']['input'];
};


export type MutationMarkPayslipAsPaidArgs = {
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


export type MutationReassignPersonalityTestArgs = {
  assignmentId: Scalars['Int']['input'];
  dueBy?: InputMaybe<Scalars['DateTime']['input']>;
  templateId?: InputMaybe<Scalars['Int']['input']>;
};


export type MutationReassignTaskWorkstationArgs = {
  newWorkstationId: Scalars['Int']['input'];
  taskId: Scalars['Int']['input'];
};


export type MutationRecalculateProductionDeadlineArgs = {
  orderId: Scalars['Int']['input'];
};


export type MutationRecordRecommendationFeedbackArgs = {
  action: Scalars['String']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  recommendationId: Scalars['Int']['input'];
};


export type MutationRejectContractAnnexArgs = {
  annexId: Scalars['Int']['input'];
  reason: Scalars['String']['input'];
};


export type MutationRejectLeaveArgs = {
  adminComment?: InputMaybe<Scalars['String']['input']>;
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


export type MutationScheduleMaintenanceArgs = {
  input: MaintenanceInput;
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


export type MutationSetUpdateScheduleArgs = {
  input: UpdateScheduleInput;
};


export type MutationSetWorkScheduleArgs = {
  date: Scalars['Date']['input'];
  shiftId: Scalars['Int']['input'];
  userId: Scalars['Int']['input'];
};


export type MutationSignContractAnnexArgs = {
  annexId: Scalars['Int']['input'];
  role: Scalars['String']['input'];
};


export type MutationSignEmploymentContractArgs = {
  id: Scalars['Int']['input'];
};


export type MutationSubmitPersonalityTestArgs = {
  input: PersonalityTestAnswers;
};


export type MutationSubmitPulseSurveyArgs = {
  input: PulseSurveyInput;
};


export type MutationSubscribeToPushArgs = {
  preferencesJson: Scalars['String']['input'];
  subscriptionJson: Scalars['String']['input'];
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
  recipientEmail?: InputMaybe<Scalars['String']['input']>;
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
  input: BankAccountInput;
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


export type MutationUpdateBehavioralRuleArgs = {
  input: BehavioralRuleInput;
  ruleId: Scalars['Int']['input'];
};


export type MutationUpdateBehavioralSettingsArgs = {
  input: BehavioralSettingsInput;
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


export type MutationUpdateDocumentationArticleArgs = {
  id: Scalars['Int']['input'];
  input: DocumentationArticleInput;
};


export type MutationUpdateDocumentationCategoryArgs = {
  id: Scalars['Int']['input'];
  input: DocumentationCategoryInput;
};


export type MutationUpdateDoorTerminalArgs = {
  id: Scalars['Int']['input'];
  terminalId?: InputMaybe<Scalars['String']['input']>;
  terminalMode?: InputMaybe<Scalars['String']['input']>;
};


export type MutationUpdateEmploymentContractArgs = {
  id: Scalars['Int']['input'];
  input: EmploymentContractUpdateInput;
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


export type MutationUpdateLeaveRequestArgs = {
  endDate?: InputMaybe<Scalars['Date']['input']>;
  leaveType?: InputMaybe<Scalars['String']['input']>;
  reason?: InputMaybe<Scalars['String']['input']>;
  requestId: Scalars['Int']['input'];
  startDate?: InputMaybe<Scalars['Date']['input']>;
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


export type MutationUpdatePersonalityTemplateArgs = {
  input: UpdatePersonalityTemplateInput;
};


export type MutationUpdatePositionArgs = {
  departmentId: Scalars['Int']['input'];
  id: Scalars['Int']['input'];
  title: Scalars['String']['input'];
};


export type MutationUpdatePositionPayrollArgs = {
  annualLeaveDays?: InputMaybe<Scalars['Int']['input']>;
  currency?: InputMaybe<Scalars['String']['input']>;
  hasHealthInsurance?: InputMaybe<Scalars['Boolean']['input']>;
  hasTaxDeduction?: InputMaybe<Scalars['Boolean']['input']>;
  healthInsurancePercent?: InputMaybe<Scalars['Decimal']['input']>;
  hourlyRate: Scalars['Decimal']['input'];
  monthlySalary?: InputMaybe<Scalars['Decimal']['input']>;
  overtimeMultiplier: Scalars['Decimal']['input'];
  positionId: Scalars['Int']['input'];
  standardHoursPerDay: Scalars['Int']['input'];
  taxPercent?: InputMaybe<Scalars['Decimal']['input']>;
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


export type MutationUpdateRecommendationStatusArgs = {
  disputeNotes?: InputMaybe<Scalars['String']['input']>;
  disputeReason?: InputMaybe<Scalars['String']['input']>;
  recommendationId: Scalars['Int']['input'];
  status: Scalars['String']['input'];
};


export type MutationUpdateRoleArgs = {
  description?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  name?: InputMaybe<Scalars['String']['input']>;
};


export type MutationUpdateScheduleTemplateArgs = {
  description?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['Int']['input'];
  items?: InputMaybe<Array<ScheduleTemplateItemInput>>;
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


export type MutationUpdateSessionSettingsArgs = {
  maxAgeHours: Scalars['Int']['input'];
};


export type MutationUpdateShiftArgs = {
  breakDurationMinutes?: InputMaybe<Scalars['Int']['input']>;
  endTime: Scalars['Time']['input'];
  id: Scalars['Int']['input'];
  name: Scalars['String']['input'];
  overnight?: InputMaybe<Scalars['Boolean']['input']>;
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


export type MutationUpdateUserPayrollArgs = {
  annualLeaveDays?: InputMaybe<Scalars['Int']['input']>;
  currency?: InputMaybe<Scalars['String']['input']>;
  hasHealthInsurance?: InputMaybe<Scalars['Boolean']['input']>;
  hasTaxDeduction?: InputMaybe<Scalars['Boolean']['input']>;
  healthInsurancePercent?: InputMaybe<Scalars['Decimal']['input']>;
  hourlyRate: Scalars['Decimal']['input'];
  monthlySalary?: InputMaybe<Scalars['Decimal']['input']>;
  overtimeMultiplier: Scalars['Decimal']['input'];
  standardHoursPerDay: Scalars['Int']['input'];
  taxPercent?: InputMaybe<Scalars['Decimal']['input']>;
  userId: Scalars['Int']['input'];
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

export type Notification = {
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  isRead: Scalars['Boolean']['output'];
  message: Scalars['String']['output'];
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
  entryEnabled: Scalars['Boolean']['output'];
  exitEnabled: Scalars['Boolean']['output'];
  latitude: Scalars['Float']['output'];
  longitude: Scalars['Float']['output'];
  radius: Scalars['Int']['output'];
};

export type OperationLogType = {
  changes?: Maybe<Scalars['JSONScalar']['output']>;
  entityId: Scalars['Int']['output'];
  entityType: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  operation: Scalars['String']['output'];
  timestamp: Scalars['DateTime']['output'];
  user?: Maybe<User>;
  userId?: Maybe<Scalars['Int']['output']>;
};

export type OrganizationalHealthType = {
  anomalyCount: Scalars['Int']['output'];
  avgAttendance: Scalars['Float']['output'];
  avgBurnoutRisk: Scalars['Float']['output'];
  avgEfficiency: Scalars['Float']['output'];
  avgPunctuality: Scalars['Float']['output'];
  departmentId: Scalars['Int']['output'];
  departmentName: Scalars['String']['output'];
  employeeCount: Scalars['Int']['output'];
  isSystemicIssue: Scalars['Boolean']['output'];
  trend: Scalars['String']['output'];
  turnoverRate: Scalars['Float']['output'];
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

export type PaymentStatisticsType = {
  averagePaymentPerEmployee: Scalars['Float']['output'];
  byMethod?: Maybe<Scalars['JSONScalar']['output']>;
  byStatus?: Maybe<Scalars['JSONScalar']['output']>;
  totalAmount: Scalars['Float']['output'];
  totalBatches: Scalars['Int']['output'];
  totalEmployeesPaid: Scalars['Int']['output'];
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
  batchId?: Maybe<Scalars['Int']['output']>;
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

export type PersonalityQuestionType = {
  bg: Scalars['String']['output'];
  direction: Scalars['String']['output'];
  en: Scalars['String']['output'];
  factor: Scalars['String']['output'];
  id: Scalars['Int']['output'];
};

export type PersonalityTestAnswers = {
  answers: Array<Scalars['Int']['input']>;
  templateId: Scalars['Int']['input'];
};

export type PersonalityTestAssignmentType = {
  assignedAt: Scalars['DateTime']['output'];
  assignedBy: Scalars['Int']['output'];
  assignerName: Scalars['String']['output'];
  companyId: Scalars['Int']['output'];
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  dueBy: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  notifiedOverdue: Scalars['Boolean']['output'];
  status: Scalars['String']['output'];
  templateId: Scalars['Int']['output'];
  templateName: Scalars['String']['output'];
  userEmail: Scalars['String']['output'];
  userId: Scalars['Int']['output'];
  userName: Scalars['String']['output'];
};

export type PersonalityTestTemplateType = {
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  createdBy: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  selectedQuestionIds: Array<Scalars['Int']['output']>;
  shuffle: Scalars['Boolean']['output'];
};

export type Position = {
  department?: Maybe<Department>;
  departmentId: Scalars['Int']['output'];
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
  newCost: Scalars['Decimal']['output'];
  newMarkup: Scalars['Decimal']['output'];
  newPremium: Scalars['Decimal']['output'];
  newPrice: Scalars['Decimal']['output'];
  oldCost: Scalars['Decimal']['output'];
  oldMarkup: Scalars['Decimal']['output'];
  oldPremium: Scalars['Decimal']['output'];
  oldPrice: Scalars['Decimal']['output'];
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
  quantityUsed: Scalars['Decimal']['output'];
  unit?: Maybe<Scalars['String']['output']>;
};

export type ProductionRecordWorker = {
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  startedAt?: Maybe<Scalars['DateTime']['output']>;
  userId: Scalars['Int']['output'];
  workstationId?: Maybe<Scalars['Int']['output']>;
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

export type PulseSurveyInput = {
  burnoutFeeling?: InputMaybe<Scalars['Int']['input']>;
  energyLevel?: InputMaybe<Scalars['Int']['input']>;
  engagementFeeling?: InputMaybe<Scalars['Int']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  stressLevel?: InputMaybe<Scalars['Int']['input']>;
  workSatisfaction?: InputMaybe<Scalars['Int']['input']>;
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
  approvedLeaveRequestsInRange: Array<LeaveRequest>;
  auditLogs: Array<AuditLog>;
  bankAccounts: Array<BankAccount>;
  bankTransactions: Array<BankTransaction>;
  batches: Array<Batch>;
  behavioralAnomalies: Array<BehavioralAnomalyType>;
  behavioralProfiles: Array<BehavioralProfileType>;
  behavioralRecommendations: Array<BehavioralRecommendationType>;
  behavioralRules: Array<BehavioralRuleType>;
  behavioralSettings?: Maybe<BehavioralSettingsType>;
  behavioralSystemHealth?: Maybe<BehavioralSystemHealthType>;
  biasReports: Array<BiasReportType>;
  cashJournalEntries: Array<CashJournalEntryType>;
  cashJournalUnified: CashJournalUnifiedResult;
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
  deployStatus: DeployStatus;
  documentationArticles: Array<DocumentationArticle>;
  documentationCategories: Array<DocumentationCategory>;
  employmentContract?: Maybe<EmploymentContract>;
  employmentContracts: Array<EmploymentContract>;
  gateway?: Maybe<Gateway>;
  gatewayStats: GatewayStats;
  gateways: Array<Gateway>;
  getFefoSuggestion: Array<FefoSuggestion>;
  globalPayrollConfig: GlobalPayrollConfig;
  globalSetting?: Maybe<GlobalSetting>;
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
  maintenanceStatus: MaintenanceStatus;
  managementStats: ManagementStats;
  managerEffectiveness: Array<ManagerEffectivenessType>;
  me: User;
  modules: Array<Module>;
  monthlySummaries: Array<MonthlySummaryType>;
  monthlyWorkDays?: Maybe<MonthlyWorkDays>;
  myDailyStats: Array<DailyStat>;
  myLeaveRequests: Array<LeaveRequest>;
  myNotifications: Array<Notification>;
  myNotificationsCount: Scalars['Int']['output'];
  myPaymentHistory: Array<SalaryPaymentItemType>;
  mySchedules: Array<WorkSchedule>;
  mySwapRequests: Array<ShiftSwapRequest>;
  notificationSetting?: Maybe<NotificationSetting>;
  notificationSettings: Array<NotificationSetting>;
  officeLocation?: Maybe<OfficeLocation>;
  operationLogs: Array<OperationLogType>;
  organizationalHealth: Array<OrganizationalHealthType>;
  orthodoxHolidays: Array<OrthodoxHoliday>;
  overdueProductionOrders: Array<ProductionOrder>;
  passwordSettings: PasswordSettings;
  paymentBatch?: Maybe<SalaryPaymentBatchType>;
  paymentBatches: Array<SalaryPaymentBatchType>;
  paymentStatistics?: Maybe<PaymentStatisticsType>;
  payrollForecast: PayrollForecast;
  payrollLegalSettings: PayrollLegalSettings;
  payrollSummary: Array<PayrollSummaryItem>;
  pendingAdminSwaps: Array<ShiftSwapRequest>;
  pendingLeaveRequests: Array<LeaveRequest>;
  personalityProfiles: Array<BehavioralPersonalityProfileType>;
  personalityQuestions: Array<PersonalityQuestionType>;
  personalityTemplates: Array<PersonalityTestTemplateType>;
  personalityTestAssignments: Array<PersonalityTestAssignmentType>;
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
  scheduleStats: Array<ScheduleStat>;
  scheduleTemplate?: Maybe<ScheduleTemplate>;
  scheduleTemplates: Array<ScheduleTemplate>;
  sessionSettings: SessionSettings;
  shifts: Array<Shift>;
  smtpSettings?: Maybe<SmtpSettings>;
  stockConsumptionLogs: Array<StockConsumptionLog>;
  storageZones: Array<StorageZone>;
  suppliers: Array<Supplier>;
  templatePreview: Array<TemplatePreviewItem>;
  terminal?: Maybe<Terminal>;
  terminalOrders: Array<TerminalOrder>;
  terminals: Array<Terminal>;
  timeLogs: Array<TimeLog>;
  updateSchedule?: Maybe<UpdateScheduleType>;
  user?: Maybe<User>;
  userAdvances: Array<AdvancePayment>;
  userDailyStats: Array<DailyStat>;
  userLoans: Array<ServiceLoan>;
  userPaymentHistory: Array<SalaryPaymentItemType>;
  userPresences: Array<UserPresence>;
  users: PaginatedUsers;
  vapidPublicKey?: Maybe<Scalars['String']['output']>;
  vatRegister?: Maybe<VatRegister>;
  vatRegisters: Array<VatRegister>;
  vehicle?: Maybe<Vehicle>;
  vehicleAccidents: Array<VehicleAccident>;
  vehicleCostSummary: VehicleCostSummary;
  vehicleDocuments: Array<VehicleDocument>;
  vehicleDrivers: Array<VehicleDriver>;
  vehicleFuelLogs: Array<VehicleFuel>;
  vehicleInspections: Array<VehicleInspection>;
  vehicleInsurances: Array<VehicleInsurance>;
  vehicleMileage: Array<VehicleMileage>;
  vehicleRepairs: Array<VehicleRepair>;
  vehicleSchedules: Array<VehicleSchedule>;
  vehicleTrips: Array<VehicleTrip>;
  vehicleTypes: Array<VehicleType>;
  vehicles: VehiclePage;
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


export type QueryApprovedLeaveRequestsInRangeArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
};


export type QueryAuditLogsArgs = {
  action?: InputMaybe<Scalars['String']['input']>;
  limit?: Scalars['Int']['input'];
  skip?: Scalars['Int']['input'];
};


export type QueryBankAccountsArgs = {
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
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


export type QueryBehavioralAnomaliesArgs = {
  profileId?: InputMaybe<Scalars['Int']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryBehavioralProfilesArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryBehavioralRecommendationsArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryBehavioralSystemHealthArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryCashJournalEntriesArgs = {
  endDate?: InputMaybe<Scalars['String']['input']>;
  operationType?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['String']['input']>;
};


export type QueryCashJournalUnifiedArgs = {
  endDate?: InputMaybe<Scalars['String']['input']>;
  limit?: Scalars['Int']['input'];
  operationType?: InputMaybe<Scalars['String']['input']>;
  paymentMethod?: InputMaybe<Scalars['String']['input']>;
  skip?: Scalars['Int']['input'];
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


export type QueryDocumentationArticlesArgs = {
  categoryId: Scalars['Int']['input'];
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


export type QueryGlobalSettingArgs = {
  key: Scalars['String']['input'];
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


export type QueryManagerEffectivenessArgs = {
  managerId?: InputMaybe<Scalars['Int']['input']>;
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


export type QueryMyNotificationsArgs = {
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
  unreadOnly?: Scalars['Boolean']['input'];
};


export type QueryMyNotificationsCountArgs = {
  unreadOnly?: Scalars['Boolean']['input'];
};


export type QueryMyPaymentHistoryArgs = {
  year?: InputMaybe<Scalars['Int']['input']>;
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


export type QueryOrganizationalHealthArgs = {
  periodEnd?: InputMaybe<Scalars['String']['input']>;
  periodStart?: InputMaybe<Scalars['String']['input']>;
};


export type QueryOrthodoxHolidaysArgs = {
  year?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryPaymentBatchArgs = {
  id: Scalars['Int']['input'];
};


export type QueryPaymentBatchesArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
  periodEnd?: InputMaybe<Scalars['Date']['input']>;
  periodStart?: InputMaybe<Scalars['Date']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
};


export type QueryPaymentStatisticsArgs = {
  companyId: Scalars['Int']['input'];
  month?: InputMaybe<Scalars['Int']['input']>;
  year: Scalars['Int']['input'];
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


export type QueryPersonalityProfilesArgs = {
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryPersonalityQuestionsArgs = {
  templateId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryPersonalityTestAssignmentsArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
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


export type QueryScheduleStatsArgs = {
  month: Scalars['Int']['input'];
  year: Scalars['Int']['input'];
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


export type QueryTemplatePreviewArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
  templateId: Scalars['Int']['input'];
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
  endDate?: InputMaybe<Scalars['Date']['input']>;
  limit?: Scalars['Int']['input'];
  startDate?: InputMaybe<Scalars['Date']['input']>;
  userId?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryUserArgs = {
  id?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryUserAdvancesArgs = {
  userId: Scalars['Int']['input'];
};


export type QueryUserDailyStatsArgs = {
  endDate: Scalars['Date']['input'];
  startDate: Scalars['Date']['input'];
  userId: Scalars['Int']['input'];
};


export type QueryUserLoansArgs = {
  userId: Scalars['Int']['input'];
};


export type QueryUserPaymentHistoryArgs = {
  userId: Scalars['Int']['input'];
  year?: InputMaybe<Scalars['Int']['input']>;
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


export type QueryVehicleAccidentsArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleCostSummaryArgs = {
  vehicleId: Scalars['Int']['input'];
  year?: InputMaybe<Scalars['Int']['input']>;
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


export type QueryVehicleSchedulesArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehicleTripsArgs = {
  vehicleId: Scalars['Int']['input'];
};


export type QueryVehiclesArgs = {
  companyId?: InputMaybe<Scalars['Int']['input']>;
  fuelType?: InputMaybe<Scalars['String']['input']>;
  limit?: Scalars['Int']['input'];
  search?: InputMaybe<Scalars['String']['input']>;
  skip?: Scalars['Int']['input'];
  status?: InputMaybe<Scalars['String']['input']>;
  vehicleType?: InputMaybe<Scalars['String']['input']>;
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
  recipeId?: Maybe<Scalars['Int']['output']>;
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
  wastePercentage: Scalars['Decimal']['output'];
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

export type RecommendationFeedbackType = {
  actionTakenAt: Scalars['DateTime']['output'];
  daysToOutcome: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  improvementDelta: Scalars['Float']['output'];
  managerAction: Scalars['String']['output'];
  managerId: Scalars['Int']['output'];
  managerNotes?: Maybe<Scalars['String']['output']>;
  metricAfter?: Maybe<Scalars['JSONScalar']['output']>;
  metricBefore?: Maybe<Scalars['JSONScalar']['output']>;
  outcome: Scalars['String']['output'];
  outcomeMeasuredAt: Scalars['DateTime']['output'];
  recommendationId: Scalars['Int']['output'];
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

export type SalaryPaymentBatchType = {
  companyId: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['Int']['output'];
  items: Array<SalaryPaymentItemType>;
  notes?: Maybe<Scalars['String']['output']>;
  paidByUser?: Maybe<User>;
  paymentDate: Scalars['DateTime']['output'];
  paymentMethod: Scalars['String']['output'];
  paymentReference?: Maybe<Scalars['String']['output']>;
  periodEnd: Scalars['Date']['output'];
  periodStart: Scalars['Date']['output'];
  status: Scalars['String']['output'];
  totalAmount: Scalars['Float']['output'];
};

export type SalaryPaymentItemType = {
  amount: Scalars['Float']['output'];
  batchId: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  paidAt?: Maybe<Scalars['DateTime']['output']>;
  payslipId?: Maybe<Scalars['Int']['output']>;
  user?: Maybe<User>;
  userId: Scalars['Int']['output'];
};

export type ScheduleStat = {
  assignedDays: Scalars['Int']['output'];
  isComplete: Scalars['Boolean']['output'];
  userId: Scalars['Int']['output'];
  userName: Scalars['String']['output'];
  workDaysNorm: Scalars['Int']['output'];
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
  dayIndex: Scalars['Int']['input'];
  shiftId?: InputMaybe<Scalars['Int']['input']>;
};

export type ScrapTaskInput = {
  quantity: Scalars['Float']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
  taskId: Scalars['Int']['input'];
};

export type ServiceBookContract = {
  baseSalary: Scalars['Float']['output'];
  endDate?: Maybe<Scalars['String']['output']>;
  hoursPerWeek?: Maybe<Scalars['Int']['output']>;
  position: Scalars['String']['output'];
  startDate?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  type: Scalars['String']['output'];
};

export type ServiceBookEmployee = {
  contracts: Array<ServiceBookContract>;
  egn: Scalars['String']['output'];
  name: Scalars['String']['output'];
  periods: Array<ServiceBookPeriod>;
};

export type ServiceBookExport = {
  companyId: Scalars['Int']['output'];
  employees: Array<ServiceBookEmployee>;
  generatedAt: Scalars['String']['output'];
  reportType: Scalars['String']['output'];
  year: Scalars['Int']['output'];
};

export type ServiceBookPeriod = {
  gross: Scalars['Float']['output'];
  month: Scalars['Int']['output'];
  net: Scalars['Float']['output'];
  year: Scalars['Int']['output'];
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
  startDate: Scalars['DateTime']['output'];
  totalAmount: Scalars['Decimal']['output'];
  user: User;
  userId: Scalars['Int']['output'];
};

export type SessionSettings = {
  maxAgeHours: Scalars['Int']['output'];
};

export type Shift = {
  breakDurationMinutes: Scalars['Int']['output'];
  endTime: Scalars['Time']['output'];
  id: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  overnight: Scalars['Boolean']['output'];
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
  smtpPassword: Scalars['String']['output'];
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

export type TemplatePreviewItem = {
  date: Scalars['Date']['output'];
  dayIndex: Scalars['Int']['output'];
  shiftId?: Maybe<Scalars['Int']['output']>;
  shiftName: Scalars['String']['output'];
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
  idempotencyKey?: Maybe<Scalars['String']['output']>;
  isManual: Scalars['Boolean']['output'];
  latitude?: Maybe<Scalars['Decimal']['output']>;
  longitude?: Maybe<Scalars['Decimal']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  startTime: Scalars['DateTime']['output'];
  type: Scalars['String']['output'];
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

export type UpdatePersonalityTemplateInput = {
  id: Scalars['Int']['input'];
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  selectedQuestionIds?: InputMaybe<Array<Scalars['Int']['input']>>;
  shuffle?: InputMaybe<Scalars['Boolean']['input']>;
};

export type UpdateScheduleInput = {
  dayOfWeek?: InputMaybe<Scalars['Int']['input']>;
  enabled?: Scalars['Boolean']['input'];
  hour?: Scalars['Int']['input'];
  minute?: Scalars['Int']['input'];
  notifyEmail?: Scalars['String']['input'];
  scheduleType?: Scalars['String']['input'];
  scheduledAt?: InputMaybe<Scalars['DateTime']['input']>;
};

export type UpdateScheduleType = {
  createdAt: Scalars['DateTime']['output'];
  dayOfWeek?: Maybe<Scalars['Int']['output']>;
  enabled: Scalars['Boolean']['output'];
  hour: Scalars['Int']['output'];
  id: Scalars['Int']['output'];
  lastRunAt?: Maybe<Scalars['DateTime']['output']>;
  lastRunOutput?: Maybe<Scalars['String']['output']>;
  lastRunStatus?: Maybe<Scalars['String']['output']>;
  minute: Scalars['Int']['output'];
  notifyEmail: Scalars['String']['output'];
  scheduleType: Scalars['String']['output'];
  scheduledAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt: Scalars['DateTime']['output'];
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
  activeContract?: Maybe<EmploymentContract>;
  address?: Maybe<Scalars['String']['output']>;
  birthDate?: Maybe<Scalars['Date']['output']>;
  bonuses: Array<Bonus>;
  company?: Maybe<Company>;
  companyId?: Maybe<Scalars['Int']['output']>;
  companyName?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  department?: Maybe<Department>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  departmentName?: Maybe<Scalars['String']['output']>;
  egn?: Maybe<Scalars['String']['output']>;
  email?: Maybe<Scalars['String']['output']>;
  employmentContract?: Maybe<EmploymentContract>;
  firstName?: Maybe<Scalars['String']['output']>;
  fullName: Scalars['String']['output'];
  iban?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  isActive: Scalars['Boolean']['output'];
  isSmtpConfigured: Scalars['Boolean']['output'];
  jobTitle?: Maybe<Scalars['String']['output']>;
  lastLogin?: Maybe<Scalars['DateTime']['output']>;
  lastName?: Maybe<Scalars['String']['output']>;
  leaveBalance?: Maybe<LeaveBalance>;
  passwordForceChange: Scalars['Boolean']['output'];
  payrolls: Array<Payroll>;
  phoneNumber?: Maybe<Scalars['String']['output']>;
  pin?: Maybe<Scalars['String']['output']>;
  position?: Maybe<Position>;
  positionId?: Maybe<Scalars['Int']['output']>;
  profilePicture?: Maybe<Scalars['String']['output']>;
  qrToken?: Maybe<Scalars['String']['output']>;
  role?: Maybe<Role>;
  roleId: Scalars['Int']['output'];
  surname?: Maybe<Scalars['String']['output']>;
  timelogs: Array<TimeLog>;
  username?: Maybe<Scalars['String']['output']>;
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
  expiresAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  ipAddress?: Maybe<Scalars['String']['output']>;
  isActive: Scalars['Boolean']['output'];
  lastUsedAt?: Maybe<Scalars['DateTime']['output']>;
  user?: Maybe<User>;
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
  documents?: Maybe<Array<VehicleDocument>>;
  drivers: Array<VehicleDriver>;
  engineNumber?: Maybe<Scalars['String']['output']>;
  expenses: Array<VehicleExpense>;
  fuelCards?: Maybe<Array<VehicleFuelCard>>;
  fuelRecords: Array<VehicleFuel>;
  fuelType: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  initialMileage?: Maybe<Scalars['Int']['output']>;
  inspections: Array<VehicleInspection>;
  isCompany?: Maybe<Scalars['Boolean']['output']>;
  make: Scalars['String']['output'];
  mileages: Array<VehicleMileage>;
  model: Scalars['String']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  ownerName?: Maybe<Scalars['String']['output']>;
  preTripInspections: Array<VehiclePreTripInspection>;
  registrationNumber: Scalars['String']['output'];
  repairs: Array<VehicleRepair>;
  schedules: Array<VehicleSchedule>;
  status: Scalars['String']['output'];
  tolls: Array<VehicleToll>;
  trips: Array<VehicleTrip>;
  type?: Maybe<VehicleType>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicleTypeId?: Maybe<Scalars['Int']['output']>;
  vignettes?: Maybe<Array<VehicleVignette>>;
  vin?: Maybe<Scalars['String']['output']>;
  year?: Maybe<Scalars['Int']['output']>;
};

export type VehicleAccident = {
  actualCost: Scalars['Decimal']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['Date']['output'];
  description: Scalars['String']['output'];
  downtimeDays: Scalars['Int']['output'];
  estimatedCost: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  location?: Maybe<Scalars['String']['output']>;
  photos?: Maybe<Scalars['JSONScalar']['output']>;
  policeReportNumber?: Maybe<Scalars['String']['output']>;
  severity: Scalars['String']['output'];
  status: Scalars['String']['output'];
  thirdPartyInsurance?: Maybe<Scalars['String']['output']>;
  thirdPartyName?: Maybe<Scalars['String']['output']>;
  vehicleId: Scalars['Int']['output'];
};

export type VehicleAccidentInput = {
  actualCost?: Scalars['Float']['input'];
  date: Scalars['DateTime']['input'];
  description: Scalars['String']['input'];
  downtimeDays?: Scalars['Int']['input'];
  estimatedCost?: Scalars['Float']['input'];
  location?: InputMaybe<Scalars['String']['input']>;
  photos?: InputMaybe<Array<Scalars['String']['input']>>;
  policeReportNumber?: InputMaybe<Scalars['String']['input']>;
  severity?: Scalars['String']['input'];
  status?: Scalars['String']['input'];
  thirdPartyInsurance?: InputMaybe<Scalars['String']['input']>;
  thirdPartyName?: InputMaybe<Scalars['String']['input']>;
  vehicleId: Scalars['Int']['input'];
};

export type VehicleCostCenter = {
  companyId: Scalars['Int']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  departmentId?: Maybe<Scalars['Int']['output']>;
  id: Scalars['Int']['output'];
  isActive?: Maybe<Scalars['Boolean']['output']>;
  name: Scalars['String']['output'];
};

export type VehicleCostSummary = {
  costPerKm?: Maybe<Scalars['Float']['output']>;
  grandTotal: Scalars['Float']['output'];
  totalFuel: Scalars['Float']['output'];
  totalInspections: Scalars['Float']['output'];
  totalInsurances: Scalars['Float']['output'];
  totalRepairs: Scalars['Float']['output'];
  totalTolls: Scalars['Float']['output'];
  totalVignettes: Scalars['Float']['output'];
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
  category?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  isPrimary?: Maybe<Scalars['Boolean']['output']>;
  licenseNumber?: Maybe<Scalars['String']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  user?: Maybe<User>;
  userId: Scalars['Int']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleDriverInput = {
  category?: InputMaybe<Scalars['String']['input']>;
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  isPrimary?: InputMaybe<Scalars['Boolean']['input']>;
  licenseExpiry: Scalars['DateTime']['input'];
  licenseNumber: Scalars['String']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  phone?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['DateTime']['input']>;
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

export type VehicleExpense = {
  amount?: Maybe<Scalars['Decimal']['output']>;
  companyId: Scalars['Int']['output'];
  costCenterId?: Maybe<Scalars['Int']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  expenseDate: Scalars['Date']['output'];
  expenseType: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  isDeductible?: Maybe<Scalars['Boolean']['output']>;
  referenceId?: Maybe<Scalars['Int']['output']>;
  referenceType?: Maybe<Scalars['String']['output']>;
  totalAmount?: Maybe<Scalars['Decimal']['output']>;
  vatAmount?: Maybe<Scalars['Decimal']['output']>;
  vehicleId: Scalars['Int']['output'];
};

export type VehicleFuel = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['DateTime']['output'];
  driverId?: Maybe<Scalars['Int']['output']>;
  efficiencyLPer100km?: Maybe<Scalars['Float']['output']>;
  fuelCardId?: Maybe<Scalars['Int']['output']>;
  fuelType?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  invoiceNumber?: Maybe<Scalars['String']['output']>;
  isAnomaly: Scalars['Boolean']['output'];
  liters: Scalars['Decimal']['output'];
  location?: Maybe<Scalars['String']['output']>;
  mileage?: Maybe<Scalars['Int']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  price: Scalars['Decimal']['output'];
  pricePerLiter: Scalars['Decimal']['output'];
  quantity: Scalars['Decimal']['output'];
  total: Scalars['Decimal']['output'];
  totalAmount: Scalars['Decimal']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleFuelCard = {
  cardNumber: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  expiryDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['Int']['output'];
  isActive?: Maybe<Scalars['Boolean']['output']>;
  limit?: Maybe<Scalars['Decimal']['output']>;
  pin?: Maybe<Scalars['String']['output']>;
  provider?: Maybe<Scalars['String']['output']>;
  vehicleId: Scalars['Int']['output'];
};

export type VehicleFuelInput = {
  date: Scalars['DateTime']['input'];
  fuelType?: InputMaybe<Scalars['String']['input']>;
  liters: Scalars['Float']['input'];
  mileage?: InputMaybe<Scalars['Float']['input']>;
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
  cost?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  inspectionDate: Scalars['Date']['output'];
  inspector?: Maybe<Scalars['String']['output']>;
  mileage?: Maybe<Scalars['Int']['output']>;
  nextDate?: Maybe<Scalars['Date']['output']>;
  nextInspectionDate?: Maybe<Scalars['Date']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  protocolNumber?: Maybe<Scalars['String']['output']>;
  result: Scalars['String']['output'];
  validUntil: Scalars['Date']['output'];
  vehicleId: Scalars['Int']['output'];
};

export type VehicleInspectionInput = {
  cost?: InputMaybe<Scalars['Float']['input']>;
  date: Scalars['DateTime']['input'];
  inspectionType?: InputMaybe<Scalars['String']['input']>;
  nextDate?: InputMaybe<Scalars['String']['input']>;
  nextInspectionDate?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  protocolNumber?: InputMaybe<Scalars['String']['input']>;
  result?: InputMaybe<Scalars['String']['input']>;
  vehicleId: Scalars['Int']['input'];
};

export type VehicleInspectionUpdateInput = {
  cost?: InputMaybe<Scalars['Float']['input']>;
  date?: InputMaybe<Scalars['String']['input']>;
  nextDate?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  protocolNumber?: InputMaybe<Scalars['String']['input']>;
  result?: InputMaybe<Scalars['String']['input']>;
};

export type VehicleInsurance = {
  coverageAmount?: Maybe<Scalars['Decimal']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentUrl?: Maybe<Scalars['String']['output']>;
  endDate: Scalars['Date']['output'];
  id: Scalars['Int']['output'];
  insuranceCompany?: Maybe<Scalars['String']['output']>;
  insuranceType: Scalars['String']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  paymentType?: Maybe<Scalars['String']['output']>;
  policyNumber: Scalars['String']['output'];
  premium?: Maybe<Scalars['Decimal']['output']>;
  provider?: Maybe<Scalars['String']['output']>;
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

export type VehiclePage = {
  totalCount: Scalars['Int']['output'];
  vehicles: Array<Vehicle>;
};

export type VehiclePreTripInspection = {
  brakesCondition?: Maybe<Scalars['Boolean']['output']>;
  brakesParking?: Maybe<Scalars['Boolean']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  driverId: Scalars['Int']['output'];
  fireExtinguisher?: Maybe<Scalars['Boolean']['output']>;
  firstAidKit?: Maybe<Scalars['Boolean']['output']>;
  fluidsBrake?: Maybe<Scalars['Boolean']['output']>;
  fluidsCoolant?: Maybe<Scalars['Boolean']['output']>;
  fluidsOil?: Maybe<Scalars['Boolean']['output']>;
  fluidsWasher?: Maybe<Scalars['Boolean']['output']>;
  horn?: Maybe<Scalars['Boolean']['output']>;
  id: Scalars['Int']['output'];
  inspectionDate?: Maybe<Scalars['DateTime']['output']>;
  lightsBrake?: Maybe<Scalars['Boolean']['output']>;
  lightsHeadlights?: Maybe<Scalars['Boolean']['output']>;
  lightsTurn?: Maybe<Scalars['Boolean']['output']>;
  lightsWarning?: Maybe<Scalars['Boolean']['output']>;
  mirrors?: Maybe<Scalars['Boolean']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  overallStatus: Scalars['String']['output'];
  photos?: Maybe<Scalars['JSONScalar']['output']>;
  seatbelts?: Maybe<Scalars['Boolean']['output']>;
  tiresCondition?: Maybe<Scalars['Boolean']['output']>;
  tiresPressure?: Maybe<Scalars['Boolean']['output']>;
  tiresTread?: Maybe<Scalars['Boolean']['output']>;
  vehicleId: Scalars['Int']['output'];
  warningTriangle?: Maybe<Scalars['Boolean']['output']>;
  wipers?: Maybe<Scalars['Boolean']['output']>;
};

export type VehicleRepair = {
  cost: Scalars['Decimal']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  laborCost?: Maybe<Scalars['Decimal']['output']>;
  laborHours?: Maybe<Scalars['Decimal']['output']>;
  mileage?: Maybe<Scalars['Int']['output']>;
  nextServiceKm?: Maybe<Scalars['Int']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  parts?: Maybe<Scalars['JSONScalar']['output']>;
  partsCost?: Maybe<Scalars['Decimal']['output']>;
  repairDate: Scalars['DateTime']['output'];
  repairType?: Maybe<Scalars['String']['output']>;
  totalCost?: Maybe<Scalars['Decimal']['output']>;
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

export type VehicleSchedule = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['Int']['output'];
  intervalKm?: Maybe<Scalars['Int']['output']>;
  intervalMonths?: Maybe<Scalars['Int']['output']>;
  lastServiceDate?: Maybe<Scalars['Date']['output']>;
  lastServiceKm?: Maybe<Scalars['Int']['output']>;
  nextServiceDate?: Maybe<Scalars['Date']['output']>;
  nextServiceKm?: Maybe<Scalars['Int']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  scheduleType: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicleId: Scalars['Int']['output'];
  vehicleServiceId?: Maybe<Scalars['Int']['output']>;
};

export type VehicleToll = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentUrl?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  route?: Maybe<Scalars['String']['output']>;
  section?: Maybe<Scalars['String']['output']>;
  tollAmount: Scalars['Decimal']['output'];
  tollDate?: Maybe<Scalars['DateTime']['output']>;
  vehicleId: Scalars['Int']['output'];
};

export type VehicleTrip = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  deliveryId?: Maybe<Scalars['Int']['output']>;
  distanceKm?: Maybe<Scalars['Int']['output']>;
  driverId: Scalars['Int']['output'];
  endAddress?: Maybe<Scalars['String']['output']>;
  endTime?: Maybe<Scalars['DateTime']['output']>;
  expenses?: Maybe<Scalars['Decimal']['output']>;
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

export type VehicleVignette = {
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentUrl?: Maybe<Scalars['String']['output']>;
  id: Scalars['Int']['output'];
  price?: Maybe<Scalars['Decimal']['output']>;
  provider?: Maybe<Scalars['String']['output']>;
  purchaseDate?: Maybe<Scalars['Date']['output']>;
  validFrom?: Maybe<Scalars['Date']['output']>;
  validUntil?: Maybe<Scalars['Date']['output']>;
  vehicleId: Scalars['Int']['output'];
  vignetteType: Scalars['String']['output'];
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
  cashBalance: Scalars['Decimal']['output'];
  cashExpense: Scalars['Decimal']['output'];
  cashIncome: Scalars['Decimal']['output'];
  id: Scalars['Int']['output'];
  incomingInvoicesCount: Scalars['Int']['output'];
  incomingInvoicesTotal: Scalars['Decimal']['output'];
  invoicesCount: Scalars['Int']['output'];
  invoicesTotal: Scalars['Decimal']['output'];
  outgoingInvoicesCount: Scalars['Int']['output'];
  outgoingInvoicesTotal: Scalars['Decimal']['output'];
  overdueInvoicesCount: Scalars['Int']['output'];
  paidInvoicesCount: Scalars['Int']['output'];
  unpaidInvoicesCount: Scalars['Int']['output'];
  vatCollected: Scalars['Decimal']['output'];
  vatPaid: Scalars['Decimal']['output'];
  year: Scalars['Int']['output'];
};
