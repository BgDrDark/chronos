import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Typography, Box, RadioGroup, FormControlLabel, Radio, Paper, Stepper, Step, StepLabel, Alert,
} from '@mui/material';

const LIKERT_LABELS = [
  'Напълно несъгласен',
  'По-скоро несъгласен',
  'Нито съгласен, нито несъгласен',
  'По-скоро съгласен',
  'Напълно съгласен',
];

const FACTOR_NAMES: Record<string, string> = {
  openness: 'Отвореност към нов опит',
  conscientiousness: 'Съзнателност',
  extraversion: 'Екстраверсия',
  agreeableness: 'Дружелюбност',
  neuroticism: 'Невротизъм',
};

interface Question {
  id: number;
  bg: string;
  en: string;
  factor: string;
  direction: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  questions: Question[];
  templateId: number;
  onSubmit: (templateId: number, answers: number[]) => Promise<void>;
}

const QUESTIONS_PER_PAGE = 10;

const PersonalityTestForm: React.FC<Props> = ({ open, onClose, questions, templateId, onSubmit }) => {
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [activeStep, setActiveStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalPages = Math.ceil(questions.length / QUESTIONS_PER_PAGE);

  const currentQuestions = questions.slice(
    activeStep * QUESTIONS_PER_PAGE,
    (activeStep + 1) * QUESTIONS_PER_PAGE,
  );

  const factorForStep = activeStep < Math.ceil(50 / QUESTIONS_PER_PAGE)
    ? ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'][activeStep]
    : null;

  const answeredCount = Object.keys(answers).length;

  const handleAnswer = (questionId: number, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const allCurrentAnswered = currentQuestions.every((q) => answers[q.id] !== undefined);

  const handleNext = () => {
    if (activeStep < totalPages - 1) {
      setActiveStep((s) => s + 1);
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep((s) => s - 1);
    }
  };

  const handleSubmit = async () => {
    if (answeredCount < questions.length) {
      setError(`Моля, отговорете на всички ${questions.length} въпроса (отговорени: ${answeredCount}).`);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const orderedAnswers = questions.map((q) => answers[q.id]);
      await onSubmit(templateId, orderedAnswers);
      onClose();
    } catch {
      setError('Грешка при изпращане. Опитайте отново.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (answeredCount > 0) {
      if (!window.confirm('Сигурни ли сте, че искате да затворите? Отговорите ще бъдат загубени.')) return;
    }
    setAnswers({});
    setActiveStep(0);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h6">Психологически профил (IPIP-50)</Typography>
        <Typography variant="body2" color="text.secondary">
          {answeredCount}/{questions.length} отговорени
        </Typography>
      </DialogTitle>
      <DialogContent dividers>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
          {Array.from({ length: totalPages }).map((_, i) => (
            <Step key={i}>
              <StepLabel>{FACTOR_NAMES[['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'][i]] || `Стъпка ${i + 1}`}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Typography variant="subtitle2" color="primary" gutterBottom>
          {factorForStep ? FACTOR_NAMES[factorForStep] : `Страница ${activeStep + 1}`}
        </Typography>

        {currentQuestions.map((q) => (
          <Paper key={q.id} variant="outlined" sx={{ p: 2, mb: 2 }}>
            <Typography variant="body1" gutterBottom>
              {q.bg}
            </Typography>
            <RadioGroup
              row
              value={answers[q.id] ?? ''}
              onChange={(e) => handleAnswer(q.id, parseInt(e.target.value, 10))}
            >
              {LIKERT_LABELS.map((label, i) => (
                <FormControlLabel
                  key={i}
                  value={i + 1}
                  control={<Radio size="small" />}
                  label={<Typography variant="caption">{label}</Typography>}
                  sx={{ mr: 1 }}
                />
              ))}
            </RadioGroup>
          </Paper>
        ))}
      </DialogContent>
      <DialogActions sx={{ justifyContent: 'space-between', px: 3, py: 2 }}>
        <Button disabled={activeStep === 0} onClick={handleBack}>
          Назад
        </Button>
        <Box>
          <Button onClick={handleClose} sx={{ mr: 1 }}>
            Отказ
          </Button>
          {activeStep < totalPages - 1 ? (
            <Button variant="contained" disabled={!allCurrentAnswered} onClick={handleNext}>
              Напред
            </Button>
          ) : (
            <Button
              variant="contained"
              color="primary"
              disabled={submitting || answeredCount < questions.length}
              onClick={handleSubmit}
            >
              {submitting ? 'Изпращане...' : 'Изпрати'}
            </Button>
          )}
        </Box>
      </DialogActions>
    </Dialog>
  );
};

export default PersonalityTestForm;
