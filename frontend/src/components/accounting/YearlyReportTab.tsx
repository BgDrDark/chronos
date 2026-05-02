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
  GET_YEARLY_SUMMARIES,
  GENERATE_YEARLY_SUMMARY,
} from '../../graphql/accountingQueries';
import { type AccountingSummary } from '../../types';

export const YearlyReportTab: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [startYear, setStartYear] = useState(currentYear.toString());
  const [endYear, setEndYear] = useState(currentYear.toString());
  const [generateYear, setGenerateYear] = useState(currentYear.toString());
  const [generating, setGenerating] = useState(false);
  const { currency } = useCurrency();

  const { data, loading, refetch } = useQuery(GET_YEARLY_SUMMARIES, {
    variables: { startYear: startYear ? parseInt(startYear) : undefined, endYear: endYear ? parseInt(endYear) : undefined },
  });

  const [generateYearlySummary] = useMutation(GENERATE_YEARLY_SUMMARY);

  const summaries: AccountingSummary[] = data?.yearlySummaries || [];

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const handleGenerate = async () => {
    if (!generateYear) return;
    setGenerating(true);
    try {
      await generateYearlySummary({ variables: { year: parseInt(generateYear) } });
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
        <TextField size="small" label="От година" type="number" value={startYear} onChange={(e) => setStartYear(e.target.value)} sx={{ width: 120 }} />
        <TextField size="small" label="До година" type="number" value={endYear} onChange={(e) => setEndYear(e.target.value)} sx={{ width: 120 }} />
        <Box sx={{ flexGrow: 1 }} />
        <TextField size="small" label="Генерирай за година" type="number" value={generateYear} onChange={(e) => setGenerateYear(e.target.value)} sx={{ width: 120 }} />
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
                <TableCell>Година</TableCell>
                <TableCell align="right">Брой фактури</TableCell>
                <TableCell align="right">Входящи</TableCell>
                <TableCell align="right">Изходящи</TableCell>
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
                  <TableCell sx={{ fontWeight: 'bold' }}>{summary.year}</TableCell>
                  <TableCell align="right">{summary.invoicesCount}</TableCell>
                  <TableCell align="right">{summary.incomingInvoicesCount}</TableCell>
                  <TableCell align="right">{summary.outgoingInvoicesCount}</TableCell>
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