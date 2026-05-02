import React, { useState, useEffect } from 'react';
import { 
  Typography, Card, CardContent, Box, LinearProgress, CircularProgress
} from '@mui/material';
import QrCodeIcon from '@mui/icons-material/QrCode';
import { useMutation, useQuery, gql, DocumentNode } from '@apollo/client';
import { QRCodeSVG } from 'qrcode.react';

const REGENERATE_QR_MUTATION = gql`
  mutation RegenerateQr {
    regenerateMyQrCode
  }
`;

const GET_QR_CONFIG = gql`
  query GetQrConfig {
    globalPayrollConfig {
      qrRegenIntervalMinutes
    }
  }
`;

interface MyQrCardProps {
    token: string | null;
    refetchQuery: DocumentNode; 
    variables?: Record<string, unknown>;
}

const MyQrCard: React.FC<MyQrCardProps> = ({ token, refetchQuery, variables }) => {
    const { data: configData } = useQuery(GET_QR_CONFIG);
    const [regenerateQr, { loading }] = useMutation(REGENERATE_QR_MUTATION, { 
        refetchQueries: [{ query: refetchQuery, variables: variables }] 
    });

    const intervalMinutes = configData?.globalPayrollConfig?.qrRegenIntervalMinutes || 15;
    const intervalMs = intervalMinutes * 60 * 1000;

    const [timeLeft, setTimeLeft] = useState(intervalMs);

    // Initial regeneration if token is missing
    useEffect(() => {
        if (!token && !loading) {
            regenerateQr().catch(e => console.error("Initial QR generation failed", e));
        }
    }, [token, loading, regenerateQr]);

    useEffect(() => {
        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1000) {
                    regenerateQr().catch(e => console.error("Auto-regen failed", e));
                    return intervalMs;
                }
                return prev - 1000;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [intervalMs, regenerateQr]);

    const progress = (timeLeft / intervalMs) * 100;

    return (
        <Card sx={{ 
            height: '100%', 
            borderRadius: 4, 
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)', 
            display: 'flex', 
            flexDirection: 'column', 
            position: 'relative',
            overflow: 'hidden',
            border: '2px solid',
            borderColor: 'primary.main'
        }}>
            <CardContent sx={{ textAlign: 'center', flexGrow: 1, p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                    <QrCodeIcon color="primary" sx={{ fontSize: 28 }} />
                    <Typography variant="h6" fontWeight="bold" color="primary">ВХОД</Typography>
                </Box>
                
                <Box sx={{ 
                    p: 2, 
                    bgcolor: 'white', 
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 4, 
                    border: '1px solid #eee',
                    mb: 1.5,
                    position: 'relative',
                    width: '100%',
                    maxWidth: 200,
                    aspectRatio: '1/1'
                }}>
                    {token ? (
                        <QRCodeSVG value={token} size={180} style={{ height: "auto", maxWidth: "100%", width: "100%" }} />
                    ) : (
                        <CircularProgress size={40} />
                    )}
                    {loading && (
                        <Box sx={{ 
                            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, 
                            bgcolor: 'rgba(255,255,255,0.7)', display: 'flex', 
                            alignItems: 'center', justifyContent: 'center', borderRadius: 4 
                        }}>
                            <CircularProgress size={40} />
                        </Box>
                    )}
                </Box>

                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                    {Math.ceil(timeLeft / 60000)} мин. до обновяване
                </Typography>
            </CardContent>

            <Box sx={{ width: '100%' }}>
                <LinearProgress 
                    variant="determinate" 
                    value={progress} 
                    sx={{ 
                        height: 8, 
                        bgcolor: 'rgba(0,0,0,0.05)',
                        '& .MuiLinearProgress-bar': {
                            transition: 'transform 1s linear'
                        }
                    }} 
                />
            </Box>
        </Card>
    );
};

export default MyQrCard;
