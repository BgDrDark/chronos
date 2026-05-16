import React from 'react';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { Alert, Box, Typography } from '@mui/material';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import WifiIcon from '@mui/icons-material/Wifi';

export const NetworkStatusBanner: React.FC = () => {
  const { isOnline } = useNetworkStatus();

  if (isOnline) return null;

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
