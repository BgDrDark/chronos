import React, { useState } from 'react';
import { getErrorMessage, Terminal } from '../../types';
import {
  Typography, Card, CardContent,
  Box, CircularProgress,
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip,
  IconButton,
} from '@mui/material';
import {
  MeetingRoom as DoorIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { TERMINALS_QUERY } from '../../graphql/queries/kioskAdmin';
import { ACCESS_DOORS_QUERY } from '../../graphql/queries';
import { DELETE_TERMINAL } from '../../graphql/mutations/kioskAdmin';
import TerminalUpdateDialog from './dialogs/TerminalDialog';

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

const TerminalsPage: React.FC = () => {
  const { data: terminalsData, loading: terminalsLoading, refetch: refetchTerminals } = useQuery(TERMINALS_QUERY);
  const { data: doorsData, loading: doorsLoading } = useQuery(ACCESS_DOORS_QUERY);
  const [deleteTerminal] = useMutation(DELETE_TERMINAL);

  const [terminalDialogOpen, setTerminalDialogOpen] = useState(false);
  const [selectedTerminal, setSelectedTerminal] = useState<Terminal | null>(null);

  const handleDeleteTerminal = async (id: number) => {
    if (window.confirm('Сигурни ли сте, че искате да изтриете този терминал?')) {
      try {
        await deleteTerminal({ variables: { id } });
        refetchTerminals();
      } catch (e) {
        alert(getErrorMessage(e));
      }
    }
  };

  const loading = terminalsLoading || doorsLoading;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">Активни Терминали</Typography>
          <IconButton onClick={() => refetchTerminals()}><RefreshIcon /></IconButton>
        </Box>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead sx={{ bgcolor: 'action.hover' }}>
              <TableRow>
                <TableCell>Статус</TableCell>
                <TableCell>Alias / Device</TableCell>
                <TableCell>Хардуерен ID</TableCell>
                <TableCell>Свързана врата</TableCell>
                <TableCell>Последна активност</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : terminalsData?.terminals?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    Няма регистрирани терминали
                  </TableCell>
                </TableRow>
              ) : (
                terminalsData?.terminals?.map((t: any) => {
                  const associatedDoor = doorsData?.accessDoors?.find(
                    (d: any) => d.terminalId === t.hardwareUuid
                  );
                  return (
                    <TableRow key={t.id}>
                      <TableCell>
                        <Chip
                          size="small"
                          label={t.isActive ? 'Online' : 'Offline'}
                          color={t.isActive ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {t.alias || t.deviceName}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t.deviceModel} ({t.osVersion})
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {t.hardwareUuid}
                      </TableCell>
                      <TableCell>
                        {associatedDoor ? (
                          <Chip
                            icon={<DoorIcon />}
                            label={`${associatedDoor.name} (${associatedDoor.terminalMode})`}
                            color="primary"
                            size="small"
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            Няма свързана врата
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{formatTimeAgo(t.lastSeen)}</TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => {
                            setSelectedTerminal(t);
                            setTerminalDialogOpen(true);
                          }}
                          title="Редактирай"
                        >
                          <EditIcon fontSize="inherit" />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteTerminal(t.id)}
                          title="Изтрий"
                        >
                          <DeleteIcon fontSize="inherit" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>

      <TerminalUpdateDialog
        open={terminalDialogOpen}
        onClose={() => setTerminalDialogOpen(false)}
        terminal={selectedTerminal}
        doors={doorsData?.accessDoors || []}
        onSuccess={() => {
          setTerminalDialogOpen(false);
          refetchTerminals();
        }}
      />
    </Card>
  );
};

export default TerminalsPage;
