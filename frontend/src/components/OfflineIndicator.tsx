import React from 'react';
import { Chip } from '@mui/material';
import WifiOffIcon from '@mui/icons-material/WifiOff';

export const OfflineIndicator: React.FC = () => {
  const [offline, setOffline] = React.useState(!navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => setOffline(false);
    const handleOffline = () => setOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!offline) return null;

  return (
    <Chip
      icon={<WifiOffIcon />}
      label="Офлайн режим"
      color="warning"
      size="small"
      sx={{
        position: 'fixed',
        bottom: 16,
        left: 16,
        zIndex: 2000,
        fontWeight: 'bold',
        boxShadow: 2,
      }}
    />
  );
};
