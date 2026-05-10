import React, { useState } from 'react';
import { Container, Typography, Box, Paper, TextField, Button, Switch, FormControlLabel, Grid, MenuItem } from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { GET_BEHAVIORAL_SETTINGS } from '../api/queries';
import { UPDATE_BEHAVIORAL_SETTINGS } from '../api/mutations';
import { BehavioralSettings } from '../types';
import { useError } from '../../../context/ErrorContext';

const SettingsPage: React.FC = () => {
  const { data, loading } = useQuery(GET_BEHAVIORAL_SETTINGS);
  const [updateSettings] = useMutation(UPDATE_BEHAVIORAL_SETTINGS);
  const { showSuccess, showError } = useError();

  const [form, setForm] = useState({
    rawProfileDays: 90,
    aggregatedProfileMonths: 12,
    recommendationMonths: 6,
    feedbackMonths: 24,
    auditLogMonths: 36,
    autoCleanupEnabled: true,
    cleanupSchedule: 'nightly',
    anonymizeInsteadOfDelete: false,
  });

  React.useEffect(() => {
    if (data?.behavioralSettings) {
      const s: BehavioralSettings = data.behavioralSettings;
      setForm({
        rawProfileDays: s.rawProfileDays,
        aggregatedProfileMonths: s.aggregatedProfileMonths,
        recommendationMonths: s.recommendationMonths,
        feedbackMonths: s.feedbackMonths,
        auditLogMonths: s.auditLogMonths,
        autoCleanupEnabled: s.autoCleanupEnabled,
        cleanupSchedule: s.cleanupSchedule,
        anonymizeInsteadOfDelete: s.anonymizeInsteadOfDelete,
      });
    }
  }, [data]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateSettings({ variables: { input: form } });
      showSuccess('Настройките са запазени успешно');
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Грешка при запазване');
    }
  };

  if (loading) return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Настройки на поведенчески анализ
      </Typography>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Запазване на профили (дни)"
                type="number"
                fullWidth
                value={form.rawProfileDays}
                onChange={e => setForm({ ...form, rawProfileDays: Number(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Агрегирани профили (месеци)"
                type="number"
                fullWidth
                value={form.aggregatedProfileMonths}
                onChange={e => setForm({ ...form, aggregatedProfileMonths: Number(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Препоръки (месеци)"
                type="number"
                fullWidth
                value={form.recommendationMonths}
                onChange={e => setForm({ ...form, recommendationMonths: Number(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Feedback (месеци)"
                type="number"
                fullWidth
                value={form.feedbackMonths}
                onChange={e => setForm({ ...form, feedbackMonths: Number(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Audit log (месеци)"
                type="number"
                fullWidth
                value={form.auditLogMonths}
                onChange={e => setForm({ ...form, auditLogMonths: Number(e.target.value) })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                select
                label="Разписание за почистване"
                fullWidth
                value={form.cleanupSchedule}
                onChange={e => setForm({ ...form, cleanupSchedule: e.target.value })}
              >
                <MenuItem value="nightly">Нощно</MenuItem>
                <MenuItem value="weekly">Седмично</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={form.autoCleanupEnabled}
                    onChange={e => setForm({ ...form, autoCleanupEnabled: e.target.checked })}
                  />
                }
                label="Автоматично почистване"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={form.anonymizeInsteadOfDelete}
                    onChange={e => setForm({ ...form, anonymizeInsteadOfDelete: e.target.checked })}
                  />
                }
                label="Анонимизиране вместо изтриване"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Button type="submit" variant="contained" color="primary">
                Запази настройките
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Container>
  );
};

export default SettingsPage;
