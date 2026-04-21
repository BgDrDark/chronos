import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Alert,
  Grid,
  Box,
  InputAdornment
} from '@mui/material';
import { useMutation, gql } from '@apollo/client';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { type User } from '../types';
import { InfoIcon } from './ui/InfoIcon';
import { scheduleFieldsHelp } from './ui/fieldsHelpText';
import { extractErrorMessage } from '../context/ErrorContext';

const CREATE_MANUAL_TIME_LOG_MUTATION = gql`
  mutation CreateManualTimeLog($userId: Int!, $startTime: DateTime!, $endTime: DateTime!, $breakDurationMinutes: Int) {
    createManualTimeLog(userId: $userId, startTime: $startTime, endTime: $endTime, breakDurationMinutes: $breakDurationMinutes) {
      id
      startTime
      endTime
    }
  }
`;

const manualLogSchema = z.object({
  userId: z.string().min(1, 'Изберете служител'),
  date: z.string().min(1, 'Изберете дата'),
  startTime: z.string().min(1, 'Изберете начален час'),
  endTime: z.string().min(1, 'Изберете краен час'),
  breakDuration: z.string().optional(),
});

type ManualLogFormData = z.infer<typeof manualLogSchema>;

interface ManualTimeLogModalProps {
  open: boolean;
  onClose: () => void;
  users: User[];
  initialDate?: string | null;
  initialUserId?: string | number | null;
  refetch: () => void;
}

const ManualTimeLogModal: React.FC<ManualTimeLogModalProps> = ({ 
  open, onClose, users, initialDate, initialUserId, refetch 
}) => {
  const [createLog, { loading }] = useMutation(CREATE_MANUAL_TIME_LOG_MUTATION);
  const [apiError, setApiError] = React.useState<string | null>(null);

  const { control, handleSubmit, reset, formState: { errors } } = useForm<ManualLogFormData>({
    resolver: zodResolver(manualLogSchema),
    defaultValues: {
      userId: initialUserId?.toString() || '',
      date: initialDate || new Date().toISOString().split('T')[0],
      startTime: '09:00',
      endTime: '17:00',
      breakDuration: '60'
    }
  });

  // Reset form when initial values change or modal opens
  React.useEffect(() => {
    if (open) {
      reset({
        userId: initialUserId?.toString() || '',
        date: initialDate || new Date().toISOString().split('T')[0],
        startTime: '09:00',
        endTime: '17:00',
        breakDuration: '60'
      });
      setApiError(null);
    }
  }, [open, initialUserId, initialDate, reset]);

  const onSubmit = async (data: ManualLogFormData) => {
    setApiError(null);
    try {
      const startDateTime = new Date(`${data.date}T${data.startTime}:00`).toISOString();
      const endDateTime = new Date(`${data.date}T${data.endTime}:00`).toISOString();

      await createLog({
        variables: {
          userId: parseInt(data.userId),
          startTime: startDateTime,
          endTime: endDateTime,
          breakDurationMinutes: parseInt(data.breakDuration || '0') || 0
        }
      });
      
      refetch();
      onClose();
    } catch (err) {
      setApiError(extractErrorMessage(err));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Ръчно добавяне на часове</DialogTitle>
      <Box component="form" onSubmit={handleSubmit(onSubmit)}>
        <DialogContent dividers>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <Controller
                name="userId"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    fullWidth
                    label="Служител"
                    error={!!errors.userId}
                    helperText={errors.userId?.message}
                    size="small"
                  >
                    {users?.length > 0 ? users.map((u: User) => (
                      <MenuItem key={u.id} value={u.id}>
                        {u.firstName} {u.lastName} ({u.email})
                      </MenuItem>
                    )) : <MenuItem disabled value="">Зареждане...</MenuItem>}
                  </TextField>
                )}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Controller
                name="date"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="date"
                    fullWidth
                    label="Дата"
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.date}
                    helperText={errors.date?.message}
                    size="small"
                    slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={scheduleFieldsHelp.scheduleDate} /></InputAdornment> } }}
                  />
                )}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <Controller
                name="startTime"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="time"
                    fullWidth
                    label="Начало"
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.startTime}
                    helperText={errors.startTime?.message}
                    size="small"
                    slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={scheduleFieldsHelp.startTime} /></InputAdornment> } }}
                  />
                )}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <Controller
                name="endTime"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="time"
                    fullWidth
                    label="Край"
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.endTime}
                    helperText={errors.endTime?.message}
                    size="small"
                    slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={scheduleFieldsHelp.endTime} /></InputAdornment> } }}
                  />
                )}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Controller
                name="breakDuration"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    fullWidth
                    label="Почивка (минути)"
                    size="small"
                    slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={scheduleFieldsHelp.breakMinutes} /></InputAdornment> } }}
                  />
                )}
              />
            </Grid>
          </Grid>
          {apiError && <Alert severity="error" sx={{ mt: 2 }}>{apiError}</Alert>}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} color="inherit">Отказ</Button>
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Запис...' : 'Запази'}
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
};

export default ManualTimeLogModal;
