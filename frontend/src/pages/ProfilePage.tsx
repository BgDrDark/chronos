import React, { useState } from 'react';
import { 
  Container, Typography, Grid, Card, CardContent, Avatar, Box, 
  Chip, Tab, Tabs, List, ListItem, ListItemIcon, ListItemText,
  Paper, CircularProgress, Alert, IconButton, Divider, TextField, Button,
  Dialog, DialogTitle, DialogContent, DialogActions,
  FormControlLabel, Switch, MenuItem
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import { useParams } from 'react-router-dom';
import PersonIcon from '@mui/icons-material/Person';
import BusinessIcon from '@mui/icons-material/Business';
import BadgeIcon from '@mui/icons-material/Badge';
import EmailIcon from '@mui/icons-material/Email';
import EventAvailableIcon from '@mui/icons-material/EventAvailable';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import DescriptionIcon from '@mui/icons-material/Description';
import ContractIcon from '@mui/icons-material/Assignment';
import SettingsIcon from '@mui/icons-material/Settings';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import KeyIcon from '@mui/icons-material/Key';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import ReceiptIcon from '@mui/icons-material/Receipt';
import PaidIcon from '@mui/icons-material/Paid';
import axios from 'axios';
import { useCurrency } from '../currencyContext';
import { useAppTheme } from '../themeContext';
import { formatDate } from '../utils/dateUtils';
import { getApiUrl } from '../utils/api';
import { formatHours } from '../utils/formatUtils';
import { getErrorMessage } from '../types';
import PushNotificationManager from '../components/PushNotificationManager';
import MyQrCard from '../components/MyQrCard';
import DocumentManager from '../components/DocumentManager';
import ContractDossier from '../components/ContractDossier';
import { biometricService } from '../services/biometricService';
import { type Payslip } from '../types';

const GET_USER_PROFILE =     gql`
  query GetUserProfile($id: Int) {
    user(id: $id) {
      id
      email
      firstName
      lastName
      phoneNumber
      address
      egn
      birthDate
      iban
      cardNumber
      pinExists
      jobTitle
      departmentName
      companyName
      createdAt
      qrToken
      profilePicture
      role { name }
      leaveBalance {
        totalDays
        usedDays
      }
      payrolls {
        monthlySalary
        hourlyRate
        currency
      }
      activeContract {
        id
        contractNumber
        contractType
        startDate
        endDate
        baseSalary
        salaryInstallmentsCount
        monthlyAdvanceAmount
        positionTitle
        department {
          id
          name
        }
      }
    }
    me {
      id
      role { name }
    }
  }
`;

const CHANGE_PASSWORD_MUTATION = gql`
  mutation ChangePassword($oldPassword: String!, $newPassword: String!) {
    changePassword(oldPassword: $oldPassword, newPassword: $newPassword)
  }
`;

const REISSUE_PIN_MUTATION = gql`
  mutation ReissuePin($userId: Int!) {
    reissuePin(userId: $userId)
  }
`;

const REVEAL_PIN_MUTATION = gql`
  mutation RevealPin($password: String!) {
    revealPin(password: $password)
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
      leaveDays
      sickDays
    }
  }
`;

const GET_MY_PAYMENT_HISTORY = gql`
  query MyPaymentHistory($year: Int) {
    myPaymentHistory(year: $year) {
      id
      amount
      paidAt
      payslip {
        id
        totalAmount
        grossSalary
        periodStart
        periodEnd
        regularAmount
        overtimeAmount
        bonusAmount
        taxAmount
        insuranceAmount
      }
    }
  }
`;

const PaymentHistorySection: React.FC<{ userId: number }> = ({ userId }) => {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const { data, loading } = useQuery(GET_MY_PAYMENT_HISTORY, {
    variables: { year: selectedYear },
  });
  const { currency } = useCurrency();

  const payments = data?.myPaymentHistory || [];
  const totalForYear = payments.reduce((sum: number, p: any) => sum + (p.amount || 0), 0);

  if (loading) return <CircularProgress />;

  return (
    <Card variant="outlined" sx={{ borderRadius: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PaidIcon color="primary" /> История на плащанията
          </Typography>
          <TextField
            select
            size="small"
            label="Година"
            value={selectedYear}
            onChange={e => setSelectedYear(parseInt(e.target.value))}
            sx={{ width: 120 }}
          >
            {[currentYear, currentYear - 1, currentYear - 2, currentYear - 3].map(year => (
              <MenuItem key={year} value={year}>{year}</MenuItem>
            ))}
          </TextField>
        </Box>

        <Box sx={{ mb: 3, p: 2, bgcolor: 'success.light', color: 'white', borderRadius: 2, textAlign: 'center' }}>
          <Typography variant="caption" sx={{ opacity: 0.9 }}>ОБЩО ПОЛУЧЕНО ЗА {selectedYear}</Typography>
          <Typography variant="h5" fontWeight="bold">{totalForYear.toFixed(2)} {currency}</Typography>
        </Box>

        {payments.length === 0 ? (
          <Alert severity="info">Няма намерени плащания за {selectedYear} г.</Alert>
        ) : (
          <List>
            {payments.map((payment: any) => (
              <React.Fragment key={payment.id}>
                <ListItem>
                  <ListItemIcon>
                    <ReceiptIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`${formatDate(payment.payslip?.periodStart)} - ${formatDate(payment.payslip?.periodEnd)}`}
                    secondary={`Платено на: ${formatDate(payment.paidAt)}`}
                  />
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="h6" color="success.main" fontWeight="bold">
                      {Number(payment.amount).toFixed(2)} {currency}
                    </Typography>
                    {payment.payslip && (
                      <Typography variant="caption" color="text.secondary">
                        Бруто: {Number(payment.payslip.grossSalary).toFixed(2)} {currency}
                      </Typography>
                    )}
                  </Box>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

const PersonalDataSection: React.FC<{ user: any }> = ({ user }) => {
    const maskData = (val: string, showFirst: number = 4) => {
        if (!val) return '—';
        if (val.length <= showFirst) return val;
        return val.slice(0, showFirst) + '*'.repeat(val.length - showFirst);
    };

    return (
        <Card sx={{ mb: 3, borderRadius: 3, bgcolor: 'rgba(0,0,0,0.02)', border: '1px solid #e0e0e0' }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                    <PersonIcon color="primary" />
                    <Typography variant="h6" fontWeight="bold">Лични данни (Защитени)</Typography>
                </Box>
                <Grid container spacing={3}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="caption" color="text.secondary">Име и Фамилия</Typography>
                        <Typography variant="body1" fontWeight="medium">{user.firstName} {user.lastName}</Typography>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="caption" color="text.secondary">ЕГН</Typography>
                        <Typography variant="body1" fontWeight="medium">{maskData(user.egn, 4)}</Typography>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="caption" color="text.secondary">Телефон</Typography>
                        <Typography variant="body1" fontWeight="medium">{user.phoneNumber || '—'}</Typography>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="caption" color="text.secondary">Дата на раждане</Typography>
                        <Typography variant="body1" fontWeight="medium">{user.birthDate || '—'}</Typography>
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                        <Typography variant="caption" color="text.secondary">Адрес</Typography>
                        <Typography variant="body1" fontWeight="medium">{user.address || '—'}</Typography>
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                        <Typography variant="caption" color="text.secondary">Банкова сметка (IBAN)</Typography>
                        <Typography variant="body1" fontWeight="medium" sx={{ fontFamily: 'monospace' }}>
                            {maskData(user.iban, 4)}
                        </Typography>
                    </Grid>
                </Grid>

                {user.activeContract && (
                    <>
                        <Divider sx={{ my: 3 }} />
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                            <AccountBalanceWalletIcon color="primary" />
                            <Typography variant="h6" fontWeight="bold">Трудов договор</Typography>
                        </Box>
                        <Grid container spacing={3}>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography variant="caption" color="text.secondary">Номер на договор</Typography>
                                <Typography variant="body1" fontWeight="medium">
                                    {user.activeContract.contractNumber || '—'}
                                </Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography variant="caption" color="text.secondary">Тип договор</Typography>
                                <Typography variant="body1">
                                    {user.activeContract.contractType === 'full_time' ? 'Пълно работно време' : 
                                     user.activeContract.contractType === 'part_time' ? 'Непълно работно време' : 'Граждански/Друг'}
                                </Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography variant="caption" color="text.secondary">Период</Typography>
                                <Typography variant="body1">
                                    {user.activeContract.startDate ? formatDate(user.activeContract.startDate) : '—'}
                                    {user.activeContract.endDate && ` - ${formatDate(user.activeContract.endDate)}`}
                                </Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography variant="caption" color="text.secondary">Длъжност</Typography>
                                <Typography variant="body1" fontWeight="medium">
                                    {user.activeContract.positionTitle || user.activeContract.position?.title || '—'}
                                </Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography variant="caption" color="text.secondary">Отдел</Typography>
                                <Typography variant="body1" fontWeight="medium">
                                    {user.activeContract.department?.name || '—'}
                                </Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography variant="caption" color="text.secondary">Основна заплата (Бруто)</Typography>
                                <Typography variant="body1" fontWeight="bold" color="primary">
                                    {user.activeContract.baseSalary ? `${parseFloat(user.activeContract.baseSalary).toFixed(2)} лв.` : '—'}
                                </Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 6 }}>
                                <Typography variant="caption" color="text.secondary">Плащания (Вноски)</Typography>
                                <Typography variant="body1">{user.activeContract.salaryInstallmentsCount} вноски / месец</Typography>
                            </Grid>
                        </Grid>
                    </>
                )}
            </CardContent>
        </Card>
    );
};

const ProfilePage: React.FC = () => {
    const { id } = useParams<{ id?: string }>();
    const userId = id ? parseInt(id) : undefined;
    const { currency } = useCurrency();
    const { mode, toggleTheme, dashboardConfig, toggleDashboardWidget } = useAppTheme();
    const [activeTab, setActiveTab] = useState(0);
    const [uploading, setUploading] = useState(false);

    // Password state
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [passwordMsg, setPasswordMsg] = useState<{type: 'success'|'error', text: string} | null>(null);
    const [changePassword] = useMutation(CHANGE_PASSWORD_MUTATION);

    // Biometric state
    const [biometricLoading, setBiometricLoading] = useState(false);
    const [biometricMsg, setBiometricMsg] = useState<{type: 'success'|'error', text: string} | null>(null);

    // PIN state
    const [pinMsg, setPinMsg] = useState<{type: 'success'|'error', text: string} | null>(null);
    const [reissuePin] = useMutation(REISSUE_PIN_MUTATION);
    const [revealedPin, setRevealedPin] = useState<string | null>(null);
    const [pinDialogOpen, setPinDialogOpen] = useState(false);
    const [pinPassword, setPinPassword] = useState('');
    const [revealPin] = useMutation(REVEAL_PIN_MUTATION);

    // Payslip state
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [payslipResult, setPayslipResult] = useState<Payslip | null>(null);
    const [generatePayslip] = useMutation(GENERATE_PAYSLIP_MUTATION);

    const { data, loading, error, refetch } = useQuery(GET_USER_PROFILE, {
        variables: { id: userId },
        fetchPolicy: 'network-only'
    });

    const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const apiUrl = import.meta.env.VITE_API_URL 
                ? (import.meta.env.VITE_API_URL.endsWith('/') ? import.meta.env.VITE_API_URL : `${import.meta.env.VITE_API_URL}/`)
                : '';
            const url = apiUrl ? `${apiUrl}auth/users/me/avatar` : '/auth/users/me/avatar';
            await axios.post(url, formData, {
                headers: { 
                    'Content-Type': 'multipart/form-data',
                },
                withCredentials: true,
            });
            refetch();
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } } };
            alert(error.response?.data?.detail || "Грешка при качване");
        } finally {
            setUploading(false);
        }
    };

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

    const handleRegisterBiometric = async () => {
        setBiometricLoading(true);
        setBiometricMsg(null);
        try {
            await biometricService.registerBiometrics("Моят телефон");
            setBiometricMsg({ type: 'success', text: 'Биометрията е регистрирана успешно!' });
        } catch (err) {
            setBiometricMsg({ type: 'error', text: getErrorMessage(err) || 'Грешка при регистрация' });
        } finally {
            setBiometricLoading(false);
        }
    };

    const handleReissuePin = async () => {
        try {
            const uid = data?.user?.id;
            if (!uid) return;
            const res = await reissuePin({ variables: { userId: uid } });
            setPinMsg({ type: 'success', text: `Вашият нов PIN е: ${res.data.reissuePin}. Запомнете го!` });
            setRevealedPin(res.data.reissuePin);
            setTimeout(() => setRevealedPin(null), 30000);
            refetch();
        } catch (err) {
            setPinMsg({ type: 'error', text: getErrorMessage(err) });
        }
    };

    const handleRevealPin = async () => {
        try {
            const res = await revealPin({ variables: { password: pinPassword } });
            setRevealedPin(res.data.revealPin);
            setPinDialogOpen(false);
            setPinPassword('');
            setTimeout(() => setRevealedPin(null), 30000);
        } catch (err) {
            setPinMsg({ type: 'error', text: getErrorMessage(err) });
            setPinDialogOpen(false);
            setPinPassword('');
        }
    };

    const handleGeneratePayslip = async () => {
        try {
            const res = await generatePayslip({ variables: { startDate, endDate } });
            setPayslipResult(res.data.generateMyPayslip);
        } catch (err) {
            alert(getErrorMessage(err));
        }
    };

    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>;
    if (error) return <Alert severity="error">{error.message}</Alert>;

    const user = data.user;
    const isOwnProfile = data.me.id === user.id;
    const isAdmin = ['admin', 'super_admin'].includes(data.me.role.name);

    const canSeeFinance = isOwnProfile || isAdmin;

    const paymentsTabIndex = 3;
    const settingsTabIndex = canSeeFinance ? 4 : 3;

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
            {/* Header / Avatar Section */}
            <Paper sx={{ p: 4, borderRadius: 4, mb: 4, background: 'linear-gradient(135deg, #3f51b5 0%, #1a237e 100%)', color: 'white' }}>
                <Grid container spacing={3} alignItems="center">
                    <Grid>
                        <Box sx={{ position: 'relative' }}>
                            <Avatar 
                                src={user.profilePicture ? `${getApiUrl()}/uploads/${user.profilePicture}` : undefined}
                                sx={{ width: 120, height: 120, bgcolor: 'secondary.main', fontSize: 48, border: '4px solid white', boxShadow: 3 }}
                            >
                                {user.firstName?.[0]}{user.lastName?.[0]}
                            </Avatar>
                            {isOwnProfile && (
                                <IconButton
                                    component="label"
                                    sx={{ 
                                        position: 'absolute', bottom: 0, right: 0, 
                                        bgcolor: 'white', color: 'primary.main',
                                        '&:hover': { bgcolor: '#f5f5f5' },
                                        boxShadow: 2,
                                        width: 36, height: 36
                                    }}
                                    disabled={uploading}
                                >
                                    <input type="file" hidden accept="image/*" onChange={handleAvatarUpload} />
                                    {uploading ? <CircularProgress size={20} /> : <PhotoCameraIcon sx={{ fontSize: 20 }} />}
                                </IconButton>
                            )}
                        </Box>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 'grow' }}>
                        <Typography variant="h4" fontWeight="bold">
                            {user.firstName} {user.lastName}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                            <Chip label={['admin', 'super_admin'].includes(user.role.name) ? "Администратор" : "Служител"} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }} />
                            <Chip label={user.departmentName || "Без отдел"} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }} />
                            <Chip label={user.companyName || "Без фирма"} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }} />
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
                    <Tab icon={<PersonIcon />} label="Лични данни" iconPosition="start" />
                    <Tab icon={<ContractIcon />} label="Трудов договор" iconPosition="start" />
                    <Tab icon={<DescriptionIcon />} label="Документи" iconPosition="start" />
                    {canSeeFinance && <Tab icon={<PaidIcon />} label="Заплати" iconPosition="start" />}
                    <Tab icon={<SettingsIcon />} label="Настройки и Сигурност" iconPosition="start" />
                </Tabs>
            </Box>

            {/* TAB 0: Personal & Employment Info */}
            {activeTab === 0 && (
                <>
                    {canSeeFinance && (
                        <Box sx={{ mb: 4 }}>
                            <PersonalDataSection user={user} />
                        </Box>
                    )}
                    <Grid container spacing={3}>
                        <Grid size={{ xs: 12, md: 6 }}>
                        <Card variant="outlined" sx={{ borderRadius: 3, height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom fontWeight="bold">Информация за заетостта</Typography>
                                <List>
                                    <ListItem>
                                        <ListItemIcon><EmailIcon color="primary" /></ListItemIcon>
                                        <ListItemText primary="Имейл" secondary={user.email} />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemIcon><BadgeIcon color="primary" /></ListItemIcon>
                                        <ListItemText primary="Длъжност" secondary={user.jobTitle || 'Не е зададена'} />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemIcon><BusinessIcon color="primary" /></ListItemIcon>
                                        <ListItemText primary="Организация" secondary={`${user.departmentName} / ${user.companyName}`} />
                                    </ListItem>
                                    <ListItem>
                                        <ListItemIcon><EventAvailableIcon color="primary" /></ListItemIcon>
                                        <ListItemText primary="В системата от" secondary={formatDate(user.createdAt)} />
                                    </ListItem>
                                </List>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid size={{ xs: 12, md: 6 }}>
                        <Grid container spacing={3}>
                            {/* Leave Balance Card */}
                            <Grid size={{ xs: 12 }}>
                                <Card variant="outlined" sx={{ borderRadius: 3, bgcolor: 'success.light', color: 'white' }}>
                                    <CardContent>
                                        <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>ОСТАВАЩ ОТПУСК</Typography>
                                        <Typography variant="h3" fontWeight="bold">
                                            {user.leaveBalance ? user.leaveBalance.totalDays - user.leaveBalance.usedDays : 0} дни
                                        </Typography>
                                        <Typography variant="caption">От общо {user.leaveBalance?.totalDays || 0} за годината</Typography>
                                    </CardContent>
                                </Card>
                            </Grid>

                            {/* Finance Card */}
                            {canSeeFinance && (
                                <Grid size={{ xs: 12 }}>
                                    <Card variant="outlined" sx={{ borderRadius: 3 }}>
                                        <CardContent>
                                            <Typography variant="h6" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <AccountBalanceWalletIcon color="warning" /> Финансови параметри
                                            </Typography>
                                            <Grid container spacing={2}>
                                                <Grid size={{ xs: 6 }}>
                                                    <Typography variant="caption" color="text.secondary">Месечна заплата</Typography>
                                                    <Typography variant="h6">{user.payrolls?.[0]?.monthlySalary || 0} {currency}</Typography>
                                                </Grid>
                                                <Grid size={{ xs: 6 }}>
                                                    <Typography variant="caption" color="text.secondary">Часова ставка</Typography>
                                                    <Typography variant="h6">{user.payrolls?.[0]?.hourlyRate || 0} {currency}</Typography>
                                                </Grid>
                                            </Grid>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            )}
                        </Grid>
                    </Grid>
                </Grid>
                </>
            )}

            {/* TAB 1: Contract Dossier */}
            {activeTab === 1 && (
                <ContractDossier userId={user.id} isReadOnly={true} />
            )}

            {/* TAB 2: Documents (Digital Dossier) */}
            {activeTab === 2 && (
                <DocumentManager userId={user.id} isAdmin={isAdmin} />
            )}

            {/* TAB 3: Payment History (conditional) */}
            {activeTab === paymentsTabIndex && canSeeFinance && (
                <PaymentHistorySection userId={user.id} />
            )}

            {/* TAB 3 or 4: Settings & Security */}
            {activeTab === settingsTabIndex && isOwnProfile && (
                <Grid container spacing={3}>
                    {/* Dashboard Settings */}
                    <Grid size={{ xs: 12 }}>
                        <Card variant="outlined" sx={{ borderRadius: 3 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom fontWeight="bold">Настройки на таблото</Typography>
                                <FormControlLabel
                                    control={<Switch checked={mode === 'dark'} onChange={toggleTheme} />}
                                    label="Тъмен режим (Dark Mode)"
                                />
                                <FormControlLabel
                                    control={<Switch checked={dashboardConfig.showChart} onChange={() => toggleDashboardWidget('showChart')} />}
                                    label="Покажи графика с активност"
                                />
                                <FormControlLabel
                                    control={<Switch checked={dashboardConfig.showWeeklyTable} onChange={() => toggleDashboardWidget('showWeeklyTable')} />}
                                    label="Покажи детайлна седмична таблица"
                                />
                                <FormControlLabel
                                    control={<Switch checked={dashboardConfig.showFleetCard} onChange={() => toggleDashboardWidget('showFleetCard')} />}
                                    label="Покажи картичка Автопарк"
                                />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Push Notifications */}
                    <Grid size={{ xs: 12 }}>
                        <PushNotificationManager />
                    </Grid>

                    {/* QR Card */}
                    <Grid size={{ xs: 12, md: 4 }}>
                        <MyQrCard 
                            token={user.qrToken} 
                            refetchQuery={GET_USER_PROFILE} 
                            variables={{ id: userId }}
                        />
                    </Grid>

                    {/* Password Change */}
                    <Grid size={{ xs: 12, md: 8 }}>
                        <Card variant="outlined" sx={{ borderRadius: 3 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom fontWeight="bold">Смяна на парола</Typography>
                                {passwordMsg && <Alert severity={passwordMsg.type} sx={{ mb: 2 }}>{passwordMsg.text}</Alert>}
                                <Grid container spacing={2}>
                                    <Grid size={{ xs: 12 }}>
                                        <TextField fullWidth type="password" label="Текуща парола" value={oldPassword} onChange={e => setOldPassword(e.target.value)} />
                                    </Grid>
                                    <Grid size={{ xs: 12, sm: 6 }}>
                                        <TextField fullWidth type="password" label="Нова парола" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
                                    </Grid>
                                    <Grid size={{ xs: 12, sm: 6 }}>
                                        <TextField fullWidth type="password" label="Потвърди парола" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
                                    </Grid>
                                    <Grid size={{ xs: 12 }}>
                                        <Button variant="contained" onClick={handlePasswordChange}>Промени парола</Button>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Biometric */}
                    <Grid size={{ xs: 12 }}>
                        <Card variant="outlined" sx={{ borderRadius: 3 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <FingerprintIcon /> Биометрия (Passkey)
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Регистрирайте вашия пръстов отпечатък или FaceID за по-безопасен и бърз вход.
                                </Typography>
                                {biometricMsg && (
                                    <Alert severity={biometricMsg.type} sx={{ mb: 2 }} onClose={() => setBiometricMsg(null)}>
                                        {biometricMsg.text}
                                    </Alert>
                                )}
                                <Button variant="outlined" startIcon={<FingerprintIcon />} onClick={handleRegisterBiometric} disabled={biometricLoading}>
                                    {biometricLoading ? 'Регистриране...' : 'Регистрирай биометрия'}
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Карта + PIN */}
                    <Grid size={{ xs: 12 }}>
                        <Card variant="outlined" sx={{ borderRadius: 3 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <KeyIcon /> Карта и PIN код за достъп
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Картата и PIN кодът се използват като фактори за достъп до защитени зони.
                                </Typography>
                                {pinMsg && (
                                    <Alert severity={pinMsg.type} sx={{ mb: 2 }} onClose={() => setPinMsg(null)}>
                                        {pinMsg.text}
                                    </Alert>
                                )}
                                <Grid container spacing={2}>
                                    <Grid size={{ xs: 12, sm: 6 }}>
                                        <Typography variant="caption" color="text.secondary">Номер на карта</Typography>
                                        <Typography variant="body1" fontWeight="medium">{user.cardNumber || '—'}</Typography>
                                    </Grid>
                                    <Grid size={{ xs: 12, sm: 6 }}>
                                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>PIN код</Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            {user.pinExists ? (
                                                <>
                                                    <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '1.2rem', letterSpacing: 2 }}>
                                                        {revealedPin ?? '**** ****'}
                                                    </Typography>
                                                    <IconButton size="small" onClick={() => setPinDialogOpen(true)}>
                                                        {revealedPin ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                                    </IconButton>
                                                </>
                                            ) : (
                                                <Typography variant="body1">Нямате зададен PIN код</Typography>
                                            )}
                                            <Button variant="outlined" startIcon={<KeyIcon />} onClick={handleReissuePin} size="small">
                                                {user.pinExists ? 'Преиздай' : 'Генерирай'}
                                            </Button>
                                        </Box>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* PIN reveal dialog */}
                    <Dialog open={pinDialogOpen} onClose={() => { setPinDialogOpen(false); setPinPassword(''); }} maxWidth="xs" fullWidth>
                        <DialogTitle>Показване на PIN код</DialogTitle>
                        <DialogContent>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Въведете паролата си, за да видите PIN кода.
                            </Typography>
                            <TextField
                                fullWidth
                                type="password"
                                label="Парола"
                                value={pinPassword}
                                onChange={e => setPinPassword(e.target.value)}
                                autoFocus
                            />
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => { setPinDialogOpen(false); setPinPassword(''); }}>Отказ</Button>
                            <Button variant="contained" onClick={handleRevealPin} disabled={!pinPassword}>Покажи</Button>
                        </DialogActions>
                    </Dialog>

                    {/* Payslip */}
                    <Grid size={{ xs: 12 }}>
                        <Card variant="outlined" sx={{ borderRadius: 3 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom fontWeight="bold">Генериране на фиш</Typography>
                                <Grid container spacing={2} alignItems="center">
                                    <Grid size={{ xs: 12, sm: 5 }}>
                                        <TextField fullWidth type="date" label="От дата" InputLabelProps={{ shrink: true }} value={startDate} onChange={e => setStartDate(e.target.value)} />
                                    </Grid>
                                    <Grid size={{ xs: 12, sm: 5 }}>
                                        <TextField fullWidth type="date" label="До дата" InputLabelProps={{ shrink: true }} value={endDate} onChange={e => setEndDate(e.target.value)} />
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
                                                <Typography fontWeight="bold">{Number(payslipResult.regularAmount).toFixed(2)} {currency}</Typography>
                                            </Grid>
                                            <Grid size={{ xs: 6 }}>
                                                <Typography variant="body2" color="error">Извънреден труд:</Typography>
                                                <Typography fontWeight="bold" color="error">{formatHours(payslipResult.totalOvertimeHours)}</Typography>
                                            </Grid>
                                            <Grid size={{ xs: 6 }}>
                                                <Typography variant="body2" color="error">Сума (Извънредни):</Typography>
                                                <Typography fontWeight="bold" color="error">{Number(payslipResult.overtimeAmount).toFixed(2)} {currency}</Typography>
                                            </Grid>
                                            <Grid size={{ xs: 12 }}><Divider sx={{ my: 1 }} /></Grid>
                                            <Grid size={{ xs: 6 }}>
                                                <Typography variant="body2" color="warning.dark">Бонуси:</Typography>
                                                <Typography fontWeight="bold">+{Number(payslipResult.bonusAmount).toFixed(2)} {currency}</Typography>
                                            </Grid>
                                            <Grid size={{ xs: 6 }}>
                                                <Typography variant="body2" color="text.secondary">Отпуск / Болнични:</Typography>
                                                <Typography fontWeight="medium">{payslipResult.leaveDays} д. / {payslipResult.sickDays} д.</Typography>
                                            </Grid>
                                            <Grid size={{ xs: 12 }}><Divider sx={{ my: 1 }} /></Grid>
                                            <Grid size={{ xs: 6 }}>
                                                <Typography variant="body2" color="error.main">Осигуровки:</Typography>
                                                <Typography fontWeight="bold" color="error.main">-{Number(payslipResult.insuranceAmount).toFixed(2)} {currency}</Typography>
                                            </Grid>
                                            <Grid size={{ xs: 6 }}>
                                                <Typography variant="body2" color="error.main">Данък (ДДФЛ):</Typography>
                                                <Typography fontWeight="bold" color="error.main">-{Number(payslipResult.taxAmount).toFixed(2)} {currency}</Typography>
                                            </Grid>
                                        </Grid>
                                        <Box sx={{ mt: 3, p: 2, bgcolor: 'success.light', color: 'white', borderRadius: 2, textAlign: 'center' }}>
                                            <Typography variant="subtitle2" sx={{ opacity: 0.9 }}>ОБЩО ЗА ПОЛУЧАВАНЕ (НЕТО)</Typography>
                                            <Typography variant="h4" fontWeight="bold">{Number(payslipResult.totalAmount).toFixed(2)} {currency}</Typography>
                                        </Box>
                                        <Box sx={{ mt: 2, textAlign: 'center' }}>
                                            <Button variant="outlined" size="small" onClick={async () => {
                                                try {
                                                    const res = await fetch(`${getApiUrl()}/export/payslip/${payslipResult.id}/pdf`, {
                                                        credentials: 'include',
                                                    });
                                                    if (!res.ok) throw new Error('Failed');
                                                    const blob = await res.blob();
                                                    const url = window.URL.createObjectURL(blob);
                                                    const a = document.createElement('a');
                                                    a.href = url;
                                                    a.download = `payslip_${payslipResult.id}.pdf`;
                                                    a.click();
                                                } catch { alert('Грешка при сваляне'); }
                                            }}>
                                                Изтегли PDF
                                            </Button>
                                        </Box>
                                    </Box>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}
        </Container>
    );
};

export default ProfilePage;
