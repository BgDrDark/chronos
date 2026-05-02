import { formatDate } from '../../utils/dateUtils';
import React, { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
} from '@mui/material';
import { FileCopy as FileCopyIcon, Add as AddIcon } from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import { useError, extractErrorMessage } from '../../context/ErrorContext';
import { getInvoiceStatusText, getInvoiceStatusColor } from './invoiceUtils';
import { GET_PROFORMA_INVOICES, CONVERT_PROFORMA_TO_INVOICE } from '../../graphql/accountingQueries';
import { type Invoice } from '../../types';

interface ProformaTabProps {
  handleOpenDialog: (invoice?: Invoice) => void;
}

interface Proforma {
  id: number;
  number: string;
  date: string;
  clientName: string;
  subtotal: number;
  vatRate: number;
  vatAmount: number;
  total: number;
  status: string;
}

export const ProformaTab: React.FC<ProformaTabProps> = ({ handleOpenDialog }) => {
  const [search, setSearch] = useState('');
  const { showSuccess, showError } = useError();
  const { currency } = useCurrency();

  const { data, loading, refetch } = useQuery(GET_PROFORMA_INVOICES, {
    variables: { search: search || undefined },
  });

  const [convertProformaToInvoice] = useMutation(CONVERT_PROFORMA_TO_INVOICE);

  const proformas: Proforma[] = data?.proformaInvoices || [];

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const handleConvert = async (proformaId: number, invoiceType: string) => {
    try {
      await convertProformaToInvoice({ variables: { proformaId, invoiceType } });
      showSuccess('Проформата е конвертирана във фактура');
      refetch();
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <TextField
          size="small"
          label="Търси"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ width: 300 }}
        />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Нова проформа
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Номер</TableCell>
                <TableCell>Дата</TableCell>
                <TableCell>Клиент</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>ДДС</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell align="center">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {proformas.map((inv: Proforma) => (
                <TableRow key={inv.id}>
                  <TableCell>{inv.number}</TableCell>
                  <TableCell>{formatDate(inv.date)}</TableCell>
                  <TableCell>{inv.clientName}</TableCell>
                  <TableCell align="right">{formatPrice(Number(inv.total))}</TableCell>
                  <TableCell>{inv.vatRate}%</TableCell>
                  <TableCell>
                    <Chip label={getInvoiceStatusText(inv.status)} color={getInvoiceStatusColor(inv.status)} size="small" />
                  </TableCell>
                  <TableCell align="center">
                    {inv.status !== 'converted' && (
                      <Tooltip title="Конвертирай в изходяща фактура">
                        <IconButton size="small" onClick={() => handleConvert(inv.id, 'outgoing')}>
                          <FileCopyIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {proformas.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">Няма проформа фактури</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};