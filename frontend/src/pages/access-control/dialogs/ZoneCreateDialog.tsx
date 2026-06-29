import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, CircularProgress, Box, Chip,
  FormControl, InputLabel, Select, MenuItem,
  FormControlLabel, Switch
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import { CREATE_ACCESS_ZONE } from '../../../graphql/mutations/accessControl';

const ZoneCreateDialog: React.FC<{open: boolean, onClose: () => void, onSuccess: () => void, zones: any[], parentZoneId?: number | null}> = ({ open, onClose, onSuccess, zones, parentZoneId }) => {
    const [createZone] = useMutation(CREATE_ACCESS_ZONE);
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
        parentZoneId: parentZoneId ?? null,
        inheritPermissions: true
    });

    React.useEffect(() => {
        if (open) {
            setFormData((prev) => ({
                ...prev,
                parentZoneId: parentZoneId ?? null,
                inheritPermissions: parentZoneId != null ? true : prev.inheritPermissions
            }));
        }
    }, [open, parentZoneId]);

    const [loading, setLoading] = useState(false);

    const handleCreate = async () => {
        setLoading(true);
        try {
            await createZone({ variables: { input: formData } });
            onSuccess();
            setFormData({ zoneId: '', name: '', level: 1, dependsOn: [], requiredHoursStart: '00:00', requiredHoursEnd: '23:59', antiPassbackEnabled: false, antiPassbackType: 'soft', antiPassbackTimeout: 5, parentZoneId: null, inheritPermissions: true });
        } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Нова Зона</DialogTitle>
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
                        {zones.filter((z: any) => z.zoneId !== formData.zoneId).map((z: any) => (
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
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Отказ</Button>
                <Button variant="contained" onClick={handleCreate} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Създай'}</Button>
            </DialogActions>
        </Dialog>
    );
};

export default ZoneCreateDialog;
