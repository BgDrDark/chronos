import React from 'react';
import { Container, Typography, Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Alert } from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { GET_BIAS_REPORTS } from '../api/queries';
import { COMPUTE_BIAS_REPORT } from '../api/mutations';
import { BiasReport } from '../types';
import { useError } from '../../../context/ErrorContext';

const BiasMonitorPage: React.FC = () => {
  const { data, loading, refetch } = useQuery(GET_BIAS_REPORTS);
  const [computeBias] = useMutation(COMPUTE_BIAS_REPORT);
  const { showSuccess, showError } = useError();

  const reports: BiasReport[] = data?.biasReports || [];
  const latestReport = reports.length > 0 ? reports[0] : null;

  const handleCompute = async () => {
    try {
      await computeBias();
      showSuccess('Bias анализът е генериран');
      refetch();
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Грешка при генериране');
    }
  };

  if (loading) return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Bias Monitor
      </Typography>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Последна справка за предразсъдъци
        </Typography>
        
        {latestReport ? (
          <>
            <Alert severity={latestReport.overallBiasDetected ? 'warning' : 'success'} sx={{ mb: 3 }}>
              {latestReport.overallBiasDetected 
                ? 'Открити са статистически значими разлики между групи.' 
                : 'Няма открити значими предразсъдъци в текущия период.'}
            </Alert>

            {latestReport.findings.length > 0 && (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Метрика</TableCell>
                      <TableCell>Група А</TableCell>
                      <TableCell>Средно А</TableCell>
                      <TableCell>Група Б</TableCell>
                      <TableCell>Средно Б</TableCell>
                      <TableCell>Разлика</TableCell>
                      <TableCell>Препоръка</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {latestReport.findings.map((finding: any, idx: number) => (
                      <TableRow key={idx}>
                        <TableCell>{finding.metric}</TableCell>
                        <TableCell><Chip label={finding.group_a} size="small" /></TableCell>
                        <TableCell>{finding.group_a_avg?.toFixed(2)}</TableCell>
                        <TableCell><Chip label={finding.group_b} size="small" /></TableCell>
                        <TableCell>{finding.group_b_avg?.toFixed(2)}</TableCell>
                        <TableCell>
                          <Chip 
                            label={finding.difference?.toFixed(2)} 
                            color={finding.difference > 0.3 ? 'error' : 'warning'} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell>{finding.recommendation}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </>
        ) : (
          <Typography color="text.secondary">Няма генерирани справки.</Typography>
        )}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <button 
          onClick={handleCompute}
          style={{ padding: '10px 20px', background: '#1976d2', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        >
          Генерирай Bias анализ
        </button>
      </Box>
    </Container>
  );
};

export default BiasMonitorPage;
