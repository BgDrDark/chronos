import React, { useState } from 'react';
import { 
  Container, Typography, Box, CircularProgress, Alert, Paper, Dialog, 
  DialogTitle, DialogContent, Button, DialogActions, Stack,
  useTheme, useMediaQuery 
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import MedicalServicesIcon from '@mui/icons-material/MedicalServices';
import BeachAccessIcon from '@mui/icons-material/BeachAccess';
import WeekendIcon from '@mui/icons-material/Weekend';
import { formatDate } from '../utils/dateUtils';
import { TextField } from '@mui/material';
import { ShiftTypeColors } from '../utils/shiftUtils';
import ShiftLegend from '../components/ShiftLegend';
import ShiftEventContent from '../components/ShiftEventContent';

const GET_MY_SCHEDULES_QUERY = gql`
  query GetMySchedules($startDate: Date!, $endDate: Date!) {
    mySchedules(startDate: $startDate, endDate: $endDate) {
      id
      date
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

const REQUEST_LEAVE_MUTATION = gql`
  mutation RequestLeave($startDate: Date!, $endDate: Date!, $leaveType: String!, $reason: String) {
    requestLeave(leaveInput: {startDate: $startDate, endDate: $endDate, leaveType: $leaveType, reason: $reason}) {
      id
      status
    }
  }
`;

const MySchedulePage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [open, setOpen] = useState(false);
  const [requestOpen, setRequestOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [currentEvent, setCurrentEvent] = useState<any | null>(null);
  
  // Request State
  const [leaveType, setLeaveType] = useState('paid_leave');
  const [reason, setReason] = useState('');

  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
  const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];

  const { data, loading, error } = useQuery(GET_MY_SCHEDULES_QUERY, {
    variables: {
      startDate: startOfMonth,
      endDate: endOfMonth
    }
  });

  const { data: holidaysData } = useQuery(GET_PUBLIC_HOLIDAYS_QUERY, {
    variables: { year: today.getFullYear() }
  });

  const includeOrthodox = localStorage.getItem('include_orthodox_holidays') === 'true';
  const { data: orthodoxHolidaysData } = useQuery(GET_ORTHODOX_HOLIDAYS_QUERY, {
    variables: { year: today.getFullYear() },
    skip: !includeOrthodox
  });

  const [requestLeave, { loading: saving }] = useMutation(REQUEST_LEAVE_MUTATION);

  const scheduleEvents = data?.mySchedules.map((s: any) => {
    // Use shared color logic
    const shiftType = s.shift?.shiftType || 'regular';
    const bgColor = ShiftTypeColors[shiftType] || ShiftTypeColors.regular;

    return {
      title: s.shift?.name || 'Смяна',
      date: s.date,
      backgroundColor: bgColor,
      borderColor: bgColor,
      extendedProps: {
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
    // Remove display: 'background' to allow custom content rendering (icon)
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

  const events = [...scheduleEvents, ...holidayEvents, ...orthodoxHolidayEvents];

  // Filter holidays for current month (based on displayed range? Or just simple current month)
  // The user sees a calendar. Ideally we pass holidays that match the calendar view.
  // But for simplicity, let's pass holidays for the queried period (this month)
  // Holidays data is for whole year.
  const currentMonthHolidays = [...(holidaysData?.publicHolidays || []), ...(includeOrthodox ? (orthodoxHolidaysData?.orthodoxHolidays || []) : [])].filter((h: any) => {
      const d = new Date(h.date);
      // We are showing startOfMonth to endOfMonth.
      const start = new Date(startOfMonth);
      const end = new Date(endOfMonth);
      return d >= start && d <= end;
  });

  const handleDateClick = (arg: any) => {
    setSelectedDate(arg.dateStr);
    // Find non-background events first
    const event = events.find((e: any) => e.date === arg.dateStr && !e.extendedProps?.isHoliday);
    setCurrentEvent(event);
    setOpen(true);
  };

  const handleEventClick = (arg: any) => {
    if (arg.event.extendedProps.isHoliday) return; // Ignore clicks on holidays for now
    setSelectedDate(arg.event.startStr);
    setCurrentEvent({
        title: arg.event.title,
        extendedProps: arg.event.extendedProps
    });
    setOpen(true);
  };

  const initRequest = (type: string) => {
      setLeaveType(type);
      setReason('');
      setOpen(false);
      setRequestOpen(true);
  };

  const handleRequestSubmit = async () => {
    if (!selectedDate) return;
    try {
      await requestLeave({
        variables: {
          startDate: selectedDate,
          endDate: selectedDate, // Single day request for now
          leaveType: leaveType,
          reason: reason
        }
      });
      setRequestOpen(false);
      alert('Заявката е изпратена успешно!');
    } catch (e: any) { alert(e.message); }
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

      {/* Details Dialog */}
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

          <Typography variant="subtitle2" gutterBottom>Заяви отсъствие:</Typography>
          <Stack spacing={1}>
            <Button 
                variant="outlined" 
                color="warning" 
                startIcon={<BeachAccessIcon />} 
                onClick={() => initRequest('paid_leave')}
            >
                Заяви Платен отпуск
            </Button>
            <Button 
                variant="outlined" 
                color="error" 
                startIcon={<MedicalServicesIcon />} 
                onClick={() => initRequest('sick_leave')}
            >
                Заяви Болничен
            </Button>
            <Button 
                variant="outlined" 
                color="info" 
                startIcon={<WeekendIcon />} 
                onClick={() => initRequest('unpaid_leave')}
            >
                Заяви Неплатен отпуск
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Затвори</Button>
        </DialogActions>
      </Dialog>

      {/* Request Dialog */}
      <Dialog open={requestOpen} onClose={() => setRequestOpen(false)} fullWidth maxWidth="xs">
          <DialogTitle>Заявка за {leaveType === 'paid_leave' ? 'платен отпуск' : leaveType === 'sick_leave' ? 'болничен' : 'неплатен отпуск'}</DialogTitle>
          <DialogContent>
              <Typography variant="body2" gutterBottom>Дата: {formatDate(selectedDate)}</Typography>
              <TextField 
                  label="Причина (по избор)" 
                  multiline 
                  rows={3} 
                  fullWidth 
                  value={reason} 
                  onChange={(e) => setReason(e.target.value)} 
                  margin="normal"
              />
          </DialogContent>
          <DialogActions>
              <Button onClick={() => setRequestOpen(false)}>Отказ</Button>
              <Button variant="contained" onClick={handleRequestSubmit} disabled={saving}>Изпрати</Button>
          </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MySchedulePage;
