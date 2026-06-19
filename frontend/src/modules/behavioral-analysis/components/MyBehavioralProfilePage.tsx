import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Paper, Grid, Card, CardContent, Chip, LinearProgress,
  Alert, Button, Dialog, DialogTitle, DialogContent, DialogActions,
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import {
  GET_BEHAVIORAL_PROFILES, GET_BEHAVIORAL_RECOMMENDATIONS, GET_BEHAVIORAL_ANOMALIES,
  GET_PERSONALITY_PROFILES, GET_PERSONALITY_TEMPLATES, GET_PERSONALITY_QUESTIONS,
  GET_MANAGER_EFFECTIVENESS, GET_PERSONALITY_TEST_ASSIGNMENTS,
} from '../api/queries';
import { SUBMIT_PERSONALITY_TEST, SUBMIT_PULSE_SURVEY, COMPUTE_MANAGER_EFFECTIVENESS } from '../api/mutations';
import { BehavioralProfile, BehavioralRecommendation, BehavioralAnomaly, BehavioralPersonalityProfile, PersonalityTestAssignment, PersonalityTestTemplate } from '../types';
import CoachingTips from './coaching/CoachingTips';
import DisputeForm from './coaching/DisputeForm';
import PersonalityTestForm from './PersonalityTestForm';
import PersonalityRadarChart from './PersonalityRadarChart';
import PulseSurveyForm from './PulseSurveyForm';
import ManagerEffectivenessCard from './ManagerEffectivenessCard';
import PsychologyIcon from '@mui/icons-material/Psychology';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import AssignmentIcon from '@mui/icons-material/Assignment';
import FeedbackIcon from '@mui/icons-material/Feedback';

const GET_ME = gql`
  query GetMe {
    me {
      id
      role { name }
    }
  }
`;

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
  const [testFormOpen, setTestFormOpen] = useState(false);
  const [pulseSurveyOpen, setPulseSurveyOpen] = useState(false);
  const [postponeDialog, setPostponeDialog] = useState<'idle' | 'open' | 'dismissed'>('idle');

  const { data: meData } = useQuery(GET_ME);

  const currentUserId: number | undefined = (meData as any)?.me?.id;
  const userRole: string | undefined = (meData as any)?.me?.role?.name;

  const { data: profilesData, loading: profilesLoading } = useQuery(GET_BEHAVIORAL_PROFILES);
  const { data: recsData, loading: recsLoading, refetch: refetchRecs } = useQuery(GET_BEHAVIORAL_RECOMMENDATIONS);
  const { data: anomaliesData, loading: anomaliesLoading } = useQuery(GET_BEHAVIORAL_ANOMALIES);

  const { data: personalityData, refetch: refetchPersonality } = useQuery(GET_PERSONALITY_PROFILES);
  const { data: templatesData } = useQuery(GET_PERSONALITY_TEMPLATES);
  const { data: mgrData, refetch: refetchMgr } = useQuery(GET_MANAGER_EFFECTIVENESS);

  const { data: assignmentsData } = useQuery(GET_PERSONALITY_TEST_ASSIGNMENTS, {
    variables: { userId: currentUserId, status: "pending" },
    skip: !currentUserId,
  });

  const [submitTest, { loading: testSubmitting }] = useMutation(SUBMIT_PERSONALITY_TEST);
  const [submitSurvey, { loading: surveySubmitting }] = useMutation(SUBMIT_PULSE_SURVEY);
  const [computeMgr] = useMutation(COMPUTE_MANAGER_EFFECTIVENESS);

  const profile: BehavioralProfile | undefined = profilesData?.behavioralProfiles?.[0];
  const recommendations: BehavioralRecommendation[] = recsData?.behavioralRecommendations || [];
  const anomalies: BehavioralAnomaly[] = anomaliesData?.behavioralAnomalies || [];

  const personalityProfiles: BehavioralPersonalityProfile[] = personalityData?.personalityProfiles || [];
  const latestPersonality = personalityProfiles[0] || null;

  const templates: PersonalityTestTemplate[] = templatesData?.personalityTemplates || [];
  const pendingAssignments: PersonalityTestAssignment[] = assignmentsData?.personalityTestAssignments || [];
  const activeAssignment = pendingAssignments[0] || null;

  const activeTemplate = activeAssignment
    ? templates.find(t => t.id === activeAssignment.templateId) || templates[0] || null
    : templates[0] || null;

  const { data: questionsData, loading: questionsLoading } = useQuery(GET_PERSONALITY_QUESTIONS, {
    variables: { templateId: activeTemplate?.id },
    skip: !activeTemplate?.id,
  });

  const questions = questionsData?.personalityQuestions || [];
  const managerData = mgrData?.managerEffectiveness?.[0] || null;

  const isManager: boolean = !!(userRole && ['admin', 'super_admin'].includes(userRole));

  useEffect(() => {
    if (activeAssignment && postponeDialog === 'idle') {
      setPostponeDialog('open');
    }
  }, [activeAssignment, postponeDialog]);

  const handleSubmitTest = async (templateId: number, answers: number[]) => {
    await submitTest({ variables: { input: { templateId, answers } } });
    await refetchPersonality();
  };

  const handleSubmitPulse = async (input: any) => {
    await submitSurvey({ variables: { input } });
  };

  const handleComputeMgr = async () => {
    await computeMgr({ variables: { managerId: currentUserId || 0 } });
    await refetchMgr();
  };

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

      {activeAssignment && (
        <Alert
          severity={new Date(activeAssignment.dueBy) < new Date() ? 'error' : 'info'}
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" variant="outlined" onClick={() => setTestFormOpen(true)}>
              Към теста
            </Button>
          }
        >
          {new Date(activeAssignment.dueBy) < new Date()
            ? `Имате просрочен личностен тест! Срокът беше ${new Date(activeAssignment.dueBy).toLocaleDateString('bg-BG')}. Моля, попълнете го.`
            : `Имате назначен личностен тест. Моля, попълнете го до ${new Date(activeAssignment.dueBy).toLocaleDateString('bg-BG')}.`
          }
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

        {/* Personality Profile (IPIP-50) */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Психологически профил (Big Five)
                </Typography>
                {!latestPersonality && activeTemplate && (
                  <Button variant="contained" size="small" startIcon={<AssignmentIcon />} onClick={() => setTestFormOpen(true)}>
                    Попълни теста
                  </Button>
                )}
                {latestPersonality && (
                  <Button variant="outlined" size="small" onClick={() => setTestFormOpen(true)}>
                      Попълни отново
                  </Button>
                )}
              </Box>
              {questionsLoading ? (
                <Typography>Зареждане на въпросите...</Typography>
              ) : latestPersonality ? (
                <PersonalityRadarChart
                  openness={latestPersonality.openness}
                  conscientiousness={latestPersonality.conscientiousness}
                  extraversion={latestPersonality.extraversion}
                  agreeableness={latestPersonality.agreeableness}
                  neuroticism={latestPersonality.neuroticism}
                  interpretation={latestPersonality.interpretation}
                />
              ) : questions.length > 0 ? (
                <Typography color="text.secondary">
                  Попълнете теста, за да видите вашия Big Five профил.
                </Typography>
              ) : (
                <Typography color="text.secondary">
                  Няма активен тестов шаблон. Свържете се с администратор.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Pulse Survey */}
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                <FeedbackIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Как се чувствате?
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Споделете как сте напоследък — това помага за по-точна оценка на рисковете
              </Typography>
            </Box>
            <Button variant="contained" onClick={() => setPulseSurveyOpen(true)}>
              Попълни анкетата
            </Button>
          </Paper>
        </Grid>

        {/* Manager Effectiveness */}
        {isManager && managerData && (
          <Grid size={{ xs: 12 }}>
            <ManagerEffectivenessCard data={managerData} />
          </Grid>
        )}
        {isManager && !managerData && (
          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Ефективност на мениджъра</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Кликнете за да изчислите вашата ефективност като мениджър.
                </Typography>
                <Button variant="contained" onClick={handleComputeMgr}>
                  Изчисли
                </Button>
              </CardContent>
            </Card>
          </Grid>
        )}

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

      <PersonalityTestForm
        open={testFormOpen}
        onClose={() => setTestFormOpen(false)}
        questions={questions}
        templateId={activeTemplate?.id || 0}
        onSubmit={handleSubmitTest}
      />

      <PulseSurveyForm
        open={pulseSurveyOpen}
        onClose={() => setPulseSurveyOpen(false)}
        onSubmit={handleSubmitPulse}
      />

      <Dialog open={postponeDialog === 'open'} maxWidth="sm" fullWidth>
        <DialogTitle>
          {activeAssignment && new Date(activeAssignment.dueBy) < new Date()
            ? 'Просрочен личностен тест'
            : 'Назначен личностен тест'}
        </DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            {activeAssignment && new Date(activeAssignment.dueBy) < new Date()
              ? `Имате просрочен личностен тест. Срокът изтече на ${new Date(activeAssignment.dueBy).toLocaleDateString('bg-BG')}.`
              : `Имате назначен личностен тест${activeAssignment ? ` с шаблон "${activeAssignment.templateName}"` : ''}.`}
          </Typography>
          {activeAssignment && new Date(activeAssignment.dueBy) >= new Date() && (
            <Typography>
              Краен срок: <strong>{new Date(activeAssignment.dueBy).toLocaleDateString('bg-BG')}</strong>
            </Typography>
          )}
          <Typography sx={{ mt: 2 }} color="text.secondary">
            Тестът отнема около 10-15 минути. Можете да го отложите за по-късно.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setPostponeDialog('dismissed'); }} color="inherit">
            Отложи за по-късно
          </Button>
          <Button
            variant="contained"
            onClick={() => { setPostponeDialog('dismissed'); setTestFormOpen(true); }}
          >
            Изпълни сега
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MyBehavioralProfilePage;
