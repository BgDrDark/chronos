import React, { useState } from 'react';
import { 
  Box, Typography, Button, Card, CardContent, TextField, 
  Dialog, DialogTitle, DialogContent, DialogActions, 
  List, ListItem, ListItemText, ListItemSecondaryAction, IconButton, 
  Alert
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { type ApiKey } from '../types';

const GET_KEYS = gql`
  query GetApiKeys {
    apiKeys {
      id
      name
      keyPrefix
      isActive
      createdAt
      lastUsedAt
      permissions
    }
  }
`;

const CREATE_KEY = gql`
  mutation CreateKey($name: String!) {
    createApiKey(name: $name) {
      keyInfo { id name }
      rawKey
    }
  }
`;

const DELETE_KEY = gql`
  mutation DeleteKey($id: Int!) {
    deleteApiKey(id: $id)
  }
`;

const ApiKeyManager: React.FC = () => {
    const { data, refetch } = useQuery(GET_KEYS);
    const [createKey, { loading: creating }] = useMutation(CREATE_KEY);
    const [deleteKey] = useMutation(DELETE_KEY);

    const [open, setOpen] = useState(false);
    const [newName, setNewName] = useState('');
    const [generatedKey, setGeneratedKey] = useState<string | null>(null);

    const handleCreate = async () => {
        try {
            const res = await createKey({ variables: { name: newName } });
            setGeneratedKey(res.data.createApiKey.rawKey);
            setNewName('');
            refetch();
        } catch (err: unknown) { 
            if (err instanceof Error) alert(err.message);
            else alert('Възникна неочаквана грешка');
        }
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm("Този ключ ще спре да работи веднага. Сигурни ли сте?")) return;
        try {
            await deleteKey({ variables: { id } });
            refetch();
        } catch (err: unknown) { 
            if (err instanceof Error) alert(err.message);
            else alert('Възникна неочаквана грешка');
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        alert("Ключът е копиран!");
    };

    return (
        <Card variant="outlined" sx={{ borderRadius: 3, border: '1px solid #2196f3' }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <VpnKeyIcon color="primary" /> API Ключове за Интеграция
                    </Typography>
                    <Button startIcon={<AddIcon />} variant="contained" onClick={() => { setOpen(true); setGeneratedKey(null); }}>
                        Нов Ключ
                    </Button>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Използвайте тези ключове за свързване на Chronos с външни системи (ТРЗ софтуер, ERP и др.).
                </Typography>

                <List>
                    {data?.apiKeys.map((k: ApiKey) => (
                        <ListItem key={k.id} divider>
                            <ListItemText 
                                primary={k.name} 
                                secondary={`Префикс: ${k.keyPrefix}... | Последно ползван: ${k.lastUsedAt ? new Date(k.lastUsedAt).toLocaleString('bg-BG') : 'Никога'}`} 
                            />
                            <ListItemSecondaryAction>
                                <IconButton color="error" onClick={() => handleDelete(k.id)}>
                                    <DeleteIcon />
                                </IconButton>
                            </ListItemSecondaryAction>
                        </ListItem>
                    ))}
                    {data?.apiKeys.length === 0 && (
                        <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 2 }}>
                            Няма активни API ключове.
                        </Typography>
                    )}
                </List>

                <Dialog open={open} onClose={() => setOpen(false)} maxWidth="xs" fullWidth>
                    <DialogTitle>Генериране на API Ключ</DialogTitle>
                    <DialogContent>
                        {!generatedKey ? (
                            <TextField 
                                fullWidth label="Име на интеграцията" margin="normal"
                                placeholder="напр. Счетоводен Софтуер"
                                value={newName} onChange={e => setNewName(e.target.value)}
                            />
                        ) : (
                            <Box sx={{ mt: 2 }}>
                                <Alert severity="warning" sx={{ mb: 2 }}>
                                    Запишете този ключ СЕГА. Той няма да бъде показан повече!
                                </Alert>
                                <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, display: 'flex', alignItems: 'center', gap: 1, wordBreak: 'break-all' }}>
                                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                                        {generatedKey}
                                    </Typography>
                                    <IconButton size="small" onClick={() => copyToClipboard(generatedKey)}>
                                        <ContentCopyIcon fontSize="small" />
                                    </IconButton>
                                </Box>
                            </Box>
                        )}
                    </DialogContent>
                    <DialogActions>
                        {!generatedKey ? (
                            <>
                                <Button onClick={() => setOpen(false)}>Отказ</Button>
                                <Button variant="contained" onClick={handleCreate} disabled={!newName || creating}>Генерирай</Button>
                            </>
                        ) : (
                            <Button variant="contained" onClick={setOpen.bind(null, false)}>Готово</Button>
                        )}
                    </DialogActions>
                </Dialog>
            </CardContent>
        </Card>
    );
};

export default ApiKeyManager;