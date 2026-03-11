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
    <Paper elevation={3} sx={{ p: 3, borderRadius: 4, bgcolor: '#f8f9fa' }}>
      <Box sx={{ 
        mb: 3, 
        p: 2, 
        bgcolor: '#fff', 
        borderRadius: 2, 
        border: '2px solid #e0e0e0',
        minHeight: '60px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Typography variant="h4" sx={{ letterSpacing: 8, fontWeight: 'bold', color: '#1a73e8' }}>
          {code || 'ВЪВЕДЕТЕ КОД'}
        </Typography>
      </Box>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(3, 1fr)', 
        gap: 2 
      }}>
        {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map(num => (
          <Button 
            key={num}
            variant="contained" 
            size="large"
            onClick={() => handleKeyPress(num)}
            sx={{ 
              height: 80, 
              fontSize: '1.5rem', 
              borderRadius: 3,
              bgcolor: '#fff',
              color: '#444',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              '&:hover': { bgcolor: '#f1f3f4' }
            }}
          >
            {num}
          </Button>
        ))}
        
        <Button 
          variant="contained" 
          size="large"
          color="error"
          onClick={handleDelete}
          sx={{ height: 80, borderRadius: 3 }}
        >
          <BackspaceIcon />
        </Button>
        
        <Button 
          variant="contained" 
          size="large"
          onClick={() => handleKeyPress('0')}
          sx={{ 
            height: 80, 
            fontSize: '1.5rem', 
            borderRadius: 3,
            bgcolor: '#fff',
            color: '#444',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            '&:hover': { bgcolor: '#f1f3f4' }
          }}
        >
          0
        </Button>

        <Button 
          variant="contained" 
          size="large"
          color="success"
          onClick={handleSubmit}
          disabled={code.length < 4 || isLoading}
          sx={{ height: 80, borderRadius: 3 }}
        >
          <CheckCircleIcon />
        </Button>
      </Box>
      
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Минимум 4 цифри за вход
        </Typography>
      </Box>
    </Paper>
  );
};

export default CodeKeyboard;
