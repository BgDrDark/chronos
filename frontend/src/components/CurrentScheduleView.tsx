import React, { useState } from 'react';
import { useQuery, gql } from '@apollo/client';
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, IconButton, CircularProgress, Tooltip, Button, Stack
} from '@mui/material';
import { 
  ArrowBack, 
  ArrowForward, 
  Print as PrintIcon, 
  Share as ShareIcon 
} from '@mui/icons-material';
import { 
  getDaysInMonth, 
  format, 
  addMonths, 
  subMonths, 
  startOfMonth, 
  endOfMonth, 
  isWeekend
} from 'date-fns';
import { bg } from 'date-fns/locale';
import { ShiftTypeColors } from '../utils/shiftUtils';

// --- QUERIES ---
const GET_SCHEDULES_QUERY = gql`
  query GetSchedulesForView($startDate: Date!, $endDate: Date!) {
    workSchedules(startDate: $startDate, endDate: $endDate) {
      id
      date
      user {
        id
      }
      shift {
        id
        name
        shiftType
        startTime
        endTime
      }
    }
  }
`;

const GET_USERS_QUERY = gql`
  query GetUsersForView($limit: Int) {
    users(limit: $limit) {
      users {
        id
        email
        firstName
        lastName
        position {
          title
        }
      }
    }
  }
`;

const GET_PUBLIC_HOLIDAYS_QUERY = gql`
  query GetPublicHolidaysForView($year: Int) {
    publicHolidays(year: $year) {
      id
      date
      name
      localName
    }
  }
`;

const GET_ORTHODOX_HOLIDAYS_QUERY = gql`
  query GetOrthodoxHolidaysForView($year: Int) {
    orthodoxHolidays(year: $year) {
      id
      date
      name
      localName
    }
  }
`;

const CurrentScheduleView: React.FC = () => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const startDate = startOfMonth(currentDate);
  const endDate = endOfMonth(currentDate);
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Queries
  const { data: usersData, loading: usersLoading } = useQuery(GET_USERS_QUERY, {
    variables: { limit: 1000 }
  });

  const { data: schedData, loading: schedLoading } = useQuery(GET_SCHEDULES_QUERY, {
    variables: {
      startDate: format(startDate, 'yyyy-MM-dd'),
      endDate: format(endDate, 'yyyy-MM-dd')
    },
    fetchPolicy: 'network-only'
  });

  const { data: holidaysData } = useQuery(GET_PUBLIC_HOLIDAYS_QUERY, {
    variables: { year: year }
  });

  const includeOrthodox = localStorage.getItem('include_orthodox_holidays') === 'true';
  const { data: orthodoxHolidaysData } = useQuery(GET_ORTHODOX_HOLIDAYS_QUERY, {
    variables: { year: year },
    skip: !includeOrthodox
  });

  // Processing
  const daysInMonth = getDaysInMonth(currentDate);
  const daysArray = Array.from({ length: daysInMonth }, (_, i) => {
    const d = new Date(year, month, i + 1);
    return {
      date: d,
      dayNum: i + 1,
      isWeekend: isWeekend(d),
      dayName: format(d, 'EEEEEE', { locale: bg }), // short day name (e.g. 'П')
    };
  });

  const schedulesMap = new Map<string, any>();
  if (schedData?.workSchedules) {
    schedData.workSchedules.forEach((s: any) => {
      const key = `${s.user.id}-${s.date}`;
      schedulesMap.set(key, s.shift);
    });
  }

  const holidaysMap = new Map<string, any>();
  if (holidaysData?.publicHolidays) {
    holidaysData.publicHolidays.forEach((h: any) => {
        holidaysMap.set(h.date, h);
    });
  }

  if (includeOrthodox && orthodoxHolidaysData?.orthodoxHolidays) {
    orthodoxHolidaysData.orthodoxHolidays.forEach((h: any) => {
        holidaysMap.set(h.date, { ...h, isOrthodox: true });
    });
  }

  // Derived Legend Data
  const uniqueShifts = new Map<number, any>();
  if (schedData?.workSchedules) {
    schedData.workSchedules.forEach((s: any) => {
      if (s.shift && !uniqueShifts.has(s.shift.id)) {
        uniqueShifts.set(s.shift.id, s.shift);
      }
    });
  }

  // Handlers
  const handlePrevMonth = () => setCurrentDate(subMonths(currentDate, 1));
  const handleNextMonth = () => setCurrentDate(addMonths(currentDate, 1));
  
  const handlePrint = () => {
    window.print();
  };

  const handleShare = async () => {
    const url = window.location.href;
    const title = `График за ${format(currentDate, 'MMMM yyyy', { locale: bg })}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: `Разгледайте работния график за ${format(currentDate, 'MMMM yyyy', { locale: bg })}`,
          url: url
        });
      } catch (error) {
        console.log('Error sharing', error);
      }
    } else {
      try {
        await navigator.clipboard.writeText(url);
        alert('Линкът е копиран в клипборда!');
      } catch {
        alert('Неуспешно копиране на линка.');
      }
    }
  };

  if (usersLoading || schedLoading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* Toolbar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }} className="no-print">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={handlePrevMonth}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h5" sx={{ textTransform: 'capitalize', fontWeight: 'bold' }}>
            {format(currentDate, 'MMMM yyyy', { locale: bg })}
          </Typography>
          <IconButton onClick={handleNextMonth}>
            <ArrowForward />
          </IconButton>
        </Box>
        
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<ShareIcon />} onClick={handleShare}>
            Сподели
          </Button>
          <Button variant="contained" startIcon={<PrintIcon />} onClick={handlePrint}>
            Принтирай
          </Button>
        </Stack>
      </Box>

      {/* Table */}
      <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: '75vh', overflow: 'auto' }}>
        <Table stickyHeader size="small" sx={{ borderCollapse: 'separate' }}>
          <TableHead>
            <TableRow>
              <TableCell 
                sx={{ 
                  fontWeight: 'bold', 
                  backgroundColor: 'background.paper', 
                  position: 'sticky', 
                  left: 0, 
                  zIndex: 3,
                  borderRight: '1px solid #e0e0e0',
                  minWidth: 200
                }}
              >
                Служител
              </TableCell>
              {daysArray.map((day) => {
                  const dateStr = format(day.date, 'yyyy-MM-dd');
                  const isHoliday = holidaysMap.has(dateStr);
                  return (
                    <TableCell 
                        key={day.dayNum} 
                        align="center"
                        sx={{ 
                        fontWeight: 'bold',
                        minWidth: 35,
                        px: 0.5,
                        backgroundColor: isHoliday ? '#fff3e0' : (day.isWeekend ? '#f5f5f5' : 'background.paper'),
                        color: day.isWeekend ? 'text.secondary' : 'text.primary',
                        borderLeft: day.dayNum === 1 ? '1px solid #e0e0e0' : 'none'
                        }}
                    >
                        <Box sx={{ fontSize: '0.75rem', lineHeight: 1 }}>{day.dayName}</Box>
                        <Box sx={{ fontSize: '0.9rem' }}>{day.dayNum}</Box>
                    </TableCell>
                  );
              })}
            </TableRow>
          </TableHead>
          <TableBody>
            {usersData?.users?.users.map((user: any) => (
              <TableRow key={user.id} hover>
                <TableCell 
                  component="th" 
                  scope="row"
                  sx={{ 
                    position: 'sticky', 
                    left: 0, 
                    backgroundColor: 'background.paper',
                    zIndex: 2,
                    borderRight: '1px solid #e0e0e0',
                    py: 1
                  }}
                >
                  <Typography variant="body2" fontWeight="medium">
                    {user.firstName} {user.lastName}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" noWrap display="block">
                    {user.position?.title || user.email}
                  </Typography>
                </TableCell>
                {daysArray.map((day) => {
                  const dateStr = format(day.date, 'yyyy-MM-dd');
                  const shift = schedulesMap.get(`${user.id}-${dateStr}`);
                  const isHoliday = holidaysMap.has(dateStr);
                  
                  let cellContent = '';
                  let cellColor = 'transparent';
                  let tooltip = '';
                  let textColor = 'text.primary';

                  if (shift) {
                    cellContent = shift.name.charAt(0).toUpperCase();
                    cellColor = ShiftTypeColors[shift.shiftType] || '#eee';
                    tooltip = `${shift.name} (${shift.startTime.substring(0,5)} - ${shift.endTime.substring(0,5)})`;
                    textColor = '#fff'; // Assuming dark background for shifts
                    
                    // Special handling for 'Day Off' or 'Unpaid' if we want lighter text? 
                    // Usually ShiftTypeColors are dark enough for white text, except maybe yellow.
                    if (shift.shiftType === 'public_holiday' || shift.shiftType === 'paid_leave' && cellColor === '#ffc107') {
                        textColor = 'black';
                    }
                  } else if (isHoliday) {
                      // Optional: Show holiday icon or color if no shift assigned?
                      // The prompt says "only show ... shift name". If no shift, empty.
                      // But the background is already styled in header.
                  }

                  return (
                    <Tooltip key={day.dayNum} title={tooltip} arrow enterDelay={100}>
                      <TableCell 
                        align="center" 
                        sx={{ 
                          p: 0, 
                          borderLeft: '1px solid #f0f0f0',
                          backgroundColor: isHoliday ? '#fff8e1' : (day.isWeekend ? '#fafafa' : 'inherit')
                        }}
                      >
                        {shift && (
                          <Box
                            sx={{
                              width: '28px',
                              height: '28px',
                              borderRadius: '50%',
                              backgroundColor: cellColor,
                              color: textColor,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              margin: '0 auto',
                              fontSize: '0.85rem',
                              fontWeight: 'bold',
                              cursor: 'default'
                            }}
                          >
                            {cellContent}
                          </Box>
                        )}
                      </TableCell>
                    </Tooltip>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Legend */}
      <Box sx={{ mt: 3, p: 2, borderTop: '1px solid #eee' }} className="print-legend">
        <Typography variant="subtitle2" gutterBottom>Легенда на смените:</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          {Array.from(uniqueShifts.values()).map((shift: any) => (
            <Box key={shift.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 24,
                  height: 24,
                  borderRadius: '50%',
                  backgroundColor: ShiftTypeColors[shift.shiftType] || '#999',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 'bold'
                }}
              >
                {shift.name.charAt(0).toUpperCase()}
              </Box>
              <Typography variant="body2">
                {shift.name} ({shift.startTime.substring(0, 5)} - {shift.endTime.substring(0, 5)})
              </Typography>
            </Box>
          ))}
          {uniqueShifts.size === 0 && (
            <Typography variant="caption" color="text.secondary">Няма назначени смени за този месец.</Typography>
          )}
        </Box>
      </Box>

      {/* Print Styles */}
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body, html { visibility: hidden; height: auto; }
          .MuiDrawer-root { display: none; }
          header { display: none; }
          /* Reset visibility for the component */
          #root { visibility: hidden; }
          
          /* Specifically target the table container to be visible */
          .MuiTableContainer-root, .print-legend {
             visibility: visible;
             position: absolute;
             left: 0;
             top: 0;
             width: 100%;
          }
          
          .MuiTableContainer-root {
             overflow: visible !important;
             max-height: none !important;
          }

          /* Ensure table fits */
          table { width: 100% !important; border-collapse: collapse; }
          th, td { border: 1px solid #ccc !important; font-size: 10px !important; padding: 2px !important; }
          
          /* Force landscape hint (browser dependent) */
          @page { size: landscape; margin: 10mm; }
        }
      `}</style>
    </Box>
  );
};

export default CurrentScheduleView;
