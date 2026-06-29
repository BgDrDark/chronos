import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Select, MenuItem, InputLabel, FormControl,
  Button, CircularProgress, Typography, Box,
} from '@mui/material';
import { useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import { UPDATE_TERMINAL } from '../../../graphql/mutations/kioskAdmin';
import { UPDATE_DOOR_TERMINAL } from '../../../graphql/gatewayMutations';

const TerminalUpdateDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  terminal: any;
  doors: any[];
  onSuccess: () => void;
}> = ({ open, onClose, terminal, doors, onSuccess }) => {
  const [updateDoorTerminal] = useMutation(UPDATE_DOOR_TERMINAL);
  const [updateTerminal] = useMutation(UPDATE_TERMINAL);
  const [selectedDoorId, setSelectedDoorId] = useState<number | ''>('');
  const [mode, setMode] = useState<string>('both');
  const [alias, setAlias] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const prevTerminalKeyRef = React.useRef<string>('');

  React.useEffect(() => {
    const key = terminal ? `${terminal.id}-${open}` : '';
    if (!key || prevTerminalKeyRef.current === key) return;
    prevTerminalKeyRef.current = key;
    setTimeout(() => {
      const currentDoor = doors.find(d => d.terminalId === terminal?.hardwareUuid);
      if (currentDoor) {
        setSelectedDoorId(currentDoor.id);
        setMode(terminal?.mode || currentDoor.terminalMode || 'both');
      } else {
        setSelectedDoorId('');
        setMode(terminal?.mode || 'both');
      }
      setAlias(terminal?.alias || terminal?.deviceName || '');
    }, 0);
  }, [terminal, open, doors]);

  const handleSave = async () => {
    if (!terminal) return;
    setLoading(true);
    try {
      await updateTerminal({
        variables: {
          id: parseInt(terminal.id),
          alias: alias,
          mode: mode,
        },
      });

      if (selectedDoorId) {
        await updateDoorTerminal({
          variables: {
            id: selectedDoorId,
            terminalId: terminal.hardwareUuid,
            terminalMode: mode,
          },
        });
      } else {
        const currentDoor = doors.find(d => d.terminalId === terminal.hardwareUuid);
        if (currentDoor) {
          await updateDoorTerminal({
            variables: {
              id: currentDoor.id,
              terminalId: null,
              terminalMode: 'access',
            },
          });
        }
      }
      onSuccess();
    } catch (e) {
      alert(getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Настройка на Терминал</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
        <Box>
          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
            HWID: {terminal?.hardwareUuid}
          </Typography>
        </Box>

        <TextField
          label="Име (Alias)"
          fullWidth
          value={alias}
          onChange={(e) => setAlias(e.target.value)}
          placeholder="напр. Вход Цех"
        />

        <FormControl fullWidth>
          <InputLabel>Режим на работа</InputLabel>
          <Select
            value={mode}
            label="Режим на работа"
            onChange={(e) => setMode(e.target.value)}
          >
            <MenuItem value="access">Само Достъп (Отваря врата)</MenuItem>
            <MenuItem value="clock">Само Работно време (Clock In/Out)</MenuItem>
            <MenuItem value="both">Комбиниран (Достъп + Работно време)</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Свържи с врата</InputLabel>
          <Select
            value={selectedDoorId}
            label="Свържи с врата"
            onChange={(e) => setSelectedDoorId(e.target.value as number)}
          >
            <MenuItem value=""><em>Няма (Само за работно време)</em></MenuItem>
            {doors.map(d => (
              <MenuItem key={d.id} value={d.id}>
                {d.name} {d.terminalId && d.terminalId !== terminal?.hardwareUuid ? '(Зает)' : ''}
              </MenuItem>
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

export default TerminalUpdateDialog;
