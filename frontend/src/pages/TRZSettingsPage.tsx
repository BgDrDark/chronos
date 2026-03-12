import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Switch,
  TextField,
  Button,
  Divider,
  Alert,
  Chip,
} from '@mui/material';
import {
  NightsStay as NightIcon,
  Timer as OvertimeIcon,
  Event as HolidayIcon,
  FlightTakeoff as TripIcon,
  WorkHistory as ExperienceIcon,
  Restaurant as VoucherIcon,
  DirectionsCar as TransportIcon,
  CardGiftcard as BenefitIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useMutation, gql } from '@apollo/client';

const UPDATE_GLOBAL_SETTING = gql`
  mutation UpdateGlobalSetting($key: String!, $value: String!) {
    updateGlobalSetting(key: $key, value: $value) {
      key
      value
    }
  }
`;

interface TRZFeature {
  key: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  rateKey?: string;
  rateLabel?: string;
}

const TRZSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Record<string, string>>({
    trz_night_work_enabled: 'false',
    trz_overtime_enabled: 'false',
    trz_holiday_work_enabled: 'false',
    trz_business_trips_enabled: 'false',
    trz_work_experience_enabled: 'false',
    trz_food_vouchers_enabled: 'false',
    trz_transport_allowance_enabled: 'false',
    trz_company_benefits_enabled: 'false',
    trz_default_night_rate: '0.5',
    trz_default_overtime_rate: '1.5',
    trz_default_holiday_rate: '2.0',
    trz_default_daily_allowance: '40.00',
  });

  const [updateSetting] = useMutation(UPDATE_GLOBAL_SETTING);
  const [saved, setSaved] = useState(false);

  const features: TRZFeature[] = [
    {
      key: 'trz_night_work_enabled',
      label: 'Нощен труд',
      description: 'Включва изчисляването на нощен труд (22:00 - 06:00) с 50% надбавка',
      icon: <NightIcon />,
      rateKey: 'trz_default_night_rate',
      rateLabel: 'Надбавка за нощен труд (%)',
    },
    {
      key: 'trz_overtime_enabled',
      label: 'Извънреден труд',
      description: 'Включва изчисляването на извънреден труд (след 8 часа)',
      icon: <OvertimeIcon />,
      rateKey: 'trz_default_overtime_rate',
      rateLabel: 'Множител за извънреден',
    },
    {
      key: 'trz_holiday_work_enabled',
      label: 'Труд по празници',
      description: 'Включва изчисляването на труд по официални празници с 100% надбавка',
      icon: <HolidayIcon />,
      rateKey: 'trz_default_holiday_rate',
      rateLabel: 'Множител за празничен труд',
    },
    {
      key: 'trz_business_trips_enabled',
      label: 'Командировки',
      description: 'Включва управлението на командировки и дневни',
      icon: <TripIcon />,
      rateKey: 'trz_default_daily_allowance',
      rateLabel: 'Дневни (лв)',
    },
    {
      key: 'trz_work_experience_enabled',
      label: 'Трудов стаж',
      description: 'Включва проследяването на трудов стаж и клас',
      icon: <ExperienceIcon />,
    },
    {
      key: 'trz_food_vouchers_enabled',
      label: 'Ваучери за храна',
      description: 'Включва ваучерите за храна (до 200 лв месечно необлагаемо)',
      icon: <VoucherIcon />,
    },
    {
      key: 'trz_transport_allowance_enabled',
      label: 'Транспортни помощи',
      description: 'Включва транспортните помощи за служителите',
      icon: <TransportIcon />,
    },
    {
      key: 'trz_company_benefits_enabled',
      label: 'Фирмени придобивки',
      description: 'Включва фирмените придобивки (служебен автомобил, телефон и др.)',
      icon: <BenefitIcon />,
    },
  ];

  const handleToggle = (key: string) => {
    const newValue = settings[key] === 'true' ? 'false' : 'true';
    setSettings({ ...settings, [key]: newValue });
  };

  const handleRateChange = (key: string, value: string) => {
    setSettings({ ...settings, [key]: value });
  };

  const handleSave = async () => {
    try {
      for (const [key, value] of Object.entries(settings)) {
        await updateSetting({
          variables: { key, value },
        });
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Typography variant="h5" component="h1" gutterBottom sx={{ fontWeight: 'bold', mb: 3 }}>
        ⚙️ ТРЗ Настройки
      </Typography>

      {saved && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Настройките са запазени успешно!
        </Alert>
      )}

      <Alert severity="info" sx={{ mb: 3 }}>
        Включете или изключете ТРЗ функционалностите според нуждите на вашата фирма.
        Всяка функция може да бъде активирана или деактивирана с превключвателя.
      </Alert>

      <Grid container spacing={3}>
        {features.map((feature) => (
          <Grid size={{ xs: 12, md: 6 }} key={feature.key}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                  <Box sx={{ color: 'primary.main', mt: 0.5 }}>
                    {feature.icon}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" component="h3">
                      {feature.label}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </Box>
                  <Switch
                    checked={settings[feature.key] === 'true'}
                    onChange={() => handleToggle(feature.key)}
                    color="primary"
                  />
                </Box>

                {feature.rateKey && settings[feature.key] === 'true' && (
                  <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                    <TextField
                      label={feature.rateLabel}
                      type="number"
                      size="small"
                      value={settings[feature.rateKey || '']}
                      onChange={(e) => handleRateChange(feature.rateKey || '', e.target.value)}
                      sx={{ width: '100%' }}
                      inputProps={{ step: 0.1, min: 0 }}
                    />
                  </Box>
                )}

                <Box sx={{ mt: 2 }}>
                  <Chip
                    label={settings[feature.key] === 'true' ? 'Включено' : 'Изключено'}
                    color={settings[feature.key] === 'true' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          size="large"
        >
          Запази настройките
        </Button>
      </Box>

      <Divider sx={{ my: 4 }} />

      <Typography variant="h6" gutterBottom>
        Описание на надбавките
      </Typography>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Нощен труд
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Труд положен между 22:00 и 06:00 часа. По закон се заплаща с минимум 50% надбавка.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Извънреден труд
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Труд след 8 часа дневно. Първите 2 часа - 50% надбавка, над 2 часа - 100% надбавка.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Труд по празници
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Труд по официални празници. По закон се заплаща с 100% надбавка (множител 2.0).
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TRZSettingsPage;
