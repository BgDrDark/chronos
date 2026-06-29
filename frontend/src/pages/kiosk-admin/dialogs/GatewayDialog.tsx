import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Select, MenuItem, InputLabel, FormControl,
  Button, CircularProgress,
} from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import { COMPANIES_QUERY } from '../../../graphql/queries';
import { UPDATE_GATEWAY } from '../../../graphql/mutations/kioskAdmin';

const GatewayEditDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  gateway: any;
  onSuccess: () => void;
}> = ({ open, onClose, gateway, onSuccess }) => {
  const { data: compData } = useQuery(COMPANIES_QUERY);
  const [updateGateway] = useMutation(UPDATE_GATEWAY);

  const [alias, setAlias] = useState('');
  const [companyId, setCompanyId] = useState<number | ''>('');
  const [loading, setLoading] = useState(false);

  const prevGatewayKeyRef = React.useRef<string>('');

  React.useEffect(() => {
    const key = gateway ? `${gateway.id}-${open}` : '';
    if (!key || prevGatewayKeyRef.current === key) return;
    prevGatewayKeyRef.current = key;
    setTimeout(() => {
      setAlias(gateway?.alias || '');
      setCompanyId(gateway?.companyId || '');
    }, 0);
  }, [gateway, open]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await updateGateway({
        variables: {
          id: gateway.id,
          alias: alias,
          companyId: companyId === '' ? null : parseInt(companyId.toString()),
        },
      });
      onSuccess();
    } catch (e) {
      alert(getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Редакция на Gateway</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
        <TextField
          label="Alias (Приятелско име)"
          fullWidth
          value={alias}
          onChange={(e) => setAlias(e.target.value)}
        />
        <FormControl fullWidth>
          <InputLabel>Фирма</InputLabel>
          <Select
            value={companyId}
            label="Фирма"
            onChange={(e) => setCompanyId(e.target.value as number)}
          >
            <MenuItem value=""><em>-- Няма (Системна) --</em></MenuItem>
            {compData?.companies?.map((c: any) => (
              <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отказ</Button>
        <Button variant="contained" onClick={handleSave} disabled={loading}>
          {loading ? <CircularProgress size={24} /> : 'Запази'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default GatewayEditDialog;
