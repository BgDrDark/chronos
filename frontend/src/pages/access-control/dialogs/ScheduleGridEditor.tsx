import React from 'react';
import {
  Box, Typography, IconButton, Chip, TextField,
  FormControl, Select, MenuItem, Paper, Stack
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import type { DayEntry } from './ScheduleTimeGrid';

const DAY_LABELS: Record<number, string> = {
  1: 'Понеделник', 2: 'Вторник', 3: 'Сряда', 4: 'Четвъртък',
  5: 'Петък', 6: 'Събота', 7: 'Неделя',
};

interface Props {
  entries: DayEntry[];
  onChange: (entries: DayEntry[]) => void;
}

const ScheduleGridEditor: React.FC<Props> = ({ entries, onChange }) => {
  const addEntry = (day: number) => {
    onChange([...entries, { day_of_week: day, start: '08:00', end: '17:00', holiday: 'deny' }]);
  };

  const removeEntry = (idx: number) => {
    const e = [...entries];
    e.splice(idx, 1);
    onChange(e);
  };

  const updateEntry = (idx: number, patch: Partial<DayEntry>) => {
    const e = [...entries];
    e[idx] = { ...e[idx], ...patch };
    onChange(e);
  };

  const groupedEntries: Record<number, { idx: number; entry: DayEntry }[]> = {};
  for (let d = 1; d <= 7; d++) groupedEntries[d] = [];
  entries.forEach((entry, idx) => {
    if (!groupedEntries[entry.day_of_week]) groupedEntries[entry.day_of_week] = [];
    groupedEntries[entry.day_of_week].push({ idx, entry });
  });

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        Седмичен график
      </Typography>
      <Stack spacing={1.5}>
        {[1, 2, 3, 4, 5, 6, 7].map((day) => {
          const dayEntries = groupedEntries[day] || [];
          return (
            <Box key={day}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 110, fontWeight: 500 }}>
                  {DAY_LABELS[day]}
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, flex: 1 }}>
                  {dayEntries.length === 0 && (
                    <Typography variant="caption" color="text.secondary">—</Typography>
                  )}
                  {dayEntries.map(({ idx, entry }) => (
                    <Chip
                      key={idx}
                      size="small"
                      label={`${entry.start}-${entry.end}`}
                      onDelete={() => removeEntry(idx)}
                      color={entry.holiday === 'deny' ? 'default' : entry.holiday === 'allow' ? 'success' : 'info'}
                      variant="outlined"
                    />
                  ))}
                </Box>
                <IconButton size="small" onClick={() => addEntry(day)} title="Добави часови диапазон">
                  <AddIcon fontSize="small" />
                </IconButton>
              </Box>
              {dayEntries.map(({ idx, entry }) => (
                <Box key={idx} sx={{ display: 'flex', gap: 1, ml: 13, mt: 0.5, alignItems: 'center' }}>
                  <TextField
                    size="small" type="time" value={entry.start}
                    onChange={(e) => updateEntry(idx, { start: e.target.value })}
                    sx={{ width: 100 }} InputLabelProps={{ shrink: true }}
                  />
                  <Typography variant="caption">до</Typography>
                  <TextField
                    size="small" type="time" value={entry.end}
                    onChange={(e) => updateEntry(idx, { end: e.target.value })}
                    sx={{ width: 100 }} InputLabelProps={{ shrink: true }}
                  />
                  <FormControl size="small" sx={{ minWidth: 110 }}>
                    <Select
                      value={entry.holiday || 'deny'}
                      onChange={(e) => updateEntry(idx, { holiday: e.target.value as DayEntry['holiday'] })}
                    >
                        <MenuItem value="deny">Няма достъп на празник</MenuItem>
                          <MenuItem value="allow">Свободен достъп на празник</MenuItem>
                          <MenuItem value="ignore">Следва нормалния график на празник</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              ))}
            </Box>
          );
        })}
      </Stack>
    </Paper>
  );
};

export default ScheduleGridEditor;
