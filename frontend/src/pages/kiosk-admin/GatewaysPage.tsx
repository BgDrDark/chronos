import React, { useState } from 'react';
import { getErrorMessage, Gateway } from '../../types';
import {
  Typography, Card, CardContent,
  Box, CircularProgress,
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip,
  IconButton,
} from '@mui/material';
import {
  Edit as EditIcon,
  Refresh as RefreshIcon,
  CloudDownload as DownloadIcon,
  CloudUpload as UploadIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { GATEWAYS_QUERY } from '../../graphql/queries/kioskAdmin';
import { SYNC_GATEWAY_CONFIG } from '../../graphql/mutations/kioskAdmin';
import GatewayEditDialog from './dialogs/GatewayDialog';

const formatTimeAgo = (dateStr: string | null) => {
  if (!dateStr) return 'Никога';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return `${diff}с`;
  if (diff < 3600) return `${Math.floor(diff / 60)}м`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}ч`;
  return `${Math.floor(diff / 86400)}д`;
};

const GatewaysPage: React.FC = () => {
  const { data: gatewaysData, loading: gatewaysLoading, refetch: refetchGateways } = useQuery(GATEWAYS_QUERY);
  const [syncGateway] = useMutation(SYNC_GATEWAY_CONFIG);

  const [gatewayEditOpen, setGatewayEditOpen] = useState(false);
  const [selectedGateway, setSelectedGateway] = useState<Gateway | null>(null);
  const [syncingGateway, setSyncingGateway] = useState<number | null>(null);
  const [syncingStatus, setSyncingStatus] = useState<string>('');

  const syncGatewayConfig = async (gatewayId: number, direction: 'push' | 'pull') => {
    setSyncingGateway(gatewayId);
    setSyncingStatus(direction === 'push' ? 'Изтегляне на данни от Gateway...' : 'Изпращане на данни към Gateway...');
    try {
      await syncGateway({ variables: { id: gatewayId, direction } });
      setSyncingStatus(direction === 'push' ? 'Успешно изтеглено!' : 'Успешно изпратено!');
      refetchGateways();
    } catch (err) {
      setSyncingStatus(`Грешка: ${getErrorMessage(err)}`);
    }
    setTimeout(() => { setSyncingGateway(null); setSyncingStatus(''); }, 3000);
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">Регистрирани Gateways</Typography>
          <IconButton onClick={() => refetchGateways()}><RefreshIcon /></IconButton>
        </Box>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead sx={{ bgcolor: 'action.hover' }}>
              <TableRow>
                <TableCell>Статус</TableCell>
                <TableCell>Име</TableCell>
                <TableCell>Alias</TableCell>
                <TableCell>IP Адрес</TableCell>
                <TableCell>Heartbeat</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {gatewaysLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : gatewaysData?.gateways?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    Няма регистрирани gateways
                  </TableCell>
                </TableRow>
              ) : (
                gatewaysData?.gateways?.map((gw: any) => (
                  <TableRow key={gw.id}>
                    <TableCell>
                      <Chip
                        size="small"
                        label={gw.isActive ? 'Активен' : 'Неактивен'}
                        color={gw.isActive ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>{gw.name}</TableCell>
                    <TableCell>{gw.alias || '-'}</TableCell>
                    <TableCell>{gw.ipAddress || '-'}</TableCell>
                    <TableCell>{formatTimeAgo(gw.lastHeartbeat)}</TableCell>
                    <TableCell>
                      {syncingGateway === gw.id ? (
                        <Typography variant="caption" color="primary">{syncingStatus}</Typography>
                      ) : (
                        <>
                          <IconButton
                            size="small"
                            title="Pull from Gateway"
                            onClick={() => syncGatewayConfig(gw.id, 'push')}
                          >
                            <DownloadIcon fontSize="inherit" />
                          </IconButton>
                          <IconButton
                            size="small"
                            title="Push to Gateway"
                            onClick={() => syncGatewayConfig(gw.id, 'pull')}
                          >
                            <UploadIcon fontSize="inherit" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => { setSelectedGateway(gw); setGatewayEditOpen(true); }}
                          >
                            <EditIcon fontSize="inherit" />
                          </IconButton>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>

      <GatewayEditDialog
        open={gatewayEditOpen}
        onClose={() => setGatewayEditOpen(false)}
        gateway={selectedGateway}
        onSuccess={() => { setGatewayEditOpen(false); refetchGateways(); }}
      />
    </Card>
  );
};

export default GatewaysPage;
