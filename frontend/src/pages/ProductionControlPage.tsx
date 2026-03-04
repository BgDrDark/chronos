import React, { useState, useMemo } from 'react';
import {
  Container, Typography, Box, Paper, Grid, Button, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Select, MenuItem, FormControl, InputLabel, CircularProgress,
  Alert, IconButton, Autocomplete
} from '@mui/material';
import {
  AddShoppingCart as OrderIcon,
  SwapVert as SwapIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import { ME_QUERY } from '../graphql/queries';

const GET_PRODUCTION_ORDERS_FOR_DAY = gql`
  query GetProductionOrdersForDay($date: String) {
    productionOrdersForDay(date: $date) {
      id
      quantity
      dueDate
      productionDeadline
      status
      notes
      recipe {
        id
        name
      }
      tasks {
        id
        name
        status
        workstation {
          id
          name
        }
        startedAt
        completedAt
      }
    }
    workstations {
      id
      name
    }
  }
`;

const GET_OVERDUE_ORDERS = gql`
  query GetOverdueOrders {
    overdueProductionOrders {
      id
      quantity
      dueDate
      productionDeadline
      status
      notes
      recipe {
        id
        name
      }
      tasks {
        id
        name
        status
        workstation {
          id
          name
        }
      }
    }
  }
`;

const REASSIGN_TASK_WORKSTATION = gql`
  mutation ReassignTaskWorkstation($taskId: Int!, $newWorkstationId: Int!) {
    reassignTaskWorkstation(taskId: $taskId, newWorkstationId: $newWorkstationId) {
      id
      status
    }
  }
`;

const UPDATE_ORDER_QUANTITY = gql`
  mutation UpdateOrderQuantity($orderId: Int!, $quantity: Float!) {
    updateProductionOrderQuantity(orderId: $orderId, quantity: $quantity) {
      id
      quantity
    }
  }
`;

const ProductionControlPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [showOverdue, setShowOverdue] = useState(false);
  const [selectedWorkstation, setSelectedWorkstation] = useState<number | null>(null);
  const [reassignDialog, setReassignDialog] = useState<{open: boolean, taskId: number | null, currentWorkstation: string}>({
    open: false, taskId: null, currentWorkstation: ''
  });
  const [newWorkstationId, setNewWorkstationId] = useState<number | ''>('');
  const [quantityDialog, setQuantityDialog] = useState<{open: boolean, orderId: number | null, currentQuantity: number, recipeName: string}>({
    open: false, orderId: null, currentQuantity: 0, recipeName: ''
  });
  const [dailyQuantity, setDailyQuantity] = useState<string>('');

  const { data, loading, error, refetch } = useQuery(showOverdue ? GET_OVERDUE_ORDERS : GET_PRODUCTION_ORDERS_FOR_DAY, {
    variables: { date: selectedDate },
    skip: showOverdue
  });

  const [reassignTask, { loading: reassignLoading }] = useMutation(REASSIGN_TASK_WORKSTATION);
  const [updateQuantity, { loading: updateQuantityLoading }] = useMutation(UPDATE_ORDER_QUANTITY);

  const allOrders = showOverdue ? data?.overdueProductionOrders : data?.productionOrdersForDay;
  const workstations = data?.workstations || [];

  // Filter orders by workstation
  const orders = useMemo(() => {
    if (!allOrders) return [];
    if (!selectedWorkstation) return allOrders;
    return allOrders.filter((order: any) => 
      order.tasks?.some((task: any) => task.workstation.id === selectedWorkstation)
    );
  }, [allOrders, selectedWorkstation]);

  const handleReassign = async () => {
    if (!reassignDialog.taskId || !newWorkstationId) return;
    try {
      await reassignTask({
        variables: {
          taskId: reassignDialog.taskId,
          newWorkstationId
        }
      });
      setReassignDialog({ open: false, taskId: null, currentWorkstation: '' });
      setNewWorkstationId('');
      refetch();
    } catch (err) {
      console.error(err);
      alert('Грешка при преместване');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'default';
      case 'ready': return 'info';
      case 'in_progress': return 'warning';
      case 'completed': return 'success';
      case 'confirmed': return 'success';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'Чака';
      case 'ready': return 'Готова';
      case 'in_progress': return 'В работа';
      case 'completed': return 'Приключена';
      case 'confirmed': return 'Потвърдена';
      default: return status;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          Контрол Производство
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Управление на поръчките за деня
        </Typography>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, sm: 4, md: 2 }}>
            <TextField
              type="date"
              label="Дата"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 4, md: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Отдел/Станция</InputLabel>
              <Select
                value={selectedWorkstation || ''}
                label="Отдел/Станция"
                onChange={(e) => setSelectedWorkstation(e.target.value as number || null)}
              >
                <MenuItem value="">Всички</MenuItem>
                {workstations.map((ws: any) => (
                  <MenuItem key={ws.id} value={ws.id}>{ws.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 4, md: 2 }}>
            <Button
              variant={showOverdue ? 'contained' : 'outlined'}
              color="error"
              onClick={() => setShowOverdue(!showOverdue)}
              startIcon={<WarningIcon />}
              fullWidth
            >
              Просрочени
            </Button>
          </Grid>
          <Grid size={{ xs: 12, sm: 4, md: 2 }}>
            <Button
              variant="outlined"
              onClick={() => refetch()}
              startIcon={<RefreshIcon />}
              fullWidth
            >
              Обнови
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Грешка при зареждане: {error.message}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>№</TableCell>
              <TableCell>Продукт</TableCell>
              <TableCell align="right">К-во</TableCell>
              <TableCell>Произв. срок</TableCell>
              <TableCell>Краен срок</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Задачи</TableCell>
              <TableCell>Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders?.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary">
                    Няма поръчки за {showOverdue ? 'просрочени' : selectedDate}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {orders?.map((order: any) => (
              <TableRow 
                key={order.id}
                sx={{ 
                  backgroundColor: order.productionDeadline && new Date(order.productionDeadline) < new Date() ? 'rgba(244, 67, 54, 0.1)' : 'inherit'
                }}
              >
                <TableCell>{order.id}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{order.recipe.name}</TableCell>
                <TableCell align="right">{order.quantity}</TableCell>
                <TableCell>
                  {order.productionDeadline ? (
                    <Chip 
                      label={new Date(order.productionDeadline).toLocaleDateString('bg-BG')}
                      color={new Date(order.productionDeadline) < new Date() ? 'error' : 'default'}
                      size="small"
                    />
                  ) : '-'}
                </TableCell>
                <TableCell>
                  {new Date(order.dueDate).toLocaleDateString('bg-BG')}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={getStatusLabel(order.status)}
                    color={getStatusColor(order.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {order.tasks?.map((task: any) => (
                    <Box key={task.id} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Chip 
                        label={task.workstation.name}
                        size="small"
                        variant="outlined"
                      />
                      <Chip 
                        label={getStatusLabel(task.status)}
                        color={getStatusColor(task.status) as any}
                        size="small"
                      />
                      {task.status !== 'completed' && (
                        <IconButton 
                          size="small"
                          onClick={() => setReassignDialog({ 
                            open: true, 
                            taskId: task.id, 
                            currentWorkstation: task.workstation.name 
                          })}
                        >
                          <SwapIcon fontSize="small" />
                        </IconButton>
                      )}
                    </Box>
                  ))}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button 
                      size="small" 
                      startIcon={<EditIcon />}
                      onClick={() => setQuantityDialog({
                        open: true,
                        orderId: order.id,
                        currentQuantity: order.quantity,
                        recipeName: order.recipe.name
                      })}
                    >
                      К-во
                    </Button>
                    <Button size="small" startIcon={<CheckIcon />}>
                      Потвърди
                    </Button>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={reassignDialog.open} onClose={() => setReassignDialog({ open: false, taskId: null, currentWorkstation: '' })}>
        <DialogTitle>Преместване на задача</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Текуща станция: <b>{reassignDialog.currentWorkstation}</b>
          </Typography>
          <FormControl fullWidth>
            <InputLabel>Нова станция</InputLabel>
            <Select
              value={newWorkstationId}
              label="Нова станция"
              onChange={(e) => setNewWorkstationId(e.target.value as number)}
            >
              {workstations.map((ws: any) => (
                <MenuItem key={ws.id} value={ws.id}>{ws.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReassignDialog({ open: false, taskId: null, currentWorkstation: '' })}>
            Отказ
          </Button>
          <Button 
            onClick={handleReassign} 
            variant="contained"
            disabled={!newWorkstationId || reassignLoading}
          >
            {reassignLoading ? '...' : 'Премести'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Quantity Dialog */}
      <Dialog open={quantityDialog.open} onClose={() => setQuantityDialog({ open: false, orderId: null, currentQuantity: 0, recipeName: '' })}>
        <DialogTitle>Промяна на количество за деня</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Рецепта: <b>{quantityDialog.recipeName}</b><br />
            Общо количество: <b>{quantityDialog.currentQuantity}</b>
          </Typography>
          <TextField
            fullWidth
            type="number"
            label="Количество за днес"
            value={dailyQuantity}
            onChange={(e) => setDailyQuantity(e.target.value)}
            helperText="Въведете колко ще се произведе днес. Останалите ще бъдат за утре."
            inputProps={{ min: 1, max: quantityDialog.currentQuantity }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQuantityDialog({ open: false, orderId: null, currentQuantity: 0, recipeName: '' })}>
            Отказ
          </Button>
          <Button 
            variant="contained"
            disabled={!dailyQuantity || parseInt(dailyQuantity) <= 0 || parseInt(dailyQuantity) > quantityDialog.currentQuantity || updateQuantityLoading}
            onClick={async () => {
              try {
                await updateQuantity({
                  variables: {
                    orderId: quantityDialog.orderId,
                    quantity: parseFloat(dailyQuantity)
                  }
                });
                setQuantityDialog({ open: false, orderId: null, currentQuantity: 0, recipeName: '' });
                setDailyQuantity('');
                refetch();
              } catch (err) {
                console.error(err);
                alert('Грешка при обновяване');
              }
            }}
          >
            {updateQuantityLoading ? '...' : 'Запази'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProductionControlPage;
