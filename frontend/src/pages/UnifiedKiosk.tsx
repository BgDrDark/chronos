import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from "html5-qrcode";
import { 
    Box, Typography, Paper, Button, Container, Dialog, 
    DialogTitle, DialogContent, DialogActions, TextField, Alert, Avatar, 
    CircularProgress, IconButton, Chip
} from '@mui/material';
import {
    AccessTime as AccessTimeIcon,
    CheckCircle as CheckCircleIcon,
    Close as CloseIcon,
    Error as ErrorIcon,
    Lock as LockIcon,
    Sync as SyncIcon,
    Contactless as NfcIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../utils/api';
import CodeKeyboard from '../components/CodeKeyboard';

interface TerminalHardwareInfo {
    mode: 'clock' | 'access' | 'both';
    registered: boolean;
    terminal_id: number | null;
    alias: string | null;
    is_active?: boolean;
    config?: TerminalCustomization;
}

export interface TerminalCustomization {
  display: {
    clock_size: 'large' | 'medium' | 'small';
    show_date: boolean;
    show_weather: boolean;
    background: { type: 'color' | 'gradient' | 'image'; value: string };
    logo_url: string | null;
  };
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    error: string;
    success: string;
  };
  timeouts: {
    inactivity_reset: number;
    screensaver_delay: number;
    screensaver_idle_action: 'reset' | 'screensaver';
  };
  screensaver: {
    type: 'logo' | 'clock' | 'slideshow' | 'none';
    image_url: string | null;
  };
  sounds: {
    enabled: boolean;
    scan_success: string;
    scan_error: string;
    keypress: string;
  };
  text: {
    title: string | null;
    welcome_message: string | null;
    scan_placeholder: string;
    scanning_text: string;
    success_message: string;
    error_message: string;
  };
  tts: {
    enabled: boolean;
    language: string;
    scan_success: boolean;
    scan_error: boolean;
  };
  security: {
    exit_method: 'pin' | 'password';
    exit_pin_required: boolean;
  };
  mode: 'qr' | 'nfc' | 'both';
}

const DEFAULT_TERMINAL_CUSTOMIZATION: TerminalCustomization = {
  display: { clock_size: 'large', show_date: true, show_weather: false, background: { type: 'color', value: '#1a1a2e' }, logo_url: null },
  colors: { primary: '#1976d2', secondary: '#dc004e', background: '#1a1a2e', surface: '#16213e', text: '#ffffff', error: '#ff5252', success: '#4caf50' },
  timeouts: { inactivity_reset: 120, screensaver_delay: 30, screensaver_idle_action: 'reset' },
  screensaver: { type: 'logo', image_url: null },
  sounds: { enabled: true, scan_success: 'default', scan_error: 'default', keypress: 'default' },
  text: { title: null, welcome_message: null, scan_placeholder: 'Поставете карта или QR код', scanning_text: 'Сканиране...', success_message: 'Достъпът е разрешен', error_message: 'Достъпът е отказан' },
  tts: { enabled: false, language: 'bg-BG', scan_success: true, scan_error: true },
  security: { exit_method: 'pin', exit_pin_required: true },
  mode: 'both',
};

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
    const [hwInfo, setHwInfo] = useState<TerminalHardwareInfo | null>(null);
    const [terminalCfg, setTerminalCfg] = useState<TerminalCustomization>(DEFAULT_TERMINAL_CUSTOMIZATION);
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
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    const [offlineQueue, setOfflineQueue] = useState<OfflineLog[]>([]);
    const [isOnline] = useState(navigator.onLine);
    const [syncing, setSyncing] = useState(false);
    
    // Idle Timer State
    const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [idle, setIdle] = useState(false);
    const [now, setNow] = useState(new Date());
    const lastActivityRef = useRef(Date.now());

    const resetIdleTimer = useCallback(() => {
        lastActivityRef.current = Date.now();
        setIdle(false);
        if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
        const delay = terminalCfg.timeouts.inactivity_reset * 1000;
        idleTimerRef.current = setTimeout(() => setIdle(true), delay);
    }, [terminalCfg.timeouts.inactivity_reset]);

    useEffect(() => {
        return () => { if (idleTimerRef.current) clearTimeout(idleTimerRef.current); };
    }, []);

    useEffect(() => {
        resetIdleTimer();
    }, [resetIdleTimer]);

    useEffect(() => {
        if (!idle) resetIdleTimer();
    }, [idle, resetIdleTimer]);

    useEffect(() => {
        const events = ['click', 'touchstart', 'keydown', 'mousemove'] as const;
        const handler = () => resetIdleTimer();
        for (const ev of events) window.addEventListener(ev, handler, { passive: true });
        return () => { for (const ev of events) window.removeEventListener(ev, handler); };
    }, [terminalCfg.timeouts.inactivity_reset, resetIdleTimer]);

    // WakeLock
    useEffect(() => {
        const lock: Promise<any> | null = 'wakeLock' in navigator ? (navigator as any).wakeLock.request('screen') : null;
        return () => { lock?.then((w: any) => w.release().catch(() => {})); };
    }, []);

    // Clock tick for screensaver
    useEffect(() => {
        if (!idle) return;
        const interval = setInterval(() => setNow(new Date()), 30000);
        return () => clearInterval(interval);
    }, [idle]);

    // Exit Lock State
    const [exitDialogOpen, setExitDialogOpen] = useState(false);
    const [exitPin, setExitPin] = useState('');
    const [exitEmail, setExitEmail] = useState('');
    const [exitPassword, setExitPassword] = useState('');
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

    useEffect(() => {
        isScanningRef.current = isScanning;
        setIsScanningRef.current = setIsScanning;
        setScanResultRef.current = setScanResult;
        setOfflineQueueRef.current = setOfflineQueue;
        offlineQueueRef.current = offlineQueue;
    }, [isScanning, setIsScanning, setScanResult, setOfflineQueue, offlineQueue]);

    // TTS Function
    const speak = useCallback((text: string, ttsType?: 'scan_success' | 'scan_error') => {
        if (!terminalCfg.tts.enabled) return;
        if (ttsType === 'scan_success' && !terminalCfg.tts.scan_success) return;
        if (ttsType === 'scan_error' && !terminalCfg.tts.scan_error) return;
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance(text);
            msg.lang = terminalCfg.tts.language;
            window.speechSynthesis.speak(msg);
        }
    }, [terminalCfg.tts]);

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
                setHwInfo(data);
                if (data.config) setTerminalCfg(data.config);
            } catch {
                setHwInfo({ mode: 'both', registered: false, terminal_id: null, alias: null });
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

    // Apply config colors as CSS variables
    useEffect(() => {
        const c = terminalCfg.colors;
        const root = document.documentElement;
        root.style.setProperty('--kiosk-primary', c.primary);
        root.style.setProperty('--kiosk-secondary', c.secondary);
        root.style.setProperty('--kiosk-bg', c.background);
        root.style.setProperty('--kiosk-surface', c.surface);
        root.style.setProperty('--kiosk-text', c.text);
        root.style.setProperty('--kiosk-error', c.error);
        root.style.setProperty('--kiosk-success', c.success);
    }, [terminalCfg]);

    const playSound = (type: 'success' | 'error') => {
        if (!terminalCfg.sounds.enabled) return;
        const soundKey = type === 'success' ? 'scan_success' : 'scan_error';
        const sound = terminalCfg.sounds[soundKey];
        if (sound && sound !== 'none' && sound !== 'default') {
            new Audio(sound).play().catch(() => {});
        } else if (sound !== 'none') {
            new Audio(type === 'success' ? '/success.mp3' : '/error.mp3').play().catch(() => {});
        }
    };

    const handleRequest = useCallback(async (payload: { qr_token?: string, code?: string, card_number?: string }) => {
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
                    
                    const ttsMsg = data.message || (data.access_granted ? terminalCfg.text.success_message : terminalCfg.text.error_message);
                    speak(ttsMsg, 'scan_success');
                    playSound('success');
                } else {
                    const msg = data.message || data.detail || terminalCfg.text.error_message;
                    setScanResultRef.current({ status: 'error', message: msg });
                    speak(terminalCfg.text.error_message, 'scan_error');
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
        const shouldScan = (terminalCfg.mode === 'qr' || terminalCfg.mode === 'both') && !loading && !scanResult;
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
    }, [terminalCfg.mode, loading, scanResult, onScanSuccess]);

    // NFC Reader
    const nfcReadingRef = useRef(false);
    useEffect(() => {
        const shouldReadNfc = (terminalCfg.mode === 'nfc' || terminalCfg.mode === 'both') && !loading && !scanResult;
        if (!shouldReadNfc || !('NDEFReader' in window)) return;

        let reader: any;
        let aborted = false;

        (async () => {
            try {
                reader = new (window as any).NDEFReader();
                await reader.scan();
                nfcReadingRef.current = true;
                reader.addEventListener('reading', ({ message }: any) => {
                    if (nfcReadingRef.current && message.records.length > 0) {
                        const decoder = new TextDecoder();
                        for (const record of message.records) {
                            if (record.mediaType === 'text/plain' || record.recordType === 'text') {
                                const text = decoder.decode(record.data);
                                handleRequest({ card_number: text });
                                break;
                            } else if (record.recordType === 'url') {
                                const url = decoder.decode(record.data);
                                handleRequest({ qr_token: url });
                                break;
                            }
                        }
                    }
                });
            } catch { /* NFC not available */ }
        })();

        return () => {
            aborted = true;
            nfcReadingRef.current = false;
        };
    }, [terminalCfg.mode, loading, scanResult, handleRequest]);

    const handleExitVerify = async () => {
        setIsVerifying(true);
        setExitError(null);
        try {
            const password = exitPassword.trim();
            if (terminalCfg.security.exit_method === 'password') {
                const response = await fetch(getApiUrl('auth/token'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `username=${encodeURIComponent(exitEmail)}&password=${encodeURIComponent(password)}`
                });
                if (response.ok) navigate('/');
                else setExitError('Невалиден имейл или парола');
            } else {
                const response = await fetch(getApiUrl(`kiosk/terminal/${hwidRef.current}/verify-pin`), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pin: exitPin })
                });
                if (response.ok) navigate('/');
                else setExitError('Невалиден ПИН код');
            }
        } catch { setExitError('Грешка при свързване'); }
        finally { setIsVerifying(false); }
    };

    if (loading) return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', bgcolor: terminalCfg.colors.background, color: terminalCfg.colors.text, flexDirection: 'column', gap: 2 }}>
            <CircularProgress sx={{ color: terminalCfg.colors.text }} />
            <Typography variant="h6">{terminalCfg.text.scanning_text}</Typography>
        </Box>
    );

    const defaultBg = terminalCfg.display.background.type === 'color'
        ? terminalCfg.display.background.value
        : terminalCfg.display.background.value;

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
                        <Typography variant="subtitle1" sx={{ color: 'white', fontWeight: 'bold', lineHeight: 1 }}>{hwInfo?.alias || terminalCfg.text.title || 'Chronos Terminal'}</Typography>
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

            {/* Screensaver Overlay */}
            {idle && (
                <Box sx={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: 9998, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: '#0d1117', color: '#c9d1d9' }}>
                    <AccessTimeIcon sx={{ fontSize: 120, opacity: 0.3, mb: 4 }} />
                    <Typography variant="h1" sx={{ fontSize: terminalCfg.display.clock_size, fontWeight: 300, mb: 2 }}>
                        {now.toLocaleTimeString('bg-BG', { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                    {terminalCfg.display.show_date && (
                        <Typography variant="h5" sx={{ opacity: 0.6 }}>
                            {now.toLocaleDateString('bg-BG', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        </Typography>
                    )}
                </Box>
            )}

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
                        <Box sx={{ 
                            display: 'flex', 
                            flexDirection: 'column', 
                            gap: 3,
                            alignItems: 'center'
                        }}>
                            {/* QR Scanner */}
                            {(terminalCfg.mode === 'qr' || terminalCfg.mode === 'both') && (
                                <Box sx={{ 
                                    overflow: 'hidden', borderRadius: 8, border: '8px solid rgba(255,255,255,0.2)', 
                                    bgcolor: 'black', boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
                                    '& #qr-reader': { border: 'none !important' },
                                    maxWidth: 400,
                                }}>
                                    <div id="qr-reader" style={{ width: '100%' }}></div>
                                </Box>
                            )}

                            {/* NFC */}
                            {(terminalCfg.mode === 'nfc' || terminalCfg.mode === 'both') && (
                                <Paper sx={{ 
                                    p: 2, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.1)',
                                    backdropFilter: 'blur(10px)', width: '100%', maxWidth: 400,
                                    textAlign: 'center', color: 'white'
                                }}>
                                    <NfcIcon sx={{ fontSize: 48, opacity: 0.7 }} />
                                    <Typography variant="body1">Доближете карта до NFC четеца</Typography>
                                </Paper>
                            )}

                            {/* Code Keyboard - always visible */}
                            <Box sx={{ maxWidth: 400, width: '100%' }}>
                                <CodeKeyboard onCodeSubmit={(code) => handleRequest({ code })} isLoading={!isScanning} />
                            </Box>
                        </Box>

                        <Box sx={{ mt: 4, textAlign: 'center', display: 'flex', justifyContent: 'center', gap: 2 }}>
                            {hwInfo?.mode !== 'access' && <Chip icon={<AccessTimeIcon sx={{ color: 'white !important' }} />} label="Работно Време" sx={{ bgcolor: 'primary.main', color: 'white' }} />}
                            {hwInfo?.mode !== 'clock' && <Chip icon={<LockIcon sx={{ color: 'white !important' }} />} label="Контрол на Достъпа" sx={{ bgcolor: 'secondary.main', color: 'white' }} />}
                        </Box>
                    </Container>
                )}
            </Box>

            {/* PIN Exit Dialog */}
            <Dialog open={exitDialogOpen} onClose={() => { setExitDialogOpen(false); setExitPin(''); setExitError(null); }}>
                <DialogTitle>Администраторски изход</DialogTitle>
                <DialogContent>
                    {terminalCfg.security.exit_method === 'password' ? (
                        <>
                            <TextField fullWidth label="Имейл" margin="normal" value={exitEmail} onChange={(e) => setExitEmail(e.target.value)} autoFocus />
                            <TextField fullWidth label="Парола" type="password" margin="normal" value={exitPassword} onChange={(e) => setExitPassword(e.target.value)} />
                        </>
                    ) : (
                        <TextField fullWidth label="ПИН код" type="password" margin="normal" value={exitPin} onChange={(e) => setExitPin(e.target.value)} autoFocus inputProps={{ inputMode: 'numeric', pattern: '[0-9]*' }} />
                    )}
                    {exitError && <Alert severity="error" sx={{ mt: 2 }}>{exitError}</Alert>}
                </DialogContent>
                <DialogActions sx={{ p: 3 }}>
                    <Button onClick={() => { setExitDialogOpen(false); setExitPin(''); setExitEmail(''); setExitPassword(''); setExitError(null); }}>Отказ</Button>
                    <Button onClick={handleExitVerify} variant="contained" disabled={isVerifying}>Вход</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default UnifiedKiosk;
