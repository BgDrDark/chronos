import { formatDate } from '../../utils/dateUtils';
import React, { useState, useMemo } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Typography,
  Chip,
  TextField,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Print as PrintIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useQuery } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import { GET_INVOICES } from '../../graphql/accountingQueries';
import {
  getInvoiceStatusText,
  getInvoiceStatusColor,
  isInvoiceReadOnly,
  getBatchInfo,
} from './invoiceUtils';

interface InvoiceListProps {
  invoiceType: 'incoming' | 'outgoing';
  onAdd: () => void;
  onEdit: (invoice: unknown) => void;
  onView: (invoice: unknown) => void;
  onPrint: (invoiceId: number) => void;
  onDelete: (invoice: unknown) => void;
}

interface RawInvoice {
  id: number;
  number: string;
  date: string;
  status: string;
  total: number;
  vatRate: number;
  supplier?: { name?: string } | null;
  clientName?: string | null;
  batch?: unknown;
}

export const InvoiceList: React.FC<InvoiceListProps> = ({
  invoiceType,
  onAdd,
  onEdit,
  onView,
  onPrint,
  onDelete,
}) => {
  const [search, setSearch] = useState('');
  const { currency } = useCurrency();

  const { data, loading, error } = useQuery(GET_INVOICES, {
    variables: { type: invoiceType, search: search || undefined },
  });

  const invoices = useMemo(() => (data?.invoices || []) as RawInvoice[], [data]);

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
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
        <Chip
          label={`+ Нова ${invoiceType === 'incoming' ? 'входяща' : 'изходяща'} фактура`}
          onClick={onAdd}
          icon={<AddIcon />}
          color="primary"
          clickable
        />
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <Typography>Зареждане...</Typography>
        </Box>
      ) : error ? (
        <Box sx={{ p: 2 }}>
          <Typography color="error">Грешка при зареждане на фактурите</Typography>
        </Box>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>Номер</TableCell>
                <TableCell>Дата</TableCell>
                <TableCell>{invoiceType === 'incoming' ? 'Доставчик' : 'Клиент'}</TableCell>
                <TableCell>Партида</TableCell>
                <TableCell>Срок годност</TableCell>
                <TableCell align="right">Сума</TableCell>
                <TableCell>ДДС</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoices.map((invoice) => {
                const batchInfo = getBatchInfo(invoice.batch);
                const readOnly = isInvoiceReadOnly(invoice.status);

                return (
                  <TableRow
                    key={invoice.id}
                    hover
                    onClick={() => onView(invoice)}
                    sx={{
                      cursor: 'pointer',
                      opacity: readOnly ? 0.7 : 1,
                    }}
                  >
                    <TableCell>
                      <IconButton size="small">
                        <ExpandMoreIcon />
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Typography fontWeight="bold">{invoice.number}</Typography>
                    </TableCell>
                    <TableCell>
                      {formatDate(invoice.date)}
                    </TableCell>
                    <TableCell>
                      {invoiceType === 'incoming'
                        ? invoice.supplier?.name || '-'
                        : invoice.clientName || '-'}
                    </TableCell>
                    <TableCell>{batchInfo.batchNumber}</TableCell>
                    <TableCell>{batchInfo.expiryDate}</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight="bold">
                        {formatPrice(invoice.total)}
                      </Typography>
                    </TableCell>
                    <TableCell>{invoice.vatRate}%</TableCell>
                    <TableCell>
                      <Chip
                        label={getInvoiceStatusText(invoice.status)}
                        color={getInvoiceStatusColor(invoice.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Tooltip title="PDF">
                        <IconButton size="small" onClick={() => onPrint(invoice.id)}>
                          <PrintIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={readOnly ? 'READONLY - не може да се редактира' : 'Редактирай'}>
                        <span>
                          <IconButton
                            size="small"
                            onClick={() => onEdit(invoice)}
                            disabled={readOnly}
                          >
                            <EditIcon />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title={invoiceType === 'incoming' ? 'Изтриването е забранено' : 'Изтрий'}>
                        <IconButton
                          size="small"
                          onClick={() => onDelete(invoice)}
                          disabled={invoiceType === 'incoming'}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default InvoiceList;