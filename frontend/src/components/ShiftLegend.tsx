import React from 'react';
import { Box, Typography, Chip, Paper } from '@mui/material';
import { getShiftIcon, ShiftTypeLabels, ShiftTypeColors } from '../utils/shiftUtils';
import { formatDate } from '../utils/dateUtils';

const legendItems = [
  'regular',
  'paid_leave',
  'sick_leave',
  'unpaid_leave',
  'day_off'
];

const adminItems = [
    'missing',
    'manual_log',
    'auto_log'
];

interface ShiftLegendProps {
  showAdminItems?: boolean;
  holidays?: Array<{ date: string; localName: string | null; name: string }>;
  monthlyNorm?: { days: number; hours: number } | null;
}

const ShiftLegend: React.FC<ShiftLegendProps> = ({ showAdminItems = false, holidays = [], monthlyNorm }) => {
  // Sort holidays by date
  const sortedHolidays = [...(holidays || [])].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return (
    <Paper elevation={1} sx={{ mt: 2, p: 2, borderRadius: 2, bgcolor: 'background.paper' }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        
        {/* Monthly Norm Section */}
        {monthlyNorm && (
            <Box sx={{ p: 1.5, bgcolor: '#e3f2fd', border: '1px solid #90caf9', borderRadius: 1 }}>
                <Typography variant="subtitle2" color="#1565c0" gutterBottom fontWeight="bold">Норматив за месеца</Typography>
                <Typography variant="body2" color="text.primary">
                    Работни дни: <strong>{monthlyNorm.days}</strong> &nbsp;|&nbsp; Часове: <strong>{monthlyNorm.hours}</strong> (при 8-часов ден)
                </Typography>
            </Box>
        )}

        {/* Shifts Section */}
        <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>Видове смени и отпуски</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {legendItems.map((type) => (
                <Chip
                key={type}
                size="small"
                label={ShiftTypeLabels[type]}
                icon={getShiftIcon(type, { style: { color: 'white' } })}
                sx={{ 
                    bgcolor: ShiftTypeColors[type], 
                    color: 'white',
                    '& .MuiChip-icon': { color: 'white' },
                    fontWeight: 'medium'
                }}
                />
            ))}
            </Box>
        </Box>

        {/* Admin Section (Optional) */}
        {showAdminItems && (
             <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>Системни статуси</Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {adminItems.map((type) => (
                    <Chip
                    key={type}
                    size="small"
                    label={ShiftTypeLabels[type]}
                    icon={getShiftIcon(type, { style: { color: 'white' } })}
                    sx={{ 
                        bgcolor: ShiftTypeColors[type], 
                        color: 'white',
                        '& .MuiChip-icon': { color: 'white' },
                        fontWeight: 'medium'
                    }}
                    />
                ))}
                </Box>
            </Box>
        )}

        {/* Public Holidays Section */}
        <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>Празници този месец</Typography>
            {sortedHolidays.length > 0 ? (
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {sortedHolidays.map((h) => (
                        <Chip
                            key={h.date}
                            size="small"
                            label={`${formatDate(h.date)}: ${h.localName || h.name}`}
                            icon={getShiftIcon('public_holiday', { style: { color: '#b71c1c' } })}
                            sx={{ 
                                bgcolor: '#ffebee', 
                                color: '#b71c1c',
                                border: '1px solid #ffcdd2',
                                fontWeight: 'medium'
                            }}
                        />
                    ))}
                </Box>
            ) : (
                 <Typography variant="caption" color="text.secondary">Няма празници за този месец.</Typography>
            )}
        </Box>

      </Box>
    </Paper>
  );
};

export default ShiftLegend;
