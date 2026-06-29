import React, { useState } from 'react';
import {
  Typography, Card, CardContent, Button,
  Box, CircularProgress, Switch, FormControlLabel, TextField,
} from '@mui/material';
import { Security as SecurityIcon } from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import KioskCustomizationSettings from '../../components/KioskCustomizationSettings';

const GET_KIOSK_SECURITY_SETTINGS = gql`
  query GetKioskSecurity {
    kioskSecuritySettings {
      requireGps
      requireSameNetwork
    }
  }
`;

const GET_VALIDATE_CODE_RATE_LIMIT = gql`
  query GetValidateCodeRateLimit {
    globalSetting(key: "kiosk_validate_code_rate_limit") {
      key
      value
    }
  }
`;

const UPDATE_KIOSK_SECURITY_MUTATION = gql`
  mutation UpdateKioskSecurity($requireGps: Boolean!, $requireSameNetwork: Boolean!) {
    updateKioskSecuritySettings(requireGps: $requireGps, requireSameNetwork: $requireSameNetwork)
  }
`;

const SET_VALIDATE_CODE_RATE_LIMIT = gql`
  mutation SetValidateCodeRateLimit($key: String!, $value: String!) {
    setGlobalSetting(key: $key, value: $value) {
      key
      value
    }
  }
`;

const KioskSecuritySettings: React.FC = () => {
  const { data, loading, refetch } = useQuery(GET_KIOSK_SECURITY_SETTINGS);
  const { data: rateData, loading: rateLoading, refetch: refetchRate } = useQuery(
    GET_VALIDATE_CODE_RATE_LIMIT,
    { fetchPolicy: 'network-only' }
  );
  const [updateSecurity, { loading: updating }] = useMutation(UPDATE_KIOSK_SECURITY_MUTATION);
  const [setRateLimit, { loading: updatingRate }] = useMutation(SET_VALIDATE_CODE_RATE_LIMIT);
  const [msg, setMsg] = useState('');
  const [rateValue, setRateValue] = useState('5/minute');
  const [rateMsg, setRateMsg] = useState('');

  React.useEffect(() => {
    if (rateData?.globalSetting?.value) {
      setRateValue(rateData.globalSetting.value);
    }
  }, [rateData]);

  if (loading || rateLoading) return <CircularProgress size={24} />;

  const handleToggle = async (field: 'requireGps' | 'requireSameNetwork', value: boolean) => {
    const variables = {
      requireGps: field === 'requireGps' ? value : data.kioskSecuritySettings.requireGps,
      requireSameNetwork: field === 'requireSameNetwork' ? value : data.kioskSecuritySettings.requireSameNetwork,
    };
    try {
      await updateSecurity({ variables });
      setMsg('Настройките за Kiosk са обновени.');
      refetch();
      setTimeout(() => setMsg(''), 3000);
    } catch (e: unknown) {
      const error = e as { message?: string };
      alert(error.message || 'Грешка');
    }
  };

  const handleSaveRateLimit = async () => {
    const match = rateValue.match(/^\d+\/(minute|hour|second|day)$/);
    if (!match) {
      setRateMsg('Невалиден формат. Пример: "10/minute"');
      return;
    }
    try {
      await setRateLimit({ variables: { key: 'kiosk_validate_code_rate_limit', value: rateValue } });
      setRateMsg('Лимитът е запазен.');
      refetchRate();
      setTimeout(() => setRateMsg(''), 3000);
    } catch (e: unknown) {
      const error = e as { message?: string };
      setRateMsg(error.message || 'Грешка');
    }
  };

  return (
    <>
      <Card sx={{ mb: 4, border: '1px solid #f44336' }}>
        <CardContent>
          <Typography
            variant="h6"
            gutterBottom
            color="error.main"
            sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
          >
            <SecurityIcon /> Сигурност на Kiosk Терминал
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Управление на допълнителните защити при генериране на QR код. Тези настройки важат за всички служители.
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={data?.kioskSecuritySettings?.requireGps}
                  onChange={(e) => handleToggle('requireGps', e.target.checked)}
                  disabled={updating}
                />
              }
              label="Изисквай GPS верификация (Геофенсинг)"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={data?.kioskSecuritySettings?.requireSameNetwork}
                  onChange={(e) => handleToggle('requireSameNetwork', e.target.checked)}
                  disabled={updating}
                />
              }
              label="Изисквай същата локална мрежа (IP Match)"
            />
          </Box>
          {msg && <Typography color="success.main" sx={{ mt: 1 }}>{msg}</Typography>}
        </CardContent>
      </Card>

      <Card sx={{ mb: 4, border: '1px solid #ff9800' }}>
        <CardContent>
          <Typography
            variant="h6"
            gutterBottom
            color="warning.main"
            sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
          >
            <SecurityIcon /> Лимит на опитите за код от клавиатура
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Максимален брой опити за въвеждане на code от терминала за определен период.
            Формат: <code>число/минути</code>, напр. <code>5/minute</code>, <code>10/hour</code>.
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <TextField
              size="small"
              value={rateValue}
              onChange={(e) => setRateValue(e.target.value)}
              placeholder="5/minute"
              sx={{ width: 200 }}
            />
            <Button
              variant="contained"
              size="small"
              onClick={handleSaveRateLimit}
              disabled={updatingRate}
            >
              {updatingRate ? 'Запазва се...' : 'Запази'}
            </Button>
          </Box>
          {rateMsg && (
            <Typography
              color={rateMsg.includes('запазен') ? 'success.main' : 'error.main'}
              sx={{ mt: 1 }}
            >
              {rateMsg}
            </Typography>
          )}
        </CardContent>
      </Card>
    </>
  );
};

const ConfigPage: React.FC = () => {
  return (
    <Box>
      <KioskSecuritySettings />
      <KioskCustomizationSettings />
    </Box>
  );
};

export default ConfigPage;
