import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Grid,
  TextField,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Send as SendIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import {
  useQuery,
  useMutation,
  gql,
} from '@apollo/client';
import { ME_QUERY } from '../graphql/queries';

const GET_NOTIFICATION_SETTINGS = gql`
  query GetNotificationSettings($companyId: Int!) {
    notificationSettings(companyId: $companyId) {
      id
      eventType
      emailEnabled
      pushEnabled
      emailTemplate
      recipients
      intervalMinutes
      enabled
    }
  }
`;

const GET_SMTP_SETTINGS = gql`
  query GetSmtpSettings {
    smtpSettings {
      smtpServer
      smtpPort
      smtpUsername
      smtpPassword
      senderEmail
      useTls
    }
  }
`;

const SAVE_NOTIFICATION_SETTING = gql`
  mutation SaveNotificationSetting($settingData: NotificationSettingInput!) {
    saveNotificationSetting(settingData: $settingData) {
      id
      eventType
      enabled
    }
  }
`;

const UPDATE_SMTP_SETTINGS = gql`
  mutation UpdateSmtpSettings($settings: SmtpSettingsInput!) {
    updateSmtpSettings(settings: $settings) {
      smtpServer
    }
  }
`;

const TEST_NOTIFICATION = gql`
  mutation TestNotification($eventType: String!) {
    testNotification(eventType: $eventType)
  }
`;

const EVENT_TYPES = [
  { value: 'shift_swap', label: 'Размяна на смени' },
  { value: 'leave_approved', label: 'Одобрена отпуска' },
  { value: 'leave_rejected', label: 'Отказана отпуска' },
  { value: 'low_stock', label: 'Ниска наличност в склад' },
  { value: 'new_order', label: 'Нова поръчка' },
  { value: 'order_completed', label: 'Поръчката е завършена' },
  { value: 'inventory_completed', label: 'Инвентаризация приключена' },
  { value: 'payroll_ready', label: 'Заплатите са готови' },
];

const DEFAULT_TEMPLATE = `Здравейте,

Има ново събитие: {{event_type}}

{{event_details}}

Поздрави,
Chronos екип`;

interface Recipient {
  type: 'email' | 'role';
  value: string;
}

interface NotificationSetting {
  id?: number;
  eventType: string;
  emailEnabled: boolean;
  pushEnabled: boolean;
  emailTemplate: string;
  recipients: Recipient[];
  intervalMinutes: number;
  enabled: boolean;
}

const NotificationsPageTabMap: Record<string, number> = {
  'events': 0,
  'smtp': 1,
};

interface Props {
  tab?: string;
}

export default function NotificationsPage({ tab }: Props) {
  const initialTab = tab ? (NotificationsPageTabMap[tab] ?? 0) : 0;
  const { data: meData } = useQuery(ME_QUERY);
  const companyId = meData?.me?.companyId;
  
  const { data: settingsData, refetch } = useQuery(GET_NOTIFICATION_SETTINGS, {
    variables: { companyId },
    skip: !companyId,
  });

  const { data: smtpData } = useQuery(GET_SMTP_SETTINGS);

  const [saveSetting, { loading: saving }] = useMutation(SAVE_NOTIFICATION_SETTING);
  const [updateSmtp, { loading: updatingSmtp }] = useMutation(UPDATE_SMTP_SETTINGS);
  const [testNotification, { loading: testing }] = useMutation(TEST_NOTIFICATION);

  const [tabValue, setTabValue] = useState(initialTab);
  const [settings, setSettings] = useState<NotificationSetting[]>([]);
  const [smtpForm, setSmtpForm] = useState({
    smtpServer: '',
    smtpPort: 587,
    smtpUsername: '',
    smtpPassword: '',
    senderEmail: '',
    useTls: true,
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (settingsData?.notificationSettings) {
      // eslint-disable-next-line
      setSettings(settingsData.notificationSettings.map((s: any) => {
        let parsedRecipients: Recipient[] = [];
        try {
          if (s.recipients) {
            parsedRecipients = typeof s.recipients === 'string' 
              ? JSON.parse(s.recipients) 
              : s.recipients;
          }
        } catch {
          parsedRecipients = [];
        }
        return {
          id: s.id,
          eventType: s.eventType,
          emailEnabled: s.emailEnabled,
          pushEnabled: s.pushEnabled,
          emailTemplate: s.emailTemplate || DEFAULT_TEMPLATE,
          recipients: parsedRecipients,
          intervalMinutes: s.intervalMinutes || 60,
          enabled: s.enabled,
        };
      }));
    }
  }, [settingsData]);

  useEffect(() => {
    if (smtpData?.smtpSettings) {
      // eslint-disable-next-line
      setSmtpForm({
        smtpServer: smtpData.smtpSettings.smtpServer || '',
        smtpPort: smtpData.smtpSettings.smtpPort || 587,
        smtpUsername: smtpData.smtpSettings.smtpUsername || '',
        smtpPassword: smtpData.smtpSettings.smtpPassword || '',
        senderEmail: smtpData.smtpSettings.senderEmail || '',
        useTls: smtpData.smtpSettings.useTls ?? true,
      });
    }
  }, [smtpData]);

  const handleSettingChange = (eventType: string, field: keyof NotificationSetting, value: any) => {
    setSettings(prev => {
      const existing = prev.find(s => s.eventType === eventType);
      if (existing) {
        return prev.map(s => 
          s.eventType === eventType ? { ...s, [field]: value } : s
        );
      } else {
        const newSetting: NotificationSetting = {
          eventType,
          emailEnabled: false,
          pushEnabled: false,
          emailTemplate: DEFAULT_TEMPLATE,
          recipients: [],
          intervalMinutes: 60,
          enabled: false,
          [field]: value,
        };
        return [...prev, newSetting];
      }
    });
  };

  const handleSaveSetting = async (setting: NotificationSetting) => {
    try {
      await saveSetting({
        variables: {
          settingData: {
            id: setting.id,
            eventType: setting.eventType,
            emailEnabled: setting.emailEnabled,
            pushEnabled: setting.pushEnabled,
            emailTemplate: setting.emailTemplate,
            recipients: JSON.stringify(setting.recipients || []),
            intervalMinutes: setting.intervalMinutes,
            enabled: setting.enabled,
            companyId,
          },
        },
      });
      setMessage({ type: 'success', text: 'Настройките са запазени!' });
      refetch();
      setTimeout(() => setMessage(null), 3000);
    } catch {
      setMessage({ type: 'error', text: 'Грешка при запазване' });
    }
  };

  const handleSaveSmtp = async () => {
    try {
      await updateSmtp({
        variables: {
          settings: smtpForm,
        },
      });
      setMessage({ type: 'success', text: 'SMTP настройките са запазени!' });
      setTimeout(() => setMessage(null), 3000);
    } catch {
      setMessage({ type: 'error', text: 'Грешка при запазване на SMTP' });
    }
  };

  const handleTestEmail = async (eventType: string) => {
    try {
      await testNotification({ variables: { eventType } });
      setMessage({ type: 'success', text: 'Тестовият имейл е изпратен!' });
      setTimeout(() => setMessage(null), 3000);
    } catch {
      setMessage({ type: 'error', text: 'Грешка при изпращане на тест' });
    }
  };

  if (!companyId) {
    return <CircularProgress />;
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_: any, v: number) => setTabValue(v)}>
            <Tab label="Събития и Уведомления" />
            <Tab label="SMTP Настройки" />
          </Tabs>
        </Box>

        {tabValue === 0 && (
          <Box sx={{ p: 3 }}>
            {message && (
              <Alert severity={message.type} sx={{ mb: 2 }}>
                {message.text}
              </Alert>
            )}

            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Конфигурирайте за всяко събитие какви уведомления да се изпращат и по какъв начин.
            </Typography>

            {EVENT_TYPES.map((event) => {
              const setting = settings.find(s => s.eventType === event.value) || {
                eventType: event.value,
                emailEnabled: false,
                pushEnabled: false,
                emailTemplate: DEFAULT_TEMPLATE,
                recipients: [],
                intervalMinutes: 60,
                enabled: false,
              };

              return (
                <Paper key={event.value} variant="outlined" sx={{ mb: 2, p: 2 }}>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {event.label}
                        </Typography>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={setting.enabled}
                              onChange={(e) => handleSettingChange(event.value, 'enabled', e.target.checked)}
                            />
                          }
                          label="Активно"
                        />
                      </Box>
                    </Grid>

                    <Grid size={{ xs: 12, sm: 6 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={setting.emailEnabled}
                            onChange={(e) => handleSettingChange(event.value, 'emailEnabled', e.target.checked)}
                            disabled={!setting.enabled}
                          />
                        }
                        label="Имейл"
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={setting.pushEnabled}
                            onChange={(e) => handleSettingChange(event.value, 'pushEnabled', e.target.checked)}
                            disabled={!setting.enabled}
                          />
                        }
                        label="Push"
                      />
                    </Grid>

                    <Grid size={{ xs: 12, sm: 4 }}>
                      <TextField
                        fullWidth
                        label="Интервал (минути)"
                        type="number"
                        value={setting.intervalMinutes}
                        onChange={(e) => handleSettingChange(event.value, 'intervalMinutes', parseInt(e.target.value))}
                        disabled={!setting.enabled}
                        size="small"
                        helperText="Минимален интервал между имейли"
                      />
                    </Grid>

                    <Grid size={{ xs: 12, sm: 8 }} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<SendIcon />}
                        onClick={() => handleTestEmail(event.value)}
                        disabled={!setting.emailEnabled || testing}
                      >
                        Тест
                      </Button>
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={<SaveIcon />}
                        onClick={() => handleSaveSetting(setting)}
                        disabled={saving}
                      >
                        Запази
                      </Button>
                    </Grid>

                    {setting.emailEnabled && (
                      <>
                        <Grid size={{ xs: 12, sm: 6 }}>
                          <TextField
                            fullWidth
                            label="Имейл шаблон (HTML)"
                            multiline
                            rows={4}
                            value={setting.emailTemplate}
                            onChange={(e) => handleSettingChange(event.value, 'emailTemplate', e.target.value)}
                            disabled={!setting.enabled}
                            placeholder={DEFAULT_TEMPLATE}
                            helperText="Използвай {{event_type}} и {{event_details}} за променливи"
                          />
                        </Grid>

                        <Grid size={{ xs: 12, sm: 6 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Получатели
                          </Typography>
                          {setting.recipients?.map((recipient: Recipient, idx: number) => (
                            <Box key={idx} sx={{ display: 'flex', gap: 1, mb: 1 }}>
                              <TextField
                                select
                                size="small"
                                value={recipient.type}
                                onChange={(e) => {
                                  const newRecipients = [...setting.recipients];
                                  newRecipients[idx] = { ...recipient, type: e.target.value as 'email' | 'role' };
                                  handleSettingChange(event.value, 'recipients', newRecipients);
                                }}
                                SelectProps={{ native: true }}
                                sx={{ width: 100 }}
                              >
                                <option value="email">Имейл</option>
                                <option value="role">Роля</option>
                              </TextField>
                              <TextField
                                size="small"
                                value={recipient.value}
                                onChange={(e) => {
                                  const newRecipients = [...setting.recipients];
                                  newRecipients[idx] = { ...recipient, value: e.target.value };
                                  handleSettingChange(event.value, 'recipients', newRecipients);
                                }}
                                placeholder={recipient.type === 'email' ? 'email@example.com' : 'employee, manager, admin'}
                                sx={{ flex: 1 }}
                              />
                              <Button size="small" onClick={() => {
                                const newRecipients = setting.recipients.filter((_: Recipient, i: number) => i !== idx);
                                handleSettingChange(event.value, 'recipients', newRecipients);
                              }}>
                                <DeleteIcon />
                              </Button>
                            </Box>
                          ))}
                          <Button
                            size="small"
                            startIcon={<AddIcon />}
                            onClick={() => {
                              const newRecipients = [...(setting.recipients || []), { type: 'email' as const, value: '' }];
                              handleSettingChange(event.value, 'recipients', newRecipients);
                            }}
                          >
                            Добави получател
                          </Button>
                          <Typography variant="caption" display="block" color="text.secondary">
                            Оставeте празно за всички потребители
                          </Typography>
                        </Grid>
                      </>
                    )}
                  </Grid>
                </Paper>
              );
            })}
          </Box>
        )}

        {tabValue === 1 && (
          <Box sx={{ p: 3 }}>
            {message && (
              <Alert severity={message.type} sx={{ mb: 2 }}>
                {message.text}
              </Alert>
            )}

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              SMTP Настройки за имейли
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Конфигурирайте SMTP сървъра за изпращане на имейли.
            </Typography>

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 8 }}>
                <TextField
                  fullWidth
                  label="SMTP Сървър"
                  value={smtpForm.smtpServer}
                  onChange={(e) => setSmtpForm({ ...smtpForm, smtpServer: e.target.value })}
                  placeholder="smtp.gmail.com"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField
                  fullWidth
                  label="Порт"
                  type="number"
                  value={smtpForm.smtpPort}
                  onChange={(e) => setSmtpForm({ ...smtpForm, smtpPort: parseInt(e.target.value) })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Потребител"
                  value={smtpForm.smtpUsername}
                  onChange={(e) => setSmtpForm({ ...smtpForm, smtpUsername: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Парола"
                  type="password"
                  value={smtpForm.smtpPassword}
                  onChange={(e) => setSmtpForm({ ...smtpForm, smtpPassword: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 8 }}>
                <TextField
                  fullWidth
                  label="Sender Email"
                  value={smtpForm.senderEmail}
                  onChange={(e) => setSmtpForm({ ...smtpForm, senderEmail: e.target.value })}
                  placeholder="noreply@company.com"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={smtpForm.useTls}
                      onChange={(e) => setSmtpForm({ ...smtpForm, useTls: e.target.checked })}
                    />
                  }
                  label="TLS"
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveSmtp}
                  disabled={updatingSmtp}
                >
                  Запази SMTP
                </Button>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>
    </Container>
  );
}
