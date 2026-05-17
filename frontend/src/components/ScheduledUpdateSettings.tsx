import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import {
  Card, CardContent, Typography, TextField, Button, Box,
  Alert, AlertTitle, CircularProgress, Chip, Switch,
  FormControlLabel, InputAdornment, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import UpdateIcon from '@mui/icons-material/Update';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { InfoIcon } from '../components/ui/InfoIcon';
import { getErrorMessage } from '../types';
import {
  UPDATE_SCHEDULE_QUERY,
  SET_UPDATE_SCHEDULE_MUTATION,
  RUN_UPDATE_NOW_MUTATION,
} from '../graphql/queries';

const DAYS_OF_WEEK = [
  { value: 0, label: 'Понеделник' },
  { value: 1, label: 'Вторник' },
  { value: 2, label: 'Сряда' },
  { value: 3, label: 'Четвъртък' },
  { value: 4, label: 'Петък' },
  { value: 5, label: 'Събота' },
  { value: 6, label: 'Неделя' },
];

const ScheduledUpdateSettings: React.FC = () => {
  const { data, loading, refetch } = useQuery(UPDATE_SCHEDULE_QUERY, {
    pollInterval: 30000,
    fetchPolicy: 'network-only',
  });

  const [setUpdateSchedule, { loading: saving }] = useMutation(SET_UPDATE_SCHEDULE_MUTATION);
  const [runUpdateNow, { loading: running }] = useMutation(RUN_UPDATE_NOW_MUTATION);

  const [enabled, setEnabled] = useState(false);
  const [scheduleType, setScheduleType] = useState<'once' | 'weekly'>('once');
  const [scheduledAt, setScheduledAt] = useState<string>('');
  const [dayOfWeek, setDayOfWeek] = useState<number>(0);
  const [hour, setHour] = useState<number>(3);
  const [minute, setMinute] = useState<number>(0);
  const [notifyEmail, setNotifyEmail] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const schedule = data?.updateSchedule;
  const lastRunStatus = schedule?.lastRunStatus;
  const lastRunAt = schedule?.lastRunAt;

  useEffect(() => {
    if (schedule) {
      setEnabled(schedule.enabled);
      setScheduleType(schedule.scheduleType);
      if (schedule.scheduledAt) {
        setScheduledAt(new Date(schedule.scheduledAt).toISOString().slice(0, 16));
      }
      if (schedule.dayOfWeek !== null && schedule.dayOfWeek !== undefined) {
        setDayOfWeek(schedule.dayOfWeek);
      }
      setHour(schedule.hour);
      setMinute(schedule.minute);
      setNotifyEmail(schedule.notifyEmail || '');
    }
  }, [schedule]);

  const handleSave = async () => {
    setError(null);
    setSuccessMsg(null);
    try {
      const input: any = {
        enabled,
        scheduleType,
        hour,
        minute,
        notifyEmail,
      };

      if (scheduleType === 'once') {
        if (!scheduledAt) {
          setError('Моля, изберете дата и час');
          return;
        }
        input.scheduledAt = new Date(scheduledAt).toISOString();
      } else {
        input.dayOfWeek = dayOfWeek;
      }

      await setUpdateSchedule({ variables: { input } });
      setSuccessMsg('Настройките са запазени');
      refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleRunNow = async () => {
    setError(null);
    setSuccessMsg(null);
    try {
      const result = await runUpdateNow();
      setSuccessMsg(result.data?.runUpdateNow || 'Update завършен');
      refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const statusColor = lastRunStatus === 'success' ? 'success' : lastRunStatus === 'failed' ? 'error' : lastRunStatus === 'skipped' ? 'warning' : 'default';

  return (
    <Card sx={{ mb: 4, border: enabled ? '2px solid #2196f3' : '1px solid rgba(0,0,0,0.12)' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <UpdateIcon color={enabled ? 'primary' : 'action'} />
          <Typography variant="h6" fontWeight="bold">Автоматични актуализации</Typography>
          {enabled && <Chip label="АКТИВИРАНО" color="primary" size="small" />}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {successMsg && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMsg(null)}>
            {successMsg}
          </Alert>
        )}

        {lastRunStatus && (
          <Box sx={{ mb: 2 }}>
            <Chip
              label={`Последен статус: ${lastRunStatus}${lastRunAt ? ` (${new Date(lastRunAt).toLocaleString('bg-BG')})` : ''}`}
              color={statusColor}
              size="small"
            />
          </Box>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                color="primary"
              />
            }
            label="Активирано"
          />

          <FormControl fullWidth>
            <InputLabel>Тип разписание</InputLabel>
            <Select
              value={scheduleType}
              label="Тип разписание"
              onChange={(e) => setScheduleType(e.target.value as 'once' | 'weekly')}
            >
              <MenuItem value="once">Еднократно</MenuItem>
              <MenuItem value="weekly">Седмично</MenuItem>
            </Select>
          </FormControl>

          {scheduleType === 'once' && (
            <TextField
              fullWidth
              label="Дата и час"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              InputLabelProps={{ shrink: true }}
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoIcon helpText="Кога да се провери и изпълни актуализацията" />
                    </InputAdornment>
                  ),
                },
              }}
            />
          )}

          {scheduleType === 'weekly' && (
            <>
              <FormControl fullWidth>
                <InputLabel>Ден от седмицата</InputLabel>
                <Select
                  value={dayOfWeek}
                  label="Ден от седмицата"
                  onChange={(e) => setDayOfWeek(e.target.value as number)}
                >
                  {DAYS_OF_WEEK.map((day) => (
                    <MenuItem key={day.value} value={day.value}>{day.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  fullWidth
                  label="Час"
                  type="number"
                  value={hour}
                  onChange={(e) => setHour(parseInt(e.target.value) || 0)}
                  inputProps={{ min: 0, max: 23 }}
                />
                <TextField
                  fullWidth
                  label="Минути"
                  type="number"
                  value={minute}
                  onChange={(e) => setMinute(parseInt(e.target.value) || 0)}
                  inputProps={{ min: 0, max: 59 }}
                />
              </Box>
            </>
          )}

          <TextField
            fullWidth
            label="Email за уведомление"
            type="email"
            value={notifyEmail}
            onChange={(e) => setNotifyEmail(e.target.value)}
            placeholder="admin@example.com"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Email, на който ще се изпраща статус след update" />
                  </InputAdornment>
                ),
              },
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSave}
            disabled={saving || !enabled}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            {saving ? 'Запазване...' : 'Запази'}
          </Button>

          <Button
            variant="outlined"
            color="success"
            onClick={handleRunNow}
            disabled={running}
            startIcon={running ? <CircularProgress size={20} /> : <PlayArrowIcon />}
          >
            {running ? 'Изпълнява се...' : 'Изпълни сега'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ScheduledUpdateSettings;
