import React, { useEffect, useState } from 'react';
import { Box, Typography, CircularProgress, IconButton } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useNavigate } from 'react-router-dom';

interface LaunchParams {
  files: { getFile: () => Promise<File> }[];
  resolve: () => void;
}

const DocumentViewerPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    const handleLaunchQueue = async () => {
      if ('launchQueue' in window) {
        const launchQueue = (window as { launchQueue?: { setConsumer: (cb: (params: LaunchParams) => void) => void } }).launchQueue;
        launchQueue?.setConsumer(async (launchParams: LaunchParams) => {
          if (!launchParams.files.length) return;
          
          const fileHandle = launchParams.files[0];
          const file = await fileHandle.getFile();
          setFile(file);
          
          const url = URL.createObjectURL(file);
          setPreviewUrl(url);
          
          launchParams.resolve();
        });
      }
    };

    handleLaunchQueue();
  }, []);

  if (!file) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const isImage = file.type.startsWith('image/');
  const isPdf = file.type === 'application/pdf';

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate(-1)}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6">{file.name}</Typography>
      </Box>

      {isImage && (
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <img src={previewUrl} alt={file.name} style={{ maxWidth: '100%', maxHeight: '80vh' }} />
        </Box>
      )}

      {isPdf && (
        <Box sx={{ height: '80vh' }}>
          <iframe src={previewUrl} style={{ width: '100%', height: '100%', border: 'none' }} />
        </Box>
      )}
    </Box>
  );
};

export default DocumentViewerPage;
