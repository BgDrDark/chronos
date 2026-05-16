import React from 'react';
import { usePWAInstall } from '../hooks/usePWAInstall';
import { Snackbar, Alert, Button, Box, Typography, IconButton } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import CloseIcon from '@mui/icons-material/Close';

export const PWAInstallBanner: React.FC = () => {
  const { install, isInstallable, isInstalled } = usePWAInstall();
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    if (isInstallable && !isInstalled) {
      const timer = setTimeout(() => setOpen(true), 3000);
      return () => clearTimeout(timer);
    }
  }, [isInstallable, isInstalled]);

  const handleInstall = async () => {
    await install();
    setOpen(false);
  };

  if (!isInstallable || isInstalled) return null;

  return (
    <Snackbar
      open={open}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      autoHideDuration={30000}
      onClose={() => setOpen(false)}
    >
      <Alert
        severity="info"
        variant="filled"
        sx={{ width: '100%', maxWidth: 400 }}
        action={
          <IconButton size="small" color="inherit" onClick={() => setOpen(false)}>
            <CloseIcon />
          </IconButton>
        }
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DownloadIcon />
          <Typography variant="body2" sx={{ flexGrow: 1 }}>
            Инсталирай Chronos за бърз достъп
          </Typography>
          <Button size="small" color="inherit" onClick={handleInstall} sx={{ fontWeight: 'bold' }}>
            Инсталирай
          </Button>
        </Box>
      </Alert>
    </Snackbar>
  );
};
