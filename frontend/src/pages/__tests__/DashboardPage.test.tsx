import { vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MockedProvider } from '@apollo/client/testing';
import { gql } from '@apollo/client';
import DashboardPage from '../DashboardPage';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../themeContext', () => ({
  useAppTheme: () => ({
    dashboardConfig: { showChart: true, showWeeklyTable: true, showFleetCard: true },
    mode: 'light',
    toggleTheme: vi.fn(),
    toggleDashboardWidget: vi.fn(),
  }),
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="chart">{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

vi.mock('../components/ShiftSwapCenter', () => ({
  default: () => <div data-testid="shift-swap-center">Shift Swap Center</div>,
}));

vi.mock('../components/MyQrCard', () => ({
  default: () => <div data-testid="my-qr-card">My QR Card</div>,
}));

const DASHBOARD_QUERY = gql`
  query GetDashboardData($startDate: Date!, $endDate: Date!) {
    me {
      id
      email
      firstName
      lastName
      qrToken
      role { name }
      leaveBalance { totalDays usedDays }
      timelogs(startDate: $startDate, endDate: $endDate) { id startTime endTime }
    }
    activeTimeLog { id startTime }
    myDailyStats(startDate: $startDate, endDate: $endDate) {
      date regularHours overtimeHours totalWorkedHours shiftName
    }
    weeklySummary(date: $startDate) {
      totalRegularHours totalOvertimeHours targetHours debtHours surplusHours statusMessage
    }
  }
`;

const now = new Date();
const startOfWeek = new Date(now);
startOfWeek.setDate(now.getDate() - now.getDay() + (now.getDay() === 0 ? -6 : 1));
const endOfWeek = new Date(startOfWeek);
endOfWeek.setDate(startOfWeek.getDate() + 6);

const createMocks = (overrides: Record<string, unknown> = {}) => {
  const defaultMe = {
    id: 1,
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    qrToken: 'qr-token-123',
    role: { name: 'user' },
    leaveBalance: { totalDays: 20, usedDays: 5 },
    timelogs: [],
    __typename: 'User',
  };

  return [
    {
      request: {
        query: DASHBOARD_QUERY,
        variables: {
          startDate: startOfWeek.toISOString().split('T')[0],
          endDate: endOfWeek.toISOString().split('T')[0],
        },
      },
      result: {
        data: {
          me: { ...defaultMe, ...overrides.me },
          activeTimeLog: overrides.activeTimeLog ?? null,
          myDailyStats: [
            {
              date: startOfWeek.toISOString().split('T')[0],
              regularHours: 8,
              overtimeHours: 0,
              totalWorkedHours: 8,
              shiftName: 'Дневна',
              __typename: 'UserDailyStat',
            },
          ],
          weeklySummary: {
            totalRegularHours: 40,
            totalOvertimeHours: 0,
            targetHours: 40,
            debtHours: 0,
            surplusHours: 0,
            statusMessage: 'Седмицата е балансирана',
            __typename: 'WeeklySummary',
          },
        },
      },
    },
  ];
};

const renderDashboard = (mocks: unknown[] = createMocks()) => {
  render(
    <MockedProvider mocks={mocks as any} addTypename={true}>
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    </MockedProvider>
  );
};

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('renders loading state initially', () => {
    renderDashboard();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders dashboard with user data', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/лично табло/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/здравей, test!/i)).toBeInTheDocument();
    expect(screen.getByText(/my qr card/i)).toBeInTheDocument();
    expect(screen.getByText(/shift swap center/i)).toBeInTheDocument();
  });

  test('shows clock in button when no active session', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /вход/i })).toBeInTheDocument();
    });
  });

  test('shows clock out button when active session exists', async () => {
    const activeSessionMocks = createMocks({
      activeTimeLog: { id: 1, startTime: new Date(Date.now() - 3600000).toISOString(), __typename: 'TimeLog' },
    });

    renderDashboard(activeSessionMocks);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /изход/i })).toBeInTheDocument();
    });
  });

  test('displays weekly summary alert', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/седмицата е балансирана/i)).toBeInTheDocument();
    });
  });

  test('displays shift name', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/текуща смяна/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/дневна/i)).toBeInTheDocument();
  });

  test('shows admin fleet widget for admin users', async () => {
    const adminMocks = createMocks({
      me: {
        id: 1,
        email: 'admin@example.com',
        firstName: 'Admin',
        lastName: 'User',
        qrToken: 'qr-token-123',
        role: { name: 'admin' },
        leaveBalance: { totalDays: 20, usedDays: 5 },
        timelogs: [],
        __typename: 'User',
      },
    });

    renderDashboard(adminMocks);

    await waitFor(() => {
      expect(screen.getByText(/автопарк/i)).toBeInTheDocument();
    });
  });

  test('displays error when query fails', async () => {
    const errorMocks = [{
      request: {
        query: DASHBOARD_QUERY,
        variables: {
          startDate: startOfWeek.toISOString().split('T')[0],
          endDate: endOfWeek.toISOString().split('T')[0],
        },
      },
      error: new Error('Network error'),
    }];

    renderDashboard(errorMocks);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  test('shows weekly activity chart', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/активност през седмицата/i)).toBeInTheDocument();
    });
    expect(screen.getByTestId('chart')).toBeInTheDocument();
  });

  test('shows detailed weekly table', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/детайлен отчет за седмицата/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/ден/i)).toBeInTheDocument();
    expect(screen.getByText(/вход/i)).toBeInTheDocument();
    expect(screen.getByText(/изход/i)).toBeInTheDocument();
  });
});
