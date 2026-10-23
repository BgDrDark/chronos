import React, { useState } from 'react';
import { Box, Button, Typography, Paper } from '@mui/material';
import { 
  Backspace as BackspaceIcon, 
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';

interface CodeKeyboardProps {
  onCodeSubmit: (code: string) => void;
  isLoading?: boolean;
}

const CodeKeyboard: React.FC<CodeKeyboardProps> = ({ onCodeSubmit, isLoading }) => {
  const [code, setCode] = useState('');

  const handleKeyPress = (val: string) => {
    if (code.length < 8) {
      setCode(prev => prev + val);
    }
  };

  const handleDelete = () => {
    setCode(prev => prev.slice(0, -1));
  };

  const handleSubmit = () => {
    if (code.length >= 4) {
      onCodeSubmit(code);
      setCode('');
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 2, borderRadius: 3, bgcolor: '#f8f9fa' }}>
      <Box sx={{ 
        mb: 2, 
        p: 1.5, 
        bgcolor: '#fff', 
        borderRadius: 1.5, 
        border: '2px solid #e0e0e0',
        minHeight: '44px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Typography variant="h5" sx={{ letterSpacing: 6, fontWeight: 'bold', color: '#1a73e8' }}>
          {code || 'ВЪВЕДЕТЕ КОД'}
        </Typography>
      </Box>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(3, 1fr)', 
        gap: 1.5 
      }}>
        {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map(num => (
          <Button 
            key={num}
            variant="contained" 
            size="small"
            onClick={() => handleKeyPress(num)}
            sx={{ 
              height: 56, 
              fontSize: '1.2rem', 
              borderRadius: 2,
              bgcolor: '#fff',
              color: '#444',
              boxShadow: '0 3px 4px rgba(0,0,0,0.08)',
              '&:hover': { bgcolor: '#f1f3f4' }
            }}
          >
            {num}
          </Button>
        ))}
        
        <Button 
          variant="contained" 
          size="small"
          color="error"
          onClick={handleDelete}
          sx={{ height: 56, borderRadius: 2 }}
        >
          <BackspaceIcon />
        </Button>
        
        <Button 
          variant="contained" 
          size="small"
          onClick={() => handleKeyPress('0')}
          sx={{ 
            height: 56, 
            fontSize: '1.2rem', 
            borderRadius: 2,
            bgcolor: '#fff',
            color: '#444',
            boxShadow: '0 3px 4px rgba(0,0,0,0.08)',
            '&:hover': { bgcolor: '#f1f3f4' }
          }}
        >
          0
        </Button>

        <Button 
          variant="contained" 
          size="small"
          color="success"
          onClick={handleSubmit}
          disabled={code.length < 4 || isLoading}
          sx={{ height: 56, borderRadius: 2 }}
        >
          <CheckCircleIcon />
        </Button>
      </Box>
      
      <Box sx={{ mt: 1.5, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Минимум 4 цифри за вход
        </Typography>
      </Box>
    </Paper>
  );
};

export default CodeKeyboard;
