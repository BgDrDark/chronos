import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Typography, Box, Paper, Grid, Card, CardContent, Chip, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Alert } from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { GET_BEHAVIORAL_PROFILES, GET_BEHAVIORAL_RECOMMENDATIONS } from '../api/queries';
import { UPDATE_RECOMMENDATION_STATUS } from '../api/mutations';
import { BehavioralProfile, BehavioralRecommendation } from '../types';
import { useError } from '../../../context/ErrorContext';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import WarningIcon from '@mui/icons-material/Warning';

const EmployeeProfilePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showSuccess, showError } = useError();

  const userId = parseInt(id || '0', 10);

  const { data: profilesData, loading: profilesLoading } = useQuery(GET_BEHAVIORAL_PROFILES, {
    variables: { userId },
    skip: !userId,
  });

  const { data: recsData, loading: recsLoading, refetch: refetchRecs } = useQuery(GET_BEHAVIORAL_RECOMMENDATIONS, {
    variables: { userId },
    skip: !userId,
  });

  const [updateStatus] = useMutation(UPDATE_RECOMMENDATION_STATUS);

  const [disputeOpen, setDisputeOpen] = useState(false);
  const [selectedRecId, setSelectedRecId] = useState<number | null>(null);
  const [disputeForm, setDisputeForm] = useState({ reason: '', notes: '' });

  const profile: BehavioralProfile | undefined = profilesData?.behavioralProfiles?.[0];
  const recommendations: BehavioralRecommendation[] = recsData?.behavioralRecommendations || [];

  const handleDispute = async () => {
    if (!selectedRecId) return;
    try {
      await updateStatus({
        variables: {
          recommendationId: selectedRecId,
          status: 'disputed',
          disputeReason: disputeForm.reason,
          disputeNotes: disputeForm.notes,
        },
      });
      showSuccess('Препоръката е обжалвана успешно');
      setDisputeOpen(false);
      setDisputeForm({ reason: '', notes: '' });
      refetchRecs();
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Грешка при обжалване');
    }
  };

  if (profilesLoading || recsLoading) return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;
  if (!profile) return <Box sx={{ p: 3, textAlign: 'center' }}>Няма налични данни за този служител.</Box>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)} sx={{ mb: 2 }}>
        Назад
      </Button>

      <Typography variant="h4" gutterBottom>
        Профил на служител (ID: {userId})
      </Typography>

      <Grid container spacing={3}>
        {/* Main Scores */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Основни метрики</Typography>
              <Grid container spacing={2}>
                {[
                  { label: 'Точност', value: profile.punctualityScore, color: profile.punctualityScore > 80 ? 'success' : 'error' },
                  { label: 'Ефективност', value: profile.efficiencyScore, color: profile.efficiencyScore > 70 ? 'success' : 'warning' },
                  { label: 'Ангажираност', value: profile.engagementScore, color: profile.engagementScore > 60 ? 'success' : 'warning' },
                  { label: 'Риск прегаряне', value: profile.burnoutRisk * 100, color: profile.burnoutRisk < 0.4 ? 'success' : 'error' },
                ].map((metric) => (
                  <Grid size={{ xs: 12, sm: 6 }} key={metric.label}>
                    <Box sx={{ mb: 1, display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">{metric.label}</Typography>
                      <Typography variant="body2" fontWeight="bold">{metric.value.toFixed(1)}</Typography>
                    </Box>
                    <Box sx={{ height: 8, bgcolor: '#e0e0e0', borderRadius: 1 }}>
                      <Box sx={{ height: '100%', bgcolor: metric.color === 'success' ? '#388e3c' : metric.color === 'warning' ? '#fbc02d' : '#d32f2f', borderRadius: 1, width: `${Math.min(metric.value, 100)}%` }} />
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* XAI Contribution Factors */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>XAI Фактори</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Какво влияе най-много на резултата?
              </Typography>
              {profile.contributionFactors ? (
                Object.entries(profile.contributionFactors).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</Typography>
                      <Typography variant="caption">{((value as number) * 100).toFixed(0)}%</Typography>
                    </Box>
                    <Box sx={{ height: 4, bgcolor: '#e0e0e0', borderRadius: 1 }}>
                      <Box sx={{ height: '100%', bgcolor: '#1976d2', borderRadius: 1, width: `${(value as number) * 100}%` }} />
                    </Box>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">Няма налични данни.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recommendations & Disputes */}
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Препоръки и Действия</Typography>
            {recommendations.length === 0 ? (
              <Typography color="text.secondary">Няма активни препоръки.</Typography>
            ) : (
              recommendations.map(rec => (
                <Box key={rec.id} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Chip label={rec.priority} color={rec.priority === 'critical' ? 'error' : rec.priority === 'high' ? 'warning' : 'default'} size="small" />
                      <Typography variant="subtitle1">{rec.title}</Typography>
                    </Box>
                    <Typography variant="body2">{rec.explanation}</Typography>
                    {rec.status === 'disputed' && (
                      <Alert severity="info" sx={{ mt: 1 }} icon={<WarningIcon />}>
                        Обжалвана: {rec.disputeReason}
                      </Alert>
                    )}
                  </Box>
                  {rec.status === 'pending' && (
                    <Button 
                      variant="outlined" 
                      color="error" 
                      size="small"
                      onClick={() => { setSelectedRecId(rec.id); setDisputeOpen(true); }}
                    >
                      Обжалвай
                    </Button>
                  )}
                </Box>
              ))
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Dispute Dialog */}
      <Dialog open={disputeOpen} onClose={() => setDisputeOpen(false)}>
        <DialogTitle>Обжалване на препоръка</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Причина"
            margin="dense"
            value={disputeForm.reason}
            onChange={e => setDisputeForm({ ...disputeForm, reason: e.target.value })}
            required
          />
          <TextField
            fullWidth
            label="Допълнителни бележки"
            margin="dense"
            multiline
            rows={3}
            value={disputeForm.notes}
            onChange={e => setDisputeForm({ ...disputeForm, notes: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDisputeOpen(false)}>Отказ</Button>
          <Button onClick={handleDispute} variant="contained" color="error">Потвърди</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default EmployeeProfilePage;
