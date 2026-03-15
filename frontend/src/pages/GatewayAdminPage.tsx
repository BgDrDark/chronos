import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Tabs,
  Tab
} from '@mui/material';
import {
  Edit as EditIcon,
  Computer as ComputerIcon,
  Print as PrintIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useQuery } from '@apollo/client';
import {
  GATEWAYS_QUERY,
  TERMINALS_QUERY,
  PRINTERS_QUERY,
  GATEWAY_STATS_QUERY
} from '../graphql/queries';

interface Gateway {
  id: number;
  name: string;
  hardwareUuid: string;
  alias: string | null;
  ipAddress: string | null;
  localHostname: string | null;
  terminalPort: number;
  webPort: number;
  isActive: boolean;
  lastHeartbeat: string | null;
  registeredAt: string;
}

interface Terminal {
  id: number;
  hardwareUuid: string;
  deviceName: string | null;
  deviceType: string | null;
  deviceModel: string | null;
  osVersion: string | null;
  gatewayId: number | null;
  isActive: boolean;
  lastSeen: string | null;
  totalScans: number;
  alias: string | null;
}

interface Printer {
  id: number;
  name: string;
  printerType: string | null;
  ipAddress: string | null;
  port: number;
  protocol: string | null;
  windowsShareName: string | null;
  manufacturer: string | null;
  model: string | null;
  gatewayId: number;
  isActive: boolean;
  isDefault: boolean;
  lastTest: string | null;
  lastError: string | null;
}

interface GatewayStats {
  totalGateways: number;
  activeGateways: number;
  inactiveGateways: number;
  totalTerminals: number;
  activeTerminals: number;
  totalPrinters: number;
  activePrinters: number;
}

const GatewayAdminPage: React.FC = () => {
  const [selectedGateway, setSelectedGateway] = useState<Gateway | null>(null);
  const [tab, setTab] = useState(0);
  const [aliasDialogOpen, setAliasDialogOpen] = useState(false);
  const [aliasValue, setAliasValue] = useState('');

  const { data: statsData, loading: statsLoading } = useQuery<{ gatewayStats: GatewayStats }>(GATEWAY_STATS_QUERY);
  const { data: gatewaysData, loading: gatewaysLoading, refetch: refetchGateways } = useQuery<{ gateways: Gateway[] }>(GATEWAYS_QUERY);
  const { data: terminalsData, loading: terminalsLoading } = useQuery<{ terminals: Terminal[] }>(TERMINALS_QUERY, {
    variables: { gatewayId: selectedGateway?.id }
  });
  const { data: printersData, loading: printersLoading } = useQuery<{ printers: Printer[] }>(PRINTERS_QUERY, {
    variables: { gatewayId: selectedGateway?.id }
  });

  const handleGatewayClick = (gateway: Gateway) => {
    setSelectedGateway(gateway);
    setTab(0);
  };

  const handleEditAlias = () => {
    if (selectedGateway) {
      setAliasValue(selectedGateway.alias || '');
      setAliasDialogOpen(true);
    }
  };

  const formatTimeAgo = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Gateway Management
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Gateways
              </Typography>
              <Typography variant="h4">
                {statsLoading ? '-' : statsData?.gatewayStats.totalGateways || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active
              </Typography>
              <Typography variant="h4" color="success.main">
                {statsLoading ? '-' : statsData?.gatewayStats.activeGateways || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Terminals
              </Typography>
              <Typography variant="h4">
                {statsLoading ? '-' : statsData?.gatewayStats.totalTerminals || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Printers
              </Typography>
              <Typography variant="h4">
                {statsLoading ? '-' : statsData?.gatewayStats.totalPrinters || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Gateway List */}
        <Grid size={{ xs: 12, md: selectedGateway ? 5 : 12 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Gateways</Typography>
                <IconButton onClick={() => refetchGateways()}>
                  <RefreshIcon />
                </IconButton>
              </Box>

              {gatewaysLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Status</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Alias</TableCell>
                        <TableCell>IP Address</TableCell>
                        <TableCell>Last Seen</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {gatewaysData?.gateways.map((gateway) => (
                        <TableRow
                          key={gateway.id}
                          hover
                          onClick={() => handleGatewayClick(gateway)}
                          selected={selectedGateway?.id === gateway.id}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell>
                            <Chip
                              size="small"
                              label={gateway.isActive ? 'Active' : 'Inactive'}
                              color={gateway.isActive ? 'success' : 'default'}
                            />
                          </TableCell>
                          <TableCell>{gateway.name}</TableCell>
                          <TableCell>{gateway.alias || '-'}</TableCell>
                          <TableCell>{gateway.ipAddress || '-'}</TableCell>
                          <TableCell>{formatTimeAgo(gateway.lastHeartbeat)}</TableCell>
                        </TableRow>
                      ))}
                      {(!gatewaysData?.gateways || gatewaysData.gateways.length === 0) && (
                        <TableRow>
                          <TableCell colSpan={5} align="center">
                            No gateways registered
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Gateway Details */}
        {selectedGateway && (
          <Grid size={{ xs: 12, md: 7 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    {selectedGateway.name}
                  </Typography>
                  <Button
                    variant="outlined"
                    startIcon={<EditIcon />}
                    onClick={handleEditAlias}
                    size="small"
                  >
                    Edit Alias
                  </Button>
                </Box>

                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="textSecondary">Hardware UUID</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {selectedGateway.hardwareUuid.substring(0, 16)}...
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="textSecondary">Alias</Typography>
                    <Typography variant="body2">{selectedGateway.alias || '-'}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="textSecondary">IP Address</Typography>
                    <Typography variant="body2">{selectedGateway.ipAddress || '-'}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="textSecondary">Last Heartbeat</Typography>
                    <Typography variant="body2">{formatTimeAgo(selectedGateway.lastHeartbeat)}</Typography>
                  </Grid>
                </Grid>

                <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
                  <Tab icon={<ComputerIcon />} label="Terminals" />
                  <Tab icon={<PrintIcon />} label="Printers" />
                </Tabs>

                {tab === 0 && (
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Status</TableCell>
                          <TableCell>Device</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Last Seen</TableCell>
                          <TableCell>Scans</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {terminalsLoading ? (
                          <TableRow>
                            <TableCell colSpan={5} align="center">
                              <CircularProgress size={20} />
                            </TableCell>
                          </TableRow>
                        ) : (
                          terminalsData?.terminals
                            .filter((t) => t.gatewayId === selectedGateway.id)
                            .map((terminal) => (
                              <TableRow key={terminal.id}>
                                <TableCell>
                                  <Chip
                                    size="small"
                                    label={terminal.isActive ? 'Online' : 'Offline'}
                                    color={terminal.isActive ? 'success' : 'error'}
                                  />
                                </TableCell>
                                <TableCell>{terminal.deviceName || terminal.hardwareUuid.substring(0, 8)}</TableCell>
                                <TableCell>{terminal.deviceType || '-'}</TableCell>
                                <TableCell>{formatTimeAgo(terminal.lastSeen)}</TableCell>
                                <TableCell>{terminal.totalScans}</TableCell>
                              </TableRow>
                            ))
                        )}
                        {(!terminalsData?.terminals || terminalsData.terminals.filter((t) => t.gatewayId === selectedGateway.id).length === 0) && (
                          <TableRow>
                            <TableCell colSpan={5} align="center">No terminals</TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}

                {tab === 1 && (
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Status</TableCell>
                          <TableCell>Name</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Address</TableCell>
                          <TableCell>Default</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {printersLoading ? (
                          <TableRow>
                            <TableCell colSpan={5} align="center">
                              <CircularProgress size={20} />
                            </TableCell>
                          </TableRow>
                        ) : (
                          printersData?.printers
                            .filter((p) => p.gatewayId === selectedGateway.id)
                            .map((printer) => (
                              <TableRow key={printer.id}>
                                <TableCell>
                                  <Chip
                                    size="small"
                                    label={printer.isActive ? 'Active' : 'Inactive'}
                                    color={printer.isActive ? 'success' : 'default'}
                                  />
                                </TableCell>
                                <TableCell>{printer.name}</TableCell>
                                <TableCell>{printer.printerType || '-'}</TableCell>
                                <TableCell>{printer.ipAddress || printer.windowsShareName || '-'}</TableCell>
                                <TableCell>
                                  {printer.isDefault && <Chip size="small" label="Default" color="primary" />}
                                </TableCell>
                              </TableRow>
                            ))
                        )}
                        {(!printersData?.printers || printersData.printers.filter((p) => p.gatewayId === selectedGateway.id).length === 0) && (
                          <TableRow>
                            <TableCell colSpan={5} align="center">No printers</TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Edit Alias Dialog */}
      <Dialog open={aliasDialogOpen} onClose={() => setAliasDialogOpen(false)}>
        <DialogTitle>Edit Gateway Alias</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Alias"
            fullWidth
            value={aliasValue}
            onChange={(e) => setAliasValue(e.target.value)}
            placeholder="e.g., Вход Главен"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAliasDialogOpen(false)}>Cancel</Button>
          <Button onClick={() => setAliasDialogOpen(false)} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GatewayAdminPage;
