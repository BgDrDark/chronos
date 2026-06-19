import React, { useState, useMemo } from 'react';
import dayjs from 'dayjs';
import { useQuery, useMutation } from '@apollo/client';
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, IconButton, CircularProgress, Tooltip, Button, Stack,
  MenuItem, Select, InputLabel, FormControl, Chip, Avatar
} from '@mui/material';
import {
  ArrowBack, ArrowForward, Print as PrintIcon, Share as ShareIcon,
  ContentCopy, CheckCircle, Warning
} from '@mui/icons-material';
import { useError, extractErrorMessage } from '../context/ErrorContext';
import { ShiftTypeColors } from '../utils/shiftUtils';
import {
  GET_SHIFTS_FOR_GRID,
  GET_SCHEDULES_FOR_GRID,
  GET_SCHEDULE_STATS,
  SET_WORK_SCHEDULE,
  COPY_SCHEDULES_FROM_MONTH,
  GET_USERS_QUERY,
  GET_PUBLIC_HOLIDAYS_QUERY,
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
  annual_paid: 'Пл',
  paid_leave: 'Пл',
  sick: 'Б',
  sick_leave: 'Б',
  unpaid: 'Н',
  unpaid_leave: 'Н',
  maternity: 'М',
  paternity: 'Бщ',
  parental: 'Р',
  child_care: 'Гр',
  study: 'Уч',
};

interface ScheduleGridProps {
  onOpenTemplatePreview: () => void;
}

const ScheduleGrid: React.FC<ScheduleGridProps> = ({ onOpenTemplatePreview }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [editingCell, setEditingCell] = useState<{ userId: number; date: string } | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);

  const { showError, showSuccess } = useError();
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1;

  const startDate = dayjs(currentDate).startOf('month').format('YYYY-MM-DD');
  const endDate = dayjs(currentDate).endOf('month').format('YYYY-MM-DD');

  const { data: usersData, loading: usersLoading } = useQuery(GET_USERS_QUERY, { variables: { limit: 1000 } });
  const { data: shiftsData, loading: shiftsLoading } = useQuery(GET_SHIFTS_FOR_GRID);
  const { data: schedData, loading: schedLoading, refetch: refetchSched } = useQuery(GET_SCHEDULES_FOR_GRID, {
    variables: { startDate, endDate }, fetchPolicy: 'network-only'
  });
  const { data: holidaysData } = useQuery(GET_PUBLIC_HOLIDAYS_QUERY, { variables: { year } });
  const { data: leavesData } = useQuery(GET_APPROVED_LEAVES_IN_RANGE, { variables: { startDate, endDate } });
  const { data: statsData } = useQuery(GET_SCHEDULE_STATS, { variables: { month, year } });

  const [setSchedule] = useMutation(SET_WORK_SCHEDULE);
  const [copySchedules] = useMutation(COPY_SCHEDULES_FROM_MONTH);

  const daysArray = useMemo(() => {
    const daysInMonth = dayjs(currentDate).daysInMonth();
    return Array.from({ length: daysInMonth }, (_, i) => {
      const d = dayjs(currentDate).date(i + 1);
      return {
        dateStr: d.format('YYYY-MM-DD'),
        dayNum: i + 1,
        isWeekend: d.day() === 0 || d.day() === 6,
        dayName: d.format('dd'),
      };
    });
  }, [currentDate]);

  const schedulesMap = useMemo(() => {
    const map = new Map<string, { id: number; shift: { id: number; name: string; shiftType: string; startTime: string; endTime: string } }>();
    schedData?.workSchedules?.forEach((s: any) => {
      if (s.shift) map.set(`${s.user.id}-${s.date}`, { id: s.id, shift: s.shift });
    });
    return map;
  }, [schedData]);

  const holidaysMap = useMemo(() => {
    const map = new Map<string, string>();
    holidaysData?.publicHolidays?.forEach((h: any) => map.set(h.date, h.localName || h.name));
    return map;
  }, [holidaysData]);

  const leavesMap = useMemo(() => {
    const map = new Map<string, { leaveType: string; label: string; color: string }>();
    leavesData?.approvedLeaveRequestsInRange?.forEach((l: any) => {
      const start = new Date(l.startDate);
      const end = new Date(l.endDate);
      const color = LeaveTypeColors[l.leaveType] || '#757575';
      const label = LeaveTypeLabels[l.leaveType] || l.leaveType.charAt(0).toUpperCase();
      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        map.set(`${l.user.id}-${dateStr}`, { leaveType: l.leaveType, label, color });
      }
    });
    return map;
  }, [leavesData]);

  const filteredUsers = useMemo(() => {
    const users = usersData?.users?.users || [];
    return selectedUsers.length === 0 ? users : users.filter((u: any) => selectedUsers.includes(u.id));
  }, [usersData, selectedUsers]);

  const handleShiftSelect = async (userId: number, dateStr: string, shiftId: number) => {
    try {
      await setSchedule({ variables: { userId, shiftId, date: dateStr } });
      refetchSched();
    } catch (err) {
      showError(extractErrorMessage(err));
    }
    setEditingCell(null);
  };

  const handleCopyFromPrevMonth = async () => {
    const prevMonth = month === 1 ? 12 : month - 1;
    const prevYear = month === 1 ? year - 1 : year;
    let totalCopied = 0;

    for (const user of usersData?.users?.users || []) {
      try {
        const result = await copySchedules({
          variables: { userId: user.id, sourceMonth: prevMonth, sourceYear: prevYear, targetMonth: month, targetYear: year }
        });
        totalCopied += result.data?.copySchedulesFromMonth || 0;
      } catch (err) {
        showError(extractErrorMessage(err));
      }
    }

    if (totalCopied > 0) {
      showSuccess(`Копирани ${totalCopied} графика от ${dayjs(prevYear).month(prevMonth - 1).format('MMMM YYYY')}`);
      refetchSched();
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

  if (usersLoading || schedLoading || shiftsLoading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
  }

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }} className="no-print">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton onClick={() => setCurrentDate(dayjs(currentDate).subtract(1, 'month').toDate())}><ArrowBack /></IconButton>
          <Typography variant="h5" sx={{ textTransform: 'capitalize', fontWeight: 'bold', minWidth: 180, textAlign: 'center' }}>
            {dayjs(currentDate).format('MMMM YYYY')}
          </Typography>
          <IconButton onClick={() => setCurrentDate(dayjs(currentDate).add(1, 'month').toDate())}><ArrowForward /></IconButton>
        </Box>

        <Stack direction="row" spacing={1} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Филтър</InputLabel>
            <Select
              multiple
              value={selectedUsers}
              label="Филтър"
              renderValue={(selected) => (selected as number[]).length === 0 ? 'Всички' : `${(selected as number[]).length} избрани`}
            >
              {usersData?.users?.users.map((u: any) => (
                <MenuItem key={u.id} value={u.id}>
                  <Chip label={u.firstName ? `${u.firstName} ${u.lastName}` : u.email} variant={selectedUsers.includes(u.id) ? 'filled' : 'outlined'} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Tooltip title="Копирай от миналия месец" arrow>
            <IconButton onClick={handleCopyFromPrevMonth} color="primary"><ContentCopy /></IconButton>
          </Tooltip>
          <Tooltip title="Приложи шаблон" arrow>
            <Button variant="outlined" size="small" onClick={onOpenTemplatePreview}>Шаблон</Button>
          </Tooltip>
          <Tooltip title="Принтирай" arrow>
            <IconButton onClick={handlePrint} color="primary"><PrintIcon /></IconButton>
          </Tooltip>
          <Tooltip title="Сподели" arrow>
            <IconButton onClick={handleShare} color="primary"><ShareIcon /></IconButton>
          </Tooltip>
        </Stack>
      </Box>

      <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: '60vh', overflow: 'auto' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', position: 'sticky', left: 0, zIndex: 3, backgroundColor: 'background.paper', minWidth: 180 }}>Служител</TableCell>
              {daysArray.map((day) => {
                const holiday = holidaysMap.get(day.dateStr);
                return (
                  <TableCell key={day.dateStr} align="center" sx={{
                    fontWeight: 'bold', minWidth: 32, px: 0.5,
                    backgroundColor: holiday ? '#fff3e0' : (day.isWeekend ? '#f5f5f5' : 'background.paper'),
                    color: day.isWeekend ? 'text.secondary' : 'text.primary',
                  }}>
                    <Box sx={{ fontSize: '0.7rem', lineHeight: 1 }}>{day.dayName}</Box>
                    <Box sx={{ fontSize: '0.85rem', fontWeight: holiday ? 'bold' : 'normal' }}>{day.dayNum}</Box>
                  </TableCell>
                );
              })}
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers.map((user: any) => (
              <TableRow key={user.id} hover>
                <TableCell sx={{ position: 'sticky', left: 0, backgroundColor: 'background.paper', zIndex: 2, py: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 28, height: 28, fontSize: '0.75rem' }}>{(user.firstName?.[0] || user.email[0]).toUpperCase()}</Avatar>
                    <Box>
                      <Typography variant="body2" fontWeight="medium" noWrap>{user.firstName ? `${user.firstName} ${user.lastName}` : user.email}</Typography>
                      <Typography variant="caption" color="text.secondary" noWrap>{user.position?.title || ''}</Typography>
                    </Box>
                  </Box>
                </TableCell>
                {daysArray.map((day) => {
                  const entry = schedulesMap.get(`${user.id}-${day.dateStr}`);
                  const leave = leavesMap.get(`${user.id}-${day.dateStr}`);
                  const isEditing = editingCell?.userId === user.id && editingCell?.date === day.dateStr;

                  return (
                    <TableCell key={day.dateStr} align="center" sx={{ p: 0, cursor: 'pointer', '&:hover': { backgroundColor: '#e3f2fd' } }} onClick={() => setEditingCell({ userId: user.id, date: day.dateStr })}>
                      {isEditing ? (
                        <Box sx={{ p: 0.5 }} onClick={(e) => e.stopPropagation()}>
                          <Select size="small" value={entry?.shift.id || ''} onChange={(e) => handleShiftSelect(user.id, day.dateStr, e.target.value as number)} onClose={() => setEditingCell(null)} autoFocus fullWidth sx={{ fontSize: '0.7rem', minHeight: 24 }}>
                            <MenuItem value={0} sx={{ fontSize: '0.7rem' }}>Почивен</MenuItem>
                            {shiftsData?.shifts.map((s: any) => (
                              <MenuItem key={s.id} value={s.id} sx={{ fontSize: '0.7rem' }}>{s.name} ({s.startTime.substring(0, 5)})</MenuItem>
                            ))}
                          </Select>
                        </Box>
                      ) : entry ? (
                        <Tooltip title={`${entry.shift.name} (${entry.shift.startTime.substring(0, 5)} - ${entry.shift.endTime.substring(0, 5)})`} arrow>
                          <Box sx={{ width: 26, height: 26, borderRadius: '50%', margin: '0 auto', backgroundColor: ShiftTypeColors[entry.shift.shiftType] || '#999', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 'bold' }}>{entry.shift.name.charAt(0).toUpperCase()}</Box>
                        </Tooltip>
                      ) : leave ? (
                        <Tooltip title={LeaveTypeLabels[leave.leaveType] || leave.leaveType} arrow>
                          <Box sx={{ width: 26, height: 26, borderRadius: '4px', margin: '0 auto', backgroundColor: leave.color, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>{leave.label}</Box>
                        </Tooltip>
                      ) : (
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#ccc', margin: '0 auto' }} />
                      )}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {statsData?.scheduleStats && (
        <Box sx={{ mt: 2, p: 2, borderTop: '1px solid #eee', display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="subtitle2" sx={{ width: '100%' }}>Статистика за месеца:</Typography>
          {statsData.scheduleStats.map((stat: any) => {
            const user = usersData?.users?.users?.find((u: any) => u.id === stat.userId);
            if (selectedUsers.length > 0 && !selectedUsers.includes(stat.userId)) return null;
            return (
              <Box key={stat.userId} sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200 }}>
                {stat.isComplete ? <CheckCircle sx={{ color: 'success.main', fontSize: 18 }} /> : <Warning sx={{ color: 'warning.main', fontSize: 18 }} />}
                <Typography variant="body2" fontWeight="medium">{user?.firstName ? `${user.firstName} ${user.lastName}` : user?.email}:</Typography>
                <Typography variant="body2" color={stat.isComplete ? 'success.main' : 'warning.main'}>{stat.assignedDays}/{stat.workDaysNorm} дни</Typography>
              </Box>
            );
          })}
        </Box>
      )}

      <style>{`@media print { .no-print { display: none !important; } body, html { visibility: hidden; } .MuiTableContainer-root { visibility: visible; position: absolute; left: 0; top: 0; width: 100%; } @page { size: landscape; margin: 5mm; } }`}</style>
    </Box>
  );
};

export default ScheduleGrid;
