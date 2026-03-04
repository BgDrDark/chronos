import React, { useState, useEffect } from 'react';
import { 
  Typography, TextField, Button, Box, Alert, 
  CssBaseline, Container, CircularProgress 
} from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';

const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [verifying, setVerifying] = useState(true);
  const [isTokenValid, setIsTokenValid] = useState(false);

  useEffect(() => {
    const verifyToken = async () => {
        if (!token) {
            setVerifying(false);
            return;
        }

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:14240'}/auth/verify-reset-token?token=${token}`);
            if (response.ok) {
                setIsTokenValid(true);
            } else {
                setIsTokenValid(false);
                const data = await response.json();
                setError(data.detail || 'Невалиден или изтекъл линк.');
            }
        } catch (err) {
            setIsTokenValid(false);
            setError('Грешка при проверка на линка.');
        } finally {
            setVerifying(false);
        }
    };

    verifyToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Паролите не съвпадат');
      return;
    }
    if (password.length < 8) {
        setError('Паролата трябва да е поне 8 символа');
        return;
    }

    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await fetch((import.meta.env.VITE_API_URL || 'http://localhost:14240') + '/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Грешка при смяна на паролата');
      }

      setMessage('Паролата е променена успешно! Пренасочване към вход...');
      setTimeout(() => navigate('/login'), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
      return (
        <Container sx={{ mt: 10 }}>
            <Alert severity="error">Липсва валиден токен за смяна на парола.</Alert>
            <Button sx={{ mt: 2 }} onClick={() => navigate('/login')}>Към вход</Button>
        </Container>
      );
  }

  return (
    <Box 
      sx={{ 
        height: '100vh', width: '100vw', 
        backgroundImage: 'url(https://images.unsplash.com/photo-1497215728101-856f4ea42174?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80)',
        backgroundSize: 'cover', display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}
    >
      <CssBaseline />
      <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', bgcolor: 'rgba(0,0,0,0.4)' }} />
      
      <Container maxWidth="xs" sx={{ position: 'relative', zIndex: 1 }}>
        <Box sx={{ p: 4, bgcolor: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(20px)', borderRadius: 4, border: '1px solid rgba(255,255,255,0.2)', color: 'white' }}>
          
          {verifying ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
                <CircularProgress sx={{ color: 'white', mb: 2 }} />
                <Typography>Проверка на линка...</Typography>
            </Box>
          ) : !isTokenValid ? (
             <Box sx={{ textAlign: 'center' }}>
                <Alert severity="error" sx={{ mb: 2 }}>{error || 'Невалиден или изтекъл линк.'}</Alert>
                <Button variant="contained" onClick={() => navigate('/login')}>
                    Обратно към Вход
                </Button>
             </Box>
          ) : (
            <>
              <Typography variant="h4" fontWeight="bold" align="center" gutterBottom>
                Нова парола
              </Typography>
              <Typography variant="body2" align="center" sx={{ mb: 3, color: 'rgba(255,255,255,0.8)' }}>
                Въведете новата си парола по-долу.
              </Typography>

              <form onSubmit={handleSubmit}>
                <TextField
                  fullWidth label="Нова парола" type="password" margin="normal" required value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  sx={{ 
                    '& .MuiOutlinedInput-root': { color: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
                  }}
                />
                <TextField
                  fullWidth label="Потвърди парола" type="password" margin="normal" required value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  sx={{ 
                    '& .MuiOutlinedInput-root': { color: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
                  }}
                />
                
                {message && <Alert severity="success" sx={{ mt: 2 }}>{message}</Alert>}
                {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

                <Button
                  type="submit" fullWidth variant="contained" size="large"
                  sx={{ mt: 3, py: 1.5, fontWeight: 'bold' }} disabled={loading}
                >
                  Смени паролата
                </Button>
              </form>
            </>
          )}
        </Box>
      </Container>
    </Box>
  );
};

export default ResetPasswordPage;
