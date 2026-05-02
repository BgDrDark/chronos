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
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import { useError, extractErrorMessage } from '../../context/ErrorContext';
import { ValidatedTextField } from '../ui/ValidatedTextField';
import {
  GET_CASH_JOURNAL_ENTRIES,
  CREATE_CASH_JOURNAL_ENTRY,
  DELETE_CASH_JOURNAL_ENTRY,
  GET_INVOICES,
} from '../../graphql/accountingQueries';
import { type Invoice, type CashJournalEntry } from '../../types';
import { formatDate } from '../../utils/dateUtils';

export const CashJournalTab: React.FC = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [operationType, setOperationType] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [cashForm, setCashForm] = useState({
    date: new Date().toISOString().split('T')[0],
    operationType: 'income',
    amount: '',
    description: '',
  });
  const { currency } = useCurrency();
  const { showSuccess, showError } = useError();

  const { data, loading, refetch } = useQuery(GET_CASH_JOURNAL_ENTRIES, {
    variables: { startDate: startDate || undefined, endDate: endDate || undefined, operationType: operationType || undefined },
  });

  const { data: invoicesData } = useQuery(GET_INVOICES, {
    variables: { type: undefined, status: 'paid' },
  });

  const [createCashEntry] = useMutation(CREATE_CASH_JOURNAL_ENTRY);
  const [deleteCashEntry] = useMutation(DELETE_CASH_JOURNAL_ENTRY);

  const handleAddEntry = async () => {
    try {
      await createCashEntry({
        variables: {
          input: {
            date: cashForm.date,
            operationType: cashForm.operationType,
            amount: parseFloat(cashForm.amount),
            description: cashForm.description,
            referenceType: 'manual',
            companyId: 1,
          },
        },
      });
      setOpenDialog(false);
      setCashForm({ date: new Date().toISOString().split('T')[0], operationType: 'income', amount: '', description: '' });
      refetch();
    } catch (err) {
      console.error(err);
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

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const entries: CashJournalEntry[] = data?.cashJournalEntries || [];
  const allInvoices: Invoice[] = invoicesData?.invoices || [];
  const paidInvoices = allInvoices.filter((inv: Invoice) => inv.status === 'paid');
  const incomingInvoices = paidInvoices.filter((inv: Invoice) => inv.type === 'incoming');
  const outgoingInvoices = paidInvoices.filter((inv: Invoice) => inv.type === 'outgoing');

  const totalIncoming = incomingInvoices.reduce((sum: number, inv: Invoice) => sum + Number(inv.total), 0);
  const totalOutgoing = outgoingInvoices.reduce((sum: number, inv: Invoice) => sum + Number(inv.total), 0);

  return (
    <Box>
      <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Фактури (платени)</Typography>
        <Box sx={{ display: 'flex', gap: 4 }}>
          <Box sx={{ p: 2, bgcolor: '#ffebee', borderRadius: 1, flex: 1 }}>
            <Typography variant="subtitle2">Входящи фактури (Разход)</Typography>
            <Typography variant="h5" color="error.main">{formatPrice(totalIncoming)}</Typography>
            <Typography variant="body2" color="text.secondary">{incomingInvoices.length} бр.</Typography>
          </Box>
          <Box sx={{ p: 2, bgcolor: '#e8f5e9', borderRadius: 1, flex: 1 }}>
            <Typography variant="subtitle2">Изходящи фактури (Приход)</Typography>
            <Typography variant="h5" color="success.main">{formatPrice(totalOutgoing)}</Typography>
            <Typography variant="body2" color="text.secondary">{outgoingInvoices.length} бр.</Typography>
          </Box>
        </Box>
      </Box>

      {incomingInvoices.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Входящи фактури (Разход)</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#ffebee' }}>
                  <TableCell>№</TableCell>
                  <TableCell>дата</TableCell>
                  <TableCell>Доставчик</TableCell>
                  <TableCell>Сума</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {incomingInvoices.map((inv: Invoice) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.number}</TableCell>
                    <TableCell>{formatDate(inv.date)}</TableCell>
                    <TableCell>{inv.supplier?.name || '-'}</TableCell>
                    <TableCell align="right" sx={{ color: 'error.main' }}>{formatPrice(Number(inv.total))}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {outgoingInvoices.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Изходящи фактури (Приход)</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                  <TableCell>№</TableCell>
                  <TableCell>дата</TableCell>
                  <TableCell>Клиент</TableCell>
                  <TableCell>Сума</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {outgoingInvoices.map((inv: Invoice) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.number}</TableCell>
                    <TableCell>{formatDate(inv.date)}</TableCell>
                    <TableCell>{inv.clientName || '-'}</TableCell>
                    <TableCell align="right" sx={{ color: 'success.main' }}>{formatPrice(Number(inv.total))}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            size="small"
            label="От дата"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <TextField
            size="small"
            label="До дата"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <Select
            size="small"
            value={operationType}
            onChange={(e) => setOperationType(e.target.value)}
            displayEmpty
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">Всички типове</MenuItem>
            <MenuItem value="income">Приход</MenuItem>
            <MenuItem value="expense">Разход</MenuItem>
          </Select>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenDialog(true)}>
          Добави операция
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>Описание</TableCell>
                <TableCell>Създал</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((entry: CashJournalEntry) => (
                <TableRow key={entry.id} sx={{ backgroundColor: entry.operationType === 'income' ? '#e8f5e9' : '#ffebee' }}>
                  <TableCell>{formatDate(entry.date)}</TableCell>
                  <TableCell>
                    <Chip label={entry.operationType === 'income' ? 'Приход' : 'Разход'} color={entry.operationType === 'income' ? 'success' : 'error'} size="small" />
                  </TableCell>
                  <TableCell align="right">{formatPrice(Number(entry.amount))}</TableCell>
                  <TableCell>{entry.description}</TableCell>
                  <TableCell>{entry.creator?.firstName} {entry.creator?.lastName}</TableCell>
                  <TableCell>
                    <IconButton size="small" color="error" onClick={() => handleDelete(entry.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

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
                  onChange={(e) => setCashForm(() => ({ ...cashForm, operationType: e.target.value as string }))}
                >
                  <MenuItem value="income">Приход</MenuItem>
                  <MenuItem value="expense">Разход</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ValidatedTextField
                label="Сума"
                type="number"
                value={cashForm.amount}
                onChange={(value) => setCashForm({ ...cashForm, amount: value })}
                tooltip="Сума в лева"
                required
              />
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