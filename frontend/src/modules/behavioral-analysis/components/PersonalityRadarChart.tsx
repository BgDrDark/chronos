import React from 'react';
import { Box, Typography } from '@mui/material';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

interface Props {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  interpretation?: string | null;
}

const PersonalityRadarChart: React.FC<Props> = ({
  openness, conscientiousness, extraversion, agreeableness, neuroticism, interpretation,
}) => {
  const data = [
    { factor: 'Отвореност', value: openness, fullMark: 10 },
    { factor: 'Съзнателност', value: conscientiousness, fullMark: 10 },
    { factor: 'Екстраверсия', value: extraversion, fullMark: 10 },
    { factor: 'Дружелюбност', value: agreeableness, fullMark: 10 },
    { factor: 'Невротизъм', value: neuroticism, fullMark: 10 },
  ];

  const interpretationLines = interpretation?.split('\n').filter(Boolean) || [];

  return (
    <Box>
      <ResponsiveContainer width="100%" height={350}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="factor" fontSize={12} />
          <PolarRadiusAxis domain={[0, 10]} tickCount={6} fontSize={10} />
          <Tooltip />
          <Legend />
          <Radar
            name="Стен (1-10)"
            dataKey="value"
            stroke="#1976d2"
            fill="#1976d2"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
      {interpretationLines.length > 0 && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom fontWeight="bold">
            Тълкуване
          </Typography>
          {interpretationLines.map((line, i) => (
            <Typography key={i} variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
              {line}
            </Typography>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default PersonalityRadarChart;
