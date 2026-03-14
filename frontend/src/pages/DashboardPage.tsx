import React, { useEffect, useState } from 'react';
import { Container, Typography, CircularProgress, Box, Alert, Button, Card, CardContent, Grid } from '@mui/material';
import { useQuery, gql, useMutation } from '@apollo/client';
import { useNavigate } from 'react-router-dom';
import { UserDailyStat } from '../types';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import BuildIcon from '@mui/icons-material/Build';
import SecurityIcon from '@mui/icons-material/Security';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import { 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip as MuiChip, Chip
} from '@mui/material';
import { formatDuration, formatDurationHHMM } from '../utils/formatUtils';
import { useAppTheme } from '../themeContext';
import ShiftSwapCenter from '../components/ShiftSwapCenter';
import MyQrCard from '../components/MyQrCard';

const DASHBOARD_QUERY = gql`
  query GetDashboardData($startDate: Date!, $endDate: Date!) {
    me {
      id
      email
      firstName
      lastName
      qrToken
      role {
        name
      }
      leaveBalance {
        totalDays
        usedDays
      }
      timelogs(startDate: $startDate, endDate: $endDate) {
        id
        startTime
        endTime
      }
    }
    activeTimeLog {
      id
      startTime
    }
    myDailyStats(startDate: $startDate, endDate: $endDate) {
      date
      regularHours
      overtimeHours
      totalWorkedHours
      shiftName
    }
    weeklySummary(date: $startDate) {
      totalRegularHours
      totalOvertimeHours
      targetHours
      debtHours
      surplusHours
      statusMessage
    }
  }
`;

const CLOCK_IN_MUTATION = gql`
  mutation ClockIn($lat: Float, $lon: Float) {
    clockIn(latitude: $lat, longitude: $lon) {
      id
      startTime
    }
  }
`;

const CLOCK_OUT_MUTATION = gql`
  mutation ClockOut($lat: Float, $lon: Float) {
    clockOut(latitude: $lat, longitude: $lon) {
      id
      endTime
    }
  }
`;

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { dashboardConfig } = useAppTheme();
  const [isAdmin, setIsAdmin] = useState(false);
  
  // Calculate current week range
  const now = new Date();
  const start = new Date(now);
  start.setDate(now.getDate() - now.getDay() + (now.getDay() === 0 ? -6 : 1));
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  end.setHours(23, 59, 59, 999);

  const endDateStr = end.toISOString().split('T')[0];
  const startDateStr = start.toISOString().split('T')[0];

  const { loading, error, data, refetch } = useQuery(DASHBOARD_QUERY, {
    variables: { startDate: startDateStr, endDate: endDateStr },
    fetchPolicy: 'network-only'
  });
  
  const [clockIn] = useMutation(CLOCK_IN_MUTATION);
  const [clockOut] = useMutation(CLOCK_OUT_MUTATION);
  const [timer, setTimer] = useState<string>('00:00:00');

  useEffect(() => {
    if (!loading && (!data || !data.me)) {
      navigate('/login');
    }
    if (data?.me?.role?.name) {
      // eslint-disable-next-line
      setIsAdmin(['admin', 'super_admin'].includes(data.me.role.name));
    }
  }, [data, loading, navigate]);

  // Timer logic for active session
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    if (data?.activeTimeLog) {
      interval = setInterval(() => {
        const rawStartTime = data.activeTimeLog.startTime;
        const startTimeStr = rawStartTime; 
        
        const start = new Date(startTimeStr).getTime();
        const now = new Date().getTime();
        const diff = now - start;
        
        if (diff < 0) {
          setTimer('00:00:00');
          return;
        }
        
        const h = Math.floor(diff / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        
        setTimer(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`);
      }, 1000);
    } else {
      // eslint-disable-next-line
      setTimer('00:00:00');
    }
    return () => clearInterval(interval);
  }, [data?.activeTimeLog]);

  // Use backend stats directly
  const chartData = data?.myDailyStats?.map((stat: UserDailyStat) => ({
    name: new Date(stat.date).toLocaleDateString('bg-BG', { weekday: 'short' }),
    regular: stat.regularHours,
    overtime: stat.overtimeHours,
    total: stat.totalWorkedHours,
    fullDate: stat.date,
    shiftName: stat.shiftName
  })) || [];

  const handleClockToggle = async () => {
    try {
      if (data?.activeTimeLog) {
        await clockOut();
      } else {
        await clockIn();
      }
      await refetch();
    } catch (err: unknown) {
      const error = err as { message?: string };
      alert(error.message || 'Грешка');
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error.message}</Alert>;
  if (!data || !data.me) return null;

  const { email, firstName } = data.me;
  const isActive = !!data.activeTimeLog;
  const summary = data.weeklySummary;
  
  interface ChartDataItem {
    name: string;
    regular: number;
    overtime: number;
    total: number;
    fullDate: string;
    shiftName?: string;
  }
  
  const currentSchedule = chartData.find((d: ChartDataItem) => d.fullDate === new Date().toISOString().split('T')[0]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold" color="primary">
        Лично табло
      </Typography>

      <Grid container spacing={3}>
        {/* КАРТА ЗА QR КОД */}
        <Grid size={{ xs: 12, md: 3 }}>
            <MyQrCard 
              token={data.me.qrToken} 
              refetchQuery={DASHBOARD_QUERY} 
              variables={{ startDate: startDateStr, endDate: endDateStr }}
            />
        </Grid>

        {/* КАРТА ЗА CLOCK IN/OUT */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%', borderRadius: 4, boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Здравей, {firstName || email.split('@')[0]}!
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Текуща смяна: <strong>{currentSchedule?.shiftName || 'Няма смяна'}</strong>
              </Typography>
              
              <Box sx={{ 
                p: 2.2, 
                textAlign: 'center', 
                backgroundColor: isActive ? 'rgba(76, 175, 80, 0.08)' : 'rgba(0, 0, 0, 0.02)',
                borderRadius: 4,
                border: '1px solid',
                borderColor: isActive ? 'success.light' : 'divider',
                mb: 2
              }}>
                <Typography variant="overline" display="block" color="text.secondary" sx={{ lineHeight: 1.2 }}>
                  {isActive ? 'ВРЕМЕ ОТ НАЧАЛОТО' : 'НЯМА АКТИВНА СЕСИЯ'}
                </Typography>
                <Typography variant="h4" sx={{ my: 1.5, fontFamily: 'monospace', fontWeight: 'bold', color: isActive ? 'success.main' : 'text.primary' }}>
                  {timer}
                </Typography>
                
                <Button
                  variant="contained"
                  size="medium"
                  color={isActive ? 'error' : 'success'}
                  startIcon={isActive ? <StopIcon /> : <PlayArrowIcon />}
                  onClick={handleClockToggle}
                  sx={{ px: 4, py: 1, borderRadius: 10, fontWeight: 'bold', boxShadow: 2 }}
                >
                  {isActive ? 'Изход' : 'Вход'}
                </Button>
              </Box>

              {summary && (
                <Alert 
                  severity={summary.debtHours > 0 ? "warning" : "success"}
                  icon={summary.debtHours > 0 ? <WarningIcon /> : <CheckCircleIcon />}
                  sx={{ borderRadius: 3, fontWeight: 'medium', py: 0.5 }}
                >
                  <Typography variant="body2">{summary.statusMessage}</Typography>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* СТАТИСТИКА И ГРАФИКА */}
        {dashboardConfig.showChart && (
          <Grid size={{ xs: 12, md: 5 }}>
            <Card sx={{ height: '100%', borderRadius: 4, boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" fontWeight="bold">Активност през седмицата</Typography>
                </Box>
                
                <Box sx={{ width: '100%', height: 250, mt: 2, minWidth: 0, minHeight: 250, position: 'relative' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} />
                      <YAxis axisLine={false} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ borderRadius: '10px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                        cursor={{ fill: 'rgba(0,0,0,0.04)' }}
                        formatter={(value) => [
                          formatDuration(Math.round(parseFloat(String(value ?? 0)) * 60)), 
                          'Отработено'
                        ]}
                      />
                      <Bar dataKey="regular" stackId="a" fill="#3f51b5" radius={[0, 0, 4, 4]} />
                      <Bar dataKey="overtime" stackId="a" fill="#f44336" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* АВТОПАРК WIDGET */}
      {isAdmin && (
        <Grid container spacing={3} sx={{ mt: 1, mb: 3 }}>
          <Grid size={{ xs: 12 }}>
            <Card sx={{ borderRadius: 4, boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" fontWeight="bold">Автопарк</Typography>
                  <Button 
                    size="small" 
                    onClick={() => navigate('/admin/fleet')}
                  >
                    Към автомобили
                  </Button>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.main', borderRadius: 2, color: 'white' }}>
                      <DirectionsCarIcon sx={{ fontSize: 32, mb: 1 }} />
                      <Typography variant="h4">0</Typography>
                      <Typography variant="body2">Общо</Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.main', borderRadius: 2, color: 'white' }}>
                      <DirectionsCarIcon sx={{ fontSize: 32, mb: 1 }} />
                      <Typography variant="h4">0</Typography>
                      <Typography variant="body2">Активни</Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.main', borderRadius: 2, color: 'white' }}>
                      <BuildIcon sx={{ fontSize: 32, mb: 1 }} />
                      <Typography variant="h4">0</Typography>
                      <Typography variant="body2">В ремонт</Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'error.main', borderRadius: 2, color: 'white' }}>
                      <DirectionsCarIcon sx={{ fontSize: 32, mb: 1 }} />
                      <Typography variant="h4">0</Typography>
                      <Typography variant="body2">Извън експл.</Typography>
                    </Box>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="error" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <WarningIcon fontSize="small" /> Под внимание:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip 
                      icon={<SecurityIcon />} 
                      label="Няма изтичащи застраховки" 
                      color="success" 
                      variant="outlined" 
                      size="small"
                    />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* ТАБЛИЧЕН СЕДМИЧЕН ГРАФИК */}
      {dashboardConfig.showWeeklyTable && (
        <Card sx={{ mt: 3, borderRadius: 4, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', mb: 4 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>Детайлен отчет за седмицата</Typography>
            <TableContainer>
              <Table size="small">
                <TableHead sx={{ bgcolor: 'rgba(0,0,0,0.02)' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Ден</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', display: { xs: 'none', md: 'table-cell' } }}>Смяна</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Вход</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Изход</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Извънреден</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', display: { xs: 'none', md: 'table-cell' } }} align="right">Общо</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[...chartData].reverse().map((day) => {
                    const dayLogs = data.me.timelogs
                        .filter((l: { startTime: string }) => l.startTime.startsWith(day.fullDate))
                        .sort((a: { startTime: string }, b: { startTime: string }) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime());
                    
                    const firstStart = dayLogs.length > 0 ? dayLogs[0].startTime : null;
                    const lastLog = dayLogs.length > 0 ? dayLogs[dayLogs.length - 1] : null;
                    const lastEnd = lastLog ? lastLog.endTime : null;
                    const isDayActive = lastLog && !lastLog.endTime;

                    return (
                      <TableRow key={day.fullDate} hover>
                        <TableCell>
                            {day.name}, {new Date(day.fullDate).toLocaleDateString('bg-BG', { day: '2-digit', month: '2-digit', year: '2-digit' }).replace(/\//g, '.')}
                        </TableCell>
                        <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                          {day.shiftName ? (
                            <MuiChip 
                              label={day.shiftName} 
                              size="small" 
                              variant="outlined" 
                              sx={{ fontSize: '0.7rem' }}
                            />
                          ) : '—'}
                        </TableCell>
                        <TableCell>
                          {firstStart ? new Date(firstStart).toLocaleTimeString('bg-BG', { hour: '2-digit', minute: '2-digit' }) : '—'}
                        </TableCell>
                        <TableCell>
                          {isDayActive 
                            ? <MuiChip label="Активен" color="success" size="small" variant="outlined" />
                            : (lastEnd ? new Date(lastEnd).toLocaleTimeString('bg-BG', { hour: '2-digit', minute: '2-digit' }) : '—')
                          }
                        </TableCell>
                        <TableCell sx={{ color: day.overtime > 0 ? 'error.main' : 'inherit', fontWeight: day.overtime > 0 ? 'bold' : 'normal' }}>
                          {formatDurationHHMM(Math.round(day.overtime * 60))}
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', display: { xs: 'none', md: 'table-cell' } }}>
                          {formatDurationHHMM(Math.round(day.total * 60))}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* АВТОПАРК КАРТИЧКА */}
      {dashboardConfig.showFleetCard && (
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%', borderRadius: 4, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', cursor: 'pointer', transition: 'transform 0.2s', '&:hover': { transform: 'translateY(-4px)' } }} onClick={() => navigate('/fleet')}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DirectionsCarIcon color="primary" />
                  <Typography variant="h6" fontWeight="bold">Автопарк</Typography>
                </Box>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Управление на автомобили, горива, ремонти и документи
              </Typography>
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Chip label="Преглед" size="small" color="primary" variant="outlined" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* ЦЕНТЪР ЗА РАЗМЯНА НА СМЕНИ */}
      <ShiftSwapCenter />
    </Container>
  );
};

export default DashboardPage;