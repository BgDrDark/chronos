import React, { useState, useMemo } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { ThemeContext, type DashboardConfig } from './themeContext';

export const AppThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('themeMode') as 'light' | 'dark') || 'light';
  });

  const [dashboardConfig, setDashboardConfig] = useState<DashboardConfig>(() => {
    const saved = localStorage.getItem('dashboardConfig');
    return saved ? JSON.parse(saved) : { showChart: true, showWeeklyTable: true, showFleetCard: true };
  });

  const toggleTheme = () => {
    setMode((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('themeMode', next);
      return next;
    });
  };

  const toggleDashboardWidget = (widget: keyof DashboardConfig) => {
    setDashboardConfig((prev) => {
      const next = { ...prev, [widget]: !prev[widget] };
      localStorage.setItem('dashboardConfig', JSON.stringify(next));
      return next;
    });
  };

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: '#2563eb',
          },
          secondary: {
            main: '#8b5cf6',
          },
          background: {
            default: mode === 'light' ? '#f8fafc' : '#0a0e17',
            paper: mode === 'light' ? '#ffffff' : '#111827',
          },
          divider: mode === 'light' ? '#e2e8f0' : '#1e293b',
        },
        typography: {
          fontSize: 12.8,
          h1: { fontSize: '2rem' },
          h2: { fontSize: '1.6rem' },
          h3: { fontSize: '1.4rem' },
          h4: { fontSize: '1.2rem' },
          h5: { fontSize: '1.1rem' },
          h6: { fontSize: '1rem' },
          button: { fontSize: '0.8rem' },
          body1: { fontSize: '0.8rem' },
          body2: { fontSize: '0.75rem' },
        },
        components: {
          MuiButton: {
            styleOverrides: {
              root: { padding: '4.8px 12.8px' },
              sizeLarge: { padding: '6.4px 17.6px' },
              sizeSmall: { padding: '3.2px 8px' },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                backgroundImage: 'none',
              },
            },
          },
          MuiTextField: { defaultProps: { size: 'small' } },
          MuiSelect: { defaultProps: { size: 'small' } },
          MuiFormControl: { defaultProps: { size: 'small' } },
        },
        spacing: 6.4,
      }),
    [mode]
  );

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme, dashboardConfig, toggleDashboardWidget }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};
