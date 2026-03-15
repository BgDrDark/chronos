import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from "html5-qrcode";
import { 
    Box, Typography, Paper, Button, Container, Dialog, 
    DialogTitle, DialogContent, DialogActions, TextField, Alert, Avatar 
} from '@mui/material';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import LockIcon from '@mui/icons-material/Lock';
import { useNavigate } from 'react-router-dom';
import { getApiUrl } from '../utils/api';

const KioskPage: React.FC = () => {
    const [scanResult, setScanResult] = useState<{ 
        status: 'success' | 'error', 
        message: string, 
        user?: string, 
        profilePicture?: string 
    } | null>(null);
    const [isScanning, setIsScanning] = useState(true);
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    
    // Exit Lock State
    const [exitDialogOpen, setExitDialogOpen] = useState(false);
    const [adminEmail, setAdminEmail] = useState('');
    const [adminPassword, setAdminPassword] = useState('');
    const [exitError, setExitError] = useState<string | null>(null);
    const [isVerifying, setIsVerifying] = useState(false);

    const navigate = useNavigate();
    const isScanningRef = useRef(isScanning);
    const setIsScanningRef = useRef(setIsScanning);
    const setScanResultRef = useRef(setScanResult);
    const scannerRef = useRef<Html5QrcodeScanner | null>(null);
    isScanningRef.current = isScanning;
    setIsScanningRef.current = setIsScanning;
    setScanResultRef.current = setScanResult;

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const response = await fetch(getApiUrl('kiosk/config'));
                const data = await response.json();
                if (data.background_image) {
                    setBackgroundImage(getApiUrl(`uploads/${data.background_image}`));
                }
            } catch (error) {
                console.error('Failed to fetch config:', error);
            }
        };
        fetchConfig();
    }, []);

    const onScanSuccess = useCallback(async (decodedText: string) => {
        if (!isScanningRef.current) return;
        
        if (scannerRef.current) {
            scannerRef.current.pause();
        }
        setIsScanningRef.current(false);

        try {
            const response = await fetch(getApiUrl('kiosk/scan'), {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Kiosk-Secret': 'super-secret-kiosk-key' // Replace with correct secret
                },
                body: JSON.stringify({ qr_token: decodedText, action: 'auto' })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                setScanResultRef.current({ 
                    status: 'success', 
                    message: data.message, 
                    user: data.user,
                    profilePicture: data.profile_picture
                });
                new Audio('/success.mp3').play().catch(() => {}); 
            } else {
                setScanResultRef.current({ status: 'error', message: data.detail || 'Грешка при сканиране' });
                new Audio('/error.mp3').play().catch(() => {});
            }
        } catch {
            setScanResultRef.current({ status: 'error', message: "Мрежова грешка" });
        }

        setTimeout(() => {
            setScanResultRef.current(null);
            setIsScanningRef.current(true);
            if (scannerRef.current) {
                scannerRef.current.resume();
            }
        }, 4000);
    }, []);

    const onScanFailure = () => {
        // Ignored
    };

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

    useEffect(() => {
        const scanner = new Html5QrcodeScanner(
            "reader",
            { 
                fps: 5, 
                qrbox: { width: 250, height: 250 },
                formatsToSupport: [ Html5QrcodeSupportedFormats.QR_CODE ]
            },
            false
        );
        
        scanner.render(onScanSuccess, onScanFailure);
        scannerRef.current = scanner;

        return () => {
            scanner.clear().catch(error => {
                console.error("Failed to clear html5QrcodeScanner. ", error);
            });
        };
    }, [onScanSuccess]);

    const defaultBg = 'url(https://images.unsplash.com/photo-1497215728101-856f4ea42174?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80)';

    return (
        <Box sx={{ 
            height: '100vh', 
            width: '100vw',
            backgroundImage: backgroundImage ? `url(${backgroundImage})` : defaultBg,
            backgroundRepeat: 'no-repeat',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            p: 3,
            position: 'relative'
        }}>
            {/* Dark Overlay for better contrast */}
            <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', bgcolor: 'rgba(0,0,0,0.4)', zIndex: 0 }} />

            <Container maxWidth="sm" sx={{ position: 'relative', zIndex: 1 }}>
                <Paper sx={{ p: 3, borderRadius: 4, bgcolor: 'rgba(45, 45, 45, 0.85)', backdropFilter: 'blur(10px)', color: 'white', textAlign: 'center', mb: 4 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2, gap: 1 }}>
                        <AccessTimeIcon color="primary" sx={{ fontSize: 40 }} />
                        <Typography variant="h4" fontWeight="bold">ВХОД / ИЗХОД</Typography>
                    </Box>
                    <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                        Моля, сканирайте своя QR код пред камерата.
                    </Typography>
                </Paper>

                <Box sx={{ 
                    overflow: 'hidden', 
                    borderRadius: 4, 
                    border: '4px solid rgba(255,255,255,0.2)', 
                    bgcolor: 'black',
                    '& #reader': { border: 'none !important' }
                }}>
                    <div id="reader" style={{ width: '100%' }}></div>
                </Box>

                {scanResult && (
                    <Paper sx={{ 
                        position: 'fixed', 
                        top: 0, left: 0, right: 0, bottom: 0,
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        zIndex: 9999,
                        bgcolor: scanResult.status === 'success' ? 'rgba(27, 94, 32, 0.95)' : 'rgba(183, 28, 28, 0.95)',
                        backdropFilter: 'blur(15px)',
                        color: 'white',
                        animation: 'fadeIn 0.3s ease-out',
                        '@keyframes fadeIn': { from: { opacity: 0 }, to: { opacity: 1 } }
                    }}>
                        {scanResult.status === 'success' ? (
                            <>
                                <Avatar 
                                    src={scanResult.profilePicture ? getApiUrl(`uploads/${scanResult.profilePicture}`) : undefined} 
                                    sx={{ width: 300, height: 300, mb: 4, border: '10px solid white', boxShadow: 10 }}
                                >
                                    {scanResult.user?.charAt(0)}
                                </Avatar>
                                <Typography variant="h2" fontWeight="900" gutterBottom align="center">
                                    {scanResult.message}
                                </Typography>
                                <Typography variant="h4" sx={{ opacity: 0.9 }}>
                                    {scanResult.user}
                                </Typography>
                                <CheckCircleIcon sx={{ fontSize: 120, mt: 4, color: '#a5d6a7' }} />
                            </>
                        ) : (
                            <>
                                <ErrorIcon sx={{ fontSize: 150, mb: 4, color: '#ef9a9a' }} />
                                <Typography variant="h3" fontWeight="900" gutterBottom align="center">
                                    ГРЕШКА
                                </Typography>
                                <Typography variant="h4" align="center" sx={{ px: 4 }}>
                                    {scanResult.message}
                                </Typography>
                                <Button 
                                    variant="contained" 
                                    size="large"
                                    onClick={() => setScanResult(null)}
                                    sx={{ mt: 6, bgcolor: 'white', color: '#b71c1c', fontWeight: 'bold', '&:hover': { bgcolor: '#f5f5f5' } }}
                                >
                                    Опитай отново
                                </Button>
                            </>
                        )}
                    </Paper>
                )}
                
                <Box sx={{ mt: 4, textAlign: 'center' }}>
                    <Button 
                        variant="outlined"
                        sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.5)', bgcolor: 'rgba(0,0,0,0.3)', '&:hover': { borderColor: 'white', bgcolor: 'rgba(0,0,0,0.5)' } }}
                        onClick={handleExitAttempt} 
                        startIcon={<LockIcon />}
                    >
                        Изход от режим Терминал
                    </Button>
                </Box>

                <Dialog open={exitDialogOpen} onClose={() => setExitDialogOpen(false)}>
                    <DialogTitle sx={{ textAlign: 'center' }}>Изисква се администратор</DialogTitle>
                    <DialogContent>
                        <Typography variant="body2" sx={{ mb: 2 }}>
                            Въведете администраторски данни, за да излезете от режима на терминала.
                        </Typography>
                        <TextField
                            fullWidth
                            label="Администраторски имейл"
                            margin="normal"
                            value={adminEmail}
                            onChange={(e) => setAdminEmail(e.target.value)}
                        />
                        <TextField
                            fullWidth
                            label="Парола"
                            type="password"
                            margin="normal"
                            value={adminPassword}
                            onChange={(e) => setAdminPassword(e.target.value)}
                        />
                        {exitError && <Alert severity="error" sx={{ mt: 2 }}>{exitError}</Alert>}
                    </DialogContent>
                    <DialogActions sx={{ p: 3 }}>
                        <Button onClick={() => setExitDialogOpen(false)} color="inherit">Отказ</Button>
                        <Button 
                            onClick={handleVerifyExit} 
                            variant="contained" 
                            color="primary"
                            disabled={isVerifying || !adminEmail || !adminPassword}
                        >
                            {isVerifying ? 'Проверка...' : 'Отключи'}
                        </Button>
                    </DialogActions>
                </Dialog>
            </Container>
        </Box>
    );
};

export default KioskPage;
