export interface BehavioralProfile {
  id: number;
  userId: number;
  companyId: number;
  periodStart: string;
  periodEnd: string;
  employeeType: string;
  tenureDays: number;
  probationMode: boolean;
  dataCompleteness: number;
  punctualityScore: number;
  efficiencyScore: number;
  overtimeScore: number;
  burnoutRisk: number;
  financialStressScore: number;
  attendanceScore: number;
  engagementScore?: number | null;
  scrapRate: number;
  peerGroupPercentile: number;
  trendDirection: string;
  status: string;
  confidenceScore: number;
  contributionFactors?: Record<string, unknown>;
  ruleEngineVersion: string;
  computedAt: string;
  version: number;
}

export interface BehavioralAnomaly {
  id: number;
  profileId: number;
  userId: number;
  anomalyType: string;
  severity: number;
  metricName: string;
  actualValue: number;
  expectedValue: number;
  deviation: number;
  confidenceScore: number;
  suppressed: boolean;
  suppressionReason?: string;
  description: string;
  contextSummary?: Record<string, unknown>;
  detectedAt: string;
}

export interface BehavioralRule {
  id: number;
  name: string;
  description?: string;
  ruleType: string;
  isSystem: boolean;
  isActive: boolean;
  shadowMode: boolean;
  companyId: number;
  conditionType: string;
  conditionConfig: Record<string, unknown>;
  recommendationTemplate: Record<string, unknown>;
  autoExecuteAction?: string;
  autoExecute: boolean;
  effectivenessScore: number;
  falsePositiveRate: number;
  triggerCount: number;
  acceptedCount: number;
  effectiveCount: number;
  falsePositiveCount: number;
  createdBy: number;
  createdAt: string;
  updatedAt: string;
}

export interface BehavioralRecommendation {
  id: number;
  ruleId: number;
  userId: number;
  anomalyId?: number;
  type: string;
  priority: string;
  title: string;
  description: string;
  suggestedAction: string;
  explanation: string;
  coachingTips?: Record<string, unknown>;
  confidenceScore: number;
  status: string;
  autoExecuted: boolean;
  throttled: boolean;
  aggregatedCount: number;
  disputeReason?: string;
  disputeNotes?: string;
  createdAt: string;
  expiresAt?: string;
}

export interface BehavioralSettings {
  id: number;
  companyId: number;
  rawProfileDays: number;
  aggregatedProfileMonths: number;
  recommendationMonths: number;
  feedbackMonths: number;
  auditLogMonths: number;
  autoCleanupEnabled: boolean;
  cleanupSchedule: string;
  anonymizeInsteadOfDelete: boolean;
  updatedBy: number;
  updatedAt: string;
}

export interface OrganizationalHealth {
  departmentId: number;
  departmentName: string;
  avgBurnoutRisk: number;
  avgAttendance: number;
  avgEfficiency: number;
  avgPunctuality: number;
  anomalyCount: number;
  employeeCount: number;
  turnoverRate: number;
  trend: string;
  isSystemicIssue: boolean;
}

export interface BiasReport {
  id: number;
  companyId: number;
  periodStart: string;
  periodEnd: string;
  findings: Record<string, unknown>[];
  overallBiasDetected: boolean;
  generatedAt: string;
}

export interface BehavioralPersonalityProfile {
  id: number;
  userId: number;
  companyId: number;
  templateId: number;
  completedAt: string;
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  opennessRaw: number;
  conscientiousnessRaw: number;
  extraversionRaw: number;
  agreeablenessRaw: number;
  neuroticismRaw: number;
  interpretation: string | null;
}

export interface BehavioralPulseSurvey {
  id: number;
  userId: number;
  companyId: number;
  submittedAt: string;
  burnoutFeeling: number | null;
  engagementFeeling: number | null;
  stressLevel: number | null;
  energyLevel: number | null;
  workSatisfaction: number | null;
  surveyVersion: string;
  notes: string | null;
}

export interface PersonalityQuestion {
  id: number;
  bg: string;
  en: string;
  factor: string;
  direction: string;
}

export interface PersonalityTestTemplate {
  id: number;
  name: string;
  selectedQuestionIds: number[];
  shuffle: boolean;
  isActive: boolean;
  createdAt: string;
}

export interface ManagerEffectiveness {
  id: number;
  managerId: number;
  companyId: number;
  periodStart: string;
  periodEnd: string;
  teamAvgAttendance: number;
  teamAvgEngagement: number;
  teamAvgBurnout: number;
  teamBurnoutVariance: number;
  teamTurnoverRate: number;
  teamSize: number;
  teamAnomalyCount: number;
  managerEffectivenessScore: number;
  sentimentScore: number;
  trendDirection: string;
  computedAt: string;
}
