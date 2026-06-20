import React, { useState, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { getApiUrl, fetchWithAuth } from '../utils/api';
import { getErrorMessage } from '../types';
import { 
  Container, Typography, Card, CardContent, Grid, TextField, Button, 
  Alert, Box, CircularProgress, Switch, FormControlLabel, Divider, InputAdornment,
  LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions,
  List, ListItem, ListItemButton, ListItemText, Radio, Chip, IconButton
} from '@mui/material';
import { InfoIcon } from '../components/ui/InfoIcon';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import StorageIcon from '@mui/icons-material/Storage';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import HistoryIcon from '@mui/icons-material/History';
import GoogleIcon from '@mui/icons-material/Google';
import SystemUpdateIcon from '@mui/icons-material/SystemUpdate';
import CloseIcon from '@mui/icons-material/Close';
import { useQuery, useMutation, gql } from '@apollo/client';
import AuditLogViewer from '../components/AuditLogViewer';
import ApiKeyManager from '../components/ApiKeyManager';
import WebhookManager from '../components/WebhookManager';
import MaintenanceModeSettings from '../components/MaintenanceModeSettings';
import ScheduledUpdateSettings from '../components/ScheduledUpdateSettings';
import ModuleManager from '../components/ModuleManager';
import PasswordComplexitySettings from '../components/PasswordComplexitySettings';
import { type SxProps, type Theme } from '@mui/material';
import { type ActiveSession } from '../types';

interface ValidatedTextFieldProps {
  label: string;
  value: string | number;
  onChange: (value: string | number) => void;
  tooltip?: string;
  placeholder?: string;
  error?: string;
  success?: boolean;
  required?: boolean;
  type?: 'text' | 'number' | 'email' | 'password' | 'date';
  sx?: SxProps<Theme>;
  size?: 'small' | 'medium';
  fullWidth?: boolean;
  disabled?: boolean;
}

const ValidatedTextField: React.FC<ValidatedTextFieldProps> = ({
  label, value, onChange, tooltip, placeholder, error, success,
  required, type = 'text', sx, size = 'small', fullWidth = true, disabled
}) => {
  const showError = !!error;
  const strValue = String(value);
  const showSuccess = success && !showError && strValue.length > 0;

  const endAdornment = tooltip ? (
    <InputAdornment position="end">
      <InfoIcon helpText={tooltip} />
    </InputAdornment>
  ) : undefined;
  
  return (
    <TextField
      label={label}
      value={value}
      onChange={(e) => onChange(type === 'number' ? (e.target.value.replace(/[^0-9.-]/g, '')) : e.target.value)}
      placeholder={placeholder}
      error={showError}
      helperText={error}
      required={required}
      type={type}
      size={size}
      fullWidth={fullWidth}
      disabled={disabled}
      slotProps={{
        input: { endAdornment }
      }}
      sx={{
        ...sx,
        '& .MuiOutlinedInput-root': {
          '&.Mui-error': {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'error.main',
            },
          },
          ...(showSuccess && {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'success.main',
              borderWidth: 2,
            },
          }),
        },
      }}
    />
  );
};

const SETTINGS_QUERY = gql`
  query GetSettings {
    me {
      id
      email
      username
      firstName
      lastName
      phoneNumber
      address
      egn
      birthDate
      iban
      jobTitle
      departmentName
      companyName
      role {
        name
      }
    }
  }
 `;

const GET_OFFICE_LOC_QUERY = gql`
  query GetOfficeLoc {
    officeLocation {
      latitude
      longitude
      radius
      entryEnabled
      exitEnabled
    }
  }
`;

const UPDATE_OFFICE_LOC_MUTATION = gql`
  mutation UpdateOfficeLoc($latitude: Float!, $longitude: Float!, $radius: Int!, $entryEnabled: Boolean!, $exitEnabled: Boolean!) {
    updateOfficeLocation(latitude: $latitude, longitude: $longitude, radius: $radius, entryEnabled: $entryEnabled, exitEnabled: $exitEnabled) {
      radius
    }
  }
 `;

const UPDATE_SECURITY_CONFIG = gql`
  mutation UpdateSecurityConfig($maxLoginAttempts: Int!, $lockoutMinutes: Int!) {
    updateSecurityConfig(maxLoginAttempts: $maxLoginAttempts, lockoutMinutes: $lockoutMinutes)
  }
`;

const GET_GOOGLE_CALENDAR_ACCOUNT = gql`
  query GetGoogleCalendar {
    googleCalendarAccount {
      id
      email
      isActive
      syncSettings {
        syncWorkSchedules
        syncTimeLogs
        syncLeaveRequests
        syncPublicHolidays
        privacyLevel
      }
    }
  }
`;

const UPDATE_GOOGLE_SYNC_MUTATION = gql`
  mutation UpdateGoogleSync(
    $syncWorkSchedules: Boolean!,
    $syncTimeLogs: Boolean!,
    $syncLeaveRequests: Boolean!,
    $syncPublicHolidays: Boolean!,
    $privacyLevel: String!
  ) {
    updateGoogleCalendarSettings(
      syncWorkSchedules: $syncWorkSchedules,
      syncTimeLogs: $syncTimeLogs,
      syncLeaveRequests: $syncLeaveRequests,
      syncPublicHolidays: $syncPublicHolidays,
      privacyLevel: $privacyLevel
    )
  }
`;

const DISCONNECT_GOOGLE_MUTATION = gql`
  mutation DisconnectGoogle {
    disconnectGoogleCalendar
  }
`;

const GET_ACTIVE_SESSIONS = gql`
  query GetActiveSessions {
    activeSessions {
      id
      user { email }
      ipAddress
      userAgent
      expiresAt
      lastUsedAt
      isActive
    }
  }
`;

const INVALIDATE_SESSION = gql`
  mutation InvalidateSession($sessionId: Int!) {
    invalidateUserSession(sessionId: $sessionId)
  }
`;

const GET_SESSION_SETTINGS = gql`
  query GetSessionSettings {
    sessionSettings {
      maxAgeHours
    }
  }
`;

const UPDATE_SESSION_SETTINGS = gql`
  mutation UpdateSessionSettings($maxAgeHours: Int!) {
    updateSessionSettings(maxAgeHours: $maxAgeHours)
  }
`;

const ActiveSessions: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_ACTIVE_SESSIONS);
    const [invalidate] = useMutation(INVALIDATE_SESSION);
    const { data: settingsData } = useQuery(GET_SESSION_SETTINGS);
    const [updateSettings] = useMutation(UPDATE_SESSION_SETTINGS);
    const [maxAgeHours, setMaxAgeHours] = useState(settingsData?.sessionSettings?.maxAgeHours ?? 12);
    const [saving, setSaving] = useState(false);
    const [saveMsg, setSaveMsg] = useState('');

    const handleSaveSettings = async () => {
        const hours = parseInt(maxAgeHours as any, 10);
        if (isNaN(hours) || hours < 1 || hours > 168) {
            setSaveMsg('Стойността трябва да е между 1 и 168 часа.');
            return;
        }
        setSaving(true);
        try {
            await updateSettings({ variables: { maxAgeHours: hours } });
            setSaveMsg('Настройките са запазени.');
            refetch();
            setTimeout(() => setSaveMsg(''), 3000);
        } catch (err) {
            setSaveMsg(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    const handleInvalidate = async (id: string) => {
        if (!window.confirm("Сигурни ли сте, че искате да прекратите тази сесия?")) return;
        try {
            await invalidate({ variables: { sessionId: id } });
            refetch();
        } catch (err) { alert(getErrorMessage(err)); }
    };

    if (loading) return <CircularProgress />;

    return (
        <Card sx={{ mb: 4, border: '1px solid #9c27b0' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom color="secondary.main">Активни сесии</Typography>
                <Box sx={{ mb: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Typography variant="subtitle2" gutterBottom>Максимална продължителност на сесия (часове)</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <TextField
                            type="number"
                            size="small"
                            value={maxAgeHours}
                            onChange={(e) => setMaxAgeHours(e.target.value)}
                            inputProps={{ min: 1, max: 168 }}
                            sx={{ width: 120 }}
                        />
                        <Button
                            variant="contained"
                            size="small"
                            onClick={handleSaveSettings}
                            disabled={saving}
                        >
                            {saving ? 'Запазва се...' : 'Запази'}
                        </Button>
                    </Box>
                    {saveMsg && (
                        <Alert severity={saveMsg.includes('запазени') ? 'success' : 'error'} sx={{ mt: 1 }} onClose={() => setSaveMsg('')}>
                            {saveMsg}
                        </Alert>
                    )}
                </Box>
                <Box sx={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ textAlign: 'left', borderBottom: '1px solid #ddd' }}>
                                <th style={{ padding: 8 }}>Потребител</th>
                                <th style={{ padding: 8 }}>IP</th>
                                <th style={{ padding: 8 }}>Последна активност</th>
                                <th style={{ padding: 8 }}>Действие</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data?.activeSessions.map((s: ActiveSession) => (
                                <tr key={s.id} style={{ borderBottom: '1px solid #eee' }}>
                                    <td style={{ padding: 8 }}>{s.user.email}</td>
                                    <td style={{ padding: 8 }}>{s.ipAddress || '-'}</td>
                                    <td style={{ padding: 8 }}>{s.lastUsedAt ? new Date(s.lastUsedAt).toLocaleString('bg-BG') : '-'}</td>
                                    <td style={{ padding: 8 }}>
                                        <Button size="small" color="error" onClick={() => handleInvalidate(s.id)}>
                                            Прекрати
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                            {data?.activeSessions.length === 0 && (
                                <tr><td colSpan={4} style={{ padding: 8, textAlign: 'center' }}>Няма активни сесии.</td></tr>
                            )}
                        </tbody>
                    </table>
                </Box>
            </CardContent>
        </Card>
    );
};

const GoogleCalendarSettings: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_GOOGLE_CALENDAR_ACCOUNT);
    const [updateSync, { loading: updating }] = useMutation(UPDATE_GOOGLE_SYNC_MUTATION);
    const [disconnect, { loading: disconnecting }] = useMutation(DISCONNECT_GOOGLE_MUTATION);
    const [msg, setMsg] = useState('');

    const handleToggle = async (field: string, value: string | boolean) => {
        if (!data?.googleCalendarAccount?.syncSettings) return;
        
        const s = data.googleCalendarAccount.syncSettings;
        const variables = {
            syncWorkSchedules: field === 'syncWorkSchedules' ? value : s.syncWorkSchedules,
            syncTimeLogs: field === 'syncTimeLogs' ? value : s.syncTimeLogs,
            syncLeaveRequests: field === 'syncLeaveRequests' ? value : s.syncLeaveRequests,
            syncPublicHolidays: field === 'syncPublicHolidays' ? value : s.syncPublicHolidays,
            privacyLevel: field === 'privacyLevel' ? value : s.privacyLevel
        };

        try {
            await updateSync({ variables });
            setMsg('Настройките са запазени.');
            refetch();
            setTimeout(() => setMsg(''), 3000);
        } catch (err) { alert(getErrorMessage(err)); }
    };

    const handleConnect = async () => {
        try {
            const res = await fetch(`${getApiUrl()}/auth/google/init`, {
                method: 'POST',
                credentials: 'include',
            });
            if (!res.ok) throw new Error('Failed to initialize Google auth');
            const data = await res.json();
            window.location.href = data.auth_url;
        } catch (err) {
            alert(getErrorMessage(err));
        }
    };

    const handleDisconnect = async () => {
        if (!window.confirm("Сигурни ли сте, че искате да прекъснете връзката с Google Calendar?")) return;
        try {
            await disconnect();
            refetch();
        } catch (err) { alert(getErrorMessage(err)); }
    };

    if (loading) return <CircularProgress size={24} />;

    const account = data?.googleCalendarAccount;

    return (
        <Card sx={{ mb: 4, border: '1px solid #4285F4' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#4285F4' }}>
                    <GoogleIcon /> Интеграция с Google Calendar
                </Typography>
                
                {!account ? (
                    <Box sx={{ py: 2 }}>
                        <Typography variant="body2" color="text.secondary" paragraph>
                            Свържете вашия Google календар, за да виждате графика си, отпуските и работните си часове директно в телефона си.
                        </Typography>
                        <Button 
                            variant="contained" 
                            startIcon={<GoogleIcon />} 
                            onClick={handleConnect}
                            sx={{ bgcolor: '#4285F4', '&:hover': { bgcolor: '#357ae8' } }}
                        >
                            Свържи с Google
                        </Button>
                    </Box>
                ) : (
                    <Box>
                        <Alert severity="success" sx={{ mb: 3 }} action={
                            <Button color="inherit" size="small" onClick={handleDisconnect} disabled={disconnecting}>
                                Прекъсни
                            </Button>
                        }>
                            Свързан акаунт: <strong>{account.email}</strong>
                        </Alert>

                        <Typography variant="subtitle2" gutterBottom fontWeight="bold">Какво да синхронизираме:</Typography>
                        <Grid container spacing={1}>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <FormControlLabel 
                                    control={<Switch checked={account.syncSettings.syncWorkSchedules} onChange={(e) => handleToggle('syncWorkSchedules', e.target.checked)} disabled={updating} />}
                                    label="Работни графици"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <FormControlLabel 
                                    control={<Switch checked={account.syncSettings.syncLeaveRequests} onChange={(e) => handleToggle('syncLeaveRequests', e.target.checked)} disabled={updating} />}
                                    label="Отпуски и болнични"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <FormControlLabel 
                                    control={<Switch checked={account.syncSettings.syncTimeLogs} onChange={(e) => handleToggle('syncTimeLogs', e.target.checked)} disabled={updating} />}
                                    label="Реално отработено време"
                                />
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <FormControlLabel 
                                    control={<Switch checked={account.syncSettings.syncPublicHolidays} onChange={(e) => handleToggle('syncPublicHolidays', e.target.checked)} disabled={updating} />}
                                    label="Официални празници"
                                />
                            </Grid>
                        </Grid>

                        <Divider sx={{ my: 2 }} />
                        
                        <Typography variant="subtitle2" gutterBottom fontWeight="bold">Ниво на поверителност в календара:</Typography>
                        <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                            <Button 
                                size="small" 
                                variant={account.syncSettings.privacyLevel === 'full' ? 'contained' : 'outlined'}
                                onClick={() => handleToggle('privacyLevel', 'full')}
                                disabled={updating}
                            >
                                Пълни детайли
                            </Button>
                            <Button 
                                size="small" 
                                variant={account.syncSettings.privacyLevel === 'busy_only' ? 'contained' : 'outlined'}
                                onClick={() => handleToggle('privacyLevel', 'busy_only')}
                                disabled={updating}
                            >
                                Само "Зает"
                            </Button>
                        </Box>
                        
                        {msg && <Typography color="success.main" sx={{ mt: 2 }}>{msg}</Typography>}
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

const SecuritySettings: React.FC = () => {
    const [maxAttempts, setMaxAttempts] = useState(5);
    const [lockoutMins, setLockoutMins] = useState(15);
    const [updateSecurity] = useMutation(UPDATE_SECURITY_CONFIG);
    const [msg, setMsg] = useState('');

    const handleSave = async () => {
        try {
            await updateSecurity({ variables: { maxLoginAttempts: parseInt(String(maxAttempts)), lockoutMinutes: parseInt(String(lockoutMins)) } });
            setMsg('Настройките за сигурност са запазени.');
        } catch (err) { alert(getErrorMessage(err)); }
    };

    return (
        <Card sx={{ mb: 4, border: '1px solid #d32f2f' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom color="error.main">Сигурност (Login Protection)</Typography>
                <Grid container spacing={2} alignItems="center">
                    <Grid size={{ xs: 12, sm: 5 }}>
                        <ValidatedTextField 
                            label="Макс. неуспешни опити" 
                            type="number" 
                            value={maxAttempts} 
                            onChange={(val) => setMaxAttempts(Number(val))}
                            tooltip="Брой неуспешни опити за вход преди заключване (препоръчително 3-5)"
                            placeholder="5"
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 5 }}>
                        <ValidatedTextField 
                            label="Заключване (минути)" 
                            type="number" 
                            value={lockoutMins} 
                            onChange={(val) => setLockoutMins(Number(val))}
                            tooltip="Време за заключване в минути след неуспешни опити (препоръчително 15-30)"
                            placeholder="15"
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 2 }}>
                        <Button variant="contained" color="error" fullWidth onClick={handleSave}>Запази</Button>
                    </Grid>
                </Grid>
                {msg && <Typography color="success.main" sx={{ mt: 1 }}>{msg}</Typography>}
            </CardContent>
        </Card>
    );
};

const OfficeLocationSettings: React.FC = () => {
    const { data, loading } = useQuery(GET_OFFICE_LOC_QUERY);
    const [updateLoc, { loading: updating }] = useMutation(UPDATE_OFFICE_LOC_MUTATION);
    
    const [lat, setLat] = useState('');
    const [lon, setLon] = useState('');
    const [rad, setRad] = useState('100');
    const [entryEnabled, setEntryEnabled] = useState(false);
    const [exitEnabled, setExitEnabled] = useState(false);
    const [msg, setMsg] = useState<{type: 'success'|'error', text: string} | null>(null);

    const locInitialized = useRef(false);
    React.useEffect(() => {
        if (data?.officeLocation && !locInitialized.current) {
            locInitialized.current = true;
            setLat(data.officeLocation.latitude !== 0 ? data.officeLocation.latitude.toString() : '');
            setLon(data.officeLocation.longitude !== 0 ? data.officeLocation.longitude.toString() : '');
            setRad(data.officeLocation.radius?.toString() || '100');
            setEntryEnabled(data.officeLocation.entryEnabled || false);
            setExitEnabled(data.officeLocation.exitEnabled || false);
        }
    }, [data]);

    const handleGetCurrent = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    setLat(pos.coords.latitude.toString());
                    setLon(pos.coords.longitude.toString());
                },
                (err) => alert("Грешка при вземане на локация: " + err.message)
            );
        } else {
            alert("Геолокацията не се поддържа.");
        }
    };

    const handleSave = async () => {
        try {
            await updateLoc({ 
                variables: { 
                    latitude: lat ? Number(lat) : 0, 
                    longitude: lon ? Number(lon) : 0, 
                    radius: parseInt(rad) || 100,
                    entryEnabled,
                    exitEnabled
                } 
            });
            setMsg({ type: 'success', text: 'Офис локацията е запазена.' });
        } catch (err) {
            setMsg({ type: 'error', text: getErrorMessage(err) });
        }
    };

    if (loading) return <CircularProgress />;

    return (
        <Card sx={{ mb: 4, border: '1px solid #2196f3' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom color="primary.main">Офис Локация (Geofencing)</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Ако зададете координати тук, системата ще позволява "Вход" само ако служителят се намира в посочения радиус. Оставете празно или 0, за да деактивирате проверката.
                </Typography>
                
                <Grid container spacing={2} alignItems="center">
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <ValidatedTextField
                          label="Latitude"
                          value={lat}
                          onChange={(val) => setLat(val as string)}
                          tooltip="Географска ширина (напр. 42.6977)"
                          placeholder="42.6977"
                          type="number"
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <ValidatedTextField
                          label="Longitude"
                          value={lon}
                          onChange={(val) => setLon(val as string)}
                          tooltip="Географска дължина (напр. 23.3219)"
                          placeholder="23.3219"
                          type="number"
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <ValidatedTextField
                          label="Радиус (метри)"
                          value={rad}
                          onChange={(val) => setRad(val as string)}
                          tooltip="Радиус в метри за GPS проверката (препоръчително 100-500м)"
                          placeholder="100"
                          type="number"
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <FormControlLabel 
                            control={<Switch checked={entryEnabled} onChange={(e) => setEntryEnabled(e.target.checked)} />}
                            label="Изисквай локация при Вход (Clock In)"
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <FormControlLabel 
                            control={<Switch checked={exitEnabled} onChange={(e) => setExitEnabled(e.target.checked)} />}
                            label="Изисквай локация при Изход (Clock Out)"
                        />
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <Button variant="outlined" startIcon={<LocationOnIcon />} onClick={handleGetCurrent}>
                                Вземи текуща позиция
                            </Button>
                            <Button variant="contained" onClick={handleSave} disabled={updating}>
                                Запази
                            </Button>
                        </Box>
                    </Grid>
                </Grid>
                {msg && <Alert severity={msg.type} sx={{ mt: 2 }}>{msg.text}</Alert>}
            </CardContent>
        </Card>
    );
};

const SystemSettings: React.FC = () => {
    const [uploading, setUploading] = useState(false);
    const [cutoffDate, setCutoffDate] = useState('');
    const [archiving, setArchiving] = useState(false);
    const [msg, setMsg] = useState<{type: 'success'|'error', text: string} | null>(null);

    const handleDownloadBackup = async () => {
        try {
            const res = await fetch(`${getApiUrl()}/system/backup`, {
                credentials: 'include',
            });
            if (!res.ok) throw new Error('Грешка при сваляне');
            
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chronos_backup_${new Date().toISOString()}.json`;
            a.click();
        } catch (err) { alert(getErrorMessage(err)); }
    };

    const handleRestore = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!window.confirm("ВНИМАНИЕ: Възстановяването ще изтрие ВСИЧКИ текущи данни и ще ги замени с тези от файла! Сигурни ли сте?")) {
            event.target.value = ''; // Reset input
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch(`${getApiUrl()}/system/restore`, {
                method: 'POST',
                credentials: 'include',
                body: formData
            });
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Restore failed');
            }
            
            setMsg({ type: 'success', text: 'Базата данни е възстановена успешно!' });
            alert("Възстановяването успешно! Препоръчително е да излезете и влезете отново.");
        } catch (err) {
            setMsg({ type: 'error', text: getErrorMessage(err) });
        } finally {
            setUploading(false);
            event.target.value = '';
        }
    };

    const handleArchive = async () => {
        if (!cutoffDate) return;
        if (!window.confirm(`Сигурни ли сте, че искате да ИЗТРИЕТЕ всички работни данни (смени, логове) преди ${cutoffDate}?`)) return;

        setArchiving(true);
        try {
            const res = await fetch(`${getApiUrl()}/system/archive?cutoff_date=${cutoffDate}`, {
                method: 'POST',
                credentials: 'include',
            });

            if (!res.ok) throw new Error('Archive failed');

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chronos_archive_${cutoffDate}.json`;
            a.click();
            
            setMsg({ type: 'success', text: 'Архивирането успешно! Данните са изтрити и свалени локално.' });
        } catch (err) {
            setMsg({ type: 'error', text: getErrorMessage(err) });
        } finally {
            setArchiving(false);
        }
    };

    return (
        <Card sx={{ mb: 4, border: '1px solid #607d8b' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#455a64' }}>
                    <StorageIcon /> Система и Архивиране
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Управление на резервни копия и почистване на базата данни.
                </Typography>

                {msg && <Alert severity={msg.type} sx={{ mb: 2 }}>{msg.text}</Alert>}

                <Grid container spacing={3}>
                    {/* Backup & Restore */}
                    <Grid size={{ xs: 12, md: 6 }}>
                        <Card variant="outlined">
                            <CardContent>
                                <Typography variant="subtitle1" gutterBottom fontWeight="bold">Резервно копие (Backup)</Typography>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <Button 
                                        variant="contained" 
                                        startIcon={<CloudDownloadIcon />} 
                                        onClick={handleDownloadBackup}
                                    >
                                        Свали пълен Backup
                                    </Button>
                                    
                                    <Button
                                        component="label"
                                        variant="outlined"
                                        color="error"
                                        startIcon={uploading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
                                        disabled={uploading}
                                    >
                                        Възстанови от файл
                                        <input type="file" hidden accept=".json" onChange={handleRestore} />
                                    </Button>
                                    <Typography variant="caption" color="error">
                                        * Възстановяването ще изтрие текущите данни!
                                    </Typography>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Archiving */}
                    <Grid size={{ xs: 12, md: 6 }}>
                        <Card variant="outlined">
                            <CardContent>
                                <Typography variant="subtitle1" gutterBottom fontWeight="bold">Архивиране (Почистване)</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Изтрива транзакционни данни (смени, логове) по-стари от избраната дата.
                                </Typography>
                                
                                <TextField 
                                    fullWidth 
                                    type="date" 
                                    label="Дата (всичко преди нея)" 
                                    InputLabelProps={{ shrink: true }}
                                    value={cutoffDate}
                                    onChange={(e) => setCutoffDate(e.target.value)}
                                    sx={{ mb: 2 }}
                                />
                                
                                <Button 
                                    variant="contained" 
                                    color="secondary" 
                                    fullWidth
                                    startIcon={archiving ? <CircularProgress size={20} color="inherit" /> : <HistoryIcon />}
                                    onClick={handleArchive}
                                    disabled={!cutoffDate || archiving}
                                >
                                    Архивирай и Изтрий
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
};

interface VersionInfo {
    tag: string;
    version: string;
    releaseNotes: string;
    publishedAt: string;
}

const VersionSelectorDialog: React.FC<{
    open: boolean;
    onClose: () => void;
    versions: VersionInfo[];
    currentVersion: string;
    selectedVersion: string | null;
    onSelect: (tag: string) => void;
    onDeploy: () => void;
    deploying: boolean;
    deployProgress: string;
    deployOutput: string;
    deployResult: 'success' | 'failed' | 'rolled_back' | null;
}> = ({
    open, onClose, versions, currentVersion, selectedVersion,
    onSelect, onDeploy, deploying, deployProgress, deployOutput, deployResult
}) => {
    const logEndRef = useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [deployOutput]);

    return (
        <Dialog open={open} onClose={deploying ? undefined : onClose} maxWidth="sm" fullWidth>
            <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SystemUpdateIcon />
                    {deploying ? 'Обновяване...' : deployResult ? 'Резултат' : 'Избери версия'}
                </Box>
                {!deploying && (
                    <IconButton onClick={onClose} size="small"><CloseIcon /></IconButton>
                )}
            </DialogTitle>

            <DialogContent dividers>
                {deploying && (
                    <Box>
                        <LinearProgress sx={{ mb: 2 }} />
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {deployProgress || 'Deploy в процес...'}
                        </Typography>
                        {deployOutput && (
                            <Box sx={{
                                maxHeight: 250, overflowY: 'auto', bgcolor: 'grey.900',
                                color: 'grey.100', p: 1.5, borderRadius: 1, fontFamily: 'monospace', fontSize: '0.7rem'
                            }}>
                                {deployOutput.split('\n').map((line, i) => (
                                    <Box key={i} sx={{
                                        color: line.includes('SUCCESS') ? '#4caf50' :
                                               line.includes('FAILED') || line.includes('ERROR') ? '#f44336' :
                                               line.includes('ROLLBACK') ? '#ff9800' : 'inherit'
                                    }}>{line}</Box>
                                ))}
                                <div ref={logEndRef} />
                            </Box>
                        )}
                    </Box>
                )}

                {deployResult && !deploying && (
                    <Alert severity={deployResult === 'success' ? 'success' : 'error'}>
                        {deployResult === 'success'
                            ? `Успешно обновяване до ${selectedVersion}!`
                            : deployResult === 'rolled_back'
                                ? `Deploy неуспешен — автоматичен rollback към предишна версия.`
                                : `Deploy неуспешен. Провери логовете.`}
                    </Alert>
                )}

                {!deploying && !deployResult && (
                    <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Текуща версия: <strong>{currentVersion}</strong>
                        </Typography>
                        {versions.length === 0 ? (
                            <Alert severity="info">Използвате най-новата версия.</Alert>
                        ) : (
                            <List disablePadding>
                                {versions.map((v) => (
                                    <ListItem key={v.tag} disablePadding sx={{ mb: 1 }}>
                                        <ListItemButton
                                            selected={selectedVersion === v.tag}
                                            onClick={() => onSelect(v.tag)}
                                            sx={{ borderRadius: 1, border: '1px solid', borderColor: 'divider' }}
                                        >
                                            <Radio checked={selectedVersion === v.tag} sx={{ mr: 1 }} />
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        <Typography fontWeight="bold">{v.version}</Typography>
                                                        {v.tag === versions[0]?.tag && (
                                                            <Chip label="latest" size="small" color="success" variant="outlined" />
                                                        )}
                                                    </Box>
                                                }
                                                secondary={
                                                    <Box sx={{ mt: 0.5 }}>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {v.publishedAt ? new Date(v.publishedAt).toLocaleDateString('bg-BG') : ''}
                                                        </Typography>
                                                        {v.releaseNotes && (
                                                            <Typography
                                                                variant="body2"
                                                                sx={{ whiteSpace: 'pre-wrap', mt: 0.5, maxHeight: 100, overflowY: 'auto' }}
                                                            >
                                                                {v.releaseNotes.length > 300
                                                                    ? v.releaseNotes.substring(0, 300) + '...'
                                                                    : v.releaseNotes}
                                                            </Typography>
                                                        )}
                                                    </Box>
                                                }
                                            />
                                        </ListItemButton>
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </Box>
                )}
            </DialogContent>

            <DialogActions sx={{ p: 2 }}>
                {deployResult ? (
                    <Button variant="contained" onClick={onClose}>Затвори</Button>
                ) : !deploying && versions.length > 0 ? (
                    <Button
                        variant="contained"
                        color="warning"
                        onClick={onDeploy}
                        disabled={!selectedVersion}
                        startIcon={<SystemUpdateIcon />}
                    >
                        Обнови до {selectedVersion?.replace(/^v/, '')}
                    </Button>
                ) : null}
            </DialogActions>
        </Dialog>
    );
};

const DeploymentSettings: React.FC = () => {
    const [deploying, setDeploying] = useState(false);
    const [checking, setChecking] = useState(false);
    const [msg, setMsg] = useState<{type: 'success'|'error'|'info', text: string} | null>(null);
    const [lastCheck, setLastCheck] = useState<string | null>(null);
    const [currentVersion, setCurrentVersion] = useState<string>('loading...');
    const [deployLog, setDeployLog] = useState<string[]>([]);
    const [showLog, setShowLog] = useState(false);
    const [loadingLog, setLoadingLog] = useState(false);
    const [deployProgress, setDeployProgress] = useState<string>('');
    const [deployOutput, setDeployOutput] = useState<string>('');
    const [dialogOpen, setDialogOpen] = useState(false);
    const [versions, setVersions] = useState<VersionInfo[]>([]);
    const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
    const [deployResult, setDeployResult] = useState<'success' | 'failed' | 'rolled_back' | null>(null);

    const API_URL = getApiUrl();
    const GITHUB_REPO = import.meta.env.VITE_GITHUB_REPO || 'BgDrDark/chronos';
    const FALLBACK_VERSION = '3.6.1.0';

    const isNewerVersion = (latest: string, current: string): boolean => {
        const parse = (v: string) => v.replace(/^v/, '').split('.').map(n => parseInt(n, 10) || 0);
        const a = parse(latest), b = parse(current);
        const len = Math.max(a.length, b.length);
        for (let i = 0; i < len; i++) {
            const ai = a[i] || 0, bi = b[i] || 0;
            if (ai > bi) return true;
            if (ai < bi) return false;
        }
        return false;
    };

    React.useEffect(() => {
        fetch(`${API_URL}/webhook/health`)
            .then(res => res.json())
            .then(data => setCurrentVersion(data.version || FALLBACK_VERSION))
            .catch(() => setCurrentVersion(FALLBACK_VERSION));
    }, [API_URL]);

    React.useEffect(() => {
        if (!deploying) return;

        const pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`${API_URL}/webhook/deploy-status`);
                if (res.ok) {
                    const data = await res.json();
                    setDeployProgress(data.progress || '');
                    if (data.output) setDeployOutput(data.output);
                    if (!data.is_deploying) {
                        clearInterval(pollInterval);
                        setDeploying(false);
                        if (data.status === 'success') {
                            setDeployResult('success');
                            fetch(`${API_URL}/webhook/health`)
                                .then(r => r.json())
                                .then(d => setCurrentVersion(d.version || FALLBACK_VERSION))
                                .catch(() => {});
                        } else if (data.status === 'rolled_back') {
                            setDeployResult('rolled_back');
                        } else {
                            setDeployResult('failed');
                        }
                    }
                }
            } catch {
                // Ignore polling errors
            }
        }, 2000);

        return () => clearInterval(pollInterval);
    }, [deploying, API_URL]);

    const handleFetchDeployLog = async () => {
        setShowLog(!showLog);
        if (!showLog && deployLog.length === 0) {
            setLoadingLog(true);
            try {
                const res = await fetch(`${API_URL}/webhook/deploy-log?lines=50`, { credentials: 'include' });
                if (res.ok) {
                    const data = await res.json();
                    setDeployLog(data.log || []);
                }
            } catch {
                // Ignore
            } finally {
                setLoadingLog(false);
            }
        }
    };

    const handleCheckUpdate = async () => {
        setChecking(true);
        setMsg(null);
        setDeployResult(null);

        try {
            const releasesRes = await fetch(
                `https://api.github.com/repos/${GITHUB_REPO}/releases?per_page=20`,
                { headers: { 'Accept': 'application/vnd.github.v3+json' } }
            );

            if (!releasesRes.ok) {
                setMsg({ type: 'error', text: 'GitHub API недостъпен. Проверете ръчно на GitHub.' });
                setChecking(false);
                return;
            }

            const releases = await releasesRes.json();
            const newer: VersionInfo[] = releases
                .filter((r: any) => isNewerVersion(r.tag_name?.replace(/^v/, '') || '', currentVersion))
                .map((r: any) => ({
                    tag: r.tag_name,
                    version: r.tag_name?.replace(/^v/, '') || 'unknown',
                    releaseNotes: r.body || '',
                    publishedAt: r.published_at || '',
                }));

            setVersions(newer);
            setSelectedVersion(newer.length > 0 ? newer[0].tag : null);
            setLastCheck(new Date().toLocaleString('bg-BG'));
            setDialogOpen(true);

            if (newer.length === 0) {
                setMsg({ type: 'info', text: 'Използвате най-новата версия' });
            }
        } catch (err: any) {
            setMsg({ type: 'error', text: err.message || 'Грешка при проверка' });
        } finally {
            setChecking(false);
        }
    };

    const handleDeploy = async () => {
        if (!selectedVersion) return;

        setDeploying(true);
        setDeployResult(null);
        setDeployProgress('Starting deployment...');
        setDeployOutput('');

        try {
            const res = await fetchWithAuth(`${API_URL}/webhook/deploy`, {
                method: 'POST',
                body: JSON.stringify({ version: selectedVersion })
            });

            if (!res.ok) {
                const data = await res.json();
                setMsg({ type: 'error', text: data.detail || 'Грешка при обновяване' });
                setDeploying(false);
                setDialogOpen(false);
            }
        } catch (err: any) {
            setMsg({ type: 'error', text: err.message || 'Грешка при обновяване' });
            setDeploying(false);
            setDialogOpen(false);
        }
    };

    const handleCloseDialog = () => {
        if (!deploying) {
            setDialogOpen(false);
            setDeployResult(null);
        }
    };

    return (
        <Card sx={{ mb: 4, border: '1px solid #607d8b' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#455a64' }}>
                    <SystemUpdateIcon /> Обновяване на Приложението
                </Typography>
                {msg && <Alert severity={msg.type} sx={{ mb: 2 }}>{msg.text}</Alert>}

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Typography variant="body1" fontWeight="bold">
                        Текуща версия: {currentVersion}
                    </Typography>
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={handleCheckUpdate}
                        disabled={checking || deploying}
                        startIcon={checking ? <CircularProgress size={16} /> : undefined}
                    >
                        {checking ? 'Проверка...' : 'Провери'}
                    </Button>
                </Box>

                {deploying && !dialogOpen && (
                    <Box sx={{ mb: 2 }}>
                        <LinearProgress sx={{ mb: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                            {deployProgress || 'Deploy в процес...'}
                        </Typography>
                    </Box>
                )}

                {lastCheck && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                        Последна проверка: {lastCheck}
                    </Typography>
                )}

                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={handleFetchDeployLog}
                        disabled={loadingLog}
                        startIcon={loadingLog ? <CircularProgress size={16} /> : undefined}
                    >
                        {showLog ? 'Скрий логове' : 'Покажи логове'}
                    </Button>
                </Box>

                {showLog && (
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                            Последни 50 реда от deploy.log
                        </Typography>
                        <Box sx={{
                            maxHeight: 300, overflowY: 'auto', bgcolor: 'grey.900',
                            color: 'grey.100', p: 1.5, borderRadius: 1, fontFamily: 'monospace',
                            fontSize: '0.75rem', lineHeight: 1.4,
                        }}>
                            {deployLog.length > 0 ? (
                                deployLog.map((line, i) => (
                                    <Box key={i} sx={{
                                        color: line.includes('SUCCESS') ? '#4caf50' :
                                               line.includes('FAILED') || line.includes('ERROR') ? '#f44336' :
                                               line.includes('ROLLBACK') ? '#ff9800' : 'inherit'
                                    }}>
                                        {line}
                                    </Box>
                                ))
                            ) : (
                                <Typography variant="caption" color="text.secondary">
                                    Няма налични логове
                                </Typography>
                            )}
                        </Box>
                    </Box>
                )}
            </CardContent>

            <VersionSelectorDialog
                open={dialogOpen}
                onClose={handleCloseDialog}
                versions={versions}
                currentVersion={currentVersion}
                selectedVersion={selectedVersion}
                onSelect={setSelectedVersion}
                onDeploy={handleDeploy}
                deploying={deploying}
                deployProgress={deployProgress}
                deployOutput={deployOutput}
                deployResult={deployResult}
            />
        </Card>
    );
};

const SettingsPage: React.FC = () => {
  const { data, loading, error } = useQuery(SETTINGS_QUERY);
  
  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error.message}</Alert>;
  if (!data || !data.me) return <Navigate to="/login" replace />;

  const { me } = data;
  const isAdmin = ['admin', 'super_admin'].includes(me.role.name);
  const isSuperAdmin = me.role.name === 'super_admin';

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">Настройки</Typography>

      {!isAdmin && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Персоналните настройки (парола, биометрия, фишове, известия) са преместени в <strong>Профил → Настройки и Сигурност</strong>.
        </Alert>
      )}

      {isAdmin && (
        <>
            <MaintenanceModeSettings />
            {isSuperAdmin && <ScheduledUpdateSettings />}
            
            <OfficeLocationSettings />
            
            <GoogleCalendarSettings />
            
            {isSuperAdmin && <PasswordComplexitySettings />}
            
            <SecuritySettings />
            
            <ActiveSessions />

            <Box sx={{ mb: 4 }}>
                <ApiKeyManager />
            </Box>

            <Box sx={{ mb: 4 }}>
                <WebhookManager />
            </Box>

            {isSuperAdmin && <ModuleManager />}

            <SystemSettings />

            {isSuperAdmin && <DeploymentSettings />}

            <Card sx={{ mb: 4, border: '1px solid #ff5722' }}>
                <CardContent>
                    <AuditLogViewer />
                </CardContent>
            </Card>
        </>
      )}
    </Container>
  );
};

export default SettingsPage;