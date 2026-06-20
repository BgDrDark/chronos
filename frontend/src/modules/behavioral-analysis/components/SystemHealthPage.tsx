import React from 'react';
import { Container, Typography, Box, Grid, Card, CardContent, Chip, Alert, Button } from '@mui/material';
import { useQuery } from '@apollo/client';
import { GET_SYSTEM_HEALTH } from '../api/queries';
import { formatDate } from '../../../utils/dateUtils';

const SystemHealthPage: React.FC = () => {
  const { data, loading, refetch } = useQuery(GET_SYSTEM_HEALTH);

  if (loading) return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;

  const health = data?.behavioralSystemHealth;

  if (!health) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="info">Няма налични данни за системното здраве.</Alert>
      </Container>
    );
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'partial': return 'warning';
      default: return 'error';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Системно здраве
      </Typography>

      <Grid container spacing={3}>
        {/* Status Overview */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Статус на изчисленията</Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">Последно изчисление</Typography>
                <Chip 
                  label={health.lastComputationStatus} 
                  color={statusColor(health.lastComputationStatus)} 
                  size="small" 
                />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">Изпълнено на</Typography>
                <Typography variant="body2">{health.lastComputationAt ? formatDate(health.lastComputationAt) : 'Никога'}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">Време за изпълнение</Typography>
                <Typography variant="body2">{health.lastComputationDurationSeconds ? `${health.lastComputationDurationSeconds}s` : '-'}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Circuit Breaker */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Circuit Breaker</Typography>
              <Alert severity={health.circuitBreakerOpen ? 'error' : 'success'} sx={{ mb: 2 }}>
                {health.circuitBreakerOpen ? 'Отворен (Спряно)' : 'Затворен (Активен)'}
              </Alert>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Брой грешки</Typography>
                <Typography variant="body2">{health.circuitBreakerFailureCount}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Stats */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Статистика</Typography>
              <Grid container spacing={2}>
                <Grid size={6}>
                  <Typography variant="body2" color="text.secondary">Обработени служители</Typography>
                  <Typography variant="h4">{health.employeesProcessed}</Typography>
                </Grid>
                <Grid size={6}>
                  <Typography variant="body2" color="text.secondary">Грешки</Typography>
                  <Typography variant="h4" color="error">{health.employeesFailed}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Alerts */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Днешни алерти</Typography>
              <Typography variant="h3" color="warning.main" align="center" sx={{ mt: 2 }}>
                {health.triggeredAlertsToday}
              </Typography>
              <Typography variant="caption" display="block" align="center" sx={{ mt: 1 }}>
                Real-time събития днес
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
        <Button variant="contained" onClick={() => refetch()}>
          Опресни статуса
        </Button>
      </Box>
    </Container>
  );
};

export default SystemHealthPage;
