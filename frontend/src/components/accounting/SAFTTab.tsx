import React, { useState } from 'react';
import { Box, Paper, Typography, TextField, FormControl, InputLabel, Select, MenuItem, Button, CircularProgress, Alert, Grid, Chip, Table, TableHead, TableRow, TableCell, TableBody, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useMutation } from '@apollo/client';
import { GENERATE_SAFT_FILE } from '../../graphql/accountingQueries';

const SAFTTab: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [saftType, setSaftType] = useState('monthly');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [generateSAFT] = useMutation(GENERATE_SAFT_FILE);

  const monthNames = ['Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни', 'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'];

  const handleGenerate = async () => {
    setGenerating(true);
    setResult(null);
    try {
      const { data } = await generateSAFT({
        variables: {
          companyId: 1,
          year,
          month,
          saftType
        }
      });
      setResult(data?.generateSAFTFile);
    } catch (err) {
      console.error(err);
      setResult({ error: 'Грешка при генериране на SAF-T файл' });
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!result?.xmlContent) return;
    const blob = new Blob([result.xmlContent], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.fileName || `SAFT_${year}_${month}.xml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3, bgcolor: '#f8f9fa' }}>
        <Typography variant="h6" gutterBottom>Генериране на SAF-T файл</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          SAF-T (Standard Audit File for Tax) е задължителен за големи предприятия от Януари 2026.
          Файлът се подава към НАП по електронен път.
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
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
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Тип</InputLabel>
            <Select value={saftType} label="Тип" onChange={(e) => setSaftType(e.target.value)}>
              <MenuItem value="monthly">Месечен</MenuItem>
              <MenuItem value="annual">Годишен</MenuItem>
              <MenuItem value="on_demand">По заявка</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            color="primary"
            onClick={handleGenerate}
            disabled={generating}
            startIcon={generating ? <CircularProgress size={16} color="inherit" /> : null}
          >
            {generating ? 'Генериране...' : 'Генерирай SAF-T'}
          </Button>
        </Box>
      </Paper>

      {result && (
        <Box>
          {result.error ? (
            <Alert severity="error">{result.error}</Alert>
          ) : (
            <>
              <Alert severity="success" sx={{ mb: 2 }}>
                SAF-T файлът е генериран успешно! Размер: {result.fileSize} bytes
              </Alert>

              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Информация за файла:</Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2"><strong>Период:</strong> {result.periodStart} - {result.periodEnd}</Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2"><strong>Име на файл:</strong> {result.fileName}</Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="body2">
                      <strong>Валидация:</strong>{' '}
                      <Chip
                        label={result.validationResult?.status === 'valid' ? 'Валиден' : 'Невалиден'}
                        color={result.validationResult?.status === 'valid' ? 'success' : 'error'}
                        size="small"
                      />
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="contained" color="primary" onClick={handleDownload}>
                  Свали XML
                </Button>
              </Box>

              {result.validationResult?.warnings?.length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <strong>Предупреждения:</strong>
                  <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                    {result.validationResult.warnings.map((w: string, i: number) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </Alert>
              )}
            </>
          )}
        </Box>
      )}

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>Информация за SAF-T</Typography>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Задължителни предприятия</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Период</TableCell>
                  <TableCell>Задължени предприятия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Януари 2026</TableCell>
                  <TableCell>Големи (&gt;300 млн. € оборот)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Януари 2028</TableCell>
                  <TableCell>Средни (&gt;15 млн. € оборот)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Януари 2030</TableCell>
                  <TableCell>Всички останали</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </AccordionDetails>
        </Accordion>
      </Box>
    </Box>
  );
};

export default SAFTTab;
