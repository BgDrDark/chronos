import { vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import MyCardPage from '../MyCardPage';

const mockNavigate = vi.fn();
const mockAxiosGet = vi.fn();

vi.mock('axios', () => ({
  default: {
    get: (...args: unknown[]) => mockAxiosGet(...args),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('qrcode.react', () => ({
  QRCodeSVG: ({ value }: { value: string }) => (
    <div data-testid="qr-code" data-value={value}>QR Code: {value}</div>
  ),
}));

const mockGeolocation = {
  getCurrentPosition: vi.fn(),
};

Object.defineProperty(navigator, 'geolocation', {
  value: mockGeolocation,
  writable: true,
});

Object.defineProperty(navigator, 'bluetooth', {
  value: undefined,
  writable: true,
});

Object.defineProperty(navigator, 'wakeLock', {
  value: { request: vi.fn() },
  writable: true,
});

const renderPage = () => {
  render(
    <BrowserRouter>
      <MyCardPage />
    </BrowserRouter>
  );
};

describe('MyCardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (navigator as any).bluetooth = undefined;
    mockGeolocation.getCurrentPosition.mockImplementation((success: (pos: GeolocationPosition) => void) => {
      success({ coords: { latitude: 42.7, longitude: 23.3 } } as GeolocationPosition);
    });
  });

  test('renders page header and loading state', async () => {
    mockAxiosGet.mockImplementation(() => new Promise(() => {}));
    renderPage();
    expect(screen.getByText(/карта за достъп/i)).toBeInTheDocument();
    expect(screen.getByText(/сканирай тук/i)).toBeInTheDocument();
  });

  test('displays QR code when token is received', async () => {
    mockAxiosGet.mockResolvedValueOnce({
      data: { qr_token: 'test-qr-token-123' },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('qr-code')).toBeInTheDocument();
    });
    expect(screen.getByTestId('qr-code')).toHaveAttribute('data-value', 'test-qr-token-123');
  });

  test('displays error when token fetch fails', async () => {
    mockAxiosGet.mockRejectedValueOnce({
      response: { data: { detail: 'Неоторизиран' } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/неоторизиран/i)).toBeInTheDocument();
    });
  });

  test('navigates back when back button is clicked', async () => {
    mockAxiosGet.mockResolvedValueOnce({
      data: { qr_token: 'test-token' },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('qr-code')).toBeInTheDocument();
    });

    const backButton = screen.getAllByRole('button', { name: '' })[0];
    await userEvent.click(backButton);
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  test('refresh button is present and clickable', async () => {
    mockAxiosGet.mockResolvedValueOnce({
      data: { qr_token: 'token-1' },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('qr-code')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button', { name: '' });
    const refreshButton = allButtons[1];
    expect(refreshButton).not.toBeDisabled();
  });

  test('shows bluetooth scan button when bluetooth not available', async () => {
    mockAxiosGet.mockImplementation(() => new Promise(() => {}));

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /сканирай за терминал/i })).toBeInTheDocument();
    });
  });

  test('shows beacon detected message after successful bluetooth scan', async () => {
    mockAxiosGet.mockImplementation(() => new Promise(() => {}));

    const mockRequestDevice = vi.fn().mockResolvedValue({ name: 'Chronos-Terminal-1' });
    (navigator as any).bluetooth = { requestDevice: mockRequestDevice };

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /сканирай за терминал/i })).toBeInTheDocument();
    });

    const scanButton = screen.getByRole('button', { name: /сканирай за терминал/i });
    await act(async () => {
      await userEvent.click(scanButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/терминалът е засечен/i)).toBeInTheDocument();
    });
  });

  test('handles bluetooth scan cancellation gracefully', async () => {
    mockAxiosGet.mockImplementation(() => new Promise(() => {}));

    const mockRequestDevice = vi.fn().mockRejectedValue(new Error('User cancelled'));
    (navigator as any).bluetooth = { requestDevice: mockRequestDevice };

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /сканирай за терминал/i })).toBeInTheDocument();
    });

    const scanButton = screen.getByRole('button', { name: /сканирай за терминал/i });
    await act(async () => {
      await userEvent.click(scanButton);
    });

    // After cancellation, the bluetooth button should reappear (beaconDetected stays false)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /сканирай за терминал/i })).toBeInTheDocument();
    });
  });

  test('shows countdown timer', async () => {
    mockAxiosGet.mockResolvedValueOnce({
      data: { qr_token: 'test-token' },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/сек\./i)).toBeInTheDocument();
    });
  });
});
