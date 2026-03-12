import React, { useState } from 'react';
import { 
  Container, Typography, Card, CardContent, Grid, TextField, Button, 
  Alert, Box, CircularProgress, Switch, FormControlLabel, Divider, Tooltip
} from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import ReceiptIcon from '@mui/icons-material/Receipt';
import StorageIcon from '@mui/icons-material/Storage';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import HistoryIcon from '@mui/icons-material/History';
import GoogleIcon from '@mui/icons-material/Google';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import { useQuery, useMutation, gql } from '@apollo/client';
import { formatHours } from '../utils/formatUtils';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppTheme } from '../themeContext';
import { useCurrency } from '../currencyContext';
import { biometricService } from '../services/biometricService';
import AuditLogViewer from '../components/AuditLogViewer';
import PushNotificationManager from '../components/PushNotificationManager';
import ApiKeyManager from '../components/ApiKeyManager';
import WebhookManager from '../components/WebhookManager';
import ModuleManager from '../components/ModuleManager';
import PasswordComplexitySettings from '../components/PasswordComplexitySettings';
import { type SxProps, type Theme } from '@mui/material';
import { type ActiveSession, type Payslip } from '../types';

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
  
  return (
    <Tooltip title={tooltip || ''} arrow placement="top">
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
    </Tooltip>
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
      qrToken
      role {
        name
      }
      activeContract {
        id
        baseSalary
        contractType
        salaryInstallmentsCount
        monthlyAdvanceAmount
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

const CHANGE_PASSWORD_MUTATION = gql`
  mutation ChangePassword($oldPassword: String!, $newPassword: String!) {
    changePassword(oldPassword: $oldPassword, newPassword: $newPassword)
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

const GENERATE_PAYSLIP_MUTATION = gql`
  mutation GenerateMyPayslip($startDate: Date!, $endDate: Date!) {
    generateMyPayslip(startDate: $startDate, endDate: $endDate) {
      id
      periodStart
      periodEnd
      totalAmount
      regularAmount
      overtimeAmount
      bonusAmount
      taxAmount
      insuranceAmount
      totalRegularHours
      totalOvertimeHours
      sickDays
      leaveDays
    }
  }
`;

const ActiveSessions: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_ACTIVE_SESSIONS);
    const [invalidate] = useMutation(INVALIDATE_SESSION);

    const handleInvalidate = async (id: number) => {
        if (!window.confirm("Сигурни ли сте, че искате да прекратите тази сесия?")) return;
        try {
            await invalidate({ variables: { sessionId: id } });
            refetch();
        } catch (_err: unknown) { if (err instanceof Error) if (err instanceof Error) if (_err instanceof Error) alert(_err.message); }
    };

    if (loading) return <CircularProgress />;

    return (
        <Card sx={{ mb: 4, border: '1px solid #9c27b0' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom color="secondary.main">Активни сесии</Typography>
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
                                    <td style={{ padding: 8 }}>{new Date(s.lastUsedAt).toLocaleString('bg-BG')}</td>
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

    const handleToggle = async (field: string, value: boolean) => {
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
        } catch (_err: unknown) { if (err instanceof Error) if (err instanceof Error) if (_err instanceof Error) alert(_err.message); }
    };

    const handleConnect = () => {
        const token = localStorage.getItem('token');
        window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:14240'}/auth/google/login?token=${token}`;
    };

    const handleDisconnect = async () => {
        if (!window.confirm("Сигурни ли сте, че искате да прекъснете връзката с Google Calendar?")) return;
        try {
            await disconnect();
            refetch();
        } catch (_err: unknown) { if (err instanceof Error) if (err instanceof Error) if (_err instanceof Error) alert(_err.message); }
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
        } catch (_err: unknown) { if (err instanceof Error) if (err instanceof Error) if (_err instanceof Error) alert(_err.message); }
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

    React.useEffect(() => {
        if (data?.officeLocation) {
            setLat(data.officeLocation.latitude);
            setLon(data.officeLocation.longitude);
            setRad(data.officeLocation.radius);
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
                    latitude: parseFloat(lat), 
                    longitude: parseFloat(lon), 
                    radius: parseInt(rad),
                    entryEnabled,
                    exitEnabled
                } 
            });
            setMsg({ type: 'success', text: 'Офис локацията е запазена.' });
        } catch (_err: unknown) {
            setMsg({ type: 'error', text: (_err instanceof Error ? _err.message : "Грешка") });
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
                            <Button variant="contained" onClick={handleSave} disabled={updating || !lat || !lon}>
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
            const token = localStorage.getItem('token');
            const res = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/system/backup`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Грешка при сваляне');
            
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chronos_backup_${new Date().toISOString()}.json`;
            a.click();
        } catch (_err: unknown) { if (err instanceof Error) if (err instanceof Error) if (_err instanceof Error) alert(_err.message); }
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
            const token = localStorage.getItem('token');
            const res = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/system/restore`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Restore failed');
            }
            
            setMsg({ type: 'success', text: 'Базата данни е възстановена успешно!' });
            alert("Възстановяването успешно! Препоръчително е да излезете и влезете отново.");
        } catch (_err: unknown) {
            setMsg({ type: 'error', text: (_err instanceof Error ? _err.message : "Грешка") });
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
            const token = localStorage.getItem('token');
            const res = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/system/archive?cutoff_date=${cutoffDate}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error('Archive failed');

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chronos_archive_${cutoffDate}.json`;
            a.click();
            
            setMsg({ type: 'success', text: 'Архивирането успешно! Данните са изтрити и свалени локално.' });
        } catch (_err: unknown) {
            setMsg({ type: 'error', text: (_err instanceof Error ? _err.message : "Грешка") });
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

const SettingsPage: React.FC = () => {
  const { data, loading, error } = useQuery(SETTINGS_QUERY);
  const { mode, toggleTheme, dashboardConfig, toggleDashboardWidget } = useAppTheme();
  const { currency } = useCurrency(); // Get global currency
  const location = useLocation();
  const navigate = useNavigate();
  
  const [forcePasswordChange, setForcePasswordChange] = useState(false);
  const passwordChangeSectionRef = React.useRef<HTMLDivElement>(null);

  // Check for force_password_change query parameter
  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('force_password_change') === 'true') {
      setForcePasswordChange(true);
      // Scroll to password change section
      if (passwordChangeSectionRef.current) {
        passwordChangeSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      // Clear the query parameter from URL
      navigate(location.pathname, { replace: true });
    }
  }, [location, navigate]);
  
  // Password State
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<{type: 'success'|'error', text: string} | null>(null);
  const [changePassword] = useMutation(CHANGE_PASSWORD_MUTATION);

  // Biometric State
  const [biometricLoading, setBiometricLoading] = useState(false);
  const [biometricMsg, setBiometricMsg] = useState<{type: 'success'|'error', text: string} | null>(null);

  const handleRegisterBiometric = async () => {
    setBiometricLoading(true);
    setBiometricMsg(null);
    try {
      await biometricService.registerBiometrics("Моят телефон");
      setBiometricMsg({ type: 'success', text: 'Биометрията е регистрирана успешно!' });
    } catch (_err: unknown) {
      setBiometricMsg({ type: 'error', text: (_err instanceof Error ? _err.message : "Грешка") || 'Грешка при регистрация' });
    } finally {
      setBiometricLoading(false);
    }
  };

  // Payslip State
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [payslipResult, setPayslipResult] = useState<Payslip | null>(null);
  const [generatePayslip] = useMutation(GENERATE_PAYSLIP_MUTATION);

  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'Паролите не съвпадат' });
      return;
    }
    try {
      await changePassword({ variables: { oldPassword, newPassword } });
      setPasswordMsg({ type: 'success', text: 'Паролата е променена успешно' });
      setOldPassword(''); setNewPassword(''); setConfirmPassword('');
    } catch (_err: unknown) {
      setPasswordMsg({ type: 'error', text: (_err instanceof Error ? _err.message : "Грешка") });
    }
  };

  const handleGeneratePayslip = async () => {
    try {
      const res = await generatePayslip({ variables: { startDate, endDate } });
      setPayslipResult(res.data.generateMyPayslip);
    } catch (_err: unknown) {
      if (err instanceof Error) if (_err instanceof Error) alert(_err.message);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error.message}</Alert>;
  if (!data || !data.me) return <Alert severity="warning">Няма данни за потребителя.</Alert>;

  const { me } = data;
  const isAdmin = ['admin', 'super_admin'].includes(me.role.name);
  const isSuperAdmin = me.role.name === 'super_admin';

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">Настройки</Typography>

      {/* 1. Настройки на таблото */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Настройки на таблото</Typography>
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={mode === 'dark'}
                  onChange={toggleTheme}
                />
              }
              label="Тъмен режим (Dark Mode)"
            />
          </Box>
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={dashboardConfig.showChart}
                  onChange={() => toggleDashboardWidget('showChart')}
                />
              }
              label="Покажи графика с активност"
            />
          </Box>
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={dashboardConfig.showWeeklyTable}
                  onChange={() => toggleDashboardWidget('showWeeklyTable')}
                />
              }
              label="Покажи детайлна седмична таблица"
            />
          </Box>
          <Box sx={{ mt: 3 }}>
            <PushNotificationManager />
          </Box>
        </CardContent>
      </Card>

      {/* Останалите админ настройки */}
      {isAdmin && (
        <>
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

            <Card sx={{ mb: 4, border: '1px solid #ff5722' }}>
                <CardContent>
                    <AuditLogViewer />
                </CardContent>
            </Card>
        </>
      )}

      {/* 4. Смяна на парола */}
      <Card sx={{ mb: 4 }} ref={passwordChangeSectionRef}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Смяна на парола</Typography>
          {forcePasswordChange && (
            <Alert severity="warning" sx={{ mb: 2 }}>
                Моля, сменете вашата парола, за да отговаря на новите изисквания за сигурност.
            </Alert>
          )}
          {passwordMsg && <Alert severity={passwordMsg.type} sx={{ mb: 2 }}>{passwordMsg.text}</Alert>}
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <TextField 
                fullWidth type="password" label="Текуща парола" 
                value={oldPassword} onChange={e => setOldPassword(e.target.value)} 
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                fullWidth type="password" label="Нова парола" 
                value={newPassword} onChange={e => setNewPassword(e.target.value)} 
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                fullWidth type="password" label="Потвърди парола" 
                value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} 
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Button variant="contained" onClick={handlePasswordChange}>Промени парола</Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 4.1. Регистрация на биометрия */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <FingerprintIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
            Биометрия (Passkey)
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Регистрирайте вашия пръстов отпечатък или FaceID за по-безопасен и бърз вход.
          </Typography>
          {biometricMsg && (
            <Alert severity={biometricMsg.type} sx={{ mb: 2 }} onClose={() => setBiometricMsg(null)}>
              {biometricMsg.text}
            </Alert>
          )}
          <Button 
            variant="outlined" 
            startIcon={<FingerprintIcon />}
            onClick={handleRegisterBiometric}
            disabled={biometricLoading}
          >
            {biometricLoading ? 'Регистриране...' : 'Регистрирай биометрия'}
          </Button>
        </CardContent>
      </Card>

      {/* 5. Фиш за заплата */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Генериране на фиш</Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, sm: 5 }}>
              <TextField 
                fullWidth type="date" label="От дата" InputLabelProps={{ shrink: true }}
                value={startDate} onChange={e => setStartDate(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 5 }}>
              <TextField 
                fullWidth type="date" label="До дата" InputLabelProps={{ shrink: true }}
                value={endDate} onChange={e => setEndDate(e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 2 }}>
              <Button variant="contained" fullWidth onClick={handleGeneratePayslip}>Генерирай</Button>
            </Grid>
          </Grid>

          {payslipResult && (
             <Box sx={{ mt: 3, p: 3, bgcolor: 'background.paper', borderRadius: 3, border: '1px solid #e0e0e0', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <ReceiptIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6" fontWeight="bold">Детайлен отчет</Typography>
                </Box>
                
                <Grid container spacing={2}>
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="text.secondary">Редовни часове:</Typography>
                        <Typography fontWeight="bold">{formatHours(payslipResult.totalRegularHours)}</Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="text.secondary">Сума (Редовни):</Typography>
                        <Typography fontWeight="bold">{parseFloat(payslipResult.regularAmount).toFixed(2)} {currency}</Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="error">Извънреден труд:</Typography>
                        <Typography fontWeight="bold" color="error">{formatHours(payslipResult.totalOvertimeHours)}</Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="error">Сума (Извънредни):</Typography>
                        <Typography fontWeight="bold" color="error">{parseFloat(payslipResult.overtimeAmount).toFixed(2)} {currency}</Typography>
                    </Grid>
                    
                    <Grid size={{ xs: 12 }}><Divider sx={{ my: 1 }} /></Grid>
                    
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="warning.dark">Бонуси:</Typography>
                        <Typography fontWeight="bold">+{parseFloat(payslipResult.bonusAmount).toFixed(2)} {currency}</Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="text.secondary">Отпуск / Болнични:</Typography>
                        <Typography fontWeight="medium">{payslipResult.leaveDays} д. / {payslipResult.sickDays} д.</Typography>
                    </Grid>
                    
                    <Grid size={{ xs: 12 }}><Divider sx={{ my: 1 }} /></Grid>
                    
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="error.main">Осигуровки:</Typography>
                        <Typography fontWeight="bold" color="error.main">-{parseFloat(payslipResult.insuranceAmount).toFixed(2)} {currency}</Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                        <Typography variant="body2" color="error.main">Данък (ДДФЛ):</Typography>
                        <Typography fontWeight="bold" color="error.main">-{parseFloat(payslipResult.taxAmount).toFixed(2)} {currency}</Typography>
                    </Grid>
                </Grid>

                <Box sx={{ mt: 3, p: 2, bgcolor: 'success.light', color: 'white', borderRadius: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2" sx={{ opacity: 0.9 }}>ОБЩО ЗА ПОЛУЧАВАНЕ (НЕТО)</Typography>
                    <Typography variant="h4" fontWeight="bold">{parseFloat(payslipResult.totalAmount).toFixed(2)} {currency}</Typography>
                </Box>
                
                <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Button 
                        variant="outlined" 
                        size="small"
                        onClick={async () => {
                            try {
                                const token = localStorage.getItem('token');
                                const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:14240'}/export/payslip/${payslipResult.id}/pdf`, {
                                    headers: { 'Authorization': `Bearer ${token}` }
                                });
                                if (!res.ok) throw new Error('Failed');
                                const blob = await res.blob();
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `payslip_${payslipResult.id}.pdf`;
                                a.click();
                            } catch { alert('Грешка при сваляне'); }
                        }}
                    >
                        Изтегли PDF
                    </Button>
                </Box>
             </Box>
          )}
        </CardContent>
      </Card>

    </Container>
  );
};

export default SettingsPage;