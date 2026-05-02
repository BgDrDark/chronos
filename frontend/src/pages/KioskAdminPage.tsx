import React, { useState } from 'react';
import { getErrorMessage, Terminal, Gateway, AccessZone, User } from '../types';
import { 
  Typography, Card, CardContent, Button, 
  Box, CircularProgress, Switch, FormControlLabel,
  Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Paper, Chip,
  IconButton, Dialog, DialogTitle, DialogContent, 
  DialogActions, TextField, Select, MenuItem, InputLabel,
  FormControl, Autocomplete, Checkbox, List, ListItem,
  ListItemText, ListItemButton, ListItemIcon, Stack
} from '@mui/material';
import { TabbedPage } from '../components/TabbedPage';
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
  Cancel as CancelIcon,
  People as PeopleIcon,
  CloudDownload as DownloadIcon,
  CloudUpload as UploadIcon
} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import KioskCustomizationSettings from '../components/KioskCustomizationSettings';
import { useNavigate } from 'react-router-dom';
import { 
  GATEWAYS_QUERY, 
  TERMINALS_QUERY, 
  ACCESS_ZONES_QUERY,
  ACCESS_DOORS_QUERY,
  ACCESS_CODES_QUERY,
  ACCESS_LOGS_QUERY,
  USERS_QUERY,
  COMPANIES_QUERY
} from '../graphql/queries';
import {
  CREATE_ACCESS_ZONE,
  UPDATE_ACCESS_ZONE,
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
        } catch (e: unknown) {
            const error = e as { message?: string };
            alert(error.message || 'Грешка');
        }
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

    const tabs = [
      { label: 'Конфигурация', path: '/admin/kiosk/config' },
      { label: 'Терминали', path: '/admin/kiosk/terminals' },
      { label: 'Gateways', path: '/admin/kiosk/gateways' },
      { label: 'Зони', path: '/admin/kiosk/zones' },
      { label: 'Врати', path: '/admin/kiosk/doors' },
      { label: 'Кодове', path: '/admin/kiosk/codes' },
      { label: 'Логове', path: '/admin/kiosk/logs' },
      { label: 'Потребители', path: '/admin/kiosk/users' },
    ];

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
    const [deleteZone] = useMutation(DELETE_ACCESS_ZONE);
    const [deleteDoor] = useMutation(DELETE_ACCESS_DOOR);
    const [openDoor] = useMutation(OPEN_DOOR);

    const handleOpenDoor = async (id: number) => {
        try {
            const { data } = await openDoor({ variables: { id } });
            if (data.openDoor) alert('Вратата е отворена успешно!');
        } catch (e: unknown) {
            const error = e as { message?: string };
            alert(`Грешка: ${error.message || 'неизвестна'}`);
        }
    };
    const [revokeCode] = useMutation(REVOKE_ACCESS_CODE);
    const [deleteCode] = useMutation(DELETE_ACCESS_CODE);
    const [deleteTerminal] = useMutation(DELETE_TERMINAL);

    const handleDeleteTerminal = async (id: number) => {
        if (window.confirm('Сигурни ли сте, че искате да изтриете този терминал?')) {
            try {
                await deleteTerminal({ variables: { id } });
                refetchTerminals();
            } catch (e) {
                alert(getErrorMessage(e));
            }
        }
    };

    // Dialog States
    const [zoneDialogOpen, setZoneDialogOpen] = useState(false);
    const [zoneEditOpen, setZoneEditOpen] = useState(false);
    const [doorDialogOpen, setDoorDialogOpen] = useState(false);
    const [terminalDialogOpen, setTerminalDialogOpen] = useState(false);
    const [selectedTerminal, setSelectedTerminal] = useState<Terminal | null>(null);
    const [selectedUserForAccess, setSelectedUserForAccess] = useState<User | null>(null);
    const [selectedZone, setSelectedZone] = useState<AccessZone | null>(null);
    const [selectedGateway, setSelectedGateway] = useState<Gateway | null>(null);
    const [codeDialogOpen, setCodeDialogOpen] = useState(false);
    const [gatewayEditOpen, setGatewayEditOpen] = useState(false);
    const [accessDialogOpen, setAccessDialogOpen] = useState(false);
    const [usersDialogOpen, setUsersDialogOpen] = useState(false);
    const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
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
        } catch (err) {
            setSyncingStatus(`Грешка: ${getErrorMessage(err)}`);
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
            } catch (e) { alert(getErrorMessage(e)); }
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
        <TabbedPage tabs={tabs} defaultTabPath="/admin/kiosk/config">
            <Typography variant="h4" gutterBottom fontWeight="bold">Отдел КД (Контрол на Достъпа)</Typography>

            {/* Kiosk Settings Tab */}
            {tab === 'config' && (
                <Box>
                    <KioskSecuritySettings />
                    <KioskCustomizationSettings />
                </Box>
            )}

            {/* Terminals Tab */}
            {tab === 'terminals' && (
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
            {tab === 'gateways' && (
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
            {tab === 'zones' && (
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
                                                <IconButton size="small" color="primary" onClick={() => { setSelectedZone(z); setZoneEditOpen(true); }}><EditIcon fontSize="inherit" /></IconButton>
                                                <IconButton size="small" onClick={() => { setSelectedZone(z); setUsersDialogOpen(true); }}><PeopleIcon fontSize="inherit" /></IconButton>
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
            {tab === 'doors' && (
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
            {tab === 'codes' && (
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
            {tab === 'logs' && (
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
            {tab === 'users' && (
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

            <ZoneCreateDialog open={zoneDialogOpen} onClose={() => setZoneDialogOpen(false)} onSuccess={() => { setZoneDialogOpen(false); refetchZones(); }} zones={zonesData?.accessZones || []} />
            <ZoneEditDialog open={zoneEditOpen} onClose={() => setZoneEditOpen(false)} onSuccess={() => { setZoneEditOpen(false); refetchZones(); }} zones={zonesData?.accessZones || []} zone={selectedZone} />
            <DoorCreateDialog open={doorDialogOpen} onClose={() => setDoorDialogOpen(false)} onSuccess={() => { setDoorDialogOpen(false); refetchDoors(); }} gateways={gatewaysData?.gateways || []} zones={zonesData?.accessZones || []} />
            <CodeCreateDialog open={codeDialogOpen} onClose={() => setCodeDialogOpen(false)} onSuccess={() => { setCodeDialogOpen(false); refetchCodes(); }} />
            <ZoneUsersDialog open={usersDialogOpen} onClose={() => setUsersDialogOpen(false)} zone={selectedZone || {}} usersData={usersData} />
            <UserAccessDialog open={accessDialogOpen} onClose={() => { setAccessDialogOpen(false); setSelectedUsers([]); }} user={selectedUserForAccess} bulkUsers={selectedUsers} zones={zonesData?.accessZones || []} onSuccess={() => { setAccessDialogOpen(false); setSelectedUsers([]); refetchZones(); }} />
            <TerminalUpdateDialog 
                open={terminalDialogOpen} 
                onClose={() => setTerminalDialogOpen(false)} 
                terminal={selectedTerminal} 
                doors={doorsData?.accessDoors || []}
                onSuccess={() => { setTerminalDialogOpen(false); refetchTerminals(); refetchDoors(); }}
            />
        </TabbedPage>
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

const ZoneCreateDialog: React.FC<{open: boolean, onClose: () => void, onSuccess: () => void, zones: any[]}> = ({ open, onClose, onSuccess, zones }) => {
    const [createZone] = useMutation(CREATE_ACCESS_ZONE);
    const [formData, setFormData] = useState({ 
        zoneId: '', 
        name: '', 
        level: 1, 
        dependsOn: [] as string[],
        requiredHoursStart: '00:00', 
        requiredHoursEnd: '23:59', 
        antiPassbackEnabled: false, 
        antiPassbackType: 'soft', 
        antiPassbackTimeout: 5 
    });
    const [loading, setLoading] = useState(false);

    const handleCreate = async () => {
        setLoading(true);
        try {
            await createZone({ variables: { input: formData } });
            onSuccess();
            setFormData({ zoneId: '', name: '', level: 1, dependsOn: [], requiredHoursStart: '00:00', requiredHoursEnd: '23:59', antiPassbackEnabled: false, antiPassbackType: 'soft', antiPassbackTimeout: 5 });
        } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Нова Зона</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="ID" fullWidth value={formData.zoneId} onChange={(e) => setFormData({...formData, zoneId: e.target.value})} />
                <TextField label="Име" fullWidth value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
                <FormControl fullWidth>
                    <InputLabel>Ниво</InputLabel>
                    <Select value={formData.level} label="Ниво" onChange={(e) => setFormData({...formData, level: e.target.value as number})}>
                        <MenuItem value={1}>Ниво 1</MenuItem>
                        <MenuItem value={2}>Ниво 2</MenuItem>
                        <MenuItem value={3}>Ниво 3</MenuItem>
                    </Select>
                </FormControl>

                <FormControl fullWidth>
                    <InputLabel>Зависи от</InputLabel>
                    <Select
                        multiple
                        value={formData.dependsOn}
                        label="Зависи от"
                        onChange={(e) => setFormData({...formData, dependsOn: typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value})}
                        renderValue={(selected) => (
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {selected.map((value) => (
                                    <Chip key={value} label={value} size="small" />
                                ))}
                            </Box>
                        )}
                    >
                        {zones.filter(z => z.zoneId !== formData.zoneId).map((z: any) => (
                            <MenuItem key={z.id} value={z.zoneId}>{z.name}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Отказ</Button>
                <Button variant="contained" onClick={handleCreate} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Създай'}</Button>
            </DialogActions>
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

const ZoneUsersDialog: React.FC<{open: boolean, onClose: () => void, zone: unknown, usersData: unknown}> = ({ open, onClose, zone, usersData }) => {
    const [assignZone] = useMutation(ASSIGN_ZONE_TO_USER, { refetchQueries: [{ query: ACCESS_ZONES_QUERY }] });
    const [removeZone] = useMutation(REMOVE_ZONE_FROM_USER, { refetchQueries: [{ query: ACCESS_ZONES_QUERY }] });
    const [selectedUser, setSelectedUser] = useState<unknown>(null);
    if (!zone) return null;
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Потребители в {(zone as { name?: string }).name}</DialogTitle>
            <DialogContent sx={{ pt: 2 }}>
                <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                    <Autocomplete 
                        fullWidth 
                        options={(usersData as { users: { users: unknown[] } })?.users?.users || []} 
                        getOptionLabel={(option) => `${(option as { firstName?: string }).firstName || ''} ${(option as { lastName?: string }).lastName || ''}`} 
                        value={selectedUser} 
                        onChange={(_, v) => setSelectedUser(v)} 
                        renderInput={(p) => <TextField {...p} label="Добави" size="small" />} 
                    />
                    <Button variant="contained" onClick={async () => { 
                        const userId = (selectedUser as { id?: number })?.id;
                        const zoneId = (zone as { id?: number })?.id;
                        if (userId && zoneId) { 
                            await assignZone({ variables: { userId: Number(userId), zoneId: Number(zoneId) } }); 
                            setSelectedUser(null); 
                        } 
                    }}>Добави</Button>
                </Box>
                <List>{(zone as { authorizedUsers?: unknown[] })?.authorizedUsers?.map((u: unknown) => (
                    <ListItem 
                        key={(u as { id: number }).id} 
                        secondaryAction={
                            <IconButton edge="end" color="error" onClick={async () => {
                                const userId = (u as { id: number }).id;
                                const zoneId = (zone as { id: number }).id;
                                if (userId && zoneId) {
                                    await removeZone({ variables: { userId: Number(userId), zoneId: Number(zoneId) } });
                                }
                            }}>
                                <DeleteIcon />
                            </IconButton>
                        }
                    >
                        <ListItemText primary={`${(u as { firstName?: string }).firstName || ''} ${(u as { lastName?: string }).lastName || ''}`} />
                    </ListItem>
                ))}</List>
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
        } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
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
    const [, setLoading] = useState(false);
    const handleAction = async (action: string) => {
        if (!confirm(`Сигурни ли сте?`)) return;
        setLoading(true);
        try { await bulkAction({ variables: { action } }); onAction(); } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
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

const ZoneEditDialog: React.FC<{
    open: boolean, 
    onClose: () => void, 
    onSuccess: () => void, 
    zones: any[],
    zone: any
}> = ({ open, onClose, onSuccess, zones, zone }) => {
    const [updateZone] = useMutation(UPDATE_ACCESS_ZONE);
    const [formData, setFormData] = useState({ 
        zoneId: '', 
        name: '', 
        level: 1, 
        dependsOn: [] as string[],
        requiredHoursStart: '00:00', 
        requiredHoursEnd: '23:59', 
        antiPassbackEnabled: false, 
        antiPassbackType: 'soft', 
        antiPassbackTimeout: 5,
        description: ''
    });
    const [loading, setLoading] = useState(false);

    React.useEffect(() => {
        if (zone && open) {
            setFormData({
                zoneId: zone.zoneId || '',
                name: zone.name || '',
                level: zone.level || 1,
                dependsOn: zone.dependsOn || [],
                requiredHoursStart: zone.requiredHoursStart || '00:00',
                requiredHoursEnd: zone.requiredHours_end || '23:59',
                antiPassbackEnabled: zone.antiPassbackEnabled || false,
                antiPassbackType: zone.antiPassbackType || 'soft',
                antiPassbackTimeout: zone.antiPassbackTimeout || 5,
                description: zone.description || ''
            });
        }
    }, [zone, open]);

    const handleSave = async () => {
        setLoading(true);
        try {
            await updateZone({ 
                variables: { 
                    id: parseInt(zone.id),
                    input: formData 
                } 
            });
            onSuccess();
        } catch (e) { alert(getErrorMessage(e)); } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Редактиране на Зона</DialogTitle>
            <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
                <TextField label="ID" fullWidth value={formData.zoneId} onChange={(e) => setFormData({...formData, zoneId: e.target.value})} />
                <TextField label="Име" fullWidth value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
                <FormControl fullWidth>
                    <InputLabel>Ниво</InputLabel>
                    <Select value={formData.level} label="Ниво" onChange={(e) => setFormData({...formData, level: e.target.value as number})}>
                        <MenuItem value={1}>Ниво 1</MenuItem>
                        <MenuItem value={2}>Ниво 2</MenuItem>
                        <MenuItem value={3}>Ниво 3</MenuItem>
                    </Select>
                </FormControl>

                <FormControl fullWidth>
                    <InputLabel>Зависи от</InputLabel>
                    <Select
                        multiple
                        value={formData.dependsOn}
                        label="Зависи от"
                        onChange={(e) => setFormData({...formData, dependsOn: typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value})}
                        renderValue={(selected) => (
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {selected.map((value) => (
                                    <Chip key={value} label={value} size="small" />
                                ))}
                            </Box>
                        )}
                    >
                        {zones.filter(z => z.zoneId !== formData.zoneId).map((z: any) => (
                            <MenuItem key={z.id} value={z.zoneId}>{z.name}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
                
                <Stack direction="row" spacing={2}>
                    <TextField label="От" type="time" fullWidth value={formData.requiredHoursStart} onChange={(e) => setFormData({...formData, requiredHoursStart: e.target.value})} InputLabelProps={{ shrink: true }} />
                    <TextField label="До" type="time" fullWidth value={formData.requiredHoursEnd} onChange={(e) => setFormData({...formData, requiredHoursEnd: e.target.value})} InputLabelProps={{ shrink: true }} />
                </Stack>

                <TextField label="Описание" fullWidth multiline rows={2} value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} />
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Отказ</Button>
                <Button variant="contained" onClick={handleSave} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Запази'}</Button>
            </DialogActions>
        </Dialog>
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
