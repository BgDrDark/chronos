import React, { useState } from 'react';
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
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  Grid,
  Avatar,
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DirectionsCar as CarIcon,
  LocalGasStation as FuelIcon,
  Build as RepairIcon,
  Security as InsuranceIcon,
  CheckCircle as InspectionIcon,
  Speed as MileageIcon,
  Person as DriverIcon,
  Route as TripIcon,
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

const FleetPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [vehiclesOpen, setVehiclesOpen] = useState(false);
  const [mileageOpen, setMileageOpen] = useState(false);
  const [fuelOpen, setFuelOpen] = useState(false);
  const [repairOpen, setRepairOpen] = useState(false);
  const [insuranceOpen, setInsuranceOpen] = useState(false);
  const [inspectionOpen, setInspectionOpen] = useState(false);
  const [driverOpen, setDriverOpen] = useState(false);
  const [tripOpen, setTripOpen] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const vehicleStatusColors: Record<string, string> = {
    active: 'success',
    in_repair: 'warning',
    out_of_service: 'error',
    sold: 'default',
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 2 }}>
        <Typography variant="h5" component="div" sx={{ fontWeight: 'bold', py: 2 }}>
          Автомобили
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setVehiclesOpen(true)}
        >
          Нов автомобил
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ px: 2, py: 2 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>Общо</Typography>
                <Typography variant="h4">0</Typography>
              </Box>
              <Avatar sx={{ bgcolor: 'primary.main' }}><CarIcon /></Avatar>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>Активни</Typography>
                <Typography variant="h4" color="success.main">0</Typography>
              </Box>
              <Avatar sx={{ bgcolor: 'success.main' }}><CarIcon /></Avatar>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>В ремонт</Typography>
                <Typography variant="h4" color="warning.main">0</Typography>
              </Box>
              <Avatar sx={{ bgcolor: 'warning.main' }}><RepairIcon /></Avatar>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>Извън експлоатация</Typography>
                <Typography variant="h4" color="error.main">0</Typography>
              </Box>
              <Avatar sx={{ bgcolor: 'error.main' }}><CarIcon /></Avatar>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ px: 2 }}>
        <Tab icon={<CarIcon />} label="Автомобили" />
        <Tab icon={<MileageIcon />} label="Километри" />
        <Tab icon={<FuelIcon />} label="Гориво" />
        <Tab icon={<RepairIcon />} label="Ремонти" />
        <Tab icon={<InsuranceIcon />} label="Застраховки" />
        <Tab icon={<InspectionIcon />} label="ГТП" />
        <Tab icon={<DriverIcon />} label="Водачи" />
        <Tab icon={<TripIcon />} label="Маршрути" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Рег. номер</TableCell>
                <TableCell>Марка/Модел</TableCell>
                <TableCell>VIN</TableCell>
                <TableCell>Година</TableCell>
                <TableCell>Гориво</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Пробег</TableCell>
                <TableCell align="right">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={8} align="center">
                  Няма регистрирани автомобили. Добавете първия.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setMileageOpen(true)}>
            Нов запис
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма записи за километри.
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setFuelOpen(true)}>
            Нов запис
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма записи за гориво.
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setRepairOpen(true)}>
            Нов запис
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма записи за ремонти.
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setInsuranceOpen(true)}>
            Нов запис
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма записи за застраховки.
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={5}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setInspectionOpen(true)}>
            Нов запис
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма записи за ГТП.
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={6}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDriverOpen(true)}>
            Нов водач
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма назначени водачи.
        </Typography>
      </TabPanel>

      <TabPanel value={tabValue} index={7}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setTripOpen(true)}>
            Нов маршрут
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary" align="center">
          Няма записи за маршрути.
        </Typography>
      </TabPanel>

      {/* Add Vehicle Dialog */}
      <Dialog open={vehiclesOpen} onClose={() => setVehiclesOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Нов автомобил</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField autoFocus margin="dense" label="Рег. номер" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="VIN" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Марка" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Модел" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Година" type="number" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип</InputLabel>
                <Select label="Тип">
                  <MenuItem value="car">Лека кола</MenuItem>
                  <MenuItem value="truck">Камион</MenuItem>
                  <MenuItem value="van">Бус</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Гориво</InputLabel>
                <Select label="Гориво" defaultValue="dizel">
                  <MenuItem value="benzin">Бензин</MenuItem>
                  <MenuItem value="dizel">Дизел</MenuItem>
                  <MenuItem value="electric">Електрически</MenuItem>
                  <MenuItem value="hybrid">Хибрид</MenuItem>
                  <MenuItem value="lng">LNG</MenuItem>
                  <MenuItem value="cng">CNG</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Статус</InputLabel>
                <Select label="Статус" defaultValue="active">
                  <MenuItem value="active">Активен</MenuItem>
                  <MenuItem value="in_repair">В ремонт</MenuItem>
                  <MenuItem value="out_of_service">Извън експлоатация</MenuItem>
                  <MenuItem value="sold">Продаден</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Цвят" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Начален пробег" type="number" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl margin="dense">
                <FormControlLabel control={<Switch defaultChecked />} label="Фирмен автомобил" />
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={3} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVehiclesOpen(false)}>Отказ</Button>
          <Button onClick={() => setVehiclesOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Mileage Dialog */}
      <Dialog open={mileageOpen} onClose={() => setMileageOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нов запис за километри</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select label="Автомобил">
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField autoFocus margin="dense" label="Дата" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Километри" type="number" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMileageOpen(false)}>Отказ</Button>
          <Button onClick={() => setMileageOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Fuel Dialog */}
      <Dialog open={fuelOpen} onClose={() => setFuelOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нов запис за гориво</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select label="Автомобил">
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField autoFocus margin="dense" label="Дата" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Километри" type="number" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Литри" type="number" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Цена" type="number" fullWidth variant="outlined" InputProps={{ startAdornment: 'лв.' }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип гориво</InputLabel>
                <Select label="Тип гориво" defaultValue="dizel">
                  <MenuItem value="benzin">Бензин</MenuItem>
                  <MenuItem value="dizel">Дизел</MenuItem>
                  <MenuItem value="lng">LNG</MenuItem>
                  <MenuItem value="cng">CNG</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Бензиностанция" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFuelOpen(false)}>Отказ</Button>
          <Button onClick={() => setFuelOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Repair Dialog */}
      <Dialog open={repairOpen} onClose={() => setRepairOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нов запис за ремонт</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select label="Автомобил">
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField autoFocus margin="dense" label="Дата" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Километри" type="number" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Описание" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Сервиз" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Стойност" type="number" fullWidth variant="outlined" InputProps={{ startAdornment: 'лв.' }} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип ремонт</InputLabel>
                <Select label="Тип ремонт">
                  <MenuItem value="maintenance">Техническо обслужване</MenuItem>
                  <MenuItem value="repair">Ремонт</MenuItem>
                  <MenuItem value="tire">Гуми</MenuItem>
                  <MenuItem value="body">Каросерия</MenuItem>
                  <MenuItem value="electrical">Електрика</MenuItem>
                  <MenuItem value="other">Друго</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRepairOpen(false)}>Отказ</Button>
          <Button onClick={() => setRepairOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Insurance Dialog */}
      <Dialog open={insuranceOpen} onClose={() => setInsuranceOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова застраховка</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select label="Автомобил">
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField autoFocus margin="dense" label="Застрахователна компания" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Номер на полица" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип застраховка</InputLabel>
                <Select label="Тип застраховка">
                  <MenuItem value="grazhdanska">Гражданска отговорност</MenuItem>
                  <MenuItem value="avtokasko">Автокаско</MenuItem>
                  <MenuItem value="imot">Имущество</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Начална дата" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Крайна дата" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Стойност" type="number" fullWidth variant="outlined" InputProps={{ startAdornment: 'лв.' }} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInsuranceOpen(false)}>Отказ</Button>
          <Button onClick={() => setInsuranceOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Inspection (GTP) Dialog */}
      <Dialog open={inspectionOpen} onClose={() => setInspectionOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нов преглед ГТП</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select label="Автомобил">
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField autoFocus margin="dense" label="Дата на преглед" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Валиден до" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Номер на протокол" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Стойност" type="number" fullWidth variant="outlined" InputProps={{ startAdornment: 'лв.' }} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Резултат</InputLabel>
                <Select label="Резултат">
                  <MenuItem value="passed">Преминат</MenuItem>
                  <MenuItem value="failed">Непреминат</MenuItem>
                  <MenuItem value="pending">Предстои</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInspectionOpen(false)}>Отказ</Button>
          <Button onClick={() => setInspectionOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Driver Dialog */}
      <Dialog open={driverOpen} onClose={() => setDriverOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нов водач</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Служител</InputLabel>
                <Select label="Служител">
                  <MenuItem value="">-- Изберете служител --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select label="Автомобил">
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField autoFocus margin="dense" label="Номер на шофьорска книжка" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Валидна до" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Телефон" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Категория" fullWidth variant="outlined" placeholder="B, C, D..." />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl margin="dense">
                <FormControlLabel control={<Switch defaultChecked />} label="Основен водач" />
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDriverOpen(false)}>Отказ</Button>
          <Button onClick={() => setDriverOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Trip Dialog */}
      <Dialog open={tripOpen} onClose={() => setTripOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Нов маршрут</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select label="Автомобил">
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Водач</InputLabel>
                <Select label="Водач">
                  <MenuItem value="">-- Изберете водач --</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField autoFocus margin="dense" label="Дата тръгване" type="datetime-local" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Дата връщане" type="datetime-local" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Място тръгване" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Място пристигане" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField margin="dense" label="Километри" type="number" fullWidth variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Цел</InputLabel>
                <Select label="Цел">
                  <MenuItem value="business">Служебна</MenuItem>
                  <MenuItem value="personal">Лична</MenuItem>
                  <MenuItem value="transport">Транспорт</MenuItem>
                  <MenuItem value="delivery">Доставка</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Описание" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTripOpen(false)}>Отказ</Button>
          <Button onClick={() => setTripOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FleetPage;
