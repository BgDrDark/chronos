import { vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { MockedProvider } from '@apollo/client/testing';
import { gql } from '@apollo/client';
import MySchedulePage from '../MySchedulePage';

vi.mock('@fullcalendar/react', () => ({
  default: ({ dateClick, eventClick, events }: any) => (
    <div data-testid="calendar">
      <div data-testid="calendar-events">{events?.length || 0} events</div>
      <button data-testid="date-click" onClick={() => dateClick?.({ dateStr: '2024-01-15' })}>
        Click Date
      </button>
      <button
        data-testid="event-click"
        onClick={() => eventClick?.({
          event: {
            startStr: '2024-01-15',
            title: 'Дневна смяна',
            extendedProps: { shiftType: 'regular', shiftName: 'Дневна смяна', startTime: '08:00', endTime: '16:00' }
          }
        })}
      >
        Click Event
      </button>
    </div>
  ),
}));

vi.mock('../components/ShiftLegend', () => ({
  default: () => <div data-testid="shift-legend">Shift Legend</div>,
}));

vi.mock('../components/ShiftEventContent', () => ({
  default: () => <div data-testid="shift-event-content">Event Content</div>,
}));

const GET_MY_SCHEDULES_QUERY = gql`
  query GetMySchedules($startDate: Date!, $endDate: Date!) {
    mySchedules(startDate: $startDate, endDate: $endDate) {
      id date shift { id name startTime endTime shiftType }
    }
  }
`;

const GET_PUBLIC_HOLIDAYS_QUERY = gql`
  query GetPublicHolidays($year: Int) {
    publicHolidays(year: $year) { id date name localName }
  }
`;

const GET_ORTHODOX_HOLIDAYS_QUERY = gql`
  query GetOrthodoxHolidays($year: Int) {
    orthodoxHolidays(year: $year) { id date name localName }
  }
`;

const REQUEST_LEAVE_MUTATION = gql`
  mutation RequestLeave($startDate: Date!, $endDate: Date!, $leaveType: String!, $reason: String) {
    requestLeave(leaveInput: {startDate: $startDate, endDate: $endDate, leaveType: $leaveType, reason: $reason}) {
      id status
    }
  }
`;

const createMocks = () => {
  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
  const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];

  return [
    {
      request: { query: GET_MY_SCHEDULES_QUERY, variables: { startDate: startOfMonth, endDate: endOfMonth } },
      result: {
        data: {
          mySchedules: [
            {
              id: 1,
              date: '2024-01-15',
              shift: { id: 1, name: 'Дневна смяна', startTime: '08:00:00', endTime: '16:00:00', shiftType: 'regular' },
            },
            {
              id: 2,
              date: '2024-01-16',
              shift: { id: 2, name: 'Нощна смяна', startTime: '22:00:00', endTime: '06:00:00', shiftType: 'night' },
            },
          ],
        },
      },
    },
    {
      request: { query: GET_PUBLIC_HOLIDAYS_QUERY, variables: { year: today.getFullYear() } },
      result: {
        data: {
          publicHolidays: [
            { id: 1, date: '2024-01-01', name: 'New Year', localName: 'Нова година' },
          ],
        },
      },
    },
    {
      request: { query: GET_ORTHODOX_HOLIDAYS_QUERY, variables: { year: today.getFullYear() } },
      result: {
        data: { orthodoxHolidays: [] },
      },
    },
    {
      request: { query: REQUEST_LEAVE_MUTATION, variables: expect.any(Object) },
      result: {
        data: { requestLeave: { id: 1, status: 'pending' } },
      },
    },
  ];
};

const renderMySchedule = (mocks: unknown[] = createMocks()) => {
  render(
    <MockedProvider mocks={mocks as any} addTypename={true}>
      <BrowserRouter>
        <MySchedulePage />
      </BrowserRouter>
    </MockedProvider>
  );
};

describe('MySchedulePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders loading state initially', () => {
    renderMySchedule();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders calendar with schedule data', async () => {
    renderMySchedule();

    await waitFor(() => {
      expect(screen.getByText(/моят график/i)).toBeInTheDocument();
    });

    expect(screen.getByTestId('calendar')).toBeInTheDocument();
    expect(screen.getByTestId('shift-legend')).toBeInTheDocument();
  });

  test('displays number of events in calendar', async () => {
    renderMySchedule();

    await waitFor(() => {
      expect(screen.getByText(/моят график/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/2 events/i)).toBeInTheDocument();
  });

  test('opens details dialog when date is clicked', async () => {
    renderMySchedule();

    await waitFor(() => {
      expect(screen.getByText(/моят график/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByTestId('date-click'));
    });

    await waitFor(() => {
      expect(screen.getByText(/преглед на деня/i)).toBeInTheDocument();
    });
  });

  test('shows leave request buttons in details dialog', async () => {
    renderMySchedule();

    await waitFor(() => {
      expect(screen.getByText(/моят график/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByTestId('date-click'));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /заяви платен отпуск/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /заяви болничен/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /заяви неплатен отпуск/i })).toBeInTheDocument();
    });
  });

  test('closes details dialog when close button is clicked', async () => {
    renderMySchedule();

    await waitFor(() => {
      expect(screen.getByText(/моят график/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByTestId('date-click'));
    });

    await waitFor(() => {
      expect(screen.getByText(/преглед на деня/i)).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /затвори/i }));
    });

    await waitFor(() => {
      expect(screen.queryByText(/преглед на деня/i)).not.toBeInTheDocument();
    });
  });

  test('displays error when query fails', async () => {
    const today = new Date();
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];

    const errorMocks = [{
      request: { query: GET_MY_SCHEDULES_QUERY, variables: { startDate: startOfMonth, endDate: endOfMonth } },
      error: new Error('Failed to load schedule'),
    }];

    renderMySchedule(errorMocks);

    await waitFor(() => {
      expect(screen.getByText(/грешка/i)).toBeInTheDocument();
    });
  });
});
