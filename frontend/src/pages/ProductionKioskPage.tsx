import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Typography, Paper, Grid, Button, Chip, IconButton,
  Card, CardContent, CircularProgress, Container,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Avatar, Alert
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  CheckCircle as DoneIcon,
  Timer as TimerIcon,
  ChevronLeft as BackIcon,
  Warning as WarningIcon,
  QrCodeScanner as ScanIcon,
  Logout as ExitIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { useQuery, useMutation, gql, useLazyQuery } from '@apollo/client';
import { UPDATE_TASK_STATUS, SCRAP_TASK, MARK_TASK_SCRAP } from '../graphql/confectioneryMutations';

const GENERATE_LABEL = gql`
  query GenerateLabel($orderId: Int!) {
    generateLabel(orderId: $orderId) {
      productName
      batchNumber
      productionDate
      expiryDate
      allergens
      storageConditions
      qrCodeContent
      quantity
    }
  }
`;

const GET_WORKSTATIONS = gql`
  query GetWorkstations {
    workstations {
      id
      name
      description
    }
  }
`;

const GET_TERMINAL_ORDERS = gql`
  query GetTerminalOrders($workstationId: Int!) {
    terminalOrders(workstationId: $workstationId) {
      id
      orderNumber
      productName
      quantity
      status
      recipeName
      instructions
      tasks {
        id
        name
        quantity
        status
      }
    }
  }
`;

interface Employee {
  employee_id: number;
  first_name: string;
  last_name: string;
  profile_picture?: string;
}

const ProductionKioskPage: React.FC = () => {
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [qrInput, setQrInput] = useState('');
  const [qrError, setQrError] = useState('');
  const [identifying, setIdentifying] = useState(false);
  const [selectedStation, setSelectedStation] = useState<number | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [activeTask, setActiveTask] = useState<any>(null);
  const [taskStartTime, setTaskStartTime] = useState<Date | null>(null);
  const [labelData, setLabelData] = useState<any>(null);
  const [scrapDialog, setScrapDialog] = useState<{open: boolean, taskId: number | null, taskName: string, maxQuantity: number}>({
    open: false, taskId: null, taskName: '', maxQuantity: 0
  });
  const [scrapQuantity, setScrapQuantity] = useState<string>('');
  const [scrapReason, setScrapReason] = useState<string>('');
  const [terminalId] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const urlTerminal = params.get('terminal');
    if (urlTerminal) {
      return `terminal_${urlTerminal}`;
    }
    return `terminal_${Math.random().toString(36).substr(2, 9)}`;
  });
  
  const [terminalDisplayName, setTerminalDisplayName] = useState<string>('');
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlTerminal = params.get('terminal');
    if (urlTerminal) {
      setTerminalDisplayName(`Цех ${urlTerminal}`);
    }
  }, []);
  
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: wsData, loading: wsLoading } = useQuery(GET_WORKSTATIONS);
  
  const { data: orderData, loading: ordersLoading, refetch: refetchOrders } = useQuery(GET_TERMINAL_ORDERS, {
    variables: { workstationId: selectedStation },
    skip: !selectedStation,
    pollInterval: 3000,
  });
  
  const [fetchLabel] = useLazyQuery(GENERATE_LABEL, {
    onCompleted: (data) => setLabelData(data.generateLabel)
  });

  const [updateStatus] = useMutation(UPDATE_TASK_STATUS);
  const [scrapTask] = useMutation(SCRAP_TASK);
  const [markScrap] = useMutation(MARK_TASK_SCRAP);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleIdentify = async () => {
    if (!qrInput.trim()) return;
    
    setIdentifying(true);
    setQrError('');
    
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/terminal/identify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qr_token: qrInput.trim() })
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Невалиден QR код');
      }
      
      const data = await response.json();
      setEmployee(data);
      setQrInput('');
    } catch (err: any) {
      setQrError(err.message || 'Грешка при идентификация');
    } finally {
      setIdentifying(false);
    }
  };

  const handleLogout = () => {
    setEmployee(null);
    setSelectedStation(null);
    setSelectedOrder(null);
    setActiveTask(null);
  };

  const handleStartTask = (task: any) => {
    setActiveTask(task);
    setTaskStartTime(new Date());
  };

  const handleCompleteTask = async () => {
    if (!activeTask) return;
    try {
      await updateStatus({ variables: { id: activeTask.id, status: 'completed' } });
      setActiveTask(null);
      setTaskStartTime(null);
      refetchOrders();
    } catch (err) {
      console.error(err);
    }
  };

  const handleScrapTask = async () => {
    if (!scrapDialog.taskId || !scrapQuantity) return;
    const qty = parseFloat(scrapQuantity);
    if (qty <= 0 || qty > scrapDialog.maxQuantity) {
      alert('Невалидно количество');
      return;
    }
    try {
      await scrapTask({ 
        variables: { 
          input: { 
            task_id: scrapDialog.taskId, 
            quantity: qty, 
            reason: scrapReason || null 
          } 
        } 
      });
      setScrapDialog({ open: false, taskId: null, taskName: '', maxQuantity: 0 });
      refetchOrders();
    } catch (err) {
      console.error(err);
      alert('Грешка при бракуване');
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      if (taskStartTime) {
        setTaskStartTime(new Date(taskStartTime));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [taskStartTime]);

  const getElapsedTime = () => {
    if (!taskStartTime) return '00:00';
    const diff = Math.floor((Date.now() - taskStartTime.getTime()) / 1000);
    const mins = Math.floor(diff / 60).toString().padStart(2, '0');
    const secs = (diff % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const renderHeader = (title: string) => (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      p: 2,
      bgcolor: '#1976d2',
      color: 'white'
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {employee && (
          <Avatar sx={{ mr: 2, bgcolor: 'white', color: '#1976d2' }}>
            {employee.profile_picture && (employee.profile_picture.startsWith('/') || employee.profile_picture.startsWith('http')) ? (
              <img 
                src={employee.profile_picture} 
                alt="" 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            ) : (
              <PersonIcon />
            )}
          </Avatar>
        )}
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{title}</Typography>
          {employee && (
            <Typography variant="body2">{employee.first_name} {employee.last_name}</Typography>
          )}
        </Box>
      </Box>
      <Button
        variant="contained"
        color="error"
        startIcon={<ExitIcon />}
        onClick={handleLogout}
        sx={{ fontWeight: 'bold' }}
      >
        ИЗХОД
      </Button>
    </Box>
  );

  if (!employee) {
    return (
      <Box sx={{ 
        minHeight: '100vh', 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center',
        bgcolor: '#f5f5f5',
        p: 3
      }}>
        <Card sx={{ maxWidth: 500, width: '100%', p: 4, borderRadius: 4, textAlign: 'center' }}>
          <ScanIcon sx={{ fontSize: 80, color: '#1976d2', mb: 2 }} />
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
            ИДЕНТИФИКАЦИЯ
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Сканирайте вашия QR код
          </Typography>
          
          <TextField
            fullWidth
            inputRef={inputRef}
            value={qrInput}
            onChange={(e) => setQrInput(e.target.value)}
            placeholder="Въведете или сканирайте QR код"
            onKeyPress={(e) => e.key === 'Enter' && handleIdentify()}
            sx={{ mb: 2 }}
            disabled={identifying}
          />
          
          {qrError && (
            <Alert severity="error" sx={{ mb: 2 }}>{qrError}</Alert>
          )}
          
          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleIdentify}
            disabled={identifying || !qrInput.trim()}
            sx={{ height: 60, fontSize: '1.2rem', borderRadius: 3 }}
          >
            {identifying ? <CircularProgress color="inherit" /> : 'ВХОД'}
          </Button>
        </Card>
      </Box>
    );
  }

  if (!selectedStation) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
        {renderHeader(terminalDisplayName || 'Избор на станция')}
        <Container maxWidth="md" sx={{ textAlign: 'center', pt: 6 }}>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
            Избери работна станция
          </Typography>
          {wsLoading ? (
            <CircularProgress sx={{ mt: 4 }} />
          ) : (
            <Grid container spacing={3} sx={{ mt: 4 }}>
              {wsData?.workstations.map((ws: any) => (
                <Grid size={{ xs: 12, sm: 6, md: 4 }} key={ws.id}>
                  <Card 
                    sx={{ 
                      height: 180, 
                      cursor: 'pointer',
                      transition: 'transform 0.2s',
                      '&:hover': { transform: 'scale(1.02)' },
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      alignItems: 'center'
                    }}
                    onClick={() => setSelectedStation(ws.id)}
                  >
                    <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{ws.name}</Typography>
                    {ws.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1, px: 2 }}>
                        {ws.description}
                      </Typography>
                    )}
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Container>
      </Box>
    );
  }

  const currentWorkstation = wsData?.workstations?.find((w: any) => w.id === selectedStation);
  const orders = orderData?.terminalOrders || [];

  if (activeTask) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5', display: 'flex', flexDirection: 'column' }}>
        {renderHeader(activeTask.name)}
        <Box sx={{ flex: 1, p: 3, display: 'flex', flexDirection: 'column' }}>
          <Card sx={{ flex: 1, borderRadius: 4, p: 3 }}>
            <Typography variant="h4" sx={{ fontWeight: 'bold', textAlign: 'center', mb: 2 }}>
              {activeTask.name}
            </Typography>
            
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 4 }}>
              <TimerIcon sx={{ fontSize: 40, mr: 1, color: '#4caf50' }} />
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#4caf50' }}>
                {getElapsedTime()}
              </Typography>
            </Box>

            {activeTask.instructions && (
              <Paper sx={{ p: 3, bgcolor: '#fffde7', borderRadius: 2, mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>Инструкции:</Typography>
                <Typography variant="body1">{activeTask.instructions}</Typography>
              </Paper>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">
                Поръчка: <b>{selectedOrder?.productName}</b> (Qty: {activeTask.quantity})
              </Typography>
            </Box>
          </Card>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 2 }}>
            <Button
              variant="contained"
              color="error"
              size="large"
              startIcon={<WarningIcon />}
              onClick={() => setScrapDialog({ 
                open: true, 
                taskId: activeTask.id, 
                taskName: activeTask.name, 
                maxQuantity: activeTask.quantity 
              })}
              sx={{ height: 80, fontSize: '1.5rem', borderRadius: 3 }}
            >
              БРАК
            </Button>
            <Button
              variant="contained"
              color="success"
              size="large"
              startIcon={<DoneIcon />}
              onClick={handleCompleteTask}
              sx={{ height: 80, fontSize: '1.5rem', borderRadius: 3 }}
            >
              ЗАВЪРШИ
            </Button>
          </Box>
        </Box>

        <Dialog open={scrapDialog.open} onClose={() => setScrapDialog({ ...scrapDialog, open: false })} maxWidth="sm" fullWidth>
          <DialogTitle>Брак</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Количество"
              type="number"
              value={scrapQuantity}
              onChange={(e) => setScrapQuantity(e.target.value)}
              sx={{ mb: 2 }}
              inputProps={{ min: 1, max: scrapDialog.maxQuantity }}
            />
            <TextField
              fullWidth
              label="Причина"
              multiline
              rows={2}
              value={scrapReason}
              onChange={(e) => setScrapReason(e.target.value)}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setScrapDialog({ ...scrapDialog, open: false })}>Отказ</Button>
            <Button onClick={handleScrapTask} variant="contained" color="error">Бракувай</Button>
          </DialogActions>
        </Dialog>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      {renderHeader(terminalDisplayName || currentWorkstation?.name || 'Поръчки')}
      <Container maxWidth="lg" sx={{ pt: 4, pb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={() => setSelectedStation(null)} sx={{ mr: 2 }}>
            <BackIcon fontSize="large" />
          </IconButton>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            {currentWorkstation?.name} - Поръчки
          </Typography>
        </Box>

        {ordersLoading ? (
          <CircularProgress />
        ) : orders.length === 0 ? (
          <Typography variant="h5" color="text.secondary" textAlign="center" sx={{ mt: 4 }}>
            Няма активни поръчки за тази станция
          </Typography>
        ) : (
          <Grid container spacing={3}>
            {orders.map((order: any) => (
              <Grid size={{ xs: 12, md: 6 }} key={order.id}>
                <Card sx={{ borderRadius: 4 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{order.productName}</Typography>
                      <Chip 
                        label={order.status === 'in_progress' ? 'В работа' : 'Готова'} 
                        color={order.status === 'in_progress' ? 'primary' : 'success'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Поръчка №{order.orderNumber} | Количество: {order.quantity}
                    </Typography>
                    {order.instructions && (
                      <Alert severity="info" sx={{ mt: 2 }}>{order.instructions}</Alert>
                    )}
                    
                    <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Задачи:</Typography>
                    {order.tasks?.map((task: any) => (
                      <Box key={task.id} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1, bgcolor: '#f5f5f5', borderRadius: 1, mb: 1 }}>
                        <Box>
                          <Typography variant="body1"><b>{task.name}</b></Typography>
                          <Typography variant="body2" color="text.secondary">Количество: {task.quantity}</Typography>
                        </Box>
                        {task.status === 'completed' ? (
                          <Chip label="Завършена" color="success" size="small" />
                        ) : (
                          <Button 
                            variant="contained" 
                            startIcon={<StartIcon />}
                            onClick={() => {
                              setSelectedOrder(order);
                              handleStartTask(task);
                            }}
                          >
                            СТАРТ
                          </Button>
                        )}
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </Box>
  );
};

export default ProductionKioskPage;
