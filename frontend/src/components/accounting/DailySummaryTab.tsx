import { formatDate } from '../../utils/dateUtils';
import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import {
  GET_DAILY_SUMMARIES,
  GENERATE_DAILY_SUMMARY,
} from '../../graphql/accountingQueries';
import { type AccountingSummary } from '../../types';

export const DailySummaryTab: React.FC = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [generateDate, setGenerateDate] = useState(new Date().toISOString().split('T')[0]);
  const [generating, setGenerating] = useState(false);
  const { currency } = useCurrency();

  const { data, loading, refetch } = useQuery(GET_DAILY_SUMMARIES, {
    variables: { startDate: startDate || undefined, endDate: endDate || undefined },
  });

  const [generateDailySummary] = useMutation(GENERATE_DAILY_SUMMARY);

  const summaries: AccountingSummary[] = data?.dailySummaries || [];

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const handleGenerate = async () => {
    if (!generateDate) return;
    setGenerating(true);
    try {
      await generateDailySummary({ variables: { date: generateDate } });
      refetch();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField size="small" label="От дата" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <TextField size="small" label="До дата" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <Box sx={{ flexGrow: 1 }} />
        <TextField size="small" label="Генерирай за дата" type="date" value={generateDate} onChange={(e) => setGenerateDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <Button variant="contained" color="primary" onClick={handleGenerate} disabled={generating} startIcon={generating ? <CircularProgress size={16} color="inherit" /> : null}>
          Генерирай
        </Button>
      </Box>

      {loading ? <CircularProgress /> : summaries.length === 0 ? (
        <Alert severity="info">Няма данни за избрания период</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell align="right">Брой фактури</TableCell>
                <TableCell align="right">Обща сума</TableCell>
                <TableCell align="right">Приход (каса)</TableCell>
                <TableCell align="right">Разход (каса)</TableCell>
                <TableCell align="right">Баланс</TableCell>
                <TableCell align="right">ДДС събран</TableCell>
                <TableCell align="right">ДДС платен</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summaries.map((summary: AccountingSummary) => (
                <TableRow key={summary.id}>
                  <TableCell>{summary.date ? formatDate(summary.date) : '-'}</TableCell>
                  <TableCell align="right">{summary.invoicesCount}</TableCell>
                  <TableCell align="right">{formatPrice(summary.invoicesTotal ?? 0)}</TableCell>
                  <TableCell align="right" sx={{ color: 'success.main' }}>+{formatPrice(summary.cashIncome ?? 0)}</TableCell>
                  <TableCell align="right" sx={{ color: 'error.main' }}>-{formatPrice(summary.cashExpense ?? 0)}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold', color: (summary.cashBalance ?? 0) >= 0 ? 'success.main' : 'error.main' }}>{formatPrice(summary.cashBalance ?? 0)}</TableCell>
                  <TableCell align="right">{formatPrice(summary.vatCollected ?? 0)}</TableCell>
                  <TableCell align="right">{formatPrice(summary.vatPaid ?? 0)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};