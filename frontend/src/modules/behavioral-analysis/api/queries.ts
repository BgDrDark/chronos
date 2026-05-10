import { gql } from '@apollo/client';

export const GET_BEHAVIORAL_PROFILES = gql`
  query GetBehavioralProfiles($companyId: Int, $userId: Int) {
    behavioralProfiles(companyId: $companyId, userId: $userId) {
      id
      userId
      companyId
      periodStart
      periodEnd
      employeeType
      tenureDays
      probationMode
      dataCompleteness
      punctualityScore
      efficiencyScore
      overtimeScore
      burnoutRisk
      financialStressScore
      engagementScore
      scrapRate
      peerGroupPercentile
      trendDirection
      status
      confidenceScore
      contributionFactors
      ruleEngineVersion
      computedAt
      version
    }
  }
`;

export const GET_BEHAVIORAL_ANOMALIES = gql`
  query GetBehavioralAnomalies($profileId: Int, $userId: Int) {
    behavioralAnomalies(profileId: $profileId, userId: $userId) {
      id
      profileId
      userId
      anomalyType
      severity
      metricName
      actualValue
      expectedValue
      deviation
      confidenceScore
      suppressed
      suppressionReason
      description
      contextSummary
      detectedAt
    }
  }
`;

export const GET_BEHAVIORAL_RULES = gql`
  query GetBehavioralRules {
    behavioralRules {
      id
      name
      description
      ruleType
      isSystem
      isActive
      shadowMode
      companyId
      conditionType
      conditionConfig
      recommendationTemplate
      autoExecuteAction
      autoExecute
      effectivenessScore
      falsePositiveRate
      triggerCount
      acceptedCount
      effectiveCount
      falsePositiveCount
      createdBy
      createdAt
      updatedAt
    }
  }
`;

export const GET_BEHAVIORAL_RECOMMENDATIONS = gql`
  query GetBehavioralRecommendations($userId: Int, $status: String) {
    behavioralRecommendations(userId: $userId, status: $status) {
      id
      ruleId
      userId
      anomalyId
      type
      priority
      title
      description
      suggestedAction
      explanation
      coachingTips
      confidenceScore
      status
      autoExecuted
      throttled
      aggregatedCount
      disputeReason
      disputeNotes
      createdAt
      expiresAt
    }
  }
`;

export const GET_BEHAVIORAL_SETTINGS = gql`
  query GetBehavioralSettings {
    behavioralSettings {
      id
      companyId
      rawProfileDays
      aggregatedProfileMonths
      recommendationMonths
      feedbackMonths
      auditLogMonths
      autoCleanupEnabled
      cleanupSchedule
      anonymizeInsteadOfDelete
      updatedBy
      updatedAt
    }
  }
`;

export const GET_ORGANIZATIONAL_HEALTH = gql`
  query GetOrganizationalHealth($periodStart: String, $periodEnd: String) {
    organizationalHealth(periodStart: $periodStart, periodEnd: $periodEnd) {
      departmentId
      departmentName
      avgBurnoutRisk
      avgEngagement
      avgEfficiency
      avgPunctuality
      anomalyCount
      employeeCount
      turnoverRate
      trend
      isSystemicIssue
    }
  }
`;

export const GET_BIAS_REPORTS = gql`
  query GetBiasReports {
    biasReports {
      id
      companyId
      periodStart
      periodEnd
      findings
      overallBiasDetected
      generatedAt
    }
  }
`;

export const GET_SYSTEM_HEALTH = gql`
  query GetSystemHealth {
    behavioralSystemHealth {
      id
      companyId
      lastComputationAt
      lastComputationStatus
      lastComputationDurationSeconds
      employeesProcessed
      employeesFailed
      circuitBreakerOpen
      circuitBreakerFailureCount
      lastSuccessfulProfileDate
      triggeredAlertsToday
      lastBiasCheck
    }
  }
`;
