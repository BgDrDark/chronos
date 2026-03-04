import React, { useState } from 'react';
import { 
  Card, CardContent, Typography, Box, Button, 
  CircularProgress, Alert
} from '@mui/material';
import WallpaperIcon from '@mui/icons-material/Wallpaper';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import axios from 'axios';

const KioskCustomizationSettings: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleBackgroundUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMsg(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const apiUrl = import.meta.env.VITE_API_URL || 'https://dev.oblak24.org';
      
      await axios.post(`${apiUrl}/system/kiosk-background`, formData, {
        headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
        }
      });
      
      setMsg({ type: 'success', text: 'Фоновото изображение на терминала е обновено успешно.' });
    } catch (err: any) {
      setMsg({ type: 'error', text: err.response?.data?.detail || err.message });
    } finally {
      setUploading(false);
      event.target.value = ''; // Reset input
    }
  };

  return (
    <Card sx={{ mb: 4, border: '1px solid #009688' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom color="teal" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WallpaperIcon color="inherit" /> Персонализация на Kiosk
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Качете изображение, което да се показва като фон на Kiosk терминала за маркиране на време.
        </Typography>

        <Box sx={{ mt: 2 }}>
            <Button
                component="label"
                variant="contained"
                color="primary"
                startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
                disabled={uploading}
            >
                Качи фон за терминал
                <input type="file" hidden accept="image/*" onChange={handleBackgroundUpload} />
            </Button>
        </Box>

        {msg && <Alert severity={msg.type} sx={{ mt: 2 }}>{msg.text}</Alert>}
      </CardContent>
    </Card>
  );
};

export default KioskCustomizationSettings;
