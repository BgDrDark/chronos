import React, { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import {
  Box, Typography, TextField, Button, Grid, Card, CardContent, IconButton,
  Tooltip, InputAdornment, MenuItem, Chip, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { Delete as DeleteIcon, Add as AddIcon, Save as SaveIcon } from '@mui/icons-material';
import { useError, extractErrorMessage } from '../context/ErrorContext';
import { InfoIcon } from '../components/ui/InfoIcon';
import {
  GET_SHIFTS_QUERY,
  GET_USERS_QUERY,
  CREATE_SHIFT_MUTATION,
  DELETE_SHIFT_MUTATION,
  BULK_SET_SCHEDULE_MUTATION,
  GET_TEMPLATES_FOR_PREVIEW,
} from '../graphql/queries';

const CREATE_TEMPLATE = gql`
  mutation CreateTemplate($name: String!, $description: String, $items: [ScheduleTemplateItemInput!]!) {
    createScheduleTemplate(name: $name, description: $description, items: $items) { id }
  }
`;

const DELETE_TEMPLATE = gql`
  mutation DeleteTemplate($id: Int!) { deleteScheduleTemplate(id: $id) }
`;

const ShiftsSection: React.FC = () => {
  const { data, refetch } = useQuery(GET_SHIFTS_QUERY);
  const [createShift] = useMutation(CREATE_SHIFT_MUTATION);
  const [deleteShift] = useMutation(DELETE_SHIFT_MUTATION);
  const { showError, showSuccess } = useError();

  const [name, setName] = useState('');
  const [start, setStart] = useState('09:00');
  const [end, setEnd] = useState('17:00');
  const [tolerance, setTolerance] = useState('15');
  const [breakDuration, setBreakDuration] = useState('60');
  const [payMultiplier, setPayMultiplier] = useState('1.0');

  const handleCreate = async () => {
    try {
      await createShift({ variables: { name, startTime: start, endTime: end, tolerance: parseInt(tolerance), breakDuration: parseInt(breakDuration), payMultiplier } });
      setName('');
      refetch();
      showSuccess('Смяната е създадена.');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteShift({ variables: { id } });
      refetch();
      showSuccess('Смяната е изтрита.');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Създаване на нова смяна</Typography>
      <Grid container spacing={2} alignItems="center">
        <Grid size={{ xs: 12, sm: 2 }}>
          <TextField fullWidth label="Име на смяната" value={name} onChange={(e) => setName(e.target.value)}
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Наименование на смяната (напр. Сутрешна, Вечерна)" /></InputAdornment> } }} />
        </Grid>
        <Grid size={{ xs: 6, sm: 2 }}>
          <TextField fullWidth label="Начало" type="time" value={start} onChange={(e) => setStart(e.target.value)} InputLabelProps={{ shrink: true }}
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Час на започване на смяната" /></InputAdornment> } }} />
        </Grid>
        <Grid size={{ xs: 6, sm: 2 }}>
          <TextField fullWidth label="Край" type="time" value={end} onChange={(e) => setEnd(e.target.value)} InputLabelProps={{ shrink: true }}
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Час на приключване на смяната" /></InputAdornment> } }} />
        </Grid>
        <Grid size={{ xs: 4, sm: 1.5 }}>
          <TextField fullWidth label="Толеранс (мин)" type="number" value={tolerance} onChange={(e) => setTolerance(e.target.value)} helperText="Прилепване на времето"
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Толеранс в минути за късно влизане/ранно излизане" /></InputAdornment> } }} />
        </Grid>
        <Grid size={{ xs: 4, sm: 1.5 }}>
          <TextField fullWidth label="Почивка (мин)" type="number" value={breakDuration} onChange={(e) => setBreakDuration(e.target.value)} helperText="Автоматично удържане"
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Продължителност на почивката в минути" /></InputAdornment> } }} />
        </Grid>
        <Grid size={{ xs: 4, sm: 2 }}>
          <TextField fullWidth label="Коефициент Заплащане" type="number" value={payMultiplier} onChange={(e) => setPayMultiplier(e.target.value)} inputProps={{ step: "0.01" }} helperText="Умножител за надницата"
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Коефициент за изчисление на заплатата" /></InputAdornment> } }} />
        </Grid>
        <Grid size={{ xs: 12, sm: 1 }}>
          <Tooltip title="Създай нова смяна" arrow>
            <Button fullWidth variant="contained" onClick={handleCreate} disabled={!name}><AddIcon /></Button>
          </Tooltip>
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>Налични смени</Typography>
      <Grid container spacing={2}>
        {data?.shifts.map((shift: any) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={shift.id}>
            <Card variant="outlined" sx={{ borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Typography variant="subtitle1" fontWeight="bold">{shift.name}</Typography>
                  <Tooltip title="Изтрий смяната" arrow>
                    <IconButton size="small" onClick={() => handleDelete(shift.id)} color="error"><DeleteIcon /></IconButton>
                  </Tooltip>
                </Box>
                <Typography variant="body2" color="text.secondary">{shift.startTime.substring(0, 5)} - {shift.endTime.substring(0, 5)}</Typography>
                <Typography variant="caption" display="block" color="text.secondary">Толеранс: {shift.toleranceMinutes} мин. | Почивка: {shift.breakDurationMinutes} мин.</Typography>
                <Typography variant="caption" display="block" sx={{ fontWeight: 'bold', color: 'primary.main' }}>Коефициент: {shift.payMultiplier}x</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

const TemplatesSection: React.FC = () => {
  const { data, loading, refetch } = useQuery(GET_TEMPLATES_FOR_PREVIEW);
  const { data: shiftsData } = useQuery(GET_SHIFTS_QUERY);
  const [createTemplate] = useMutation(CREATE_TEMPLATE);
  const [deleteTemplate] = useMutation(DELETE_TEMPLATE);
  const { showError, showSuccess } = useError();

  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [items, setItems] = useState<{ dayIndex: number; shiftId: number | null }[]>([{ dayIndex: 0, shiftId: null }]);

  const handleAddItem = () => setItems([...items, { dayIndex: items.length, shiftId: null }]);
  const handleRemoveItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index).map((item, i) => ({ ...item, dayIndex: i }));
    setItems(newItems);
  };

  const handleSave = async () => {
    try {
      await createTemplate({ variables: { name, description: desc, items: items.map(i => ({ dayIndex: i.dayIndex, shiftId: i.shiftId })) } });
      setOpen(false);
      setName(''); setDesc(''); setItems([{ dayIndex: 0, shiftId: null }]);
      refetch();
      showSuccess('Шаблонът е създаден.');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteTemplate({ variables: { id } });
      refetch();
      showSuccess('Шаблонът е изтрит.');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  if (loading) return null;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Шаблони за ротации</Typography>
        <Button startIcon={<AddIcon />} variant="outlined" onClick={() => setOpen(true)}>Нов Шаблон</Button>
      </Box>
      <Grid container spacing={2}>
        {data?.scheduleTemplates.map((t: any) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={t.id}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="subtitle1" fontWeight="bold">{t.name}</Typography>
                  <IconButton size="small" color="error" onClick={() => handleDelete(t.id)}><DeleteIcon fontSize="small" /></IconButton>
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>{t.description || 'Няма описание'}</Typography>
                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {t.items?.map((item: any) => (
                    <Chip key={item.dayIndex} label={item.shift ? item.shift.name : 'ПОЧ'} size="small" variant={item.shift ? "filled" : "outlined"} />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Създаване на шаблон</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Име на шаблона" margin="normal" value={name} onChange={e => setName(e.target.value)} />
          <TextField fullWidth label="Описание" margin="normal" value={desc} onChange={e => setDesc(e.target.value)} />
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Дни в ротацията:</Typography>
          {items.map((item, index) => (
            <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
              <Typography sx={{ minWidth: 60 }}>Ден {index + 1}:</Typography>
              <TextField select size="small" fullWidth value={item.shiftId || ''} onChange={(e) => {
                const newItems = [...items];
                newItems[index].shiftId = e.target.value ? parseInt(e.target.value as string) : null;
                setItems(newItems);
              }}>
                <MenuItem value=""><em>Почивка</em></MenuItem>
                {shiftsData?.shifts?.map((s: any) => (<MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>))}
              </TextField>
              <IconButton size="small" onClick={() => handleRemoveItem(index)} disabled={items.length === 1}><DeleteIcon fontSize="small" /></IconButton>
            </Box>
          ))}
          <Button startIcon={<AddIcon />} size="small" onClick={handleAddItem} sx={{ mt: 1 }}>Добави ден</Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Отказ</Button>
          <Button onClick={handleSave} variant="contained" startIcon={<SaveIcon />}>Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

const BulkAssignSection: React.FC = () => {
  const { data: usersData, loading: usersLoading } = useQuery(GET_USERS_QUERY, { variables: { limit: 1000 } });
  const { data: shiftsData, loading: shiftsLoading } = useQuery(GET_SHIFTS_QUERY);
  const [bulkSet, { loading: submitting }] = useMutation(BULK_SET_SCHEDULE_MUTATION);
  const { showError, showSuccess } = useError();

  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [selectedShift, setSelectedShift] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4]);

  const handleDayToggle = (day: number) => setDays(prev => prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]);

  const handleSubmit = async () => {
    try {
      await bulkSet({ variables: { userIds: selectedUsers, shiftId: parseInt(selectedShift), startDate, endDate, daysOfWeek: days } });
      setSelectedUsers([]);
      showSuccess('Графиците са генерирани успешно!');
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const dayNames = ['Пон', 'Вт', 'Ср', 'Чет', 'Пет', 'Съб', 'Нед'];

  if (usersLoading || shiftsLoading) return null;

  return (
    <Box sx={{ maxWidth: 800 }}>
      <Typography variant="h6" gutterBottom>Масово назначаване на смени</Typography>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <TextField select fullWidth label="Изберете служители" SelectProps={{
            multiple: true, value: selectedUsers, onChange: (e) => setSelectedUsers(e.target.value as number[]),
            renderValue: (selected) => {
              const selectedArray = selected as number[];
              return usersData?.users?.users?.filter((u: any) => selectedArray.includes(u.id)).map((u: any) => u.firstName ? `${u.firstName} ${u.lastName || ''}` : u.email).join(', ');
            }
          }} margin="normal">
            {usersData?.users?.users?.map((u: any) => (<MenuItem key={u.id} value={u.id}>{u.firstName ? `${u.firstName} ${u.lastName || ''}` : u.email}</MenuItem>))}
          </TextField>
          <TextField select fullWidth label="Смяна" value={selectedShift} onChange={(e) => setSelectedShift(e.target.value)} margin="normal">
            {shiftsData?.shifts?.map((s: any) => (<MenuItem key={s.id} value={s.id}>{s.name} ({(s.startTime || '').substring(0, 5)} - {(s.endTime || '').substring(0, 5)})</MenuItem>))}
          </TextField>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField fullWidth label="От дата" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} InputLabelProps={{ shrink: true }} margin="normal"
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Начална дата за назначаване на смени" /></InputAdornment> } }} />
            <TextField fullWidth label="До дата" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} InputLabelProps={{ shrink: true }} margin="normal"
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Крайна дата за назначаване на смени" /></InputAdornment> } }} />
          </Box>
          <Typography variant="subtitle2" sx={{ mt: 2 }}>Работни дни от седмицата:</Typography>
          <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {dayNames.map((name) => (
              <Button key={name} variant={days.includes(dayNames.indexOf(name)) ? "contained" : "outlined"} onClick={() => handleDayToggle(dayNames.indexOf(name))} size="small">{name}</Button>
            ))}
          </Box>
        </Grid>
        <Grid size={{ xs: 12 }}>
          <Button variant="contained" size="large" onClick={handleSubmit} disabled={submitting || !selectedUsers.length || !selectedShift || !startDate || !endDate}>
            {submitting ? 'Генериране...' : 'Генерирай графици'}
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};

const ScheduleSettings: React.FC = () => {
  return (
    <Box sx={{ mt: 3 }}>
      <ShiftsSection />
      <Box sx={{ my: 4, borderTop: '2px solid #e0e0e0' }} />
      <TemplatesSection />
      <Box sx={{ my: 4, borderTop: '2px solid #e0e0e0' }} />
      <BulkAssignSection />
    </Box>
  );
};

export default ScheduleSettings;
