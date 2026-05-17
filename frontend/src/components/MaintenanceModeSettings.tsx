import React, { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import {
  Card, CardContent, Typography, TextField, Button, Box,
  Alert, AlertTitle, CircularProgress, Chip, Switch,
  FormControlLabel, InputAdornment
} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import CancelIcon from '@mui/icons-material/Cancel';
import { InfoIcon } from '../components/ui/InfoIcon';
import { getErrorMessage } from '../types';
import {
  MAINTENANCE_STATUS_QUERY,
  SCHEDULE_MAINTENANCE_MUTATION,
  CANCEL_MAINTENANCE_MUTATION,
} from '../graphql/queries';

const MaintenanceModeSettings: React.FC = () => {
  const { data, loading, refetch } = useQuery(MAINTENANCE_STATUS_QUERY, {
    pollInterval: 10000,
    fetchPolicy: 'network-only',
  });

  const [scheduleMaintenance] = useMutation(SCHEDULE_MAINTENANCE_MUTATION);
  const [cancelMaintenance] = useMutation(CANCEL_MAINTENANCE_MUTATION);

  const [enabled, setEnabled] = useState(false);
  const [delayMinutes, setDelayMinutes] = useState(0);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const maintStatus = data?.maintenanceStatus;
  const isActive = maintStatus?.enabled;
  const isScheduled = maintStatus?.scheduledAt && !maintStatus?.enabled;
  const minutesUntil = maintStatus?.minutesUntil;
  const currentReason = maintStatus?.reason || '';

  const handleToggle = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await scheduleMaintenance({
        variables: {
          input: {
            enabled: !isActive,
            delayMinutes: !isActive ? delayMinutes : 0,
            reason: !isActive ? reason : '',
          },
        },
      });
      setEnabled(!isActive);
      refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await cancelMaintenance();
      refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card sx={{ mb: 4, border: isActive ? '2px solid #f44336' : isScheduled ? '2px solid #ff9800' : '1px solid rgba(0,0,0,0.12)' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <SettingsIcon color={isActive ? 'error' : isScheduled ? 'warning' : 'action'} />
          <Typography variant="h6" fontWeight="bold">Режим поддръжка</Typography>
          {isActive && <Chip label="АКТИВЕН" color="error" size="small" />}
          {isScheduled && <Chip label="НАСРОЧЕН" color="warning" size="small" />}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {isScheduled && minutesUntil !== null && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <AlertTitle>Насрочена поддръжка</AlertTitle>
            Системата ще премине в режим поддръжка след <strong>{minutesUntil} мин.</strong>
            {currentReason && <><br />Причина: {currentReason}</>}
          </Alert>
        )}

        {isActive && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Режим поддръжка е активен</AlertTitle>
            Само администраторите могат да влизат в системата.
            {currentReason && <><br />Причина: {currentReason}</>}
          </Alert>
        )}

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                color="error"
              />
            }
            label={enabled ? 'Включи поддръжка' : 'Изключи поддръжка'}
          />
        </Box>

        {enabled && !isActive && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 2 }}>
            <TextField
              fullWidth
              label="Забавяне (минути)"
              type="number"
              value={delayMinutes}
              onChange={(e) => setDelayMinutes(parseInt(e.target.value) || 0)}
              inputProps={{ min: 0 }}
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoIcon helpText="0 = веднага, >0 = след X минути" />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <TextField
              fullWidth
              label="Причина / Съобщение"
              multiline
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Напр: Ъпгрейд на базата данни"
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoIcon helpText="Това съобщение ще се вижда от всички потребители" />
                    </InputAdornment>
                  ),
                },
              }}
            />
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color={isActive ? 'success' : 'error'}
            onClick={handleToggle}
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : null}
          >
            {isActive ? 'Изключи поддръжка' : submitting ? 'Зареждане...' : 'Насрочи поддръжка'}
          </Button>

          {isScheduled && (
            <Button
              variant="outlined"
              color="warning"
              onClick={handleCancel}
              disabled={submitting}
              startIcon={<CancelIcon />}
            >
              Отмени
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default MaintenanceModeSettings;
