import React, { useState, useEffect } from 'react';
import { Snackbar, Alert, Button, Box, Typography } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

const DISMISS_KEY = 'pwa-install-dismissed';
const VISIT_KEY = 'pwa-install-visits';
const DISMISS_DAYS = 7;
const MIN_VISITS = 2;

export const PWAInstallBanner: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showBanner, setShowBanner] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
      return;
    }

    // Track visits
    try {
      const visits = parseInt(localStorage.getItem(VISIT_KEY) || '0', 10);
      localStorage.setItem(VISIT_KEY, String(visits + 1));
    } catch { /* ignore */ }

    // Check if dismissed
    try {
      const dismissed = localStorage.getItem(DISMISS_KEY);
      if (dismissed) {
        const dismissedTime = parseInt(dismissed, 10);
        if (Date.now() - dismissedTime < DISMISS_DAYS * 24 * 60 * 60 * 1000) {
          return; // Still within dismiss period
        }
        localStorage.removeItem(DISMISS_KEY);
      }
    } catch { /* ignore */ }

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Only show after MIN_VISITS
      try {
        const visits = parseInt(localStorage.getItem(VISIT_KEY) || '0', 10);
        if (visits >= MIN_VISITS) {
          setShowBanner(true);
        }
      } catch {
        setShowBanner(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    if (result.outcome === 'accepted') {
      setShowBanner(false);
      setIsInstalled(true);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setShowBanner(false);
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch { /* ignore */ }
  };

  if (!showBanner || isInstalled) return null;

  return (
    <Snackbar
      open={true}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert
        severity="info"
        variant="filled"
        sx={{ width: '100%', maxWidth: 450 }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DownloadIcon />
          <Typography variant="body2" sx={{ flexGrow: 1 }}>
            Инсталирайте Chronos за по-бърз достъп.
          </Typography>
          <Button size="small" color="inherit" onClick={handleInstall} sx={{ fontWeight: 'bold' }}>
            Инсталирай
          </Button>
          <Button size="small" color="inherit" onClick={handleDismiss}>
            Не сега
          </Button>
        </Box>
      </Alert>
    </Snackbar>
  );
};
