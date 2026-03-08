import React, { useState } from 'react';
import { 
  Container, Typography, Card, CardContent, Button, 
  Box, CircularProgress, Switch, FormControlLabel,
  Tabs, Tab, Grid, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Paper, Chip,
  IconButton, Dialog, DialogTitle, DialogContent, 
  DialogActions, TextField, Select, MenuItem, InputLabel,
  FormControl, Autocomplete, Checkbox, List, ListItem,
  ListItemText, ListItemButton, ListItemIcon
} from '@mui/material';
import {
  Security as SecurityIcon,
  QrCodeScanner as QrCodeScannerIcon,
  Router as GatewayIcon,
  MeetingRoom as DoorIcon,
  Layers as ZoneIcon,
  VpnKey as CodeIcon,
  History as LogIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Group as GroupIcon,
  People as PeopleIcon,
  Sync as SyncIcon,
  CloudDownload as DownloadIcon,
  CloudUpload as UploadIcon
} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import KioskCustomizationSettings from '../components/KioskCustomizationSettings';
import { useNavigate } from 'react-router-dom';
import { 
  GATEWAYS_QUERY, 
  TERMINALS_QUERY, 
  PRINTERS_QUERY, 
  GATEWAY_STATS_QUERY,
  ACCESS_ZONES_QUERY,
  ACCESS_DOORS_QUERY,
  ACCESS_CODES_QUERY,
  ACCESS_LOGS_QUERY,
  USERS_QUERY,
  COMPANIES_QUERY
} from '../graphql/queries';
import {
  CREATE_ACCESS_ZONE,
  DELETE_ACCESS_ZONE,
  CREATE_ACCESS_DOOR,
  DELETE_ACCESS_DOOR,
  OPEN_DOOR,
  UPDATE_DOOR_TERMINAL,
  CREATE_ACCESS_CODE,
  REVOKE_ACCESS_CODE,
  DELETE_ACCESS_CODE,
  UPDATE_GATEWAY,
  ASSIGN_ZONE_TO_USER,
  REMOVE_ZONE_FROM_USER,
  BULK_UPDATE_USER_ACCESS,
  BULK_EMERGENCY_ACTION,
  SYNC_GATEWAY_CONFIG,
  UPDATE_TERMINAL,
  DELETE_TERMINAL
} from '../graphql/gatewayMutations';

const GET_KIOSK_SECURITY_SETTINGS = gql`
  query GetKioskSecurity {
    kioskSecuritySettings {
      requireGps
      requireSameNetwork
    }
  }
`;

const UPDATE_KIOSK_SECURITY_MUTATION = gql`
  mutation UpdateKioskSecurity($requireGps: Boolean!, $requireSameNetwork: Boolean!) {
    updateKioskSecuritySettings(requireGps: $requireGps, requireSameNetwork: $requireSameNetwork)
  }
`;

const KioskSecuritySettings: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_KIOSK_SECURITY_SETTINGS);
    const [updateSecurity, { loading: updating }] = useMutation(UPDATE_KIOSK_SECURITY_MUTATION);
    const [msg, setMsg] = useState('');

    if (loading) return <CircularProgress size={24} />;

    const handleToggle = async (field: 'requireGps' | 'requireSameNetwork', value: boolean) => {
        const variables = {
            requireGps: field === 'requireGps' ? value : data.kioskSecuritySettings.requireGps,
            requireSameNetwork: field === 'requireSameNetwork' ? value : data.kioskSecuritySettings.requireSameNetwork
        };
        try {
            await updateSecurity({ variables });
            setMsg('Настройките за Kiosk са обновени.');
            refetch();
            setTimeout(() => setMsg(''), 3000);
        } catch (e: any) { alert(e.message); }
    };

    return (
        <Card sx={{ mb: 4, border: '1px solid #f44336' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom color="error.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SecurityIcon /> Сигурност на Kiosk Терминал
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Управление на допълнителните защити при генериране на QR код. Тези настройки важат за всички служители.
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <FormControlLabel 
                        control={
                            <Switch 
                                checked={data?.kioskSecuritySettings?.requireGps} 
                                onChange={(e) => handleToggle('requireGps', e.target.checked)} 
                                disabled={updating}
                            />
                        }
                        label="Изисквай GPS верификация (Геофенсинг)"
                    />
                    <FormControlLabel 
                        control={
                            <Switch 
                                checked={data?.kioskSecuritySettings?.requireSameNetwork} 
                                onChange={(e) => handleToggle('requireSameNetwork', e.target.checked)} 
                                disabled={updating}
                            />
                        }
                        label="Изисквай същата локална мрежа (IP Match)"
                    />
                </Box>
                {msg && <Typography color="success.main" sx={{ mt: 1 }}>{msg}</Typography>}
            </CardContent>
        </Card>
    );
};

const KioskAdminPage: React.FC<{tab?: string}> = ({ tab }) => {
    const navigate = useNavigate();
    const tabMap: Record<string, number> = {
        'kiosk': 0,
        'terminals': 1,
        'gateways': 2,
        'zones': 3,
        'doors': 4,
        'codes': 5,
        'logs': 6,
        'users': 7
    };
    
    const activeTab = tab ? tabMap[tab] || 0 : 0;

    const handleTabChange = (_: any, newValue: number) => {
        const reverseMap = Object.entries(tabMap).find(([_, v]) => v === newValue);
        if (reverseMap) {
            const pathSuffix = reverseMap[0] === 'kiosk' ? '' : `/${reverseMap[0]}`;
            navigate(`/admin/kiosk${pathSuffix}`);
        }
    };

    // Queries
    const { data: gatewaysData, loading: gatewaysLoading, refetch: refetchGateways } = useQuery(GATEWAYS_QUERY);
    const { data: terminalsData, loading: terminalsLoading, refetch: refetchTerminals } = useQuery(TERMINALS_QUERY);
    const { data: zonesData, loading: zonesLoading, refetch: refetchZones } = useQuery(ACCESS_ZONES_QUERY);
    const { data: doorsData, loading: doorsLoading, refetch: refetchDoors } = useQuery(ACCESS_DOORS_QUERY);
    const { data: codesData, loading: codesLoading, refetch: refetchCodes } = useQuery(ACCESS_CODES_QUERY);
    const { data: logsData, loading: logsLoading, refetch: refetchLogs } = useQuery(ACCESS_LOGS_QUERY, {
        variables: { limit: 50 }
    });
    const { data: usersData, loading: usersLoading } = useQuery(USERS_QUERY);

    // Mutations
    const [createZone] = useMutation(CREATE_ACCESS_ZONE);
    const [deleteZone] = useMutation(DELETE_ACCESS_ZONE);
    const [createDoor] = useMutation(CREATE_ACCESS_DOOR);
    const [deleteDoor] = useMutation(DELETE_ACCESS_DOOR);
    const [openDoor] = useMutation(OPEN_DOOR);

    const handleOpenDoor = async (id: number) => {
        try {
            const { data } = await openDoor({ variables: { id } });
            if (data.openDoor) alert('Вратата е отворена успешно!');
        } catch (e: any) {
            alert(`Грешка: ${e.message}`);
        }
    };
    const [updateDoorTerminal] = useMutation(UPDATE_DOOR_TERMINAL);
    const [createCode] = useMutation(CREATE_ACCESS_CODE);
    const [revokeCode] = useMutation(REVOKE_ACCESS_CODE);
    const [deleteCode] = useMutation(DELETE_ACCESS_CODE);
    const [updateGateway] = useMutation(UPDATE_GATEWAY);
    const [deleteTerminal] = useMutation(DELETE_TERMINAL);

    const handleDeleteTerminal = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете този терминал?')) {
            try {
                await deleteTerminal({ variables: { id } });
                refetchTerminals();
            } catch (e: any) {
                alert(e.message);
            }
        }
    };

    // Dialog States
    const [zoneDialogOpen, setZoneDialogOpen] = useState(false);
    const [doorDialogOpen, setDoorDialogOpen] = useState(false);
    const [terminalDialogOpen, setTerminalDialogOpen] = useState(false);
    const [selectedTerminal, setSelectedTerminal] = useState<any>(null);
    const [codeDialogOpen, setCodeDialogOpen] = useState(false);
    const [gatewayEditOpen, setGatewayEditOpen] = useState(false);
    const [usersDialogOpen, setUsersDialogOpen] = useState(false);
    const [accessDialogOpen, setAccessDialogOpen] = useState(false);
    const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
    const [selectedUserForAccess, setSelectedUserForAccess] = useState<any>(null);
    const [selectedZone, setSelectedZone] = useState<any>(null);
    const [selectedGateway, setSelectedGateway] = useState<any>(null);
    const [syncingGateway, setSyncingGateway] = useState<number | null>(null);
    const [syncingStatus, setSyncingStatus] = useState<string>('');

    const [syncGateway] = useMutation(SYNC_GATEWAY_CONFIG);

    const syncGatewayConfig = async (gatewayId: number, direction: 'push' | 'pull') => {
        setSyncingGateway(gatewayId);
        setSyncingStatus(direction === 'push' ? 'Изтегляне на данни от Gateway...' : 'Изпращане на данни към Gateway...');
        try {
            await syncGateway({ variables: { id: gatewayId, direction } });
            setSyncingStatus(direction === 'push' ? 'Успешно изтеглено!' : 'Успешно изпратено!');
            refetchGateways();
            refetchZones();
            refetchDoors();
        } catch (err: any) {
            setSyncingStatus(`Грешка: ${err.message || 'Грешка при свързване'}`);
        }
        setTimeout(() => { setSyncingGateway(null); setSyncingStatus(''); }, 3000);
    };


    const formatTimeAgo = (dateStr: string | null) => {
        if (!dateStr) return 'Никога';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
        if (diff < 60) return `${diff}с`;
        if (diff < 3600) return `${Math.floor(diff / 60)}м`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}ч`;
        return `${Math.floor(diff / 86400)}д`;
    };

    const handleDeleteZone = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете тази зона?')) {
            try {
                await deleteZone({ variables: { id } });
                refetchZones();
            } catch (e: any) { alert(e.message); }
        }
    };

    const handleDeleteDoor = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете тази врата?')) {
            try {
                await deleteDoor({ variables: { id } });
                refetchDoors();
            } catch (e: any) { alert(e.message); }
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom fontWeight="bold">Отдел КД (Контрол на Достъпа)</Typography>
            
            <Tabs 
                value={activeTab} 
                onChange={handleTabChange} 
                variant="scrollable"
                scrollButtons="auto"
                sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
            >
                <Tab icon={<QrCodeScannerIcon />} label="Конфигурация" />
                <Tab icon={<PeopleIcon />} label="Терминали" />
                <Tab icon={<GatewayIcon />} label="Gateways" />
                <Tab icon={<ZoneIcon />} label="Зони" />
                <Tab icon={<DoorIcon />} label="Врати" />
                <Tab icon={<CodeIcon />} label="Кодове" />
                <Tab icon={<LogIcon />} label="Логове" />
                <Tab icon={<PeopleIcon />} label="Потребители" />
            </Tabs>

            {/* Kiosk Settings Tab */}
            {activeTab === 0 && (
                <Box>
                    <KioskSecuritySettings />
                    <KioskCustomizationSettings />
                </Box>
            )}

            {/* Terminals Tab */}
            {activeTab === 1 && (
                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                            <Typography variant="h6">Активни Терминали</Typography>
                            <IconButton onClick={() => refetchTerminals()}><RefreshIcon /></IconButton>
                        </Box>
                        <TableContainer component={Paper} variant="outlined">
                            <Table size="small">
                                <TableHead sx={{ bgcolor: 'action.hover' }}>
                                    <TableRow>
                                        <TableCell>Статус</TableCell>
                                        <TableCell>Alias / Device</TableCell>
                                        <TableCell>Хардуерен ID</TableCell>
                                        <TableCell>Свързана врата</TableCell>
                                        <TableCell>Последна активност</TableCell>
                                        <TableCell>Действия</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {terminalsLoading ? (
                                        <TableRow><TableCell colSpan={6} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                    ) : terminalsData?.terminals.map((t: any) => {
                                        const associatedDoor = doorsData?.accessDoors.find((d: any) => d.terminalId === t.hardwareUuid);
                                        return (
                                            <TableRow key={t.id}>
                                                <TableCell><Chip size="small" label={t.isActive ? 'Online' : 'Offline'} color={t.isActive ? 'success' : 'default'} /></TableCell>
                                                <TableCell>
                                                    <Typography variant="body2" fontWeight="bold">{t.alias || t.deviceName}</Typography>
                                                    <Typography variant="caption" color="text.secondary">{t.deviceModel} ({t.osVersion})</Typography>
                                                </TableCell>
                                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{t.hardwareUuid}</TableCell>
                                                <TableCell>
                                                    {associatedDoor ? (
                                                        <Chip 
                                                            icon={<DoorIcon />} 
                                                            label={`${associatedDoor.name} (${associatedDoor.terminalMode})`} 
                                                            color="primary" 
                                                            size="small" 
                                                            variant="outlined" 
                                                        />
                                                    ) : (
                                                        <Typography variant="caption" color="text.secondary">Няма свързана врата</Typography>
                                                    )}
                                                </TableCell>
                                                <TableCell>{formatTimeAgo(t.lastSeen)}</TableCell>
                                                <TableCell>
                                                    <IconButton size="small" color="primary" onClick={() => { setSelectedTerminal(t); setTerminalDialogOpen(true); }} title="Редактирай">
                                                        <EditIcon fontSize="inherit" />
                                                    </IconButton>
                                                    <IconButton size="small" color="error" onClick={() => handleDeleteTerminal(t.id)} title="Изтрий">
                                                        <DeleteIcon fontSize="inherit" />
                                                    </IconButton>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}

            {/* Gateways Tab */}
            {activeTab === 2 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <EmergencyControl 
                        currentMode={gatewaysData?.gateways[0]?.systemMode || 'normal'} 
                        onAction={() => refetchGateways()} 
                    />
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                                <Typography variant="h6">Регистрирани Gateways</Typography>
                                <IconButton onClick={() => refetchGateways()}><RefreshIcon /></IconButton>
                            </Box>
                            <TableContainer component={Paper} variant="outlined">
                                <Table size="small">
                                    <TableHead sx={{ bgcolor: 'action.hover' }}>
                                        <TableRow>
                                            <TableCell>Статус</TableCell>
                                            <TableCell>Име</TableCell>
                                            <TableCell>Alias</TableCell>
                                            <TableCell>IP Адрес</TableCell>
                                            <TableCell>Heartbeat</TableCell>
                                            <TableCell>Действия</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {gatewaysLoading ? (
                                            <TableRow><TableCell colSpan={6} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                        ) : gatewaysData?.gateways.map((gw: any) => (
                                            <TableRow key={gw.id}>
                                                <TableCell><Chip size="small" label={gw.isActive ? 'Активен' : 'Неактивен'} color={gw.isActive ? 'success' : 'default'} /></TableCell>
                                                <TableCell>{gw.name}</TableCell>
                                                <TableCell>{gw.alias || '-'}</TableCell>
                                                <TableCell>{gw.ipAddress || '-'}</TableCell>
                                                <TableCell>{formatTimeAgo(gw.lastHeartbeat)}</TableCell>
                                                <TableCell>
                                                    {syncingGateway === gw.id ? (
                                                        <Typography variant="caption" color="primary">{syncingStatus}</Typography>
                                                    ) : (
                                                        <>
                                                            <IconButton size="small" title="Pull from Gateway" onClick={() => syncGatewayConfig(gw.id, 'push')}><DownloadIcon fontSize="inherit" /></IconButton>
                                                            <IconButton size="small" title="Push to Gateway" onClick={() => syncGatewayConfig(gw.id, 'pull')}><UploadIcon fontSize="inherit" /></IconButton>
                                                            <IconButton size="small" onClick={() => { setSelectedGateway(gw); setGatewayEditOpen(true); }}><EditIcon fontSize="inherit" /></IconButton>
                                                        </>
                                                    )}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Box>
            )}

            {/* Zones Tab */}
            {activeTab === 3 && (
                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                            <Typography variant="h6">Зони за достъп</Typography>
                            <Button startIcon={<AddIcon />} variant="contained" size="small" onClick={() => setZoneDialogOpen(true)}>Нова Зона</Button>
                        </Box>
                        <TableContainer component={Paper} variant="outlined">
                            <Table size="small">
                                <TableHead sx={{ bgcolor: 'action.hover' }}>
                                    <TableRow>
                                        <TableCell>ID</TableCell>
                                        <TableCell>Име</TableCell>
                                        <TableCell>Ниво</TableCell>
                                        <TableCell>Работно време</TableCell>
                                        <TableCell>Anti-Passback</TableCell>
                                        <TableCell>Действия</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {zonesLoading ? (
                                        <TableRow><TableCell colSpan={6} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                    ) : zonesData?.accessZones.map((z: any) => (
                                        <TableRow key={z.id}>
                                            <TableCell sx={{ fontFamily: 'monospace' }}>{z.zoneId}</TableCell>
                                            <TableCell>{z.name}</TableCell>
                                            <TableCell>{z.level}</TableCell>
                                            <TableCell>{z.requiredHoursStart} - {z.requiredHours_end}</TableCell>
                                            <TableCell>{z.antiPassbackEnabled ? <Chip size="small" label={z.antiPassbackType} color="primary" variant="outlined" /> : 'Изкл.'}</TableCell>
                                            <TableCell>
                                                <IconButton size="small" color="primary" onClick={() => { setSelectedZone(z); setUsersDialogOpen(true); }}><GroupIcon fontSize="inherit" /></IconButton>
                                                <IconButton size="small" color="error" onClick={() => handleDeleteZone(z.id)}><DeleteIcon fontSize="inherit" /></IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}

            {/* Doors Tab */}
            {activeTab === 4 && (
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
                                    ) : doorsData?.accessDoors.map((d: any) => (
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
            )}

            {/* Codes Tab */}
            {activeTab === 5 && (
                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                            <Typography variant="h6">Временни Кодове</Typography>
                            <Button startIcon={<AddIcon />} variant="contained" size="small" onClick={() => setCodeDialogOpen(true)}>Генерирай</Button>
                        </Box>
                        <TableContainer component={Paper} variant="outlined">
                            <Table size="small">
                                <TableHead sx={{ bgcolor: 'action.hover' }}>
                                    <TableRow>
                                        <TableCell>Код</TableCell>
                                        <TableCell>Тип</TableCell>
                                        <TableCell>Оставащи</TableCell>
                                        <TableCell>Статус</TableCell>
                                        <TableCell>Действия</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {codesLoading ? (
                                        <TableRow><TableCell colSpan={5} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                    ) : codesData?.accessCodes.map((c: any) => (
                                        <TableRow key={c.id}>
                                            <TableCell sx={{ fontWeight: 'bold' }}>{c.code}</TableCell>
                                            <TableCell>{c.codeType}</TableCell>
                                            <TableCell>{c.usesRemaining < 0 ? '∞' : c.usesRemaining}</TableCell>
                                            <TableCell><Chip size="small" label={c.isActive ? 'Валиден' : 'Анулиран'} color={c.isActive ? 'success' : 'error'} /></TableCell>
                                            <TableCell>
                                                {c.isActive && <IconButton size="small" color="warning" onClick={async () => { await revokeCode({ variables: { id: c.id } }); refetchCodes(); }}><CancelIcon fontSize="inherit" /></IconButton>}
                                                <IconButton size="small" color="error" onClick={async () => { await deleteCode({ variables: { id: c.id } }); refetchCodes(); }}><DeleteIcon fontSize="inherit" /></IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}

            {/* Logs Tab */}
            {activeTab === 6 && (
                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                            <Typography variant="h6">Последни събития</Typography>
                            <IconButton onClick={() => refetchLogs()}><RefreshIcon /></IconButton>
                        </Box>
                        <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 600 }}>
                            <Table size="small" stickyHeader>
                                <TableHead><TableRow><TableCell>Време</TableCell><TableCell>Потребител</TableCell><TableCell>Зона</TableCell><TableCell>Резултат</TableCell></TableRow></TableHead>
                                <TableBody>
                                    {logsLoading ? (
                                        <TableRow><TableCell colSpan={4} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                    ) : logsData?.accessLogs.map((l: any) => (
                                        <TableRow key={l.id}>
                                            <TableCell>{new Date(l.timestamp).toLocaleString('bg-BG')}</TableCell>
                                            <TableCell>{l.userName || l.userId}</TableCell>
                                            <TableCell>{l.zoneName}</TableCell>
                                            <TableCell><Chip size="small" label={l.result === 'granted' ? 'РАЗРЕШЕНО' : 'ОТКАЗАНО'} color={l.result === 'granted' ? 'success' : 'error'} /></TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}

            {/* Users Tab */}
            {activeTab === 7 && (
                <Card>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, alignItems: 'center' }}>
                            <Typography variant="h6">Управление на достъпа</Typography>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button variant="contained" size="small" disabled={selectedUsers.length === 0} startIcon={<SecurityIcon />} onClick={() => { setSelectedUserForAccess(null); setAccessDialogOpen(true); }}>Групова Промяна</Button>
                                <IconButton onClick={() => usersData.refetch()}><RefreshIcon /></IconButton>
                            </Box>
                        </Box>
                        <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 600 }}>
                            <Table size="small" stickyHeader>
                                <TableHead>
                                    <TableRow>
                                        <TableCell padding="checkbox"><Checkbox onChange={(e) => setSelectedUsers(e.target.checked ? usersData?.users.users.map((u: any) => parseInt(u.id)) : [])} /></TableCell>
                                        <TableCell>Служител</TableCell>
                                        <TableCell>Достъп</TableCell>
                                        <TableCell align="right">Действия</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {usersLoading ? (
                                        <TableRow><TableCell colSpan={4} align="center"><CircularProgress size={24} /></TableCell></TableRow>
                                    ) : usersData?.users.users.map((u: any) => {
                                        const userId = parseInt(u.id);
                                        const userZones = zonesData?.accessZones.filter((z: any) => z.authorizedUsers?.some((au: any) => au.id === u.id)) || [];
                                        return (
                                            <TableRow key={u.id} hover selected={selectedUsers.includes(userId)}>
                                                <TableCell padding="checkbox"><Checkbox checked={selectedUsers.includes(userId)} onChange={() => setSelectedUsers(prev => prev.includes(userId) ? prev.filter(id => id !== userId) : [...prev, userId])} /></TableCell>
                                                <TableCell>{u.firstName} {u.lastName}</TableCell>
                                                <TableCell><Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>{userZones.map((z: any) => <Chip key={z.id} label={z.name} size="small" variant="outlined" />)}</Box></TableCell>
                                                <TableCell align="right"><Button size="small" onClick={() => { setSelectedUserForAccess(u); setAccessDialogOpen(true); }}>Промени</Button></TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}

            {/* Dialogs */}
            <GatewayEditDialog
                open={gatewayEditOpen}
                onClose={() => setGatewayEditOpen(false)}
                gateway={selectedGateway}
                onSuccess={() => { setGatewayEditOpen(false); refetchGateways(); }}
            />

            <ZoneCreateDialog open={zoneDialogOpen} onClose={() => setZoneDialogOpen(false)} onSuccess={() => { setZoneDialogOpen(false); refetchZones(); }} />
            <DoorCreateDialog open={doorDialogOpen} onClose={() => setDoorDialogOpen(false)} onSuccess={() => { setDoorDialogOpen(false); refetchDoors(); }} gateways={gatewaysData?.gateways || []} zones={zonesData?.accessZones || []} />
            <CodeCreateDialog open={codeDialogOpen} onClose={() => setCodeDialogOpen(false)} onSuccess={() => { setCodeDialogOpen(false); refetchCodes(); }} />
            <ZoneUsersDialog open={usersDialogOpen} onClose={() => setUsersDialogOpen(false)} zone={selectedZone} usersData={usersData} />
            <UserAccessDialog open={accessDialogOpen} onClose={() => { setAccessDialogOpen(false); setSelectedUsers([]); }} user={selectedUserForAccess} bulkUsers={selectedUsers} zones={zonesData?.accessZones || []} onSuccess={() => { setAccessDialogOpen(false); setSelectedUsers([]); refetchZones(); }} />
            <TerminalUpdateDialog 
                open={terminalDialogOpen} 
                onClose={() => setTerminalDialogOpen(false)} 
                terminal={selectedTerminal} 
                doors={doorsData?.accessDoors || []}
                onSuccess={() => { setTerminalDialogOpen(false); refetchTerminals(); refetchDoors(); }}
            />
        </Box>
    );
};

// --- Sub-components for dialogs ---

const TerminalUpdateDialog: React.FC<{
    open: boolean, 
    onClose: () => void, 
    terminal: any, 
    doors: any[],
    onSuccess: () => void
}> = ({ open, onClose, terminal, doors, onSuccess }) => {
    const [updateDoorTerminal] = useMutation(UPDATE_DOOR_TERMINAL);
    const [updateTerminal] = useMutation(UPDATE_TERMINAL);
    
    const [selectedDoorId, setSelectedDoorId] = useState<number | ''>('');
    const [mode, setMode] = useState<string>('both');
    const [alias, setAlias] = useState<string>('');
    const [loading, setLoading] = useState(false);

    React.useEffect(() => {
        if (terminal && open) {
            const currentDoor = doors.find(d => d.terminalId === terminal.hardwareUuid);
            if (currentDoor) {
                setSelectedDoorId(currentDoor.id);
                setMode(terminal.mode || currentDoor.terminalMode || 'both');
            } else {
                setSelectedDoorId('');
                setMode(terminal.mode || 'both');
            }
            setAlias(terminal.alias || terminal.deviceName || '');
        }
    }, [terminal, open, doors]);

    const handleSave = async () => {
        if (!terminal) return;
        setLoading(true);
        try {
            // 1. Обновяваме данните на самия терминал (Alias, Mode)
            await updateTerminal({
                variables: {
                    id: parseInt(terminal.id),
                    alias: alias,
                    mode: mode
                }
            });

            // 2. Обновяваме връзката с врата
            if (selectedDoorId) {
                await updateDoorTerminal({
                    variables: {
                        id: selectedDoorId,
                        terminalId: terminal.hardwareUuid,
                        terminalMode: mode
                    }
                });
            } else {
                // Разкачаме ако е имало
                const currentDoor = doors.find(d => d.terminalId === terminal.hardwareUuid);
                if (currentDoor) {
                    await updateDoorTerminal({
                        variables: {
                            id: currentDoor.id,
                            terminalId: null,
                            terminalMode: 'access'
                        }
                    });
                }
            }
            onSuccess();
        } catch (e: any) {
            alert(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Настройка на Терминал</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
                <Box>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>HWID: {terminal?.hardwareUuid}</Typography>
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

const ZoneCreateDialog: React.FC<{open: boolean, onClose: () => void, onSuccess: () => void}> = ({ open, onClose, onSuccess }) => {
    const [createZone] = useMutation(CREATE_ACCESS_ZONE);
    const [formData, setFormData] = useState({ zoneId: '', name: '', level: 1, requiredHoursStart: '00:00', requiredHoursEnd: '23:59', antiPassbackEnabled: false, antiPassbackType: 'soft', antiPassbackTimeout: 5 });
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Нова Зона</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="ID" fullWidth value={formData.zoneId} onChange={(e) => setFormData({...formData, zoneId: e.target.value})} />
                <TextField label="Име" fullWidth value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
                <Select value={formData.level} onChange={(e) => setFormData({...formData, level: e.target.value as number})}>
                    <MenuItem value={1}>Ниво 1</MenuItem>
                    <MenuItem value={2}>Ниво 2</MenuItem>
                </Select>
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Отказ</Button><Button variant="contained" onClick={async () => { await createZone({ variables: { input: formData } }); onSuccess(); }}>Създай</Button></DialogActions>
        </Dialog>
    );
};

const DoorCreateDialog: React.FC<{open: boolean, onClose: () => void, onSuccess: () => void, gateways: any[], zones: any[]}> = ({ open, onClose, onSuccess, gateways, zones }) => {
    const [createDoor] = useMutation(CREATE_ACCESS_DOOR);
    const [formData, setFormData] = useState({ doorId: '', name: '', zoneDbId: 0, gatewayId: 0, deviceId: '', relayNumber: 1 });
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Нова Врата</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="ID" fullWidth value={formData.doorId} onChange={(e) => setFormData({...formData, doorId: e.target.value})} />
                <TextField label="Име" fullWidth value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
                <Select value={formData.zoneDbId} onChange={(e) => setFormData({...formData, zoneDbId: e.target.value as number})}>
                    {zones.map(z => <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>)}
                </Select>
                <Select value={formData.gatewayId} onChange={(e) => setFormData({...formData, gatewayId: e.target.value as number})}>
                    {gateways.map(g => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
                </Select>
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Отказ</Button><Button variant="contained" onClick={async () => { await createDoor({ variables: { input: formData } }); onSuccess(); }}>Създай</Button></DialogActions>
        </Dialog>
    );
};

const CodeCreateDialog: React.FC<{open: boolean, onClose: () => void, onSuccess: () => void}> = ({ open, onClose, onSuccess }) => {
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

const ZoneUsersDialog: React.FC<{open: boolean, onClose: () => void, zone: any, usersData: any}> = ({ open, onClose, zone, usersData }) => {
    const [assignZone] = useMutation(ASSIGN_ZONE_TO_USER, { refetchQueries: [{ query: ACCESS_ZONES_QUERY }] });
    const [removeZone] = useMutation(REMOVE_ZONE_FROM_USER, { refetchQueries: [{ query: ACCESS_ZONES_QUERY }] });
    const [selectedUser, setSelectedUser] = useState<any>(null);
    if (!zone) return null;
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Потребители в {zone.name}</DialogTitle>
            <DialogContent sx={{ pt: 2 }}>
                <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                    <Autocomplete fullWidth options={usersData?.users.users || []} getOptionLabel={(option: any) => `${option.firstName} ${option.lastName}`} value={selectedUser} onChange={(_, v) => setSelectedUser(v)} renderInput={(p) => <TextField {...p} label="Добави" size="small" />} />
                    <Button variant="contained" onClick={async () => { await assignZone({ variables: { userId: parseInt(selectedUser.id), zoneId: zone.id } }); setSelectedUser(null); }}>Добави</Button>
                </Box>
                <List>{zone.authorizedUsers?.map((u: any) => (<ListItem key={u.id} secondaryAction={<IconButton edge="end" color="error" onClick={async () => await removeZone({ variables: { userId: parseInt(u.id), zoneId: zone.id } })}><DeleteIcon /></IconButton>}><ListItemText primary={`${u.firstName} ${u.lastName}`} /></ListItem>))}</List>
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Затвори</Button></DialogActions>
        </Dialog>
    );
};

const UserAccessDialog: React.FC<{open: boolean, onClose: () => void, user: any, bulkUsers: number[], zones: any[], onSuccess: () => void}> = ({ open, onClose, user, bulkUsers, zones, onSuccess }) => {
    const [assignZone] = useMutation(ASSIGN_ZONE_TO_USER);
    const [removeZone] = useMutation(REMOVE_ZONE_FROM_USER);
    const [bulkUpdate] = useMutation(BULK_UPDATE_USER_ACCESS);
    const [checkedZones, setCheckedZones] = useState<number[]>([]);
    const [loading, setLoading] = useState(false);

    React.useEffect(() => {
        if (user) {
            const auth = zones.filter(z => z.authorizedUsers?.some((au: any) => au.id === user.id)).map(z => parseInt(z.id));
            setCheckedZones(auth);
        } else setCheckedZones([]);
    }, [user, zones, open]);

    const handleSave = async () => {
        setLoading(true);
        const uids = user ? [parseInt(user.id)] : bulkUsers;
        try {
            if (user) {
                for (const z of zones) {
                    const zid = parseInt(z.id);
                    const isAuth = z.authorizedUsers?.some((au: any) => parseInt(au.id) === uids[0]);
                    const shouldAuth = checkedZones.includes(zid);
                    if (shouldAuth && !isAuth) await assignZone({ variables: { userId: uids[0], zoneId: zid } });
                    else if (!shouldAuth && isAuth) await removeZone({ variables: { userId: uids[0], zoneId: zid } });
                }
            } else if (checkedZones.length > 0) {
                await bulkUpdate({ variables: { userIds: uids, zoneIds: checkedZones, action: 'add' } });
            }
            onSuccess();
        } catch (e: any) { alert(e.message); } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
            <DialogTitle>{user ? `Достъп: ${user.firstName}` : `Групова промяна (${bulkUsers.length} души)`}</DialogTitle>
            <DialogContent>
                <List>{zones.map((z) => (<ListItem key={z.id} disablePadding><ListItemButton onClick={() => setCheckedZones(prev => prev.includes(parseInt(z.id)) ? prev.filter(id => id !== parseInt(z.id)) : [...prev, parseInt(z.id)] )} dense><ListItemIcon><Checkbox edge="start" checked={checkedZones.includes(parseInt(z.id))} /></ListItemIcon><ListItemText primary={z.name} /></ListItemButton></ListItem>))}</List>
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Отказ</Button><Button variant="contained" onClick={handleSave} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Запази'}</Button></DialogActions>
        </Dialog>
    );
};

const EmergencyControl: React.FC<{currentMode: string, onAction: () => void}> = ({ currentMode, onAction }) => {
    const [bulkAction] = useMutation(BULK_EMERGENCY_ACTION);
    const [loading, setLoading] = useState(false);
    const handleAction = async (action: string) => {
        if (!confirm(`Сигурни ли сте?`)) return;
        setLoading(true);
        try { await bulkAction({ variables: { action } }); onAction(); } catch (e: any) { alert(e.message); } finally { setLoading(false); }
    };
    const getProps = () => {
        if (currentMode === 'emergency_unlock') return { color: '#d32f2f', text: 'АВАРИЙНО ОТКЛЮЧЕНО' };
        if (currentMode === 'lockdown') return { color: '#212121', text: 'ПЪЛНА БЛОКАДА' };
        return { color: '#1976d2', text: 'НОРМАЛЕН РЕЖИМ' };
    };
    const p = getProps();
    return (
        <Card sx={{ bgcolor: p.color, color: 'white', mb: 2 }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                    <Typography variant="h5" fontWeight="bold">{p.text}</Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button variant="contained" sx={{ bgcolor: 'white', color: '#d32f2f' }} onClick={() => handleAction('emergency_unlock')} disabled={currentMode === 'emergency_unlock'}>ОТКЛЮЧИ</Button>
                        <Button variant="contained" sx={{ bgcolor: 'black', color: 'white' }} onClick={() => handleAction('lockdown')} disabled={currentMode === 'lockdown'}>БЛОКАДА</Button>
                        <Button variant="outlined" sx={{ color: 'white', borderColor: 'white' }} onClick={() => handleAction('normal')} disabled={currentMode === 'normal'}>НОРМАЛЕН</Button>
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
};

const GatewayEditDialog: React.FC<{
    open: boolean,
    onClose: () => void,
    gateway: any,
    onSuccess: () => void
}> = ({ open, onClose, gateway, onSuccess }) => {
    const { data: compData } = useQuery(COMPANIES_QUERY);
    const [updateGateway] = useMutation(UPDATE_GATEWAY);
    
    const [alias, setAlias] = useState('');
    const [companyId, setCompanyId] = useState<number | ''>('');
    const [loading, setLoading] = useState(false);

    React.useEffect(() => {
        if (gateway && open) {
            setAlias(gateway.alias || '');
            setCompanyId(gateway.companyId || '');
        }
    }, [gateway, open]);

    const handleSave = async () => {
        setLoading(true);
        try {
            await updateGateway({
                variables: {
                    id: gateway.id,
                    alias: alias,
                    companyId: companyId === '' ? null : parseInt(companyId.toString())
                }
            });
            onSuccess();
        } catch (e: any) {
            alert(e.message);
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
                        {compData?.companies.map((c: any) => (
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

export default KioskAdminPage;
