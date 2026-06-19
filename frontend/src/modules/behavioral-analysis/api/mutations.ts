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
      avgAttendance
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

export const SUBMIT_PERSONALITY_TEST = gql`
  mutation SubmitPersonalityTest($input: PersonalityTestAnswers!) {
    submitPersonalityTest(input: $input) {
      id
      userId
      companyId
      templateId
      completedAt
      openness
      conscientiousness
      extraversion
      agreeableness
      neuroticism
      opennessRaw
      conscientiousnessRaw
      extraversionRaw
      agreeablenessRaw
      neuroticismRaw
      interpretation
    }
  }
`;

export const SUBMIT_PULSE_SURVEY = gql`
  mutation SubmitPulseSurvey($input: PulseSurveyInput!) {
    submitPulseSurvey(input: $input) {
      id
      userId
      companyId
      submittedAt
      burnoutFeeling
      engagementFeeling
      stressLevel
      energyLevel
      workSatisfaction
      surveyVersion
      notes
    }
  }
`;

export const COMPUTE_MANAGER_EFFECTIVENESS = gql`
  mutation ComputeManagerEffectiveness($managerId: Int!, $periodStart: String, $periodEnd: String) {
    computeManagerEffectiveness(managerId: $managerId, periodStart: $periodStart, periodEnd: $periodEnd) {
      id
      managerId
      companyId
      periodStart
      periodEnd
      teamAvgAttendance
      teamAvgEngagement
      teamAvgBurnout
      teamBurnoutVariance
      teamTurnoverRate
      teamSize
      teamAnomalyCount
      managerEffectivenessScore
      sentimentScore
      trendDirection
      computedAt
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

export const CREATE_PERSONALITY_TEMPLATE = gql`
  mutation CreatePersonalityTemplate($input: CreatePersonalityTemplateInput!) {
    createPersonalityTemplate(input: $input) {
      id
      name
      selectedQuestionIds
      shuffle
      isActive
      createdAt
    }
  }
`;

export const UPDATE_PERSONALITY_TEMPLATE = gql`
  mutation UpdatePersonalityTemplate($input: UpdatePersonalityTemplateInput!) {
    updatePersonalityTemplate(input: $input) {
      id
      name
      selectedQuestionIds
      shuffle
      isActive
      createdAt
    }
  }
`;

export const DELETE_PERSONALITY_TEMPLATE = gql`
  mutation DeletePersonalityTemplate($id: Int!) {
    deletePersonalityTemplate(id: $id)
  }
`;

export const ASSIGN_PERSONALITY_TEST = gql`
  mutation AssignPersonalityTest($userIds: [Int!]!, $templateId: Int!, $dueBy: DateTime!) {
    assignPersonalityTest(userIds: $userIds, templateId: $templateId, dueBy: $dueBy) {
      id
      userId
      userName
      userEmail
      templateId
      templateName
      dueBy
      status
      assignedAt
    }
  }
`;

export const REASSIGN_PERSONALITY_TEST = gql`
  mutation ReassignPersonalityTest($assignmentId: Int!, $dueBy: DateTime, $templateId: Int) {
    reassignPersonalityTest(assignmentId: $assignmentId, dueBy: $dueBy, templateId: $templateId) {
      id
      userId
      userName
      userEmail
      templateId
      templateName
      dueBy
      status
      completedAt
    }
  }
`;
