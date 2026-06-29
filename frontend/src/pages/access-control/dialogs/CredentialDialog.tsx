import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, Select, MenuItem
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import { CREATE_ACCESS_CODE } from '../../../graphql/mutations/accessControl';

const CredentialDialog: React.FC<{open: boolean, onClose: () => void, onSuccess: () => void}> = ({ open, onClose, onSuccess }) => {
    const [createCode] = useMutation(CREATE_ACCESS_CODE);
    const [formData, setFormData] = useState({ code: '', codeType: 'one_time', usesRemaining: 1, expiresHours: 24 });
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Нов Код</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="Код" fullWidth value={formData.code} onChange={(e) => setFormData({...formData, code: e.target.value})} />
                <Select value={formData.codeType} onChange={(e) => setFormData({...formData, codeType: e.target.value})}>
                    <MenuItem value="one_time">Еднократен</MenuItem>
                    <MenuItem value="permanent">Постоянен</MenuItem>
                </Select>
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Отказ</Button><Button variant="contained" onClick={async () => { await createCode({ variables: { input: formData } }); onSuccess(); }}>Генерирай</Button></DialogActions>
        </Dialog>
    );
};

export default CredentialDialog;
