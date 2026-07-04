import React, { useState, useEffect, useCallback } from 'react';
import {
  Typography, Card, CardContent, Button,
  Box, CircularProgress, Switch, FormControlLabel, TextField, InputAdornment,
  Select, MenuItem, FormControl, InputLabel, Tabs, Tab, Alert, Grid, Slider
} from '@mui/material';
import {
  Security as SecurityIcon,
  Palette as PaletteIcon,
  VolumeUp as VolumeIcon,
  TextFields as TextIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import KioskCustomizationSettings from '../../components/KioskCustomizationSettings';
import { InfoIcon } from '../../components/ui/InfoIcon';
import { getApiUrl } from '../../utils/api';

const TERMINALS_QUERY = gql`
  query GetTerminalsForConfig {
    terminals { id hardwareUuid alias deviceName isActive }
  }
`;

interface TerminalConfig {
  colors: { primary: string; secondary: string; background: string; text: string; accent: string };
  display: { clock_size: number; show_date: boolean; show_weather: boolean; background: { type: string; value: string } };
  sounds: { scan_success: string; scan_error: string; keypress: string; volume: number };
  tts: { enabled: boolean; language: string; scan_success: boolean; scan_error: boolean };
  text: { scanning_text: string; welcome_message: string; success_message: string; error_message: string; qr_placeholder: string; keyboard_placeholder: string };
  timeouts: { inactivity_reset: number };
  security: { exit_method: string; exit_pin_required: boolean };
}

const DEFAULT_CONFIG: TerminalConfig = {
  colors: { primary: '#1a237e', secondary: '#0d47a1', background: '#1a237e', text: '#ffffff', accent: '#4fc3f7' },
  display: { clock_size: 80, show_date: true, show_weather: false, background: { type: 'color', value: '#1a237e' } },
  sounds: { scan_success: 'default', scan_error: 'default', keypress: 'none', volume: 0.7 },
  tts: { enabled: false, language: 'bg-BG', scan_success: true, scan_error: true },
  text: { scanning_text: 'Сканирайте QR код или въведете код', welcome_message: '', success_message: 'Успешен вход', error_message: 'Грешка при достъп', qr_placeholder: 'Поставете QR код пред камерата', keyboard_placeholder: 'Въведете вашия код' },
  timeouts: { inactivity_reset: 30 },
  security: { exit_method: 'pin', exit_pin_required: true },
};

const TerminalConfigEditor: React.FC = () => {
  const { data: terminalsData, loading: terminalsLoading } = useQuery(TERMINALS_QUERY);
  const [selectedHwid, setSelectedHwid] = useState('');
  const [config, setConfig] = useState<TerminalConfig>(DEFAULT_CONFIG);
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchConfig = useCallback(async (hwid: string) => {
    setLoading(true);
    try {
      const res = await fetch(getApiUrl(`kiosk/terminal/${hwid}/config`));
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    if (selectedHwid) fetchConfig(selectedHwid);
    else setConfig(DEFAULT_CONFIG);
  }, [selectedHwid, fetchConfig]);

  const handleSave = async () => {
    if (!selectedHwid) return;
    setSaving(true);
    setMsg(null);
    try {
      const res = await fetch(getApiUrl(`kiosk/terminal/${selectedHwid}/config`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (res.ok) setMsg({ type: 'success', text: 'Конфигурацията е запазена.' });
      else setMsg({ type: 'error', text: 'Грешка при запазване.' });
    } catch {
      setMsg({ type: 'error', text: 'Мрежова грешка.' });
    }
    setSaving(false);
  };

  const update = <K extends keyof TerminalConfig>(section: K, values: Partial<TerminalConfig[K]>) => {
    setConfig(prev => ({ ...prev, [section]: { ...prev[section], ...values } }));
  };

  if (terminalsLoading) return <CircularProgress size={24} />;

  const terminals = terminalsData?.terminals || [];

  return (
    <Card sx={{ mb: 4, border: '1px solid #1565c0' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom color="primary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PaletteIcon color="primary" /> Персонализация по Терминал
        </Typography>

        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Избери терминал</InputLabel>
          <Select value={selectedHwid} label="Избери терминал" onChange={(e) => setSelectedHwid(e.target.value)}>
            {terminals.map((t: any) => (
              <MenuItem key={t.id} value={t.hardwareUuid}>
                {t.alias || t.deviceName || t.hardwareUuid}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {!selectedHwid && (
          <Typography variant="body2" color="text.secondary">Изберете терминал, за да редактирате настройките му.</Typography>
        )}

        {loading && <CircularProgress size={24} />}

        {selectedHwid && !loading && (
          <>
            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
              <Tab label="Изглед" />
              <Tab label="Звук / TTS" />
              <Tab label="Текст" />
              <Tab label="Сигурност" />
            </Tabs>

            {tab === 0 && (
              <Box>
                <TextField fullWidth label="Първичен цвят" size="small" sx={{ mb: 2 }}
                  value={config.colors.primary}
                  onChange={(e) => update('colors', { primary: e.target.value })}
                />
                <TextField fullWidth label="Вторичен цвят" size="small" sx={{ mb: 2 }}
                  value={config.colors.secondary}
                  onChange={(e) => update('colors', { secondary: e.target.value })}
                />
                <TextField fullWidth label="Фонов цвят" size="small" sx={{ mb: 2 }}
                  value={config.colors.background}
                  onChange={(e) => update('colors', { background: e.target.value })}
                />
                <TextField fullWidth label="Цвят на текст" size="small" sx={{ mb: 2 }}
                  value={config.colors.text}
                  onChange={(e) => update('colors', { text: e.target.value })}
                />
                <TextField fullWidth label="Акцентен цвят" size="small" sx={{ mb: 2 }}
                  value={config.colors.accent}
                  onChange={(e) => update('colors', { accent: e.target.value })}
                />
                <Typography gutterBottom>Големина на часовника: {config.display.clock_size}px</Typography>
                <Slider min={40} max={160} step={5} value={config.display.clock_size}
                  onChange={(_, v) => update('display', { clock_size: v as number })} sx={{ mb: 2 }} />
                <FormControlLabel control={<Switch checked={config.display.show_date}
                  onChange={(e) => update('display', { show_date: e.target.checked })} />}
                  label="Показвай дата на скрийнсейвъра" sx={{ mb: 1 }} />
              </Box>
            )}

            {tab === 1 && (
              <Box>
                <FormControlLabel control={<Switch checked={config.tts.enabled}
                  onChange={(e) => update('tts', { enabled: e.target.checked })} />}
                  label="Гласово озвучаване (TTS)" sx={{ mb: 2 }} />
                <TextField fullWidth label="TTS език" size="small" sx={{ mb: 2 }}
                  value={config.tts.language}
                  onChange={(e) => update('tts', { language: e.target.value })}
                />
                <FormControlLabel control={<Switch checked={config.tts.scan_success}
                  onChange={(e) => update('tts', { scan_success: e.target.checked })} />}
                  label="Озвучавай успешно сканиране" sx={{ mb: 1 }} />
                <FormControlLabel control={<Switch checked={config.tts.scan_error}
                  onChange={(e) => update('tts', { scan_error: e.target.checked })} />}
                  label="Озвучавай грешка" sx={{ mb: 2 }} />
                <Typography gutterBottom>Сила на звука: {Math.round(config.sounds.volume * 100)}%</Typography>
                <Slider min={0} max={1} step={0.1} value={config.sounds.volume}
                  onChange={(_, v) => update('sounds', { volume: v as number })} sx={{ mb: 2 }} />
              </Box>
            )}

            {tab === 2 && (
              <Box>
                <TextField fullWidth label="Текст при сканиране" size="small" sx={{ mb: 2 }}
                  value={config.text.scanning_text}
                  onChange={(e) => update('text', { scanning_text: e.target.value })}
                />
                <TextField fullWidth label="Приветствен текст" size="small" sx={{ mb: 2 }}
                  value={config.text.welcome_message}
                  onChange={(e) => update('text', { welcome_message: e.target.value })}
                />
                <TextField fullWidth label="Текст при успех" size="small" sx={{ mb: 2 }}
                  value={config.text.success_message}
                  onChange={(e) => update('text', { success_message: e.target.value })}
                />
                <TextField fullWidth label="Текст при грешка" size="small" sx={{ mb: 2 }}
                  value={config.text.error_message}
                  onChange={(e) => update('text', { error_message: e.target.value })}
                />
                <TextField fullWidth label="Плейсхолдер QR" size="small" sx={{ mb: 2 }}
                  value={config.text.qr_placeholder}
                  onChange={(e) => update('text', { qr_placeholder: e.target.value })}
                />
                <TextField fullWidth label="Плейсхолдер клавиатура" size="small" sx={{ mb: 2 }}
                  value={config.text.keyboard_placeholder}
                  onChange={(e) => update('text', { keyboard_placeholder: e.target.value })}
                />
              </Box>
            )}

            {tab === 3 && (
              <Box>
                <TextField fullWidth label="Изчакване (сек)" size="small" type="number" sx={{ mb: 2 }}
                  value={config.timeouts.inactivity_reset}
                  onChange={(e) => update('timeouts', { inactivity_reset: parseInt(e.target.value) || 30 })}
                />
                <FormControlLabel control={<Switch checked={config.security.exit_pin_required}
                  onChange={(e) => update('security', { exit_pin_required: e.target.checked })} />}
                  label="Изисквай ПИН за изход" sx={{ mb: 1 }} />
              </Box>
            )}

            <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button variant="contained" startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                onClick={handleSave} disabled={saving || !selectedHwid}>
                {saving ? 'Запазва се...' : 'Запази'}
              </Button>
              {msg && <Alert severity={msg.type} sx={{ flex: 1 }}>{msg.text}</Alert>}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

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

  useEffect(() => {
    if (rateData?.globalSetting?.value) setRateValue(rateData.globalSetting.value);
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
          <Typography variant="h6" gutterBottom color="error.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon /> Сигурност на Kiosk Терминал
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Управление на допълнителните защити при генериране на QR код. Тези настройки важат за всички служители.
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <FormControlLabel control={<Switch checked={data?.kioskSecuritySettings?.requireGps} onChange={(e) => handleToggle('requireGps', e.target.checked)} disabled={updating} />}
              label={<Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>Изисквай GPS верификация <InfoIcon helpText="Ограничава генерирането на QR код до служители, които са на определената GPS локация" /></Box>} />
            <FormControlLabel control={<Switch checked={data?.kioskSecuritySettings?.requireSameNetwork} onChange={(e) => handleToggle('requireSameNetwork', e.target.checked)} disabled={updating} />}
              label={<Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>Изисквай същата локална мрежа <InfoIcon helpText="Генерирането на QR код става само от устройства в същата локална мрежа като сървъра" /></Box>} />
          </Box>
          {msg && <Typography color="success.main" sx={{ mt: 1 }}>{msg}</Typography>}
        </CardContent>
      </Card>

      <Card sx={{ mb: 4, border: '1px solid #ff9800' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom color="warning.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon /> Лимит на опитите за код от клавиатура
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Максимален брой опити за въвеждане на code от терминала за определен период.
            Формат: <code>число/минути</code>, напр. <code>5/minute</code>, <code>10/hour</code>.
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <TextField size="small" value={rateValue} onChange={(e) => setRateValue(e.target.value)} placeholder="5/minute" sx={{ width: 200 }}
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText="Максимален брой опити за въвеждане на код от клавиатурата за определен период" /></InputAdornment> } }} />
            <Button variant="contained" size="small" onClick={handleSaveRateLimit} disabled={updatingRate}>
              {updatingRate ? 'Запазва се...' : 'Запази'}
            </Button>
          </Box>
          {rateMsg && (
            <Typography color={rateMsg.includes('запазен') ? 'success.main' : 'error.main'} sx={{ mt: 1 }}>
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
      <TerminalConfigEditor />
    </Box>
  );
};

export default ConfigPage;
