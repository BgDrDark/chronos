import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App.tsx';
import { ApolloProvider } from '@apollo/client';
import client from './apolloClient';
import { AppThemeProvider } from './ThemeContext';
import { CurrencyProvider } from './CurrencyContext';
// @ts-expect-error - virtual module from vite-plugin-pwa
import { registerSW } from 'virtual:pwa-register';

// Регистрираме Service Worker за автоматично обновяване
if ('serviceWorker' in navigator) {
  registerSW({ 
    immediate: false,
    onNeedRefresh() {
      // Show a prompt to the user to refresh
      if (confirm('Има нова версия на приложението. Искате ли да обновите?')) {
        window.location.reload();
      }
    },
    onRegistered(r: unknown) {
      console.log('SW Registered: ', r);
    },
    onRegisterError(error: unknown) {
      console.error('SW Registration error: ', error);
    }
  });
} else {
  console.warn('Service Workers are not supported in this browser.');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ApolloProvider client={client}>
      <AppThemeProvider>
        <CurrencyProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </CurrencyProvider>
      </AppThemeProvider>
    </ApolloProvider>
  </StrictMode>,
);
