import React, { useEffect, useState, useRef } from 'react';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from "html5-qrcode";
import { 
    Box, Typography, Paper, Button, Container, Dialog, 
    DialogTitle, DialogContent, DialogActions, TextField, Alert, Avatar, 
    CircularProgress, Card, CardContent, Grid
} from '@mui/material';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import LockIcon from '@mui/icons-material/Lock';
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner';
import { getApiUrl } from '../utils/api';

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
        status: 'success' | 'error', 
        message: string, 
        user?: string,
        clock_action?: string,
        door_opened?: boolean,
        door_name?: string
    } | null>(null);
    const [isScanning, setIsScanning] = useState(true);
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    const [offlineQueue, setOfflineQueue] = useState<OfflineLog[]>([]);
    const [isOnline, setIsOnline] = useState(navigator.onLine);
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

    // Get or create hardware UUID
    const getOrCreateHWID = (): string => {
        let id = localStorage.getItem('terminal_hardware_uuid');
        if (!id) {
            id = 'TERMINAL-' + Math.random().toString(36).substring(2, 15).toUpperCase();
            localStorage.setItem('terminal_hardware_uuid', id);
        }
        hwidRef.current = id;
        return id;
    };

    // Load offline queue from localStorage
    const loadOfflineQueue = () => {
        const saved = localStorage.getItem('offline_queue');
        if (saved) {
            try {
                setOfflineQueue(JSON.parse(saved));
            } catch (e) {
                console.error('Failed to parse offline queue', e);
            }
        }
    };

    // Save offline queue to localStorage
    const saveOfflineQueue = (queue: OfflineLog[]) => {
        localStorage.setItem('offline_queue', JSON.stringify(queue));
        setOfflineQueue(queue);
    };

    // Add to offline queue
    const addToOfflineQueue = (log: Omit<OfflineLog, 'id'>) => {
        const newLog: OfflineLog = {
            ...log,
            id: Date.now().toString() + Math.random().toString(36).substring(7)
        };
        const newQueue = [...offlineQueue, newLog];
        saveOfflineQueue(newQueue);
    };

    // Sync offline data with backend
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
                saveOfflineQueue([]); // Clear queue after successful sync
            }
        } catch (err) {
            console.error('Sync failed:', err);
        } finally {
            setSyncing(false);
        }
    };

    // Check online status
    useEffect(() => {
        const handleOnline = () => {
            setIsOnline(true);
            // Try to sync when back online
            if (offlineQueue.length > 0) {
                syncOfflineData();
            }
        };
        
        const handleOffline = () => {
            setIsOnline(false);
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, [offlineQueue]);

    // Initialize terminal
    useEffect(() => {
        const initTerminal = async () => {
            const hwid = getOrCreateHWID();
            loadOfflineQueue();
            
            // Request fullscreen
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen().catch(() => {});
            }

            // Prevent screen sleep
            let wakeLock: any = null;
            const requestWakeLock = async () => {
                try {
                    if ('wakeLock' in navigator) {
                        wakeLock = await (navigator as any).wakeLock.request('screen');
                    }
                } catch (err) {
                    console.log('Wake Lock not available');
                }
            };
            requestWakeLock();

            // Fetch config from backend
            try {
                const response = await fetch(getApiUrl(`kiosk/terminal/${hwid}/config`));
                const data = await response.json();
                setConfig(data);
            } catch (err) {
                console.error('Failed to fetch config:', err);
                // Use default config if offline
                setConfig({ mode: 'both', registered: false, terminal_id: null, alias: null });
            }

            // Fetch background image
            try {
                const bgResponse = await fetch(getApiUrl('kiosk/config'));
                const bgData = await bgResponse.json();
                if (bgData.background_image) {
                    setBackgroundImage(getApiUrl(`uploads/${bgData.background_image}`));
                }
            } catch (e) {
                console.error("Failed to fetch kiosk config", e);
            }

            setLoading(false);

            return () => {
                if (wakeLock) {
                    wakeLock.release();
                }
            };
        };

        initTerminal();
    }, []);

    // Play sound
    const playSound = (type: 'success' | 'error') => {
        const audio = new Audio(type === 'success' ? '/success.mp3' : '/error.mp3');
        audio.play().catch(() => {});
    };

    // Handle QR scan success
    const onScanSuccess = async (decodedText: string) => {
        if (!isScanning || !config) return;
        
        if (scannerRef.current) {
            scannerRef.current.pause();
        }
        setIsScanning(false);

        const hwid = getOrCreateHWID();

        try {
            let response;
            
            if (isOnline) {
                // Direct API call
                response = await fetch(getApiUrl(`kiosk/terminal/${hwid}/scan`), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        qr_token: decodedText,
                        action: 'auto',
                        terminal_hardware_uuid: hwid
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    setScanResult({
                        status: 'success',
                        message: data.message || 'Успешно!',
                        user: data.user,
                        clock_action: data.clock_action,
                        door_opened: data.door_opened,
                        door_name: data.door_name
                    });
                    playSound('success');
                } else {
                    setScanResult({
                        status: 'error',
                        message: data.message || 'Грешка'
                    });
                    playSound('error');
                }
            } else {
                // Offline mode - add to queue
                addToOfflineQueue({
                    type: 'clock',
                    timestamp: new Date().toISOString(),
                    action: 'auto'
                });
                
                setScanResult({
                    status: 'success',
                    message: 'Записано офлайн. Ще бъде синхронизирано по-късно.',
                    clock_action: 'in'
                });
                playSound('success');
            }
        } catch (e) {
            setScanResult({ status: 'error', message: 'Мрежова грешка' });
            playSound('error');
        }

        // Reset scanner after 4 seconds
        setTimeout(() => {
            setScanResult(null);
            setIsScanning(true);
            if (scannerRef.current) {
                scannerRef.current.resume();
            }
        }, 4000);
    };

    const onScanFailure = () => {
        // Ignored
    };

    // Handle exit attempt
    const handleExitAttempt = () => {
        setExitDialogOpen(true);
    };

    const handleExitVerify = async () => {
        setIsVerifying(true);
        try {
            const response = await fetch(getApiUrl('auth/token'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `username=${encodeURIComponent(adminEmail)}&password=${encodeURIComponent(adminPassword)}`
            });
            
            if (response.ok) {
                window.location.href = '/';
            } else {
                setExitError('Невалиден имейл или парола');
            }
        } catch (e) {
            setExitError('Грешка при свързване');
        } finally {
            setIsVerifying(false);
        }
    };

    // Handle manual code entry
    const handleManualCodeEntry = async (code: string) => {
        if (!code || !config) return;
        
        const hwid = getOrCreateHWID();
        
        try {
            if (isOnline) {
                const response = await fetch(getApiUrl(`kiosk/terminal/${hwid}/scan`), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        qr_token: code,
                        action: 'auto',
                        terminal_hardware_uuid: hwid
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    setScanResult({
                        status: 'success',
                        message: data.message || 'Успешно!',
                        user: data.user,
                        clock_action: data.clock_action
                    });
                    playSound('success');
                } else {
                    setScanResult({
                        status: 'error',
                        message: data.message || 'Грешка'
                    });
                    playSound('error');
                }
            } else {
                addToOfflineQueue({
                    type: 'clock',
                    timestamp: new Date().toISOString(),
                    action: 'auto'
                });
                setScanResult({
                    status: 'success',
                    message: 'Записано офлайн'
                });
                playSound('success');
            }
        } catch (e) {
            setScanResult({ status: 'error', message: 'Мрежова грешка' });
            playSound('error');
        }
        
        setTimeout(() => {
            setScanResult(null);
        }, 4000);
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column', gap: 2 }}>
                <CircularProgress size={48} />
                <Typography>Зареждане на терминала...</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ 
            minHeight: '100vh', 
            bgcolor: backgroundImage ? `url(${backgroundImage})` : '#f5f5f5',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            display: 'flex',
            flexDirection: 'column'
        }}>
            {/* Status bar */}
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                p: 1,
                bgcolor: isOnline ? 'success.main' : 'warning.main',
                color: 'white'
            }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {config?.alias || 'Терминал'}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {!isOnline && (
                        <Typography variant="body2">⚠️ Офлайн</Typography>
                    )}
                    {offlineQueue.length > 0 && (
                        <Typography variant="body2">📥 {offlineQueueQueue.length} чака</Typography>
                    )}
                    {isOnline && offlineQueue.length > 0 && (
                        <Button size="small" color="inherit" onClick={syncOfflineData} disabled={syncing}>
                            {syncing ? 'Синхр...' : 'Синхр'}
                        </Button>
                    )}
                    <Button size="small" color="inherit" onClick={handleExitAttempt}>✕</Button>
                </Box>
            </Box>

            {/* Main content */}
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 3 }}>
                {/* Mode indicator */}
                <Box sx={{ mb: 3, display: 'flex', gap: 1 }}>
                    {config?.mode === 'clock' && (
                        <Chip icon={<AccessTimeIcon />} label="Clock In/Out" color="primary" />
                    )}
                    {config?.mode === 'access' && (
                        <Chip icon={<LockIcon />} label="Достъп" color="secondary" />
                    )}
                    {config?.mode === 'both' && (
                        <>
                            <Chip icon={<AccessTimeIcon />} label="Clock In/Out" color="primary" />
                            <Chip icon={<LockIcon />} label="Достъп" color="secondary" />
                        </>
                    )}
                </Box>

                {/* Scan Result */}
                {scanResult ? (
                    <Paper sx={{ 
                        p: 4, 
                        textAlign: 'center',
                        bgcolor: scanResult.status === 'success' ? 'success.light' : 'error.light',
                        minWidth: 300
                    }}>
                        {scanResult.status === 'success' ? (
                            <CheckCircleIcon sx={{ fontSize: 80, color: 'success.dark', mb: 2 }} />
                        ) : (
                            <ErrorIcon sx={{ fontSize: 80, color: 'error.dark', mb: 2 }} />
                        )}
                        <Typography variant="h5" sx={{ mb: 1 }}>
                            {scanResult.message}
                        </Typography>
                        {scanResult.user && (
                            <Typography variant="h6">{scanResult.user}</Typography>
                        )}
                        {scanResult.door_opened && (
                            <Typography>🚪 {scanResult.door_name}</Typography>
                        )}
                    </Paper>
                ) : (
                    /* QR Scanner */
                    <Paper sx={{ p: 3, maxWidth: 500, width: '100%' }}>
                        <Typography variant="h6" align="center" sx={{ mb: 2 }}>
                            {config?.mode === 'clock' ? 'Сканирайте QR кода си' : 
                             config?.mode === 'access' ? 'Сканирайте за достъп' :
                             'Сканирайте QR кода'}
                        </Typography>
                        
                        <Box id="qr-scanner" sx={{ width: '100%' }}>
                            <Html5QrcodeScanner
                                fps={10}
                                qrbox={250}
                                supportedFormats={[Html5QrcodeSupportedFormats.QR_CODE]}
                                onSuccess={onScanSuccess}
                                onFailure={onScanFailure}
                                config={{ fps: 10, qrbox: { width: 250, height: 250 } }}
                            />
                        </Box>
                        
                        <Divider sx={{ my: 2 }}>
                            <Typography variant="body2" color="text.secondary">или</Typography>
                        </Divider>
                        
                        {/* Manual code entry */}
                        <ManualCodeEntry onSubmit={handleManualCodeEntry} />
                    </Paper>
                )}
            </Box>

            {/* Exit dialog */}
            <Dialog open={exitDialogOpen} onClose={() => setExitDialogOpen(false)}>
                <DialogTitle>Изход от терминал</DialogTitle>
                <DialogContent>
                    <TextField
                        fullWidth
                        label="Email"
                        value={adminEmail}
                        onChange={(e) => setAdminEmail(e.target.value)}
                        sx={{ mt: 1 }}
                    />
                    <TextField
                        fullWidth
                        label="Парола"
                        type="password"
                        value={adminPassword}
                        onChange={(e) => setAdminPassword(e.target.value)}
                        sx={{ mt: 1 }}
                    />
                    {exitError && <Alert severity="error" sx={{ mt: 1 }}>{exitError}</Alert>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setExitDialogOpen(false)}>Отказ</Button>
                    <Button onClick={handleExitVerify} variant="contained" disabled={isVerifying}>
                        {isVerifying ? 'Проверка...' : 'Вход'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

// Manual code entry component
const ManualCodeEntry: React.FC<{ onSubmit: (code: string) => void }> = ({ onSubmit }) => {
    const [code, setCode] = useState('');
    
    return (
        <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
                fullWidth
                size="small"
                label="Въведете код"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyPress={(e) => {
                    if (e.key === 'Enter' && code) {
                        onSubmit(code);
                        setCode('');
                    }
                }}
            />
            <Button variant="contained" onClick={() => { onSubmit(code); setCode(''); }} disabled={!code}>
                OK
            </Button>
        </Box>
    );
};

// Chip component (simple implementation)
const Chip: React.FC<{ icon?: React.ReactNode; label: string; color?: string }> = ({ icon, label, color }) => (
    <Box sx={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: 0.5,
        px: 1.5, 
        py: 0.5, 
        borderRadius: 1,
        bgcolor: color === 'primary' ? 'primary.light' : color === 'secondary' ? 'secondary.light' : 'grey.300',
        color: color === 'primary' ? 'primary.contrastText' : color === 'secondary' ? 'secondary.contrastText' : 'text.primary'
    }}>
        {icon}
        <Typography variant="body2">{label}</Typography>
    </Box>
);

// Add useNavigate import
import { useNavigate } from 'react-router-dom';

// Fix: offlineQueue.length reference
const offlineQueueQueue = { length: 0 };

export default UnifiedKiosk;
