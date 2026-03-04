import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Alert,
  Grid
} from '@mui/material';
import { useMutation, gql } from '@apollo/client';

const CREATE_MANUAL_TIME_LOG_MUTATION = gql`
  mutation CreateManualTimeLog($userId: Int!, $startTime: DateTime!, $endTime: DateTime!, $breakDurationMinutes: Int) {
    createManualTimeLog(userId: $userId, startTime: $startTime, endTime: $endTime, breakDurationMinutes: $breakDurationMinutes) {
      id
      startTime
      endTime
    }
  }
`;

interface ManualTimeLogModalProps {
  open: boolean;
  onClose: () => void;
  users: any[];
  initialDate?: string | null;
  initialUserId?: string | number | null;
  refetch: () => void;
}

const ManualTimeLogModal: React.FC<ManualTimeLogModalProps> = ({ 
  open, onClose, users, initialDate, initialUserId, refetch 
}) => {
  const [userId, setUserId] = useState<string>('');
  const [date, setDate] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('09:00');
  const [endTime, setEndTime] = useState<string>('17:00');
  const [breakDuration, setBreakDuration] = useState<string>('60');
  const [error, setError] = useState<string | null>(null);

  const [createLog, { loading }] = useMutation(CREATE_MANUAL_TIME_LOG_MUTATION);

  useEffect(() => {
    if (open) {
      if (initialUserId) setUserId(initialUserId.toString());
      if (initialDate) setDate(initialDate);
      else setDate(new Date().toISOString().split('T')[0]);
      setBreakDuration('60');
      setError(null);
    }
  }, [open, initialDate, initialUserId]);

  const handleSubmit = async () => {
    setError(null);
    if (!userId || !date || !startTime || !endTime) {
      setError('Моля попълнете всички полета.');
      return;
    }

    try {
      // Combine date and time to ISO DateTime string
      const startDateTime = new Date(`${date}T${startTime}:00`).toISOString();
      const endDateTime = new Date(`${date}T${endTime}:00`).toISOString();

      await createLog({
        variables: {
          userId: parseInt(userId),
          startTime: startDateTime,
          endTime: endDateTime,
          breakDurationMinutes: parseInt(breakDuration) || 0
        }
      });
      
      refetch();
      onClose();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Ръчно добавяне на часове</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 0.5 }}>
          <Grid size={{ xs: 12 }}>
            <TextField
              select
              fullWidth
              label="Служител"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            >
              {users?.length > 0 ? users.map((u: any) => (
                <MenuItem key={u.id} value={u.id}>
                  {u.firstName} {u.lastName} ({u.email})
                </MenuItem>
              )) : <MenuItem disabled value="">Зареждане...</MenuItem>}
            </TextField>
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField
              type="date"
              fullWidth
              label="Дата"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField
              type="time"
              fullWidth
              label="Начало"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField
              type="time"
              fullWidth
              label="Край"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField
              type="number"
              fullWidth
              label="Почивка (минути)"
              value={breakDuration}
              onChange={(e) => setBreakDuration(e.target.value)}
            />
          </Grid>
        </Grid>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">Отказ</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          Запази
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ManualTimeLogModal;
