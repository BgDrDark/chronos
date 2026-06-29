import React, { useState } from 'react';
import {
  Typography, Card, CardContent, Button,
  Box, CircularProgress,
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip,
  IconButton
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { getErrorMessage, AccessSchedule } from '../../types';
import { ACCESS_SCHEDULES_QUERY } from '../../graphql/queries/accessPolicy';
import { DELETE_ACCESS_SCHEDULE } from '../../graphql/mutations/accessPolicy';
import { COMPANIES_QUERY } from '../../graphql/queries';
import AccessScheduleDialog from './dialogs/AccessScheduleDialog';

/* ---------- SchedulesPage ---------- */
const SchedulesPage: React.FC = () => {
    const { data: compData } = useQuery(COMPANIES_QUERY);
    const companyId = compData?.companies?.[0]?.id;

    const { data: schedulesData, loading: schedulesLoading, refetch: refetchSchedules } = useQuery(ACCESS_SCHEDULES_QUERY, {
        variables: { companyId },
        skip: !companyId,
    });

    const [deleteSchedule] = useMutation(DELETE_ACCESS_SCHEDULE);

    const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
    const [scheduleEditOpen, setScheduleEditOpen] = useState(false);
    const [selectedSchedule, setSelectedSchedule] = useState<AccessSchedule | null>(null);

    const handleDeleteSchedule = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете този график?')) {
            try {
                await deleteSchedule({ variables: { id } });
                refetchSchedules();
            } catch (e) { alert(getErrorMessage(e)); }
        }
    };

    return (
        <>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, alignItems: 'center' }}>
                        <Typography variant="h6">Графици за достъп</Typography>
                        <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => setScheduleDialogOpen(true)}>Нов график</Button>
                    </Box>
                    <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                            <TableHead sx={{ bgcolor: 'action.hover' }}>
                                <TableRow>
                                    <TableCell>Име</TableCell>
                                    <TableCell>Часова зона</TableCell>
                                    <TableCell>Празнична отмяна</TableCell>
                                    <TableCell>Статус</TableCell>
                                    <TableCell align="right">Действия</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {schedulesLoading ? (
                                    <TableRow><TableCell colSpan={5} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                ) : schedulesData?.accessSchedules?.length === 0 ? (
                                    <TableRow><TableCell colSpan={5} align="center">Няма добавени графици</TableCell></TableRow>
                                ) : schedulesData?.accessSchedules?.map((s: AccessSchedule) => (
                                    <TableRow key={s.id} hover>
                                        <TableCell sx={{ fontWeight: 500 }}>{s.name}</TableCell>
                                        <TableCell>{s.timezone}</TableCell>
                                        <TableCell><Chip size="small" label={s.holidayOverrideAuto ? 'Автоматичен' : 'Ръчен'} color={s.holidayOverrideAuto ? 'primary' : 'default'} variant="outlined" /></TableCell>
                                        <TableCell><Chip size="small" label={s.isActive ? 'Активен' : 'Неактивен'} color={s.isActive ? 'success' : 'default'} /></TableCell>
                                        <TableCell align="right">
                                            <IconButton size="small" onClick={() => { setSelectedSchedule(s); setScheduleEditOpen(true); }}><EditIcon fontSize="small" /></IconButton>
                                            <IconButton size="small" onClick={() => handleDeleteSchedule(s.id)}><DeleteIcon fontSize="small" /></IconButton>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>

            <AccessScheduleDialog
                open={scheduleDialogOpen}
                onClose={() => setScheduleDialogOpen(false)}
                onSuccess={() => { setScheduleDialogOpen(false); refetchSchedules(); }}
                companyId={companyId}
            />
            <AccessScheduleDialog
                open={scheduleEditOpen}
                onClose={() => setScheduleEditOpen(false)}
                onSuccess={() => { setScheduleEditOpen(false); refetchSchedules(); }}
                schedule={selectedSchedule}
                companyId={companyId}
            />
        </>
    );
};

export default SchedulesPage;
