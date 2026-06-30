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
import { getErrorMessage, AccessLevel } from '../../types';
import { InfoIcon } from '../../components/ui/InfoIcon';
import { accessControlFieldsHelp } from '../../components/ui/fieldsHelpText';
import { ACCESS_LEVELS_QUERY } from '../../graphql/queries/accessPolicy';
import { DELETE_ACCESS_LEVEL } from '../../graphql/mutations/accessPolicy';
import { COMPANIES_QUERY } from '../../graphql/queries';
import AccessLevelDialog from './dialogs/AccessLevelDialog';

/* ---------- AccessLevelsPage ---------- */
const AccessLevelsPage: React.FC = () => {
    const { data: compData } = useQuery(COMPANIES_QUERY);
    const companyId = compData?.companies?.[0]?.id;

    const { data: levelsData, loading: levelsLoading, refetch: refetchLevels } = useQuery(ACCESS_LEVELS_QUERY, {
        variables: { companyId },
        skip: !companyId,
    });

    const [deleteLevel] = useMutation(DELETE_ACCESS_LEVEL);

    const [levelDialogOpen, setLevelDialogOpen] = useState(false);
    const [levelEditOpen, setLevelEditOpen] = useState(false);
    const [selectedLevel, setSelectedLevel] = useState<AccessLevel | null>(null);

    const handleDeleteLevel = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете това ниво на достъп?')) {
            try {
                await deleteLevel({ variables: { id } });
                refetchLevels();
            } catch (e) { alert(getErrorMessage(e)); }
        }
    };

    return (
        <>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, alignItems: 'center' }}>
                        <Typography variant="h6">Нива на достъп <InfoIcon helpText={accessControlFieldsHelp.accessLevelName} /></Typography>
                        <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => setLevelDialogOpen(true)}>Ново ниво</Button>
                    </Box>
                    <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                            <TableHead sx={{ bgcolor: 'action.hover' }}>
                                <TableRow>
                                    <TableCell>Име</TableCell>
                                    <TableCell>Описание</TableCell>
                                    <TableCell align="center">Зони</TableCell>
                                    <TableCell align="center">Потребители</TableCell>
                                    <TableCell>Статус</TableCell>
                                    <TableCell align="right">Действия</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {levelsLoading ? (
                                    <TableRow><TableCell colSpan={6} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                ) : levelsData?.accessLevels?.length === 0 ? (
                                    <TableRow><TableCell colSpan={6} align="center">Няма добавени нива на достъп</TableCell></TableRow>
                                ) : levelsData?.accessLevels?.map((lv: AccessLevel) => (
                                    <TableRow key={lv.id} hover>
                                        <TableCell sx={{ fontWeight: 500 }}>{lv.name}</TableCell>
                                        <TableCell>{lv.description || '-'}</TableCell>
                                        <TableCell align="center">{lv.zoneAssignments?.length || 0}</TableCell>
                                        <TableCell align="center">{lv.userCount ?? 0}</TableCell>
                                        <TableCell><Chip size="small" label={lv.isActive ? 'Активно' : 'Неактивно'} color={lv.isActive ? 'success' : 'default'} /></TableCell>
                                        <TableCell align="right">
                                            <IconButton size="small" onClick={() => { setSelectedLevel(lv); setLevelEditOpen(true); }}><EditIcon fontSize="small" /></IconButton>
                                            <IconButton size="small" onClick={() => handleDeleteLevel(lv.id)}><DeleteIcon fontSize="small" /></IconButton>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>

            <AccessLevelDialog
                open={levelDialogOpen}
                onClose={() => setLevelDialogOpen(false)}
                onSuccess={() => { setLevelDialogOpen(false); refetchLevels(); }}
                companyId={companyId}
            />
            <AccessLevelDialog
                open={levelEditOpen}
                onClose={() => setLevelEditOpen(false)}
                onSuccess={() => { setLevelEditOpen(false); refetchLevels(); }}
                level={selectedLevel}
                companyId={companyId}
            />
        </>
    );
};

export default AccessLevelsPage;
