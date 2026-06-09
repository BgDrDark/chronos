import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Button,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

interface ShareData {
  title: string;
  text: string;
  url: string;
}

export const SharePage: React.FC = () => {
  const navigate = useNavigate();
  const [shareData, setShareData] = useState<ShareData | null>(null);
  const [parsed, setParsed] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const title = params.get('title') || '';
    const text = params.get('text') || '';
    const url = params.get('url') || '';

    if (title || text || url) {
      setShareData({ title, text, url });
    } else {
      // Try POST body via service worker
      try {
        const body = (window as any).__share_body__;
        if (body) {
          setShareData(body);
        }
      } catch (e) {
        // ignore
      }
    }
    setParsed(true);
  }, []);

  if (!parsed) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!shareData || (!shareData.title && !shareData.text && !shareData.url)) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6">Няма споделено съдържание</Typography>
        <Button
          variant="contained"
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
        >
          Към началната страница
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Споделено съдържание
      </Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <List>
          {shareData.title && (
            <ListItem>
              <ListItemText
                primary="Заглавие"
                secondary={shareData.title}
              />
            </ListItem>
          )}
          {shareData.text && (
            <ListItem>
              <ListItemText
                primary="Текст"
                secondary={shareData.text}
              />
            </ListItem>
          )}
          {shareData.url && (
            <ListItem>
              <ListItemText
                primary="URL"
                secondary={shareData.url}
              />
            </ListItem>
          )}
        </List>
      </Paper>
      <Button variant="contained" onClick={() => navigate('/')}>
        Към началната страница
      </Button>
    </Box>
  );
};
