import React, { useState } from 'react';
import {
  Typography, Card, CardContent, Button, Box, CircularProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem,
} from '@mui/material';
import {
  Edit as EditIcon, Delete as DeleteIcon, Add as AddIcon,
  Elevator as ElevatorIcon, Layers as FloorIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { getErrorMessage } from '../../types';
import { GATEWAYS_QUERY } from '../../graphql/queries/kioskAdmin';
import { ELEVATOR_GROUPS_QUERY } from '../../graphql/queries/elevator';
import {
  CREATE_ELEVATOR_GROUP, UPDATE_ELEVATOR_GROUP, DELETE_ELEVATOR_GROUP,
  CREATE_ELEVATOR_FLOOR, UPDATE_ELEVATOR_FLOOR, DELETE_ELEVATOR_FLOOR,
} from '../../graphql/mutations/elevator';

interface ElevatorGroupForm {
  name: string;
  gatewayId: number | '';
  terminalId: string;
  controllerType: string;
}

interface ElevatorFloorForm {
  elevatorGroupId: number;
  floorNumber: number;
  name: string;
  zoneId: number | null;
  relayDeviceId: string;
  relayNumber: number;
  order: number;
}

const emptyGroupForm = (): ElevatorGroupForm => ({
  name: '', gatewayId: '', terminalId: '', controllerType: 'sr201',
});

const emptyFloorForm = (groupId: number): ElevatorFloorForm => ({
  elevatorGroupId: groupId, floorNumber: 1, name: '', zoneId: null,
  relayDeviceId: '', relayNumber: 1, order: 0,
});

const ElevatorPage: React.FC = () => {
  const { data: groupsData, loading: groupsLoading, refetch: refetchGroups } = useQuery(ELEVATOR_GROUPS_QUERY);
  const { data: gatewaysData } = useQuery(GATEWAYS_QUERY);
  const [deleteGroup] = useMutation(DELETE_ELEVATOR_GROUP);
  const [deleteFloor] = useMutation(DELETE_ELEVATOR_FLOOR);

  const [groupDialog, setGroupDialog] = useState(false);
  const [groupForm, setGroupForm] = useState<ElevatorGroupForm>(emptyGroupForm());
  const [editingGroup, setEditingGroup] = useState<any>(null);
  const [groupLoading, setGroupLoading] = useState(false);

  const [floorDialog, setFloorDialog] = useState(false);
  const [floorForm, setFloorForm] = useState<ElevatorFloorForm>(emptyFloorForm(0));
  const [editingFloor, setEditingFloor] = useState<any>(null);
  const [floorLoading, setFloorLoading] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);

  const [createGroup] = useMutation(CREATE_ELEVATOR_GROUP);
  const [updateGroup] = useMutation(UPDATE_ELEVATOR_GROUP);
  const [createFloor] = useMutation(CREATE_ELEVATOR_FLOOR);
  const [updateFloor] = useMutation(UPDATE_ELEVATOR_FLOOR);

  const handleSaveGroup = async () => {
    setGroupLoading(true);
    try {
      if (editingGroup) {
        await updateGroup({ variables: { id: editingGroup.id, input: groupForm } });
      } else {
        await createGroup({ variables: { input: groupForm } });
      }
      setGroupDialog(false);
      setEditingGroup(null);
      refetchGroups();
    } catch (e) { alert(getErrorMessage(e)); } finally { setGroupLoading(false); }
  };

  const handleDeleteGroup = async (id: number) => {
    if (window.confirm('Сигурни ли сте, че искате да изтриете тази етажна група?')) {
      try {
        await deleteGroup({ variables: { id } });
        refetchGroups();
      } catch (e) { alert(getErrorMessage(e)); }
    }
  };

  const handleSaveFloor = async () => {
    setFloorLoading(true);
    try {
      if (editingFloor) {
        await updateFloor({ variables: { id: editingFloor.id, input: floorForm } });
      } else {
        await createFloor({ variables: { input: floorForm } });
      }
      setFloorDialog(false);
      setEditingFloor(null);
      refetchGroups();
    } catch (e) { alert(getErrorMessage(e)); } finally { setFloorLoading(false); }
  };

  const handleDeleteFloor = async (id: number) => {
    if (window.confirm('Сигурни ли сте, че искате да изтриете този етаж?')) {
      try {
        await deleteFloor({ variables: { id } });
        refetchGroups();
      } catch (e) { alert(getErrorMessage(e)); }
    }
  };

  const openFloorDialog = (group: any, floor: any = null) => {
    setSelectedGroupId(group.id);
    setEditingFloor(floor);
    setFloorForm(floor ? {
      elevatorGroupId: floor.elevatorGroupId,
      floorNumber: floor.floorNumber,
      name: floor.name || '',
      zoneId: floor.zoneId ?? null,
      relayDeviceId: floor.relayDeviceId,
      relayNumber: floor.relayNumber,
      order: floor.order ?? 0,
    } : emptyFloorForm(group.id));
    setFloorDialog(true);
  };

  const gateways = gatewaysData?.gateways ?? [];

  const groups = groupsData?.elevatorGroups ?? [];

  return (
    <>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Етажен контрол</Typography>
            <Button startIcon={<AddIcon />} variant="contained" size="small" onClick={() => { setEditingGroup(null); setGroupForm(emptyGroupForm()); setGroupDialog(true); }}>
              Нова група
            </Button>
          </Box>

          {groupsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>
          ) : groups.length === 0 ? (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>Няма Етажни групи</Typography>
          ) : groups.map((group: any) => (
            <Card key={group.id} variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ElevatorIcon color="primary" />
                    <Typography variant="subtitle1" fontWeight={600}>{group.name}</Typography>
                    <Chip label={group.controllerType} size="small" variant="outlined" />
                    {!group.isActive && <Chip label="неактивна" size="small" color="error" />}
                  </Box>
                  <Box>
                    <IconButton size="small" onClick={() => { setEditingGroup(group); setGroupForm({ name: group.name, gatewayId: group.gatewayId, terminalId: group.terminalId, controllerType: group.controllerType }); setGroupDialog(true); }}>
                      <EditIcon fontSize="inherit" />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDeleteGroup(group.id)}>
                      <DeleteIcon fontSize="inherit" />
                    </IconButton>
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Gateway: {group.gatewayId} | Terminal: {group.terminalId}
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" fontWeight={500}>Етажи</Typography>
                  <Button size="small" startIcon={<AddIcon />} variant="outlined" onClick={() => openFloorDialog(group)}>
                    Добави етаж
                  </Button>
                </Box>
                {(group.floors ?? []).length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>Няма добавени етажи</Typography>
                ) : (
                  <TableContainer component={Paper} variant="outlined" sx={{ bgcolor: 'action.hover' }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>#</TableCell>
                          <TableCell>Етаж</TableCell>
                          <TableCell>Име</TableCell>
                          <TableCell>Зона</TableCell>
                          <TableCell>Relay устройство</TableCell>
                          <TableCell>Relay #</TableCell>
                          <TableCell>Действия</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {group.floors.map((floor: any) => (
                          <TableRow key={floor.id}>
                            <TableCell>{floor.floorNumber}</TableCell>
                            <TableCell>{floor.name || '-'}</TableCell>
                            <TableCell>{floor.order}</TableCell>
                            <TableCell>{floor.zone?.name ?? '-'}</TableCell>
                            <TableCell sx={{ fontFamily: 'monospace' }}>{floor.relayDeviceId}</TableCell>
                            <TableCell>{floor.relayNumber}</TableCell>
                            <TableCell>
                              <IconButton size="small" onClick={() => openFloorDialog(group, floor)}>
                                <EditIcon fontSize="inherit" />
                              </IconButton>
                              <IconButton size="small" color="error" onClick={() => handleDeleteFloor(floor.id)}>
                                <DeleteIcon fontSize="inherit" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          ))}
        </CardContent>
      </Card>

      {/* Group Dialog */}
      <Dialog open={groupDialog} onClose={() => setGroupDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingGroup ? 'Редактиране на група' : 'Нова Етажна група'}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField label="Име" fullWidth value={groupForm.name} onChange={(e) => setGroupForm({...groupForm, name: e.target.value})} />
          <FormControl fullWidth>
            <InputLabel>Gateway</InputLabel>
            <Select value={groupForm.gatewayId} label="Gateway" onChange={(e) => setGroupForm({...groupForm, gatewayId: e.target.value as number})}>
              {gateways.map((g: any) => (
                <MenuItem key={g.id} value={g.id}>{g.name} ({g.type})</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField label="Terminal ID" fullWidth value={groupForm.terminalId} onChange={(e) => setGroupForm({...groupForm, terminalId: e.target.value})} />
          <FormControl fullWidth>
            <InputLabel>Тип контролер</InputLabel>
            <Select value={groupForm.controllerType} label="Тип контролер" onChange={(e) => setGroupForm({...groupForm, controllerType: e.target.value})}>
              <MenuItem value="sr201">SR201</MenuItem>
              <MenuItem value="custom">Custom</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGroupDialog(false)}>Отказ</Button>
          <Button variant="contained" onClick={handleSaveGroup} disabled={groupLoading}>
            {groupLoading ? <CircularProgress size={24} /> : 'Запази'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floor Dialog */}
      <Dialog open={floorDialog} onClose={() => setFloorDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingFloor ? 'Редактиране на етаж' : 'Нов етаж'}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField label="Етаж #" type="number" fullWidth value={floorForm.floorNumber} onChange={(e) => setFloorForm({...floorForm, floorNumber: parseInt(e.target.value) || 0})} />
          <TextField label="Име" fullWidth value={floorForm.name} onChange={(e) => setFloorForm({...floorForm, name: e.target.value})} helperText="Напр. Партер, Етаж 1, Сървърна" />
          <TextField label="Relay устройство" fullWidth value={floorForm.relayDeviceId} onChange={(e) => setFloorForm({...floorForm, relayDeviceId: e.target.value})} helperText="ID на SR201 или друго relay устройство" />
          <TextField label="Relay #" type="number" fullWidth value={floorForm.relayNumber} onChange={(e) => setFloorForm({...floorForm, relayNumber: parseInt(e.target.value) || 1})} />
          <TextField label="Ред" type="number" fullWidth value={floorForm.order} onChange={(e) => setFloorForm({...floorForm, order: parseInt(e.target.value) || 0})} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFloorDialog(false)}>Отказ</Button>
          <Button variant="contained" onClick={handleSaveFloor} disabled={floorLoading}>
            {floorLoading ? <CircularProgress size={24} /> : 'Запази'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ElevatorPage;
