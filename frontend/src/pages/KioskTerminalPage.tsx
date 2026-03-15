import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from "html5-qrcode";
import { 
    Box, Typography, Paper, Button, Container, 
    Dialog, DialogTitle, DialogContent, DialogActions, 
    TextField, Alert, Stack
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Lock as LockIcon,
  Keyboard as KeyboardIcon,
  QrCodeScanner as QrCodeScannerIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../utils/api';
import CodeKeyboard from '../components/CodeKeyboard';

const KioskTerminalPage: React.FC = () => {
    const [scanResult, setScanResult] = useState<{ 
        status: 'success' | 'error' | 'warning', 
        message: string, 
        user?: string, 
        doorOpened?: boolean,
        doorName?: string
    } | null>(null);
    const [isScanning, setIsScanning] = useState(true);
    const [mode, setMode] = useState<'qr' | 'keyboard'>('qr');
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    const [terminalId, setTerminalId] = useState<string>('');
    
    // Exit Lock State
    const [exitDialogOpen, setExitDialogOpen] = useState(false);
    const [adminEmail, setAdminEmail] = useState('');
    const [adminPassword, setAdminPassword] = useState('');
    const [exitError, setExitError] = useState<string | null>(null);
    const [isVerifying, setIsVerifying] = useState(false);

    const navigate = useNavigate();
    const scannerRef = useRef<Html5QrcodeScanner | null>(null);

    // Initialize Terminal ID
    useEffect(() => {
        let id = localStorage.getItem('terminal_hardware_uuid');
        if (!id) {
            id = crypto.randomUUID();
            localStorage.setItem('terminal_hardware_uuid', id);
        }
        setTerminalId(id);
        
        // PWA optimizations
        // Request fullscreen on mount
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen().catch(() => {});
        }
        
        // Prevent screen sleep using Wake Lock API
        let wakeLock: WakeLockSentinel | null = null;

        const requestWakeLock = async () => {
            try {
                if ('wakeLock' in navigator) {
                    wakeLock = await (navigator as any).wakeLock.request('screen');
                }
            } catch {
                console.log('Wake Lock not available');
            }
        };
        requestWakeLock();
        
        return () => {
            if (wakeLock) {
                wakeLock.release();
            }
        };
    }, []);

    // TTS Function
    const speak = (text: string) => {
        if ('speechSynthesis' in window) {
            const msg = new SpeechSynthesisUtterance(text);
            msg.lang = 'bg-BG';
            window.speechSynthesis.speak(msg);
        }
    };

    // Fetch Kiosk Config
    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const response = await fetch(getApiUrl('kiosk/config'));
                const data = await response.json();
                if (data.background_image) {
                    setBackgroundImage(getApiUrl(`uploads/${data.background_image}`));
                }
            } catch (e) {
                console.error("Failed to fetch kiosk config", e);
            }
        };
        fetchConfig();
    }, []);

    const handleAccessRequest = useCallback(async (payload: { qr_token?: string, code?: string }) => {
        if (!isScanning && mode === 'qr') return;
        
        if (mode === 'qr' && scannerRef.current) {
            scannerRef.current.pause();
        }
        setIsScanning(false);

        try {
            const response = await fetch(getApiUrl('kiosk/terminal/scan'), {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Kiosk-Secret': 'super-secret-kiosk-key'
                },
                body: JSON.stringify({ 
                    ...payload, 
                    terminal_hardware_uuid: terminalId,
                    action: 'auto' 
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const status = data.status === 'success' ? 'success' : (data.status === 'warning' ? 'warning' : 'error');
                setScanResult({ 
                    status, 
                    message: data.message, 
                    user: data.user,
                    doorOpened: data.door_opened,
                    doorName: data.door_name
                });
                
                speak(data.message);
                
                if (data.door_opened) {
                    new Audio('/success.mp3').play().catch(() => {});
                }
            } else {
                const errorMsg = data.detail || 'Грешка при достъп';
                setScanResult({ status: 'error', message: errorMsg });
                speak(errorMsg);
                new Audio('/error.mp3').play().catch(() => {});
            }
        } catch {
            setScanResult({ status: 'error', message: "Мрежова грешка" });
            speak("Мрежова грешка");
        }

        setTimeout(() => {
            setScanResult(null);
            setIsScanning(true);
            if (mode === 'qr' && scannerRef.current) {
                scannerRef.current.resume();
            }
        }, 4000);
    }, [isScanning, mode, terminalId]);

    const onScanSuccess = useCallback((decodedText: string) => {
        handleAccessRequest({ qr_token: decodedText });
    }, [handleAccessRequest]);

    useEffect(() => {
        if (mode === 'qr') {
            const scanner = new Html5QrcodeScanner(
                "reader",
                { 
                    fps: 10, 
                    qrbox: { width: 280, height: 280 },
                    formatsToSupport: [ Html5QrcodeSupportedFormats.QR_CODE ]
                },
                false
            );
            
            scanner.render(onScanSuccess, () => {});
            scannerRef.current = scanner;

            return () => {
                scanner.clear().catch(error => {
                    console.error("Failed to clear scanner", error);
                });
            };
        } else {
            if (scannerRef.current) {
                scannerRef.current.clear().catch(() => {});
                scannerRef.current = null;
            }
        }
    }, [mode, onScanSuccess]);

    const handleExitAttempt = () => {
        setExitDialogOpen(true);
        setExitError(null);
    };

    const handleVerifyExit = async () => {
        setIsVerifying(true);
        setExitError(null);
        try {
            const response = await fetch(getApiUrl('auth/verify-admin-kiosk'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: adminEmail, password: adminPassword })
            });

            if (response.ok) {
                navigate('/');
            } else {
                const data = await response.json();
                setExitError(data.detail || "Грешен имейл или парола");
            }
        } catch {
            setExitError("Грешка при връзка със сървъра");
        } finally {
            setIsVerifying(false);
        }
    };

    const defaultBg = 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)';

    return (
        <Box sx={{ 
            height: '100vh', 
            width: '100vw',
            background: backgroundImage ? `url(${backgroundImage})` : defaultBg,
            backgroundRepeat: 'no-repeat',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            p: 3,
            position: 'relative',
            overflow: 'hidden'
        }}>
            <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', bgcolor: 'rgba(0,0,0,0.5)', zIndex: 0 }} />

            <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1 }}>
                <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 4 }}>
                    <Paper 
                        elevation={mode === 'qr' ? 10 : 2}
                        onClick={() => setMode('qr')}
                        sx={{ 
                            p: 2, px: 4, borderRadius: 4, cursor: 'pointer',
                            bgcolor: mode === 'qr' ? 'primary.main' : 'rgba(255,255,255,0.1)',
                            color: 'white', display: 'flex', alignItems: 'center', gap: 1,
                            transition: 'all 0.3s'
                        }}
                    >
                        <QrCodeScannerIcon />
                        <Typography variant="h6">QR СКЕНЕР</Typography>
                    </Paper>
                    <Paper 
                        elevation={mode === 'keyboard' ? 10 : 2}
                        onClick={() => setMode('keyboard')}
                        sx={{ 
                            p: 2, px: 4, borderRadius: 4, cursor: 'pointer',
                            bgcolor: mode === 'keyboard' ? 'primary.main' : 'rgba(255,255,255,0.1)',
                            color: 'white', display: 'flex', alignItems: 'center', gap: 1,
                            transition: 'all 0.3s'
                        }}
                    >
                        <KeyboardIcon />
                        <Typography variant="h6">КЛАВИАТУРА</Typography>
                    </Paper>
                </Stack>

                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                    <Box sx={{ width: '100%', maxWidth: '500px' }}>
                        {mode === 'qr' ? (
                            <Box sx={{ 
                                overflow: 'hidden', 
                                borderRadius: 8, 
                                border: '8px solid rgba(255,255,255,0.2)', 
                                bgcolor: 'black',
                                boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
                                '& #reader': { border: 'none !important' }
                            }}>
                                <div id="reader" style={{ width: '100%' }}></div>
                            </Box>
                        ) : (
                            <CodeKeyboard onCodeSubmit={(code) => handleAccessRequest({ code })} isLoading={!isScanning} />
                        )}
                    </Box>
                </Box>

                <Box sx={{ mt: 6, textAlign: 'center' }}>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)', mb: 2, fontFamily: 'monospace' }}>
                        ID: {terminalId}
                    </Typography>
                    <Button 
                        variant="contained"
                        sx={{ 
                            borderRadius: 10, px: 4, py: 1.5,
                            bgcolor: 'rgba(0,0,0,0.4)', color: 'white', 
                            border: '1px solid rgba(255,255,255,0.3)',
                            '&:hover': { bgcolor: 'rgba(0,0,0,0.6)', borderColor: 'white' } 
                        }}
                        onClick={handleExitAttempt} 
                        startIcon={<LockIcon />}
                    >
                        АДМИН ПАНЕЛ
                    </Button>
                </Box>

                {scanResult && (
                    <Paper sx={{ 
                        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        zIndex: 9999,
                        bgcolor: scanResult.status === 'success' ? '#1b5e20' : (scanResult.status === 'warning' ? '#f57c00' : '#b71c1c'),
                        color: 'white', p: 4, textAlign: 'center',
                        animation: 'fadeIn 0.3s ease-out',
                        '@keyframes fadeIn': { from: { opacity: 0 }, to: { opacity: 1 } }
                    }}>
                        {scanResult.status === 'success' ? <CheckCircleIcon sx={{ fontSize: 180, mb: 4 }} /> : <ErrorIcon sx={{ fontSize: 180, mb: 4 }} />}
                        <Typography variant="h2" fontWeight="900" gutterBottom>{scanResult.message}</Typography>
                        {scanResult.user && <Typography variant="h4">{scanResult.user}</Typography>}
                        {scanResult.doorOpened && (
                            <Box sx={{ mt: 4, p: 2, border: '2px dashed white', borderRadius: 4 }}>
                                <Typography variant="h5">ВРАТАТА Е ОТВОРЕНА: {scanResult.doorName}</Typography>
                            </Box>
                        )}
                    </Paper>
                )}

                <Dialog open={exitDialogOpen} onClose={() => setExitDialogOpen(false)}>
                    <DialogTitle>Администраторски достъп</DialogTitle>
                    <DialogContent>
                        <TextField fullWidth label="Имейл" margin="normal" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} />
                        <TextField fullWidth label="Парола" type="password" margin="normal" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} />
                        {exitError && <Alert severity="error" sx={{ mt: 2 }}>{exitError}</Alert>}
                    </DialogContent>
                    <DialogActions sx={{ p: 3 }}>
                        <Button onClick={() => setExitDialogOpen(false)}>Отказ</Button>
                        <Button onClick={handleVerifyExit} variant="contained" disabled={isVerifying}>Отключи</Button>
                    </DialogActions>
                </Dialog>
            </Container>
        </Box>
    );
};

export default KioskTerminalPage;
