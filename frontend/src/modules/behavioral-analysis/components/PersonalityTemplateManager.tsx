import React, { useState, useMemo } from 'react';
import {
  Container, Typography, Box, Paper, Button, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControlLabel, Switch, Alert,
  Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, IconButton, Tooltip, TablePagination, TableSortLabel,
} from '@mui/material';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_PERSONALITY_TEMPLATES, GET_PERSONALITY_QUESTIONS,
} from '../api/queries';
import {
  CREATE_PERSONALITY_TEMPLATE, UPDATE_PERSONALITY_TEMPLATE,
  DELETE_PERSONALITY_TEMPLATE,
} from '../api/mutations';
import { PersonalityTestTemplate } from '../types';
import { useError } from '../../../context/ErrorContext';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';

const FACTOR_LABELS: Record<string, string> = {
  openness: 'Отвореност',
  conscientiousness: 'Съзнателност',
  extraversion: 'Екстраверсия',
  agreeableness: 'Дружелюбност',
  neuroticism: 'Невротизъм',
};

const FACTOR_COLORS: Record<string, string> = {
  openness: '#1976d2',
  conscientiousness: '#388e3c',
  extraversion: '#fbc02d',
  agreeableness: '#e64a19',
  neuroticism: '#7b1fa2',
};

const PersonalityTemplateManager: React.FC = () => {
  const { showSuccess, showError } = useError();

  const { data: templatesData, loading: templatesLoading, refetch: refetchTemplates } = useQuery(GET_PERSONALITY_TEMPLATES);
  const { data: allQuestionsData, loading: questionsLoading } = useQuery(GET_PERSONALITY_QUESTIONS, {
    variables: { templateId: null },
  });

  const [createTemplate] = useMutation(CREATE_PERSONALITY_TEMPLATE);
  const [updateTemplate] = useMutation(UPDATE_PERSONALITY_TEMPLATE);
  const [deleteTemplate] = useMutation(DELETE_PERSONALITY_TEMPLATE);

  // Editing state — inline, not in dialog
  const [editing, setEditing] = useState<{ id: number | null; name: string; shuffle: boolean; selectedIds: Set<number> } | null>(null);

  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [sortField, setSortField] = useState<'id' | 'factor'>('factor');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const templates: PersonalityTestTemplate[] = templatesData?.personalityTemplates || [];
  const allQuestions: any[] = allQuestionsData?.personalityQuestions || [];

  const factorCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const q of allQuestions) counts[q.factor] = (counts[q.factor] || 0) + 1;
    return counts;
  }, [allQuestions]);

  const selectedFactorCounts = useMemo(() => {
    if (!editing) return {};
    const counts: Record<string, number> = {};
    for (const q of allQuestions) {
      if (editing.selectedIds.has(q.id)) counts[q.factor] = (counts[q.factor] || 0) + 1;
    }
    return counts;
  }, [editing, allQuestions]);

  const sortedQuestions = useMemo(() => {
    const sorted = [...allQuestions];
    sorted.sort((a, b) => {
      const cmp = sortField === 'factor' ? a.factor.localeCompare(b.factor) : a.id - b.id;
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return sorted;
  }, [allQuestions, sortField, sortDir]);

  const handleSort = (field: 'id' | 'factor') => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('asc'); }
  };

  const toggleQuestion = (id: number) => {
    if (!editing) return;
    setEditing(prev => {
      if (!prev) return prev;
      const next = new Set(prev.selectedIds);
      if (next.has(id)) next.delete(id);
      else if (next.size < 50) next.add(id);
      return { ...prev, selectedIds: next };
    });
  };

  const openCreate = () => {
    setEditing({ id: null, name: '', shuffle: true, selectedIds: new Set() });
    setPage(0);
  };

  const openEdit = (t: PersonalityTestTemplate) => {
    setEditing({ id: t.id, name: t.name, shuffle: t.shuffle, selectedIds: new Set(t.selectedQuestionIds || []) });
    setPage(0);
  };

  const cancelEditing = () => setEditing(null);

  const handleSave = async () => {
    if (!editing) return;
    if (!editing.name.trim()) { showError('Името е задължително.'); return; }
    if (editing.selectedIds.size !== 50) { showError('Трябва да изберете точно 50 въпроса.'); return; }
    try {
      const ids = Array.from(editing.selectedIds);
      if (editing.id !== null) {
        await updateTemplate({
          variables: { input: { id: editing.id, name: editing.name, selectedQuestionIds: ids, shuffle: editing.shuffle } },
        });
        showSuccess('Шаблонът е обновен.');
      } else {
        await createTemplate({
          variables: { input: { name: editing.name, selectedQuestionIds: ids, shuffle: editing.shuffle } },
        });
        showSuccess('Шаблонът е създаден.');
      }
      setEditing(null);
      await refetchTemplates();
    } catch (err: any) {
      showError(err.message);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteTemplate({ variables: { id } });
      showSuccess('Шаблонът е изтрит.');
      setDeleteConfirm(null);
      if (editing?.id === id) setEditing(null);
      await refetchTemplates();
    } catch (err: any) {
      showError(err.message);
    }
  };

  if (templatesLoading || questionsLoading) {
    return <Box sx={{ p: 3, textAlign: 'center' }}>Зареждане...</Box>;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Управление на шаблони за личностов тест</Typography>
        {!editing && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            Нов шаблон
          </Button>
        )}
      </Box>

      {/* Editing form — inline, always visible while editing */}
      {editing && (
        <Paper sx={{ p: 3, mb: 3, border: '2px solid #1976d2' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" color="primary">
              {editing.id !== null ? 'Редактиране на шаблон' : 'Нов шаблон'}
            </Typography>
            <IconButton onClick={cancelEditing} size="small"><CloseIcon /></IconButton>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mb: 2 }}>
            <TextField
              label="Име на шаблона"
              value={editing.name}
              onChange={e => setEditing({ ...editing, name: e.target.value })}
              size="small"
              sx={{ minWidth: 300 }}
            />
            <FormControlLabel
              control={<Switch checked={editing.shuffle} onChange={e => setEditing({ ...editing, shuffle: e.target.checked })} />}
              label="Разбъркване"
            />
            <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSave} disabled={editing.selectedIds.size !== 50 || !editing.name.trim()}>
              Запази
            </Button>
          </Box>
          <Alert severity={editing.selectedIds.size === 50 ? 'success' : 'info'} sx={{ mb: 1 }}>
            Избрани <strong>{editing.selectedIds.size}</strong> от 50 въпроса.
            {Object.entries(selectedFactorCounts).map(([factor, count]) => (
              <Chip key={factor} label={`${FACTOR_LABELS[factor] || factor}: ${count}`} size="small" variant="outlined" sx={{ ml: 0.5, borderColor: FACTOR_COLORS[factor] }} />
            ))}
            {editing.selectedIds.size !== 50 && ' — Изберете от таблицата долу.'}
          </Alert>
        </Paper>
      )}

      {/* Existing templates */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Съществуващи шаблони</Typography>
        {templates.length === 0 ? (
          <Typography color="text.secondary">Няма създадени шаблони.</Typography>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Име</TableCell>
                  <TableCell>Брой въпроси</TableCell>
                  <TableCell>Разбъркване</TableCell>
                  <TableCell>Активен</TableCell>
                  <TableCell>Създаден</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {templates.map((t) => (
                  <TableRow key={t.id} selected={editing?.id === t.id}>
                    <TableCell>{t.name}</TableCell>
                    <TableCell>{t.selectedQuestionIds?.length || 0}</TableCell>
                    <TableCell>{t.shuffle ? 'Да' : 'Не'}</TableCell>
                    <TableCell>{t.isActive ? 'Да' : 'Не'}</TableCell>
                    <TableCell>{new Date(t.createdAt).toLocaleDateString('bg-BG')}</TableCell>
                    <TableCell align="right">
                      <Tooltip title="Редактирай">
                        <span><IconButton size="small" onClick={() => openEdit(t)} disabled={!!editing}><EditIcon /></IconButton></span>
                      </Tooltip>
                      <Tooltip title="Изтрий">
                        <span><IconButton size="small" color="error" onClick={() => setDeleteConfirm(t.id)} disabled={!!editing}><DeleteIcon /></IconButton></span>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Question pool */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>Въпросник (200 IPIP-50 въпроса)</Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {Object.entries(factorCounts).map(([factor, count]) => (
            <Chip key={factor} label={`${FACTOR_LABELS[factor] || factor}: ${count}`} sx={{ bgcolor: FACTOR_COLORS[factor], color: '#fff' }} size="small" />
          ))}
        </Box>

        <TableContainer sx={{ maxHeight: 500 }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox" sx={{ minWidth: 48 }} />
                <TableCell sx={{ minWidth: 50 }}>
                  <TableSortLabel active={sortField === 'id'} direction={sortField === 'id' ? sortDir : 'asc'} onClick={() => handleSort('id')}>ID</TableSortLabel>
                </TableCell>
                <TableCell sx={{ minWidth: 80 }}>
                  <TableSortLabel active={sortField === 'factor'} direction={sortField === 'factor' ? sortDir : 'asc'} onClick={() => handleSort('factor')}>Фактор</TableSortLabel>
                </TableCell>
                <TableCell sx={{ minWidth: 200 }}>Въпрос (BG)</TableCell>
                <TableCell sx={{ minWidth: 200 }}>Въпрос (EN)</TableCell>
                <TableCell sx={{ minWidth: 70 }}>Посока</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedQuestions.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((q) => {
                const isSelected = editing?.selectedIds.has(q.id) ?? false;
                return (
                  <TableRow
                    key={q.id}
                    hover={!!editing}
                    selected={isSelected}
                    onClick={() => toggleQuestion(q.id)}
                    sx={{
                      cursor: editing ? 'pointer' : 'default',
                      '&.Mui-selected': { bgcolor: `${FACTOR_COLORS[q.factor]}20` },
                    }}
                  >
                    <TableCell padding="checkbox">
                      <Chip
                        label={isSelected ? `${[...(editing!.selectedIds)].indexOf(q.id) + 1}` : ''}
                        size="small"
                        variant={isSelected ? 'filled' : 'outlined'}
                        sx={{
                          minWidth: 28, height: 24,
                          bgcolor: isSelected ? FACTOR_COLORS[q.factor] : 'transparent',
                          color: isSelected ? '#fff' : '#ccc',
                          borderColor: isSelected ? FACTOR_COLORS[q.factor] : '#ccc',
                        }}
                      />
                    </TableCell>
                    <TableCell>{q.id}</TableCell>
                    <TableCell>
                      <Chip label={FACTOR_LABELS[q.factor] || q.factor} size="small" sx={{ bgcolor: FACTOR_COLORS[q.factor], color: '#fff', fontSize: '0.7rem' }} />
                    </TableCell>
                    <TableCell>{q.bg}</TableCell>
                    <TableCell sx={{ color: 'text.secondary' }}>{q.en}</TableCell>
                    <TableCell>
                      <Chip label={q.direction === 'reverse' ? 'Обратен' : 'Положителен'} size="small" variant="outlined" color={q.direction === 'reverse' ? 'warning' : 'success'} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={sortedQuestions.length}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
          rowsPerPageOptions={[25, 50, 100]}
          labelRowsPerPage="Редове на страница:"
        />
      </Paper>

      {/* Delete confirmation */}
      <Dialog open={deleteConfirm !== null} onClose={() => setDeleteConfirm(null)}>
        <DialogTitle>Потвърдете изтриването</DialogTitle>
        <DialogContent>
          <Typography>Сигурни ли сте, че искате да изтриете този шаблон? Това действие е необратимо.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirm(null)}>Отказ</Button>
          <Button onClick={() => deleteConfirm !== null && handleDelete(deleteConfirm)} variant="contained" color="error">Изтрий</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PersonalityTemplateManager;
