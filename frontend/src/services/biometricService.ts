import { startRegistration, startAuthentication } from '@simplewebauthn/browser';
import axios from 'axios';
import { getApiUrl } from '../utils/api';

const API_URL = getApiUrl();

export const biometricService = {
  /**
   * Регистрира нова биометрия за текущия потребител
   */
  async registerBiometrics(friendlyName: string = "Моят телефон") {
    try {
      const token = localStorage.getItem('token');
      
      // 1. Вземане на опции от сървъра
      const { data: options } = await axios.post(`${API_URL}/webauthn/register/options`, {}, {
        withCredentials: true,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });

      // 2. Извикване на биометричния скенер на браузъра
      const regResponse = await startRegistration(options);

      // 3. Верификация на резултата в бекенда
      const { data: verification } = await axios.post(`${API_URL}/webauthn/register/verify`, {
        ...regResponse,
        friendly_name: friendlyName
      }, {
        withCredentials: true,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });

      return verification;
    } catch (error: any) {
      console.error('Biometric registration failed:', error);
      throw new Error(error.response?.data?.detail || error.message || 'Registration failed');
    }
  },

  /**
   * Вход в системата чрез биометрия
   */
  async loginWithBiometrics(email?: string) {
    try {
      console.log('Biometric login - API URL:', getApiUrl('webauthn/login/options'));
      
      // 1. Вземане на опции за вход
      const { data: options } = await axios.post(getApiUrl('webauthn/login/options'), { email });
      console.log('Received options:', options);

      // 2. Извикване на биометричния скенер за подпис
      const authResponse = await startAuthentication(options);

      // 3. Верификация на подписа в бекенда
      const { data: result } = await axios.post(`${API_URL}/webauthn/login/verify`, authResponse);

      // Записване на токена (както при нормален вход)
      if (result.access_token) {
        localStorage.setItem('token', result.access_token);
      }

      return result;
    } catch (error: any) {
      console.error('Biometric login failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      console.log('Error details:', error.response?.data);
      throw new Error(errorMessage);
    }
  }
};
