import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, CircularProgress, Box, Chip,
  FormControl, InputLabel, Select, MenuItem,
  FormControlLabel, Switch, Typography, Divider
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import { UPDATE_ACCESS_ZONE } from '../../../graphql/mutations/accessControl';

const ZoneEditDialog: React.FC<{
    open: boolean,
    onClose: () => void,
    onSuccess: () => void,
    zones: any[],
    zone: any
}> = ({ open, onClose, onSuccess, zones, zone }) => {
    const [updateZone] = useMutation(UPDATE_ACCESS_ZONE);
    const [formData, setFormData] = useState({
        zoneId: '',
        name: '',
        level: 1,
        dependsOn: [] as string[],
        requiredHoursStart: '00:00',
        requiredHoursEnd: '23:59',
        antiPassbackEnabled: false,
        antiPassbackType: 'soft',
        antiPassbackTimeout: 5,
        description: '',
        parentZoneId: null as number | null,
        inheritPermissions: true,
        requiredAuthFactors: [] as string[],
        interlockEnabled: false,
        interlockTimeout: 30,
        dualAuthEnabled: false,
        dualAuthTimeout: 30
    });
    const [loading, setLoading] = useState(false);

    const prevZoneKeyRef = React.useRef<string>('');

    React.useEffect(() => {
        const key = zone ? `${zone.id}-${open}` : '';
        if (!key || prevZoneKeyRef.current === key) return;
        prevZoneKeyRef.current = key;
        setTimeout(() => {
            setFormData({
                zoneId: zone.zoneId || '',
                name: zone.name || '',
                level: zone.level || 1,
                dependsOn: zone.dependsOn || [],
                requiredHoursStart: zone.requiredHoursStart || '00:00',
                requiredHoursEnd: zone.requiredHours_end || '23:59',
                antiPassbackEnabled: zone.antiPassbackEnabled || false,
                antiPassbackType: zone.antiPassbackType || 'soft',
                antiPassbackTimeout: zone.antiPassbackTimeout || 5,
                description: zone.description || '',
                parentZoneId: zone.parentZoneId ?? null,
                inheritPermissions: zone.inheritPermissions ?? true,
                requiredAuthFactors: zone.requiredAuthFactors || [],
                interlockEnabled: zone.interlockEnabled || false,
                interlockTimeout: zone.interlockTimeout || 30,
                dualAuthEnabled: zone.dualAuthEnabled || false,
                dualAuthTimeout: zone.dualAuthTimeout || 30
            });
        }, 0);
    }, [zone, open]);

    const handleSave = async () => {
        setLoading(true);
        try {
            await updateZone({
                variables: {
                    id: parseInt(zone.id),
                    input: formData
                }
            });
            onSuccess();
        } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Редактиране на Зона</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="ID" fullWidth value={formData.zoneId} onChange={(e) => setFormData({...formData, zoneId: e.target.value})} />
                <TextField label="Име" fullWidth value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
                <FormControl fullWidth>
                    <InputLabel>Ниво</InputLabel>
                    <Select value={formData.level} label="Ниво" onChange={(e) => setFormData({...formData, level: e.target.value as number})}>
                        <MenuItem value={1}>Ниво 1</MenuItem>
                        <MenuItem value={2}>Ниво 2</MenuItem>
                        <MenuItem value={3}>Ниво 3</MenuItem>
                    </Select>
                </FormControl>
                <FormControl fullWidth>
                    <InputLabel>Родителска зона</InputLabel>
                    <Select value={formData.parentZoneId ?? ''} label="Родителска зона" onChange={(e) => setFormData({...formData, parentZoneId: e.target.value ? Number(e.target.value) : null})}>
                        <MenuItem value=""><em>Няма (коренова зона)</em></MenuItem>
                        {zones.filter((z: any) => String(z.id) !== String(zone?.id) && z.zoneId !== formData.zoneId).map((z: any) => (
                            <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
                <FormControlLabel
                    control={<Switch checked={formData.inheritPermissions} onChange={(e) => setFormData({...formData, inheritPermissions: e.target.checked})} />}
                    label="Наследяване на права от родител"
                />
                <FormControl fullWidth>
                    <InputLabel>Зависи от</InputLabel>
                    <Select
                        multiple
                        value={formData.dependsOn}
                        label="Зависи от"
                        onChange={(e) => setFormData({...formData, dependsOn: typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value})}
                        renderValue={(selected) => (
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {selected.map((value) => (
                                    <Chip key={value} label={value} size="small" />
                                ))}
                            </Box>
                        )}
                    >
                        {zones.filter((z: any) => z.zoneId !== formData.zoneId).map((z: any) => (
                            <MenuItem key={z.id} value={z.zoneId}>{z.name}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <TextField label="От" type="time" fullWidth value={formData.requiredHoursStart} onChange={(e) => setFormData({...formData, requiredHoursStart: e.target.value})} InputLabelProps={{ shrink: true }} />
                    <TextField label="До" type="time" fullWidth value={formData.requiredHoursEnd} onChange={(e) => setFormData({...formData, requiredHoursEnd: e.target.value})} InputLabelProps={{ shrink: true }} />
                </Box>
                <TextField label="Описание" fullWidth multiline rows={2} value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} />
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle1" fontWeight="bold">MFA / Сигурност</Typography>
                <FormControl fullWidth>
                    <InputLabel>Изисквани фактори</InputLabel>
                    <Select
                        multiple
                        value={formData.requiredAuthFactors}
                        label="Изисквани фактори"
                        onChange={(e) => setFormData({...formData, requiredAuthFactors: typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value})}
                        renderValue={(selected) => (
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {selected.map((value) => (
                                    <Chip key={value} label={value === 'card' ? 'Карта' : value === 'pin' ? 'ПИН' : value === 'biometric' ? 'Биометрия' : value} size="small" />
                                ))}
                            </Box>
                        )}
                    >
                        <MenuItem value="card">Карта</MenuItem>
                        <MenuItem value="pin">ПИН</MenuItem>
                        <MenuItem value="biometric">Биометрия</MenuItem>
                    </Select>
                </FormControl>
                <FormControlLabel
                    control={<Switch checked={formData.interlockEnabled} onChange={(e) => setFormData({...formData, interlockEnabled: e.target.checked})} />}
                    label="Включи interlock (мантрап)"
                />
                {formData.interlockEnabled && (
                    <TextField label="Interlock таймаут (сек)" type="number" fullWidth value={formData.interlockTimeout} onChange={(e) => setFormData({...formData, interlockTimeout: parseInt(e.target.value) || 30})} />
                )}
                <FormControlLabel
                    control={<Switch checked={formData.dualAuthEnabled} onChange={(e) => setFormData({...formData, dualAuthEnabled: e.target.checked})} />}
                    label="Включи dual-auth (мантрап)"
                />
                {formData.dualAuthEnabled && (
                    <TextField label="Dual-auth таймаут (сек)" type="number" fullWidth value={formData.dualAuthTimeout} onChange={(e) => setFormData({...formData, dualAuthTimeout: parseInt(e.target.value) || 30})} />
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Отказ</Button>
                <Button variant="contained" onClick={handleSave} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Запази'}</Button>
            </DialogActions>
        </Dialog>
    );
};

export default ZoneEditDialog;
