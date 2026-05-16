import { vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { MockedProvider } from '@apollo/client/testing';
import LeavesPage from '../LeavesPage';

vi.mock('../components/ui/InfoIcon', () => ({
  InfoIcon: () => <span data-testid="info-icon">?</span>,
}));

const GET_MY_LEAVES = expect.any(Object);
const GET_PENDING_LEAVES = expect.any(Object);
const GET_ALL_LEAVES = expect.any(Object);
const GET_MY_BALANCE = expect.any(Object);
const REQUEST_LEAVE_MUTATION = expect.any(Object);
const APPROVE_LEAVE_MUTATION = expect.any(Object);
const REJECT_LEAVE_MUTATION = expect.any(Object);
const CANCEL_LEAVE_MUTATION = expect.any(Object);
const UPDATE_LEAVE_MUTATION = expect.any(Object);

const createMocks = (tab: string = 'my-requests') => {
  const baseMocks = [
    {
      request: { query: GET_MY_LEAVES },
      result: {
        data: {
          myLeaveRequests: [
            {
              id: 1,
              startDate: '2024-01-15',
              endDate: '2024-01-17',
              leaveType: 'paid_leave',
              reason: 'Family vacation',
              status: 'pending',
              createdAt: '2024-01-10',
              adminComment: null,
              user: { id: 1, email: 'test@example.com', firstName: 'Test', lastName: 'User' },
            },
            {
              id: 2,
              startDate: '2024-02-01',
              endDate: '2024-02-02',
              leaveType: 'sick_leave',
              reason: 'Flu',
              status: 'approved',
              createdAt: '2024-01-25',
              adminComment: 'Get well soon',
              user: { id: 1, email: 'test@example.com', firstName: 'Test', lastName: 'User' },
            },
          ],
          me: { id: 1, role: { name: tab === 'my-requests' ? 'user' : 'admin' } },
        },
      },
    },
    {
      request: { query: GET_MY_BALANCE, variables: { userId: 1, year: expect.any(Number) } },
      result: {
        data: {
          leaveBalance: { totalDays: 20, usedDays: 5 },
        },
      },
    },
  ];

  if (tab === 'approvals') {
    baseMocks.push({
      request: { query: GET_PENDING_LEAVES },
      result: {
        data: {
          pendingLeaveRequests: [
            {
              id: 3,
              startDate: '2024-03-01',
              endDate: '2024-03-05',
              leaveType: 'paid_leave',
              reason: 'Vacation',
              createdAt: '2024-02-20',
              user: { id: 2, email: 'john@example.com', firstName: 'John', lastName: 'Doe' },
            },
            {
              id: 4,
              startDate: '2024-03-10',
              endDate: '2024-03-12',
              leaveType: 'sick_leave',
              reason: 'Medical',
              createdAt: '2024-02-25',
              user: { id: 3, email: 'jane@example.com', firstName: 'Jane', lastName: 'Smith' },
            },
          ],
        },
      },
    });
  }

  if (tab === 'all') {
    baseMocks.push({
      request: { query: GET_ALL_LEAVES, variables: { status: null } },
      result: {
        data: {
          allLeaveRequests: [
            {
              id: 1,
              startDate: '2024-01-15',
              endDate: '2024-01-17',
              leaveType: 'paid_leave',
              reason: 'Vacation',
              status: 'pending',
              createdAt: '2024-01-10',
              adminComment: null,
              user: {
                email: 'test@example.com',
                firstName: 'Test',
                lastName: 'User',
                leaveBalance: { totalDays: 20, usedDays: 5 },
              },
            },
            {
              id: 2,
              startDate: '2024-02-01',
              endDate: '2024-02-02',
              leaveType: 'sick_leave',
              reason: 'Flu',
              status: 'approved',
              createdAt: '2024-01-25',
              adminComment: null,
              user: {
                email: 'john@example.com',
                firstName: 'John',
                lastName: 'Doe',
                leaveBalance: { totalDays: 20, usedDays: 10 },
              },
            },
          ],
        },
      },
    });
  }

  baseMocks.push(
    {
      request: { query: REQUEST_LEAVE_MUTATION, variables: expect.any(Object) },
      result: { data: { requestLeave: { id: 5, status: 'pending' } } },
    },
    {
      request: { query: APPROVE_LEAVE_MUTATION, variables: expect.any(Object) },
      result: { data: { approveLeave: { id: 3, status: 'approved' } } },
    },
    {
      request: { query: REJECT_LEAVE_MUTATION, variables: expect.any(Object) },
      result: { data: { rejectLeave: { id: 3, status: 'rejected' } } },
    },
    {
      request: { query: CANCEL_LEAVE_MUTATION, variables: expect.any(Object) },
      result: { data: { cancelLeaveRequest: { id: 1, status: 'cancelled' } } },
    },
    {
      request: { query: UPDATE_LEAVE_MUTATION, variables: expect.any(Object) },
      result: { data: { updateLeaveRequest: { id: 1, status: 'pending' } } },
    }
  );

  return baseMocks;
};

const renderLeaves = (tab: string = 'my-requests', mocks: unknown[] = createMocks(tab)) => {
  render(
    <MockedProvider mocks={mocks as any} addTypename={false}>
      <BrowserRouter>
        <LeavesPage tab={tab} />
      </BrowserRouter>
    </MockedProvider>
  );
};

describe('LeavesPage - My Requests Tab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders loading state initially', () => {
    renderLeaves('my-requests');
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays leave requests', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/платен отпуск/i)).toBeInTheDocument();
    expect(screen.getByText(/болничен/i)).toBeInTheDocument();
  });

  test('displays leave balance', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/баланс за/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/15 дни остават/i)).toBeInTheDocument();
  });

  test('shows status chips for requests', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/чакащ/i)).toBeInTheDocument();
    expect(screen.getByText(/одобрен/i)).toBeInTheDocument();
  });

  test('opens new request dialog', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /нова заявка/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/заявка за отпуск/i)).toBeInTheDocument();
    });
  });

  test('creates new leave request', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /нова заявка/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/заявка за отпуск/i)).toBeInTheDocument();
    });

    const startDateInput = screen.getByLabelText(/от дата/i);
    const endDateInput = screen.getByLabelText(/до дата/i);
    const sendButton = screen.getByRole('button', { name: /изпрати/i });

    await act(async () => {
      await userEvent.type(startDateInput, '2024-04-01');
      await userEvent.type(endDateInput, '2024-04-05');
      await userEvent.click(sendButton);
    });

    await waitFor(() => {
      expect(screen.queryByText(/заявка за отпуск/i)).not.toBeInTheDocument();
    });
  });

  test('shows validation error when required fields are missing', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /нова заявка/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/заявка за отпуск/i)).toBeInTheDocument();
    });

    const sendButton = screen.getByRole('button', { name: /изпрати/i });
    await act(async () => {
      await userEvent.click(sendButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/моля, попълнете задължителните полета/i)).toBeInTheDocument();
    });
  });

  test('displays edit and delete buttons for pending requests', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByTitle(/редактирай/i)).toBeInTheDocument();
    expect(screen.getByTitle(/прекрати\/изтрий/i)).toBeInTheDocument();
  });

  test('displays PDF download button for approved requests', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /молба pdf/i })).toBeInTheDocument();
  });

  test('displays admin comment for approved requests', async () => {
    renderLeaves('my-requests');

    await waitFor(() => {
      expect(screen.getByText(/моите заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/get well soon/i)).toBeInTheDocument();
  });

  test('shows empty state when no requests exist', async () => {
    const emptyMocks = createMocks('my-requests').map(mock => {
      if (mock.request.query === GET_MY_LEAVES) {
        return {
          ...mock,
          result: {
            data: {
              myLeaveRequests: [],
              me: { id: 1, role: { name: 'user' } },
            },
          },
        };
      }
      return mock;
    });

    renderLeaves('my-requests', emptyMocks);

    await waitFor(() => {
      expect(screen.getByText(/няма подадени заявки/i)).toBeInTheDocument();
    });
  });

  test('displays error when query fails', async () => {
    const errorMocks = [{
      request: { query: GET_MY_LEAVES },
      error: new Error('Failed to load leaves'),
    }];

    renderLeaves('my-requests', errorMocks);

    await waitFor(() => {
      expect(screen.getByText(/грешка при зареждане/i)).toBeInTheDocument();
    });
  });
});

describe('LeavesPage - Approvals Tab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('displays pending leave requests', async () => {
    renderLeaves('approvals');

    await waitFor(() => {
      expect(screen.getByText(/чакащи заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/john doe/i)).toBeInTheDocument();
    expect(screen.getByText(/jane smith/i)).toBeInTheDocument();
  });

  test('shows approve and reject buttons', async () => {
    renderLeaves('approvals');

    await waitFor(() => {
      expect(screen.getByText(/чакащи заявки/i)).toBeInTheDocument();
    });

    expect(screen.getAllByRole('button', { name: /одобри/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /отхвърли/i }).length).toBeGreaterThan(0);
  });

  test('approves a leave request', async () => {
    window.confirm = vi.fn().mockReturnValue(true);

    renderLeaves('approvals');

    await waitFor(() => {
      expect(screen.getByText(/чакащи заявки/i)).toBeInTheDocument();
    });

    const approveButtons = screen.getAllByRole('button', { name: /одобри/i });
    await act(async () => {
      await userEvent.click(approveButtons[0]);
    });

    expect(window.confirm).toHaveBeenCalled();
  });

  test('rejects a leave request', async () => {
    window.confirm = vi.fn().mockReturnValue(true);

    renderLeaves('approvals');

    await waitFor(() => {
      expect(screen.getByText(/чакащи заявки/i)).toBeInTheDocument();
    });

    const rejectButtons = screen.getAllByRole('button', { name: /отхвърли/i });
    await act(async () => {
      await userEvent.click(rejectButtons[0]);
    });

    expect(window.confirm).toHaveBeenCalled();
  });

  test('shows employer top-up checkbox for sick leave', async () => {
    renderLeaves('approvals');

    await waitFor(() => {
      expect(screen.getByText(/чакащи заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/работодателят доплаща до 100% от заплатата/i)).toBeInTheDocument();
  });

  test('displays admin comment field', async () => {
    renderLeaves('approvals');

    await waitFor(() => {
      expect(screen.getByText(/чакащи заявки/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/коментар от администратор/i)).toBeInTheDocument();
  });

  test('shows empty state when no pending requests', async () => {
    const emptyMocks = createMocks('approvals').map(mock => {
      if (mock.request.query === GET_PENDING_LEAVES) {
        return {
          ...mock,
          result: {
            data: {
              pendingLeaveRequests: [],
            },
          },
        };
      }
      return mock;
    });

    renderLeaves('approvals', emptyMocks);

    await waitFor(() => {
      expect(screen.getByText(/няма чакащи заявки/i)).toBeInTheDocument();
    });
  });
});

describe('LeavesPage - All Leaves Tab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('displays all leave requests in table', async () => {
    renderLeaves('all');

    await waitFor(() => {
      expect(screen.getByText(/служител/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/test user/i)).toBeInTheDocument();
    expect(screen.getByText(/john doe/i)).toBeInTheDocument();
  });

  test('displays status filter chips', async () => {
    renderLeaves('all');

    await waitFor(() => {
      expect(screen.getByText(/служител/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/всички/i)).toBeInTheDocument();
    expect(screen.getByText(/чакащи/i)).toBeInTheDocument();
    expect(screen.getByText(/одобрени/i)).toBeInTheDocument();
    expect(screen.getByText(/отхвърлени/i)).toBeInTheDocument();
  });

  test('filters by status when chip is clicked', async () => {
    renderLeaves('all');

    await waitFor(() => {
      expect(screen.getByText(/служител/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByText(/чакащи/i));
    });

    expect(screen.getByText(/чакащи/i).closest('[role="button"]')).toHaveClass('MuiChip-filled');
  });

  test('displays leave type for each request', async () => {
    renderLeaves('all');

    await waitFor(() => {
      expect(screen.getByText(/служител/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/платен/i)).toBeInTheDocument();
    expect(screen.getByText(/болничен/i)).toBeInTheDocument();
  });

  test('displays remaining days for each user', async () => {
    renderLeaves('all');

    await waitFor(() => {
      expect(screen.getByText(/служител/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/15/i)).toBeInTheDocument();
    expect(screen.getByText(/10/i)).toBeInTheDocument();
  });

  test('shows terminate button for approved and pending requests', async () => {
    renderLeaves('all');

    await waitFor(() => {
      expect(screen.getByText(/служител/i)).toBeInTheDocument();
    });

    expect(screen.getAllByTitle(/прекрати \/ отмени/i).length).toBeGreaterThan(0);
  });
});
