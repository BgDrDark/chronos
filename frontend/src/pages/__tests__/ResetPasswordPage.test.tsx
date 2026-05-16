import { vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, useNavigate, useSearchParams } from 'react-router-dom';
import ResetPasswordPage from '../ResetPasswordPage';

const mockFetch = vi.fn();
(globalThis as unknown as { fetch: typeof mockFetch }).fetch = mockFetch;

vi.mock('../../utils/api', () => ({
  getApiUrl: (path?: string) => `http://localhost:14240${path || ''}`,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(),
    useSearchParams: vi.fn(),
  };
});

const mockNavigate = vi.fn();

const setupSearchParams = (token: string | null) => {
  (useSearchParams as jest.Mock).mockReturnValue([
    { get: (key: string) => (key === 'token' ? token : null) },
  ]);
  (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
};

const renderPage = (token: string | null = 'valid-token-123') => {
  setupSearchParams(token);
  render(
    <BrowserRouter>
      <ResetPasswordPage />
    </BrowserRouter>
  );
};

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('when no token is provided', () => {
    test('shows error about missing token', () => {
      renderPage(null);
      expect(screen.getByText(/липсва валиден токен/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /към вход/i })).toBeInTheDocument();
    });

    test('navigates to login when clicking button', async () => {
      renderPage(null);
      const loginButton = screen.getByRole('button', { name: /към вход/i });
      await userEvent.click(loginButton);
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('when token is provided', () => {
    test('shows verification loading state initially', () => {
      renderPage('valid-token');
      expect(screen.getByText(/проверка на линка/i)).toBeInTheDocument();
    });

    test('verifies token and shows password form on success', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      renderPage('valid-token');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /нова парола/i })).toBeInTheDocument();
        expect(screen.getByLabelText(/нова парола/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/потвърди парола/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /смени паролата/i })).toBeInTheDocument();
      });
    });

    test('shows error when token verification fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Невалиден или изтекъл линк.' }),
      });

      renderPage('invalid-token');

      await waitFor(() => {
        expect(screen.getByText(/невалиден или изтекъл линк/i)).toBeInTheDocument();
      });
    });

    test('changes password successfully', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ message: 'Password changed' }),
        });

      renderPage('valid-token');

      await waitFor(() => {
        expect(screen.getByLabelText(/нова парола/i)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(/нова парола/i);
      const confirmInput = screen.getByLabelText(/потвърди парола/i);
      const submitButton = screen.getByRole('button', { name: /смени паролата/i });

      await userEvent.type(passwordInput, 'newpassword123');
      await userEvent.type(confirmInput, 'newpassword123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:14240/auth/reset-password',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              token: 'valid-token',
              new_password: 'newpassword123',
            }),
          })
        );
      });

      await waitFor(() => {
        expect(screen.getByText(/паролата е променена успешно/i)).toBeInTheDocument();
      });
    });

    test('shows error when passwords do not match', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      renderPage('valid-token');

      await waitFor(() => {
        expect(screen.getByLabelText(/нова парола/i)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(/нова парола/i);
      const confirmInput = screen.getByLabelText(/потвърди парола/i);
      const submitButton = screen.getByRole('button', { name: /смени паролата/i });

      await userEvent.type(passwordInput, 'password123');
      await userEvent.type(confirmInput, 'different123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/паролите не съвпадат/i)).toBeInTheDocument();
      });
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    test('shows error when password is too short', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      renderPage('valid-token');

      await waitFor(() => {
        expect(screen.getByLabelText(/нова парола/i)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(/нова парола/i);
      const confirmInput = screen.getByLabelText(/потвърди парола/i);
      const submitButton = screen.getByRole('button', { name: /смени паролата/i });

      await userEvent.type(passwordInput, 'short');
      await userEvent.type(confirmInput, 'short');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/поне 8 символа/i)).toBeInTheDocument();
      });
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    test('shows error when password reset API fails', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true })
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ detail: 'Token expired' }),
        });

      renderPage('valid-token');

      await waitFor(() => {
        expect(screen.getByLabelText(/нова парола/i)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(/нова парола/i);
      const confirmInput = screen.getByLabelText(/потвърди парола/i);
      const submitButton = screen.getByRole('button', { name: /смени паролата/i });

      await userEvent.type(passwordInput, 'newpassword123');
      await userEvent.type(confirmInput, 'newpassword123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/token expired/i)).toBeInTheDocument();
      });
    });

    test('button is disabled while loading', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true })
        .mockImplementation(() => new Promise(() => {}));

      renderPage('valid-token');

      await waitFor(() => {
        expect(screen.getByLabelText(/нова парола/i)).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(/нова парола/i);
      const confirmInput = screen.getByLabelText(/потвърди парола/i);
      const submitButton = screen.getByRole('button', { name: /смени паролата/i });

      await userEvent.type(passwordInput, 'newpassword123');
      await userEvent.type(confirmInput, 'newpassword123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });
  });
});
