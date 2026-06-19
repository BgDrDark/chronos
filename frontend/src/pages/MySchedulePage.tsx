import React, { useState } from 'react';
import { getErrorMessage } from '../types';
import { 
  Container, Typography, Box, CircularProgress, Alert, Paper, Dialog, 
  DialogTitle, DialogContent, Button, DialogActions, Stack,
  useTheme, useMediaQuery, TextField, MenuItem
} from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import MedicalServicesIcon from '@mui/icons-material/MedicalServices';
import BeachAccessIcon from '@mui/icons-material/BeachAccess';
import WeekendIcon from '@mui/icons-material/Weekend';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import { formatDate } from '../utils/dateUtils';
import { ShiftTypeColors } from '../utils/shiftUtils';
import ShiftLegend from '../components/ShiftLegend';
import ShiftEventContent from '../components/ShiftEventContent';
import { useError, extractErrorMessage } from '../context/ErrorContext';
import {
  GET_MY_SCHEDULES_QUERY,
  GET_PUBLIC_HOLIDAYS_QUERY,
  GET_ORTHODOX_HOLIDAYS_QUERY,
  REQUEST_LEAVE_MUTATION,
  GET_SWAP_DATA,
  MY_FUTURE_SCHEDULES,
  USER_FUTURE_SCHEDULES,
  CREATE_SWAP_MUTATION,
  GET_APPROVED_LEAVES_IN_RANGE
} from '../graphql/queries';
import type { User, WorkSchedule } from '../types';

const LeaveTypeColors: Record<string, string> = {
  annual_paid: '#2196F3',
  paid_leave: '#2196F3',
  sick: '#f44336',
  sick_leave: '#f44336',
  unpaid: '#9e9e9e',
  unpaid_leave: '#9e9e9e',
  maternity: '#9c27b0',
  paternity: '#9c27b0',
  parental: '#e91e63',
  child_care: '#ff9800',
  study: '#009688',
};

const LeaveTypeLabels: Record<string, string> = {
  annual_paid: 'Платен годишен отпуск',
  paid_leave: 'Платен годишен отпуск',
  sick: 'Болничен',
  sick_leave: 'Болничен',
  unpaid: 'Неплатен отпуск',
  unpaid_leave: 'Неплатен отпуск',
  maternity: 'Материнство',
  paternity: 'Бащинство',
  parental: 'Родителски',
  child_care: 'Грижа за дете',
  study: 'Учебен',
};

const MySchedulePage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { showError, showSuccess } = useError();
  
  const [open, setOpen] = useState(false);
  const [requestOpen, setRequestOpen] = useState(false);
  const [swapDialogOpen, setSwapDialogOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [endDate, setEndDate] = useState<string>('');
  const [currentEvent, setCurrentEvent] = useState<any | null>(null);
  
  const [leaveType, setLeaveType] = useState('paid_leave');
  const [reason, setReason] = useState('');

  const [mySchedId, setMySchedId] = useState('');
  const [targetUserId, setTargetUserId] = useState('');
  const [targetSchedId, setTargetSchedId] = useState('');

  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
  const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];

  const { data, loading, error, refetch } = useQuery(GET_MY_SCHEDULES_QUERY, {
    variables: { startDate: startOfMonth, endDate: endOfMonth }
  });

  const { data: holidaysData } = useQuery(GET_PUBLIC_HOLIDAYS_QUERY, {
    variables: { year: today.getFullYear() }
  });

  const includeOrthodox = localStorage.getItem('include_orthodox_holidays') === 'true';
  const { data: orthodoxHolidaysData } = useQuery(GET_ORTHODOX_HOLIDAYS_QUERY, {
    variables: { year: today.getFullYear() },
    skip: !includeOrthodox
  });

  const { data: leavesData } = useQuery(GET_APPROVED_LEAVES_IN_RANGE, {
    variables: { startDate: startOfMonth, endDate: endOfMonth },
  });

  const [requestLeave, { loading: saving }] = useMutation(REQUEST_LEAVE_MUTATION, {
    refetchQueries: [GET_MY_SCHEDULES_QUERY, GET_APPROVED_LEAVES_IN_RANGE]
  });

  const { data: swapData } = useQuery(GET_SWAP_DATA);

  const nextMonth = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const { data: myScheds } = useQuery(MY_FUTURE_SCHEDULES, {
    variables: { startDate: startOfMonth, endDate: nextMonth }
  });

  const { data: allScheds } = useQuery(USER_FUTURE_SCHEDULES, {
    variables: { startDate: startOfMonth, endDate: nextMonth },
    skip: !targetUserId
  });

  const [createSwap, { loading: swapSaving }] = useMutation(CREATE_SWAP_MUTATION);

  const scheduleEvents = data?.mySchedules.map((s: any) => {
    const shiftType = s.shift?.shiftType || 'regular';
    const bgColor = ShiftTypeColors[shiftType] || ShiftTypeColors.regular;

    return {
      title: s.shift?.name || 'Смяна',
      date: s.date,
      backgroundColor: bgColor,
      borderColor: bgColor,
      extendedProps: {
        scheduleId: s.id,
        shiftType: shiftType,
        shiftName: s.shift?.name,
        startTime: s.shift?.startTime,
        endTime: s.shift?.endTime
      }
    };
  }) || [];

  const holidayEvents = holidaysData?.publicHolidays.map((h: any) => ({
    title: h.localName || h.name,
    date: h.date,
    extendedProps: { isHoliday: true },
    allDay: true
  })) || [];

  const orthodoxHolidayEvents = includeOrthodox ? (orthodoxHolidaysData?.orthodoxHolidays.map((h: any) => ({
    title: `${h.localName || h.name} (Правосл.)`,
    date: h.date,
    backgroundColor: '#E8F5E9',
    extendedProps: { isHoliday: true, isOrthodox: true },
    allDay: true
  })) || []) : [];

  const leaveEvents = leavesData?.approvedLeaveRequestsInRange.flatMap((l: any) => {
    const color = LeaveTypeColors[l.leaveType] || '#757575';
    const label = LeaveTypeLabels[l.leaveType] || l.leaveType;
    const start = new Date(l.startDate);
    const end = new Date(l.endDate);
    const days: any[] = [];
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split('T')[0];
      days.push({
        title: label,
        date: dateStr,
        backgroundColor: color,
        borderColor: color,
        textColor: '#fff',
        extendedProps: { isLeave: true, leaveId: l.id, leaveType: l.leaveType },
      });
    }
    return days;
  }) || [];

  const events = [...scheduleEvents, ...leaveEvents, ...holidayEvents, ...orthodoxHolidayEvents];

  const currentMonthHolidays = [...(holidaysData?.publicHolidays || []), ...(includeOrthodox ? (orthodoxHolidaysData?.orthodoxHolidays || []) : [])].filter((h: any) => {
      const d = new Date(h.date);
      const start = new Date(startOfMonth);
      const end = new Date(endOfMonth);
      return d >= start && d <= end;
  });

  const handleDateClick = (arg: any) => {
    setSelectedDate(arg.dateStr);
    setEndDate(arg.dateStr);
    const event = events.find((e: any) => e.date === arg.dateStr && !e.extendedProps?.isHoliday);
    setCurrentEvent(event);
    setOpen(true);
  };

  const handleEventClick = (arg: any) => {
    if (arg.event.extendedProps.isHoliday) return;
    setSelectedDate(arg.event.startStr);
    setEndDate(arg.event.startStr);
    setCurrentEvent({
        title: arg.event.title,
        extendedProps: arg.event.extendedProps
    });
    setOpen(true);
  };



  const initRequest = (type: string) => {
      setLeaveType(type);
      setReason('');
      setEndDate(selectedDate || '');
      setOpen(false);
      setRequestOpen(true);
  };

  const handleRequestSubmit = async () => {
    if (!selectedDate) return;
    if (endDate < selectedDate) {
      showError('Крайната дата трябва да е след началната.');
      return;
    }
    try {
      await requestLeave({
        variables: {
          startDate: selectedDate,
          endDate: endDate,
          leaveType: leaveType,
          reason: reason
        }
      });
      setRequestOpen(false);
      showSuccess('Заявката е изпратена успешно!');
      refetch();
    } catch (e) {
      showError(extractErrorMessage(e));
    }
  };

  const initSwap = () => {
    if (!currentEvent?.extendedProps?.scheduleId) {
      showError('Няма избрана смяна за размяна.');
      return;
    }
    setMySchedId(String(currentEvent.extendedProps.scheduleId));
    setTargetUserId('');
    setTargetSchedId('');
    setOpen(false);
    setSwapDialogOpen(true);
  };

  const handleSwapSubmit = async () => {
    if (!mySchedId || !targetUserId || !targetSchedId) {
      showError('Попълнете всички полета за размяна.');
      return;
    }
    try {
      await createSwap({
        variables: {
          reqSchedId: parseInt(mySchedId),
          targetUserId: parseInt(targetUserId),
          targetSchedId: parseInt(targetSchedId)
        }
      });
      showSuccess('Заявката за размяна е изпратена!');
      setSwapDialogOpen(false);
      refetch();
    } catch (err: unknown) {
      showError(extractErrorMessage(err));
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Container sx={{ mt: 4 }}><Alert severity="error">Грешка: {error.message}</Alert></Container>;

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom fontWeight="bold">Моят график</Typography>
      <Paper sx={{ 
        p: isMobile ? 0.5 : 1, 
        borderRadius: 2, 
        boxShadow: 2,
        '& .fc': { fontSize: '0.85rem' },
        '& .fc .fc-toolbar': { mb: 1, gap: 0.5 },
        '& .fc .fc-toolbar-title': { fontSize: '1.1rem' },
        '& .fc .fc-button': { py: 0.2, px: 1, fontSize: '0.8rem' },
        '& .fc-daygrid-day-frame': { minHeight: isMobile ? '60px' : '80px' },
        '& .fc-event': { 
            border: 'none',
            cursor: 'pointer',
        }
      }}>
        <FullCalendar
          plugins={[dayGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          locale="bg"
          firstDay={1}
          headerToolbar={{
            left: 'prev,next',
            center: 'title',
            right: 'today'
          }}
          events={events}
          height="auto"
          dayMaxEvents={3}
          eventContent={(eventInfo) => <ShiftEventContent eventInfo={eventInfo} minimal={true} />}
          dateClick={handleDateClick}
          eventClick={handleEventClick}
        />
      </Paper>
      
      <ShiftLegend holidays={currentMonthHolidays} />

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>Преглед на деня: {formatDate(selectedDate)}</DialogTitle>
        <DialogContent>
          {currentEvent ? (
            <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Текущ статус:</Typography>
              <Typography variant="h6" color="primary">{currentEvent.title}</Typography>
              {currentEvent.extendedProps?.startTime && (
                <Typography variant="body2">
                  Часове: {currentEvent.extendedProps.startTime.slice(0,5)} - {currentEvent.extendedProps.endTime.slice(0,5)}
                </Typography>
              )}
            </Box>
          ) : (
             <Alert severity="info" sx={{ mb: 2 }}>Няма записани събития за този ден.</Alert>
          )}

          {!currentEvent?.extendedProps?.isLeave && (
            <>
              <Typography variant="subtitle2" gutterBottom>Заяви отсъствие:</Typography>
              <Stack spacing={1}>
            <Button 
                variant="outlined" 
                color="warning" 
                startIcon={<BeachAccessIcon />} 
                onClick={() => initRequest('annual_paid')}
            >
                Заяви Платен отпуск
            </Button>
            <Button 
                variant="outlined" 
                color="error" 
                startIcon={<MedicalServicesIcon />} 
                onClick={() => initRequest('sick')}
            >
                Заяви Болничен
            </Button>
            <Button 
                variant="outlined" 
                color="info" 
                startIcon={<WeekendIcon />} 
                onClick={() => initRequest('unpaid')}
            >
                Заяви Неплатен отпуск
            </Button>
              </Stack>
            </>
          )}

          {currentEvent && !currentEvent.extendedProps?.isLeave && (
            <>
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>Размяна на смяна:</Typography>
              <Button
                variant="outlined"
                color="primary"
                fullWidth
                startIcon={<SwapHorizIcon />}
                onClick={initSwap}
              >
                Размяна на смяна
              </Button>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Затвори</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={requestOpen} onClose={() => setRequestOpen(false)} fullWidth maxWidth="xs">
          <DialogTitle>Заявка за {(LeaveTypeLabels[leaveType] || leaveType).toLowerCase()}</DialogTitle>
          <DialogContent>
              <Stack spacing={2} sx={{ mt: 1 }}>
                <TextField
                    label="Начална дата"
                    type="date"
                    fullWidth
                    value={selectedDate || ''}
                    InputProps={{ readOnly: true }}
                    size="small"
                />
                <TextField
                    label="Крайна дата"
                    type="date"
                    fullWidth
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    inputProps={{ min: selectedDate || '' }}
                    size="small"
                />
                <TextField 
                    label="Причина (по избор)" 
                    multiline 
                    rows={3} 
                    fullWidth 
                    value={reason} 
                    onChange={(e) => setReason(e.target.value)} 
                    size="small"
                />
              </Stack>
          </DialogContent>
          <DialogActions>
              <Button onClick={() => setRequestOpen(false)}>Отказ</Button>
              <Button variant="contained" onClick={handleRequestSubmit} disabled={saving}>Изпрати</Button>
          </DialogActions>
      </Dialog>

      <Dialog open={swapDialogOpen} onClose={() => setSwapDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Размяна на смяна</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              select fullWidth label="Моя смяна" size="small"
              value={mySchedId} onChange={(e) => setMySchedId(e.target.value)}
            >
              {myScheds?.mySchedules?.length > 0 ? myScheds.mySchedules.map((s: WorkSchedule) => (
                <MenuItem key={s.id} value={s.id}>{s.date} - {s.shift?.name}</MenuItem>
              )) : <MenuItem disabled value="">Няма налични смени</MenuItem>}
            </TextField>

            <TextField
              select fullWidth label="Колега" size="small"
              value={targetUserId} onChange={(e) => setTargetUserId(e.target.value)}
            >
              {swapData?.users?.users?.filter((u: User) => String(u.id) !== String(swapData.me.id)).length > 0
                ? swapData.users.users
                    .filter((u: User) => String(u.id) !== String(swapData.me.id))
                    .map((u: User) => (
                      <MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>
                    ))
                : <MenuItem disabled value="">Няма налични колеги</MenuItem>}
            </TextField>

            <TextField
              select fullWidth label="Смяна на колегата" size="small"
              value={targetSchedId} onChange={(e) => setTargetSchedId(e.target.value)}
              disabled={!targetUserId}
            >
              {allScheds?.workSchedules?.filter((s: WorkSchedule) => String(s.user.id) === String(targetUserId)).length > 0
                ? allScheds.workSchedules
                    .filter((s: WorkSchedule) => String(s.user.id) === String(targetUserId))
                    .map((s: WorkSchedule) => (
                      <MenuItem key={s.id} value={s.id}>{s.date} - {s.shift?.name}</MenuItem>
                    ))
                : <MenuItem disabled value="">Няма налични смени</MenuItem>
              }
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSwapDialogOpen(false)}>Отказ</Button>
          <Button variant="contained" onClick={handleSwapSubmit} disabled={swapSaving || !mySchedId || !targetSchedId}>
            Изпрати покана
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MySchedulePage;
