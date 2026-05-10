import { gql } from '@apollo/client';

export const CREATE_BEHAVIORAL_RULE = gql`
  mutation CreateBehavioralRule($input: BehavioralRuleInput!) {
    createBehavioralRule(input: $input) {
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

export const UPDATE_BEHAVIORAL_RULE = gql`
  mutation UpdateBehavioralRule($ruleId: Int!, $input: BehavioralRuleInput!) {
    updateBehavioralRule(ruleId: $ruleId, input: $input) {
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

export const DELETE_BEHAVIORAL_RULE = gql`
  mutation DeleteBehavioralRule($ruleId: Int!) {
    deleteBehavioralRule(ruleId: $ruleId)
  }
`;

export const UPDATE_BEHAVIORAL_SETTINGS = gql`
  mutation UpdateBehavioralSettings($input: BehavioralSettingsInput!) {
    updateBehavioralSettings(input: $input) {
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

export const UPDATE_RECOMMENDATION_STATUS = gql`
  mutation UpdateRecommendationStatus($recommendationId: Int!, $status: String!, $disputeReason: String, $disputeNotes: String) {
    updateRecommendationStatus(recommendationId: $recommendationId, status: $status, disputeReason: $disputeReason, disputeNotes: $disputeNotes) {
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

export const COMPUTE_ORGANIZATIONAL_HEALTH = gql`
  mutation ComputeOrganizationalHealth($periodStart: String, $periodEnd: String) {
    computeOrganizationalHealth(periodStart: $periodStart, periodEnd: $periodEnd) {
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

export const COMPUTE_BIAS_REPORT = gql`
  mutation ComputeBiasReport($periodStart: String, $periodEnd: String) {
    computeBiasReport(periodStart: $periodStart, periodEnd: $periodEnd) {
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
