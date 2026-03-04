import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, useNavigate } from 'react-router-dom';
import LoginPage from '../LoginPage';

// Mock ApolloProvider and useApolloClient from @apollo/client
const mockResetStore = jest.fn().mockResolvedValue(undefined);
const mockUseApolloClient = jest.fn(() => ({
  resetStore: mockResetStore,
}));

// We need to mock ApolloProvider separately because it's a component
// and jest.mock can't mock components directly in the same way as functions/hooks
jest.mock('@apollo/client', () => {
  const actualApolloClient = jest.requireActual('@apollo/client');
  return {
    ...actualApolloClient,
    ApolloProvider: ({ children }: any) => children, // Simply render children
    useApolloClient: () => mockUseApolloClient(),
  };
});

// Mock useNavigate
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

// Mock the fetch API
const mockFetch = jest.fn();
(globalThis as any).fetch = mockFetch;

const renderLoginPage = () => {
  render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form elements', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('displays validation errors for invalid email', async () => {
    renderLoginPage();
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(emailInput, 'invalid-email');
    await userEvent.type(passwordInput, 'password123'); // Valid password length
    await userEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
    });
    expect(mockFetch).not.toHaveBeenCalled();
  });

  test('displays validation errors for short password', async () => {
    renderLoginPage();
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'short');
    await userEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByText(/password must be at least 8 characters long/i)).toBeInTheDocument();
    });
    expect(mockFetch).not.toHaveBeenCalled();
  });

  test('calls fetch and navigates on successful login', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ access_token: 'fake-token' }),
    });
    const mockNavigate = jest.fn();
    (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
    mockUseApolloClient.mockReturnValue({
      resetStore: mockResetStore,
    });


    renderLoginPage();
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(signInButton);

    await waitFor(() => {
      // The component sends a URLSearchParams object. We need to assert that.
      // JSDOM's fetch might not fully serialize it before Jest intercepts.
      const expectedBody = new URLSearchParams({
        username: 'test@example.com',
        password: 'password123',
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:14240/auth/token',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          // Assert that the body is an instance of URLSearchParams, and then compare its string representation
          body: expect.any(URLSearchParams),
        })
      );
      // Further assert the string content of the URLSearchParams object
      const call = mockFetch.mock.calls[0];
      const receivedBody = call[1].body; // Get the URLSearchParams instance
      expect(receivedBody.toString()).toEqual(expectedBody.toString());
    });

    await waitFor(() => expect(mockResetStore).toHaveBeenCalled());
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  test('displays API error on failed login', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: 'Invalid credentials' }),
    });

    renderLoginPage();
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    await userEvent.type(emailInput, 'wrong@example.com');
    await userEvent.type(passwordInput, 'wrongpassword');
    await userEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid credentials/i);
    });
    expect(mockFetch).toHaveBeenCalled();
  });
});
