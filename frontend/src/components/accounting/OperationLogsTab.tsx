import React, { useState } from 'react';
import {
  Box,
  Chip,
  CircularProgress,
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
} from '@mui/material';
import { useQuery } from '@apollo/client';
import { GET_OPERATION_LOGS } from '../../graphql/accountingQueries';
import { type AccountingLog } from '../../types';

export const OperationLogsTab: React.FC = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [operation, setOperation] = useState('');
  const [entityType, setEntityType] = useState('');

  const { data, loading } = useQuery(GET_OPERATION_LOGS, {
    variables: { startDate: startDate || undefined, endDate: endDate || undefined, operation: operation || undefined, entityType: entityType || undefined },
  });

  const logs: AccountingLog[] = data?.operationLogs || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField size="small" label="От дата" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <TextField size="small" label="До дата" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <Select size="small" value={operation} onChange={(e) => setOperation(e.target.value)} displayEmpty sx={{ minWidth: 120 }}>
          <MenuItem value="">Всички</MenuItem>
          <MenuItem value="create">Създаване</MenuItem>
          <MenuItem value="update">Промяна</MenuItem>
          <MenuItem value="delete">Изтриване</MenuItem>
        </Select>
        <Select size="small" value={entityType} onChange={(e) => setEntityType(e.target.value)} displayEmpty sx={{ minWidth: 150 }}>
          <MenuItem value="">Всички обекти</MenuItem>
          <MenuItem value="invoice">Фактура</MenuItem>
          <MenuItem value="cash_journal">Касов дневник</MenuItem>
        </Select>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата/Час</TableCell>
                <TableCell>Операция</TableCell>
                <TableCell>Обект</TableCell>
                <TableCell>ID</TableCell>
                <TableCell>Потребител</TableCell>
                <TableCell>Промени</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log: AccountingLog) => (
                <TableRow key={log.id}>
                  <TableCell>{new Date(log.timestamp).toLocaleString('bg-BG')}</TableCell>
                  <TableCell>
                    <Chip label={log.operation === 'create' ? 'Създадено' : log.operation === 'update' ? 'Променено' : 'Изтрито'} color={log.operation === 'create' ? 'success' : log.operation === 'update' ? 'warning' : 'error'} size="small" />
                  </TableCell>
                  <TableCell>{log.entityType}</TableCell>
                  <TableCell>{log.entityId}</TableCell>
                  <TableCell>{typeof log.user === 'object' ? `${log.user.firstName || ''} ${log.user.lastName || ''}` : log.user}</TableCell>
                  <TableCell><pre style={{ fontSize: 11, margin: 0 }}>{JSON.stringify(log.changes, null, 2)}</pre></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};