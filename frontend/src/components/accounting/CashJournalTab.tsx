import React, { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Receipt as ReceiptIcon,
  EditNote as EditNoteIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import { useError, extractErrorMessage } from '../../context/ErrorContext';
import { ValidatedTextField } from '../ui/ValidatedTextField';
import {
  GET_CASH_JOURNAL_UNIFIED,
  CREATE_CASH_JOURNAL_ENTRY,
  DELETE_CASH_JOURNAL_ENTRY,
} from '../../graphql/accountingQueries';
import { type CashJournalUnifiedItem, type CashJournalUnifiedResult } from '../../types';
import { formatDate } from '../../utils/dateUtils';

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  cash: 'В брой',
  bank_transfer: 'Банков превод',
  card: 'Карта',
  other: 'Друго',
};

const SOURCE_LABELS: Record<string, string> = {
  manual: 'Ръчна',
  invoice: 'Фактура',
  cash_receipt: 'Касова бележка',
};

export const CashJournalTab: React.FC = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [operationType, setOperationType] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [cashForm, setCashForm] = useState({
    date: new Date().toISOString().split('T')[0],
    operationType: 'income',
    amount: '',
    description: '',
    paymentMethod: 'cash',
  });
  const { currency } = useCurrency();
  const { showSuccess, showError } = useError();

  const { data, loading, refetch } = useQuery(GET_CASH_JOURNAL_UNIFIED, {
    variables: {
      startDate: startDate || undefined,
      endDate: endDate || undefined,
      operationType: operationType || undefined,
      paymentMethod: paymentMethod || undefined,
      skip: page * rowsPerPage,
      limit: rowsPerPage,
    },
  });

  const [createCashEntry] = useMutation(CREATE_CASH_JOURNAL_ENTRY);
  const [deleteCashEntry] = useMutation(DELETE_CASH_JOURNAL_ENTRY);

  const unifiedData: CashJournalUnifiedResult | undefined = data?.cashJournalUnified;
  const entries: CashJournalUnifiedItem[] = unifiedData?.items || [];
  const totalCount = unifiedData?.totalCount || 0;
  const totalIncome = unifiedData?.totalIncome || 0;
  const totalExpense = unifiedData?.totalExpense || 0;
  const balance = unifiedData?.balance || 0;

  const handleAddEntry = async () => {
    try {
      await createCashEntry({
        variables: {
          input: {
            date: cashForm.date,
            operationType: cashForm.operationType,
            amount: parseFloat(cashForm.amount),
            description: cashForm.description || undefined,
            paymentMethod: cashForm.paymentMethod,
            referenceType: 'manual',
            companyId: 1,
          },
        },
      });
      setOpenDialog(false);
      setCashForm({
        date: new Date().toISOString().split('T')[0],
        operationType: 'income',
        amount: '',
        description: '',
        paymentMethod: 'cash',
      });
      refetch();
      showSuccess('Операцията е добавена успешно');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Сигурен ли си, че искаш да изтриеш тази операция?')) {
      try {
        await deleteCashEntry({ variables: { id } });
        refetch();
        showSuccess('Операцията е изтрита успешно');
      } catch (err) {
        showError(extractErrorMessage(err));
      }
    }
  };

  const handleExport = async () => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    if (operationType) params.set('operation_type', operationType);
    if (paymentMethod) params.set('payment_method', paymentMethod);

    const token = localStorage.getItem('token');
    const response = await fetch(`/api/export/cash-journal/xlsx?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      showError('Грешка при експорт');
      return;
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kasov-dnevnik-${startDate || 'all'}-to-${endDate || 'all'}.xlsx`;
    a.click();
    window.URL.revokeObjectURL(url);
    showSuccess('Експортът е готов');
  };

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Box>
      {/* Balance Cards */}
      <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Касово салдо</Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Paper sx={{ p: 2, bgcolor: '#e3f2fd', borderRadius: 1, flex: 1, minWidth: 150 }}>
            <Typography variant="subtitle2" color="text.secondary">Приходи</Typography>
            <Typography variant="h5" color="success.main">{formatPrice(totalIncome)}</Typography>
          </Paper>
          <Paper sx={{ p: 2, bgcolor: '#ffebee', borderRadius: 1, flex: 1, minWidth: 150 }}>
            <Typography variant="subtitle2" color="text.secondary">Разходи</Typography>
            <Typography variant="h5" color="error.main">{formatPrice(totalExpense)}</Typography>
          </Paper>
          <Paper sx={{ p: 2, bgcolor: balance >= 0 ? '#e8f5e9' : '#ffebee', borderRadius: 1, flex: 1, minWidth: 150 }}>
            <Typography variant="subtitle2" color="text.secondary">Салдо</Typography>
            <Typography variant="h5" color={balance >= 0 ? 'success.main' : 'error.main'}>
              {formatPrice(balance)}
            </Typography>
          </Paper>
        </Box>
      </Box>

      {/* Filters */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            size="small"
            label="От дата"
            type="date"
            value={startDate}
            onChange={(e) => { setStartDate(e.target.value); setPage(0); }}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            size="small"
            label="До дата"
            type="date"
            value={endDate}
            onChange={(e) => { setEndDate(e.target.value); setPage(0); }}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <Select
            size="small"
            value={operationType}
            onChange={(e) => { setOperationType(e.target.value); setPage(0); }}
            displayEmpty
            sx={{ minWidth: 140 }}
          >
            <MenuItem value="">Всички типове</MenuItem>
            <MenuItem value="income">Приход</MenuItem>
            <MenuItem value="expense">Разход</MenuItem>
          </Select>
          <Select
            size="small"
            value={paymentMethod}
            onChange={(e) => { setPaymentMethod(e.target.value); setPage(0); }}
            displayEmpty
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="">Всички методи</MenuItem>
            <MenuItem value="cash">В брой</MenuItem>
            <MenuItem value="bank_transfer">Банков превод</MenuItem>
            <MenuItem value="card">Карта</MenuItem>
            <MenuItem value="other">Друго</MenuItem>
          </Select>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExport}>
            Експорт
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenDialog(true)}>
            Добави операция
          </Button>
        </Box>
      </Box>

      {/* Unified Table */}
      {loading ? <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Източник</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>Платежен метод</TableCell>
                <TableCell>Описание</TableCell>
                <TableCell>Създал</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((entry: CashJournalUnifiedItem) => (
                <TableRow
                  key={entry.id}
                  sx={{
                    backgroundColor: entry.operationType === 'income' ? '#e8f5e9' : '#ffebee',
                  }}
                >
                  <TableCell>{formatDate(entry.date)}</TableCell>
                  <TableCell>
                    {entry.source === 'invoice' ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <ReceiptIcon fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2" fontWeight="medium">Фактура</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {entry.invoiceNumber || `#${entry.referenceId}`}
                          </Typography>
                        </Box>
                      </Box>
                    ) : (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <EditNoteIcon fontSize="small" color="action" />
                        <Typography variant="body2">Ръчна</Typography>
                      </Box>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={entry.operationType === 'income' ? 'Приход' : 'Разход'}
                      color={entry.operationType === 'income' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                    {formatPrice(Number(entry.amount))}
                  </TableCell>
                  <TableCell>
                    {PAYMENT_METHOD_LABELS[entry.paymentMethod || ''] || entry.paymentMethod || '-'}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      {entry.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {entry.creator ? `${entry.creator.firstName} ${entry.creator.lastName}` : '-'}
                  </TableCell>
                  <TableCell>
                    {entry.source === 'manual' && (
                      <IconButton size="small" color="error" onClick={() => handleDelete(entry.id)}>
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {entries.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">Няма намерени операции</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination
            component="div"
            count={totalCount}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            rowsPerPageOptions={[25, 50, 100]}
            labelRowsPerPage="Редове:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} от ${count}`}
          />
        </TableContainer>
      )}

      {/* Add Entry Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова касова операция</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ValidatedTextField
                label="Дата"
                type="date"
                value={cashForm.date}
                onChange={(value) => setCashForm({ ...cashForm, date: value })}
                tooltip="Дата на операцията"
                required
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Тип</InputLabel>
                <Select
                  value={cashForm.operationType}
                  label="Тип"
                  onChange={(e) => setCashForm({ ...cashForm, operationType: e.target.value })}
                >
                  <MenuItem value="income">Приход</MenuItem>
                  <MenuItem value="expense">Разход</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ValidatedTextField
                label="Сума"
                type="number"
                value={cashForm.amount}
                onChange={(value) => setCashForm({ ...cashForm, amount: value })}
                tooltip="Сума в лева"
                required
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Платежен метод</InputLabel>
                <Select
                  value={cashForm.paymentMethod}
                  label="Платежен метод"
                  onChange={(e) => setCashForm({ ...cashForm, paymentMethod: e.target.value })}
                >
                  <MenuItem value="cash">В брой</MenuItem>
                  <MenuItem value="bank_transfer">Банков превод</MenuItem>
                  <MenuItem value="card">Карта</MenuItem>
                  <MenuItem value="other">Друго</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ValidatedTextField
                label="Описание"
                multiline
                rows={2}
                value={cashForm.description}
                onChange={(value) => setCashForm({ ...cashForm, description: value })}
                tooltip="Описание на операцията"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Отказ</Button>
          <Button onClick={handleAddEntry} variant="contained" disabled={!cashForm.amount}>Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
