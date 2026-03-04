import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Typography, TextField, Button, Box, Alert, 
  Avatar, CssBaseline, CircularProgress, Container, Link 
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { Link as RouterLink } from 'react-router-dom';
// @ts-ignore
import { useApolloClient } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ME_QUERY } from '../graphql/queries';
import { biometricService } from '../services/biometricService';
import { getApiUrl } from '../utils/api';
import FingerprintIcon from '@mui/icons-material/Fingerprint';

// Read CSRF token from cookie
const getCsrfToken = (): string | null => {
  const name = 'csrf_token=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return null;
};

const loginSchema = z.object({
  identifier: z.string().min(1, 'Имейл или потребителско име е задължително'),
  password: z.string().min(8, 'Паролата трябва да е поне 8 символа'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const client = useApolloClient();
  const [apiError, setApiError] = useState('');
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      identifier: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true);
    setApiError('');
    setShake(false);

    const params = new URLSearchParams();
    params.append('username', data.identifier);
    params.append('password', data.password);

    try {
      // Get CSRF token from cookie
      const csrfToken = getCsrfToken();
      
      const response = await fetch(getApiUrl('auth/token'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken || '',
        },
        body: params,
        credentials: 'include',
      });

      if (!response.ok) {
        const responseData = await response.json();
        throw new Error(responseData.detail || 'Грешен имейл или парола');
      }
      
      const responseData = await response.json();

      if (responseData.password_force_change) {
        navigate('/settings?force_password_change=true');
        return;
      }
      
      const { data: meData } = await client.query({ query: ME_QUERY, fetchPolicy: 'network-only' });
      if (meData?.me?.role?.name && ['admin', 'super_admin'].includes(meData.me.role.name)) {
        navigate('/admin/presence');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setApiError(err.message);
      setShake(true);
      setTimeout(() => setShake(false), 500);
    } finally {
      setLoading(false);
    }
  };

  const onBiometricLogin = async () => {
    setLoading(true);
    setApiError('');
    try {
      // Prompt for email optional but better for UX if we have it
      const email = (document.getElementById('email') as HTMLInputElement)?.value;
      await biometricService.loginWithBiometrics(email || undefined);
      
      // Fetch user role to determine redirection (reusing same logic)
      const { data: meData } = await client.query({ query: ME_QUERY });
      if (meData?.me?.role?.name && ['admin', 'super_admin'].includes(meData.me.role.name)) {
        navigate('/admin/presence');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setApiError(err.message);
      setShake(true);
      setTimeout(() => setShake(false), 500);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box 
      component="main" 
      sx={{ 
        height: '100vh', 
        width: '100vw',
        overflow: 'hidden',
        backgroundImage: 'url(https://images.unsplash.com/photo-1497215728101-856f4ea42174?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80)',
        backgroundRepeat: 'no-repeat',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative'
      }}
    >
      <CssBaseline />
      
      {/* Dark Overlay */}
      <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', bgcolor: 'rgba(0,0,0,0.3)' }} />

      <Container maxWidth="xs" sx={{ position: 'relative', zIndex: 1 }}>
        <Box
            sx={{
                p: 4,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                // Removed Paper container, using direct box with glass effect
                borderRadius: 8,
                backgroundColor: 'rgba(255, 255, 255, 0.15)', 
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
                animation: 'fadeIn 1s ease-out',
                '@keyframes fadeIn': {
                    '0%': { opacity: 0, transform: 'scale(0.9)' },
                    '100%': { opacity: 1, transform: 'scale(1)' },
                },
            }}
        >
          <Avatar sx={{ m: 1, bgcolor: 'primary.main', width: 64, height: 64, boxShadow: 3 }}>
            <LockOutlinedIcon fontSize="large" />
          </Avatar>
          
          <Typography component="h1" variant="h3" fontWeight="900" sx={{ mb: 0.5, color: 'white', textShadow: '2px 2px 4px rgba(0,0,0,0.3)' }}>
            Chronos
          </Typography>
          
          <Typography variant="subtitle1" sx={{ mb: 3, color: 'rgba(255,255,255,0.8)', fontWeight: 'medium' }}>
            Работно време и финанси
          </Typography>

          <Box 
            component="form" 
            noValidate 
            onSubmit={handleSubmit(onSubmit)} 
            sx={{ 
              width: '100%',
              ...(shake && {
                animation: 'shake 0.5s',
                '@keyframes shake': {
                  '0%, 100%': { transform: 'translateX(0)' },
                  '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-5px)' },
                  '20%, 40%, 60%, 80%': { transform: 'translateX(5px)' },
                }
              })
            }}
          >
            <TextField
              margin="normal"
              required
              fullWidth
              id="identifier"
              label="Имейл или потребителско име"
              autoComplete="username"
              autoFocus
              {...register('identifier')}
              error={!!errors.identifier || !!apiError}
              helperText={errors.identifier?.message}
              disabled={loading}
              sx={{ 
                '& .MuiOutlinedInput-root': {
                    color: 'white',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                },
                '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
              }}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              label="Парола"
              type="password"
              id="password"
              autoComplete="current-password"
              {...register('password')}
              error={!!errors.password || !!apiError}
              helperText={errors.password?.message}
              disabled={loading}
              sx={{ 
                '& .MuiOutlinedInput-root': {
                    color: 'white',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                },
                '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
              }}
            />
            
            {apiError && (
              <Alert severity="error" sx={{ mt: 2, borderRadius: 2, bgcolor: 'rgba(211, 47, 47, 0.2)', color: '#ffcdd2', border: '1px solid rgba(211, 47, 47, 0.5)' }}>
                {apiError}
              </Alert>
            )}

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              sx={{ 
                mt: 4, 
                mb: 1, 
                py: 1.5, 
                borderRadius: 2, 
                fontSize: '1.1rem', 
                fontWeight: 'bold',
                boxShadow: '0 4px 14px 0 rgba(0,118,255,0.39)',
                textTransform: 'none'
              }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Влез в системата'}
            </Button>

            <Button
              fullWidth
              variant="outlined"
              size="large"
              startIcon={<FingerprintIcon />}
              onClick={onBiometricLogin}
              disabled={loading}
              sx={{ 
                mb: 2, 
                py: 1.5, 
                borderRadius: 2, 
                fontSize: '1rem', 
                fontWeight: 'medium',
                color: 'white',
                borderColor: 'rgba(255,255,255,0.5)',
                textTransform: 'none',
                '&:hover': {
                    borderColor: 'white',
                    backgroundColor: 'rgba(255,255,255,0.1)'
                }
              }}
            >
              Вход с биометрия
            </Button>
            
            <Box sx={{ textAlign: 'center', mt: 1 }}>
                <Link 
                    component={RouterLink}
                    to="/forgot-password" 
                    sx={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none', fontSize: '0.85rem', '&:hover': { color: 'white' } }}
                >
                    Забравена парола?
                </Link>
            </Box>
            
            <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                    © {new Date().getFullYear()} Oblak24 Team
                </Typography>
            </Box>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default LoginPage;