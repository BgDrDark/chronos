import React, { useState } from 'react';
import { Box, TextField, FormControl, InputLabel, Select, MenuItem, Button, TableContainer, Paper, Table, TableHead, TableRow, TableCell, TableBody, Chip, CircularProgress, Alert, Typography } from '@mui/material';
import { useQuery } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import { GET_ACCOUNTING_ENTRIES, GET_ACCOUNTS } from '../../graphql/accountingQueries';
import { AccountingEntry, Account } from '../../types';
import { formatDate } from '../../utils/dateUtils';

const AccountingEntriesTab: React.FC = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [accountId, setAccountId] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const { currency } = useCurrency();

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const { data, loading, error, refetch } = useQuery(GET_ACCOUNTING_ENTRIES, {
    variables: {
      startDate: startDate || undefined,
      endDate: endDate || undefined,
      accountId: accountId || undefined,
      search: search || undefined,
    },
  });

  const { data: accountsData } = useQuery(GET_ACCOUNTS);

  const entries = data?.accountingEntries || [];
  const accounts = accountsData?.accounts || [];

  const totalDebit = entries.reduce((sum: number, entry: AccountingEntry) => sum + Number(entry.amount), 0);
  const totalVat = entries.reduce((sum: number, entry: AccountingEntry) => sum + Number(entry.vatAmount), 0);

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          size="small"
          type="date"
          label="От дата"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ width: 150 }}
        />
        <TextField
          size="small"
          type="date"
          label="До дата"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ width: 150 }}
        />
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Филтрирай по сметка</InputLabel>
          <Select
            value={accountId || ''}
            label="Филтрирай по сметка"
            onChange={(e) => setAccountId(e.target.value as number || null)}
          >
            <MenuItem value="">Всички сметки</MenuItem>
            {accounts.map((acc: Account) => (
              <MenuItem key={acc.id} value={acc.id}>
                {acc.code} - {acc.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          size="small"
          label="Търси"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ width: 200 }}
        />
        <Button
          size="small"
          variant="outlined"
          onClick={() => refetch()}
        >
          Обнови
        </Button>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : error ? (
        <Alert severity="error">Грешка при зареждане на счетоводните записи</Alert>
      ) : (
        <>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Chip label={`Общо записи: ${entries.length}`} />
            <Chip label={`Обща сума: ${formatPrice(totalDebit)}`} color="primary" />
            <Chip label={`ДДС: ${formatPrice(totalVat)}`} color="secondary" />
          </Box>

          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.100' }}>
                  <TableCell>№</TableCell>
                  <TableCell>Дата</TableCell>
                  <TableCell>№ на запис</TableCell>
                  <TableCell>Описание</TableCell>
                  <TableCell>Дебит сметка</TableCell>
                  <TableCell>Кредит сметка</TableCell>
                  <TableCell align="right">Сума</TableCell>
                  <TableCell align="right">ДДС</TableCell>
                  <TableCell>Фактура</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {entries.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">Няма счетоводни записи</TableCell>
                  </TableRow>
                ) : (
                  entries.map((entry: AccountingEntry) => (
                    <TableRow key={entry.id} hover>
                      <TableCell>{entry.id}</TableCell>
                      <TableCell>{formatDate(entry.date)}</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>{entry.entryNumber}</TableCell>
                      <TableCell>{entry.description || '-'}</TableCell>
                      <TableCell>
                        {entry.debitAccount ? (
                          <Chip
                            size="small"
                            label={`${entry.debitAccount.code} ${entry.debitAccount.name}`}
                            variant="outlined"
                            color="success"
                          />
                        ) : (
                          entry.debitAccountId
                        )}
                      </TableCell>
                      <TableCell>
                        {entry.creditAccount ? (
                          <Chip
                            size="small"
                            label={`${entry.creditAccount.code} ${entry.creditAccount.name}`}
                            variant="outlined"
                            color="warning"
                          />
                        ) : (
                          entry.creditAccountId
                        )}
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                        {formatPrice(Number(entry.amount))}
                      </TableCell>
                      <TableCell align="right">
                        {Number(entry.vatAmount) > 0 ? (
                          <Typography variant="caption" color="secondary">
                            {formatPrice(Number(entry.vatAmount))}
                          </Typography>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {entry.invoice ? (
                          <Chip
                            size="small"
                            label={entry.invoice.number}
                            variant="outlined"
                            onClick={() => {}}
                          />
                        ) : entry.invoiceId ? (
                          <Typography variant="caption">#{entry.invoiceId}</Typography>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );
};

export default AccountingEntriesTab;
