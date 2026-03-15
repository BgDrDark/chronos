import React, { useState } from 'react';
import { getErrorMessage, ScheduleTemplate, ScheduleTemplateItem, Shift } from '../types';
import { 
  Box, Typography, Button, Card, CardContent, Grid, 
  TextField, Dialog, DialogTitle, DialogContent, DialogActions, 
  IconButton, MenuItem, Chip
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';

const GET_TEMPLATES = gql`
  query GetTemplates {
    scheduleTemplates {
      id
      name
      description
      items {
        dayIndex
        shiftId
        shift { name }
      }
    }
    shifts {
      id
      name
    }
  }
`;

const CREATE_TEMPLATE = gql`
  mutation CreateTemplate($name: String!, $description: String, $items: [ScheduleTemplateItemInput!]!) {
    createScheduleTemplate(name: $name, description: $description, items: $items) {
      id
    }
  }
`;

const DELETE_TEMPLATE = gql`
  mutation DeleteTemplate($id: Int!) {
    deleteScheduleTemplate(id: $id)
  }
`;

const ScheduleTemplatesManager: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_TEMPLATES);
    const [createTemplate] = useMutation(CREATE_TEMPLATE);
    const [deleteTemplate] = useMutation(DELETE_TEMPLATE);

    const [open, setOpen] = useState(false);
    const [name, setName] = useState('');
    const [desc, setDesc] = useState('');
    const [items, setItems] = useState<{ dayIndex: number; shiftId: number | null }[]>([
        { dayIndex: 0, shiftId: null }
    ]);

    const handleAddItem = () => {
        setItems([...items, { dayIndex: items.length, shiftId: null }]);
    };

    const handleRemoveItem = (index: number) => {
        const newItems = items.filter((_, i) => i !== index)
            .map((item, i) => ({ ...item, dayIndex: i }));
        setItems(newItems);
    };

    const handleSave = async () => {
        try {
            await createTemplate({
                variables: {
                    name,
                    description: desc,
                    items: items.map(i => ({ dayIndex: i.dayIndex, shiftId: i.shiftId }))
                }
            });
            setOpen(false);
            setName(''); setDesc(''); setItems([{ dayIndex: 0, shiftId: null }]);
            refetch();
        } catch (e) { alert(getErrorMessage(e)); }
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm("Сигурни ли сте?")) return;
        try {
            await deleteTemplate({ variables: { id } });
            refetch();
        } catch (e) { alert(getErrorMessage(e)); }
    };

    if (loading) return null;

    return (
        <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Шаблони за ротации</Typography>
                <Button startIcon={<AddIcon />} variant="outlined" onClick={() => setOpen(true)}>
                    Нов Шаблон
                </Button>
            </Box>

            <Grid container spacing={2}>
                {data?.scheduleTemplates.map((t: ScheduleTemplate) => (
                    <Grid size={{ xs: 12, sm: 6, md: 4 }} key={t.id}>
                        <Card variant="outlined">
                            <CardContent>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <Typography variant="subtitle1" fontWeight="bold">{t.name}</Typography>
                                    <IconButton size="small" color="error" onClick={() => handleDelete(t.id)}>
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </Box>
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    {t.description || 'Няма описание'}
                                </Typography>
                                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {t.items?.map((item: ScheduleTemplateItem) => (
                                        <Chip 
                                            key={item.dayIndex} 
                                            label={item.shift ? item.shift.name : 'ПОЧ'} 
                                            size="small" 
                                            variant={item.shift ? "filled" : "outlined"}
                                        />
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
                    <TextField 
                        fullWidth label="Име на шаблона" margin="normal" 
                        value={name} onChange={e => setName(e.target.value)} 
                    />
                    <TextField 
                        fullWidth label="Описание" margin="normal" 
                        value={desc} onChange={e => setDesc(e.target.value)} 
                    />
                    
                    <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Дни в ротацията:</Typography>
                    {items.map((item, index) => (
                        <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                            <Typography sx={{ minWidth: 60 }}>Ден {index + 1}:</Typography>
                            <TextField
                                select size="small" fullWidth
                                value={item.shiftId || ''}
                                onChange={(e) => {
                                    const newItems = [...items];
                                    newItems[index].shiftId = e.target.value ? parseInt(e.target.value as string) : null;
                                    setItems(newItems);
                                }}
                            >
                                <MenuItem value=""><em>Почивка</em></MenuItem>
                                {data?.shifts?.map((s: Shift) => (
                                    <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                                ))}
                            </TextField>
                            <IconButton size="small" onClick={() => handleRemoveItem(index)} disabled={items.length === 1}>
                                <DeleteIcon fontSize="small" />
                            </IconButton>
                        </Box>
                    ))}
                    <Button startIcon={<AddIcon />} size="small" onClick={handleAddItem} sx={{ mt: 1 }}>
                        Добави ден
                    </Button>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpen(false)}>Отказ</Button>
                    <Button onClick={handleSave} variant="contained" startIcon={<SaveIcon />}>Запази</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ScheduleTemplatesManager;