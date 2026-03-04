import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, List, ListItem, ListItemText, ListItemSecondaryAction, 
  IconButton, Button, Card, CardContent, Chip, CircularProgress, Alert, ListItemIcon
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';

interface Document {
    id: number;
    filename: string;
    file_type: string;
    is_locked: boolean;
    created_at: string;
}

interface Props {
    userId: number;
    isAdmin: boolean;
}

const DocumentManager: React.FC<Props> = ({ userId, isAdmin }) => {
    const [docs, setDocs] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);

    const fetchDocs = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/documents/list/${userId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to load documents");
            const data = await res.json();
            setDocs(data);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocs();
    }, [userId]);

    const handleDownload = async (docId: number, filename: string) => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/documents/download/${docId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) { alert("Download failed"); }
    };

    const handleDelete = async (docId: number) => {
        if (!window.confirm("Сигурни ли сте?")) return;
        try {
            const token = localStorage.getItem('token');
            await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/documents/${docId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            fetchDocs();
        } catch (e) { alert("Delete failed"); }
    };

    const handleToggleLock = async (docId: number) => {
        try {
            const token = localStorage.getItem('token');
            await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/documents/${docId}/toggle-lock`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            fetchDocs();
        } catch (e) { alert("Lock toggle failed"); }
    };

    const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (!event.target.files?.[0]) return;
        const file = event.target.files[0];
        setUploading(true);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/documents/upload/${userId}?file_type=other`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            if (!res.ok) throw new Error("Upload failed");
            fetchDocs();
        } catch (e: any) { alert(e.message); }
        finally { setUploading(false); }
    };

    if (loading) return <CircularProgress />;

    return (
        <Card variant="outlined" sx={{ borderRadius: 3 }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" fontWeight="bold">Дигитално досие</Typography>
                    <Box>
                        <input type="file" id="doc-upload" hidden onChange={handleUpload} />
                        <label htmlFor="doc-upload">
                            <Button 
                                variant="contained" 
                                component="span" 
                                startIcon={uploading ? <CircularProgress size={20} /> : <UploadFileIcon />}
                                disabled={uploading}
                            >
                                Качи документ
                            </Button>
                        </label>
                    </Box>
                </Box>
                
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

                <List>
                    {docs.map((doc) => (
                        <ListItem key={doc.id} sx={{ borderBottom: '1px solid #eee', opacity: doc.is_locked && !isAdmin ? 0.7 : 1 }}>
                            <ListItemIcon>
                                {doc.is_locked ? <LockIcon color="warning" /> : <InsertDriveFileIcon color="action" />}
                            </ListItemIcon>
                            <ListItemText 
                                primary={
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        {doc.filename}
                                        {doc.is_locked && <Chip label="Само за четене" size="small" variant="outlined" color="warning" sx={{ height: 20, fontSize: '0.6rem' }} />}
                                    </Box>
                                } 
                                secondary={`${new Date(doc.created_at).toLocaleDateString('bg-BG')} | ${doc.file_type}`} 
                            />
                            <ListItemSecondaryAction>
                                {isAdmin && (
                                    <IconButton onClick={() => handleToggleLock(doc.id)} color={doc.is_locked ? "warning" : "default"} title={doc.is_locked ? "Отключи" : "Заключи"}>
                                        {doc.is_locked ? <LockIcon fontSize="small" /> : <LockOpenIcon fontSize="small" />}
                                    </IconButton>
                                )}
                                <IconButton 
                                    onClick={() => handleDownload(doc.id, doc.filename)} 
                                    color="primary"
                                    disabled={doc.is_locked && !isAdmin}
                                    title={doc.is_locked && !isAdmin ? "Заключен от администратор" : "Свали"}
                                >
                                    <DownloadIcon />
                                </IconButton>
                                {isAdmin && (
                                    <IconButton onClick={() => handleDelete(doc.id)} color="error" title="Изтрий">
                                        <DeleteIcon />
                                    </IconButton>
                                )}
                            </ListItemSecondaryAction>
                        </ListItem>
                    ))}
                    {docs.length === 0 && (
                        <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
                            Няма качени документи.
                        </Typography>
                    )}
                </List>
            </CardContent>
        </Card>
    );
};

export default DocumentManager;