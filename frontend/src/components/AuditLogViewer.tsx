import React, { useState } from 'react';
import { 
  Box, Typography, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Paper, CircularProgress, TextField, MenuItem,
  Chip
} from '@mui/material';
import { useQuery, gql } from '@apollo/client';
import { format } from 'date-fns';

const GET_AUDIT_LOGS = gql`
  query GetAuditLogs($skip: Int, $limit: Int, $action: String) {
    auditLogs(skip: $skip, limit: $limit, action: $action) {
      id
      action
      targetType
      targetId
      details
      createdAt
      user {
        firstName
        lastName
        email
      }
    }
  }
`;

const AuditLogViewer: React.FC = () => {
    const [actionFilter, setActionFilter] = useState('');
    const { data, loading, error } = useQuery(GET_AUDIT_LOGS, {
        variables: { skip: 0, limit: 100, action: actionFilter || null },
        fetchPolicy: 'network-only'
    });

    const getActionColor = (action: string) => {
        if (action.includes('DELETE')) return 'error';
        if (action.includes('UPDATE')) return 'warning';
        if (action.includes('APPROVE')) return 'success';
        return 'default';
    };

    if (loading && !data) return <CircularProgress />;
    if (error) return <Typography color="error">Error: {error.message}</Typography>;

    return (
        <Box>
            <Typography variant="h6" gutterBottom>История на промените (Audit Log)</Typography>
            
            <Box sx={{ mb: 2 }}>
                <TextField
                    select
                    label="Филтър по действие"
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                    size="small"
                    sx={{ minWidth: 200 }}
                >
                    <MenuItem value="">Всички</MenuItem>
                    <MenuItem value="UPDATE_GLOBAL_PAYROLL">Глобални заплати</MenuItem>
                    <MenuItem value="UPDATE_USER_PAYROLL">Потребителски заплати</MenuItem>
                    <MenuItem value="DELETE_USER">Изтриване на потребител</MenuItem>
                    <MenuItem value="DELETE_SHIFT">Изтриване на смяна</MenuItem>
                    <MenuItem value="APPROVE_REJECT_LEAVE">Отпуски (Одобрение/Отказ)</MenuItem>
                </TextField>
            </Box>

            <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                    <TableHead sx={{ bgcolor: 'action.hover' }}>
                        <TableRow>
                            <TableCell>Дата и час</TableCell>
                            <TableCell>Администратор</TableCell>
                            <TableCell>Действие</TableCell>
                            <TableCell>Обект</TableCell>
                            <TableCell>Детайли</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {data?.auditLogs.map((log: any) => (
                            <TableRow key={log.id} hover>
                                <TableCell sx={{ whiteSpace: 'nowrap' }}>
                                    {format(new Date(log.createdAt), 'dd.MM.yyyy HH:mm')}
                                </TableCell>
                                <TableCell>
                                    {log.user ? `${log.user.firstName} ${log.user.lastName}` : 'System'}
                                    <Typography variant="caption" display="block" color="text.secondary">
                                        {log.user?.email}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Chip 
                                        label={log.action} 
                                        size="small" 
                                        color={getActionColor(log.action) as any} 
                                        variant="outlined" 
                                    />
                                </TableCell>
                                <TableCell>
                                    {log.targetType} {log.targetId && `(ID: ${log.targetId})`}
                                </TableCell>
                                <TableCell sx={{ maxWidth: 300, wordWrap: 'break-word' }}>
                                    {log.details}
                                </TableCell>
                            </TableRow>
                        ))}
                        {data?.auditLogs.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                                    Няма записи в дневника.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};

export default AuditLogViewer;
