import React from 'react';
import { Card, CardContent, Typography, Box, Chip, LinearProgress, Grid } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import type { ManagerEffectiveness } from '../types';

interface Props {
  data: ManagerEffectiveness;
}

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'improving':
      return <TrendingUpIcon color="success" fontSize="small" />;
    case 'declining':
      return <TrendingDownIcon color="error" fontSize="small" />;
    default:
      return <TrendingFlatIcon color="action" fontSize="small" />;
  }
};

const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 70) return 'success';
  if (score >= 50) return 'warning';
  return 'error';
};

const MetricRow: React.FC<{ label: string; value: number; max?: number; inverse?: boolean }> = ({
  label, value, max = 100, inverse = false,
}) => {
  const pct = max > 1 ? (value / max) * 100 : value * 100;
  let color: 'success' | 'warning' | 'error' = 'success';
  if (inverse) {
    if (pct > 70) color = 'error';
    else if (pct > 40) color = 'warning';
  } else {
    if (pct < 40) color = 'error';
    else if (pct < 70) color = 'warning';
  }
  const barColor = color === 'success' ? '#388e3c' : color === 'warning' ? '#fbc02d' : '#d32f2f';
  return (
    <Box sx={{ mb: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.25 }}>
        <Typography variant="caption">{label}</Typography>
        <Typography variant="caption" fontWeight="bold">{value.toFixed(1)}</Typography>
      </Box>
      <LinearProgress variant="determinate" value={Math.min(pct, 100)} sx={{ height: 6, borderRadius: 1, bgcolor: '#e0e0e0', '& .MuiLinearProgress-bar': { bgcolor: barColor } }} />
    </Box>
  );
};

const ManagerEffectivenessCard: React.FC<Props> = ({ data }) => {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Typography variant="h6">Ефективност на мениджъра</Typography>
          <Chip
            label={`${data.managerEffectivenessScore.toFixed(0)}/100`}
            color={getScoreColor(data.managerEffectivenessScore)}
            size="small"
          />
          {getTrendIcon(data.trendDirection)}
        </Box>

        <Grid container spacing={2}>
          <Grid size={{ xs: 6 }}>
            <MetricRow label="Присъствие на екипа" value={data.teamAvgAttendance} />
            <MetricRow label="Ангажираност" value={data.teamAvgEngagement} />
            <MetricRow label="Риск прегаряне" value={data.teamAvgBurnout} max={1} inverse />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <MetricRow label="Текучество" value={data.teamTurnoverRate * 100} />
            <MetricRow label="Брой аномалии" value={data.teamAnomalyCount} max={data.teamSize} />
            <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
              Екип: {data.teamSize} души
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default ManagerEffectivenessCard;
