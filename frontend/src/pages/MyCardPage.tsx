import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, CircularProgress, 
  IconButton, Container, AppBar, Toolbar, Button 
} from '@mui/material';
import { QRCodeSVG } from 'qrcode.react';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const MyCardPage: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState(30);
  const [beaconDetected, setBeaconDetected] = useState<boolean>(false);
  const [scanning, setScanning] = useState<boolean>(false);
  const navigate = useNavigate();

  const scanForBeacon = async () => {
    if (!('bluetooth' in navigator)) {
      setBeaconDetected(true); // Fallback за устройства без поддръжка
      return;
    }

    try {
      setScanning(true);
      // Търсим Chronos терминал чрез Bluetooth
      const device = await (navigator as any).bluetooth.requestDevice({
        acceptAllDevices: false,
        filters: [{ namePrefix: 'Chronos' }]
      });

      if (device) {
        setBeaconDetected(true);
      }
    } catch (err) {
      console.error('Bluetooth scan failed:', err);
      setBeaconDetected(false);
    } finally {
      setScanning(false);
    }
  };

  const fetchToken = async () => {
    // Ако не сме админ и не е засечен бекон, първо сканираме
    // (Забележка: Админите ги пропускаме за лесно тестване)
    if (!beaconDetected && !loading) {
        // Първия път ще изискваме ръчно сканиране чрез бутон за UX
        // Но за сигурност, ако не е засечен, връщаме грешка
        setError('Моля, застанете до терминала и натиснете "Сканирай за терминал"');
        setLoading(false);
        return;
    }

    try {
      // Опит за вземане на GPS координати
      let coords = '';
      try {
        const pos = await new Promise<GeolocationPosition>((res, rej) => {
          navigator.geolocation.getCurrentPosition(res, rej, { timeout: 5000 });
        });
        coords = `?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`;
      } catch (e) {
        console.warn('GPS access denied or timeout');
      }

      const response = await axios.get(`${API_URL}/auth/qr-token${coords}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setToken(response.data.qr_token);
      setLoading(false);
      setTimeLeft(30);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Грешка при зареждане на картата');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchToken();
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          fetchToken();
          return 30;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Увеличаване на яркостта за по-лесно сканиране (PWA API)
  useEffect(() => {
    if ('wakeLock' in navigator) {
      try {
        (navigator as any).wakeLock.request('screen');
      } catch (err) {}
    }
  }, []);

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      bgcolor: '#f5f5f5', 
      display: 'flex', 
      flexDirection: 'column' 
    }}>
      <AppBar position="static" elevation={0} sx={{ bgcolor: 'white', color: 'text.primary' }}>
        <Toolbar>
          <IconButton edge="start" onClick={() => navigate(-1)} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Карта за достъп
          </Typography>
          <IconButton onClick={fetchToken} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xs" sx={{ mt: 4, textAlign: 'center' }}>
        <Paper elevation={4} sx={{ 
          p: 4, 
          borderRadius: 4, 
          bgcolor: 'white',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
            СКАНИРАЙ ТУК
          </Typography>
          
          <Box sx={{ 
            p: 2, 
            bgcolor: 'white', 
            borderRadius: 2, 
            boxShadow: 'inset 0 0 10px rgba(0,0,0,0.1)',
            mb: 3,
            position: 'relative'
          }}>
            {loading ? (
              <Box sx={{ width: 256, height: 256, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CircularProgress />
              </Box>
            ) : token ? (
              <QRCodeSVG value={token} size={256} level="H" includeMargin />
            ) : (
              <Typography color="error">{error}</Typography>
            )}
          </Box>

          <Box sx={{ width: '100%', mb: 2 }}>
            {!beaconDetected ? (
              <Button 
                variant="contained" 
                color="secondary" 
                startIcon={scanning ? <CircularProgress size={20} /> : <RefreshIcon />}
                onClick={scanForBeacon}
                disabled={scanning}
                fullWidth
                sx={{ mb: 2 }}
              >
                Сканирай за терминал (Bluetooth)
              </Button>
            ) : (
              <Typography variant="body2" color="success.main" sx={{ mb: 2, fontWeight: 'bold' }}>
                ✓ Терминалът е засечен в близост
              </Typography>
            )}

            <Typography variant="body2" color="textSecondary">
              Кодът се обновява автоматично след:
            </Typography>
            <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
              {timeLeft} сек.
            </Typography>
          </Box>

          <Typography variant="caption" color="textSecondary" sx={{ px: 2 }}>
            Покажете този код пред терминала за маркиране на присъствие. 
            Кодът е динамичен и е валиден само за кратък период.
          </Typography>
        </Paper>
        
        <Box sx={{ mt: 4 }}>
            <Typography variant="subtitle2" color="textSecondary">
                © {new Date().getFullYear()} Chronos WorkTime Security
            </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default MyCardPage;
