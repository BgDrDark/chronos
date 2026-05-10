import { startRegistration, startAuthentication } from '@simplewebauthn/browser';
import axios from 'axios';
import { getApiUrl } from '../utils/api';

const API_URL = getApiUrl();

export const biometricService = {
  async registerBiometrics(friendlyName: string = "Моят телефон") {
    try {
      const { data: options } = await axios.post(`${API_URL}/webauthn/register/options`, {}, {
        withCredentials: true,
      });

      const regResponse = await startRegistration(options);

      const { data: verification } = await axios.post(`${API_URL}/webauthn/register/verify`, {
        ...regResponse,
        friendly_name: friendlyName
      }, {
        withCredentials: true,
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
      
      const { data: options } = await axios.post(getApiUrl('webauthn/login/options'), { email });
      console.log('Received options:', options);

      const authResponse = await startAuthentication(options);

      const { data: result } = await axios.post(`${API_URL}/webauthn/login/verify`, authResponse, {
        withCredentials: true,
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
