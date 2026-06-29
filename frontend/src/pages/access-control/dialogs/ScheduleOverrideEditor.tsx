import React from 'react';
import {
  Box, Typography, Button, IconButton, Paper, Stack,
  TextField, FormControl, Select, MenuItem
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import type { OverrideEntry } from './ScheduleTimeGrid';

interface Props {
  overrides: OverrideEntry[];
  onChange: (overrides: OverrideEntry[]) => void;
}

const ScheduleOverrideEditor: React.FC<Props> = ({ overrides, onChange }) => {
  const add = () => {
    onChange([...overrides, { date_from: '', date_to: '', behavior: 'deny' }]);
  };

  const remove = (idx: number) => {
    const o = [...overrides];
    o.splice(idx, 1);
    onChange(o);
  };

  const update = (idx: number, patch: Partial<OverrideEntry>) => {
    const o = [...overrides];
    o[idx] = { ...o[idx], ...patch };
    onChange(o);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle1" fontWeight={600}>Изключения (Date Range)</Typography>
        <Button size="small" startIcon={<AddIcon />} onClick={add}>Добави</Button>
      </Box>
      {overrides.length === 0 && (
        <Typography variant="body2" color="text.secondary">Няма добавени изключения</Typography>
      )}
      <Stack spacing={1}>
        {overrides.map((o, idx) => (
          <Paper key={idx} variant="outlined" sx={{ p: 1.5 }}>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <TextField
                  size="small" type="date" label="От"
                  value={o.date_from}
                  onChange={(e) => update(idx, { date_from: e.target.value })}
                  InputLabelProps={{ shrink: true }} sx={{ width: 160 }}
                />
                <TextField
                  size="small" type="date" label="До"
                  value={o.date_to}
                  onChange={(e) => update(idx, { date_to: e.target.value })}
                  InputLabelProps={{ shrink: true }} sx={{ width: 160 }}
                />
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <Select
                    value={o.behavior || 'deny'}
                    onChange={(e) => update(idx, { behavior: e.target.value as OverrideEntry['behavior'] })}
                  >
                    <MenuItem value="deny">Забрани</MenuItem>
                    <MenuItem value="allow">Разреши</MenuItem>
                  </Select>
                </FormControl>
                <IconButton size="small" color="error" onClick={() => remove(idx)}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Box>
            </Stack>
          </Paper>
        ))}
      </Stack>
    </Box>
  );
};

export default ScheduleOverrideEditor;
