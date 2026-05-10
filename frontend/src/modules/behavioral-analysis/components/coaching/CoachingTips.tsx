import React from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemIcon, ListItemText, Chip, Divider } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import FollowTheSignsIcon from '@mui/icons-material/FollowTheSigns';
import PsychologyIcon from '@mui/icons-material/Psychology';

interface CoachingTipsData {
  approach?: string;
  talking_points?: string[];
  avoid?: string[];
  follow_up?: string;
}

interface CoachingTipsProps {
  tips: CoachingTipsData;
  recommendationType: string;
}

const getApproachColor = (approach: string): 'success' | 'warning' | 'info' | 'default' => {
  switch (approach) {
    case 'supportive':
      return 'success';
    case 'curious':
      return 'info';
    case 'discreet':
      return 'warning';
    default:
      return 'default';
  }
};

const CoachingTips: React.FC<CoachingTipsProps> = ({ tips, recommendationType }) => {
  if (!tips || (!tips.talking_points && !tips.avoid && !tips.follow_up)) {
    return null;
  }

  return (
    <Paper sx={{ p: 3, mt: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <PsychologyIcon color="primary" />
        <Typography variant="h6">Съвети за разговора</Typography>
        {tips.approach && (
          <Chip
            label={tips.approach}
            color={getApproachColor(tips.approach)}
            size="small"
            sx={{ ml: 1 }}
          />
        )}
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Тип препоръка: {recommendationType}
      </Typography>

      {tips.talking_points && tips.talking_points.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="success.main" gutterBottom>
            Използвай тези фрази:
          </Typography>
          <List dense>
            {tips.talking_points.map((point, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <ThumbUpIcon color="success" fontSize="small" />
                </ListItemIcon>
                <ListItemText primary={point} />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      <Divider sx={{ my: 2 }} />

      {tips.avoid && tips.avoid.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="error.main" gutterBottom>
            Избягвай тези фрази:
          </Typography>
          <List dense>
            {tips.avoid.map((phrase, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <ThumbDownIcon color="error" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={phrase}
                  primaryTypographyProps={{
                    sx: { textDecoration: 'line-through', color: 'text.disabled' },
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      <Divider sx={{ my: 2 }} />

      {tips.follow_up && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FollowTheSignsIcon color="info" fontSize="small" />
          <Typography variant="body2">
            <strong>Последващи действия:</strong> {tips.follow_up}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default CoachingTips;
