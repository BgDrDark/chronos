import React, { useState } from 'react';
import { 
  Typography, TextField, Button, Box, Alert, 
  CssBaseline, Container, Link
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const ForgotPasswordPage: React.FC = () => {
  // const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await fetch((import.meta.env.VITE_API_URL || 'http://localhost:14240') + '/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Грешка при изпращане на заявката');
      }

      setMessage('Ако имейлът съществува в системата, ще получите инструкции за смяна на парола.');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

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
          <Typography variant="h4" fontWeight="bold" align="center" gutterBottom>
            Забравена парола
          </Typography>
          <Typography variant="body2" align="center" sx={{ mb: 3, color: 'rgba(255,255,255,0.8)' }}>
            Въведете вашия имейл и ние ще ви изпратим линк за смяна на парола.
          </Typography>

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth label="Имейл адрес" margin="normal" required value={email}
              onChange={(e) => setEmail(e.target.value)}
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
              Изпрати линк
            </Button>
            
            <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Link component={RouterLink} to="/login" sx={{ color: 'white', textDecoration: 'none', fontSize: '0.9rem' }}>
                    Върни се към Вход
                </Link>
            </Box>
          </form>
        </Box>
      </Container>
    </Box>
  );
};

export default ForgotPasswordPage;
