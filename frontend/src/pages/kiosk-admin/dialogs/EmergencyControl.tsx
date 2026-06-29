import React, { useState } from 'react';
import {
  Card, CardContent, Button, Box, Typography,
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import { BULK_EMERGENCY_ACTION } from '../../../graphql/mutations/kioskAdmin';

export const EmergencyControl: React.FC<{ currentMode: string; onAction: () => void }> = ({ currentMode, onAction }) => {
  const [bulkAction] = useMutation(BULK_EMERGENCY_ACTION);
  const [, setLoading] = useState(false);

  const handleAction = async (action: string) => {
    if (!window.confirm('Сигурни ли сте?')) return;
    setLoading(true);
    try {
      await bulkAction({ variables: { action } });
      onAction();
    } catch (e) {
      alert(getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const getProps = () => {
    if (currentMode === 'emergency_unlock') return { color: '#d32f2f', text: 'АВАРИЙНО ОТКЛЮЧЕНО' };
    if (currentMode === 'lockdown') return { color: '#212121', text: 'ПЪЛНА БЛОКАДА' };
    return { color: '#1976d2', text: 'НОРМАЛЕН РЕЖИМ' };
  };

  const p = getProps();

  return (
    <Card sx={{ bgcolor: p.color, color: 'white', mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h5" fontWeight="bold">{p.text}</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              sx={{ bgcolor: 'white', color: '#d32f2f' }}
              onClick={() => handleAction('emergency_unlock')}
              disabled={currentMode === 'emergency_unlock'}
            >
              ОТКЛЮЧИ
            </Button>
            <Button
              variant="contained"
              sx={{ bgcolor: 'black', color: 'white' }}
              onClick={() => handleAction('lockdown')}
              disabled={currentMode === 'lockdown'}
            >
              БЛОКАДА
            </Button>
            <Button
              variant="outlined"
              sx={{ color: 'white', borderColor: 'white' }}
              onClick={() => handleAction('normal')}
              disabled={currentMode === 'normal'}
            >
              НОРМАЛЕН
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
