import React, { useState } from 'react';
import { 
  Card, CardContent, Typography, Grid, TextField, Button, 
  FormControlLabel, Checkbox, CircularProgress, Alert
} from '@mui/material';
import PasswordIcon from '@mui/icons-material/Password';
import { useQuery, useMutation, gql } from '@apollo/client';

const GET_PWD_SETTINGS = gql`
  query GetPwdSettings {
    passwordSettings {
      minLength
      maxLength
      requireUpper
      requireLower
      requireDigit
      requireSpecial
    }
  }
`;

const UPDATE_PWD_SETTINGS = gql`
  mutation UpdatePwdSettings($settings: PasswordSettingsInput!) {
    updatePasswordSettings(settings: $settings) {
      minLength
      maxLength
      requireUpper
      requireLower
      requireDigit
      requireSpecial
    }
  }
`;

const PasswordComplexitySettings: React.FC = () => {
  const { data, loading, refetch } = useQuery(GET_PWD_SETTINGS);
  const [updateSettings, { loading: updating }] = useMutation(UPDATE_PWD_SETTINGS);
  
  const [minLen, setMinLen] = useState(8);
  const [maxLen, setMaxLen] = useState(32);
  const [reqUpper, setReqUpper] = useState(true);
  const [reqLower, setReqLower] = useState(true);
  const [reqDigit, setReqDigit] = useState(true);
  const [reqSpecial, setReqSpecial] = useState(true);
  const [msg, setMsg] = useState<{type: 'success'|'error', text: string} | null>(null);

  React.useEffect(() => {
    if (data?.passwordSettings) {
      const s = data.passwordSettings;
      setMinLen(s.minLength);
      setMaxLen(s.maxLength);
      setReqUpper(s.requireUpper);
      setReqLower(s.requireLower);
      setReqDigit(s.requireDigit);
      setReqSpecial(s.requireSpecial);
    }
  }, [data]);

  const handleSave = async () => {
    try {
      await updateSettings({
        variables: {
          settings: {
            minLength: parseInt(minLen.toString()),
            maxLength: parseInt(maxLen.toString()),
            requireUpper: reqUpper,
            requireLower: reqLower,
            requireDigit: reqDigit,
            requireSpecial: reqSpecial
          }
        }
      });
      setMsg({ type: 'success', text: 'Настройките за сложност на паролите са запазени.' });
      refetch();
      setTimeout(() => setMsg(null), 3000);
    } catch (e: any) {
      setMsg({ type: 'error', text: e.message });
    }
  };

  if (loading) return <CircularProgress size={24} />;

  return (
    <Card sx={{ mb: 4, border: '1px solid #673ab7' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom color="secondary.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PasswordIcon color="secondary" /> Сложност на паролите
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Дефинирайте изискванията за сигурност на паролите за всички потребители в системата.
        </Typography>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField 
              label="Минимална дължина" 
              type="number" 
              fullWidth 
              value={minLen} 
              onChange={(e) => setMinLen(parseInt(e.target.value))} 
              size="small"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField 
              label="Максимална дължина" 
              type="number" 
              fullWidth 
              value={maxLen} 
              onChange={(e) => setMaxLen(parseInt(e.target.value))} 
              size="small"
            />
          </Grid>
          
          <Grid size={{ xs: 6, sm: 3 }}>
            <FormControlLabel 
              control={<Checkbox checked={reqUpper} onChange={e => setReqUpper(e.target.checked)} />} 
              label="Главни букви" 
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <FormControlLabel 
              control={<Checkbox checked={reqLower} onChange={e => setReqLower(e.target.checked)} />} 
              label="Малки букви" 
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <FormControlLabel 
              control={<Checkbox checked={reqDigit} onChange={e => setReqDigit(e.target.checked)} />} 
              label="Цифри" 
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <FormControlLabel 
              control={<Checkbox checked={reqSpecial} onChange={e => setReqSpecial(e.target.checked)} />} 
              label="Спец. символи" 
            />
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Button 
              variant="contained" 
              color="secondary" 
              onClick={handleSave} 
              disabled={updating}
              sx={{ mt: 1 }}
            >
              {updating ? <CircularProgress size={24} /> : 'Запази правилата'}
            </Button>
          </Grid>
        </Grid>

        {msg && <Alert severity={msg.type} sx={{ mt: 2 }}>{msg.text}</Alert>}
      </CardContent>
    </Card>
  );
};

export default PasswordComplexitySettings;
