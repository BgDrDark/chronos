import React, { useState } from 'react';
import { Container, Typography, Box, Paper, Grid, Card, CardContent, Chip, LinearProgress, Alert } from '@mui/material';
import { useQuery } from '@apollo/client';
import { GET_BEHAVIORAL_PROFILES, GET_BEHAVIORAL_RECOMMENDATIONS, GET_BEHAVIORAL_ANOMALIES } from '../api/queries';
import { BehavioralProfile, BehavioralRecommendation, BehavioralAnomaly } from '../types';
import CoachingTips from './coaching/CoachingTips';
import DisputeForm from './coaching/DisputeForm';
import PsychologyIcon from '@mui/icons-material/Psychology';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';

const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  switch (status) {
    case 'stable':
      return 'success';
    case 'improving':
      return 'info';
    case 'at_risk':
      return 'warning';
    case 'critical':
      return 'error';
    case 'star':
      return 'success';
    case 'insufficient_data':
      return 'default';
    default:
      return 'default';
  }
};

const getStatusLabel = (status: string): string => {
  switch (status) {
    case 'stable':
      return 'Стабилен';
    case 'improving':
      return 'Подобрява се';
    case 'at_risk':
      return 'В риск';
    case 'critical':
      return 'Критичен';
    case 'star':
      return 'Звезда';
    case 'insufficient_data':
      return 'Недостатъчно данни';
    default:
      return status;
  }
};

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'increasing':
      return <TrendingUpIcon color="success" fontSize="small" />;
    case 'decreasing':
      return <TrendingDownIcon color="error" fontSize="small" />;
    default:
      return <TrendingFlatIcon color="action" fontSize="small" />;
  }
};

const MetricCard: React.FC<{
  label: string;
  value: number;
  max?: number;
  inverse?: boolean;
  thresholds?: { warning: number; critical: number };
}> = ({ label, value, max = 100, inverse = false, thresholds }) => {
  const normalizedValue = max > 1 ? (value / max) * 100 : value * 100;
  
  let color: 'success' | 'warning' | 'error' = 'success';
  if (thresholds) {
    const checkValue = inverse ? value : 100 - normalizedValue;
    if (checkValue >= thresholds.critical) color = 'error';
    else if (checkValue >= thresholds.warning) color = 'warning';
  } else if (inverse) {
    if (normalizedValue > 70) color = 'error';
    else if (normalizedValue > 40) color = 'warning';
  } else {
    if (normalizedValue < 40) color = 'error';
    else if (normalizedValue < 70) color = 'warning';
  }

  const barColor = color === 'success' ? '#388e3c' : color === 'warning' ? '#fbc02d' : '#d32f2f';

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2">{label}</Typography>
        <Typography variant="body2" fontWeight="bold">
          {max > 1 ? `${value.toFixed(1)}/${max}` : `${(value * 100).toFixed(1)}%`}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(normalizedValue, 100)}
        sx={{
          height: 8,
          borderRadius: 1,
          bgcolor: '#e0e0e0',
          '& .MuiLinearProgress-bar': { bgcolor: barColor },
        }}
      />
    </Box>
  );
};

const MyBehavioralProfilePage: React.FC = () => {
  const [disputeOpen, setDisputeOpen] = useState(false);
  const [selectedRecId, setSelectedRecId] = useState<number | null>(null);

  const { data: profilesData, loading: profilesLoading } = useQuery(GET_BEHAVIORAL_PROFILES);
  const { data: recsData, loading: recsLoading, refetch: refetchRecs } = useQuery(GET_BEHAVIORAL_RECOMMENDATIONS);
  const { data: anomaliesData, loading: anomaliesLoading } = useQuery(GET_BEHAVIORAL_ANOMALIES);

  const profile: BehavioralProfile | undefined = profilesData?.behavioralProfiles?.[0];
  const recommendations: BehavioralRecommendation[] = recsData?.behavioralRecommendations || [];
  const anomalies: BehavioralAnomaly[] = anomaliesData?.behavioralAnomalies || [];

  if (profilesLoading || recsLoading || anomaliesLoading) {
    return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;
  }

  if (!profile) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="info">
          Няма наличен поведенчески профил. Данните се изчисляват нощно.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Моят поведенчески профил
      </Typography>

      {profile.status === 'insufficient_data' && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Недостатъчно данни за пълен анализ. Профилът ще бъде обновен след като имаме повече информация.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Status & Confidence */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Статус</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Chip
                  label={getStatusLabel(profile.status)}
                  color={getStatusColor(profile.status)}
                  size="medium"
                />
                {getTrendIcon(profile.trendDirection)}
              </Box>
              <Typography variant="body2" color="text.secondary">
                Сигурност на данните: {(profile.confidenceScore * 100).toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Пълнота на данните: {(profile.dataCompleteness * 100).toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Последно обновление: {new Date(profile.computedAt).toLocaleDateString('bg-BG')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* XAI Contribution Factors */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Фактори на риска
              </Typography>
              {profile.contributionFactors ? (
                Object.entries(profile.contributionFactors).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                        {key.replace(/_/g, ' ')}
                      </Typography>
                      <Typography variant="caption">{((value as number) * 100).toFixed(0)}%</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(value as number) * 100}
                      sx={{ height: 4, borderRadius: 1, bgcolor: '#e0e0e0', '& .MuiLinearProgress-bar': { bgcolor: '#1976d2' } }}
                    />
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">Няма налични данни.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Peer Group */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Сравнение с колегите</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Вашият персентил спрямо колегите от компанията
              </Typography>
              <Typography variant="h3" color="primary" align="center" sx={{ mb: 1 }}>
                {profile.peerGroupPercentile.toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                {profile.peerGroupPercentile >= 75
                  ? 'Над 75% от колегите'
                  : profile.peerGroupPercentile >= 50
                  ? 'Над половината колеги'
                  : 'Под средното ниво'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Metrics */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Метрики</Typography>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <MetricCard label="Точност" value={profile.punctualityScore} />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <MetricCard label="Ефективност" value={profile.efficiencyScore} />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <MetricCard label="Присъствие" value={profile.attendanceScore} />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <MetricCard
                    label="Риск прегаряне"
                    value={profile.burnoutRisk}
                    max={1}
                    inverse
                    thresholds={{ warning: 0.6, critical: 0.8 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <MetricCard
                    label="Финансов стрес"
                    value={profile.financialStressScore}
                    max={1}
                    inverse
                    thresholds={{ warning: 0.5, critical: 0.7 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <MetricCard
                    label="Извънреден труд"
                    value={profile.overtimeScore}
                    max={1}
                    inverse
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Recommendations */}
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Препоръки за мен</Typography>
            {recommendations.length === 0 ? (
              <Typography color="text.secondary">Няма активни препоръки. Продължавай в същия дух!</Typography>
            ) : (
              recommendations.map((rec) => (
                <Box key={rec.id} sx={{ mb: 3, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip
                      label={rec.priority}
                      color={rec.priority === 'critical' ? 'error' : rec.priority === 'high' ? 'warning' : 'default'}
                      size="small"
                    />
                    <Typography variant="subtitle1" fontWeight="bold">{rec.title}</Typography>
                  </Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>{rec.explanation}</Typography>
                  
                  {rec.status === 'disputed' && (
                    <Alert severity="info" icon={<WarningIcon />} sx={{ mb: 1 }}>
                      Обжалвана: {rec.disputeReason}
                      {rec.disputeNotes && <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>{rec.disputeNotes}</Typography>}
                    </Alert>
                  )}

                  {rec.status === 'pending' && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Не сте съгласни с тази препоръка?
                      </Typography>
                      <button
                        style={{ marginTop: 4, cursor: 'pointer', color: '#1976d2', background: 'none', border: 'none', padding: 0 }}
                        onClick={() => {
                          setSelectedRecId(rec.id);
                          setDisputeOpen(true);
                        }}
                      >
                        Обжалвай препоръката
                      </button>
                    </Box>
                  )}

                  {rec.coachingTips && (
                    <CoachingTips
                      tips={rec.coachingTips as Record<string, unknown>}
                      recommendationType={rec.type}
                    />
                  )}
                </Box>
              ))
            )}
          </Paper>
        </Grid>

        {/* Anomalies */}
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Забелязани аномалии</Typography>
            {anomalies.length === 0 ? (
              <Typography color="text.secondary">Няма забелязани аномалии.</Typography>
            ) : (
              anomalies.map((anomaly) => (
                <Box key={anomaly.id} sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  {anomaly.suppressed ? (
                    <CheckCircleIcon color="disabled" fontSize="small" />
                  ) : (
                    <WarningIcon color={anomaly.severity > 3 ? 'error' : 'warning'} fontSize="small" />
                  )}
                  <Typography variant="body2">
                    {anomaly.description}
                  </Typography>
                  {anomaly.suppressed && (
                    <Chip label="Потисната" size="small" color="default" />
                  )}
                </Box>
              ))
            )}
          </Paper>
        </Grid>
      </Grid>

      <DisputeForm
        open={disputeOpen}
        onClose={() => setDisputeOpen(false)}
        recommendationId={selectedRecId || 0}
        onSuccess={() => refetchRecs()}
      />
    </Container>
  );
};

export default MyBehavioralProfilePage;
