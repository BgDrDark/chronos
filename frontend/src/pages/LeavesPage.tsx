import React, { useState, useRef } from 'react';
import { getErrorMessage } from '../types';
import {
  Container, Typography, Box, TextField, Button,
  Card, CardContent, Grid, Chip, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, MenuItem, Select, InputLabel, FormControl,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton, Tooltip,
  FormControlLabel, Checkbox, InputAdornment
} from '@mui/material';
import { InfoIcon } from '../components/ui/InfoIcon';
import { useQuery, useMutation, gql } from '@apollo/client';
import { Navigate } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { formatDate } from '../utils/dateUtils';
import { TabbedPage } from '../components/TabbedPage';

// --- Helper for File Upload ---
const uploadFile = async (requestId: number, file: File) => {
    const formData = new FormData();
    const operations = JSON.stringify({
        query: `
            mutation AttachFile($requestId: Int!, $file: Upload!) {
                attachLeaveDocument(requestId: $requestId, file: $file) {
                    id
                }
            }
        `,
        variables: {
            requestId: parseInt(requestId.toString()),
            file: null
        }
    });
    formData.append('operations', operations);
    
    const map = JSON.stringify({
        '0': ['variables.file']
    });
    formData.append('map', map);
    formData.append('0', file);

    const token = localStorage.getItem('token');
    const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:14240') + '/graphql';
    
    const res = await fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Apollo-Require-Preflight': 'true' 
        },
        body: formData
    });
    
    if (!res.ok) {
        throw new Error("File upload failed");
    }
    const json = await res.json();
    if (json.errors) {
        throw new Error(json.errors[0].message);
    }
};

// --- GraphQL ---
const GET_MY_LEAVES = gql`
  query GetMyLeaves {
    myLeaveRequests {
      id
      startDate
      endDate
      leaveType
      reason
      status
      createdAt
      adminComment
      user {
        id
        email
        firstName
        lastName
      }
    }
    me {
      id
      role {
        name
      }
    }
  }
`;

const GET_PENDING_LEAVES = gql`
  query GetPendingLeaves {
    pendingLeaveRequests {
      id
      user {
        id
        email
        firstName
        lastName
      }
      startDate
      endDate
      leaveType
      reason
      createdAt
    }
  }
`;

const GET_ALL_LEAVES = gql`
  query GetAllLeaves($status: String) {
    allLeaveRequests(status: $status) {
      id
      user {
        email
        firstName
        lastName
        leaveBalance {
          totalDays
          usedDays
        }
      }
      startDate
      endDate
      leaveType
      reason
      status
      createdAt
      adminComment
    }
  }
`;

const GET_MY_BALANCE = gql`
  query GetLeaveBalance($userId: Int!, $year: Int!) {
    leaveBalance(userId: $userId, year: $year) {
      totalDays
      usedDays
    }
  }
`;

const REQUEST_LEAVE_MUTATION = gql`
  mutation RequestLeave($startDate: Date!, $endDate: Date!, $leaveType: String!, $reason: String) {
    requestLeave(leaveInput: {startDate: $startDate, endDate: $endDate, leaveType: $leaveType, reason: $reason}) {
      id
      status
      startDate
      endDate
      leaveType
      reason
      createdAt
    }
  }
`;

const APPROVE_LEAVE_MUTATION = gql`
  mutation ApproveLeave($requestId: Int!, $adminComment: String, $employerTopUp: Boolean) {
    approveLeave(requestId: $requestId, adminComment: $adminComment, employerTopUp: $employerTopUp) {
      id
      status
      adminComment
    }
  }
`;

const REJECT_LEAVE_MUTATION = gql`
  mutation RejectLeave($requestId: Int!, $adminComment: String) {
    rejectLeave(requestId: $requestId, adminComment: $adminComment) {
      id
      status
      adminComment
    }
  }
`;

const CANCEL_LEAVE_MUTATION = gql`
  mutation CancelLeaveRequest($requestId: Int!) {
    cancelLeaveRequest(requestId: $requestId) {
      id
      status
    }
  }
`;

const UPDATE_LEAVE_MUTATION = gql`
  mutation UpdateLeaveRequest($requestId: Int!, $startDate: Date, $endDate: Date, $leaveType: String, $reason: String) {
    updateLeaveRequest(requestId: $requestId, startDate: $startDate, endDate: $endDate, leaveType: $leaveType, reason: $reason) {
      id
      startDate
      endDate
      leaveType
      status
    }
  }
`;

// --- Components ---

const MyLeavesTab: React.FC<{ user: any }> = ({ user }) => {
  const { data, loading, error, refetch } = useQuery(GET_MY_LEAVES, {
      fetchPolicy: 'cache-and-network'
  });
  const currentYear = new Date().getFullYear();
  const { data: balanceData, loading: balanceLoading, error: balanceError } = useQuery(GET_MY_BALANCE, {
      variables: { userId: user.id, year: currentYear },
      skip: !user,
      fetchPolicy: 'cache-and-network'
  });
  
  const [open, setOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedReqId, setSelectedReqId] = useState<number | null>(null);

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [leaveType, setLeaveType] = useState('paid_leave');
  const [reason, setReason] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [requestLeave, { loading: submitting }] = useMutation(REQUEST_LEAVE_MUTATION, {
    refetchQueries: [
        { query: GET_MY_LEAVES },
        { query: GET_PENDING_LEAVES },
        { query: GET_ALL_LEAVES }
    ],
    onCompleted: async (data) => {
        if (selectedFile && data.requestLeave) {
            setUploading(true);
            try {
                await uploadFile(data.requestLeave.id, selectedFile);
            } catch (e) {
                console.error(e);
                alert("Заявката е създадена, но качването на файла неуспешно: " + getErrorMessage(e));
            } finally {
                setUploading(false);
                handleClose();
            }
        } else {
            handleClose();
        }
    },
    onError: (err) => setRequestError(err.message)
  });

  const [updateLeave, { loading: updating }] = useMutation(UPDATE_LEAVE_MUTATION, {
    onCompleted: async () => {
        if (selectedFile && selectedReqId) {
             setUploading(true);
             try {
                  await uploadFile(selectedReqId, selectedFile);
              } catch (e) {
                  alert("Качването на файла неуспешно: " + getErrorMessage(e));
              } finally {
                 setUploading(false);
                 handleClose();
                 refetch();
             }
        } else {
            handleClose();
            refetch(); 
        }
    },
    onError: (err) => setRequestError(err.message)
  });

  const [cancelLeave] = useMutation(CANCEL_LEAVE_MUTATION, {
      onCompleted: () => refetch(),
      onError: (err) => alert(err.message)
  });

  const handleClose = () => {
      setOpen(false);
      refetch();
      setStartDate('');
      setEndDate('');
      setReason('');
      setLeaveType('paid_leave');
      setSelectedFile(null);
      setRequestError(null);
      setEditMode(false);
      setSelectedReqId(null);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.target.files && event.target.files[0]) {
          setSelectedFile(event.target.files[0]);
      }
  };

  const handleRequest = async () => {
    if (!startDate || !endDate || !leaveType) {
        setRequestError("Моля, попълнете задължителните полета (дата и тип отпуск).");
        return;
    }

    // Warning for unpaid leave when paid balance exists
    if (leaveType === 'unpaid_leave' && balance && (balance.totalDays - balance.usedDays) > 0) {
        const confirmMsg = `Внимание: Имате ${balance.totalDays - balance.usedDays} дни оставащ ПЛАТЕН отпуск. Сигурни ли сте, че искате да ползвате НЕПЛАТЕН такъв?`;
        if (!window.confirm(confirmMsg)) return;
    }
    
    try {
      if (editMode && selectedReqId) {
          await updateLeave({
              variables: {
                  requestId: selectedReqId,
                  startDate,
                  endDate,
                  leaveType,
                  reason
              }
          });
      } else {
          await requestLeave({
            variables: {
              startDate,
              endDate,
              leaveType,
              reason
            }
          });
      }
    } catch {
      // Handled by onError
    }
  };

  const handleEdit = (req: any) => {
      setEditMode(true);
      setSelectedReqId(req.id);
      setStartDate(req.startDate);
      setEndDate(req.endDate);
      setLeaveType(req.leaveType);
      setReason(req.reason || '');
      setOpen(true);
  };

  const handleCancel = async (id: number) => {
      if (window.confirm("Сигурни ли сте, че искате да прекратите тази заявка? Ако е била одобрена, дните ще бъдат възстановени в баланса ви.")) {
          await cancelLeave({ variables: { requestId: id } });
      }
  };

  const handleDownloadApplication = async (requestId: number) => {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/documents/generate/leave/${requestId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to generate PDF');
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `molba_otpusk_${requestId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (e) { alert(getErrorMessage(e)); }
  };

  if (loading || balanceLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ mt: 2 }}>Грешка при зареждане на заявки: {error.message}</Alert>;
  if (balanceError) return <Alert severity="error" sx={{ mt: 2 }}>Грешка при зареждане на баланс: {balanceError.message}</Alert>;

  const balance = balanceData?.leaveBalance;

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
            <Typography variant="h6">Моите заявки</Typography>
            {balance && (
                <Typography variant="subtitle2" color="text.secondary">
                    Баланс за {currentYear}: {balance.totalDays - balance.usedDays} дни остават (От общо {balance.totalDays})
                </Typography>
            )}
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>
          Нова заявка
        </Button>
      </Box>

      <Grid container spacing={2}>
        {data?.myLeaveRequests.map((req: any) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={req.id}>
            <Card variant="outlined" sx={{ borderRadius: 2, position: 'relative', opacity: req.status === 'cancelled' ? 0.7 : 1 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                    {req.leaveType === 'paid_leave' ? 'Платен отпуск' : 
                     req.leaveType === 'unpaid_leave' ? 'Неплатен отпуск' :
                     req.leaveType === 'sick_leave' ? 'Болничен' : req.leaveType}
                    </Typography>
                    <Chip 
                        label={req.status === 'pending' ? 'Чакащ' : req.status === 'approved' ? 'Одобрен' : req.status === 'cancelled' ? 'Прекратен' : 'Отхвърлен'} 
                        color={req.status === 'approved' ? 'success' : req.status === 'rejected' || req.status === 'cancelled' ? 'default' : 'warning'} 
                        size="small" 
                        variant="outlined"
                    />
                </Box>
                <Typography variant="body2">
                  {formatDate(req.startDate)} — {formatDate(req.endDate)}
                </Typography>
                {req.reason && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Причина: {req.reason}
                    </Typography>
                )}
                {req.adminComment && (
                     <Typography variant="body2" color="info.dark" sx={{ mt: 1, fontStyle: 'italic' }}>
                        Коментар: {req.adminComment}
                    </Typography>
                )}
                
                {req.status !== 'cancelled' && req.status !== 'rejected' && req.status !== 'approved' && (
                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                        <Tooltip title="Редактирай">
                            <IconButton size="small" onClick={() => handleEdit(req)}>
                                <EditIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                        <Tooltip title="Прекрати/Изтрий">
                            <IconButton size="small" color="error" onClick={() => handleCancel(req.id)}>
                                <DeleteIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    </Box>
                )}
                {req.status === 'approved' && (
                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Button 
                            variant="outlined" 
                            size="small" 
                            startIcon={<PictureAsPdfIcon />}
                            onClick={() => handleDownloadApplication(req.id)}
                        >
                            Молба PDF
                        </Button>
                        <Typography variant="caption" color="text.secondary">
                            Одобрен
                        </Typography>
                    </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
        {data?.myLeaveRequests.length === 0 && (
            <Typography color="text.secondary" sx={{ ml: 2 }}>Няма подадени заявки.</Typography>
        )}
      </Grid>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
        <DialogTitle>{editMode ? 'Редакция на заявка' : 'Заявка за отпуск'}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal" variant="outlined">
              <InputLabel id="leave-type-label">Тип отпуск</InputLabel>
              <Select
                labelId="leave-type-label"
                label="Тип отпуск"
                value={leaveType}
                onChange={(e) => setLeaveType(e.target.value)}
              >
                <MenuItem value="paid_leave">Платен годишен отпуск</MenuItem>
                <MenuItem value="unpaid_leave">Неплатен отпуск</MenuItem>
                <MenuItem value="sick_leave">Болничен</MenuItem>
              </Select>
            </FormControl>
          <TextField
            fullWidth
            label="От дата"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            margin="normal"
            variant="outlined"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Начална дата на отпуската/болничния" />
                  </InputAdornment>
                )
              }
            }}
          />
          <TextField
            fullWidth
            label="До дата"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            margin="normal"
            variant="outlined"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Крайна дата на отпуската/болничния" />
                  </InputAdornment>
                )
              }
            }}
          />
          <TextField
            fullWidth
            label="Причина (по избор)"
            multiline
            rows={2}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            margin="normal"
            variant="outlined"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText="Причина/основание за заявката (незадължително)" />
                  </InputAdornment>
                )
              }
            }}
          />
          
          <Box sx={{ mt: 2, p: 2, border: '1px dashed grey', borderRadius: 1, textAlign: 'center' }}>
              <input
                  type="file"
                  hidden
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.jpg,.jpeg,.png"
              />
              <Button 
                  startIcon={<UploadFileIcon />} 
                  onClick={() => fileInputRef.current?.click()}
              >
                  {selectedFile ? 'Смени файл' : 'Прикачи документ (PDF/IMG)'}
              </Button>
              {selectedFile && (
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      Избран: {selectedFile.name}
                  </Typography>
              )}
              <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
                  Автоматично разпознаване на текст (OCR)
              </Typography>
          </Box>

          {requestError && <Alert severity="error" sx={{ width: '100%', mt: 2 }}>{requestError}</Alert>}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="inherit">Отказ</Button>
          <Button variant="contained" onClick={handleRequest} disabled={submitting || updating || uploading}>
              {uploading ? 'Качване...' : (editMode ? 'Запази промените' : 'Изпрати')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

const ApprovalsTab: React.FC = () => {
  const { data, loading, error, refetch } = useQuery(GET_PENDING_LEAVES, {
      fetchPolicy: 'cache-and-network'
  });
  const [approve] = useMutation(APPROVE_LEAVE_MUTATION, {
    refetchQueries: [
      { query: GET_MY_LEAVES },
      { query: GET_ALL_LEAVES },
      { query: GET_PENDING_LEAVES },
      'GetLeaveBalance'
    ]
  });
  const [reject] = useMutation(REJECT_LEAVE_MUTATION, {
    refetchQueries: [
      { query: GET_MY_LEAVES },
      { query: GET_ALL_LEAVES },
      { query: GET_PENDING_LEAVES }
    ]
  });
  const [comment, setComment] = useState('');
  const [topUpMap, setTopUpMap] = useState<{[key: number]: boolean}>({});

  const handleAction = async (id: number, action: 'approve' | 'reject') => {
      const confirmationMessage = `Сигурни ли сте, че искате да ${action === 'approve' ? 'одобрите' : 'отхвърлите'} заявката?`;
      if (!window.confirm(confirmationMessage)) return;
      
      try {
          if (action === 'approve') {
              await approve({ 
                  variables: { 
                      requestId: id, 
                      adminComment: comment,
                      employerTopUp: !!topUpMap[id]
                  } 
              });
          } else {
              await reject({ variables: { requestId: id, adminComment: comment } });
          }
          refetch();
          setComment(''); 
          setTopUpMap({});
      } catch (e) {
          alert(getErrorMessage(e));
      }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ mt: 2 }}>Грешка при зареждане на заявки: {error.message}</Alert>;

  return (
    <Box sx={{ mt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Чакащи заявки</Typography>
            <Button size="small" onClick={() => refetch()}>Опресни</Button>
        </Box>
        <Grid container spacing={2}>
            {data?.pendingLeaveRequests.map((req: any) => (
                <Grid size={{ xs: 12, sm: 6 }} key={req.id}>
                    <Card variant="outlined" sx={{ borderRadius: 2 }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                <Typography variant="subtitle1" fontWeight="bold">
                                    {req.user.firstName} {req.user.lastName} ({req.user.email})
                                </Typography>
                                <Chip 
                                    label={req.leaveType === 'paid_leave' ? 'Платен отпуск' : 
                                           req.leaveType === 'unpaid_leave' ? 'Неплатен отпуск' : req.leaveType} 
                                    color="primary" 
                                    size="small" 
                                    variant="outlined"
                                />
                            </Box>
                            <Typography variant="body1" gutterBottom>
                                {formatDate(req.startDate)} — {formatDate(req.endDate)}
                            </Typography>
                            {req.reason && <Typography variant="body2" color="text.secondary">Причина: {req.reason}</Typography>}
                            
                            {req.leaveType === 'sick_leave' && (
                                <FormControlLabel
                                    control={
                                        <Checkbox 
                                            checked={!!topUpMap[req.id]} 
                                            onChange={(e) => setTopUpMap({...topUpMap, [req.id]: e.target.checked})} 
                                        />
                                    }
                                    label="Работодателят доплаща до 100% от заплатата"
                                    sx={{ mt: 1, color: 'primary.main', display: 'block' }}
                                />
                            )}

                            <TextField 
                                label="Коментар от администратор (по избор)" 
                                multiline 
                                rows={1} 
                                value={comment} 
                                onChange={(e) => setComment(e.target.value)} 
                                fullWidth 
                                margin="normal" 
                                variant="outlined"
                            />
                            
                            <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                                <Button 
                                    variant="contained" 
                                    color="success" 
                                    startIcon={<CheckIcon />}
                                    onClick={() => handleAction(req.id, 'approve')}
                                >
                                    Одобри
                                </Button>
                                <Button 
                                    variant="outlined" 
                                    color="error" 
                                    startIcon={<CloseIcon />}
                                    onClick={() => handleAction(req.id, 'reject')}
                                >
                                    Отхвърли
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            ))}
             {data?.pendingLeaveRequests.length === 0 && (
                <Typography color="text.secondary" sx={{ ml: 2 }}>Няма чакащи заявки.</Typography>
            )}
        </Grid>
    </Box>
  );
};

const AllLeavesTab: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const { data, loading, error, refetch } = useQuery(GET_ALL_LEAVES, {
    variables: { status: statusFilter || null },
    fetchPolicy: 'cache-and-network'
  });
  
  const [cancelLeave] = useMutation(CANCEL_LEAVE_MUTATION, {
      onCompleted: () => refetch(),
      onError: (err) => alert(err.message)
  });

  const handleTerminate = async (id: number) => {
      if (window.confirm("Сигурни ли сте? За одобрени отпуски това ще прекрати отпуската считано от днес и ще възстанови остатъка.")) {
          await cancelLeave({ variables: { requestId: id } });
      }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ mt: 2 }}>Грешка: {error.message}</Alert>;

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip 
            label="Всички" 
            onClick={() => setStatusFilter('')} 
            color={statusFilter === '' ? 'primary' : 'default'} 
            variant={statusFilter === '' ? 'filled' : 'outlined'}
            />
            <Chip 
            label="Чакащи" 
            onClick={() => setStatusFilter('pending')} 
            color={statusFilter === 'pending' ? 'warning' : 'default'}
            variant={statusFilter === 'pending' ? 'filled' : 'outlined'}
            />
            <Chip 
            label="Одобрени" 
            onClick={() => setStatusFilter('approved')} 
            color={statusFilter === 'approved' ? 'success' : 'default'}
            variant={statusFilter === 'approved' ? 'filled' : 'outlined'}
            />
            <Chip 
            label="Отхвърлени" 
            onClick={() => setStatusFilter('rejected')} 
            color={statusFilter === 'rejected' ? 'error' : 'default'}
            variant={statusFilter === 'rejected' ? 'filled' : 'outlined'}
            />
        </Box>
        <Button size="small" onClick={() => refetch()}>Опресни</Button>
      </Box>

      <TableContainer component={Paper} sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <Table size="small">
          <TableHead sx={{ bgcolor: 'rgba(0,0,0,0.02)' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>Служител</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Тип</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Период</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Статус</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Оставащи дни</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Причина</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>Дата на заявяване</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }} align="center">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.allLeaveRequests.map((req: any) => (
              <TableRow key={req.id} hover>
                <TableCell>{req.user.firstName} {req.user.lastName}</TableCell>
                <TableCell>
                  {req.leaveType === 'paid_leave' ? 'Платен' : 
                   req.leaveType === 'unpaid_leave' ? 'Неплатен' : 'Болничен'}
                </TableCell>
                <TableCell>{formatDate(req.startDate)} — {formatDate(req.endDate)}</TableCell>
                <TableCell>
                  <Chip 
                    label={req.status === 'pending' ? 'Чакащ' : req.status === 'approved' ? 'Одобрен' : 'Отхвърлен'} 
                    size="small"
                    color={req.status === 'approved' ? 'success' : req.status === 'rejected' ? 'error' : 'warning'}
                  />
                </TableCell>
                <TableCell>
                    {req.user.leaveBalance ? 
                        (req.user.leaveBalance.totalDays - req.user.leaveBalance.usedDays) 
                        : 'N/A'
                    }
                </TableCell>
                <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {req.reason || '—'}
                </TableCell>
                <TableCell>{formatDate(req.createdAt)}</TableCell>
                <TableCell align="center">
                    {(req.status === 'approved' || req.status === 'pending') && (
                        <Tooltip title="Прекрати / Отмени">
                            <IconButton size="small" color="error" onClick={() => handleTerminate(req.id)}>
                                <DeleteIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

interface Props {
  tab?: string;
}

const LeavesPage: React.FC<Props> = ({ tab }) => {
  const { data, loading, error } = useQuery(GET_MY_LEAVES, { fetchPolicy: 'cache-and-network' }); 
  
  const user = data?.me;

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error" sx={{ mt: 2 }}>Грешка при зареждане на данни: {error.message}</Alert>;
  if (!user) return <Navigate to="/login" replace />;

  const isAdmin = user?.role?.name === 'admin' || user?.role?.name === 'super_admin';

  const tabs = [
    { label: 'Моите заявки', path: '/leaves/my-requests' },
    ...(isAdmin ? [{ label: 'Одобрения', path: '/leaves/approvals' }] : []),
    ...(isAdmin ? [{ label: 'Всички заявки', path: '/leaves/all' }] : []),
  ];

  const defaultTab = '/leaves/my-requests';

  return (
    <TabbedPage tabs={tabs} defaultTabPath={defaultTab}>
      {tab === 'my-requests' && user && <MyLeavesTab user={user} />}
      {tab === 'approvals' && isAdmin && <ApprovalsTab />}
      {tab === 'all' && isAdmin && <AllLeavesTab />}
    </TabbedPage>
  );
};

export default LeavesPage;
