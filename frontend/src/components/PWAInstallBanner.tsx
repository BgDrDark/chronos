import React from 'react';
import { usePWAInstall } from '../hooks/usePWAInstall';
import { Snackbar, Alert, Button, Box, Typography, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import InstallMobileIcon from '@mui/icons-material/InstallMobile';

export const PWAInstallBanner: React.FC = () => {
  const { install, dismiss, isInstallable, isInstalled } = usePWAInstall();
  const [open, setOpen] = React.useState(false);
  const [, setVisitCount] = React.useState(0);

  const prevInstallableRef = React.useRef<boolean | null>(null);

  React.useEffect(() => {
    if (isInstalled) return;
    if (!isInstallable) return;
    if (prevInstallableRef.current === isInstallable) return;
    prevInstallableRef.current = isInstallable;

    const visits = parseInt(localStorage.getItem('pwa_visit_count') || '0', 10);
    const newVisits = visits + 1;
    localStorage.setItem('pwa_visit_count', String(newVisits));
    setVisitCount(newVisits);

    const delay = newVisits >= 3 ? 1000 : 10000;
    const timer = setTimeout(() => setOpen(true), delay);
    return () => clearTimeout(timer);
  }, [isInstallable, isInstalled]);

  const handleInstall = async () => {
    const result = await install();
    if (result) setOpen(false);
  };

  const handleDismiss = () => {
    dismiss();
    setOpen(false);
  };

  if (!isInstallable || isInstalled) return null;

  return (
    <Snackbar
      open={open}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      autoHideDuration={null}
      onClose={handleDismiss}
    >
      <Alert
        severity="info"
        variant="filled"
        sx={{ width: '100%', maxWidth: 420 }}
        icon={<InstallMobileIcon />}
        action={
          <IconButton size="small" color="inherit" onClick={handleDismiss}>
            <CloseIcon />
          </IconButton>
        }
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            Инсталирай Chronos
          </Typography>
          <Typography variant="caption">
            Бърз достъп от началния екран. Работи и офлайн.
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
            <Button size="small" variant="contained" color="primary" onClick={handleInstall} sx={{ fontWeight: 'bold' }}>
              Инсталирай
            </Button>
            <Button size="small" color="inherit" onClick={handleDismiss}>
              Не сега
            </Button>
          </Box>
        </Box>
      </Alert>
    </Snackbar>
  );
};
