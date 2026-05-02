import React, { useState } from 'react';
import dayjs from 'dayjs';
import { getErrorMessage } from '../types';
import {
  Box, TextField, Button, Typography,
  Dialog, DialogTitle, DialogContent, DialogActions,
  MenuItem, Card, CardContent, IconButton, Alert, CircularProgress,
  useTheme, useMediaQuery, Grid, Stack, Tooltip, InputAdornment
} from '@mui/material';
import { TabbedPage } from '../components/TabbedPage';
import { InfoIcon } from '../components/ui/InfoIcon';
import { useQuery, useMutation, gql } from '@apollo/client';
import { type Shift, type User, type WorkSchedule, type TimeLog, type ScheduleTemplate, type PublicHoliday, type ScheduleLog } from '../types';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import listPlugin from '@fullcalendar/list';
import bgLocale from '@fullcalendar/core/locales/bg';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PrintIcon from '@mui/icons-material/Print';
import ShareIcon from '@mui/icons-material/Share';
import ManualTimeLogModal from '../components/ManualTimeLogModal';
import { formatDate } from '../utils/dateUtils';
import { ShiftTypeColors } from '../utils/shiftUtils';
import ShiftLegend from '../components/ShiftLegend';
import ShiftEventContent from '../components/ShiftEventContent';
import CurrentScheduleView from '../components/CurrentScheduleView';
import ScheduleTemplatesManager from '../components/ScheduleTemplatesManager';

// --- GraphQL ---
const GET_SHIFTS_QUERY = gql`
  query GetShifts {
    shifts {
      id
      name
      startTime
      endTime
      toleranceMinutes
      breakDurationMinutes
      payMultiplier
      shiftType
    }
  }
`;

const GET_SCHEDULES_QUERY = gql`
  query GetSchedules($startDate: Date!, $endDate: Date!) {
    workSchedules(startDate: $startDate, endDate: $endDate) {
      id
      date
      user {
        id
        email
        firstName
        lastName
      }
      shift {
        id
        name
        startTime
        endTime
        shiftType
      }
    }
  }
`;

const GET_TIME_LOGS_QUERY = gql`
  query GetTimeLogs($startDate: DateTime!, $endDate: DateTime!) {
    timeLogs(startDate: $startDate, endDate: $endDate) {
      id
      startTime
      endTime
      isManual
      user {
        id
        email
        firstName
        lastName
      }
    }
  }
`;

const GET_USERS_QUERY = gql`
  query GetUsers($limit: Int) {
    users(limit: $limit) {
      users {
        id
        email
        firstName
        lastName
      }
      totalCount
    }
  }
`;

const GET_PUBLIC_HOLIDAYS_QUERY = gql`
  query GetPublicHolidays($year: Int) {
    publicHolidays(year: $year) {
      id
      date
      name
      localName
    }
  }
`;

const GET_ORTHODOX_HOLIDAYS_QUERY = gql`
  query GetOrthodoxHolidays($year: Int) {
    orthodoxHolidays(year: $year) {
      id
      date
      name
      localName
    }
  }
`;

const CREATE_SHIFT_MUTATION = gql`
  mutation CreateShift($name: String!, $startTime: String!, $endTime: String!, $tolerance: Int, $breakDuration: Int, $payMultiplier: Decimal) {
    createShift(name: $name, startTime: $startTime, endTime: $endTime, toleranceMinutes: $tolerance, breakDurationMinutes: $breakDuration, payMultiplier: $payMultiplier) {
      id
      name
    }
  }
`;

const DELETE_SHIFT_MUTATION = gql`
  mutation DeleteShift($id: Int!) {
    deleteShift(id: $id)
  }
`;

const SET_SCHEDULE_MUTATION = gql`
  mutation SetSchedule($userId: Int!, $shiftId: Int!, $date: Date!) {
    setWorkSchedule(userId: $userId, shiftId: $shiftId, date: $date) {
      id
      date
    }
  }
`;

const DELETE_SCHEDULE_MUTATION = gql`
  mutation DeleteSchedule($id: Int!) {
    deleteWorkSchedule(id: $id)
  }
`;

const DELETE_TIME_LOG_MUTATION = gql`
  mutation DeleteTimeLog($id: Int!) {
    deleteTimeLog(id: $id)
  }
`;

const APPLY_TEMPLATE_MUTATION = gql`
  mutation ApplyTemplate($templateId: Int!, $userId: Int!, $startDate: Date!, $endDate: Date!) {
    applyScheduleTemplate(templateId: $templateId, userId: $userId, startDate: $startDate, endDate: $endDate)
  }
`;


const ShiftManager: React.FC = () => {
  const { data, refetch } = useQuery(GET_SHIFTS_QUERY);
  const [createShift] = useMutation(CREATE_SHIFT_MUTATION);
  const [deleteShift] = useMutation(DELETE_SHIFT_MUTATION);
  
  const [name, setName] = useState('');
  const [start, setStart] = useState('09:00');
  const [end, setEnd] = useState('17:00');
  const [tolerance, setTolerance] = useState('15');
  const [breakDuration, setBreakDuration] = useState('60');
  const [payMultiplier, setPayMultiplier] = useState('1.0');

  const handleCreate = async () => {
    try {
      await createShift({ 
        variables: { 
          name, 
          startTime: start, 
          endTime: end,
          tolerance: parseInt(tolerance),
          breakDuration: parseInt(breakDuration),
          payMultiplier: payMultiplier
        } 
      });
      setName('');
      refetch();
    } catch (err) { alert(getErrorMessage(err)); }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Сигурни ли сте, че искате да изтриете тази смяна?')) {
      try {
        await deleteShift({ variables: { id } });
        refetch();
      } catch (err) { alert(getErrorMessage(err)); }
    }
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>Създаване на нова смяна</Typography>
      <Grid container spacing={2} alignItems="center">
        <Grid size={{ xs: 12, sm: 2 }}>
          <TextField
            fullWidth label="Име на смяната" value={name}
            onChange={(e) => setName(e.target.value)}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Наименование на смяната (напр. Сутрешна, Вечерна)" />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 2 }}>
          <TextField
            fullWidth label="Начало" type="time" value={start}
            onChange={(e) => setStart(e.target.value)}
            InputLabelProps={{ shrink: true }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Час на започване на смяната" />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 2 }}>
          <TextField
            fullWidth label="Край" type="time" value={end}
            onChange={(e) => setEnd(e.target.value)}
            InputLabelProps={{ shrink: true }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Час на приключване на смяната" />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 4, sm: 1.5 }}>
          <TextField
            fullWidth label="Толеранс (мин)" type="number" value={tolerance}
            onChange={(e) => setTolerance(e.target.value)}
            helperText="Прилепване на времето"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Толеранс в минути за късно влизане/ранно излизане" />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 4, sm: 1.5 }}>
          <TextField
            fullWidth label="Почивка (мин)" type="number" value={breakDuration}
            onChange={(e) => setBreakDuration(e.target.value)}
            helperText="Автоматично удържане"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Продължителност на почивката в минути" />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 4, sm: 2 }}>
          <TextField
            fullWidth label="Коефициент Заплащане" type="number" value={payMultiplier}
            onChange={(e) => setPayMultiplier(e.target.value)}
            inputProps={{ step: "0.01" }}
            helperText="Умножител за надницата"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Коефициент за изчисление на заплатата" />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 1 }}>
          <Tooltip title="Създай нова смяна" arrow>
            <Button fullWidth variant="contained" onClick={handleCreate} disabled={!name}>
              <AddIcon />
            </Button>
          </Tooltip>
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>Налични смени</Typography>
      <Grid container spacing={2}>
        {data?.shifts.map((shift: Shift) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={shift.id}>
            <Card variant="outlined" sx={{ borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Typography variant="subtitle1" fontWeight="bold">{shift.name}</Typography>
                  <Tooltip title="Изтрий смяната" arrow>
                    <IconButton size="small" onClick={() => handleDelete(shift.id)} color="error">
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {shift.startTime.substring(0, 5)} - {shift.endTime.substring(0, 5)}
                </Typography>
                <Typography variant="caption" display="block" color="text.secondary">
                  Толеранс: {shift.toleranceMinutes} мин. | Почивка: {shift.breakDurationMinutes} мин.
                </Typography>
                <Typography variant="caption" display="block" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Коефициент: {shift.payMultiplier}x
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

const GET_MONTHLY_WORK_DAYS = gql`
  query GetMonthlyWorkDays($year: Int!, $month: Int!) {
    monthlyWorkDays(year: $year, month: $month) {
      id
      daysCount
    }
  }
`;

const CalendarView: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [open, setOpen] = useState(false);
  const [logOpen, setLogOpen] = useState(false);
  // Track current view date to fetch monthly norm
  const [currentViewDate, setCurrentViewDate] = useState(new Date());

  const [manualLogOpen, setManualLogOpen] = useState(false);
  const [applyTmplOpen, setApplyTmplOpen] = useState(false);
  const [selectedTmpl, setSelectedTmpl] = useState('');
  const [tmplStartDate, setTmplStartDate] = useState('');
  const [tmplEndDate, setTmplEndDate] = useState('');
  const [tmplUserId, setTmplUserId] = useState('');

  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedShift, setSelectedShift] = useState('');
  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null);
  const [isEventEdit, setIsEventEdit] = useState(false);
  const [selectedLog, setSelectedLog] = useState<ScheduleLog | null>(null);

    const { data: usersData } = useQuery(GET_USERS_QUERY, { variables: { limit: 1000 } });

    const { data: shiftsData } = useQuery(GET_SHIFTS_QUERY);

    const { data: tmplData } = useQuery(gql`query GetTmpls { scheduleTemplates { id name } }`);

    const { data: holidaysData } = useQuery(GET_PUBLIC_HOLIDAYS_QUERY, {
      variables: { year: currentViewDate.getFullYear() }
    });

    const includeOrthodox = localStorage.getItem('include_orthodox_holidays') === 'true';
    const { data: orthodoxHolidaysData } = useQuery(GET_ORTHODOX_HOLIDAYS_QUERY, {
      variables: { year: currentViewDate.getFullYear() },
      skip: !includeOrthodox
    });
    
    const { data: normData } = useQuery(GET_MONTHLY_WORK_DAYS, {
        variables: { 
            year: currentViewDate.getFullYear(), 
            month: currentViewDate.getMonth() + 1 
        }
    });

    const { data: schedData, refetch: refetchSched } = useQuery(GET_SCHEDULES_QUERY, {
      variables: {
        startDate: new Date(currentViewDate.getFullYear(), currentViewDate.getMonth(), 1).toISOString().split('T')[0],
        endDate: new Date(currentViewDate.getFullYear(), currentViewDate.getMonth() + 1, 0).toISOString().split('T')[0]
      }
    });

    const { data: logsData, error: logsError, loading: logsLoading, refetch: refetchLogs } = useQuery(GET_TIME_LOGS_QUERY, {
      variables: {
        startDate: new Date(currentViewDate.getFullYear(), currentViewDate.getMonth(), 1).toISOString(),
        endDate: new Date(currentViewDate.getFullYear(), currentViewDate.getMonth() + 1, 0, 23, 59, 59).toISOString()
      }
    });

    if (logsError) {
        console.error("Logs Error:", logsError);
    }

    const [setSchedule] = useMutation(SET_SCHEDULE_MUTATION);
    const [deleteSchedule] = useMutation(DELETE_SCHEDULE_MUTATION);
    const [deleteTimeLog] = useMutation(DELETE_TIME_LOG_MUTATION);
    const [applyTmpl] = useMutation(APPLY_TEMPLATE_MUTATION);

    const handleApplyTemplate = async () => {
        try {
            await applyTmpl({
                variables: {
                    templateId: parseInt(selectedTmpl),
                    userId: parseInt(tmplUserId),
                    startDate: tmplStartDate,
                    endDate: tmplEndDate
                }
            });
            setApplyTmplOpen(false);
            alert("Шаблонът е приложен успешно!");
            refetchSched();
        } catch (err) { alert(getErrorMessage(err)); }
    };

    const handleDatesSet = (arg: any) => {
        // Calculate the central date of the view to determine the current month correctly
        const start = arg.view.currentStart;
        const end = arg.view.currentEnd;
        const mid = new Date((start.getTime() + end.getTime()) / 2);
        
        // Only update if month changed to avoid loops
        if (mid.getMonth() !== currentViewDate.getMonth() || mid.getFullYear() !== currentViewDate.getFullYear()) {
            setCurrentViewDate(mid);
        }
    };

    const handleDateClick = (arg: any) => {
      setSelectedDate(arg.dateStr);
      setSelectedUser('');
      setSelectedShift('');
      setEditingScheduleId(null);
      setIsEventEdit(false);
      setOpen(true);
    };

    const handleEventClick = (arg: any) => {
      const props = arg.event.extendedProps;
      if (props.isLog) {
          setSelectedLog({
              id: arg.event.id,
              ...props,
              start: arg.event.start,
              end: arg.event.end
          });
          setLogOpen(true);
          return;
      }

      setSelectedDate(arg.event.startStr);
      setSelectedUser(props.userId.toString());
      setSelectedShift(props.shiftId.toString());
      setEditingScheduleId(props.scheduleId);
      setIsEventEdit(true);
      setOpen(true);
    };

    const handleUserChange = (userId: string) => {
      setSelectedUser(userId);
      if (!isEventEdit && selectedDate && schedData?.workSchedules) {
          const existingSchedule = schedData.workSchedules.find(
             (s: WorkSchedule) => s.user.id === parseInt(userId) && s.date === selectedDate
         );
         
         if (existingSchedule) {
             setSelectedShift(existingSchedule.shift.id.toString());
             setEditingScheduleId(existingSchedule.id);
         }
         else {
             setSelectedShift('');
             setEditingScheduleId(null);
         }
     }
    };

    const handleSaveSchedule = async () => {
      try {
        await setSchedule({
          variables: {
            userId: parseInt(selectedUser),
            shiftId: parseInt(selectedShift),
            date: selectedDate
          }
        });
        setOpen(false);
        refetchSched();
      } catch (err) { alert(getErrorMessage(err)); }
    };

    const handleDeleteSchedule = async () => {
      if (!editingScheduleId) return;
      if (window.confirm("Сигурни ли сте, че искате да премахнете тази смяна?")) {
        try {
          await deleteSchedule({ variables: { id: editingScheduleId } });
          setOpen(false);
          refetchSched();
        } catch (err) { alert(getErrorMessage(err)); }
      }
    };

    const handleDeleteTimeLog = async () => {
        if (!selectedLog) return;
        if (!selectedLog.logId) return;
        
        if (window.confirm(`Сигурни ли сте, че искате да изтриете този запис (ID: ${selectedLog.logId})?`)) {
            try {
                await deleteTimeLog({ variables: { id: selectedLog.logId } });
                setLogOpen(false);
                await refetchLogs();
            } catch (e: unknown) {
                alert("Грешка при изтриване: " + (e as Error).message);
            }
        }
    };

    // --- Share & Print Handlers ---
    const handlePrint = () => {
        window.print();
    };

    const handleShare = async () => {
        const url = window.location.href;
        const title = `График за ${dayjs(currentViewDate).format('MMMM YYYY')}`;
        
        if (navigator.share) {
            try {
                await navigator.share({
                    title: title,
                    text: `Разгледайте работния график`,
                    url: url
                });
            } catch (error) { console.log('Error sharing', error); }
        } else {
            try {
                await navigator.clipboard.writeText(url);
                alert('Линкът е копиран в клипборда!');
            } catch {
                alert('Неуспешно копиране на линка.');
            }
        }
    };

    const scheduleEvents = schedData?.workSchedules.map((s: WorkSchedule) => {
      const shiftType = s.shift?.shiftType || 'regular';
      let bgColor = ShiftTypeColors[shiftType] || ShiftTypeColors.regular;

      if (!s.shift) {
          bgColor = ShiftTypeColors.missing;
      }

      return {
          title: s.user.firstName ? `${s.user.firstName} ${s.user.lastName || ''}` : s.user.email,
          date: s.date,
          backgroundColor: bgColor,
          borderColor: bgColor,
          extendedProps: {
              scheduleId: s.id,
              userId: s.user.id,
              shiftId: s.shift?.id || '',
              shiftType: s.shift ? shiftType : 'missing',
              startTime: s.shift?.startTime,
              endTime: s.shift?.endTime
          }
      };
    }) || [];

    const logEvents = logsData?.timeLogs.map((l: TimeLog) => {
        const isManual = l.isManual;
        const color = isManual ? ShiftTypeColors.manual_log : ShiftTypeColors.auto_log;
        
        return {
            title: `${isManual ? '(Админ) ' : ''}[${l.id}] ${l.user.firstName || ''} ${l.user.lastName || ''} (${l.user.email})`.trim(),
            start: l.startTime,
            end: l.endTime,
            backgroundColor: color,
            borderColor: color,
            extendedProps: {
                isLog: true,
                isManual: l.isManual,
                logId: l.id,
                user: l.user
            }
        };
    }) || [];

    const holidayEvents = holidaysData?.publicHolidays.map((h: PublicHoliday) => ({
      title: `${h.localName || h.name}`,
      date: h.date,
      display: 'background',
      extendedProps: { isHoliday: true },
      allDay: true
    })) || [];

    const orthodoxHolidayEvents = includeOrthodox ? (orthodoxHolidaysData?.orthodoxHolidays.map((h: PublicHoliday) => ({
      title: `${h.localName || h.name} (Правосл.)`,
      date: h.date,
      display: 'background',
      backgroundColor: '#E8F5E9',
      extendedProps: { isHoliday: true, isOrthodox: true },
      allDay: true
    })) || []) : [];

    const events = [...scheduleEvents, ...logEvents, ...holidayEvents, ...orthodoxHolidayEvents];

    return (
      <Box sx={{ mt: 3, '& .fc': { borderRadius: 2, overflow: 'hidden', bgcolor: 'background.paper', p: isMobile ? 1 : 2, boxShadow: 1 } }}>
        
        {/* Actions Toolbar */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }} className="no-print">
            <Box>
                <Tooltip title="Приложи шаблон за ротация на смени" arrow>
                    <Button variant="outlined" color="secondary" onClick={() => setApplyTmplOpen(true)}>
                        Приложи Шаблон (Ротация)
                    </Button>
                </Tooltip>
            </Box>
            <Stack direction="row" spacing={1}>
                <Tooltip title="Генерирай линк за споделяне на текущия изглед" arrow>
                    <Button variant="outlined" startIcon={<ShareIcon />} onClick={handleShare}>
                        Сподели
                    </Button>
                </Tooltip>
                <Tooltip title="Принтирай графика" arrow>
                    <Button variant="contained" startIcon={<PrintIcon />} onClick={handlePrint}>
                        Принтирай
                    </Button>
                </Tooltip>
            </Stack>
        </Box>

        <Dialog open={applyTmplOpen} onClose={() => setApplyTmplOpen(false)} maxWidth="xs" fullWidth>
            <DialogTitle>Прилагане на ротация</DialogTitle>
            <DialogContent>
                <TextField
                    select fullWidth label="Изберете шаблон" margin="normal"
                    value={selectedTmpl} onChange={e => setSelectedTmpl(e.target.value)}
                >
                    {tmplData?.scheduleTemplates?.map((t: ScheduleTemplate) => (
                        <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
                    )) || <MenuItem disabled value="">Зареждане...</MenuItem>}
                </TextField>
                <TextField
                    select fullWidth label="Служител" margin="normal"
                    value={tmplUserId} onChange={e => setTmplUserId(e.target.value)}
                >
                    {usersData?.users?.users?.map((u: User) => (
                        <MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>
                    )) || <MenuItem disabled value="">Зареждане...</MenuItem>}
                </TextField>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    <TextField 
                        fullWidth label="От дата" type="date" margin="normal"
                        InputLabelProps={{ shrink: true }}
                        value={tmplStartDate} onChange={e => setTmplStartDate(e.target.value)}
                        slotProps={{
                          input: {
                            endAdornment: (
                              <InputAdornment position="end">
                                <InfoIcon helpText="Начална дата за прилагане на шаблона" />
                              </InputAdornment>
                            )
                          }
                        }}
                    />
                    <TextField 
                        fullWidth label="До дата" type="date" margin="normal"
                        InputLabelProps={{ shrink: true }}
                        value={tmplEndDate} onChange={e => setTmplEndDate(e.target.value)}
                        slotProps={{
                          input: {
                            endAdornment: (
                              <InputAdornment position="end">
                                <InfoIcon helpText="Крайна дата за прилагане на шаблона" />
                              </InputAdornment>
                            )
                          }
                        }}
                    />
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setApplyTmplOpen(false)}>Отказ</Button>
                <Button variant="contained" onClick={handleApplyTemplate} disabled={!selectedTmpl || !tmplUserId || !tmplStartDate || !tmplEndDate}>
                    Приложи
                </Button>
            </DialogActions>
        </Dialog>

        {logsError && <Alert severity="error" sx={{ mb: 2 }}>Error fetching logs: {logsError.message}</Alert>}
        {logsLoading && <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}><CircularProgress /></Box>}
        
        <Box className="printable-calendar">
            <FullCalendar
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin]}
            initialView={isMobile ? "listMonth" : "dayGridMonth"}
            locale={bgLocale}
            firstDay={1}
            headerToolbar={isMobile ? {
                left: 'prev,next',
                center: 'title',
                right: 'today'
            } : {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,listMonth'
            }}
            events={events}
            height="auto"
            eventContent={(eventInfo) => <ShiftEventContent eventInfo={eventInfo} />}
            dateClick={handleDateClick}
            eventClick={handleEventClick}
            datesSet={handleDatesSet}
            />
        </Box>

        <Box className="printable-legend">
            <ShiftLegend 
                showAdminItems={true} 
                holidays={[...(holidaysData?.publicHolidays || []), ...(includeOrthodox ? (orthodoxHolidaysData?.orthodoxHolidays || []) : [])].filter((h: PublicHoliday) => {
                    const d = new Date(h.date);
                    return d.getMonth() === currentViewDate.getMonth() && d.getFullYear() === currentViewDate.getFullYear();
                })}
                monthlyNorm={normData?.monthlyWorkDays ? { 
                    days: normData.monthlyWorkDays.daysCount, 
                    hours: normData.monthlyWorkDays.daysCount * 8 
                } : null}
            />
        </Box>
  
        <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="xs">
          <DialogTitle>{editingScheduleId ? 'Редактиране на график' : `Задаване на график за ${formatDate(selectedDate)}`}</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 1 }}>
                <TextField
                select
                fullWidth
                label="Служител"
                value={selectedUser}
                onChange={(e) => handleUserChange(e.target.value)}
                margin="normal"
                disabled={isEventEdit}
                >
                {usersData?.users?.users?.map((u: User) => (
                    <MenuItem key={u.id} value={u.id}>
                    {u.firstName} {u.lastName} ({u.email})
                    </MenuItem>
                )) || <MenuItem disabled value="">Зареждане...</MenuItem>}
                </TextField>
    
                <TextField
                select
                fullWidth
                label="Смяна"
                value={selectedShift}
                onChange={(e) => setSelectedShift(e.target.value)}
                margin="normal"
                >
                {shiftsData?.shifts?.map((s: WorkSchedule) => (
                    <MenuItem key={s.id} value={s.id}>
                    {s.name} ({(s.startTime || '').substring(0, 5)} - {(s.endTime || '').substring(0, 5)})
                    </MenuItem>
                )) || <MenuItem disabled value="">Зареждане...</MenuItem>}
                </TextField>
            </Box>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'space-between', px: 3, pb: 2 }}>
           <Box>
            {editingScheduleId && (
                <IconButton onClick={handleDeleteSchedule} color="error" title="Изтрий смяна">
                <DeleteIcon />
                </IconButton>
            )}
            <Button 
                startIcon={<AccessTimeIcon />}
                color="secondary"
                onClick={() => {
                    setOpen(false);
                    setManualLogOpen(true);
                }}
            >
                Добави часове
            </Button>
           </Box>
          <Box>
            <Button onClick={() => setOpen(false)}>Отказ</Button>
            <Button variant="contained" onClick={handleSaveSchedule} disabled={!selectedUser || !selectedShift}>
                Запази
            </Button>
          </Box>
        </DialogActions>
      </Dialog>
      
      <ManualTimeLogModal
        key={`${selectedDate}-${selectedUser}`}
        open={manualLogOpen}
        onClose={() => setManualLogOpen(false)}

        users={usersData?.users?.users || []}
        initialDate={selectedDate}
        initialUserId={selectedUser}
        refetch={refetchLogs}
      />

      <Dialog open={logOpen} onClose={() => setLogOpen(false)} fullWidth maxWidth="xs">
          <DialogTitle>Детайли за отработено време</DialogTitle>
          <DialogContent>
              {selectedLog && (
                  <Box sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        Начало: {
                            (selectedLog.start instanceof Date 
                                ? selectedLog.start 
                                : selectedLog.start 
                                ? new Date(selectedLog.start.endsWith('Z') ? selectedLog.start : selectedLog.start + 'Z')
                                : '-'
                            ).toLocaleString('bg-BG')
                        }
                      </Typography>
                      <Typography variant="body2">
                        Край: {
                            selectedLog.end 
                                ? (selectedLog.end instanceof Date 
                                    ? selectedLog.end 
                                    : new Date(selectedLog.end.endsWith('Z') ? selectedLog.end : selectedLog.end + 'Z')
                                  ).toLocaleString('bg-BG') 
                                : 'Активен'
                        }
                      </Typography>
                      <Typography variant="body2">Ръчно въведено: {selectedLog.isManual ? 'Да' : 'Не'}</Typography>
                      <Typography variant="caption" color="text.secondary">ID: {selectedLog.logId}</Typography>
                  </Box>
              )}
          </DialogContent>
          <DialogActions>
              <IconButton onClick={handleDeleteTimeLog} color="error" title="Изтрий запис">
                  <DeleteIcon />
              </IconButton>
              <Button onClick={() => setLogOpen(false)}>Затвори</Button>
          </DialogActions>
      </Dialog>

      {/* Print Styles for Calendar View */}
      <style>{`
        @media print {
            .no-print { display: none !important; }
            body, html { visibility: hidden; }
            #root { visibility: hidden; }
            
            /* Show only the calendar and legend */
            .printable-calendar, .printable-legend { 
                visibility: visible; 
            }
            
            .printable-calendar {
                position: absolute;
                top: 0;
                left: 0;
                width: 100% !important;
            }
            
            .printable-legend {
                position: absolute;
                top: 100%; /* Below calendar? might overlap depending on calendar height */
                left: 0;
                width: 100%;
                margin-top: 20px;
            }
            
            .fc-header-toolbar { display: none; } 
            @page { size: landscape; margin: 10mm; }
        }
      `}</style>
    </Box>
  );
};

const BULK_SET_SCHEDULE_MUTATION = gql`
  mutation BulkSetSchedule($userIds: [Int!]!, $shiftId: Int!, $startDate: Date!, $endDate: Date!, $daysOfWeek: [Int!]!) {
    bulkSetSchedule(userIds: $userIds, shiftId: $shiftId, startDate: $startDate, endDate: $endDate, daysOfWeek: $daysOfWeek)
  }
`;

// --- Components ---

const BulkAssign: React.FC = () => {
  const { data: usersData, loading: usersLoading, error: usersError } = useQuery(GET_USERS_QUERY, { variables: { limit: 1000 } });
  const { data: shiftsData, loading: shiftsLoading } = useQuery(GET_SHIFTS_QUERY);
  const [bulkSet, { loading: submitting }] = useMutation(BULK_SET_SCHEDULE_MUTATION);

  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [selectedShift, setSelectedShift] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4]);

  const handleDayToggle = (day: number) => {
    setDays(prev => prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]);
  };

  const handleSubmit = async () => {
    try {
      await bulkSet({
        variables: {
          userIds: selectedUsers,
          shiftId: parseInt(selectedShift),
          startDate,
          endDate,
          daysOfWeek: days
        }
      });
      alert('Графиците са генерирани успешно!');
      setSelectedUsers([]);
    } catch (err) { alert(getErrorMessage(err)); }
  };

  const dayNames = ['Пон', 'Вт', 'Ср', 'Чет', 'Пет', 'Съб', 'Нед'];

  if (usersLoading || shiftsLoading) return <CircularProgress sx={{ mt: 3 }} />;
  if (usersError) return <Alert severity="error" sx={{ mt: 3 }}>Грешка при зареждане на служители: {usersError.message}</Alert>;

  return (
    <Box sx={{ mt: 3, maxWidth: 800 }}>
      <Typography variant="h6" gutterBottom>Масово назначаване на смени</Typography>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <TextField
            select
            fullWidth
            label="Изберете служители"
            SelectProps={{ 
              multiple: true, 
              value: selectedUsers, 
              onChange: (e) => setSelectedUsers(e.target.value as number[]),
              renderValue: (selected) => {
                const selectedArray = selected as number[];
                return usersData?.users?.users
                  ?.filter((u: User) => selectedArray.includes(u.id))
                  .map((u: User) => u.firstName ? `${u.firstName} ${u.lastName || ''}` : u.email)
                  .join(', ');
              }
            }}
            margin="normal"
          >
            {usersData?.users?.users?.map((u: User) => (
              <MenuItem key={u.id} value={u.id}>
                {u.firstName ? `${u.firstName} ${u.lastName || ''}` : u.email}
              </MenuItem>
            )) || <MenuItem disabled value="">Зареждане...</MenuItem>}
          </TextField>
          <TextField
            select
            fullWidth
            label="Смяна"
            value={selectedShift}
            onChange={(e) => setSelectedShift(e.target.value)}
            margin="normal"
          >
            {shiftsData?.shifts?.map((s: WorkSchedule) => (
              <MenuItem key={s.id} value={s.id}>{s.name} ({(s.startTime || '').substring(0, 5)} - {(s.endTime || '').substring(0, 5)})</MenuItem>
            )) || <MenuItem disabled value="">Зареждане...</MenuItem>}
          </TextField>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth label="От дата" type="date" value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }} margin="normal"
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoIcon helpText="Начална дата за назначаване на смени" />
                    </InputAdornment>
                  )
                }
              }}
            />
            <TextField
              fullWidth label="До дата" type="date" value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }} margin="normal"
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoIcon helpText="Крайна дата за назначаване на смени" />
                    </InputAdornment>
                  )
                }
              }}
            />
          </Box>
          <Typography variant="subtitle2" sx={{ mt: 2 }}>Работни дни от седмицата:</Typography>
          <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {dayNames.map((name, index) => (
              <Button
                key={name}
                variant={days.includes(index) ? "contained" : "outlined"}
                onClick={() => handleDayToggle(index)}
                size="small"
              >
                {name}
              </Button>
            ))}
          </Box>
        </Grid>
        <Grid size={{ xs: 12 }}>
          <Button variant="contained" size="large" onClick={handleSubmit} disabled={submitting || !selectedUsers.length || !selectedShift || !startDate || !endDate}>
            {submitting ? 'Генериране...' : 'Генерирай графици'}
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};

interface Props {
  tab?: string;
}

const SchedulesPage: React.FC<Props> = ({ tab }) => {
  const tabs = [
    { label: 'Календар', path: '/admin/schedules/calendar' },
    { label: 'Текущ график', path: '/admin/schedules/current' },
    { label: 'Управление на смени', path: '/admin/schedules/shifts' },
    { label: 'Шаблони и Ротации', path: '/admin/schedules/templates' },
    { label: 'Масово назначаване', path: '/admin/schedules/bulk' },
  ];

  return (
    <TabbedPage tabs={tabs} defaultTabPath="/admin/schedules/calendar">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">Работни графици</Typography>
      </Box>
      {tab === 'calendar' && <CalendarView />}
      {tab === 'current' && <CurrentScheduleView />}
      {tab === 'shifts' && <ShiftManager />}
      {tab === 'templates' && <ScheduleTemplatesManager />}
      {tab === 'bulk' && <BulkAssign />}
    </TabbedPage>
  );
};

export default SchedulesPage;
