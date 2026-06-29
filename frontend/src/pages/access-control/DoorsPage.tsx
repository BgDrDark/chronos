import React, { useState } from 'react';
import {
  Typography, Card, CardContent, Button,
  Box, CircularProgress,
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip,
  IconButton
} from '@mui/material';
import {
  MeetingRoom as DoorIcon,
  Delete as DeleteIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { getErrorMessage, AccessDoor } from '../../types';
import { ACCESS_DOORS_QUERY, ACCESS_ZONES_QUERY } from '../../graphql/queries/accessControl';
import {
  DELETE_ACCESS_DOOR,
  OPEN_DOOR,
} from '../../graphql/mutations/accessControl';
import { GATEWAYS_QUERY } from '../../graphql/queries';
import DoorCreateDialog from './dialogs/DoorCreateDialog';

/* ---------- DoorsPage ---------- */
const DoorsPage: React.FC = () => {
    const { data: doorsData, loading: doorsLoading, refetch: refetchDoors } = useQuery(ACCESS_DOORS_QUERY);
    const { data: zonesData } = useQuery(ACCESS_ZONES_QUERY);
    const { data: gatewaysData } = useQuery(GATEWAYS_QUERY);

    const [deleteDoor] = useMutation(DELETE_ACCESS_DOOR);
    const [openDoor] = useMutation(OPEN_DOOR);

    const [doorDialogOpen, setDoorDialogOpen] = useState(false);

    const handleOpenDoor = async (id: number) => {
        try {
            const { data } = await openDoor({ variables: { id } });
            if (data.openDoor) alert('Вратата е отворена успешно!');
        } catch (e: unknown) {
            const error = e as { message?: string };
            alert(`Грешка: ${error.message || 'неизвестна'}`);
        }
    };

    const handleDeleteDoor = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете тази врата?')) {
            try {
                await deleteDoor({ variables: { id } });
                refetchDoors();
            } catch (e) { alert(getErrorMessage(e)); }
        }
    };

    return (
        <>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                        <Typography variant="h6">Врати</Typography>
                        <Button startIcon={<AddIcon />} variant="contained" size="small" onClick={() => setDoorDialogOpen(true)}>Нова Врата</Button>
                    </Box>
                    <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                            <TableHead sx={{ bgcolor: 'action.hover' }}>
                                <TableRow>
                                    <TableCell>ID</TableCell>
                                    <TableCell>Име</TableCell>
                                    <TableCell>Зона</TableCell>
                                    <TableCell>Хардуер</TableCell>
                                    <TableCell>Действия</TableCell>
                                    <TableCell>Статус</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {doorsLoading ? (
                                    <TableRow><TableCell colSpan={6} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                ) : doorsData?.accessDoors?.length === 0 ? (
                                    <TableRow><TableCell colSpan={6} align="center">Няма добавени врати</TableCell></TableRow>
                                ) : doorsData?.accessDoors?.map((d: any) => (
                                    <TableRow key={d.id}>
                                        <TableCell sx={{ fontFamily: 'monospace' }}>{d.doorId}</TableCell>
                                        <TableCell>{d.name}</TableCell>
                                        <TableCell>{d.zone?.name || d.zoneDbId}</TableCell>
                                        <TableCell>{d.deviceId} (P{d.relayNumber})</TableCell>
                                        <TableCell>
                                            <IconButton size="small" color="success" onClick={() => handleOpenDoor(d.id)} title="Отвори врата">
                                                <DoorIcon fontSize="inherit" />
                                            </IconButton>
                                            <IconButton size="small" color="error" onClick={() => handleDeleteDoor(d.id)} title="Изтрий">
                                                <DeleteIcon fontSize="inherit" />
                                            </IconButton>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                size="small"
                                                label={d.isOnline ? 'Online' : 'Offline'}
                                                color={d.isOnline ? 'success' : 'error'}
                                                variant={d.isOnline ? 'filled' : 'outlined'}
                                            />
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>

            <DoorCreateDialog
                open={doorDialogOpen}
                onClose={() => setDoorDialogOpen(false)}
                onSuccess={() => { setDoorDialogOpen(false); refetchDoors(); }}
                gateways={gatewaysData?.gateways || []}
                zones={zonesData?.accessZones || []}
            />
        </>
    );
};

export default DoorsPage;
