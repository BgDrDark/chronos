import React, { useState } from 'react';
import {
  Box, Button, Card, CardContent, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem, Select, FormControl,
  InputLabel,
} from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { ACCESS_ZONES_QUERY } from '../../graphql/queries/accessControl';
import { EMERGENCY_EVENTS_QUERY } from '../../graphql/queries/security';
import { TRIGGER_EMERGENCY, RESOLVE_EMERGENCY } from '../../graphql/mutations/security';
import { BULK_EMERGENCY_ACTION } from '../../graphql/mutations/kioskAdmin';
import { getErrorMessage } from '../../types';

const EmergencyPage: React.FC = () => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [eventType, setEventType] = useState('lockdown');
  const [scope, setScope] = useState('all');
  const [zoneId, setZoneId] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const { data: eventsData, refetch: refetchEvents } = useQuery(EMERGENCY_EVENTS_QUERY, {
    variables: { isActive: undefined },
  });
  const { data: zonesData } = useQuery(ACCESS_ZONES_QUERY);
  const [triggerEmergency, { loading: triggerLoading }] = useMutation(TRIGGER_EMERGENCY);
  const [resolveEmergency] = useMutation(RESOLVE_EMERGENCY);
  const [bulkAction] = useMutation(BULK_EMERGENCY_ACTION);

  const events = eventsData?.emergencyEvents || [];
  const activeEvents = events.filter((e: any) => e.isActive);
  const zones = zonesData?.accessZones || [];

  const getStatusColor = () => {
    if (activeEvents.some((e: any) => e.eventType === 'lockdown')) return '#212121';
    if (activeEvents.some((e: any) => e.eventType === 'emergency_unlock')) return '#d32f2f';
    if (activeEvents.length > 0) return '#e65100';
    return '#1976d2';
  };

  const getStatusText = () => {
    if (activeEvents.some((e: any) => e.eventType === 'lockdown')) return 'ПЪЛНА БЛОКАДА';
    if (activeEvents.some((e: any) => e.eventType === 'emergency_unlock')) return 'АВАРИЙНО ОТКЛЮЧЕНО';
    if (activeEvents.length > 0) return 'АКТИВНИ СЪБИТИЯ';
    return 'НОРМАЛЕН РЕЖИМ';
  };

  const handleBulkAction = async (action: string) => {
    const confirmMessages: Record<string, string> = {
      lockdown: 'Сигурни ли сте, че искате да блокирате всички врати?',
      emergency_unlock: 'Сигурни ли сте, че искате аварийно да отключите всички врати?',
      normal: 'Сигурни ли сте, че искате да възстановите нормалния режим?',
    };
    if (!window.confirm(confirmMessages[action] || 'Сигурни ли сте?')) return;
    setActionLoading(true);
    try {
      await bulkAction({ variables: { action } });
      if (action !== 'normal') {
        await triggerEmergency({
          variables: {
            input: { eventType: action, scope: 'all', zoneId: null, notes: `Бързо действие: ${action}` },
          },
        });
      } else {
        for (const event of activeEvents) {
          await resolveEmergency({ variables: { id: event.id } });
        }
      }
      refetchEvents();
    } catch (e) {
      alert(getErrorMessage(e));
    } finally {
      setActionLoading(false);
    }
  };

  const handleTrigger = async () => {
    try {
      await triggerEmergency({
        variables: {
          input: {
            eventType,
            scope,
            zoneId: scope === 'zone' ? zoneId : null,
            notes: notes || null,
          },
        },
      });
      setDialogOpen(false);
      setNotes('');
      refetchEvents();
    } catch (e) {
      alert(getErrorMessage(e));
    }
  };

  const handleResolve = async (id: number) => {
    if (!window.confirm('Сигурни ли сте, че искате да разрешите това събитие?')) return;
    try {
      await resolveEmergency({ variables: { id } });
      refetchEvents();
    } catch (e) {
      alert(getErrorMessage(e));
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'fire_alarm': return 'error';
      case 'lockdown': return 'warning';
      case 'emergency_unlock': return 'info';
      case 'evacuation': return 'error';
      case 'drill': return 'default';
      default: return 'default';
    }
  };

  const getEventLabel = (type: string) => {
    const labels: Record<string, string> = {
      lockdown: 'Блокада',
      emergency_unlock: 'Аварийно отключване',
      fire_alarm: 'Пожарна аларма',
      evacuation: 'Евакуация',
      drill: 'Упражнение',
    };
    return labels[type] || type;
  };

  const statusColor = getStatusColor();

  return (
    <Box>
      <Card sx={{ bgcolor: statusColor, color: 'white', mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h5" fontWeight="bold">{getStatusText()}</Typography>
              {activeEvents.length > 0 && (
                <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.9 }}>
                  {activeEvents.length} активни събития
                </Typography>
              )}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                sx={{ bgcolor: 'white', color: '#d32f2f' }}
                onClick={() => handleBulkAction('emergency_unlock')}
                disabled={activeEvents.some((e: any) => e.eventType === 'emergency_unlock') || actionLoading}
              >
                ОТКЛЮЧИ
              </Button>
              <Button
                variant="contained"
                sx={{ bgcolor: 'black', color: 'white' }}
                onClick={() => handleBulkAction('lockdown')}
                disabled={activeEvents.some((e: any) => e.eventType === 'lockdown') || actionLoading}
              >
                БЛОКАДА
              </Button>
              <Button
                variant="outlined"
                sx={{ color: 'white', borderColor: 'white' }}
                onClick={() => handleBulkAction('normal')}
                disabled={activeEvents.length === 0 || actionLoading}
              >
                НОРМАЛЕН
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" fontWeight="bold">История на събитията</Typography>
        <Button variant="contained" color="error" onClick={() => setDialogOpen(true)}>
          НОВА СИТУАЦИЯ
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Тип</TableCell>
              <TableCell>Обхват</TableCell>
              <TableCell>Зона</TableCell>
              <TableCell>Задействано на</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {events.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">Няма събития</TableCell>
              </TableRow>
            )}
            {events.map((event: any) => (
              <TableRow key={event.id}>
                <TableCell>
                  <Chip label={getEventLabel(event.eventType)} color={getEventColor(event.eventType)} size="small" />
                </TableCell>
                <TableCell>{event.scope === 'all' ? 'Всички' : event.scope === 'zone' ? 'Зона' : 'Gateway'}</TableCell>
                <TableCell>{event.zone?.name || '-'}</TableCell>
                <TableCell>{new Date(event.triggeredAt).toLocaleString('bg-BG')}</TableCell>
                <TableCell>
                  <Chip label={event.isActive ? 'Активно' : 'Разрешено'} color={event.isActive ? 'error' : 'success'} size="small" />
                </TableCell>
                <TableCell>
                  {event.isActive && (
                    <Button size="small" variant="outlined" color="success" onClick={() => handleResolve(event.id)}>
                      РАЗРЕШИ
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова извънредна ситуация</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Тип</InputLabel>
            <Select value={eventType} label="Тип" onChange={(e) => setEventType(e.target.value)}>
              <MenuItem value="lockdown">Блокада</MenuItem>
              <MenuItem value="emergency_unlock">Аварийно отключване</MenuItem>
              <MenuItem value="fire_alarm">Пожарна аларма</MenuItem>
              <MenuItem value="evacuation">Евакуация</MenuItem>
              <MenuItem value="drill">Упражнение</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Обхват</InputLabel>
            <Select value={scope} label="Обхват" onChange={(e) => setScope(e.target.value)}>
              <MenuItem value="all">Всички зони</MenuItem>
              <MenuItem value="zone">Конкретна зона</MenuItem>
              <MenuItem value="gateway">Gateway</MenuItem>
            </Select>
          </FormControl>
          {scope === 'zone' && (
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Зона</InputLabel>
              <Select value={zoneId} label="Зона" onChange={(e) => setZoneId(e.target.value as number)}>
                {zones.map((z: any) => (
                  <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <TextField fullWidth sx={{ mt: 2 }} label="Бележки" multiline rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Отказ</Button>
          <Button variant="contained" color="error" onClick={handleTrigger} disabled={triggerLoading}>
            {triggerLoading ? 'ЗАРЕЖДАНЕ...' : 'ЗАДЕЙСТВАЙ'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EmergencyPage;
