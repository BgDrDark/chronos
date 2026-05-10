import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MockedProvider } from '@apollo/client/testing';
import React from 'react';

// Components
import BehavioralAnalysisPage from '../../src/modules/behavioral-analysis/components/BehavioralAnalysisPage';
import RuleBuilderPage from '../../src/modules/behavioral-analysis/components/RuleBuilderPage';
import SettingsPage from '../../src/modules/behavioral-analysis/components/SettingsPage';
import OrganizationalHealthPage from '../../src/modules/behavioral-analysis/components/OrganizationalHealthPage';
import BiasMonitorPage from '../../src/modules/behavioral-analysis/components/BiasMonitorPage';
import EmployeeProfilePage from '../../src/modules/behavioral-analysis/components/EmployeeProfilePage';
import SystemHealthPage from '../../src/modules/behavioral-analysis/components/SystemHealthPage';

// Queries/Mutations
import {
  GET_BEHAVIORAL_PROFILES,
  GET_BEHAVIORAL_ANOMALIES,
  GET_BEHAVIORAL_RECOMMENDATIONS,
  GET_BEHAVIORAL_RULES,
  GET_BEHAVIORAL_SETTINGS,
  GET_ORGANIZATIONAL_HEALTH,
  GET_BIAS_REPORTS,
  GET_SYSTEM_HEALTH,
} from '../../src/modules/behavioral-analysis/api/queries';
import {
  CREATE_BEHAVIORAL_RULE,
  UPDATE_BEHAVIORAL_RULE,
  DELETE_BEHAVIORAL_RULE,
  UPDATE_BEHAVIORAL_SETTINGS,
  UPDATE_RECOMMENDATION_STATUS,
  COMPUTE_ORGANIZATIONAL_HEALTH,
  COMPUTE_BIAS_REPORT,
} from '../../src/modules/behavioral-analysis/api/mutations';

// Mocks
vi.mock('@apollo/client', async () => {
  const actual = await vi.importActual('@apollo/client');
  return {
    ...actual,
    useQuery: vi.fn(),
    useMutation: vi.fn(),
  };
});

vi.mock('../../src/context/ErrorContext', () => ({
  useError: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
  }),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => ({ id: '1' }),
  useNavigate: () => vi.fn(),
}));

// ==========================================
# Mock Data
// ==========================================

const mockProfiles = [
  {
    __typename: 'BehavioralProfileType',
    id: 1,
    userId: 1,
    companyId: 1,
    periodStart: '2024-01-01',
    periodEnd: '2024-01-31',
    employeeType: 'full_time',
    tenureDays: 365,
    probationMode: false,
    dataCompleteness: 1.0,
    punctualityScore: 95.0,
    efficiencyScore: 90.0,
    overtimeScore: 10.0,
    burnoutRisk: 0.3,
    financialStressScore: 0.1,
    engagementScore: 95.0,
    scrapRate: 2.0,
    peerGroupPercentile: 70.0,
    trendDirection: 'stable',
    status: 'stable',
    confidenceScore: 1.0,
    contributionFactors: { burnout_risk: 0.3, overtime_hours: 0.2 },
    ruleEngineVersion: 'v1.0.0',
    computedAt: '2024-01-31T12:00:00Z',
    version: 1,
  },
];

const mockAnomalies = [
  {
    __typename: 'BehavioralAnomalyType',
    id: 1,
    profileId: 1,
    userId: 1,
    anomalyType: 'threshold_breach',
    severity: 4,
    metricName: 'burnout_risk',
    actualValue: 0.8,
    expectedValue: 0.6,
    deviation: 0.2,
    confidenceScore: 0.9,
    suppressed: false,
    suppressionReason: null,
    description: 'Burnout risk exceeded threshold',
    contextSummary: null,
    detectedAt: '2024-01-30T10:00:00Z',
  },
];

const mockRecommendations = [
  {
    __typename: 'BehavioralRecommendationType',
    id: 1,
    ruleId: 1,
    userId: 1,
    anomalyId: 1,
    type: 'burnout_intervention',
    priority: 'high',
    title: 'High burnout risk detected',
    description: 'Employee shows signs of burnout',
    suggestedAction: 'Schedule a 1:1 meeting',
    explanation: 'Burnout risk is above threshold',
    coachingTips: { approach: 'supportive' },
    confidenceScore: 0.8,
    status: 'pending',
    autoExecuted: false,
    throttled: false,
    aggregatedCount: 1,
    disputeReason: null,
    disputeNotes: null,
    createdAt: '2024-01-30T12:00:00Z',
    expiresAt: null,
  },
];

const mockRules = [
  {
    __typename: 'BehavioralRuleType',
    id: 1,
    name: 'Burnout Detection',
    description: 'Detects high burnout risk',
    ruleType: 'built_in',
    isSystem: true,
    isActive: true,
    shadowMode: false,
    companyId: 1,
    conditionType: 'threshold',
    conditionConfig: { metric: 'burnout_risk', operator: '>', threshold: 0.7 },
    recommendationTemplate: { type: 'burnout_intervention', priority: 'high' },
    autoExecuteAction: 'notification',
    autoExecute: true,
    effectivenessScore: 0.8,
    falsePositiveRate: 0.1,
    triggerCount: 10,
    acceptedCount: 8,
    effectiveCount: 7,
    falsePositiveCount: 1,
    createdBy: 1,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

const mockSettings = {
  __typename: 'BehavioralSettingsType',
  id: 1,
  companyId: 1,
  rawProfileDays: 90,
  aggregatedProfileMonths: 12,
  recommendationMonths: 6,
  feedbackMonths: 24,
  auditLogMonths: 36,
  autoCleanupEnabled: true,
  cleanupSchedule: 'nightly',
  anonymizeInsteadOfDelete: false,
  updatedBy: 1,
  updatedAt: '2024-01-01T00:00:00Z',
};

const mockHealthData = [
  {
    __typename: 'OrganizationalHealthType',
    departmentId: 1,
    departmentName: 'Sales',
    avgBurnoutRisk: 0.4,
    avgEngagement: 80.0,
    avgEfficiency: 85.0,
    avgPunctuality: 90.0,
    anomalyCount: 2,
    employeeCount: 10,
    turnoverRate: 0.05,
    trend: 'stable',
    isSystemicIssue: false,
  },
];

const mockBiasReport = {
  __typename: 'BiasReportType',
  id: 1,
  companyId: 1,
  periodStart: '2024-01-01',
  periodEnd: '2024-01-31',
  findings: [
    {
      metric: 'burnout_risk',
      group_a: 'Sales',
      group_b: 'IT',
      group_a_avg: 0.8,
      group_b_avg: 0.3,
      difference: 0.5,
      recommendation: 'Review workload distribution',
    },
  ],
  overallBiasDetected: true,
  generatedAt: '2024-01-31T12:00:00Z',
};

const mockSystemHealth = {
  __typename: 'BehavioralSystemHealthType',
  id: 1,
  companyId: 1,
  lastComputationAt: '2024-01-31T02:00:00Z',
  lastComputationStatus: 'success',
  lastComputationDurationSeconds: 120,
  employeesProcessed: 50,
  employeesFailed: 0,
  circuitBreakerOpen: false,
  circuitBreakerFailureCount: 0,
  lastSuccessfulProfileDate: '2024-01-31T02:00:00Z',
  triggeredAlertsToday: 3,
  lastBiasCheck: '2024-01-30T12:00:00Z',
};

// ==========================================
# Mocks for Apollo
// ==========================================

const mocks = {
  profiles: [
    {
      request: { query: GET_BEHAVIORAL_PROFILES, variables: {} },
      result: { data: { behavioralProfiles: mockProfiles } },
    },
  ],
  anomalies: [
    {
      request: { query: GET_BEHAVIORAL_ANOMALIES, variables: {} },
      result: { data: { behavioralAnomalies: mockAnomalies } },
    },
  ],
  recommendations: [
    {
      request: { query: GET_BEHAVIORAL_RECOMMENDATIONS, variables: {} },
      result: { data: { behavioralRecommendations: mockRecommendations } },
    },
  ],
  rules: [
    {
      request: { query: GET_BEHAVIORAL_RULES },
      result: { data: { behavioralRules: mockRules } },
    },
  ],
  settings: [
    {
      request: { query: GET_BEHAVIORAL_SETTINGS },
      result: { data: { behavioralSettings: mockSettings } },
    },
  ],
  health: [
    {
      request: { query: GET_ORGANIZATIONAL_HEALTH, variables: {} },
      result: { data: { organizationalHealth: mockHealthData } },
    },
  ],
  bias: [
    {
      request: { query: GET_BIAS_REPORTS },
      result: { data: { biasReports: [mockBiasReport] } },
    },
  ],
  systemHealth: [
    {
      request: { query: GET_SYSTEM_HEALTH },
      result: { data: { behavioralSystemHealth: mockSystemHealth } },
    },
  ],
};

// ==========================================
# Tests
// ==========================================

describe('BehavioralAnalysisPage', () => {
  it('renders dashboard with metrics', async () => {
    render(
      <MockedProvider mocks={[...mocks.profiles, ...mocks.anomalies, ...mocks.recommendations]} addTypename={false}>
        <BehavioralAnalysisPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Поведенчески анализ')).toBeInTheDocument();
    });
  });

  it('shows critical count', async () => {
    const criticalMock = {
      request: { query: GET_BEHAVIORAL_PROFILES, variables: {} },
      result: {
        data: {
          behavioralProfiles: [{ ...mockProfiles[0], status: 'critical' }],
        },
      },
    };

    render(
      <MockedProvider mocks={[criticalMock, ...mocks.anomalies, ...mocks.recommendations]} addTypename={false}>
        <BehavioralAnalysisPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });
});

describe('RuleBuilderPage', () => {
  it('renders rule list', async () => {
    render(
      <MockedProvider mocks={mocks.rules} addTypename={false}>
        <RuleBuilderPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Burnout Detection')).toBeInTheDocument();
    });
  });

  it('shows rule type badge', async () => {
    render(
      <MockedProvider mocks={mocks.rules} addTypename={false}>
        <RuleBuilderPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Системно')).toBeInTheDocument();
    });
  });
});

describe('SettingsPage', () => {
  it('renders settings form', async () => {
    render(
      <MockedProvider mocks={mocks.settings} addTypename={false}>
        <SettingsPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Запазване на профили (дни)')).toBeInTheDocument();
    });
  });

  it('loads settings from API', async () => {
    render(
      <MockedProvider mocks={mocks.settings} addTypename={false}>
        <SettingsPage />
      </MockedProvider>
    );

    await waitFor(() => {
      const input = screen.getByLabelText('Запазване на профили (дни)') as HTMLInputElement;
      expect(input.value).toBe('90');
    });
  });
});

describe('OrganizationalHealthPage', () => {
  it('renders department cards', async () => {
    render(
      <MockedProvider mocks={mocks.health} addTypename={false}>
        <OrganizationalHealthPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Sales')).toBeInTheDocument();
    });
  });

  it('shows burnout risk bar', async () => {
    render(
      <MockedProvider mocks={mocks.health} addTypename={false}>
        <OrganizationalHealthPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('40%')).toBeInTheDocument();
    });
  });
});

describe('BiasMonitorPage', () => {
  it('renders bias report', async () => {
    render(
      <MockedProvider mocks={mocks.bias} addTypename={false}>
        <BiasMonitorPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Открити са статистически значими разлики между групи.')).toBeInTheDocument();
    });
  });

  it('shows findings table', async () => {
    render(
      <MockedProvider mocks={mocks.bias} addTypename={false}>
        <BiasMonitorPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('burnout_risk')).toBeInTheDocument();
    });
  });
});

describe('SystemHealthPage', () => {
  it('renders system status', async () => {
    render(
      <MockedProvider mocks={mocks.systemHealth} addTypename={false}>
        <SystemHealthPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Системно здраве')).toBeInTheDocument();
    });
  });

  it('shows circuit breaker status', async () => {
    render(
      <MockedProvider mocks={mocks.systemHealth} addTypename={false}>
        <SystemHealthPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Затворен (Активен)')).toBeInTheDocument();
    });
  });

  it('shows employee stats', async () => {
    render(
      <MockedProvider mocks={mocks.systemHealth} addTypename={false}>
        <SystemHealthPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('50')).toBeInTheDocument();
    });
  });
});
