import React, { useState } from 'react';
import {
  Container, Typography, Box, Paper, Button, Grid, TextField, MenuItem,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Dialog, DialogTitle, DialogContent, DialogActions, CircularProgress,
  List, ListItem, ListItemText, Divider, Select
} from '@mui/material';
import {
  AddShoppingCart as OrderIcon,
  Visibility as ViewIcon,
  QrCode as QrCodeIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import { CREATE_PRODUCTION_ORDER, UPDATE_PRODUCTION_ORDER_STATUS, CONFIRM_PRODUCTION_ORDER } from '../graphql/confectioneryMutations';
import { ME_QUERY } from '../graphql/queries';
import { QRCodeSVG } from 'qrcode.react';

const GENERATE_LABEL = gql`
  mutation GenerateLabel($orderId: Int!) {
    generateLabel(orderId: $orderId) {
      qrCodeContent
      batchNumber
      productName
      quantity
      expiryDate
    }
  }
`;

const GET_ORDERS_AND_RECIPES = gql`
  query GetOrdersAndRecipes {
    productionOrders {
      id
      quantity
      dueDate
      productionDeadline
      status
      notes
      confirmedAt
      confirmedBy
      recipe {
        id
        name
        ingredients {
          quantityNet
          ingredient {
            name
            unit
            currentStock
          }
        }
      }
      tasks {
        id
        status
        workstation {
          name
        }
        startedAt
        completedAt
      }
    }
    recipes {
      id
      name
    }
  }
`;

const GET_PRODUCTION_RECORD = gql`
  query GetProductionRecord($orderId: Int!) {
    productionRecordByOrder(orderId: $orderId) {
      id
      orderId
      confirmedAt
      expiryDate
      ingredients {
        id
        ingredientName
        batchNumber
        expiryDate
        quantityUsed
        unit
      }
      workers {
        id
        userName
        workstationName
        startedAt
        completedAt
      }
    }
  }
`;

const OrdersPage: React.FC = () => {
  const [openModal, setOpenModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [labelData, setLabelData] = useState<any>(null);
  const [historyOrderId, setHistoryOrderId] = useState<number | null>(null);
  const { data, loading, error, refetch } = useQuery(GET_ORDERS_AND_RECIPES);
  const { data: recordData } = useQuery(GET_PRODUCTION_RECORD, {
    variables: { orderId: historyOrderId },
    skip: !historyOrderId
  });
  const [createOrder] = useMutation(CREATE_PRODUCTION_ORDER);
  const [updateOrderStatus] = useMutation(UPDATE_PRODUCTION_ORDER_STATUS);
  const [generateLabel] = useMutation(GENERATE_LABEL);
  const [confirmOrder] = useMutation(CONFIRM_PRODUCTION_ORDER);

  const handleGenerateLabel = async (orderId: number) => {
    try {
      const result = await generateLabel({ variables: { orderId } });
      setLabelData(result.data.generateLabel);
    } catch (err) {
      console.error(err);
    }
  };

  const [form, setForm] = useState({
    recipeId: '',
    quantity: '1',
    dueDate: '',
    dueTime: '12:00',
    notes: ''
  });

  const { data: userData } = useQuery(ME_QUERY);
  const user = userData?.me;

  const handleSubmit = async () => {
    if (!user?.companyId) return;
    try {
      // Combine date and time
      const dueDateTime = `${form.dueDate}T${form.dueTime}:00Z`;

      await createOrder({
        variables: {
          input: {
            recipeId: parseInt(form.recipeId),
            quantity: parseFloat(form.quantity),
            dueDate: dueDateTime,
            notes: form.notes,
            companyId: user.companyId
          }
        }
      });
      setOpenModal(false);
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success';
      case 'confirmed': return 'info';
      case 'awaiting_stock': return 'warning';
      case 'in_progress': return 'primary';
      case 'completed': return 'info';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ready': return 'Готова за работа';
      case 'confirmed': return 'Потвърдена';
      case 'awaiting_stock': return 'Чака продукти';
      case 'in_progress': return 'В производство';
      case 'completed': return 'Завършена';
      default: return status;
    }
  };

  const handleUpdateOrderStatus = async (orderId: number, newStatus: string) => {
    try {
      await updateOrderStatus({
        variables: {
          id: orderId,
          status: newStatus
        }
      });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleConfirmOrder = async (orderId: number) => {
    try {
      await confirmOrder({ variables: { id: orderId } });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  if (error) return <Typography color="error">Грешка: {error.message}</Typography>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Поръчки за производство
        </Typography>
        <Button variant="contained" startIcon={<OrderIcon />} onClick={() => setOpenModal(true)}>
          Нова Поръчка
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>№</TableCell>
              <TableCell>Продукт</TableCell>
              <TableCell align="right">К-во</TableCell>
              <TableCell>Краен срок</TableCell>
              <TableCell>Произв.</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Бележки</TableCell>
              <TableCell>Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.productionOrders.map((order: any) => (
              <TableRow key={order.id}>
                <TableCell>{order.id}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{order.recipe.name}</TableCell>
                <TableCell align="right">{order.quantity}</TableCell>
                <TableCell>
                  {new Date(order.dueDate).toLocaleString('bg-BG', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                </TableCell>
                <TableCell>
                  {order.productionDeadline ? (
                    <Chip 
                      label={`Произв: ${new Date(order.productionDeadline).toLocaleDateString('bg-BG', { day: '2-digit', month: '2-digit' })}`}
                      color={new Date(order.productionDeadline) < new Date() ? 'error' : 'default'}
                      size="small" 
                    />
                  ) : '-'}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={getStatusLabel(order.status)} 
                    color={getStatusColor(order.status) as any} 
                    size="small" 
                  />
                </TableCell>
                <TableCell>{order.notes}</TableCell>
                <TableCell>
                  <Button size="small" startIcon={<ViewIcon />} onClick={() => setSelectedOrder(order)}>
                    Детайли
                  </Button>
                  {order.status === 'confirmed' && (
                    <Button size="small" startIcon={<HistoryIcon />} onClick={() => setHistoryOrderId(order.id)}>
                      История
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {data?.productionOrders.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">Няма активни поръчки.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Modal: Нова Поръчка */}
      <Dialog open={openModal} onClose={() => setOpenModal(false)} fullWidth maxWidth="sm">
        <DialogTitle>Приемане на нова поръчка</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Избери десерт"
                value={form.recipeId}
                onChange={e => setForm({...form, recipeId: e.target.value})}
              >
                {data?.recipes.map((r: any) => (
                  <MenuItem key={r.id} value={r.id}>{r.name}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Количество (брой/кг)"
                type="number"
                value={form.quantity}
                onChange={e => setForm({...form, quantity: e.target.value})}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Дата за издаване"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={form.dueDate}
                onChange={e => setForm({...form, dueDate: e.target.value})}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Час за издаване"
                type="time"
                InputLabelProps={{ shrink: true }}
                value={form.dueTime}
                onChange={e => setForm({...form, dueTime: e.target.value})}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Бележки (надпис, цвят, изисквания)"
                multiline
                rows={3}
                value={form.notes}
                onChange={e => setForm({...form, notes: e.target.value})}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenModal(false)}>Отказ</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={!form.recipeId || !form.dueDate}
          >
            Приеми Поръчка
          </Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Детайли на Поръчката */}
      <Dialog open={!!selectedOrder} onClose={() => setSelectedOrder(null)} fullWidth maxWidth="md">
        <DialogTitle>Поръчка №{selectedOrder?.id} - {selectedOrder?.recipe?.name}</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="textSecondary">Количество</Typography>
              <Typography variant="h6">{selectedOrder?.quantity}</Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="textSecondary">Краен срок</Typography>
              <Typography variant="h6">
                {selectedOrder?.dueDate ? new Date(selectedOrder.dueDate).toLocaleString('bg-BG') : '-'}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle2" color="textSecondary">Статус</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Select
                  value={selectedOrder?.status}
                  onChange={(e) => handleUpdateOrderStatus(selectedOrder?.id, e.target.value)}
                  sx={{ minWidth: 200 }}
                >
                  <MenuItem value="awaiting_stock">Чака продукти</MenuItem>
                  <MenuItem value="ready">Готова за работа</MenuItem>
                  <MenuItem value="confirmed">Потвърдена</MenuItem>
                  <MenuItem value="in_progress">В производство</MenuItem>
                  <MenuItem value="completed">Завършена</MenuItem>
                </Select>
                {selectedOrder?.status === 'ready' && (
                  <Button 
                    variant="contained" 
                    color="success"
                    onClick={() => handleConfirmOrder(selectedOrder?.id)}
                  >
                    Потвърди за транспорт
                  </Button>
                )}
              </Box>
            </Grid>
            {selectedOrder?.notes && (
              <Grid size={{ xs: 12 }}>
                <Typography variant="subtitle2" color="textSecondary">Бележки</Typography>
                <Typography>{selectedOrder.notes}</Typography>
              </Grid>
            )}

            <Grid size={{ xs: 12 }}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Необходими Суровини</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Суровина</TableCell>
                    <TableCell align="right">Необходимо</TableCell>
                    <TableCell align="right">Наличност</TableCell>
                    <TableCell align="right">Статус</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedOrder?.recipe?.ingredients?.map((ing: any, idx: number) => {
                    const needed = ing.quantityNet * selectedOrder.quantity;
                    const available = ing.ingredient.currentStock || 0;
                    const isEnough = available >= needed;
                    return (
                      <TableRow key={idx}>
                        <TableCell>{ing.ingredient.name}</TableCell>
                        <TableCell align="right">{needed} {ing.ingredient.unit}</TableCell>
                        <TableCell align="right">{available} {ing.ingredient.unit}</TableCell>
                        <TableCell>
                          <Chip 
                            label={isEnough ? 'Достатъчно' : 'Няма'} 
                            color={isEnough ? 'success' : 'error'} 
                            size="small" 
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Задачи</Typography>
              {selectedOrder?.tasks?.length > 0 ? (
                <List>
                  {selectedOrder.tasks.map((task: any, idx: number) => (
                    <ListItem key={idx} sx={{ borderBottom: '1px solid #eee' }}>
                      <ListItemText 
                        primary={`${task.workstation?.name || 'Станция ' + (idx + 1)}`}
                        secondary={
                          task.status === 'pending' ? 'Чака' :
                          task.status === 'in_progress' ? `В прогрес от: ${new Date(task.startedAt).toLocaleTimeString('bg-BG')}` :
                          task.status === 'completed' ? `Приключена: ${new Date(task.completedAt).toLocaleString('bg-BG')}` : ''
                        }
                      />
                      <Chip 
                        label={task.status === 'pending' ? 'Чака' : 
                               task.status === 'in_progress' ? 'В прогрес' : 
                               task.status === 'completed' ? 'Приключена' : task.status}
                        color={task.status === 'completed' ? 'success' : 
                               task.status === 'in_progress' ? 'primary' : 'default'}
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">Няма задачи за тази поръчка</Typography>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          {selectedOrder?.status === 'completed' && (
            <Button 
              startIcon={<QrCodeIcon />} 
              onClick={() => handleGenerateLabel(selectedOrder.id)}
              variant="outlined"
            >
              Генерирай етикет
            </Button>
          )}
          <Button onClick={() => { setSelectedOrder(null); setLabelData(null); }}>Затвори</Button>
        </DialogActions>
      </Dialog>

      {/* Label Preview Dialog */}
      {labelData && (
        <Dialog open={!!labelData} onClose={() => setLabelData(null)} maxWidth="xs" fullWidth>
          <DialogTitle>Етикет за поръчка</DialogTitle>
          <DialogContent sx={{ textAlign: 'center' }}>
            <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
              <Typography variant="h6">{labelData.productName}</Typography>
              <Typography>Партида: {labelData.batchNumber}</Typography>
              <Typography>Количество: {labelData.quantity}</Typography>
              <Typography>Годност: {labelData.expiryDate}</Typography>
              <Box sx={{ mt: 2, p: 1, bgcolor: 'white', border: '1px dashed #999', display: 'inline-block' }}>
                <QRCodeSVG value={labelData.qrCodeContent || `ORDER:${labelData.batchNumber}`} size={128} />
              </Box>
            </Paper>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => window.print()}>Принтирай</Button>
            <Button onClick={() => setLabelData(null)}>Затвори</Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Production History Dialog */}
      <Dialog open={!!historyOrderId} onClose={() => setHistoryOrderId(null)} maxWidth="md" fullWidth>
        <DialogTitle>История на производство</DialogTitle>
        <DialogContent dividers>
          {recordData?.productionRecordByOrder ? (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="textSecondary">Дата на производство</Typography>
                <Typography variant="h6">
                  {new Date(recordData.productionRecordByOrder.confirmedAt).toLocaleString('bg-BG')}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="textSecondary">Годен до</Typography>
                <Typography variant="h6" color="error">
                  {new Date(recordData.productionRecordByOrder.expiryDate).toLocaleDateString('bg-BG')}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12 }}>
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Работници</Typography>
                {recordData.productionRecordByOrder.workers?.length > 0 ? (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Име</TableCell>
                        <TableCell>Работна станция</TableCell>
                        <TableCell>Започнал</TableCell>
                        <TableCell>Приключил</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recordData.productionRecordByOrder.workers.map((worker: any) => (
                        <TableRow key={worker.id}>
                          <TableCell>{worker.userName}</TableCell>
                          <TableCell>{worker.workstationName}</TableCell>
                          <TableCell>{worker.startedAt ? new Date(worker.startedAt).toLocaleString('bg-BG') : '-'}</TableCell>
                          <TableCell>{worker.completedAt ? new Date(worker.completedAt).toLocaleString('bg-BG') : '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <Typography color="textSecondary">Няма записани работници</Typography>
                )}
              </Grid>

              <Grid size={{ xs: 12 }}>
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Използвани съставки</Typography>
                {recordData.productionRecordByOrder.ingredients?.length > 0 ? (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Съставка</TableCell>
                        <TableCell>Партида</TableCell>
                        <TableCell>Срок на годност</TableCell>
                        <TableCell align="right">Количество</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recordData.productionRecordByOrder.ingredients.map((ing: any) => (
                        <TableRow key={ing.id}>
                          <TableCell>{ing.ingredientName}</TableCell>
                          <TableCell>{ing.batchNumber}</TableCell>
                          <TableCell>{ing.expiryDate ? new Date(ing.expiryDate).toLocaleDateString('bg-BG') : 'N/A'}</TableCell>
                          <TableCell align="right">{ing.quantityUsed} {ing.unit}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <Typography color="textSecondary">Няма записани съставки</Typography>
                )}
              </Grid>
            </Grid>
          ) : (
            <Typography>Няма запис за производството</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryOrderId(null)}>Затвори</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OrdersPage;
