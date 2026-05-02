import React, { useState } from 'react';
import { 
  Container, Typography, Grid, Card, CardContent, Avatar, Box, 
  Chip, Tab, Tabs, List, ListItem, ListItemIcon, ListItemText,
  Paper, CircularProgress, Alert, IconButton, Divider
} from '@mui/material';
import { useQuery, gql } from '@apollo/client';
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
import axios from 'axios';
import { useCurrency } from '../currencyContext';
import { formatDate } from '../utils/dateUtils';
import PushNotificationManager from '../components/PushNotificationManager';
import MyQrCard from '../components/MyQrCard';
import DocumentManager from '../components/DocumentManager';
import ContractDossier from '../components/ContractDossier';

const GET_USER_PROFILE = gql`
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
    const [activeTab, setActiveTab] = useState(0);
    const [uploading, setUploading] = useState(false);

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
            const token = localStorage.getItem('token');
            await axios.post(url, formData, {
                headers: { 
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${token}`
                }
            });
            refetch();
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } } };
            alert(error.response?.data?.detail || "Грешка при качване");
        } finally {
            setUploading(false);
        }
    };

    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}><CircularProgress /></Box>;
    if (error) return <Alert severity="error">{error.message}</Alert>;

    const user = data.user;
    const isOwnProfile = data.me.id === user.id;
    const isAdmin = ['admin', 'super_admin'].includes(data.me.role.name);

    const canSeeFinance = isOwnProfile || isAdmin;

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
            {/* Header / Avatar Section */}
            <Paper sx={{ p: 4, borderRadius: 4, mb: 4, background: 'linear-gradient(135deg, #3f51b5 0%, #1a237e 100%)', color: 'white' }}>
                <Grid container spacing={3} alignItems="center">
                    <Grid>
                        <Box sx={{ position: 'relative' }}>
                            <Avatar 
                                src={user.profilePicture ? `${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/uploads/${user.profilePicture}` : undefined}
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

            {/* TAB 3: Settings & Security */}
            {activeTab === 3 && (
                <Grid container spacing={3}>
                    <Grid size={{ xs: 12, md: 4 }}>
                        <MyQrCard 
                            token={user.qrToken} 
                            refetchQuery={GET_USER_PROFILE} 
                            variables={{ id: userId }}
                        />
                    </Grid>
                    <Grid size={{ xs: 12, md: 8 }}>
                        <PushNotificationManager />
                    </Grid>
                </Grid>
            )}
        </Container>
    );
};

export default ProfilePage;
