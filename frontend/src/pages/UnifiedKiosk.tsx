import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from "html5-qrcode";
import { 
    Box, Typography, Paper, Button, Container, Dialog, 
    DialogTitle, DialogContent, DialogActions, TextField, Alert, Avatar, 
    CircularProgress, Stack, IconButton, Chip
} from '@mui/material';
import {
    AccessTime as AccessTimeIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    Lock as LockIcon,
    QrCodeScanner as QrCodeScannerIcon,
    Keyboard as KeyboardIcon,
    Sync as SyncIcon,
    Close as CloseIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../utils/api';
import CodeKeyboard from '../components/CodeKeyboard';

interface TerminalConfig {
    mode: 'clock' | 'access' | 'both';
    registered: boolean;
    terminal_id: number | null;
    alias: string | null;
    is_active?: boolean;
}

interface OfflineLog {
    id: string;
    type: 'clock' | 'access';
    timestamp: string;
    user_id?: number;
    zone_id?: number;
    door_id?: number;
    result?: string;
    action?: string;
}

const UnifiedKiosk: React.FC = () => {
    const [config, setConfig] = useState<TerminalConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [scanResult, setScanResult] = useState<{ 
        status: 'success' | 'warning' | 'error', 
        message: string, 
        user?: string,
        clock_action?: string,
        door_opened?: boolean,
        door_name?: string,
        profile_picture?: string
    } | null>(null);
    const [isScanning, setIsScanning] = useState(true);
    const [entryMode, setEntryMode] = useState<'qr' | 'keyboard'>('qr');
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    const [offlineQueue, setOfflineQueue] = useState<OfflineLog[]>([]);
    const [isOnline] = useState(navigator.onLine);
    const [syncing, setSyncing] = useState(false);
    
    // Exit Lock State
    const [exitDialogOpen, setExitDialogOpen] = useState(false);
    const [adminEmail, setAdminEmail] = useState('');
    const [adminPassword, setAdminPassword] = useState('');
    const [exitError, setExitError] = useState<string | null>(null);
    const [isVerifying, setIsVerifying] = useState(false);

    const navigate = useNavigate();
    const scannerRef = useRef<Html5QrcodeScanner | null>(null);
    const hwidRef = useRef<string>('');

    const isScanningRef = useRef(isScanning);
    const setIsScanningRef = useRef(setIsScanning);
    const setScanResultRef = useRef(setScanResult);
    const setOfflineQueueRef = useRef(setOfflineQueue);
    const offlineQueueRef = useRef(offlineQueue);
    isScanningRef.current = isScanning;
    setIsScanningRef.current = setIsScanning;
    setScanResultRef.current = setScanResult;
    setOfflineQueueRef.current = setOfflineQueue;
    offlineQueueRef.current = offlineQueue;

    // TTS Function
    const speak = useCallback((text: string) => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance(text);
            msg.lang = 'en-US';
            window.speechSynthesis.speak(msg);
        }
    }, []);

    // Get or create hardware UUID
    const getOrCreateHWID = useCallback((): string => {
        let id = localStorage.getItem('terminal_hardware_uuid');
        if (!id) {
            id = 'TERMINAL-' + Math.random().toString(36).substring(2, 15).toUpperCase();
            localStorage.setItem('terminal_hardware_uuid', id);
        }
        hwidRef.current = id;
        return id;
    }, []);

    // Sync offline data
    const syncOfflineData = async () => {
        if (offlineQueue.length === 0) return;
        setSyncing(true);
        try {
            const hwid = getOrCreateHWID();
            const response = await fetch(getApiUrl(`kiosk/terminal/${hwid}/sync`), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ offline_logs: offlineQueue })
            });
            if (response.ok) {
                const newQueue: OfflineLog[] = [];
                localStorage.setItem('offline_queue', JSON.stringify(newQueue));
                setOfflineQueue(newQueue);
            }
        } catch (err) {
            console.error('Sync failed:', err);
        } finally {
            setSyncing(false);
        }
    };

    // Init and Config
    useEffect(() => {
        const initTerminal = async () => {
            const hwid = getOrCreateHWID();
            
            // Load queue
            const saved = localStorage.getItem('offline_queue');
            if (saved) setOfflineQueue(JSON.parse(saved));

            // Request Fullscreen
            try { document.documentElement.requestFullscreen(); } catch { /* Ignore fullscreen errors */ }

            // Fetch Config
            try {
                const response = await fetch(getApiUrl(`kiosk/terminal/${hwid}/config`));
                const data = await response.json();
                setConfig(data);
            } catch {
                setConfig({ mode: 'both', registered: false, terminal_id: null, alias: null });
            }

            // Fetch Background
            try {
                const bgResponse = await fetch(getApiUrl('kiosk/config'));
                const bgData = await bgResponse.json();
                if (bgData.background_image) {
                    setBackgroundImage(getApiUrl(`uploads/${bgData.background_image}`));
                }
            } catch { /* Ignore background fetch errors */ }

            setLoading(false);
        };
        initTerminal();
    }, [getOrCreateHWID]);

    const playSound = (type: 'success' | 'error') => {
        const audio = new Audio(type === 'success' ? '/success.mp3' : '/error.mp3');
        audio.play().catch(() => {});
    };

    const handleRequest = useCallback(async (payload: { qr_token?: string, code?: string }) => {
        if (!isScanningRef.current) return;
        setIsScanningRef.current(false);
        if (scannerRef.current) scannerRef.current.pause();

        const hwid = getOrCreateHWID();

        try {
            if (isOnline) {
                const response = await fetch(getApiUrl(`kiosk/terminal/${hwid}/scan`), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...payload, terminal_hardware_uuid: hwid })
                });
                const data = await response.json();
                
                if (response.ok && data.success) {
                    setScanResultRef.current({
                        status: data.door_opened === false && data.access_granted === false ? 'warning' : 'success',
                        message: data.message,
                        user: data.user,
                        clock_action: data.clock_action,
                        door_opened: data.door_opened,
                        door_name: data.door_name,
                        profile_picture: data.profile_picture
                    });
                    
                    let ttsMsg = "Success";
                    if (data.clock_action === "in") {
                        ttsMsg = "Thank you, have a nice day";
                    } else if (data.clock_action === "out") {
                        ttsMsg = "Thank you, goodbye";
                    } else if (data.access_granted) {
                        ttsMsg = "Access granted";
                    }
                    speak(ttsMsg);
                    playSound('success');
                } else {
                    const msg = data.message || data.detail || 'Error';
                    setScanResultRef.current({ status: 'error', message: msg });
                    speak("Access denied");
                    playSound('error');
                }

            } else {
                const queue = [...offlineQueueRef.current, { id: Date.now().toString(), type: 'clock', timestamp: new Date().toISOString(), action: 'auto' }];
                localStorage.setItem('offline_queue', JSON.stringify(queue));
                setOfflineQueueRef.current(queue as OfflineLog[]);
                setScanResultRef.current({ status: 'success', message: 'Записано офлайн (БЕЗ ДОСТЪП)' });
                playSound('success');
            }
        } catch {
            setScanResultRef.current({ status: 'error', message: 'Мрежова грешка' });
            playSound('error');
        }

        setTimeout(() => {
            setScanResultRef.current(null);
            setIsScanningRef.current(true);
            if (scannerRef.current) scannerRef.current.resume();
        }, 4000);
    }, [isOnline, getOrCreateHWID, speak]);

    const onScanSuccess = useCallback((text: string) => {
        handleRequest({ qr_token: text });
    }, [handleRequest]);

    // Scanner Management
    useEffect(() => {
        const shouldScan = entryMode === 'qr' && !loading && !scanResult;
        if (shouldScan) {
            const scanner = new Html5QrcodeScanner(
                "qr-reader",
                { fps: 10, qrbox: { width: 280, height: 280 }, formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE] },
                false
            );
            scanner.render(onScanSuccess, () => {});
            scannerRef.current = scanner;
            return () => { scanner.clear().catch(() => {}); };
        }
    }, [entryMode, loading, scanResult, onScanSuccess]);

    const handleExitVerify = async () => {
        setIsVerifying(true);
        setExitError(null);
        try {
            const response = await fetch(getApiUrl('auth/token'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `username=${encodeURIComponent(adminEmail)}&password=${encodeURIComponent(adminPassword)}`
            });
            if (response.ok) navigate('/');
            else setExitError('Невалиден имейл или парола');
        } catch { setExitError('Грешка при свързване'); }
        finally { setIsVerifying(false); }
    };

    if (loading) return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', bgcolor: '#1a237e', color: 'white', flexDirection: 'column', gap: 2 }}>
            <CircularProgress color="inherit" />
            <Typography variant="h6">Инициализиране на терминал...</Typography>
        </Box>
    );

    const defaultBg = 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)';

    return (
        <Box sx={{ 
            minHeight: '100vh', 
            background: backgroundImage ? `url(${backgroundImage})` : defaultBg,
            backgroundSize: 'cover', backgroundPosition: 'center',
            display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden'
        }}>
            <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', bgcolor: 'rgba(0,0,0,0.4)', zIndex: 0 }} />

            {/* Top Bar */}
            <Box sx={{ zIndex: 1, p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: 'rgba(0,0,0,0.3)', backdropFilter: 'blur(5px)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}><LockIcon /></Avatar>
                    <Box>
                        <Typography variant="subtitle1" sx={{ color: 'white', fontWeight: 'bold', lineHeight: 1 }}>{config?.alias || 'Chronos Terminal'}</Typography>
                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>{isOnline ? '● Онлайн' : '○ Офлайн'}</Typography>
                    </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    {offlineQueue.length > 0 && (
                        <Button startIcon={<SyncIcon />} variant="contained" color="warning" size="small" onClick={syncOfflineData} disabled={syncing}>
                            {syncing ? 'Синхр...' : `${offlineQueue.length} в опашка`}
                        </Button>
                    )}
                    <IconButton onClick={() => setExitDialogOpen(true)} sx={{ color: 'white', bgcolor: 'rgba(255,255,255,0.1)' }}><CloseIcon /></IconButton>
                </Box>
            </Box>

            {/* Main Center Area */}
            <Box sx={{ zIndex: 1, flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 3 }}>
                
                {/* Result Overlay */}
                {scanResult && (
                    <Paper sx={{ 
                        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999,
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        bgcolor: scanResult.status === 'success' ? 'rgba(27, 94, 32, 0.95)' : 
                                 scanResult.status === 'warning' ? 'rgba(255, 145, 0, 0.95)' : 'rgba(183, 28, 28, 0.95)',
                        backdropFilter: 'blur(20px)', color: 'white', p: 4, textAlign: 'center',
                        animation: 'fadeIn 0.3s ease-out', '@keyframes fadeIn': { from: { opacity: 0 }, to: { opacity: 1 } }
                    }}>
                        <Avatar 
                            src={scanResult.profile_picture ? (scanResult.profile_picture.startsWith('http') ? scanResult.profile_picture : getApiUrl(scanResult.profile_picture.substring(1))) : undefined} 
                            sx={{ width: 280, height: 280, mb: 4, border: '10px solid white', boxShadow: 20 }}
                        >
                            {scanResult.user?.charAt(0)}
                        </Avatar>
                        <Typography variant="h1" sx={{ fontWeight: 900, mb: 1, textShadow: '0 4px 10px rgba(0,0,0,0.3)' }}>{scanResult.message}</Typography>
                        <Typography variant="h3" sx={{ opacity: 0.9, mb: 4 }}>{scanResult.user}</Typography>
                        {scanResult.door_opened && (
                            <Box sx={{ p: 2, px: 4, border: '4px dashed white', borderRadius: 4, mb: 4 }}>
                                <Typography variant="h4" fontWeight="bold">🚪 {scanResult.door_name} (ОТВОРЕНО)</Typography>
                            </Box>
                        )}
                        {scanResult.status === 'success' ? <CheckCircleIcon sx={{ fontSize: 120, color: '#a5d6a7' }} /> : <ErrorIcon sx={{ fontSize: 120, color: '#ffcc80' }} />}
                    </Paper>
                )}

                {/* Entry Interface */}
                {!scanResult && (
                    <Container maxWidth="sm">
                        <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 4 }}>
                            <Button 
                                variant={entryMode === 'qr' ? 'contained' : 'outlined'} 
                                onClick={() => setEntryMode('qr')}
                                startIcon={<QrCodeScannerIcon />}
                                sx={{ borderRadius: 4, px: 4, py: 1.5, color: 'white', borderColor: 'white' }}
                            >
                                QR СКЕНЕР
                            </Button>
                            <Button 
                                variant={entryMode === 'keyboard' ? 'contained' : 'outlined'} 
                                onClick={() => setEntryMode('keyboard')}
                                startIcon={<KeyboardIcon />}
                                sx={{ borderRadius: 4, px: 4, py: 1.5, color: 'white', borderColor: 'white' }}
                            >
                                КЛАВИАТУРА
                            </Button>
                        </Stack>

                        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                            <Box sx={{ width: '100%' }}>
                                {entryMode === 'qr' ? (
                                    <Box sx={{ 
                                        overflow: 'hidden', borderRadius: 8, border: '8px solid rgba(255,255,255,0.2)', 
                                        bgcolor: 'black', boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
                                        '& #qr-reader': { border: 'none !important' }
                                    }}>
                                        <div id="qr-reader" style={{ width: '100%' }}></div>
                                    </Box>
                                ) : (
                                    <CodeKeyboard onCodeSubmit={(code) => handleRequest({ code })} isLoading={!isScanning} />
                                )}
                            </Box>
                        </Box>

                        <Box sx={{ mt: 4, textAlign: 'center', display: 'flex', justifyContent: 'center', gap: 2 }}>
                            {config?.mode !== 'access' && <Chip icon={<AccessTimeIcon sx={{ color: 'white !important' }} />} label="Работно Време" sx={{ bgcolor: 'primary.main', color: 'white' }} />}
                            {config?.mode !== 'clock' && <Chip icon={<LockIcon sx={{ color: 'white !important' }} />} label="Контрол на Достъпа" sx={{ bgcolor: 'secondary.main', color: 'white' }} />}
                        </Box>
                    </Container>
                )}
            </Box>

            {/* Admin Exit Dialog */}
            <Dialog open={exitDialogOpen} onClose={() => setExitDialogOpen(false)}>
                <DialogTitle>Администраторски изход</DialogTitle>
                <DialogContent>
                    <TextField fullWidth label="Имейл" margin="normal" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} />
                    <TextField fullWidth label="Парола" type="password" margin="normal" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} />
                    {exitError && <Alert severity="error" sx={{ mt: 2 }}>{exitError}</Alert>}
                </DialogContent>
                <DialogActions sx={{ p: 3 }}>
                    <Button onClick={() => setExitDialogOpen(false)}>Отказ</Button>
                    <Button onClick={handleExitVerify} variant="contained" disabled={isVerifying}>Вход</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default UnifiedKiosk;
