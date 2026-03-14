import React, { useState } from 'react';
import { UserDailyStat } from '../types';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  MenuItem,
  Chip,
  Container,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  CircularProgress,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { useQuery, useLazyQuery, useMutation, gql } from '@apollo/client';
import { format } from 'date-fns';
import RefreshIcon from '@mui/icons-material/Refresh';
import CloseIcon from '@mui/icons-material/Close';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

const GET_USER_PRESENCES = gql`
  query GetUserPresences($date: Date!, $status: PresenceStatus) {
    userPresences(date: $date, status: $status) {
      user {
        id
        firstName
        lastName
        email
      }
      shiftStart
      shiftEnd
      actualArrival
      actualDeparture
      status
      isOnDuty
    }
  }
`;

const ADMIN_CLOCK_IN = gql`
  mutation AdminClockIn($userId: Int!, $customTime: DateTime) {
    adminClockIn(userId: $userId, customTime: $customTime) {
      id
      startTime
    }
  }
`;

const ADMIN_CLOCK_OUT = gql`
  mutation AdminClockOut($userId: Int!, $customTime: DateTime) {
    adminClockOut(userId: $userId, customTime: $customTime) {
      id
      endTime
    }
  }
`;

const GET_USER_DAILY_STATS = gql`
  query GetUserDailyStats($userId: Int!, $startDate: Date!, $endDate: Date!) {
    userDailyStats(userId: $userId, startDate: $startDate, endDate: $endDate) {
      date
      totalWorkedHours
      regularHours
      overtimeHours
      isWorkDay
      shiftName
      actualArrival
      actualDeparture
    }
  }
`;

const formatDuration = (hours: number) => {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return `${h}ч ${m.toString().padStart(2, '0')}м`;
};

const UserStatsDialog: React.FC<{ open: boolean; onClose: () => void; userId: number | null; userName: string }> = ({ open, onClose, userId, userName }) => {
  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(startOfMonth);
  const [endDate, setEndDate] = useState(new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0]);
  const [getStats, { data, loading }] = useLazyQuery(GET_USER_DAILY_STATS);

  React.useEffect(() => {
    if (open && userId) {
      getStats({ variables: { userId, startDate, endDate } });
    }
  }, [open, userId, startDate, endDate, getStats]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
            Статистика за {userName}
            <Typography variant="caption" display="block" color="text.secondary">
                {startDate} - {endDate}
            </Typography>
        </Box>
        <IconButton onClick={onClose}><CloseIcon /></IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ p: { xs: 1, sm: 2 } }}>
        <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
             <TextField
                label="От дата" type="date" size="small" value={startDate}
                onChange={(e) => setStartDate(e.target.value)} InputLabelProps={{ shrink: true }}
                sx={{ flex: { xs: '1 1 100%', sm: 'auto' } }}
             />
             <TextField
                label="До дата" type="date" size="small" value={endDate}
                onChange={(e) => setEndDate(e.target.value)} InputLabelProps={{ shrink: true }}
                sx={{ flex: { xs: '1 1 100%', sm: 'auto' } }}
             />
        </Box>
        {loading ? <Box sx={{textAlign: 'center', py: 4}}><CircularProgress /></Box> : (
            <TableContainer component={Paper} variant="outlined" sx={{ overflowX: 'auto' }}>
                <Table size="small" sx={{ minWidth: { xs: 600, sm: '100%' } }}>
                    <TableHead>
                        <TableRow sx={{ bgcolor: 'action.hover' }}>
                            <TableCell sx={{ whiteSpace: 'nowrap' }}>Дата</TableCell>
                            <TableCell>Смяна</TableCell>
                            <TableCell>Вход</TableCell>
                            <TableCell>Изход</TableCell>
                            <TableCell align="right">Редовни</TableCell>
                            <TableCell align="right">Извънредни</TableCell>
                            <TableCell align="right">Общо</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {data?.userDailyStats.map((stat: UserDailyStat) => (
                            <TableRow key={stat.date} sx={{ bgcolor: stat.isWorkDay ? 'transparent' : 'action.hover' }}>
                                <TableCell sx={{ whiteSpace: 'nowrap', fontSize: '0.8rem' }}>
                                    {new Date(stat.date).toLocaleDateString('bg-BG', { day: '2-digit', month: '2-digit' })}
                                </TableCell>
                                <TableCell sx={{ maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {stat.shiftName || '-'}
                                </TableCell>
                                <TableCell sx={{ whiteSpace: 'nowrap' }}>{stat.actualArrival ? format(new Date(stat.actualArrival), 'HH:mm') : '-'}</TableCell>
                                <TableCell sx={{ whiteSpace: 'nowrap' }}>{stat.actualDeparture ? format(new Date(stat.actualDeparture), 'HH:mm') : '-'}</TableCell>
                                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>{formatDuration(stat.regularHours)}</TableCell>
                                <TableCell align="right" sx={{ color: stat.overtimeHours > 0 ? 'error.main' : 'inherit', fontWeight: stat.overtimeHours > 0 ? 'bold' : 'normal', whiteSpace: 'nowrap' }}>
                                    {formatDuration(stat.overtimeHours)}
                                </TableCell>
                                <TableCell align="right" sx={{ fontWeight: 'bold', whiteSpace: 'nowrap' }}>{formatDuration(stat.totalWorkedHours)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        )}
      </DialogContent>
      <DialogActions><Button onClick={onClose}>Затвори</Button></DialogActions>
    </Dialog>
  );
};

const AdminClockDialog: React.FC<{ 
    open: boolean; onClose: () => void; onConfirm: (datetime: string | null) => void;
    mode: 'IN' | 'OUT'; userName: string; targetDate: string;
}> = ({ open, onClose, onConfirm, mode, userName, targetDate }) => {
    const [useNow, setUseNow] = useState(true);
    const [customTime, setCustomTime] = useState(format(new Date(), 'HH:mm'));
    const handleConfirm = () => {
        if (useNow) onConfirm(null);
        else onConfirm(new Date(`${targetDate}T${customTime}`).toISOString());
        onClose();
    };
    return (
        <Dialog open={open} onClose={onClose}>
            <DialogTitle>{mode === 'IN' ? 'Стартиране на смяна' : 'Приключване на смяна'}</DialogTitle>
            <DialogContent sx={{ pt: 1, minWidth: 300 }}>
                <Typography>Служител: <strong>{userName}</strong></Typography>
                <FormControlLabel control={<Switch checked={useNow} onChange={(e) => setUseNow(e.target.checked)} />} label="Сега" sx={{ mb: 2 }} />
                {!useNow && <TextField label="Час" type="time" value={customTime} onChange={(e) => setCustomTime(e.target.value)} InputLabelProps={{ shrink: true }} fullWidth />}
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Отказ</Button><Button onClick={handleConfirm} variant="contained" color={mode === 'IN' ? 'success' : 'error'}>{mode === 'IN' ? 'Старт' : 'Стоп'}</Button></DialogActions>
        </Dialog>
    );
};

const AdminDashboardPageTabMap: Record<string, number> = {
  'attendance': 0,
  'analytics': 1,
};

interface Props {
  tab?: string;
}

const AdminDashboardPage: React.FC<Props> = ({ tab }) => {
  const initialTab = tab ? (AdminDashboardPageTabMap[tab] ?? 0) : 0;
  const [tabValue, setTabValue] = useState(initialTab);
  
  // Update tab when URL changes
  React.useEffect(() => {
    const newTab = tab ? (AdminDashboardPageTabMap[tab] ?? 0) : 0;
    setTabValue(newTab);
  }, [tab]);
  
  const [date, setDate] = useState<string>(format(new Date(), 'yyyy-MM-dd'));
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUserName, setSelectedUserName] = useState('');
  const [clockDialogOpen, setClockDialogOpen] = useState(false);
  const [clockDialogMode, setClockDialogMode] = useState<'IN' | 'OUT'>('IN');
  const [actionUserId, setActionUserId] = useState<number | null>(null);

  const { data, loading, error, refetch } = useQuery(GET_USER_PRESENCES, {
    variables: { date, status: statusFilter === 'ALL' ? null : statusFilter },
    fetchPolicy: 'network-only',
  });

  const [adminClockIn] = useMutation(ADMIN_CLOCK_IN);
  const [adminClockOut] = useMutation(ADMIN_CLOCK_OUT);

  const handleOpenClockDialog = (e: React.MouseEvent, userId: number, userName: string, mode: 'IN' | 'OUT') => {
      e.stopPropagation(); setActionUserId(userId); setSelectedUserName(userName); setClockDialogMode(mode); setClockDialogOpen(true);
  };

  const handleClockAction = async (customTime: string | null) => {
      if (!actionUserId) return;
      try {
          if (clockDialogMode === 'IN') await adminClockIn({ variables: { userId: actionUserId, customTime } });
          else await adminClockOut({ variables: { userId: actionUserId, customTime } });
          refetch();
      } catch (err: unknown) {
        const error = err as { message?: string };
        alert(error.message || 'Грешка');
      }
  };

  const getStatusChip = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'ON_DUTY') return <Chip label="НА РАБОТА" color="primary" />;
    switch (s) {
      case 'LATE': return <Chip label="ЗАКЪСНЯЛ" color="warning" variant="outlined" />;
      case 'ABSENT': return <Chip label="ОТСЪСТВА" color="error" variant="outlined" />;
      case 'SICK_LEAVE': return <Chip label="БОЛНИЧЕН" variant="outlined" />;
      case 'PAID_LEAVE': return <Chip label="ОТПУСК" color="info" variant="outlined" />;
      case 'OFF_DUTY': return <Chip label="НЕ Е НА РАБОТА" sx={{ opacity: 0.6 }} variant="outlined" />;
      default: return <Chip label={status} variant="outlined" />;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">Админ Панел</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Опресни"><IconButton onClick={() => refetch()} color="primary"><RefreshIcon /></IconButton></Tooltip>
        </Box>
      </Box>

      {tabValue === 0 && (
          <>
            <Paper sx={{ p: 2, mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <TextField label="Дата" type="date" value={date} onChange={(e) => setDate(e.target.value)} InputLabelProps={{ shrink: true }} size="small" />
                <TextField select label="Статус" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} size="small" sx={{ minWidth: 150 }}>
                    <MenuItem value="ALL">Всички</MenuItem>
                    <MenuItem value="ON_DUTY">На работа</MenuItem>
                    <MenuItem value="LATE">Закъснели</MenuItem>
                    <MenuItem value="ABSENT">Отсъстващи</MenuItem>
                    <MenuItem value="SICK_LEAVE">Болнични</MenuItem>
                    <MenuItem value="PAID_LEAVE">Отпуск</MenuItem>
                    <MenuItem value="OFF_DUTY">Извън смяна</MenuItem>
                </TextField>
            </Paper>

            {loading ? <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box> : error ? <Typography color="error">Грешка: {error.message}</Typography> : (
                <TableContainer component={Paper}>
                <Table>
                    <TableHead sx={{ bgcolor: 'action.hover' }}>
                    <TableRow>
                        <TableCell>Потребител</TableCell>
                        <TableCell>Смяна</TableCell>
                        <TableCell>Пристигане</TableCell>
                        <TableCell>Тръгване</TableCell>
                        <TableCell align="center">Статус</TableCell>
                        <TableCell align="center">Действия</TableCell>
                    </TableRow>
                    </TableHead>
                    <TableBody>
                    {data?.userPresences.map((presence: any) => (
                        <TableRow key={presence.user.id} hover sx={{ cursor: 'pointer' }} onClick={() => { setSelectedUserId(presence.user.id); setSelectedUserName(`${presence.user.firstName || ''} ${presence.user.lastName || presence.user.email}`); }}>
                        <TableCell>
                            <Typography variant="subtitle2">{presence.user.firstName} {presence.user.lastName}</Typography>
                            <Typography variant="caption" color="textSecondary">{presence.user.email}</Typography>
                        </TableCell>
                        <TableCell>{presence.shiftStart ? `${presence.shiftStart.substring(0,5)} - ${presence.shiftEnd.substring(0,5)}` : 'Няма график'}</TableCell>
                        <TableCell>{presence.actualArrival ? format(new Date(presence.actualArrival), 'HH:mm') : '-'}</TableCell>
                        <TableCell>{presence.status === 'ON_DUTY' ? <Typography color="primary" fontWeight="bold">на работа</Typography> : (presence.actualDeparture ? format(new Date(presence.actualDeparture), 'HH:mm') : '-')}</TableCell>
                        <TableCell align="center">{getStatusChip(presence.status)}</TableCell>
                        <TableCell align="center">
                            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                                <IconButton size="small" color="success" onClick={(e) => handleOpenClockDialog(e, presence.user.id, `${presence.user.firstName} ${presence.user.lastName}`, 'IN')} disabled={presence.status === 'ON_DUTY'}><PlayArrowIcon fontSize="small" /></IconButton>
                                <IconButton size="small" color="error" onClick={(e) => handleOpenClockDialog(e, presence.user.id, `${presence.user.firstName} ${presence.user.lastName}`, 'OUT')} disabled={presence.status !== 'ON_DUTY'}><StopIcon fontSize="small" /></IconButton>
                            </Box>
                        </TableCell>
                        </TableRow>
                    ))}
                    </TableBody>
                </Table>
                </TableContainer>
            )}
          </>
      )}

      {tabValue === 1 && <AnalyticsDashboard />}

      <UserStatsDialog open={!!selectedUserId} onClose={() => setSelectedUserId(null)} userId={selectedUserId} userName={selectedUserName} />
      <AdminClockDialog open={clockDialogOpen} onClose={() => setClockDialogOpen(false)} onConfirm={handleClockAction} mode={clockDialogMode} userName={selectedUserName} targetDate={date} />
    </Container>
  );
};

export default AdminDashboardPage;