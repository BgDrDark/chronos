import React, { useState } from 'react';
import { getErrorMessage } from '../types';
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
  Alert,
  CircularProgress,
  Chip,
  IconButton,
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
import { gql, useMutation, useQuery } from '@apollo/client';

const CREATE_VEHICLE_MUTATION = gql`
  mutation CreateVehicle($input: VehicleCreateInput!) {
    createVehicle(input: $input) {
      id
      registrationNumber
      make
      model
      status
    }
  }
`;

const UPDATE_VEHICLE_MUTATION = gql`
  mutation UpdateVehicle($id: Int!, $input: VehicleUpdateInput!) {
    updateVehicle(id: $id, input: $input) {
      id
      registrationNumber
      make
      model
      status
    }
  }
`;

const DELETE_VEHICLE_MUTATION = gql`
  mutation DeleteVehicle($id: Int!) {
    deleteVehicle(id: $id)
  }
`;

const CREATE_MILEAGE_MUTATION = gql`
  mutation CreateVehicleMileage($input: VehicleMileageInput!) {
    createVehicleMileage(input: $input) {
      id
    }
  }
`;

const CREATE_FUEL_MUTATION = gql`
  mutation CreateVehicleFuel($input: VehicleFuelInput!) {
    createVehicleFuel(input: $input) {
      id
    }
  }
`;

const CREATE_REPAIR_MUTATION = gql`
  mutation CreateVehicleRepair($input: VehicleRepairInput!) {
    createVehicleRepair(input: $input) {
      id
    }
  }
`;

const CREATE_INSURANCE_MUTATION = gql`
  mutation CreateVehicleInsurance($input: VehicleInsuranceInput!) {
    createVehicleInsurance(input: $input) {
      id
    }
  }
`;

const CREATE_INSPECTION_MUTATION = gql`
  mutation CreateVehicleInspection($input: VehicleInspectionInput!) {
    createVehicleInspection(input: $input) {
      id
    }
  }
`;

const CREATE_DRIVER_MUTATION = gql`
  mutation CreateVehicleDriver($input: VehicleDriverInput!) {
    createVehicleDriver(input: $input) {
      id
    }
  }
`;

const CREATE_TRIP_MUTATION = gql`
  mutation CreateVehicleTrip($input: VehicleTripInput!) {
    createVehicleTrip(input: $input) {
      id
    }
  }
`;

const GET_VEHICLES_QUERY = gql`
  query GetVehicles {
    vehicles {
      id
      registrationNumber
      vin
      make
      model
      year
      vehicleTypeId
      fuelType
      status
      color
      initialMileage
      isCompany
      notes
    }
  }
`;

const GET_USERS_QUERY = gql`
  query GetUsers {
    users {
      id
      firstName
      lastName
      email
    }
  }
`;

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

  const [vehicleForm, setVehicleForm] = useState({
    registrationNumber: '',
    vin: '',
    make: '',
    model: '',
    year: new Date().getFullYear(),
    vehicleType: 'car',
    fuelType: 'dizel',
    status: 'active',
    color: '',
    initialMileage: 0,
    isCompanyVehicle: true,
    notes: '',
  });

  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [createVehicle] = useMutation(CREATE_VEHICLE_MUTATION);
  const [updateVehicle] = useMutation(UPDATE_VEHICLE_MUTATION);
  const [deleteVehicle] = useMutation(DELETE_VEHICLE_MUTATION);
  const [createMileage] = useMutation(CREATE_MILEAGE_MUTATION);
  const [createFuel] = useMutation(CREATE_FUEL_MUTATION);
  const [createRepair] = useMutation(CREATE_REPAIR_MUTATION);
  const [createInsurance] = useMutation(CREATE_INSURANCE_MUTATION);
  const [createInspection] = useMutation(CREATE_INSPECTION_MUTATION);
  const [createDriver] = useMutation(CREATE_DRIVER_MUTATION);
  const [createTrip] = useMutation(CREATE_TRIP_MUTATION);
  const { data: vehiclesData, refetch: refetchVehicles } = useQuery(GET_VEHICLES_QUERY);
  const { data: usersData } = useQuery(GET_USERS_QUERY);

  const [editingVehicle, setEditingVehicle] = useState<{ id: number; registrationNumber: string; make: string; model: string; vin: string; year: number; fuelType: string; status: string; color: string; initialMileage: number; isCompanyVehicle: boolean; notes: string } | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const [mileageForm, setMileageForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], mileage: 0, notes: '' });
  const [fuelForm, setFuelForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], liters: 0, price: 0, total: 0, notes: '' });
  const [repairForm, setRepairForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], description: '', cost: 0, notes: '' });
  const [insuranceForm, setInsuranceForm] = useState({ vehicleId: '', provider: '', policyNumber: '', startDate: new Date().toISOString().split('T')[0], endDate: '', premium: 0, notes: '' });
  const [inspectionForm, setInspectionForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], nextDate: '', cost: 0, notes: '' });
  const [driverForm, setDriverForm] = useState({ userId: '', vehicleId: '', licenseNumber: '', licenseExpiry: '', phone: '', category: 'B', isPrimary: true, notes: '' });
  const [tripForm, setTripForm] = useState({ vehicleId: '', userId: '', startDate: new Date().toISOString().split('T')[0], startLocation: '', endLocation: '', distance: 0, notes: '' });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleVehicleChange = (field: string, value: unknown) => {
    setVehicleForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSaveVehicle = async () => {
    if (!vehicleForm.registrationNumber || !vehicleForm.make) {
      setError('Моля, попълте регистрационния номер и марката');
      return;
    }

    const existingVehicle = vehiclesData?.vehicles?.find(
      (v: { registrationNumber: string }) => v.registrationNumber.toLowerCase() === vehicleForm.registrationNumber.toLowerCase()
    );
    if (existingVehicle) {
      setError('Автомобил с този регистрационен номер вече съществува');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await createVehicle({
        variables: {
          input: {
            registrationNumber: vehicleForm.registrationNumber,
            vin: vehicleForm.vin || null,
            make: vehicleForm.make,
            model: vehicleForm.model || null,
            year: vehicleForm.year,
            vehicleType: vehicleForm.vehicleType,
            fuelType: vehicleForm.fuelType,
            status: vehicleForm.status,
            color: vehicleForm.color || null,
            initialMileage: vehicleForm.initialMileage || 0,
            isCompanyVehicle: vehicleForm.isCompanyVehicle,
            notes: vehicleForm.notes || null,
          }
        }
      });

      await refetchVehicles();
      setVehiclesOpen(false);
      setVehicleForm({
        registrationNumber: '',
        vin: '',
        make: '',
        model: '',
        year: new Date().getFullYear(),
        vehicleType: 'car',
        fuelType: 'dizel',
        status: 'active',
        color: '',
        initialMileage: 0,
        isCompanyVehicle: true,
        notes: '',
      });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMileage = async () => {
    if (!mileageForm.vehicleId || !mileageForm.mileage) {
      setError('Моля, изберете автомобил и въведете километри');
      return;
    }
    try {
      await createMileage({
        variables: {
          input: {
            vehicleId: parseInt(mileageForm.vehicleId),
            date: mileageForm.date,
            mileage: mileageForm.mileage,
            notes: mileageForm.notes,
          }
        }
      });
      setMileageOpen(false);
      setMileageForm({ vehicleId: '', date: new Date().toISOString().split('T')[0], mileage: 0, notes: '' });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleSaveFuel = async () => {
    if (!fuelForm.vehicleId) {
      setError('Моля, изберете автомобил');
      return;
    }
    try {
      const total = fuelForm.liters * fuelForm.price;
      await createFuel({
        variables: {
          input: {
            vehicleId: parseInt(fuelForm.vehicleId),
            date: fuelForm.date,
            liters: fuelForm.liters,
            price: fuelForm.price,
            total: total,
            fuelType: 'dizel',
          }
        }
      });
      setFuelOpen(false);
      setFuelForm({ vehicleId: '', date: new Date().toISOString().split('T')[0], liters: 0, price: 0, total: 0, notes: '' });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleSaveRepair = async () => {
    if (!repairForm.vehicleId || !repairForm.description) {
      setError('Моля, изберете автомобил и въведете описание');
      return;
    }
    try {
      await createRepair({
        variables: {
          input: {
            vehicleId: parseInt(repairForm.vehicleId),
            date: repairForm.date,
            description: repairForm.description,
            cost: repairForm.cost,
            repairType: 'maintenance',
          }
        }
      });
      setRepairOpen(false);
      setRepairForm({ vehicleId: '', date: new Date().toISOString().split('T')[0], description: '', cost: 0, notes: '' });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleSaveInsurance = async () => {
    if (!insuranceForm.vehicleId || !insuranceForm.provider || !insuranceForm.policyNumber) {
      setError('Моля, попълте всички задължителни полета');
      return;
    }
    try {
      await createInsurance({
        variables: {
          input: {
            vehicleId: parseInt(insuranceForm.vehicleId),
            provider: insuranceForm.provider,
            policyNumber: insuranceForm.policyNumber,
            startDate: insuranceForm.startDate,
            endDate: insuranceForm.endDate,
            premium: insuranceForm.premium,
            insuranceType: 'grazhdanska',
          }
        }
      });
      setInsuranceOpen(false);
      setInsuranceForm({ vehicleId: '', provider: '', policyNumber: '', startDate: new Date().toISOString().split('T')[0], endDate: '', premium: 0, notes: '' });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleSaveInspection = async () => {
    if (!inspectionForm.vehicleId) {
      setError('Моля, изберете автомобил');
      return;
    }
    try {
      await createInspection({
        variables: {
          input: {
            vehicleId: parseInt(inspectionForm.vehicleId),
            date: inspectionForm.date,
            nextDate: inspectionForm.nextDate,
            cost: inspectionForm.cost,
            result: 'passed',
          }
        }
      });
      setInspectionOpen(false);
      setInspectionForm({ vehicleId: '', date: new Date().toISOString().split('T')[0], nextDate: '', cost: 0, notes: '' });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleSaveDriver = async () => {
    if (!driverForm.userId || !driverForm.vehicleId || !driverForm.licenseNumber) {
      setError('Моля, попълте всички задължителни полета');
      return;
    }
    try {
      await createDriver({
        variables: {
          input: {
            vehicleId: parseInt(driverForm.vehicleId),
            userId: parseInt(driverForm.userId),
            licenseNumber: driverForm.licenseNumber,
            licenseExpiry: driverForm.licenseExpiry,
            phone: driverForm.phone,
            category: driverForm.category,
            isPrimary: driverForm.isPrimary,
          }
        }
      });
      setDriverOpen(false);
      setDriverForm({ userId: '', vehicleId: '', licenseNumber: '', licenseExpiry: '', phone: '', category: 'B', isPrimary: true, notes: '' });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleSaveTrip = async () => {
    if (!tripForm.vehicleId || !tripForm.userId) {
      setError('Моля, изберете автомобил и водач');
      return;
    }
    try {
      await createTrip({
        variables: {
          input: {
            vehicleId: parseInt(tripForm.vehicleId),
            userId: parseInt(tripForm.userId),
            startDate: tripForm.startDate,
            startLocation: tripForm.startLocation,
            endLocation: tripForm.endLocation,
            distance: tripForm.distance,
            tripType: 'business',
          }
        }
      });
      setTripOpen(false);
      setTripForm({ vehicleId: '', userId: '', startDate: new Date().toISOString().split('T')[0], startLocation: '', endLocation: '', distance: 0, notes: '' });
    } catch (err) {
      setError(getErrorMessage(err));
    }
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
                <Typography variant="h4">{vehiclesData?.vehicles?.length || 0}</Typography>
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
                <Typography variant="h4" color="success.main">
                  {vehiclesData?.vehicles?.filter((v: { status: string }) => v.status === 'active').length || 0}
                </Typography>
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
                <Typography variant="h4" color="warning.main">
                  {vehiclesData?.vehicles?.filter((v: { status: string }) => v.status === 'repair').length || 0}
                </Typography>
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
                <Typography variant="h4" color="error.main">
                  {vehiclesData?.vehicles?.filter((v: { status: string }) => v.status === 'inactive').length || 0}
                </Typography>
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
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setVehiclesOpen(true)}>
            Добави автомобил
          </Button>
        </Box>
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
              {!vehiclesData?.vehicles || vehiclesData.vehicles.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    Няма регистрирани автомобили. Добавете първия.
                  </TableCell>
                </TableRow>
              ) : (
                vehiclesData.vehicles.map((vehicle: { id: number; registrationNumber: string; make: string; model: string; vin: string; year: number; fuelType: string; status: string; initialMileage: number }) => (
                  <TableRow key={vehicle.id}>
                    <TableCell>{vehicle.registrationNumber}</TableCell>
                    <TableCell>{vehicle.make} {vehicle.model}</TableCell>
                    <TableCell>{vehicle.vin || '-'}</TableCell>
                    <TableCell>{vehicle.year || '-'}</TableCell>
                    <TableCell>{vehicle.fuelType}</TableCell>
                    <TableCell>
                      <Chip 
                        label={vehicle.status === 'active' ? 'Активен' : vehicle.status === 'repair' ? 'В ремонт' : 'Извън експлоатация'}
                        color={vehicle.status === 'active' ? 'success' : vehicle.status === 'repair' ? 'warning' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{vehicle.initialMileage?.toLocaleString() || 0} км</TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => {
                        setEditingVehicle({
                          id: vehicle.id,
                          registrationNumber: vehicle.registrationNumber,
                          make: vehicle.make,
                          model: vehicle.model || '',
                          vin: vehicle.vin || '',
                          year: vehicle.year || new Date().getFullYear(),
                          fuelType: vehicle.fuelType,
                          status: vehicle.status,
                          color: '',
                          initialMileage: vehicle.initialMileage || 0,
                          isCompanyVehicle: true,
                          notes: ''
                        });
                        setEditDialogOpen(true);
                      }}>
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={async () => {
                        if (confirm(`Сигурни ли сте, че искате да изтриете ${vehicle.registrationNumber}?`)) {
                          try {
                            await deleteVehicle({ variables: { id: vehicle.id } });
                            await refetchVehicles();
                          } catch (err) {
                            setError(getErrorMessage(err));
                          }
                        }
                      }}>
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
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
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                autoFocus 
                margin="dense" 
                label="Рег. номер *" 
                fullWidth 
                variant="outlined" 
                value={vehicleForm.registrationNumber}
                onChange={(e) => handleVehicleChange('registrationNumber', e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" 
                label="VIN" 
                fullWidth 
                variant="outlined" 
                value={vehicleForm.vin}
                onChange={(e) => handleVehicleChange('vin', e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" 
                label="Марка *" 
                fullWidth 
                variant="outlined" 
                value={vehicleForm.make}
                onChange={(e) => handleVehicleChange('make', e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" 
                label="Модел" 
                fullWidth 
                variant="outlined" 
                value={vehicleForm.model}
                onChange={(e) => handleVehicleChange('model', e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" 
                label="Година" 
                type="number" 
                fullWidth 
                variant="outlined" 
                value={vehicleForm.year}
                onChange={(e) => handleVehicleChange('year', parseInt(e.target.value))}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип</InputLabel>
                <Select 
                  label="Тип" 
                  value={vehicleForm.vehicleType}
                  onChange={(e) => handleVehicleChange('vehicleType', e.target.value)}
                >
                  <MenuItem value="car">Лека кола</MenuItem>
                  <MenuItem value="truck">Камион</MenuItem>
                  <MenuItem value="van">Бус</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Гориво</InputLabel>
                <Select 
                  label="Гориво" 
                  value={vehicleForm.fuelType}
                  onChange={(e) => handleVehicleChange('fuelType', e.target.value)}
                >
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
                <Select 
                  label="Статус" 
                  value={vehicleForm.status}
                  onChange={(e) => handleVehicleChange('status', e.target.value)}
                >
                  <MenuItem value="active">Активен</MenuItem>
                  <MenuItem value="in_repair">В ремонт</MenuItem>
                  <MenuItem value="out_of_service">Извън експлоатация</MenuItem>
                  <MenuItem value="sold">Продаден</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" 
                label="Цвят" 
                fullWidth 
                variant="outlined" 
                value={vehicleForm.color}
                onChange={(e) => handleVehicleChange('color', e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" 
                label="Начален пробег" 
                type="number" 
                fullWidth 
                variant="outlined" 
                value={vehicleForm.initialMileage}
                onChange={(e) => handleVehicleChange('initialMileage', parseInt(e.target.value) || 0)}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl margin="dense">
                <FormControlLabel 
                  control={
                    <Switch 
                      checked={vehicleForm.isCompanyVehicle}
                      onChange={(e) => handleVehicleChange('isCompanyVehicle', e.target.checked)}
                    />
                  } 
                  label="Фирмен автомобил" 
                />
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField 
                margin="dense" 
                label="Забележки" 
                fullWidth 
                multiline 
                rows={3} 
                variant="outlined" 
                value={vehicleForm.notes}
                onChange={(e) => handleVehicleChange('notes', e.target.value)}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVehiclesOpen(false)}>Отказ</Button>
          <Button onClick={handleSaveVehicle} variant="contained" disabled={saving}>
            {saving ? <CircularProgress size={24} /> : 'Запази'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Vehicle Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Редактиране на автомобил</DialogTitle>
        <DialogContent>
          {editingVehicle && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField 
                  autoFocus 
                  margin="dense" 
                  label="Рег. номер *" 
                  fullWidth 
                  variant="outlined" 
                  value={editingVehicle.registrationNumber}
                  onChange={(e) => setEditingVehicle({ ...editingVehicle, registrationNumber: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField 
                  margin="dense" 
                  label="VIN" 
                  fullWidth 
                  variant="outlined" 
                  value={editingVehicle.vin}
                  onChange={(e) => setEditingVehicle({ ...editingVehicle, vin: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField 
                  margin="dense" 
                  label="Марка *" 
                  fullWidth 
                  variant="outlined" 
                  value={editingVehicle.make}
                  onChange={(e) => setEditingVehicle({ ...editingVehicle, make: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField 
                  margin="dense" 
                  label="Модел" 
                  fullWidth 
                  variant="outlined" 
                  value={editingVehicle.model}
                  onChange={(e) => setEditingVehicle({ ...editingVehicle, model: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField 
                  margin="dense" 
                  label="Година" 
                  type="number" 
                  fullWidth 
                  variant="outlined" 
                  value={editingVehicle.year}
                  onChange={(e) => setEditingVehicle({ ...editingVehicle, year: parseInt(e.target.value) })}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth margin="dense">
                  <InputLabel>Статус</InputLabel>
                  <Select 
                    label="Статус" 
                    value={editingVehicle.status}
                    onChange={(e) => setEditingVehicle({ ...editingVehicle, status: e.target.value })}
                  >
                    <MenuItem value="active">Активен</MenuItem>
                    <MenuItem value="repair">В ремонт</MenuItem>
                    <MenuItem value="inactive">Извън експлоатация</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Отказ</Button>
          <Button onClick={async () => {
            if (!editingVehicle) return;
            try {
              await updateVehicle({
                variables: {
                  id: editingVehicle.id,
                  input: {
                    registrationNumber: editingVehicle.registrationNumber,
                    make: editingVehicle.make,
                    model: editingVehicle.model,
                    vin: editingVehicle.vin,
                    year: editingVehicle.year,
                    status: editingVehicle.status,
                  }
                }
              });
              await refetchVehicles();
              setEditDialogOpen(false);
            } catch (err) {
              setError(getErrorMessage(err));
            }
          }} variant="contained">
            Запази
          </Button>
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
                <Select 
                  label="Автомобил" 
                  value={mileageForm.vehicleId}
                  onChange={(e) => setMileageForm({ ...mileageForm, vehicleId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                  {vehiclesData?.vehicles?.map((vehicle: { id: number; registrationNumber: string; make: string; model: string }) => (
                    <MenuItem key={vehicle.id} value={vehicle.id}>
                      {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                autoFocus margin="dense" label="Дата" type="date" fullWidth variant="outlined" 
                InputLabelProps={{ shrink: true }}
                value={mileageForm.date}
                onChange={(e) => setMileageForm({ ...mileageForm, date: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" label="Километри" type="number" fullWidth variant="outlined" 
                value={mileageForm.mileage}
                onChange={(e) => setMileageForm({ ...mileageForm, mileage: parseInt(e.target.value) || 0 })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField 
                margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" 
                value={mileageForm.notes}
                onChange={(e) => setMileageForm({ ...mileageForm, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMileageOpen(false)}>Отказ</Button>
          <Button onClick={handleSaveMileage} variant="contained">Запази</Button>
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
                <Select 
                  label="Автомобил" 
                  value={fuelForm.vehicleId}
                  onChange={(e) => setFuelForm({ ...fuelForm, vehicleId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                  {vehiclesData?.vehicles?.map((vehicle: { id: number; registrationNumber: string; make: string; model: string }) => (
                    <MenuItem key={vehicle.id} value={vehicle.id}>
                      {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                    </MenuItem>
                  ))}
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
          <Button onClick={handleSaveFuel} variant="contained">Запази</Button>
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
                <Select 
                  label="Автомобил" 
                  value={repairForm.vehicleId}
                  onChange={(e) => setRepairForm({ ...repairForm, vehicleId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                  {vehiclesData?.vehicles?.map((vehicle: { id: number; registrationNumber: string; make: string; model: string }) => (
                    <MenuItem key={vehicle.id} value={vehicle.id}>
                      {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                    </MenuItem>
                  ))}
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
          <Button onClick={handleSaveRepair} variant="contained">Запази</Button>
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
                <Select 
                  label="Автомобил" 
                  value={insuranceForm.vehicleId}
                  onChange={(e) => setInsuranceForm({ ...insuranceForm, vehicleId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                  {vehiclesData?.vehicles?.map((vehicle: { id: number; registrationNumber: string; make: string; model: string }) => (
                    <MenuItem key={vehicle.id} value={vehicle.id}>
                      {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                    </MenuItem>
                  ))}
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
          <Button onClick={handleSaveInsurance} variant="contained">Запази</Button>
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
                <Select 
                  label="Автомобил" 
                  value={inspectionForm.vehicleId}
                  onChange={(e) => setInspectionForm({ ...inspectionForm, vehicleId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                  {vehiclesData?.vehicles?.map((vehicle: { id: number; registrationNumber: string; make: string; model: string }) => (
                    <MenuItem key={vehicle.id} value={vehicle.id}>
                      {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                    </MenuItem>
                  ))}
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
          <Button onClick={handleSaveInspection} variant="contained">Запази</Button>
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
                <Select 
                  label="Служител" 
                  value={driverForm.userId}
                  onChange={(e) => setDriverForm({ ...driverForm, userId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете служител --</MenuItem>
                  {usersData?.users?.map((user: { id: number; firstName: string; lastName: string; email: string }) => (
                    <MenuItem key={user.id} value={user.id}>
                      {user.firstName} {user.lastName} ({user.email})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Автомобил</InputLabel>
                <Select 
                  label="Автомобил" 
                  value={driverForm.vehicleId}
                  onChange={(e) => setDriverForm({ ...driverForm, vehicleId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                  {vehiclesData?.vehicles?.map((vehicle: { id: number; registrationNumber: string; make: string; model: string }) => (
                    <MenuItem key={vehicle.id} value={vehicle.id}>
                      {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                    </MenuItem>
                  ))}
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
          <Button onClick={handleSaveDriver} variant="contained">Запази</Button>
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
                <Select 
                  label="Автомобил" 
                  value={tripForm.vehicleId}
                  onChange={(e) => setTripForm({ ...tripForm, vehicleId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете автомобил --</MenuItem>
                  {vehiclesData?.vehicles?.map((vehicle: { id: number; registrationNumber: string; make: string; model: string }) => (
                    <MenuItem key={vehicle.id} value={vehicle.id}>
                      {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Водач</InputLabel>
                <Select 
                  label="Водач" 
                  value={tripForm.userId}
                  onChange={(e) => setTripForm({ ...tripForm, userId: e.target.value })}
                >
                  <MenuItem value="">-- Изберете водач --</MenuItem>
                  {usersData?.users?.map((user: { id: number; firstName: string; lastName: string; email: string }) => (
                    <MenuItem key={user.id} value={user.id}>
                      {user.firstName} {user.lastName} ({user.email})
                    </MenuItem>
                  ))}
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
          <Button onClick={handleSaveTrip} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FleetPage;
