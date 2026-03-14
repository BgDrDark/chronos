import React, { useState, useEffect } from 'react';
import { getErrorMessage } from '../types';
import { 
  Box, Typography, Alert, CircularProgress, Card, CardContent, 
  FormControlLabel, FormGroup, Checkbox, Divider, Button
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import SaveIcon from '@mui/icons-material/Save';

const GET_VAPID_KEY = gql`
  query GetVapidKey {
    vapidPublicKey
  }
`;

const SUBSCRIBE_PUSH = gql`
  mutation SubscribePush($json: String!, $prefsJson: String!) {
    subscribeToPush(subscriptionJson: $json, preferencesJson: $prefsJson)
  }
`;

const PushNotificationManager: React.FC = () => {
    const { data: vapidData } = useQuery(GET_VAPID_KEY);
    const [subscribePush] = useMutation(SUBSCRIBE_PUSH);
    
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMsg, setSuccessMsg] = useState<string | null>(null);

    // Notification Preferences
    const [prefs, setPrefs] = useState({
        leaves: true,
        shifts: true,
        reminders: true,
        admin_alerts: true
    });

    const handlePrefChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setPrefs({
            ...prefs,
            [event.target.name]: event.target.checked
        });
    };

    const urlBase64ToUint8Array = (base64String: string) => {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    };

    const checkSubscription = async () => {
        if ('serviceWorker' in navigator) {
            try {
                // Use a timeout to avoid infinite waiting if SW is broken
                const registration = await Promise.race([
                    navigator.serviceWorker.ready,
                    new Promise((_, reject) => setTimeout(() => reject(new Error("Service Worker timeout")), 5000))
                ]) as ServiceWorkerRegistration;
                
                const subscription = await registration.pushManager.getSubscription();
                setIsSubscribed(!!subscription);
            } catch (e) {
                console.warn("SW Check failed:", e);
            }
        }
    };

    useEffect(() => {
        checkSubscription();
    }, []);

    const handleUpdateSubscription = async () => {
        setLoading(true);
        setError(null);
        setSuccessMsg(null);
        console.log("Starting Push Subscription process...");

        try {
            if (!('serviceWorker' in navigator)) {
                throw new Error("Вашият браузър не поддържа Service Workers.");
            }

            if (!('PushManager' in window)) {
                throw new Error("Вашият браузър не поддържа Push известия.");
            }

            console.log("Waiting for Service Worker to be ready...");
            
            let registration: ServiceWorkerRegistration | undefined;
            
            try {
                // Try to get existing registration first
                const regs = await navigator.serviceWorker.getRegistrations();
                registration = regs.find(r => r.active || r.waiting || r.installing);
                
                if (!registration) {
                    console.log("No registration found, trying manual registration...");
                    registration = await navigator.serviceWorker.register('/service-worker.js', { type: 'module' });
                }
            } catch (swErr) {
                console.warn("Manual SW registration failed, waiting for ready...", swErr);
                registration = await Promise.race([
                    navigator.serviceWorker.ready,
                    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 5000))
                ]) as ServiceWorkerRegistration;
            }

            if (!registration) {
                throw new Error("Service Worker не е открит. Опитайте да презаредите страницата или проверете дали браузърът ви поддържа PWA.");
            }
            
            console.log("Service Worker found:", registration.scope);

            let subscription = await registration.pushManager.getSubscription();

            if (!subscription) {
                console.log("No existing subscription. Requesting permission...");
                const permission = await Notification.requestPermission();
                if (permission !== 'granted') {
                    throw new Error("Разрешението за известия беше отказано от браузъра.");
                }

                const vapidPublicKey = vapidData?.vapidPublicKey;
                if (!vapidPublicKey) {
                    throw new Error("VAPID публичният ключ не е зареден от сървъра. Моля опреснете страницата.");
                }

                console.log("Subscribing to Push Manager...");
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
                });
            }

            console.log("Sending subscription to backend...");
            const { data: responseData } = await subscribePush({
                variables: { 
                    json: JSON.stringify(subscription),
                    prefsJson: JSON.stringify(prefs)
                }
            });

            if (responseData && responseData.subscribeToPush) {
                setIsSubscribed(true);
                setSuccessMsg("Абонаментът е активиран и настройките са запазени!");
                setTimeout(() => setSuccessMsg(null), 5000);
            } else {
                throw new Error("Сървърът отказа да запише абонамента.");
            }
        } catch (e) {
            console.error("Push Subscription Error:", e);
            setError(getErrorMessage(e) || "Възникна неочаквана грешка.");
        } finally {
            setLoading(false);
        }
    };

    const handleUnsubscribe = async () => {
        setLoading(true);
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            if (subscription) {
                await subscription.unsubscribe();
                setIsSubscribed(false);
                setSuccessMsg("Абонаментът е прекратен.");
            }
        } catch (e) {
            setError("Грешка при прекратяване: " + getErrorMessage(e));
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card variant="outlined" sx={{ borderRadius: 4, border: '1px solid #e0e0e0' }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <NotificationsActiveIcon color={isSubscribed ? "success" : "disabled"} />
                    <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                            Push Известия (PWA)
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            Получавайте съобщения директно на вашия телефон или браузър.
                        </Typography>
                    </Box>
                    <Button 
                        size="small" 
                        color="error" 
                        onClick={handleUnsubscribe} 
                        disabled={!isSubscribed || loading}
                    >
                        Изключи
                    </Button>
                </Box>

                <Divider sx={{ mb: 2 }} />

                <Typography variant="subtitle2" gutterBottom fontWeight="bold">Изберете какво да получавате:</Typography>
                
                <FormGroup>
                    <FormControlLabel
                        control={<Checkbox checked={prefs.leaves} onChange={handlePrefChange} name="leaves" size="small" />}
                        label={<Typography variant="body2">Одобрени / Отхвърлени отпуски</Typography>}
                    />
                    <FormControlLabel
                        control={<Checkbox checked={prefs.shifts} onChange={handlePrefChange} name="shifts" size="small" />}
                        label={<Typography variant="body2">Размяна на смени с колеги</Typography>}
                    />
                    <FormControlLabel
                        control={<Checkbox checked={prefs.reminders} onChange={handlePrefChange} name="reminders" size="small" />}
                        label={<Typography variant="body2">Напомняне за начало на смяна</Typography>}
                    />
                    <FormControlLabel
                        control={<Checkbox checked={prefs.admin_alerts} onChange={handlePrefChange} name="admin_alerts" size="small" />}
                        label={<Typography variant="body2">Админ: Нови заявки за одобрение</Typography>}
                    />
                </FormGroup>

                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 1, alignItems: 'center' }}>
                    {loading && <CircularProgress size={20} sx={{ mr: 1 }} />}
                    <Button 
                        variant="contained" 
                        startIcon={<SaveIcon />} 
                        size="small"
                        onClick={handleUpdateSubscription}
                        disabled={loading}
                    >
                        {isSubscribed ? "Запази предпочитанията" : "Абонирай се и Запази"}
                    </Button>
                </Box>

                {error && <Alert severity="error" sx={{ mt: 2, py: 0.5 }}>{error}</Alert>}
                {successMsg && <Alert severity="success" sx={{ mt: 2, py: 0.5 }}>{successMsg}</Alert>}
            </CardContent>
        </Card>
    );
};

export default PushNotificationManager;