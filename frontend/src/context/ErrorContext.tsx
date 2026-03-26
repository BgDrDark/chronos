import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { Snackbar, Alert, AlertColor } from '@mui/material';

interface ErrorContextType {
  showError: (message: string) => void;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
}

const ErrorContext = createContext<ErrorContextType | null>(null);

export const ErrorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: AlertColor;
  }>({ open: false, message: '', severity: 'error' });

  const showError = useCallback((message: string) => {
    setSnackbar({ open: true, message, severity: 'error' });
  }, []);

  const showSuccess = useCallback((message: string) => {
    setSnackbar({ open: true, message, severity: 'success' });
  }, []);

  const showWarning = useCallback((message: string) => {
    setSnackbar({ open: true, message, severity: 'warning' });
  }, []);

  const showInfo = useCallback((message: string) => {
    setSnackbar({ open: true, message, severity: 'info' });
  }, []);

  const handleClose = useCallback(() => {
    setSnackbar(prev => ({ ...prev, open: false }));
  }, []);

  return (
    <ErrorContext.Provider value={{ showError, showSuccess, showWarning, showInfo }}>
      {children}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={6000} 
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleClose} 
          severity={snackbar.severity} 
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </ErrorContext.Provider>
  );
};

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

export const extractErrorMessage = (error: any): string => {
  if (!error) return 'Възникна грешка';
  
  if (typeof error === 'string') return error;
  
  if (error?.graphQLErrors?.[0]?.message) {
    return error.graphQLErrors[0].message;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  if (error?.response?.message) {
    return error.response.message;
  }
  
  return 'Възникна грешка';
};
