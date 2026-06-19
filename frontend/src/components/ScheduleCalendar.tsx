import React, { useState } from 'react';
import dayjs from 'dayjs';
import { useQuery, useMutation } from '@apollo/client';
import {
  Box, Typography, Button, Stack, Tooltip, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem, Alert, CircularProgress,
  useTheme, useMediaQuery, InputAdornment
} from '@mui/material';
import { Share as ShareIcon, Print as PrintIcon, AccessTime as AccessTimeIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { IconButton } from '@mui/material';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import listPlugin from '@fullcalendar/list';
import bgLocale from '@fullcalendar/core/locales/bg';
import { useError, extractErrorMessage } from '../context/ErrorContext';
import { formatDate } from '../utils/dateUtils';
import { ShiftTypeColors } from '../utils/shiftUtils';
import ShiftLegend from '../components/ShiftLegend';
import ShiftEventContent from '../components/ShiftEventContent';
import ManualTimeLogModal from '../components/ManualTimeLogModal';
import { InfoIcon } from '../components/ui/InfoIcon';
import {
  GET_SHIFTS_QUERY,
  GET_SCHEDULES_QUERY,
  GET_USERS_QUERY,
  GET_PUBLIC_HOLIDAYS_QUERY,
  GET_ORTHODOX_HOLIDAYS_QUERY,
  GET_MONTHLY_WORK_DAYS,
  SET_SCHEDULE_MUTATION,
  DELETE_SCHEDULE_MUTATION,
  GET_TEMPLATES_FOR_PREVIEW,
  APPLY_SCHEDULE_TEMPLATE,
  GET_APPROVED_LEAVES_IN_RANGE,
} from '../graphql/queries';

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
  annual_paid: 'Платен',
  paid_leave: 'Платен',
  sick: 'Болничен',
  sick_leave: 'Болничен',
  unpaid: 'Неплатен',
  unpaid_leave: 'Неплатен',
  maternity: 'Материнство',
  paternity: 'Бащинство',
  parental: 'Родителски',
  child_care: 'Грижа',
  study: 'Учебен',
};

const ScheduleCalendar: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { showError, showSuccess } = useError();

  const [currentViewDate, setCurrentViewDate] = useState(new Date());
  const [open, setOpen] = useState(false);
  const [manualLogOpen, setManualLogOpen] = useState(false);
  const [applyTmplOpen, setApplyTmplOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedShift, setSelectedShift] = useState('');
  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null);
  const [isEventEdit, setIsEventEdit] = useState(false);
  const [selectedTmpl, setSelectedTmpl] = useState('');
  const [tmplStartDate, setTmplStartDate] = useState('');
  const [tmplEndDate, setTmplEndDate] = useState('');
  const [tmplUserId, setTmplUserId] = useState('');

  const year = currentViewDate.getFullYear();
  const month = currentViewDate.getMonth() + 1;
  const startDate = new Date(year, month - 1, 1).toISOString().split('T')[0];
  const endDate = new Date(year, month, 0).toISOString().split('T')[0];

  const { data: usersData } = useQuery(GET_USERS_QUERY, { variables: { limit: 1000 } });
  const { data: shiftsData } = useQuery(GET_SHIFTS_QUERY);
  const { data: tmplData } = useQuery(GET_TEMPLATES_FOR_PREVIEW);
  const { data: holidaysData } = useQuery(GET_PUBLIC_HOLIDAYS_QUERY, { variables: { year } });
  const includeOrthodox = localStorage.getItem('include_orthodox_holidays') === 'true';
  const { data: orthodoxHolidaysData } = useQuery(GET_ORTHODOX_HOLIDAYS_QUERY, { variables: { year }, skip: !includeOrthodox });
  const { data: normData } = useQuery(GET_MONTHLY_WORK_DAYS, { variables: { year, month } });
  const { data: leavesData } = useQuery(GET_APPROVED_LEAVES_IN_RANGE, { variables: { startDate, endDate } });
  const { data: schedData, refetch: refetchSched } = useQuery(GET_SCHEDULES_QUERY, { variables: { startDate, endDate } });

  const [setSchedule] = useMutation(SET_SCHEDULE_MUTATION);
  const [deleteSchedule] = useMutation(DELETE_SCHEDULE_MUTATION);
  const [applyTmpl] = useMutation(APPLY_SCHEDULE_TEMPLATE);

  const handleDatesSet = (arg: any) => {
    const start = arg.view.currentStart;
    const end = arg.view.currentEnd;
    const mid = new Date((start.getTime() + end.getTime()) / 2);
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
    if (arg.event.extendedProps.isLeave) return;
    if (arg.event.extendedProps.isHoliday) return;
    const props = arg.event.extendedProps;
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
      const existing = schedData.workSchedules.find(
        (s: any) => s.user.id === parseInt(userId) && s.date === selectedDate
      );
      if (existing) {
        setSelectedShift(existing.shift.id.toString());
        setEditingScheduleId(existing.id);
      } else {
        setSelectedShift('');
        setEditingScheduleId(null);
      }
    }
  };

  const handleSaveSchedule = async () => {
    try {
      await setSchedule({ variables: { userId: parseInt(selectedUser), shiftId: parseInt(selectedShift), date: selectedDate } });
      setOpen(false);
      refetchSched();
      showSuccess('Графикът е запазен.');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const handleDeleteSchedule = async () => {
    if (!editingScheduleId) return;
    try {
      await deleteSchedule({ variables: { id: editingScheduleId } });
      setOpen(false);
      refetchSched();
      showSuccess('Графикът е изтрит.');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const handleApplyTemplate = async () => {
    try {
      await applyTmpl({
        variables: { templateId: parseInt(selectedTmpl), userIds: [parseInt(tmplUserId)], startDate: tmplStartDate, endDate: tmplEndDate }
      });
      setApplyTmplOpen(false);
      showSuccess('Шаблонът е приложен успешно!');
      refetchSched();
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const handlePrint = () => window.print();

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      showSuccess('Линкът е копиран!');
    } catch {
      showError('Неуспешно копиране на линка.');
    }
  };

  const scheduleEvents = schedData?.workSchedules.map((s: any) => {
    const shiftType = s.shift?.shiftType || 'regular';
    const bgColor = s.shift ? (ShiftTypeColors[shiftType] || ShiftTypeColors.regular) : ShiftTypeColors.missing;
    return {
      title: s.user.firstName ? `${s.user.firstName} ${s.user.lastName || ''}` : s.user.email,
      date: s.date,
      backgroundColor: bgColor,
      borderColor: bgColor,
      extendedProps: { scheduleId: s.id, userId: s.user.id, shiftId: s.shift?.id || '', shiftType: s.shift ? shiftType : 'missing' },
    };
  }) || [];

  const holidayEvents = holidaysData?.publicHolidays.map((h: any) => ({
    title: `${h.localName || h.name}`,
    date: h.date,
    display: 'background',
    extendedProps: { isHoliday: true },
    allDay: true,
  })) || [];

  const orthodoxHolidayEvents = includeOrthodox ? (orthodoxHolidaysData?.orthodoxHolidays.map((h: any) => ({
    title: `${h.localName || h.name} (Правосл.)`,
    date: h.date,
    display: 'background',
    backgroundColor: '#E8F5E9',
    extendedProps: { isHoliday: true, isOrthodox: true },
    allDay: true,
  })) || []) : [];

  const leaveEvents = leavesData?.approvedLeaveRequestsInRange.flatMap((l: any) => {
    const color = LeaveTypeColors[l.leaveType] || '#757575';
    const label = LeaveTypeLabels[l.leaveType] || l.leaveType;
    const userName = l.user?.firstName ? `${l.user.firstName} ${l.user.lastName || ''}` : (l.user?.email || '');
    const start = new Date(l.startDate);
    const end = new Date(l.endDate);
    const days: any[] = [];
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split('T')[0];
      days.push({
        title: `${userName} — ${label}`,
        date: dateStr,
        backgroundColor: color,
        borderColor: color,
        textColor: '#fff',
        extendedProps: { isLeave: true, leaveId: l.id, leaveType: l.leaveType, userId: l.user?.id },
      });
    }
    return days;
  }) || [];

  const events = [...scheduleEvents, ...leaveEvents, ...holidayEvents, ...orthodoxHolidayEvents];

  return (
    <Box sx={{ mt: 3, '& .fc': { borderRadius: 2, overflow: 'hidden', bgcolor: 'background.paper', p: isMobile ? 1 : 2, boxShadow: 1 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }} className="no-print">
        <Tooltip title="Приложи шаблон за ротация на смени" arrow>
          <Button variant="outlined" color="secondary" onClick={() => setApplyTmplOpen(true)}>Приложи Шаблон</Button>
        </Tooltip>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Генерирай линк за споделяне" arrow>
            <Button variant="outlined" startIcon={<ShareIcon />} onClick={handleShare}>Сподели</Button>
          </Tooltip>
          <Tooltip title="Принтирай графика" arrow>
            <Button variant="contained" startIcon={<PrintIcon />} onClick={handlePrint}>Принтирай</Button>
          </Tooltip>
        </Stack>
      </Box>

      <Dialog open={applyTmplOpen} onClose={() => setApplyTmplOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Прилагане на ротация</DialogTitle>
        <DialogContent>
          <TextField select fullWidth label="Изберете шаблон" margin="normal" value={selectedTmpl} onChange={e => setSelectedTmpl(e.target.value)}>
            {tmplData?.scheduleTemplates?.map((t: any) => (<MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)) || <MenuItem disabled>Зареждане...</MenuItem>}
          </TextField>
          <TextField select fullWidth label="Служител" margin="normal" value={tmplUserId} onChange={e => setTmplUserId(e.target.value)}>
            {usersData?.users?.users?.map((u: any) => (<MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>)) || <MenuItem disabled>Зареждане...</MenuItem>}
          </TextField>
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            <TextField fullWidth label="От дата" type="date" margin="normal" InputLabelProps={{ shrink: true }} value={tmplStartDate} onChange={e => setTmplStartDate(e.target.value)}
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Начална дата за прилагане на шаблона" /></InputAdornment> } }} />
            <TextField fullWidth label="До дата" type="date" margin="normal" InputLabelProps={{ shrink: true }} value={tmplEndDate} onChange={e => setTmplEndDate(e.target.value)}
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Крайна дата за прилагане на шаблона" /></InputAdornment> } }} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApplyTmplOpen(false)}>Отказ</Button>
          <Button variant="contained" onClick={handleApplyTemplate} disabled={!selectedTmpl || !tmplUserId || !tmplStartDate || !tmplEndDate}>Приложи</Button>
        </DialogActions>
      </Dialog>

      <Box className="printable-calendar">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin]}
          initialView={isMobile ? "listMonth" : "dayGridMonth"}
          locale={bgLocale}
          firstDay={1}
          headerToolbar={isMobile ? { left: 'prev,next', center: 'title', right: 'today' } : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,listMonth' }}
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
          holidays={[...(holidaysData?.publicHolidays || []), ...(includeOrthodox ? (orthodoxHolidaysData?.orthodoxHolidays || []) : [])].filter((h: any) => {
            const d = new Date(h.date);
            return d.getMonth() === currentViewDate.getMonth() && d.getFullYear() === currentViewDate.getFullYear();
          })}
          monthlyNorm={normData?.monthlyWorkDays ? { days: normData.monthlyWorkDays.daysCount, hours: normData.monthlyWorkDays.daysCount * 8 } : null}
        />
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>{editingScheduleId ? 'Редактиране на график' : `Задаване на график за ${formatDate(selectedDate)}`}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1 }}>
            <TextField select fullWidth label="Служител" value={selectedUser} onChange={(e) => handleUserChange(e.target.value)} margin="normal" disabled={isEventEdit}>
              {usersData?.users?.users?.map((u: any) => (<MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName} ({u.email})</MenuItem>)) || <MenuItem disabled>Зареждане...</MenuItem>}
            </TextField>
            <TextField select fullWidth label="Смяна" value={selectedShift} onChange={(e) => setSelectedShift(e.target.value)} margin="normal">
              {shiftsData?.shifts?.map((s: any) => (<MenuItem key={s.id} value={s.id}>{s.name} ({(s.startTime || '').substring(0, 5)} - {(s.endTime || '').substring(0, 5)})</MenuItem>)) || <MenuItem disabled>Зареждане...</MenuItem>}
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'space-between', px: 3, pb: 2 }}>
          <Box>
            {editingScheduleId && (<IconButton onClick={handleDeleteSchedule} color="error"><DeleteIcon /></IconButton>)}
            <Button startIcon={<AccessTimeIcon />} color="secondary" onClick={() => { setOpen(false); setManualLogOpen(true); }}>Добави часове</Button>
          </Box>
          <Box>
            <Button onClick={() => setOpen(false)}>Отказ</Button>
            <Button variant="contained" onClick={handleSaveSchedule} disabled={!selectedUser || !selectedShift}>Запази</Button>
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
        refetch={() => {}}
      />

      <style>{`
        @media print {
          .no-print { display: none !important; }
          body, html { visibility: hidden; }
          #root { visibility: hidden; }
          .printable-calendar, .printable-legend { visibility: visible; }
          .printable-calendar { position: absolute; top: 0; left: 0; width: 100% !important; }
          .printable-legend { position: absolute; top: 100%; left: 0; width: 100%; margin-top: 20px; }
          .fc-header-toolbar { display: none; }
          @page { size: landscape; margin: 10mm; }
        }
      `}</style>
    </Box>
  );
};

export default ScheduleCalendar;
