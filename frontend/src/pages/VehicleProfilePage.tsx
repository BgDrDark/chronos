import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCurrency, formatCurrencyValue } from '../currencyContext';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Card,
  CardContent,
  Grid,
  Avatar,
  IconButton,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Add as AddIcon,
  DirectionsCar as CarIcon,
  LocalGasStation as FuelIcon,
  Build as RepairIcon,
  Security as InsuranceIcon,
  CheckCircle as InspectionIcon,
  Speed as MileageIcon,
  Person as DriverIcon,
  Description as DocIcon,
  ConfirmationNumber as VignetteIcon,
  Toll as TollIcon,
  AttachMoney as ExpenseIcon,
  History as HistoryIcon,
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const VehicleProfilePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currency } = useCurrency();
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const vehicleData = {
    id: id,
    registrationNumber: 'E1234AB',
    vin: 'ABC123456789',
    make: 'Toyota',
    model: 'Corolla',
    year: 2020,
    fuelType: 'dizel',
    color: 'Син',
    status: 'active',
    mileage: 125000,
    isCompany: true,
  };

  const driverData = {
    name: 'Петър Петров',
    phone: '+359 888 123 456',
    licenseNumber: '123456789',
    validUntil: '2027-05-15',
  };

  const insuranceData = [
    { type: 'Гражданска', company: 'ДЗИ', endDate: '2026-06-15', premium: 450 },
    { type: 'Автокаско', company: 'Алианц', endDate: '2026-08-20', premium: 800 },
  ];

  const inspectionData = [
    { date: '2025-03-10', validUntil: '2026-03-10', result: 'passed', certificate: 'ГТП-12345' },
  ];

  const expenseSummary = {
    fuel: 2450,
    repairs: 800,
    insurance: 1250,
    inspection: 100,
    total: 4600,
  };

  const historyData = [
    { date: '2026-03-10', type: 'ГТП', description: 'Преминат преглед' },
    { date: '2026-03-05', type: 'Застраховка', description: 'Подновена гражданска' },
    { date: '2026-03-01', type: 'Ремонт', description: 'Смяна на гуми' },
    { date: '2026-02-15', type: 'Гориво', description: 'Заредени 50 л' },
  ];

  const statusLabels: Record<string, string> = {
    active: 'Активен',
    in_repair: 'В ремонт',
    out_of_service: 'Извън експлоатация',
    sold: 'Продаден',
  };

  const statusColors: Record<string, string> = {
    active: 'success',
    in_repair: 'warning',
    out_of_service: 'error',
    sold: 'default',
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/admin/fleet')}>
          <BackIcon />
        </IconButton>
        <Typography variant="h5" component="div" sx={{ fontWeight: 'bold' }}>
          {vehicleData.registrationNumber} - {vehicleData.make} {vehicleData.model}
        </Typography>
        <Chip 
          label={statusLabels[vehicleData.status]} 
          color={statusColors[vehicleData.status] as any} 
          size="small" 
        />
      </Box>

      {/* Vehicle Info Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  <CarIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{vehicleData.make} {vehicleData.model}</Typography>
                  <Typography color="text.secondary">{vehicleData.year}</Typography>
                </Box>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, md: 9 }}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Typography variant="body2" color="text.secondary">Рег. номер</Typography>
                  <Typography variant="body1">{vehicleData.registrationNumber}</Typography>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Typography variant="body2" color="text.secondary">VIN</Typography>
                  <Typography variant="body1">{vehicleData.vin}</Typography>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Typography variant="body2" color="text.secondary">Гориво</Typography>
                  <Typography variant="body1">{vehicleData.fuelType === 'dizel' ? 'Дизел' : vehicleData.fuelType}</Typography>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Typography variant="body2" color="text.secondary">Пробег</Typography>
                  <Typography variant="body1">{vehicleData.mileage.toLocaleString()} км</Typography>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Driver Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: 'info.main' }}>
                <DriverIcon />
              </Avatar>
              <Box>
                <Typography variant="subtitle1" fontWeight="bold">Основен водач</Typography>
                <Typography>{driverData.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {driverData.phone} | Книга: {driverData.licenseNumber}
                </Typography>
              </Box>
            </Box>
            <Button variant="outlined" size="small">Промени</Button>
          </Box>
        </CardContent>
      </Card>

      {/* Expense Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <FuelIcon color="primary" />
              <Typography variant="h6">{formatCurrencyValue(expenseSummary.fuel, currency)}</Typography>
              <Typography variant="body2" color="text.secondary">Гориво</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <RepairIcon color="warning" />
              <Typography variant="h6">{formatCurrencyValue(expenseSummary.repairs, currency)}</Typography>
              <Typography variant="body2" color="text.secondary">Ремонти</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <InsuranceIcon color="info" />
              <Typography variant="h6">{formatCurrencyValue(expenseSummary.insurance, currency)}</Typography>
              <Typography variant="body2" color="text.secondary">Застраховки</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <ExpenseIcon color="success" />
              <Typography variant="h6">{formatCurrencyValue(expenseSummary.total, currency)}</Typography>
              <Typography variant="body2" color="text.secondary">Общо</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab icon={<MileageIcon />} label="Километри" />
          <Tab icon={<FuelIcon />} label="Гориво" />
          <Tab icon={<RepairIcon />} label="Ремонти" />
          <Tab icon={<InsuranceIcon />} label="Застраховки" />
          <Tab icon={<InspectionIcon />} label="ГТП" />
          <Tab icon={<DocIcon />} label="Документи" />
          <Tab icon={<VignetteIcon />} label="Винетки" />
          <Tab icon={<TollIcon />} label="Толове" />
          <Tab icon={<ExpenseIcon />} label="Разходи" />
          <Tab icon={<HistoryIcon />} label="История" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нов запис</Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Километри</TableCell>
                <TableCell>Източник</TableCell>
                <TableCell>Забележки</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={4} align="center">Няма записи</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Ново зареждане</Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Километри</TableCell>
                <TableCell>Литри</TableCell>
                <TableCell>Цена/л</TableCell>
                <TableCell>Общо</TableCell>
                <TableCell>Място</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={6} align="center">Няма записи</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нов ремонт</Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell>Описание</TableCell>
                <TableCell>Сервиз</TableCell>
                <TableCell>Стойност</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={5} align="center">Няма записи</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нова застраховка</Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Тип</TableCell>
                <TableCell>Компания</TableCell>
                <TableCell>Валидна до</TableCell>
                <TableCell>Премия</TableCell>
                <TableCell>Статус</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {insuranceData.map((ins, idx) => (
                <TableRow key={idx}>
                  <TableCell>{ins.type}</TableCell>
                  <TableCell>{ins.company}</TableCell>
                  <TableCell>{ins.endDate}</TableCell>
                  <TableCell>{formatCurrencyValue(ins.premium, currency)}</TableCell>
                  <TableCell>
                    <Chip 
                      label={new Date(ins.endDate) > new Date() ? 'Активна' : 'Изтекла'} 
                      color={new Date(ins.endDate) > new Date() ? 'success' : 'error'} 
                      size="small" 
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нов преглед</Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Валидна до</TableCell>
                <TableCell>Резултат</TableCell>
                <TableCell>Протокол</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {inspectionData.map((insp, idx) => (
                <TableRow key={idx}>
                  <TableCell>{insp.date}</TableCell>
                  <TableCell>{insp.validUntil}</TableCell>
                  <TableCell>
                    <Chip label="Преминат" color="success" size="small" />
                  </TableCell>
                  <TableCell>{insp.certificate}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={5}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нов документ</Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма документи
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={6}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нова винетка</Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма винетки
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={7}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нов тол</Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма записи за толове
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={8}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />}>Нов разход</Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма разходи
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={9}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell>Описание</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {historyData.map((item, idx) => (
                <TableRow key={idx}>
                  <TableCell>{item.date}</TableCell>
                  <TableCell>
                    <Chip label={item.type} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>{item.description}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>
    </Box>
  );
};

export default VehicleProfilePage;
