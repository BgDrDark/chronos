import { useState, useEffect, useMemo } from 'react';
import {
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
  Container,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tooltip,
  InputAdornment,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import {
  Send as SendIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Mail as MailIcon,
  ExpandMore,
  Search as SearchIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  DoneAll as DoneAllIcon,

} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import { ME_QUERY } from '../graphql/queries';
import {
  GET_MY_NOTIFICATIONS,
  MARK_NOTIFICATION_READ,
  MARK_ALL_NOTIFICATIONS_READ,
  DELETE_NOTIFICATION,
} from '../graphql/notifications';
import { formatDate } from '../utils/dateUtils';

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
  mutation TestNotification($eventType: String!, $recipientEmail: String) {
    testNotification(eventType: $eventType, recipientEmail: $recipientEmail)
  }
`;

const EVENT_TYPES = [
  { value: 'shift_swap', label: 'Размяна на смени', icon: '🔄' },
  { value: 'leave_approved', label: 'Одобрена отпуска', icon: '✅' },
  { value: 'leave_rejected', label: 'Отказана отпуска', icon: '❌' },
  { value: 'low_stock', label: 'Ниска наличност', icon: '📦' },
  { value: 'new_order', label: 'Нова поръчка', icon: '📋' },
  { value: 'order_completed', label: 'Поръчка завършена', icon: '✔️' },
  { value: 'inventory_completed', label: 'Инвентаризация', icon: '📊' },
  { value: 'payroll_ready', label: 'Заплати готови', icon: '💰' },
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

interface Props {
  tab?: string;
}

export default function NotificationsPage({ tab }: Props) {
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

  const [markRead] = useMutation(MARK_NOTIFICATION_READ);
  const [markAllRead] = useMutation(MARK_ALL_NOTIFICATIONS_READ);
  const [deleteNotif] = useMutation(DELETE_NOTIFICATION);

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
  const [testEmail, setTestEmail] = useState<string>('');

  const [eventSearch, setEventSearch] = useState('');

  const [listFilter, setListFilter] = useState<'all' | 'unread' | 'read'>('all');
  const [listPage, setListPage] = useState(0);
  const [listRowsPerPage, setListRowsPerPage] = useState(20);

  const { data: notifData, refetch: refetchNotifs } = useQuery(GET_MY_NOTIFICATIONS, {
    variables: {
      unreadOnly: listFilter === 'unread',
      offset: listPage * listRowsPerPage,
      limit: listRowsPerPage,
    },
  });

  const notifications = notifData?.myNotifications || [];

  useEffect(() => {
    if (settingsData?.notificationSettings) {
      setTimeout(() => {
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
      }, 0);
    }
  }, [settingsData]);

  useEffect(() => {
    if (smtpData?.smtpSettings) {
      setTimeout(() => {
        setSmtpForm({
          smtpServer: smtpData.smtpSettings.smtpServer || '',
          smtpPort: smtpData.smtpSettings.smtpPort || 587,
          smtpUsername: smtpData.smtpSettings.smtpUsername || '',
          smtpPassword: smtpData.smtpSettings.smtpPassword || '',
          senderEmail: smtpData.smtpSettings.senderEmail || '',
          useTls: smtpData.smtpSettings.useTls ?? true,
        });
      }, 0);
    }
  }, [smtpData]);

  const filteredEvents = useMemo(() => {
    if (!eventSearch) return EVENT_TYPES;
    const q = eventSearch.toLowerCase();
    return EVENT_TYPES.filter(e => e.label.toLowerCase().includes(q) || e.value.toLowerCase().includes(q));
  }, [eventSearch]);

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
      showMessage('success', 'Настройките са запазени!');
      refetch();
    } catch {
      showMessage('error', 'Грешка при запазване');
    }
  };

  const handleSaveSmtp = async () => {
    try {
      await updateSmtp({ variables: { settings: smtpForm } });
      showMessage('success', 'SMTP настройките са запазени!');
    } catch {
      showMessage('error', 'Грешка при запазване на SMTP');
    }
  };

  const handleTestEmail = async (eventType: string) => {
    try {
      await testNotification({ variables: { eventType, recipientEmail: testEmail || null } });
      showMessage('success', 'Тестовият имейл е изпратен!');
    } catch {
      showMessage('error', 'Грешка при изпращане на тест');
    }
  };

  const handleMarkRead = async (id: number) => {
    await markRead({ variables: { id } });
    refetchNotifs();
  };

  const handleMarkAllRead = async () => {
    await markAllRead();
    refetchNotifs();
  };

  const handleDeleteNotif = async (id: number) => {
    await deleteNotif({ variables: { id } });
    refetchNotifs();
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const activeCount = settings.filter(s => s.enabled).length;

  if (!companyId) {
    return <CircularProgress />;
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {message && (
        <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      {tab === 'list' && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography variant="h6" fontWeight="bold">Уведомления</Typography>
              <Typography variant="body2" color="text.secondary">История на изпратените уведомления</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <ToggleButtonGroup
                value={listFilter}
                exclusive
                onChange={(_, v) => { if (v) { setListFilter(v); setListPage(0); } }}
                size="small"
              >
                <ToggleButton value="all">Всички</ToggleButton>
                <ToggleButton value="unread">Непрочетени</ToggleButton>
                <ToggleButton value="read">Прочетени</ToggleButton>
              </ToggleButtonGroup>
              <Button
                variant="outlined"
                size="small"
                startIcon={<DoneAllIcon />}
                onClick={handleMarkAllRead}
              >
                Маркирай всички
              </Button>
            </Box>
          </Box>

          {notifications.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <Typography color="text.secondary">Няма уведомления</Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Съобщение</TableCell>
                    <TableCell width={140}>Дата</TableCell>
                    <TableCell width={80}>Статус</TableCell>
                    <TableCell width={120}>Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {notifications.map((n: any) => (
                    <TableRow
                      key={n.id}
                      sx={{
                        bgcolor: n.isRead ? 'transparent' : 'rgba(25, 118, 210, 0.04)',
                        '&:hover': { bgcolor: 'action.hover' },
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={n.isRead ? 'normal' : 'medium'}>
                          {n.message}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(n.createdAt)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={n.isRead ? 'Прочетено' : 'Ново'}
                          size="small"
                          color={n.isRead ? 'default' : 'primary'}
                          variant={n.isRead ? 'outlined' : 'filled'}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {!n.isRead && (
                            <Tooltip title="Маркирай като прочетено">
                              <IconButton size="small" onClick={() => handleMarkRead(n.id)}>
                                <DoneAllIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Изтрий">
                            <IconButton size="small" color="error" onClick={() => handleDeleteNotif(n.id)}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          <TablePagination
            component="div"
            count={-1}
            page={listPage}
            onPageChange={(_, p) => setListPage(p)}
            rowsPerPage={listRowsPerPage}
            onRowsPerPageChange={(e) => {
              setListRowsPerPage(parseInt(e.target.value, 10));
              setListPage(0);
            }}
            labelDisplayedRows={({ from, to }) => `${from}-${to} от общо`}
          />
        </Paper>
      )}

      {tab === 'events' && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography variant="h6" fontWeight="bold">Събития и уведомления</Typography>
              <Typography variant="body2" color="text.secondary">
                {activeCount} от {EVENT_TYPES.length} активни
              </Typography>
            </Box>
            <TextField
              size="small"
              placeholder="Търси събитие..."
              value={eventSearch}
              onChange={e => setEventSearch(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment>
                  ),
                },
              }}
              sx={{ width: 280 }}
            />
          </Box>

          {filteredEvents.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <Typography color="text.secondary">Няма събития, съответстващи на търсенето</Typography>
            </Box>
          ) : (
            filteredEvents.map((event) => {
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
                <Accordion key={event.value} disableGutters sx={{ mb: 1, '&:before': { display: 'none' } }}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', pr: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1 }}>
                        {setting.enabled ? (
                          <ActiveIcon color="success" fontSize="small" />
                        ) : (
                          <InactiveIcon color="disabled" fontSize="small" />
                        )}
                        <Typography variant="subtitle2" fontWeight="medium">
                          {event.icon} {event.label}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5 }} onClick={e => e.stopPropagation()}>
                        {setting.emailEnabled && <Chip icon={<MailIcon />} label="Email" size="small" color="primary" variant="outlined" />}
                        {setting.pushEnabled && <Chip label="Push" size="small" color="secondary" variant="outlined" />}
                      </Box>
                      <FormControlLabel
                        control={
                          <Switch
                            size="small"
                            checked={setting.enabled}
                            onChange={(e) => handleSettingChange(event.value, 'enabled', e.target.checked)}
                          />
                        }
                        label=""
                        onClick={e => e.stopPropagation()}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={setting.emailEnabled}
                              onChange={(e) => handleSettingChange(event.value, 'emailEnabled', e.target.checked)}
                              disabled={!setting.enabled}
                            />
                          }
                          label="Имейл известия"
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
                          label="Push известия (браузър)"
                        />
                      </Grid>

                      <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                          fullWidth
                          label="Минимален интервал (мин)"
                          type="number"
                          value={setting.intervalMinutes}
                          onChange={(e) => handleSettingChange(event.value, 'intervalMinutes', parseInt(e.target.value))}
                          disabled={!setting.enabled}
                          size="small"
                          helperText="Между две известия"
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
                            <Typography variant="subtitle2" gutterBottom>Имейл шаблон</Typography>
                            <TextField
                              fullWidth
                              multiline
                              rows={4}
                              value={setting.emailTemplate}
                              onChange={(e) => handleSettingChange(event.value, 'emailTemplate', e.target.value)}
                              disabled={!setting.enabled}
                              placeholder={DEFAULT_TEMPLATE}
                              helperText="Използвай {{event_type}} и {{event_details}} за променливи"
                              size="small"
                            />
                          </Grid>

                          <Grid size={{ xs: 12, sm: 6 }}>
                            <Typography variant="subtitle2" gutterBottom>Получатели</Typography>
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
                                <IconButton size="small" onClick={() => {
                                  const newRecipients = setting.recipients.filter((_: Recipient, i: number) => i !== idx);
                                  handleSettingChange(event.value, 'recipients', newRecipients);
                                }}>
                                  <DeleteIcon />
                                </IconButton>
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
                            <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                              Оставeте празно за всички потребители
                            </Typography>
                          </Grid>
                        </>
                      )}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              );
            })
          )}
        </Box>
      )}

      {tab === 'smtp' && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            SMTP настройки
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Конфигурирайте SMTP сървъра за изпращане на имейли.
          </Typography>

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 8 }}>
              <TextField
                fullWidth
                label="SMTP сървър"
                value={smtpForm.smtpServer}
                onChange={(e) => setSmtpForm({ ...smtpForm, smtpServer: e.target.value })}
                placeholder="smtp.gmail.com"
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                fullWidth
                label="Порт"
                type="number"
                value={smtpForm.smtpPort}
                onChange={(e) => setSmtpForm({ ...smtpForm, smtpPort: parseInt(e.target.value) })}
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Потребител"
                value={smtpForm.smtpUsername}
                onChange={(e) => setSmtpForm({ ...smtpForm, smtpUsername: e.target.value })}
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Парола"
                type="password"
                value={smtpForm.smtpPassword}
                onChange={(e) => setSmtpForm({ ...smtpForm, smtpPassword: e.target.value })}
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 8 }}>
              <TextField
                fullWidth
                label="Email изпращач"
                value={smtpForm.senderEmail}
                onChange={(e) => setSmtpForm({ ...smtpForm, senderEmail: e.target.value })}
                placeholder="noreply@company.com"
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }} sx={{ display: 'flex', alignItems: 'center' }}>
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
            <Grid size={{ xs: 12, sm: 8 }}>
              <TextField
                fullWidth
                label="Тестов получател"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="test@example.com"
                helperText="Оставете празно за изпращане до текущия потребител"
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }} sx={{ display: 'flex', alignItems: 'flex-end' }}>
              <Button
                variant="outlined"
                startIcon={testing ? <CircularProgress size={20} /> : <MailIcon />}
                onClick={() => handleTestEmail('smtp_test')}
                disabled={testing}
                sx={{ height: 40, width: '100%' }}
              >
                {testing ? 'Изпраща се...' : 'Изпрати тест'}
              </Button>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSaveSmtp}
                disabled={updatingSmtp}
              >
                Запази SMTP настройки
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Container>
  );
}
