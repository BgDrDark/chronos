import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Typography, Box, Slider, Alert, TextField,
} from '@mui/material';

const MARKS = [
  { value: 1, label: 'Никога' },
  { value: 2, label: 'Рядко' },
  { value: 3, label: 'Понякога' },
  { value: 4, label: 'Често' },
  { value: 5, label: 'Постоянно' },
];

const SATISFACTION_MARKS = [
  { value: 1, label: 'Много недоволен' },
  { value: 2, label: 'Недоволен' },
  { value: 3, label: 'Неутрален' },
  { value: 4, label: 'Доволен' },
  { value: 5, label: 'Много доволен' },
];

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (input: {
    burnoutFeeling?: number | null;
    engagementFeeling?: number | null;
    stressLevel?: number | null;
    energyLevel?: number | null;
    workSatisfaction?: number | null;
    notes?: string | null;
  }) => Promise<void>;
}

const PulseSurveyForm: React.FC<Props> = ({ open, onClose, onSubmit }) => {
  const [burnout, setBurnout] = useState<number>(3);
  const [engagement, setEngagement] = useState<number>(3);
  const [stress, setStress] = useState<number>(3);
  const [energy, setEnergy] = useState<number>(3);
  const [satisfaction, setSatisfaction] = useState<number>(3);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        burnoutFeeling: burnout,
        engagementFeeling: engagement,
        stressLevel: stress,
        energyLevel: energy,
        workSatisfaction: satisfaction,
        notes: notes || null,
      });
      onClose();
    } catch (e) {
      setError('Грешка при изпращане. Опитайте отново.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Typography variant="h6">Как се чувствате?</Typography>
        <Typography variant="body2" color="text.secondary">
          Споделете как сте напоследък — вашите отговори помагат за по-точна оценка
        </Typography>
      </DialogTitle>
      <DialogContent dividers>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Box sx={{ mb: 3 }}>
          <Typography gutterBottom>Чувствате ли се изтощен/а?</Typography>
          <Slider value={burnout} onChange={(_, v) => setBurnout(v as number)} step={1} marks={MARKS} min={1} max={5} />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography gutterBottom>Чувствате ли се ангажиран/а с работата?</Typography>
          <Slider value={engagement} onChange={(_, v) => setEngagement(v as number)} step={1} marks={MARKS} min={1} max={5} />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography gutterBottom>Ниво на стрес?</Typography>
          <Slider value={stress} onChange={(_, v) => setStress(v as number)} step={1} marks={MARKS} min={1} max={5} />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography gutterBottom>Ниво на енергия?</Typography>
          <Slider value={energy} onChange={(_, v) => setEnergy(v as number)} step={1} marks={MARKS} min={1} max={5} />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography gutterBottom>Удовлетвореност от работата?</Typography>
          <Slider value={satisfaction} onChange={(_, v) => setSatisfaction(v as number)} step={1} marks={SATISFACTION_MARKS} min={1} max={5} />
        </Box>

        <TextField
          fullWidth
          multiline
          rows={3}
          label="Допълнителни бележки (по желание)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose}>Затвори</Button>
        <Button variant="contained" disabled={submitting} onClick={handleSubmit}>
          {submitting ? 'Изпращане...' : 'Изпрати'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PulseSurveyForm;
