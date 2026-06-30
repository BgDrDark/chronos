import React, { useState } from 'react';
import {
  Typography, Card, CardContent, Button,
  Box, CircularProgress, ToggleButtonGroup, ToggleButton,
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip,
  IconButton
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  People as PeopleIcon,
  AccountTree as TreeIcon,
  TableChart as TableIcon
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { getErrorMessage, AccessZone } from '../../types';
import { InfoIcon } from '../../components/ui/InfoIcon';
import { accessControlFieldsHelp } from '../../components/ui/fieldsHelpText';
import { ACCESS_ZONES_QUERY } from '../../graphql/queries/accessControl';
import { DELETE_ACCESS_ZONE } from '../../graphql/mutations/accessControl';
import { USERS_QUERY } from '../../graphql/queries';
import ZoneCreateDialog from './dialogs/ZoneCreateDialog';
import ZoneEditDialog from './dialogs/ZoneEditDialog';
import ZoneUsersDialog from './dialogs/UserZoneAssignment';
import ZoneTreeView from './ZoneTreeView';

type ViewMode = 'tree' | 'table';

/* ---------- ZonesPage ---------- */
const ZonesPage: React.FC = () => {
    const { data: zonesData, loading: zonesLoading, refetch: refetchZones } = useQuery(ACCESS_ZONES_QUERY);
    const { data: usersData } = useQuery(USERS_QUERY);

    const [deleteZone] = useMutation(DELETE_ACCESS_ZONE);

    const [viewMode, setViewMode] = useState<ViewMode>('tree');
    const [zoneDialogOpen, setZoneDialogOpen] = useState(false);
    const [zoneEditOpen, setZoneEditOpen] = useState(false);
    const [selectedZone, setSelectedZone] = useState<AccessZone | null>(null);
    const [usersDialogOpen, setUsersDialogOpen] = useState(false);
    const [parentForNew, setParentForNew] = useState<AccessZone | null>(null);

    const handleDeleteZone = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете тази зона?')) {
            try {
                await deleteZone({ variables: { id } });
                refetchZones();
            } catch (e) { alert(getErrorMessage(e)); }
        }
    };

    const handleAddChild = (parent: AccessZone) => {
        setParentForNew(parent);
        setZoneDialogOpen(true);
    };

    const handleCreateSuccess = () => {
        setZoneDialogOpen(false);
        setParentForNew(null);
        refetchZones();
    };

    const zones: AccessZone[] = zonesData?.accessZones ?? [];

    return (
        <>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">Зони за достъп <InfoIcon helpText={accessControlFieldsHelp.zoneName} /></Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <ToggleButtonGroup
                                size="small"
                                value={viewMode}
                                exclusive
                                onChange={(_, v) => v && setViewMode(v)}
                            >
                                <ToggleButton value="tree"><TreeIcon fontSize="small" /></ToggleButton>
                                <ToggleButton value="table"><TableIcon fontSize="small" /></ToggleButton>
                            </ToggleButtonGroup>
                            <Button startIcon={<AddIcon />} variant="contained" size="small" onClick={() => { setParentForNew(null); setZoneDialogOpen(true); }}>Нова Зона</Button>
                        </Box>
                    </Box>

                    {zonesLoading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>
                    ) : zones.length === 0 ? (
                        <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>Няма добавени зони</Typography>
                    ) : viewMode === 'tree' ? (
                        <Paper variant="outlined" sx={{ maxHeight: 500, overflow: 'auto' }}>
                            <ZoneTreeView
                                zones={zones}
                                onEdit={(z) => { setSelectedZone(z); setZoneEditOpen(true); }}
                                onDelete={handleDeleteZone}
                                onAddChild={handleAddChild}
                            />
                        </Paper>
                    ) : (
                        <TableContainer component={Paper} variant="outlined">
                            <Table size="small">
                                <TableHead sx={{ bgcolor: 'action.hover' }}>
                                    <TableRow>
                                        <TableCell>ID</TableCell>
                                        <TableCell>Име</TableCell>
                                        <TableCell>Ниво</TableCell>
                                        <TableCell>Родител</TableCell>
                                        <TableCell>Насл.</TableCell>
                                        <TableCell>Работно време</TableCell>
                                        <TableCell>Anti-Passback</TableCell>
                                        <TableCell>Действия</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {zones.map((z: any) => (
                                        <TableRow key={z.id}>
                                            <TableCell sx={{ fontFamily: 'monospace' }}>{z.zoneId}</TableCell>
                                            <TableCell>{z.name}</TableCell>
                                            <TableCell>{z.level}</TableCell>
                                            <TableCell>{z.parentZone?.name ?? '-'}</TableCell>
                                            <TableCell>{z.inheritPermissions ? 'Да' : 'Не'}</TableCell>
                                            <TableCell>{z.requiredHoursStart} - {z.requiredHours_end}</TableCell>
                                            <TableCell>{z.antiPassbackEnabled ? <Chip size="small" label={z.antiPassbackType} color="primary" variant="outlined" /> : 'Изкл.'}</TableCell>
                                            <TableCell>
                                                <IconButton size="small" color="primary" onClick={() => { setSelectedZone(z); setZoneEditOpen(true); }}><EditIcon fontSize="inherit" /></IconButton>
                                                <IconButton size="small" onClick={() => { setSelectedZone(z); setUsersDialogOpen(true); }}><PeopleIcon fontSize="inherit" /></IconButton>
                                                <IconButton size="small" color="error" onClick={() => handleDeleteZone(z.id)}><DeleteIcon fontSize="inherit" /></IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}
                </CardContent>
            </Card>

            <ZoneCreateDialog
                open={zoneDialogOpen}
                onClose={() => { setZoneDialogOpen(false); setParentForNew(null); }}
                onSuccess={handleCreateSuccess}
                zones={zones}
                parentZoneId={parentForNew?.id}
            />
            <ZoneEditDialog
                open={zoneEditOpen}
                onClose={() => setZoneEditOpen(false)}
                onSuccess={() => { setZoneEditOpen(false); refetchZones(); }}
                zones={zones}
                zone={selectedZone}
            />
            <ZoneUsersDialog
                open={usersDialogOpen}
                onClose={() => setUsersDialogOpen(false)}
                zone={selectedZone || {}}
                usersData={usersData}
            />
        </>
    );
};

export default ZonesPage;
