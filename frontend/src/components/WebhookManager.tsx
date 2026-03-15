import React, { useState } from 'react';
import { getErrorMessage, Webhook } from '../types';
import { 
  Box, Typography, Button, Card, CardContent, TextField, 
  List, ListItem, ListItemText, ListItemSecondaryAction, IconButton, 
  Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import HttpIcon from '@mui/icons-material/Http';

const GET_WEBHOOKS = gql`
  query GetWebhooks {
    webhooks {
      id
      url
      description
      isActive
      events
    }
  }
`;

const CREATE_WEBHOOK = gql`
  mutation CreateWebhook($url: String!, $description: String) {
    createWebhook(url: $url, description: $description) {
      id
    }
  }
`;

const DELETE_WEBHOOK = gql`
  mutation DeleteWebhook($id: Int!) {
    deleteWebhook(id: $id)
  }
`;

const WebhookManager: React.FC = () => {
    const { data, refetch } = useQuery(GET_WEBHOOKS);
    const [createWebhook] = useMutation(CREATE_WEBHOOK);
    const [deleteWebhook] = useMutation(DELETE_WEBHOOK);

    const [open, setOpen] = useState(false);
    const [url, setUrl] = useState('');
    const [desc, setDesc] = useState('');

    const handleCreate = async () => {
        try {
            await createWebhook({ variables: { url, description: desc } });
            setOpen(false); setUrl(''); setDesc('');
            refetch();
        } catch (e) { alert(getErrorMessage(e)); }
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm("Сигурни ли сте?")) return;
        try {
            await deleteWebhook({ variables: { id } });
            refetch();
        } catch (e) { alert(getErrorMessage(e)); }
    };

    return (
        <Card variant="outlined" sx={{ borderRadius: 3, border: '1px solid #9c27b0' }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <HttpIcon color="secondary" /> Webhooks (Известяване)
                    </Typography>
                    <Button startIcon={<AddIcon />} variant="contained" color="secondary" onClick={() => setOpen(true)}>
                        Нов Webhook
                    </Button>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Изпращане на данни в реално време към външни системи при събития (Вход/Изход, Отпуски).
                </Typography>

                <List>
                    {data?.webhooks.map((w: Webhook) => (
                        <ListItem key={w.id} divider>
                            <ListItemText 
                                primary={w.url} 
                                secondary={w.description || 'Няма описание'} 
                            />
                            <ListItemSecondaryAction>
                                <IconButton color="error" onClick={() => handleDelete(w.id)}>
                                    <DeleteIcon />
                                </IconButton>
                            </ListItemSecondaryAction>
                        </ListItem>
                    ))}
                    {data?.webhooks.length === 0 && (
                        <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 2 }}>
                            Няма активни Webhooks.
                        </Typography>
                    )}
                </List>

                <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
                    <DialogTitle>Нов Webhook</DialogTitle>
                    <DialogContent>
                        <TextField 
                            fullWidth label="Target URL" margin="normal"
                            placeholder="https://your-system.com/webhook"
                            value={url} onChange={e => setUrl(e.target.value)}
                        />
                        <TextField 
                            fullWidth label="Описание" margin="normal"
                            value={desc} onChange={e => setDesc(e.target.value)}
                        />
                        <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                            Системата ще изпраща POST заявки с JSON данни към този адрес.
                        </Typography>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setOpen(false)}>Отказ</Button>
                        <Button variant="contained" color="secondary" onClick={handleCreate} disabled={!url}>Добави</Button>
                    </DialogActions>
                </Dialog>
            </CardContent>
        </Card>
    );
};

export default WebhookManager;