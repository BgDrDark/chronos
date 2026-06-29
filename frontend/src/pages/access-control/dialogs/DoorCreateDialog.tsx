import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import { CREATE_ACCESS_DOOR } from '../../../graphql/mutations/accessControl';

const DoorCreateDialog: React.FC<{open: boolean, onClose: () => void, onSuccess: () => void, gateways: any[], zones: any[]}> = ({ open, onClose, onSuccess, gateways, zones }) => {
    const [createDoor] = useMutation(CREATE_ACCESS_DOOR);
    const [formData, setFormData] = useState({ doorId: '', name: '', zoneDbId: 0, gatewayId: 0, deviceId: '', relayNumber: 1 });
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Нова Врата</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="Код на врата" fullWidth value={formData.doorId} onChange={(e) => setFormData({...formData, doorId: e.target.value})} helperText="Уникален идентификатор, напр. door_1" />
                <TextField label="Име" fullWidth value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} helperText="Човекоподобно име, напр. Вход А" />
                <FormControl fullWidth>
                    <InputLabel>Зона</InputLabel>
                    <Select value={formData.zoneDbId} label="Зона" onChange={(e) => setFormData({...formData, zoneDbId: e.target.value as number})}>
                        {zones.map((z: any) => <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>)}
                    </Select>
                </FormControl>
                <FormControl fullWidth>
                    <InputLabel>Gateway</InputLabel>
                    <Select value={formData.gatewayId} label="Gateway" onChange={(e) => setFormData({...formData, gatewayId: e.target.value as number})}>
                        {gateways.map((g: any) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
                    </Select>
                </FormControl>
                <TextField label="Име на контролера" fullWidth value={formData.deviceId} onChange={(e) => setFormData({...formData, deviceId: e.target.value})} helperText="Текстов идентификатор на контролера" />
                <TextField label="Номер на реле" fullWidth type="number" value={formData.relayNumber} onChange={(e) => setFormData({...formData, relayNumber: parseInt(e.target.value) || 1})} helperText="Номер на релето за управлението на вратата" />
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Отказ</Button>
                <Button variant="contained" onClick={async () => {
                    await createDoor({ variables: { input: formData } });
                    onSuccess();
                }}>Създай</Button>
            </DialogActions>
        </Dialog>
    );
};

export default DoorCreateDialog;
