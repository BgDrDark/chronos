import { vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { MockedProvider } from '@apollo/client/testing';
import { gql } from '@apollo/client';
import ProfilePage from '../ProfilePage';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useParams: () => ({ id: undefined }),
  };
});

vi.mock('../currencyContext', () => ({
  useCurrency: () => ({ currency: 'лв.' }),
}));

vi.mock('../themeContext', () => ({
  useAppTheme: () => ({
    mode: 'light',
    toggleTheme: vi.fn(),
    dashboardConfig: { showChart: true, showWeeklyTable: true, showFleetCard: true },
    toggleDashboardWidget: vi.fn(),
  }),
}));

vi.mock('../components/PushNotificationManager', () => ({
  default: () => <div data-testid="push-notification-manager">Push Notifications</div>,
}));

vi.mock('../components/MyQrCard', () => ({
  default: () => <div data-testid="my-qr-card">My QR Card</div>,
}));

vi.mock('../components/DocumentManager', () => ({
  default: () => <div data-testid="document-manager">Document Manager</div>,
}));

vi.mock('../components/ContractDossier', () => ({
  default: () => <div data-testid="contract-dossier">Contract Dossier</div>,
}));

vi.mock('../services/biometricService', () => ({
  biometricService: {
    registerBiometrics: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('axios', () => ({
  default: {
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

const GET_USER_PROFILE = gql`
  query GetUserProfile($id: Int) {
    user(id: $id) {
      id email firstName lastName phoneNumber address egn birthDate iban jobTitle
      departmentName companyName createdAt qrToken profilePicture
      role { name }
      leaveBalance { totalDays usedDays }
      payrolls { monthlySalary hourlyRate currency }
      activeContract {
        id contractNumber contractType startDate endDate baseSalary
        salaryInstallmentsCount monthlyAdvanceAmount positionTitle
        department { id name }
      }
    }
    me { id role { name } }
  }
`;

const CHANGE_PASSWORD_MUTATION = gql`
  mutation ChangePassword($oldPassword: String!, $newPassword: String!) {
    changePassword(oldPassword: $oldPassword, newPassword: $newPassword)
  }
`;

const GENERATE_PAYSLIP_MUTATION = gql`
  mutation GenerateMyPayslip($startDate: Date!, $endDate: Date!) {
    generateMyPayslip(startDate: $startDate, endDate: $endDate) {
      id periodStart periodEnd totalAmount regularAmount overtimeAmount
      bonusAmount taxAmount insuranceAmount totalRegularHours totalOvertimeHours
      sickDays leaveDays
    }
  }
`;

const createMocks = () => [
  {
    request: { query: GET_USER_PROFILE, variables: { id: undefined } },
    result: {
      data: {
        user: {
          id: 1,
          email: 'test@example.com',
          firstName: 'Test',
          lastName: 'User',
          phoneNumber: '+359888123456',
          address: 'Sofia, Bulgaria',
          egn: '9001011234',
          birthDate: '1990-01-01',
          iban: 'BG1234567890123456',
          jobTitle: 'Developer',
          departmentName: 'IT',
          companyName: 'Chronos',
          createdAt: '2024-01-01',
          qrToken: 'qr-token-123',
          profilePicture: null,
          role: { name: 'user' },
          leaveBalance: { totalDays: 20, usedDays: 5 },
          payrolls: [{ monthlySalary: 2000, hourlyRate: 12, currency: 'BGN' }],
          activeContract: {
            id: 1,
            contractNumber: 'CTR-001',
            contractType: 'full_time',
            startDate: '2024-01-01',
            endDate: null,
            baseSalary: '2000',
            salaryInstallmentsCount: 1,
            monthlyAdvanceAmount: null,
            positionTitle: 'Developer',
            department: { id: 1, name: 'IT' },
          },
        },
        me: { id: 1, role: { name: 'user' } },
      },
    },
  },
  {
    request: { query: CHANGE_PASSWORD_MUTATION, variables: { oldPassword: 'oldpass123', newPassword: 'newpass123' } },
    result: { data: { changePassword: true } },
  },
  {
    request: { query: GENERATE_PAYSLIP_MUTATION, variables: { startDate: '2024-01-01', endDate: '2024-01-31' } },
    result: {
      data: {
        generateMyPayslip: {
          id: 1,
          periodStart: '2024-01-01',
          periodEnd: '2024-01-31',
          totalAmount: '1500.00',
          regularAmount: '1600.00',
          overtimeAmount: '100.00',
          bonusAmount: '50.00',
          taxAmount: '150.00',
          insuranceAmount: '100.00',
          totalRegularHours: '160',
          totalOvertimeHours: '10',
          sickDays: 0,
          leaveDays: 1,
        },
      },
    },
  },
];

const renderProfile = (mocks: unknown[] = createMocks()) => {
  render(
    <MockedProvider mocks={mocks as any} addTypename={true}>
      <BrowserRouter>
        <ProfilePage />
      </BrowserRouter>
    </MockedProvider>
  );
};

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders loading state initially', () => {
    renderProfile();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders user profile header with name and role', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/test user/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/служител/i)).toBeInTheDocument();
    expect(screen.getByText(/it/i)).toBeInTheDocument();
    expect(screen.getByText(/chronos/i)).toBeInTheDocument();
  });

  test('displays personal data tab by default', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/лични данни \(защитени\)/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/test user/i)).toBeInTheDocument();
    expect(screen.getByText(/9001\*\*\*\*/i)).toBeInTheDocument();
  });

  test('displays leave balance', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/оставащ отпуск/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/15 дни/i)).toBeInTheDocument();
    expect(screen.getByText(/от общо 20 за годината/i)).toBeInTheDocument();
  });

  test('displays financial parameters', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/финансови параметри/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/2000 лв\./i)).toBeInTheDocument();
    expect(screen.getByText(/12 лв\./i)).toBeInTheDocument();
  });

  test('displays dashboard settings switches', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/test user/i)).toBeInTheDocument();
    });

    const tabs = screen.getAllByRole('tab');
    await act(async () => {
      await userEvent.click(tabs[3]);
    });

    expect(screen.getByLabelText(/тъмен режим/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/покажи графика с активност/i)).toBeInTheDocument();
  });

  test('displays push notification manager', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/test user/i)).toBeInTheDocument();
    });

    const tabs = screen.getAllByRole('tab');
    await act(async () => {
      await userEvent.click(tabs[3]);
    });

    expect(screen.getByTestId('push-notification-manager')).toBeInTheDocument();
  });

  test('displays QR card in settings tab', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/test user/i)).toBeInTheDocument();
    });

    const tabs = screen.getAllByRole('tab');
    await act(async () => {
      await userEvent.click(tabs[3]);
    });

    expect(screen.getByTestId('my-qr-card')).toBeInTheDocument();
  });

  test('displays employment information', async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/информация за заетостта/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/test@example\.com/i)).toBeInTheDocument();
    expect(screen.getByText(/developer/i)).toBeInTheDocument();
    expect(screen.getByText(/it \/ chronos/i)).toBeInTheDocument();
  });

  test('displays error when query fails', async () => {
    const errorMocks = [{
      request: { query: GET_USER_PROFILE, variables: { id: undefined } },
      error: new Error('Failed to load profile'),
    }];

    renderProfile(errorMocks);

    await waitFor(() => {
      expect(screen.getByText(/failed to load profile/i)).toBeInTheDocument();
    });
  });
});
