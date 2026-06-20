import React, { useState, useMemo } from 'react';
import {
  Container, Typography, Box, Paper, Button, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField,
  Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, IconButton, Tooltip, TablePagination, TableSortLabel,
  CircularProgress,
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import {
  GET_PERSONALITY_TEST_ASSIGNMENTS, GET_PERSONALITY_TEMPLATES,
} from '../api/queries';
import {
  ASSIGN_PERSONALITY_TEST, REASSIGN_PERSONALITY_TEST,
} from '../api/mutations';
import { PersonalityTestAssignment, PersonalityTestTemplate } from '../types';
import { useError } from '../../../context/ErrorContext';
import AddIcon from '@mui/icons-material/Add';
import ReplayIcon from '@mui/icons-material/Replay';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ScheduleIcon from '@mui/icons-material/Schedule';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import type { ReactElement } from 'react';

const GET_USERS_SIMPLE = gql`
  query GetUsersSimple {
    users(limit: 1000) {
      users {
        id
        firstName
        lastName
      }
    }
  }
`;

const STATUS_LABELS: Record<string, string> = {
  pending: 'Чакащ',
  completed: 'Завършен',
  overdue: 'Просрочен',
};

const STATUS_COLORS: Record<string, 'warning' | 'success' | 'error'> = {
  pending: 'warning',
  completed: 'success',
  overdue: 'error',
};

const STATUS_ICONS: Record<string, ReactElement> = {
  pending: <ScheduleIcon fontSize="small" />,
  completed: <CheckCircleIcon fontSize="small" />,
  overdue: <WarningAmberIcon fontSize="small" />,
};

const TestAssignmentManager: React.FC = () => {
  const { showSuccess, showError } = useError();

  const { data: assignmentsData, loading: assignmentsLoading, refetch: refetchAssignments } = useQuery(GET_PERSONALITY_TEST_ASSIGNMENTS);
  const { data: templatesData } = useQuery(GET_PERSONALITY_TEMPLATES);
  const { data: usersData } = useQuery(GET_USERS_SIMPLE);

  const [assignTest] = useMutation(ASSIGN_PERSONALITY_TEST);
  const [reassignTest] = useMutation(REASSIGN_PERSONALITY_TEST);

  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | ''>('');
  const [dueDate, setDueDate] = useState('');
  const [assignAll, setAssignAll] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [reassignDialogOpen, setReassignDialogOpen] = useState(false);
  const [reassignTarget, setReassignTarget] = useState<PersonalityTestAssignment | null>(null);
  const [reassignDueDate, setReassignDueDate] = useState('');
  const [reassignTemplateId, setReassignTemplateId] = useState<number | ''>('');
  const [reassigning, setReassigning] = useState(false);

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [sortField, setSortField] = useState<'userName' | 'dueBy' | 'status' | 'templateName'>('dueBy');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  const assignments: PersonalityTestAssignment[] = useMemo(() => {
    const list = assignmentsData?.personalityTestAssignments || [];
    if (statusFilter) return list.filter((a: PersonalityTestAssignment) => a.status === statusFilter);
    return list;
  }, [assignmentsData, statusFilter]);

  const sorted = useMemo(() => {
    return [...assignments].sort((a, b) => {
      let cmp = 0;
      if (sortField === 'userName') cmp = a.userName.localeCompare(b.userName);
      else if (sortField === 'templateName') cmp = a.templateName.localeCompare(b.templateName);
      else if (sortField === 'status') cmp = a.status.localeCompare(b.status);
      else if (sortField === 'dueBy') cmp = a.dueBy.localeCompare(b.dueBy);
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [assignments, sortField, sortDir]);

  const paginated = sorted.slice(page * rowsPerPage, (page + 1) * rowsPerPage);

  const templates: PersonalityTestTemplate[] = templatesData?.personalityTemplates || [];
  const users: { id: number; firstName: string; lastName: string }[] = usersData?.users?.users || [];

  const openAssignDialog = () => {
    setSelectedUserIds([]);
    setSelectedTemplateId('');
    setDueDate('');
    setAssignAll(false);
    setAssignDialogOpen(true);
  };

  const handleAssign = async () => {
    if (!selectedTemplateId) { showError('Изберете шаблон'); return; }
    if (!dueDate) { showError('Изберете краен срок'); return; }
    if (!assignAll && selectedUserIds.length === 0) { showError('Изберете потребители или отбележете "Всички"'); return; }
    setAssigning(true);
    try {
      await assignTest({
        variables: {
          userIds: assignAll ? [] : selectedUserIds,
          templateId: selectedTemplateId,
          dueBy: new Date(dueDate).toISOString(),
        },
      });
      showSuccess('Тестовете са назначени успешно');
      setAssignDialogOpen(false);
      refetchAssignments();
    } catch (err: any) {
      showError(err.message || 'Грешка при назначаване');
    } finally {
      setAssigning(false);
    }
  };

  const openReassignDialog = (assignment: PersonalityTestAssignment) => {
    setReassignTarget(assignment);
    setReassignDueDate(assignment.dueBy.slice(0, 16));
    setReassignTemplateId(assignment.templateId);
    setReassignDialogOpen(true);
  };

  const handleReassign = async () => {
    if (!reassignTarget) return;
    setReassigning(true);
    try {
      await reassignTest({
        variables: {
          assignmentId: reassignTarget.id,
          dueBy: reassignDueDate ? new Date(reassignDueDate).toISOString() : null,
          templateId: reassignTemplateId || null,
        },
      });
      showSuccess('Тестът е преназначен успешно');
      setReassignDialogOpen(false);
      setReassignTarget(null);
      refetchAssignments();
    } catch (err: any) {
      showError(err.message || 'Грешка при преназначаване');
    } finally {
      setReassigning(false);
    }
  };

  const toggleUserSelection = (id: number) => {
    setSelectedUserIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  if (assignmentsLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Назначаване на личностни тестове</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openAssignDialog}>
          Назначаване на тест
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        {[
          { key: null, label: 'Всички' },
          { key: 'pending', label: 'Чакащи' },
          { key: 'overdue', label: 'Просрочени' },
          { key: 'completed', label: 'Завършени' },
        ].map(f => (
          <Chip
            key={f.key || 'all'}
            label={f.label}
            variant={statusFilter === f.key ? 'filled' : 'outlined'}
            color={f.key === 'overdue' ? 'error' : f.key === 'completed' ? 'success' : f.key === 'pending' ? 'warning' : 'default'}
            onClick={() => setStatusFilter(f.key)}
          />
        ))}
      </Box>

      {sorted.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">Няма назначени тестове</Typography>
        </Paper>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>
                    <TableSortLabel active={sortField === 'userName'} direction={sortField === 'userName' ? sortDir : 'asc'} onClick={() => { setSortField('userName'); setSortDir(d => d === 'asc' ? 'desc' : 'asc'); }}>Потребител</TableSortLabel>
                  </TableCell>
                  <TableCell>Имейл</TableCell>
                  <TableCell>
                    <TableSortLabel active={sortField === 'templateName'} direction={sortField === 'templateName' ? sortDir : 'asc'} onClick={() => { setSortField('templateName'); setSortDir(d => d === 'asc' ? 'desc' : 'asc'); }}>Шаблон</TableSortLabel>
                  </TableCell>
                  <TableCell>Назначил</TableCell>
                  <TableCell>
                    <TableSortLabel active={sortField === 'dueBy'} direction={sortField === 'dueBy' ? sortDir : 'asc'} onClick={() => { setSortField('dueBy'); setSortDir(d => d === 'asc' ? 'desc' : 'asc'); }}>Краен срок</TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel active={sortField === 'status'} direction={sortField === 'status' ? sortDir : 'asc'} onClick={() => { setSortField('status'); setSortDir(d => d === 'asc' ? 'desc' : 'asc'); }}>Статус</TableSortLabel>
                  </TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginated.map(a => {
                  const isOverdue = a.status === 'overdue' || (a.status === 'pending' && new Date(a.dueBy) < new Date());
                  return (
                    <TableRow key={a.id} sx={{ bgcolor: isOverdue && a.status !== 'completed' ? '#fff3e0' : undefined }}>
                      <TableCell>{a.userName || `ID:${a.userId}`}</TableCell>
                      <TableCell>{a.userEmail}</TableCell>
                      <TableCell>{a.templateName}</TableCell>
                      <TableCell>{a.assignerName}</TableCell>
                      <TableCell>{new Date(a.dueBy).toLocaleDateString('bg-BG')}</TableCell>
                      <TableCell>
                        <Chip
                          icon={STATUS_ICONS[a.status === 'overdue' || isOverdue ? 'overdue' : a.status]}
                          label={a.status === 'overdue' || (a.status === 'pending' && isOverdue) ? 'Просрочен' : STATUS_LABELS[a.status] || a.status}
                          color={a.status === 'overdue' || isOverdue ? 'error' : STATUS_COLORS[a.status] || 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        {(a.status === 'pending' || a.status === 'overdue') && (
                          <Tooltip title="Преназначаване">
                            <IconButton size="small" onClick={() => openReassignDialog(a)}>
                              <ReplayIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={sorted.length}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={e => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
            labelRowsPerPage="Резултати на страница:"
          />
        </>
      )}

      {/* Assign Dialog */}
      <Dialog open={assignDialogOpen} onClose={() => setAssignDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Назначаване на личностен тест</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              select
              label="Шаблон"
              value={selectedTemplateId}
              onChange={e => setSelectedTemplateId(Number(e.target.value))}
              SelectProps={{ native: true }}
              fullWidth
            >
              <option value="">Изберете шаблон</option>
              {templates.filter(t => t.isActive).map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </TextField>

            <TextField
              label="Краен срок"
              type="datetime-local"
              value={dueDate}
              onChange={e => setDueDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={assignAll ? 'Всички активни потребители' : 'Избрани потребители'}
                color={assignAll ? 'primary' : 'default'}
                onClick={() => setAssignAll(!assignAll)}
                variant={assignAll ? 'filled' : 'outlined'}
              />
              <Typography variant="caption" color="text.secondary">(щракни за смяна)</Typography>
            </Box>

            {!assignAll && (
              <Box sx={{ maxHeight: 250, overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1, p: 1 }}>
                {users.map(u => (
                  <Chip
                    key={u.id}
                    label={`${u.firstName} ${u.lastName}`}
                    variant={selectedUserIds.includes(u.id) ? 'filled' : 'outlined'}
                    color={selectedUserIds.includes(u.id) ? 'primary' : 'default'}
                    onClick={() => toggleUserSelection(u.id)}
                    size="small"
                    sx={{ m: 0.3 }}
                  />
                ))}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignDialogOpen(false)}>Отказ</Button>
          <Button variant="contained" onClick={handleAssign} disabled={assigning}>
            {assigning ? 'Назначаване...' : 'Назначи'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reassign Dialog */}
      <Dialog open={reassignDialogOpen} onClose={() => setReassignDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Преназначаване на тест</DialogTitle>
        <DialogContent>
          {reassignTarget && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <Typography variant="body2">Потребител: <strong>{reassignTarget.userName}</strong></Typography>
              <Typography variant="body2">Текущ шаблон: <strong>{reassignTarget.templateName}</strong></Typography>

              <TextField
                select
                label="Нов шаблон"
                value={reassignTemplateId}
                onChange={e => setReassignTemplateId(Number(e.target.value))}
                SelectProps={{ native: true }}
                fullWidth
              >
                <option value={reassignTarget.templateId}>{reassignTarget.templateName} (текущ)</option>
                {templates.filter(t => t.isActive && t.id !== reassignTarget.templateId).map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </TextField>

              <TextField
                label="Нов краен срок"
                type="datetime-local"
                value={reassignDueDate}
                onChange={e => setReassignDueDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
                fullWidth
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReassignDialogOpen(false)}>Отказ</Button>
          <Button variant="contained" onClick={handleReassign} disabled={reassigning}>
            {reassigning ? 'Преназначаване...' : 'Преназначи'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TestAssignmentManager;
