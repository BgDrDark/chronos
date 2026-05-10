import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, TextField, Button, Grid, MenuItem, Switch, FormControlLabel, Alert } from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { GET_BEHAVIORAL_RULES } from '../api/queries';
import { CREATE_BEHAVIORAL_RULE, UPDATE_BEHAVIORAL_RULE } from '../api/mutations';
import { BehavioralRule } from '../types';
import { useError } from '../../../context/ErrorContext';

const conditionTypes = [
  { value: 'threshold', label: 'Праг (Threshold)' },
  { value: 'composite', label: 'Комбинирано (Composite)' },
  { value: 'trend', label: 'Тренд (Trend)' },
  { value: 'custom_expression', label: 'Персонален израз' },
];

const metricOptions = [
  { value: 'punctuality_score', label: 'Точност' },
  { value: 'efficiency_score', label: 'Ефективност' },
  { value: 'overtime_score', label: 'Извънреден труд' },
  { value: 'burnout_risk', label: 'Риск от прегаряне' },
  { value: 'financial_stress_score', label: 'Финансов стрес' },
  { value: 'engagement_score', label: 'Ангажираност' },
  { value: 'scrap_rate', label: 'Бракуване' },
];

const RuleBuilderPage: React.FC = () => {
  const { data, loading } = useQuery(GET_BEHAVIORAL_RULES);
  const [createRule] = useMutation(CREATE_BEHAVIORAL_RULE);
  const [updateRule] = useMutation(UPDATE_BEHAVIORAL_RULE);
  const { showSuccess, showError } = useError();

  const [selectedRule, setSelectedRule] = useState<BehavioralRule | null>(null);
  const [form, setForm] = useState({
    name: '',
    description: '',
    ruleType: 'custom',
    conditionType: 'threshold',
    conditionConfig: '{}',
    recommendationTemplate: '{}',
    autoExecuteAction: '',
    autoExecute: false,
    isActive: true,
    shadowMode: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isEditing, setIsEditing] = useState(false);

  const rules: BehavioralRule[] = data?.behavioralRules || [];

  useEffect(() => {
    if (selectedRule) {
      setForm({
        name: selectedRule.name,
        description: selectedRule.description || '',
        ruleType: selectedRule.ruleType,
        conditionType: selectedRule.conditionType,
        conditionConfig: JSON.stringify(selectedRule.conditionConfig, null, 2),
        recommendationTemplate: JSON.stringify(selectedRule.recommendationTemplate, null, 2),
        autoExecuteAction: selectedRule.autoExecuteAction || '',
        autoExecute: selectedRule.autoExecute,
        isActive: selectedRule.isActive,
        shadowMode: selectedRule.shadowMode,
      });
      setIsEditing(true);
    } else {
      setForm({
        name: '',
        description: '',
        ruleType: 'custom',
        conditionType: 'threshold',
        conditionConfig: '{\n  "metric": "burnout_risk",\n  "operator": ">",\n  "threshold": 0.7\n}',
        recommendationTemplate: '{\n  "type": "general",\n  "priority": "medium",\n  "title": "Препоръка",\n  "description": "",\n  "suggested_action": "",\n  "explanation": ""\n}',
        autoExecuteAction: '',
        autoExecute: false,
        isActive: true,
        shadowMode: false,
      });
      setIsEditing(false);
    }
    setErrors({});
  }, [selectedRule]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!form.name.trim()) newErrors.name = 'Името е задължително';
    
    try {
      JSON.parse(form.conditionConfig);
    } catch {
      newErrors.conditionConfig = 'Невалиден JSON формат';
    }
    
    try {
      JSON.parse(form.recommendationTemplate);
    } catch {
      newErrors.recommendationTemplate = 'Невалиден JSON формат';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      const input = {
        ...form,
        conditionConfig: JSON.parse(form.conditionConfig),
        recommendationTemplate: JSON.parse(form.recommendationTemplate),
      };

      if (isEditing && selectedRule) {
        await updateRule({ variables: { ruleId: selectedRule.id, input } });
        showSuccess('Правилото е обновено успешно');
      } else {
        await createRule({ variables: { input } });
        showSuccess('Правилото е създадено успешно');
      }
      
      setSelectedRule(null);
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Грешка при запазване');
    }
  };

  if (loading) return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Управление на правила
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Списък с правила</Typography>
            <Box sx={{ maxHeight: '60vh', overflow: 'auto' }}>
              {rules.map(rule => (
                <Box
                  key={rule.id}
                  sx={{
                    p: 1.5,
                    mb: 1,
                    border: '1px solid #e0e0e0',
                    borderRadius: 1,
                    cursor: 'pointer',
                    bgcolor: selectedRule?.id === rule.id ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                  }}
                  onClick={() => setSelectedRule(rule)}
                >
                  <Typography variant="subtitle2">{rule.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {rule.ruleType === 'built_in' ? 'Системно' : 'Потребителско'} • {rule.conditionType}
                  </Typography>
                </Box>
              ))}
            </Box>
            <Button
              variant="contained"
              fullWidth
              sx={{ mt: 2 }}
              onClick={() => setSelectedRule(null)}
            >
              Ново правило
            </Button>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {isEditing ? 'Редактиране на правило' : 'Създаване на ново правило'}
            </Typography>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    label="Име на правилото"
                    fullWidth
                    value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })}
                    error={!!errors.name}
                    helperText={errors.name}
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    label="Описание"
                    fullWidth
                    multiline
                    rows={2}
                    value={form.description}
                    onChange={e => setForm({ ...form, description: e.target.value })}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    select
                    label="Тип условие"
                    fullWidth
                    value={form.conditionType}
                    onChange={e => setForm({ ...form, conditionType: e.target.value })}
                  >
                    {conditionTypes.map(opt => (
                      <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    label="Конфигурация на условието (JSON)"
                    fullWidth
                    multiline
                    rows={6}
                    value={form.conditionConfig}
                    onChange={e => setForm({ ...form, conditionConfig: e.target.value })}
                    error={!!errors.conditionConfig}
                    helperText={errors.conditionConfig || 'Дефинирайте условието в JSON формат'}
                    sx={{ fontFamily: 'monospace' }}
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    label="Шаблон за препоръка (JSON)"
                    fullWidth
                    multiline
                    rows={8}
                    value={form.recommendationTemplate}
                    onChange={e => setForm({ ...form, recommendationTemplate: e.target.value })}
                    error={!!errors.recommendationTemplate}
                    helperText={errors.recommendationTemplate || 'Дефинирайте препоръката в JSON формат'}
                    sx={{ fontFamily: 'monospace' }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    select
                    label="Автоматично действие"
                    fullWidth
                    value={form.autoExecuteAction}
                    onChange={e => setForm({ ...form, autoExecuteAction: e.target.value })}
                  >
                    <MenuItem value="">Няма</MenuItem>
                    <MenuItem value="notification">Изпрати уведомление</MenuItem>
                    <MenuItem value="bonus">Добави бонус</MenuItem>
                    <MenuItem value="leave">Предложи отпуск</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', alignItems: 'center', gap: 2, pt: 1 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.autoExecute}
                        onChange={e => setForm({ ...form, autoExecute: e.target.checked })}
                      />
                    }
                    label="Автоматично изпълнение"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.shadowMode}
                        onChange={e => setForm({ ...form, shadowMode: e.target.checked })}
                      />
                    }
                    label="Shadow Mode"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.isActive}
                        onChange={e => setForm({ ...form, isActive: e.target.checked })}
                      />
                    }
                    label="Активно"
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Button type="submit" variant="contained" color="primary" size="large">
                    {isEditing ? 'Запази промените' : 'Създай правило'}
                  </Button>
                </Grid>
              </Grid>
            </form>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default RuleBuilderPage;
