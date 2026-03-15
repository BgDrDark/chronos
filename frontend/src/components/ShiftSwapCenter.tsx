import React, { useState, useMemo } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, Button, 
  MenuItem, TextField, Chip, List, Paper,
  CircularProgress
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import SendIcon from '@mui/icons-material/Send';
import { type User, type WorkSchedule, type SwapRequest } from '../types';

const GET_SWAP_DATA = gql`
  query GetSwapData {
    me {
      id
      email
      firstName
      lastName
      role { name }
    }
    users(limit: 1000) {
      users { id firstName lastName email }
    }
    mySwapRequests {
      id
      status
      createdAt
      requestor { id firstName lastName }
      targetUser { id firstName lastName }
      requestorScheduleId
      targetScheduleId
      requestorSchedule { id date shift { name } }
      targetSchedule { id date shift { name } }
    }
    pendingAdminSwaps {
      id
      status
      requestor { firstName lastName }
      targetUser { firstName lastName }
      requestorSchedule { date shift { name } }
      targetSchedule { date shift { name } }
    }
  }
`;

const MY_FUTURE_SCHEDULES = gql`
  query MyFutureSchedules($startDate: Date!, $endDate: Date!) {
    mySchedules(startDate: $startDate, endDate: $endDate) {
      id
      date
      shift { name }
    }
  }
`;

const USER_FUTURE_SCHEDULES = gql`
  query UserFutureSchedules($startDate: Date!, $endDate: Date!) {
    workSchedules(startDate: $startDate, endDate: $endDate) {
      id
      date
      user { id }
      shift { name }
    }
  }
`;

const CREATE_SWAP_MUTATION = gql`
  mutation CreateSwap($reqSchedId: Int!, $targetUserId: Int!, $targetSchedId: Int!) {
    createSwapRequest(requestorScheduleId: $reqSchedId, targetUserId: $targetUserId, targetScheduleId: $targetSchedId) {
      id
    }
  }
`;

const RESPOND_SWAP_MUTATION = gql`
  mutation RespondSwap($swapId: Int!, $accept: Boolean!) {
    respondToSwap(swapId: $swapId, accept: $accept) {
      id
    }
  }
`;

const APPROVE_SWAP_MUTATION = gql`
  mutation ApproveSwap($swapId: Int!, $approve: Boolean!) {
    approveSwap(swapId: $swapId, approve: $approve) {
      id
    }
  }
`;

const ShiftSwapCenter: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_SWAP_DATA);
    const [createSwap] = useMutation(CREATE_SWAP_MUTATION);
    const [respondSwap] = useMutation(RESPOND_SWAP_MUTATION);
    const [approveSwap] = useMutation(APPROVE_SWAP_MUTATION);

    // Form State
    const [mySchedId, setMySchedId] = useState('');
    const [targetUserId, setTargetUserId] = useState('');
    const [targetSchedId, setTargetSchedId] = useState('');

    const { today, nextMonth } = useMemo(() => {
        const now = new Date();
        const future = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
        return {
            today: now.toISOString().split('T')[0],
            nextMonth: future.toISOString().split('T')[0]
        };
    }, []);

    const { data: myScheds } = useQuery(MY_FUTURE_SCHEDULES, {
        variables: { startDate: today, endDate: nextMonth }
    });

    const { data: allScheds } = useQuery(USER_FUTURE_SCHEDULES, {
        variables: { startDate: today, endDate: nextMonth },
        skip: !targetUserId
    });

    const handleCreate = async () => {
        try {
            await createSwap({
                variables: {
                    reqSchedId: parseInt(mySchedId),
                    targetUserId: parseInt(targetUserId),
                    targetSchedId: parseInt(targetSchedId)
                }
            });
            alert("Заявката е изпратена!");
            setMySchedId(''); setTargetUserId(''); setTargetSchedId('');
            refetch();
        } catch (err: unknown) { 
            if (err instanceof Error) alert(err.message);
            else alert('Възникна грешка');
        }
    };

    const handleRespond = async (id: number, accept: boolean) => {
        try {
            await respondSwap({ variables: { swapId: id, accept } });
            refetch();
        } catch (err: unknown) { 
            if (err instanceof Error) alert(err.message);
            else alert('Възникна грешка');
        }
    };

    const handleApprove = async (id: number, approve: boolean) => {
        try {
            await approveSwap({ variables: { swapId: id, approve } });
            refetch();
        } catch (err: unknown) { 
            if (err instanceof Error) alert(err.message);
            else alert('Възникна грешка');
        }
    };

    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;

    const isAdmin = data?.me?.role?.name === 'admin';
    const myRequests: SwapRequest[] = data?.mySwapRequests || [];
    const adminPending: SwapRequest[] = data?.pendingAdminSwaps || [];

    return (
        <Box sx={{ mt: 3 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                <SwapHorizIcon color="primary" /> Размяна на смени
            </Typography>

            <Grid container spacing={3}>
                {/* 1. Create Request */}
                <Grid size={{ xs: 12, md: 4 }}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Нова заявка</Typography>
                            <TextField
                                select fullWidth label="Моя смяна" margin="normal" size="small"
                                value={mySchedId} onChange={(e) => setMySchedId(e.target.value)}
                            >
                                {myScheds?.mySchedules?.length > 0 ? myScheds.mySchedules.map((s: WorkSchedule) => (
                                    <MenuItem key={s.id} value={s.id}>{s.date} - {s.shift?.name}</MenuItem>
                                )) : <MenuItem disabled value="">Няма налични смени</MenuItem>}
                            </TextField>

                            <TextField
                                select fullWidth label="Колега" margin="normal" size="small"
                                value={targetUserId} onChange={(e) => setTargetUserId(e.target.value)}
                            >
                                {data?.users?.users?.filter((u: User) => String(u.id) !== String(data.me.id)).length > 0 ? data.users.users.filter((u: User) => String(u.id) !== String(data.me.id)).map((u: User) => (
                                    <MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>
                                )) : <MenuItem disabled value="">Няма налични колеги</MenuItem>}
                            </TextField>

                            <TextField
                                select fullWidth label="Смяна на колегата" margin="normal" size="small"
                                value={targetSchedId} onChange={(e) => setTargetSchedId(e.target.value)}
                                disabled={!targetUserId}
                            >
                                {allScheds?.workSchedules?.filter((s: WorkSchedule) => String(s.user.id) === String(targetUserId)).length > 0 ? allScheds.workSchedules
                                    .filter((s: WorkSchedule) => String(s.user.id) === String(targetUserId))
                                    .map((s: WorkSchedule) => (
                                        <MenuItem key={s.id} value={s.id}>{s.date} - {s.shift?.name}</MenuItem>
                                    )) : <MenuItem disabled value="">Няма налични смени</MenuItem>
                                }
                            </TextField>

                            <Button 
                                variant="contained" fullWidth sx={{ mt: 2 }} 
                                startIcon={<SendIcon />} onClick={handleCreate}
                                disabled={!mySchedId || !targetSchedId}
                            >
                                Изпрати покана
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>

                {/* 2. My Requests List */}
                <Grid size={{ xs: 12, md: 8 }}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Моите размени</Typography>
                            <List>
                                {myRequests.map((req: SwapRequest) => {
                                    const isIncoming = String(req.targetUser.id) === String(data.me.id);
                                    return (
                                        <Paper key={req.id} variant="outlined" sx={{ mb: 2, p: 2 }}>
                                            <Grid container alignItems="center" spacing={2}>
                                                <Grid size={{ xs: 12, sm: 8 }}>
                                                    <Typography variant="subtitle2">
                                                        {isIncoming ? `Покана от ${req.requestor.firstName}` : `Покана до ${req.targetUser.firstName}`}
                                                    </Typography>
                                                    <Typography variant="body2" color="text.secondary">
                                                        Размяна: <strong>{req.requestorSchedule.date}</strong> ({req.requestorSchedule.shift?.name}) 
                                                        ↔ <strong>{req.targetSchedule.date}</strong> ({req.targetSchedule.shift?.name})
                                                    </Typography>
                                                    <Box sx={{ mt: 1 }}>
                                                        <Chip 
                                                            label={req.status.toUpperCase()} 
                                                            size="small" 
                                                            color={req.status === 'approved' ? 'success' : (req.status === 'pending' ? 'warning' : 'default')} 
                                                        />
                                                    </Box>
                                                </Grid>
                                                <Grid size={{ xs: 12, sm: 4 }} sx={{ textAlign: 'right' }}>
                                                    {isIncoming && req.status === 'pending' && (
                                                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                                                            <Button size="small" variant="contained" color="success" onClick={() => handleRespond(req.id, true)}>Приеми</Button>
                                                            <Button size="small" variant="outlined" color="error" onClick={() => handleRespond(req.id, false)}>Откажи</Button>
                                                        </Box>
                                                    )}
                                                </Grid>
                                            </Grid>
                                        </Paper>
                                    );
                                })}
                                {myRequests.length === 0 && <Typography variant="body2" color="text.secondary">Нямате активни размени.</Typography>}
                            </List>
                        </CardContent>
                    </Card>
                </Grid>

                {/* 3. Admin Approval Section */}
                {isAdmin && adminPending.length > 0 && (
                    <Grid size={{ xs: 12 }}>
                        <Card variant="outlined" sx={{ border: '2px solid #2196f3' }}>
                            <CardContent>
                                <Typography variant="h6" color="primary" gutterBottom sx={{ fontWeight: 'bold' }}>
                                    Администратор: Чакащи одобрение размени ({adminPending.length})
                                </Typography>
                                <Grid container spacing={2}>
                                    {adminPending.map((p: SwapRequest) => (
                                        <Grid size={{ xs: 12, sm: 6, md: 4 }} key={p.id}>
                                            <Paper sx={{ p: 2, bgcolor: '#e3f2fd' }}>
                                                <Typography variant="body2">
                                                    <strong>{p.requestor.firstName}</strong> <SwapHorizIcon sx={{ verticalAlign: 'middle', fontSize: '1rem' }} /> <strong>{p.targetUser.firstName}</strong>
                                                </Typography>
                                                <Typography variant="caption" display="block">
                                                    Дати: {p.requestorSchedule.date} ↔ {p.targetSchedule.date}
                                                </Typography>
                                                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                                                    <Button fullWidth size="small" variant="contained" color="success" onClick={() => handleApprove(p.id, true)}>Одобри</Button>
                                                    <Button fullWidth size="small" variant="outlined" color="error" onClick={() => handleApprove(p.id, false)}>Отхвърли</Button>
                                                </Box>
                                            </Paper>
                                        </Grid>
                                    ))}
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>
                )}
            </Grid>
        </Box>
    );
};

export default ShiftSwapCenter;
