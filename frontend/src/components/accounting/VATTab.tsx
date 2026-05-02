import React, { useState } from 'react';
import { Box, TextField, FormControl, InputLabel, Select, MenuItem, Button, TableContainer, Paper, Table, TableHead, TableRow, TableCell, TableBody, CircularProgress, Alert } from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import { GET_VAT_REGISTERS, GENERATE_VAT_REGISTER } from '../../graphql/accountingQueries';
import { Register } from '../../types';

const VATTab: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [generating, setGenerating] = useState(false);

  const { data, loading, refetch } = useQuery(GET_VAT_REGISTERS, {
    variables: { year, month },
  });

  const [generateVAT] = useMutation(GENERATE_VAT_REGISTER);

  const registers = data?.vatRegisters || [];

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateVAT({ variables: { input: { periodMonth: month, periodYear: year, companyId: 1 } } });
      refetch();
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const monthNames = ['Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни', 'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'];

  const { currency } = useCurrency();
  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField
          size="small"
          label="Година"
          type="number"
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          sx={{ width: 120 }}
        />
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Месец</InputLabel>
          <Select value={month} label="Месец" onChange={(e) => setMonth(e.target.value as number)}>
            {monthNames.map((m, i) => <MenuItem key={i+1} value={i+1}>{m}</MenuItem>)}
          </Select>
        </FormControl>
        <Button variant="contained" onClick={handleGenerate} disabled={generating}>
          {generating ? 'Генериране...' : 'Генерирай ДДС'}
        </Button>
      </Box>

      {loading ? <CircularProgress /> : registers.length === 0 ? (
        <Alert severity="info">Няма ДДС регистър за този период</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Период</TableCell>
                <TableCell align="right">ДДС приход 20%</TableCell>
                <TableCell align="right">ДДС приход 9%</TableCell>
                <TableCell align="right">ДДС разход 20%</TableCell>
                <TableCell align="right">ДДС разход 9%</TableCell>
                <TableCell align="right">ДДС за внасяне</TableCell>
                <TableCell align="right">ДДС за възстановяване</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {registers.map((reg: Register) => (
                <TableRow key={reg.id}>
                  <TableCell sx={{ fontWeight: 'bold' }}>{monthNames[reg.periodMonth - 1]} {reg.periodYear}</TableCell>
                  <TableCell align="right">{formatPrice(Number(reg.vatCollected20))}</TableCell>
                  <TableCell align="right">{formatPrice(Number(reg.vatCollected9))}</TableCell>
                  <TableCell align="right">{formatPrice(Number(reg.vatPaid20))}</TableCell>
                  <TableCell align="right">{formatPrice(Number(reg.vatPaid9))}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold', color: reg.vatDue > 0 ? 'error.main' : 'success.main' }}>
                    {formatPrice(Number(reg.vatDue))}
                  </TableCell>
                  <TableCell align="right" sx={{ color: reg.vatCredit > 0 ? 'success.main' : 'text.default' }}>
                    {formatPrice(Number(reg.vatCredit))}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default VATTab;
