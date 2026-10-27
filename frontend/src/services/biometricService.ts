import { startRegistration, startAuthentication } from '@simplewebauthn/browser';
import axios from 'axios';
import { getApiUrl } from '../utils/api';
import { getCsrfToken } from '../utils/csrf';

const API_URL = getApiUrl();

// The WebAuthn endpoints are not CSRF-exempt, so every POST needs the
// double-submit header. On a fresh browser the cookie may not exist yet.
const csrfHeaders = async (): Promise<Record<string, string>> => {
  let token = getCsrfToken();
  // Two attempts: the first call is what makes the backend issue the cookie.
  for (let attempt = 0; attempt < 2 && !token; attempt++) {
    try {
      const response = await axios.get(`${API_URL}/auth/csrf-token`, { withCredentials: true });
      token = response.data?.csrf_token ?? null;
    } catch {
      token = null;
    }
  }
  return token ? { 'X-CSRFToken': token } : {};
};

export const biometricService = {
  async registerBiometrics(friendlyName: string = "Моят телефон") {
    try {
      const { data: options } = await axios.post(`${API_URL}/webauthn/register/options`, {}, {
        withCredentials: true,
        headers: await csrfHeaders(),
      });

      const regResponse = await startRegistration(options);

      const { data: verification } = await axios.post(`${API_URL}/webauthn/register/verify`, {
        ...regResponse,
        friendly_name: friendlyName
      }, {
        withCredentials: true,
        headers: await csrfHeaders(),
      });

      return verification;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      console.error('Biometric registration failed:', error);
      throw new Error(err.response?.data?.detail || err.message || 'Registration failed');
    }
  },

  async loginWithBiometrics(email?: string) {
    try {
      console.log('Biometric login - API URL:', getApiUrl('webauthn/login/options'));
      
      const { data: options } = await axios.post(
        getApiUrl('webauthn/login/options'),
        { email },
        { withCredentials: true, headers: await csrfHeaders() },
      );
      console.log('Received options:', options);

      const authResponse = await startAuthentication(options);

      const { data: result } = await axios.post(`${API_URL}/webauthn/login/verify`, authResponse, {
        withCredentials: true,
        headers: await csrfHeaders(),
      });

      return result;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      console.error('Biometric login failed:', error);
      const errorMessage = err.response?.data?.detail || err.message || 'Login failed';
      console.log('Error details:', err.response?.data);
      throw new Error(errorMessage);
    }
  }
};
