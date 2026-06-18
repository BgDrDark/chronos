import React from 'react';
import { Container, Typography, Box, Paper, Grid, Card, CardContent, Chip, Tooltip } from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { GET_ORGANIZATIONAL_HEALTH } from '../api/queries';
import { COMPUTE_ORGANIZATIONAL_HEALTH } from '../api/mutations';
import { OrganizationalHealth } from '../types';
import { useError } from '../../../context/ErrorContext';

const getBurnoutColor = (risk: number) => {
  if (risk >= 0.8) return '#d32f2f';
  if (risk >= 0.6) return '#f57c00';
  if (risk >= 0.4) return '#fbc02d';
  return '#388e3c';
};

const getEngagementColor = (score: number) => {
  if (score >= 80) return '#388e3c';
  if (score >= 60) return '#fbc02d';
  if (score >= 40) return '#f57c00';
  return '#d32f2f';
};

const OrganizationalHealthPage: React.FC = () => {
  const { data, loading, refetch } = useQuery(GET_ORGANIZATIONAL_HEALTH);
  const [computeHealth] = useMutation(COMPUTE_ORGANIZATIONAL_HEALTH);
  const { showSuccess, showError } = useError();

  const healthData: OrganizationalHealth[] = data?.organizationalHealth || [];

  const handleCompute = async () => {
    try {
      await computeHealth();
      showSuccess('Здравословният статус е преизчислен');
      refetch();
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Грешка при преизчисляване');
    }
  };

  if (loading) return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Организационно здраве</Typography>
        <Chip label="Heatmap View" color="primary" />
      </Box>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Карта на рисковете по отдели
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Червено: Висок риск | Оранжево: Среден риск | Жълто: Нисък риск | Зелено: Стабилно
        </Typography>

        <Grid container spacing={2}>
          {healthData.map(dept => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={dept.departmentId}>
              <Card sx={{ border: '1px solid #e0e0e0' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>{dept.departmentName}</Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">Burnout Risk</Typography>
                      <Typography variant="body2">{(dept.avgBurnoutRisk * 100).toFixed(0)}%</Typography>
                    </Box>
                    <Box sx={{ height: 8, bgcolor: '#e0e0e0', borderRadius: 1 }}>
                      <Box sx={{ height: '100%', bgcolor: getBurnoutColor(dept.avgBurnoutRisk), borderRadius: 1, width: `${dept.avgBurnoutRisk * 100}%` }} />
                    </Box>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">Attendance</Typography>
                      <Typography variant="body2">{dept.avgAttendance.toFixed(0)}</Typography>
                    </Box>
                    <Box sx={{ height: 8, bgcolor: '#e0e0e0', borderRadius: 1 }}>
                      <Box sx={{ height: '100%', bgcolor: getEngagementColor(dept.avgAttendance), borderRadius: 1, width: `${dept.avgAttendance}%` }} />
                    </Box>
                  </Box>

                  <Grid container spacing={1} sx={{ mt: 1 }}>
                    <Grid size={6}>
                      <Tooltip title="Средна ефективност">
                        <Chip label={`Eff: ${dept.avgEfficiency.toFixed(0)}`} size="small" sx={{ width: '100%' }} />
                      </Tooltip>
                    </Grid>
                    <Grid size={6}>
                      <Tooltip title="Средна точност">
                        <Chip label={`Punc: ${dept.avgPunctuality.toFixed(0)}`} size="small" sx={{ width: '100%' }} />
                      </Tooltip>
                    </Grid>
                  </Grid>

                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Chip 
                      label={dept.isSystemicIssue ? 'Системен проблем' : 'Стабилен'} 
                      color={dept.isSystemicIssue ? 'error' : 'success'} 
                      size="small" 
                    />
                    <Typography variant="caption" color="text.secondary">{dept.employeeCount} служители</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {healthData.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="text.secondary">Няма налични данни. Генерирайте справка.</Typography>
          </Box>
        )}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <button 
          onClick={handleCompute}
          style={{ padding: '10px 20px', background: '#1976d2', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        >
          Преизчисли организационно здраве
        </button>
      </Box>
    </Container>
  );
};

export default OrganizationalHealthPage;
