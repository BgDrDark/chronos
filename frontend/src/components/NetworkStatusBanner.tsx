import React from 'react';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { useBackgroundSync } from '../hooks/useBackgroundSync';
import { Alert, Box, Typography } from '@mui/material';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import SyncIcon from '@mui/icons-material/Sync';

export const NetworkStatusBanner: React.FC = () => {
  const { isOnline } = useNetworkStatus();
  const { pendingCount } = useBackgroundSync();

  if (isOnline) {
    if (pendingCount > 0) {
      return (
        <Alert
          severity="warning"
          variant="filled"
          sx={{ borderRadius: 0, position: 'sticky', top: 0, zIndex: 9999 }}
          icon={<SyncIcon />}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2">
              {pendingCount} записа чакат синхронизация
            </Typography>
          </Box>
        </Alert>
      );
    }
    return null;
  }

  return (
    <Alert
      severity="error"
      variant="filled"
      sx={{ borderRadius: 0, position: 'sticky', top: 0, zIndex: 9999 }}
      icon={<WifiOffIcon />}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="body2">
          Няма интернет връзка. Някои функции може да не работят.
        </Typography>
      </Box>
    </Alert>
  );
};
