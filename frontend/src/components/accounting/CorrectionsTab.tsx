import React, { useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  MenuItem,
  Paper,
  Radio,
  RadioGroup,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import { useError, extractErrorMessage } from '../../context/ErrorContext';
import { getInvoiceStatusText, getInvoiceStatusColor } from './invoiceUtils';
import {
  GET_INVOICE_CORRECTIONS,
  CREATE_INVOICE_CORRECTION,
  GET_INVOICES,
} from '../../graphql/accountingQueries';
import { type Invoice } from '../../types';
import { formatDate } from '../../utils/dateUtils';

interface Correction {
  id: number;
  number: string;
  type: string;
  date: string;
  originalInvoiceId: number;
  clientName: string;
  reason?: string;
  subtotal: number;
  vatAmount: number;
  total: number;
  status: string;
}

export const CorrectionsTab: React.FC = () => {
  const [type, setType] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [correctionType, setCorrectionType] = useState<'credit' | 'debit'>('credit');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);
  const [reason, setReason] = useState('');
  const [correctionDate, setCorrectionDate] = useState(new Date().toISOString().split('T')[0]);
  const [createNewInvoice, setCreateNewInvoice] = useState(false);
  const { showSuccess, showError } = useError();
  const { currency } = useCurrency();

  const { data, loading, refetch } = useQuery(GET_INVOICE_CORRECTIONS, {
    variables: { type: type || undefined },
  });

  const { data: invoicesData } = useQuery(GET_INVOICES, {
    variables: { type: undefined, status: undefined },
  });

  const [createCorrection] = useMutation(CREATE_INVOICE_CORRECTION);

  const corrections: Correction[] = data?.invoiceCorrections || [];
  const invoices: Invoice[] = invoicesData?.invoices || [];

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const handleCreateCorrection = async () => {
    if (!selectedInvoiceId) {
      showError('Моля, изберете оригинална фактура');
      return;
    }
    if (!reason.trim()) {
      showError('Моля, въведете причина');
      return;
    }

    try {
      const { data: result } = await createCorrection({
        variables: {
          originalInvoiceId: selectedInvoiceId,
          correctionType,
          reason,
          correctionDate,
          createNewInvoice,
        },
      });

      if (result?.createInvoiceCorrection) {
        showSuccess(`Корекция ${result.createInvoiceCorrection.number} е създадена успешно`);
        setDialogOpen(false);
        setSelectedInvoiceId(null);
        setReason('');
        setCorrectionType('credit');
        setCreateNewInvoice(false);
        refetch();
      }
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const selectedInvoice = invoices.find((inv: Invoice) => inv.id === selectedInvoiceId);

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Select
          size="small"
          value={type}
          onChange={(e) => setType(e.target.value)}
          displayEmpty
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">Всички типове</MenuItem>
          <MenuItem value="credit">Кредитно известие</MenuItem>
          <MenuItem value="debit">Дебитно известие</MenuItem>
        </Select>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
          Нова корекция
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Номер</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell>Дата</TableCell>
                <TableCell>Оригинална фактура</TableCell>
                <TableCell>Клиент</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>Статус</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {corrections.map((corr: Correction) => (
                <TableRow key={corr.id}>
                  <TableCell>{corr.number}</TableCell>
                  <TableCell>
                    <Chip
                      label={corr.type === 'credit' ? 'Кредитно' : 'Дебитно'}
                      color={corr.type === 'credit' ? 'warning' : 'info'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatDate(corr.date)}</TableCell>
                  <TableCell>#{corr.originalInvoiceId}</TableCell>
                  <TableCell>{corr.clientName}</TableCell>
                  <TableCell align="right">{formatPrice(Number(corr.total))}</TableCell>
                  <TableCell><Chip label={getInvoiceStatusText(corr.status)} color={getInvoiceStatusColor(corr.status)} size="small" /></TableCell>
                </TableRow>
              ))}
              {corrections.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">Няма корекции</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>➕ Нова корекция</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl>
              <FormLabel>Тип</FormLabel>
              <RadioGroup row value={correctionType} onChange={(e) => setCorrectionType(e.target.value as 'credit' | 'debit')}>
                <FormControlLabel value="credit" control={<Radio />} label="Кредитно известие" />
                <FormControlLabel value="debit" control={<Radio />} label="Дебитно известие" />
              </RadioGroup>
            </FormControl>

            <Autocomplete
              options={invoices.filter((inv: Invoice) => inv.status !== 'paid' && inv.status !== 'cancelled' && inv.status !== 'corrected')}
              getOptionLabel={(inv: Invoice) => `${inv.number} - ${inv.clientName || 'Без име'} - ${formatPrice(Number(inv.total))}`}
              value={selectedInvoice || null}
              onChange={(_, newValue) => setSelectedInvoiceId(newValue ? newValue.id : null)}
              renderInput={(params) => (
                <TextField {...params} label="Оригинална фактура" placeholder="Търсете по номер или клиент..." />
              )}
              noOptionsText="Няма намерени фактури за корекция"
            />

            {selectedInvoice && (
              <Alert severity="info">
                <strong>Оригинална фактура:</strong> {selectedInvoice.number}<br />
                <strong>Клиент:</strong> {selectedInvoice.clientName || '-'}<br />
                <strong>Сума:</strong> {formatPrice(Number(selectedInvoice.total))}<br />
                <strong>ДДС:</strong> {formatPrice(Number(selectedInvoice.vatAmount))}
              </Alert>
            )}

            <TextField
              label="Дата на корекцията"
              type="date"
              value={correctionDate}
              onChange={(e) => setCorrectionDate(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />

            <TextField
              label="Причина"
              multiline
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Въведете причината за корекцията..."
            />

            {selectedInvoice && (
              <Alert severity="warning">
                <strong>Внимание!</strong><br />
                След създаване на корекция, оригиналната фактура #{selectedInvoice.number} ще бъде маркирана като „коригирана" и няма да може да се редактира.
              </Alert>
            )}

            <FormControlLabel
              control={
                <Checkbox
                  checked={createNewInvoice}
                  onChange={(e) => setCreateNewInvoice(e.target.checked)}
                />
              }
              label="Създай нова коригирана фактура"
            />

            {selectedInvoice && (
              <Alert severity={correctionType === 'credit' ? 'warning' : 'info'}>
                <strong>Корекция ({correctionType === 'credit' ? 'Кредитно' : 'Дебитно'}):</strong><br />
                <strong>Сума:</strong> {correctionType === 'credit' ? '-' : '+'}{formatPrice(Number(selectedInvoice.subtotal))}<br />
                <strong>ДДС:</strong> {correctionType === 'credit' ? '-' : '+'}{formatPrice(Number(selectedInvoice.vatAmount))}<br />
                <strong>Общо:</strong> {correctionType === 'credit' ? '-' : '+'}{formatPrice(Number(selectedInvoice.total))}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Отказ</Button>
          <Button variant="contained" onClick={handleCreateCorrection}>
            Създай
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};