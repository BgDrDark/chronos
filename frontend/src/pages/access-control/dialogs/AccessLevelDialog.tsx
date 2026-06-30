import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, CircularProgress, Switch, FormControlLabel, InputAdornment
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage, AccessLevel } from '../../../types';
import {
  CREATE_ACCESS_LEVEL,
  UPDATE_ACCESS_LEVEL,
} from '../../../graphql/mutations/accessPolicy';
import { InfoIcon } from '../../../components/ui/InfoIcon';
import { accessControlFieldsHelp } from '../../../components/ui/fieldsHelpText';

const AccessLevelDialog: React.FC<{
    open: boolean,
    onClose: () => void,
    onSuccess: () => void,
    level?: AccessLevel | null,
    companyId?: number,
}> = ({ open, onClose, onSuccess, level, companyId }) => {
    const [createLevel] = useMutation(CREATE_ACCESS_LEVEL);
    const [updateLevel] = useMutation(UPDATE_ACCESS_LEVEL);
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [isActive, setIsActive] = useState(true);
    const [loading, setLoading] = useState(false);

    const prevKeyRef = React.useRef<string>('');

    React.useEffect(() => {
        const key = level ? `${level.id}-${open}` : `new-${open}`;
        if (!key || prevKeyRef.current === key) return;
        prevKeyRef.current = key;
        setTimeout(() => {
            setName(level?.name || '');
            setDescription(level?.description || '');
            setIsActive(level?.isActive ?? true);
        }, 0);
    }, [level, open]);

    const handleSave = async () => {
        if (!name.trim()) { alert('Името е задължително'); return; }
        setLoading(true);
        try {
            if (level) {
                await updateLevel({ variables: { id: level.id, input: { name, description: description || null, isActive } } });
            } else {
                await createLevel({ variables: { input: { name, description: description || null, isActive }, companyId } });
            }
            onSuccess();
        } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>{level ? 'Редактиране на ниво' : 'Ново ниво на достъп'}</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="Име" fullWidth value={name} onChange={(e) => setName(e.target.value)} slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={accessControlFieldsHelp.accessLevelName} /></InputAdornment> } }} />
                <TextField label="Описание" fullWidth multiline rows={2} value={description} onChange={(e) => setDescription(e.target.value)} slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={accessControlFieldsHelp.accessLevelDescription} /></InputAdornment> } }} />
                <FormControlLabel control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />} label="Активно" />
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Отказ</Button>
                <Button variant="contained" onClick={handleSave} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Запази'}</Button>
            </DialogActions>
        </Dialog>
    );
};

export default AccessLevelDialog;
