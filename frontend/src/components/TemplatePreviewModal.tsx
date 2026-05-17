import React, { useState } from 'react';
import dayjs from 'dayjs';
import { useQuery, useMutation } from '@apollo/client';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, Button, Box, Typography, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Paper, CircularProgress, Alert, InputAdornment
} from '@mui/material';
import { ShiftTypeColors } from '../utils/shiftUtils';
import { useError, extractErrorMessage } from '../context/ErrorContext';
import { InfoIcon } from '../components/ui/InfoIcon';
import {
  GET_TEMPLATES_FOR_PREVIEW,
  GET_USERS_QUERY,
  GET_SHIFTS_QUERY,
  GET_TEMPLATE_PREVIEW,
  APPLY_SCHEDULE_TEMPLATE,
} from '../graphql/queries';

interface TemplatePreviewModalProps {
  open: boolean;
  onClose: () => void;
}

const TemplatePreviewModal: React.FC<TemplatePreviewModalProps> = ({ open, onClose }) => {
  const { showError, showSuccess } = useError();
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedUser, setSelectedUser] = useState('');
  const [startDate, setStartDate] = useState(dayjs().startOf('month').format('YYYY-MM-DD'));
  const [endDate, setEndDate] = useState(dayjs().endOf('month').format('YYYY-MM-DD'));

  const { data: tmplData } = useQuery(GET_TEMPLATES_FOR_PREVIEW);
  const { data: usersData } = useQuery(GET_USERS_QUERY, { variables: { limit: 1000 } });
  const { data: shiftsData } = useQuery(GET_SHIFTS_QUERY);

  const { data: previewData, loading: previewLoading, refetch: refetchPreview } = useQuery(GET_TEMPLATE_PREVIEW, {
    variables: { templateId: parseInt(selectedTemplate), startDate, endDate },
    skip: !selectedTemplate || !startDate || !endDate,
  });

  const [applyTemplate, { loading: applying }] = useMutation(APPLY_SCHEDULE_TEMPLATE);

  const handleApply = async () => {
    if (!selectedTemplate || !selectedUser) return;
    try {
      await applyTemplate({
        variables: { templateId: parseInt(selectedTemplate), userId: parseInt(selectedUser), startDate, endDate }
      });
      showSuccess('Шаблонът е приложен успешно!');
      onClose();
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  };

  const handlePreviewChange = () => {
    if (selectedTemplate) refetchPreview();
  };

  const shiftsMap = new Map<number, { name: string; shiftType: string; startTime: string; endTime: string }>();
  shiftsData?.shifts?.forEach((s: any) => shiftsMap.set(s.id, { name: s.name, shiftType: s.shiftType, startTime: s.startTime, endTime: s.endTime }));

  const daysInPreview = previewData?.templatePreview || [];
  const assignedCount = daysInPreview.filter((d: any) => d.shiftId).length;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Преглед и прилагане на шаблон</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', gap: 2, mt: 1, flexWrap: 'wrap' }}>
          <TextField select fullWidth label="Шаблон" size="small" value={selectedTemplate}
            onChange={(e) => { setSelectedTemplate(e.target.value); setTimeout(handlePreviewChange, 100); }}
            sx={{ minWidth: 200 }}>
            {tmplData?.scheduleTemplates?.map((t: any) => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>) || <MenuItem disabled>Зареждане...</MenuItem>}
          </TextField>
          <TextField select fullWidth label="Служител" size="small" value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)} sx={{ minWidth: 200 }}>
            {usersData?.users?.users?.map((u: any) => <MenuItem key={u.id} value={u.id}>{u.firstName ? `${u.firstName} ${u.lastName}` : u.email}</MenuItem>) || <MenuItem disabled>Зареждане...</MenuItem>}
          </TextField>
          <TextField fullWidth label="От" type="date" size="small" value={startDate}
            onChange={(e) => { setStartDate(e.target.value); setTimeout(handlePreviewChange, 100); }}
            InputLabelProps={{ shrink: true }} sx={{ minWidth: 150 }}
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Начална дата за прилагане" /></InputAdornment> } }} />
          <TextField fullWidth label="До" type="date" size="small" value={endDate}
            onChange={(e) => { setEndDate(e.target.value); setTimeout(handlePreviewChange, 100); }}
            InputLabelProps={{ shrink: true }} sx={{ minWidth: 150 }}
            slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Крайна дата за прилагане" /></InputAdornment> } }} />
        </Box>

        {previewLoading && <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}><CircularProgress /></Box>}

        {daysInPreview.length > 0 && (
          <>
            <Typography variant="body2" sx={{ mt: 2, mb: 1 }}>
              Преглед: {daysInPreview.length} дни, {assignedCount} с назначена смяна
            </Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Дата</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Ден</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Смяна</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {daysInPreview.map((d: any, i: number) => {
                    const shift = d.shiftId ? shiftsMap.get(d.shiftId) : null;
                    return (
                      <TableRow key={i}>
                        <TableCell>{d.date}</TableCell>
                        <TableCell>{dayjs(d.date).format('dddd')}</TableCell>
                        <TableCell>
                          {shift ? (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: 20, height: 20, borderRadius: '50%', backgroundColor: ShiftTypeColors[shift.shiftType] || '#999' }} />
                              <Typography variant="body2">{shift.name} ({shift.startTime.substring(0, 5)} - {shift.endTime.substring(0, 5)})</Typography>
                            </Box>
                          ) : (
                            <Typography variant="body2" color="text.secondary">Почивен ден</Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}

        {selectedTemplate && daysInPreview.length === 0 && !previewLoading && (
          <Alert severity="info" sx={{ mt: 2 }}>Няма данни за избрания период.</Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отказ</Button>
        <Button variant="contained" onClick={handleApply} disabled={!selectedTemplate || !selectedUser || applying || daysInPreview.length === 0}>
          {applying ? 'Прилага се...' : 'Приложи'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TemplatePreviewModal;
