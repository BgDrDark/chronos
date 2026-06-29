import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, Box, Autocomplete, List, ListItem,
  ListItemText, ListItemButton, ListItemIcon,
  IconButton, Checkbox, CircularProgress
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { useMutation } from '@apollo/client';
import { getErrorMessage } from '../../../types';
import {
  ASSIGN_ZONE_TO_USER,
  REMOVE_ZONE_FROM_USER,
  BULK_UPDATE_USER_ACCESS,
} from '../../../graphql/mutations/accessControl';
import { ACCESS_ZONES_QUERY } from '../../../graphql/queries/accessControl';

/* ---------- ZoneUsersDialog ---------- */
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

/* ---------- UserAccessDialog ---------- */
export const UserAccessDialog: React.FC<{open: boolean, onClose: () => void, user: any, bulkUsers: number[], zones: any[], onSuccess: () => void}> = ({ open, onClose, user, bulkUsers, zones, onSuccess }) => {
    const [assignZone] = useMutation(ASSIGN_ZONE_TO_USER);
    const [removeZone] = useMutation(REMOVE_ZONE_FROM_USER);
    const [bulkUpdate] = useMutation(BULK_UPDATE_USER_ACCESS);
    const [checkedZones, setCheckedZones] = useState<number[]>([]);
    const [loading, setLoading] = useState(false);

    const prevUserAccessRef = React.useRef<string>('');

    React.useEffect(() => {
        const key = `${open}-${user?.id ?? 'bulk'}`;
        if (prevUserAccessRef.current === key) return;
        prevUserAccessRef.current = key;
        setTimeout(() => {
            if (user) {
                const auth = zones.filter(z => z.authorizedUsers?.some((au: any) => au.id === user.id)).map(z => parseInt(z.id));
                setCheckedZones(auth);
            } else setCheckedZones([]);
        }, 0);
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

export default ZoneUsersDialog;
