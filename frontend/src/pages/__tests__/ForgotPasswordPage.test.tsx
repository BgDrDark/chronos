import { vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ForgotPasswordPage from '../ForgotPasswordPage';

const mockFetch = vi.fn();
(globalThis as unknown as { fetch: typeof mockFetch }).fetch = mockFetch;

vi.mock('../../utils/api', () => ({
  getApiUrl: (path?: string) => `http://localhost:14240${path || ''}`,
}));

const renderPage = () => {
  render(
    <BrowserRouter>
      <ForgotPasswordPage />
    </BrowserRouter>
  );
};

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders forgot password form elements', () => {
    renderPage();
    expect(screen.getByText(/забравена парола/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/имейл адрес/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /изпрати линк/i })).toBeInTheDocument();
    expect(screen.getByText(/върни се към вход/i)).toBeInTheDocument();
  });

  test('displays success message on successful request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    });

    renderPage();
    const emailInput = screen.getByLabelText(/имейл адрес/i);
    const submitButton = screen.getByRole('button', { name: /изпрати линк/i });

    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:14240/auth/forgot-password',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'test@example.com' }),
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/ако имейлът съществува/i)).toBeInTheDocument();
    });
  });

  test('displays error message on failed request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: 'User not found' }),
    });

    renderPage();
    const emailInput = screen.getByLabelText(/имейл адрес/i);
    const submitButton = screen.getByRole('button', { name: /изпрати линк/i });

    await userEvent.type(emailInput, 'nonexistent@example.com');
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/грешка при изпращане/i)).toBeInTheDocument();
    });
  });

  test('button is disabled while loading', async () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    renderPage();
    const emailInput = screen.getByLabelText(/имейл адрес/i);
    const submitButton = screen.getByRole('button', { name: /изпрати линк/i });

    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  test('links back to login page', () => {
    renderPage();
    const loginLink = screen.getByRole('link', { name: /върни се към вход/i });
    expect(loginLink).toHaveAttribute('href', '/login');
  });
});
