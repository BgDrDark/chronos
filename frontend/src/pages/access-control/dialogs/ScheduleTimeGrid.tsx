import React from 'react';
import {
  Box, Typography, Divider, Switch, FormControlLabel,
  FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import ScheduleGridEditor from './ScheduleGridEditor';
import ScheduleOverrideEditor from './ScheduleOverrideEditor';

export interface TimeEntry {
  start: string;
  end: string;
  holiday?: 'deny' | 'allow' | 'ignore';
}

export interface OverrideEntry {
  date_from: string;
  date_to: string;
  behavior?: 'deny' | 'allow';
  entries?: Array<{ start: string; end: string }>;
}

export interface DayEntry {
  day_of_week: number;
  start: string;
  end: string;
  holiday?: 'deny' | 'allow' | 'ignore';
}

export interface ScheduleConfig {
  entries: DayEntry[];
  overrides?: OverrideEntry[];
  sync_with_work_schedule?: boolean;
  out_of_hours_behavior?: 'deny' | 'allow_with_log';
}

interface Props {
  config: ScheduleConfig;
  onChange: (config: ScheduleConfig) => void;
}

const ScheduleTimeGrid: React.FC<Props> = ({ config, onChange }) => {
  const update = (patch: Partial<ScheduleConfig>) => {
    onChange({ ...config, ...patch });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <ScheduleGridEditor
        entries={config.entries}
        onChange={(entries) => update({ entries })}
      />

      <Divider />

      <ScheduleOverrideEditor
        overrides={config.overrides || []}
        onChange={(overrides) => update({ overrides })}
      />

      <Divider />

      <Box>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>Настройки</Typography>
        <FormControlLabel
          control={
            <Switch
              checked={config.sync_with_work_schedule ?? false}
              onChange={(e) => update({ sync_with_work_schedule: e.target.checked })}
            />
          }
          label="Синхронизирай с работно време (WorkSchedule)"
        />
        <Box sx={{ mt: 1 }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Извънработно време</InputLabel>
            <Select
              value={config.out_of_hours_behavior || 'deny'}
              label="Извънработно време"
              onChange={(e) => update({ out_of_hours_behavior: e.target.value as ScheduleConfig['out_of_hours_behavior'] })}
            >
              <MenuItem value="deny">Откажи достъп</MenuItem>
              <MenuItem value="allow_with_log">Разреши с логване</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>
    </Box>
  );
};

export default ScheduleTimeGrid;
