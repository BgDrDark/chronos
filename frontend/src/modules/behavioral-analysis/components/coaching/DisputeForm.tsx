import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Box,
  Typography,
  Alert,
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { UPDATE_RECOMMENDATION_STATUS } from '../../api/mutations';
import { useError } from '../../../../context/ErrorContext';

interface DisputeFormProps {
  open: boolean;
  onClose: () => void;
  recommendationId: number;
  onSuccess: () => void;
}

const DISPUTE_REASONS = [
  { value: 'data_incorrect', label: 'Данните са грешни' },
  { value: 'missing_context', label: 'Има контекст който системата не вижда' },
  { value: 'personal_circumstances', label: 'Лични обстоятелства' },
  { value: 'other', label: 'Друго' },
];

const DisputeForm: React.FC<DisputeFormProps> = ({ open, onClose, recommendationId, onSuccess }) => {
  const { showSuccess, showError } = useError();
  const [updateStatus] = useMutation(UPDATE_RECOMMENDATION_STATUS);

  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!reason) {
      showError('Моля изберете причина за обжалването');
      return;
    }

    setIsSubmitting(true);
    try {
      await updateStatus({
        variables: {
          recommendationId,
          status: 'disputed',
          disputeReason: reason,
          disputeNotes: notes || undefined,
        },
      });
      showSuccess('Препоръката е обжалвана успешно');
      resetForm();
      onSuccess();
      onClose();
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Грешка при обжалване');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setReason('');
    setNotes('');
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Обжалване на препоръка</DialogTitle>
      <DialogContent>
        <Alert severity="info" sx={{ mb: 3 }}>
          Обжалването ще бъде изпратено до HR/мениджър за преглед. Статусът на препоръката ще се промени на &quot;disputed&quot;.
        </Alert>

        <FormControl component="fieldset" fullWidth sx={{ mb: 3 }}>
          <FormLabel component="legend">Причина за обжалване</FormLabel>
          <RadioGroup value={reason} onChange={(e) => setReason(e.target.value)}>
            {DISPUTE_REASONS.map((option) => (
              <FormControlLabel
                key={option.value}
                value={option.value}
                control={<Radio />}
                label={option.label}
              />
            ))}
          </RadioGroup>
        </FormControl>

        <TextField
          fullWidth
          label="Обяснение"
          multiline
          rows={4}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Опишете подробно защо не сте съгласни с тази препоръка..."
          helperText="Незадължително, но помага за по-бърз преглед"
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} disabled={isSubmitting}>
          Отказ
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={isSubmitting || !reason}
        >
          {isSubmitting ? 'Изпращане...' : 'Изпрати обжалване'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DisputeForm;
