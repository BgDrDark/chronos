import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, CircularProgress, Switch, FormControlLabel,
  Box, FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage, AccessSchedule } from '../../../types';
import {
  CREATE_ACCESS_SCHEDULE,
  UPDATE_ACCESS_SCHEDULE,
} from '../../../graphql/mutations/accessPolicy';
import ScheduleTimeGrid, { type ScheduleConfig } from './ScheduleTimeGrid';

const AccessScheduleDialog: React.FC<{
    open: boolean,
    onClose: () => void,
    onSuccess: () => void,
    schedule?: AccessSchedule | null,
    companyId?: number,
}> = ({ open, onClose, onSuccess, schedule, companyId }) => {
    const [createSchedule] = useMutation(CREATE_ACCESS_SCHEDULE);
    const [updateSchedule] = useMutation(UPDATE_ACCESS_SCHEDULE);
    const [name, setName] = useState('');
    const [timezone, setTimezone] = useState('Europe/Sofia');
    const [config, setConfig] = useState<ScheduleConfig>({ entries: [], overrides: [], sync_with_work_schedule: false, out_of_hours_behavior: 'deny' });
    const [holidayOverrideAuto, setHolidayOverrideAuto] = useState(true);
    const [isActive, setIsActive] = useState(true);
    const [loading, setLoading] = useState(false);

    const prevKeyRef = React.useRef<string>('');

    const parseConfig = (raw: unknown): ScheduleConfig => {
      if (!raw || typeof raw !== 'object') return { entries: [], overrides: [], sync_with_work_schedule: false, out_of_hours_behavior: 'deny' };
      const c = raw as Record<string, unknown>;
      return {
        entries: Array.isArray(c.entries) ? c.entries as ScheduleConfig['entries'] : [],
        overrides: Array.isArray(c.overrides) ? c.overrides as NonNullable<ScheduleConfig['overrides']> : [],
        sync_with_work_schedule: !!c.sync_with_work_schedule,
        out_of_hours_behavior: (c.out_of_hours_behavior as ScheduleConfig['out_of_hours_behavior']) || 'deny',
      };
    };

    React.useEffect(() => {
        const key = schedule ? `${schedule.id}-${open}` : `new-${open}`;
        if (!key || prevKeyRef.current === key) return;
        prevKeyRef.current = key;
        setTimeout(() => {
            setName(schedule?.name || '');
            setTimezone(schedule?.timezone || 'Europe/Sofia');
            setConfig(schedule?.config ? parseConfig(schedule.config) : { entries: [], overrides: [], sync_with_work_schedule: false, out_of_hours_behavior: 'deny' });
            // config parsed inline above
            setHolidayOverrideAuto(schedule?.holidayOverrideAuto ?? true);
            setIsActive(schedule?.isActive ?? true);
        }, 0);
    }, [schedule, open]);

    const buildConfig = (): Record<string, unknown> => {
      return {
        entries: config.entries,
        overrides: config.overrides?.length ? config.overrides : undefined,
        sync_with_work_schedule: config.sync_with_work_schedule || undefined,
        out_of_hours_behavior: config.out_of_hours_behavior === 'deny' ? undefined : config.out_of_hours_behavior,
      };
    };

    const handleSave = async () => {
        if (!name.trim()) { alert('Името е задължително'); return; }
        const finalConfig = buildConfig();
        setLoading(true);
        try {
            if (schedule) {
                await updateSchedule({ variables: { id: schedule.id, input: { name, timezone, config: finalConfig, holidayOverrideAuto, isActive } } });
            } else {
                await createSchedule({ variables: { input: { name, timezone, config: finalConfig, holidayOverrideAuto, isActive }, companyId } });
            }
            onSuccess();
        } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>{schedule ? 'Редактиране на график' : 'Нов график за достъп'}</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="Име" fullWidth value={name} onChange={(e) => setName(e.target.value)} />
                <FormControl fullWidth>
                    <InputLabel>Часова зона</InputLabel>
                    <Select value={timezone} label="Часова зона" onChange={(e) => setTimezone(e.target.value)}>
                        {TIMEZONES.map((tz) => <MenuItem key={tz} value={tz}>{tz}</MenuItem>)}
                    </Select>
                </FormControl>

                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                    <ScheduleTimeGrid config={config} onChange={setConfig} />
                </Box>

                <FormControlLabel control={<Switch checked={holidayOverrideAuto} onChange={(e) => setHolidayOverrideAuto(e.target.checked)} />} label="Автоматична отмяна за празници" />
                <FormControlLabel control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />} label="Активен" />
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Отказ</Button>
                <Button variant="contained" onClick={handleSave} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Запази'}</Button>
            </DialogActions>
        </Dialog>
    );
};

const TIMEZONES = [
  'Europe/Sofia', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
  'Europe/Moscow', 'Europe/Istanbul', 'Europe/Athens', 'Europe/Bucharest',
  'Europe/Belgrade', 'Europe/Warsaw', 'Europe/Prague', 'Europe/Vienna',
  'Europe/Budapest', 'Europe/Zurich', 'Europe/Rome', 'Europe/Madrid',
  'Europe/Lisbon', 'Europe/Amsterdam', 'Europe/Brussels', 'Europe/Stockholm',
  'Europe/Oslo', 'Europe/Copenhagen', 'Europe/Dublin', 'Europe/Helsinki',
  'Europe/Riga', 'Europe/Vilnius', 'Europe/Tallinn', 'Europe/Kyiv',
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'America/Toronto', 'America/Vancouver', 'America/Sao_Paulo', 'America/Mexico_City',
  'Asia/Dubai', 'Asia/Shanghai', 'Asia/Tokyo', 'Asia/Singapore',
  'Asia/Hong_Kong', 'Asia/Seoul', 'Asia/Taipei', 'Asia/Bangkok',
  'Asia/Kolkata', 'Asia/Karachi', 'Asia/Jakarta', 'Asia/Kuala_Lumpur',
  'Australia/Sydney', 'Australia/Melbourne', 'Australia/Perth', 'Australia/Brisbane',
  'Pacific/Auckland', 'Pacific/Fiji', 'Pacific/Honolulu',
  'Africa/Cairo', 'Africa/Johannesburg', 'Africa/Casablanca', 'Africa/Lagos',
  'Africa/Nairobi', 'Indian/Maldives',
];

export default AccessScheduleDialog;
