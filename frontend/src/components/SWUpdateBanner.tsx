import React from 'react';
import { Snackbar, Alert, Button, Box, Typography } from '@mui/material';
import SystemUpdateIcon from '@mui/icons-material/SystemUpdate';
import { useSWUpdate } from '../hooks/useSWUpdate';

export const SWUpdateBanner: React.FC = () => {
  const { needRefresh, offlineReady, update, dismiss } = useSWUpdate();

  if (!needRefresh && !offlineReady) return null;

  return (
    <Snackbar
      open={true}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert
        severity={needRefresh ? 'info' : 'success'}
        variant="filled"
        sx={{ width: '100%', maxWidth: 450 }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SystemUpdateIcon />
          <Typography variant="body2" sx={{ flexGrow: 1 }}>
            {needRefresh
              ? 'Нова версия на Chronos е налична.'
              : 'Приложението е готово за офлайн работа.'}
          </Typography>
          {needRefresh && (
            <Button size="small" color="inherit" onClick={update} sx={{ fontWeight: 'bold' }}>
              Обнови
            </Button>
          )}
          <Button size="small" color="inherit" onClick={dismiss}>
            {needRefresh ? 'По-късно' : 'OK'}
          </Button>
        </Box>
      </Alert>
    </Snackbar>
  );
};
