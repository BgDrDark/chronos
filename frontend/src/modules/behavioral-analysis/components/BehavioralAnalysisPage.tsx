import React from 'react';
import { Container, Typography, Box, Paper, Grid, Card, CardContent, Chip } from '@mui/material';
import { useQuery } from '@apollo/client';
import { GET_BEHAVIORAL_PROFILES, GET_BEHAVIORAL_ANOMALIES, GET_BEHAVIORAL_RECOMMENDATIONS } from '../api/queries';
import { BehavioralProfile, BehavioralAnomaly, BehavioralRecommendation } from '../types';
import { formatDate } from '../../../utils/dateUtils';

const priorityColors: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
  low: 'info',
  medium: 'warning',
  high: 'error',
  critical: 'error',
};

const BehavioralAnalysisPage: React.FC = () => {
  const { data: profilesData, loading: profilesLoading } = useQuery(GET_BEHAVIORAL_PROFILES);
  const { data: anomaliesData, loading: anomaliesLoading } = useQuery(GET_BEHAVIORAL_ANOMALIES);
  const { data: recommendationsData, loading: recommendationsLoading } = useQuery(GET_BEHAVIORAL_RECOMMENDATIONS);

  if (profilesLoading || anomaliesLoading || recommendationsLoading) {
    return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;
  }

  const profiles: BehavioralProfile[] = profilesData?.behavioralProfiles || [];
  const anomalies: BehavioralAnomaly[] = anomaliesData?.behavioralAnomalies || [];
  const recommendations: BehavioralRecommendation[] = recommendationsData?.behavioralRecommendations || [];

  const criticalCount = profiles.filter(p => p.status === 'critical').length;
  const atRiskCount = profiles.filter(p => p.status === 'at_risk').length;
  const pendingRecs = recommendations.filter(r => r.status === 'pending').length;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Поведенчески анализ
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Общо служители</Typography>
              <Typography variant="h4">{profiles.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Критичен риск</Typography>
              <Typography variant="h4" color="error">{criticalCount}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>В риск</Typography>
              <Typography variant="h4" color="warning.main">{atRiskCount}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Изчакващи препоръки</Typography>
              <Typography variant="h4">{pendingRecs}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Последни аномалии</Typography>
        {anomalies.length === 0 ? (
          <Typography color="text.secondary">Няма открити аномалии</Typography>
        ) : (
          anomalies.slice(0, 5).map(a => (
            <Box key={a.id} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle1">{a.description}</Typography>
                <Chip label={`Severity: ${a.severity}`} color={a.severity >= 4 ? 'error' : 'warning'} size="small" />
              </Box>
              <Typography variant="caption" color="text.secondary">
                {a.metricName} | {formatDate(a.detectedAt)}
              </Typography>
            </Box>
          ))
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>Препоръки</Typography>
        {recommendations.length === 0 ? (
          <Typography color="text.secondary">Няма активни препоръки</Typography>
        ) : (
          recommendations.slice(0, 5).map(r => (
            <Box key={r.id} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle1">{r.title}</Typography>
                <Chip label={r.priority} color={priorityColors[r.priority] || 'default'} size="small" />
              </Box>
              <Typography variant="body2" sx={{ mt: 1 }}>{r.explanation}</Typography>
            </Box>
          ))
        )}
      </Paper>
    </Container>
  );
};

export default BehavioralAnalysisPage;
