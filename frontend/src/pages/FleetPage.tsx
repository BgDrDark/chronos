import React, { useState } from 'react';
import { getErrorMessage } from '../types';
import { useCurrency, getCurrencySymbolForCurrency } from '../currencyContext';
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
  InputAdornment,
} from '@mui/material';
import { InfoIcon } from '../components/ui/InfoIcon';
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
  ArrowBack as BackIcon,
  Visibility as ViewIcon,
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
  query GetVehicles($skip: Int, $limit: Int, $search: String, $status: String, $fuelType: String, $vehicleType: String) {
    vehicles(skip: $skip, limit: $limit, search: $search, status: $status, fuelType: $fuelType, vehicleType: $vehicleType) {
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
        vehicleType { name code }
      }
      totalCount
    }
  }
`;

const GET_VEHICLE_COST_SUMMARY = gql`
  query GetVehicleCostSummary($vehicleId: Int!, $year: Int) {
    vehicleCostSummary(vehicleId: $vehicleId, year: $year) {
      totalFuel
      totalRepairs
      totalInspections
      totalInsurances
      totalVignettes
      totalTolls
      grandTotal
      costPerKm
    }
  }
`;

const GET_VEHICLE_MILEAGE = gql`
  query GetVehicleMileage($vehicleId: Int!) {
    vehicleMileage(vehicleId: $vehicleId) {
      id date mileage notes
    }
  }
`;

const GET_VEHICLE_FUEL = gql`
  query GetVehicleFuel($vehicleId: Int!) {
    vehicleFuelLogs(vehicleId: $vehicleId) {
      id date liters price total fuelType notes
    }
  }
`;

const GET_VEHICLE_REPAIRS = gql`
  query GetVehicleRepairs($vehicleId: Int!) {
    vehicleRepairs(vehicleId: $vehicleId) {
      id date description cost repairType notes
    }
  }
`;

const GET_VEHICLE_INSURANCES = gql`
  query GetVehicleInsurances($vehicleId: Int!) {
    vehicleInsurances(vehicleId: $vehicleId) {
      id provider policyNumber startDate endDate premium insuranceType notes
    }
  }
`;

const GET_VEHICLE_INSPECTIONS = gql`
  query GetVehicleInspections($vehicleId: Int!) {
    vehicleInspections(vehicleId: $vehicleId) {
      id date result nextDate cost protocolNumber notes
    }
  }
`;

const GET_VEHICLE_DRIVERS = gql`
  query GetVehicleDrivers($vehicleId: Int!) {
    vehicleDrivers(vehicleId: $vehicleId) {
      id userId licenseNumber category isPrimary assignedFrom assignedTo notes
    }
  }
`;

const GET_VEHICLE_TRIPS = gql`
  query GetVehicleTrips($vehicleId: Int!) {
    vehicleTrips(vehicleId: $vehicleId) {
      id startTime endTime startAddress endAddress distanceKm purpose notes
    }
  }
`;

const GET_USERS_QUERY = gql`
  query GetUsers {
    users {
      users {
        id
        firstName
        lastName
        email
      }
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
  const { currency } = useCurrency();
  const currencySymbol = getCurrencySymbolForCurrency(currency);
  
  const formatPrice = (value: number | string | null | undefined): string => {
    return `${currencySymbol}${Number(value || 0).toFixed(2)}`;
  };

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
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [fuelFilter, setFuelFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  
  // Detail View State
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(null);
  const [detailTab, setDetailTab] = useState(0);
  const [costYear, setCostYear] = useState(new Date().getFullYear());

  const { data: vehiclesData, refetch: refetchVehicles } = useQuery(GET_VEHICLES_QUERY, {
    variables: { 
      skip: page * rowsPerPage, 
      limit: rowsPerPage,
      search: searchText || undefined,
      status: statusFilter || undefined,
      fuelType: fuelFilter || undefined,
      vehicleType: typeFilter || undefined,
    },
  });

  // Detail Queries
  const { data: costData } = useQuery(GET_VEHICLE_COST_SUMMARY, {
    variables: { vehicleId: selectedVehicleId || 0, year: costYear },
    skip: !selectedVehicleId,
  });
  const { data: mileageData } = useQuery(GET_VEHICLE_MILEAGE, {
    variables: { vehicleId: selectedVehicleId || 0 },
    skip: !selectedVehicleId,
  });
  const { data: fuelData } = useQuery(GET_VEHICLE_FUEL, {
    variables: { vehicleId: selectedVehicleId || 0 },
    skip: !selectedVehicleId,
  });
  const { data: repairData } = useQuery(GET_VEHICLE_REPAIRS, {
    variables: { vehicleId: selectedVehicleId || 0 },
    skip: !selectedVehicleId,
  });
  const { data: insuranceData } = useQuery(GET_VEHICLE_INSURANCES, {
    variables: { vehicleId: selectedVehicleId || 0 },
    skip: !selectedVehicleId,
  });
  const { data: inspectionData } = useQuery(GET_VEHICLE_INSPECTIONS, {
    variables: { vehicleId: selectedVehicleId || 0 },
    skip: !selectedVehicleId,
  });
  const { data: driverData } = useQuery(GET_VEHICLE_DRIVERS, {
    variables: { vehicleId: selectedVehicleId || 0 },
    skip: !selectedVehicleId,
  });
  const { data: tripData } = useQuery(GET_VEHICLE_TRIPS, {
    variables: { vehicleId: selectedVehicleId || 0 },
    skip: !selectedVehicleId,
  });
  const { data: usersData } = useQuery(GET_USERS_QUERY);

  const [editingVehicle, setEditingVehicle] = useState<{ id: number; registrationNumber: string; make: string; model: string; vin: string; year: number; fuelType: string; status: string; color: string; initialMileage: number; isCompanyVehicle: boolean; notes: string } | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const [mileageForm, setMileageForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], mileage: 0, notes: '' });
  const [fuelForm, setFuelForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], mileage: 0, liters: 0, price: 0, total: 0, fuelType: 'dizel', station: '', notes: '' });
  const [repairForm, setRepairForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], mileage: 0, description: '', service: '', cost: 0, repairType: 'maintenance', notes: '' });
  const [insuranceForm, setInsuranceForm] = useState({ vehicleId: '', provider: '', policyNumber: '', startDate: new Date().toISOString().split('T')[0], endDate: '', premium: 0, insuranceType: 'grazhdanska', notes: '' });
  const [inspectionForm, setInspectionForm] = useState({ vehicleId: '', date: new Date().toISOString().split('T')[0], nextDate: '', cost: 0, protocolNumber: '', result: 'passed', notes: '' });
  const [driverForm, setDriverForm] = useState({ userId: '', vehicleId: '', licenseNumber: '', licenseExpiry: '', phone: '', category: 'B', isPrimary: true, notes: '' });
  const [tripForm, setTripForm] = useState({ vehicleId: '', userId: '', startDate: new Date().toISOString().split('T')[0], endDate: '', startLocation: '', endLocation: '', distance: 0, notes: '' });

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

    // VIN Validation
    if (vehicleForm.vin && !/^[A-HJ-NPR-Z0-9]{17}$/i.test(vehicleForm.vin)) {
      setError('VIN трябва да е точно 17 символа (без I, O, Q)');
      return;
    }

    // Year Validation
    const currentYear = new Date().getFullYear();
    if (vehicleForm.year < 1900 || vehicleForm.year > currentYear + 1) {
      setError(`Годината трябва да е между 1900 и ${currentYear + 1}`);
      return;
    }

    // Initial Mileage Validation
    if (vehicleForm.initialMileage < 0) {
      setError('Началният пробег не може да бъде отрицателен');
      return;
    }

    const existingVehicle = vehiclesData?.vehicles?.vehicles?.find(
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
    if (mileageForm.mileage < 0) {
      setError('Километрите не могат да бъдат отрицателни');
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
                <Typography variant="h4">{vehiclesData?.vehicles?.totalCount || 0}</Typography>
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
                  {vehiclesData?.vehicles?.vehicles?.filter((v: { status: string }) => v.status === 'active').length || 0}
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
                  {vehiclesData?.vehicles?.vehicles?.filter((v: { status: string }) => v.status === 'in_repair').length || 0}
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
                  {vehiclesData?.vehicles?.vehicles?.filter((v: { status: string }) => v.status === 'out_of_service').length || 0}
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
        <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            size="small"
            label="Търсене (Рег. номер, Марка, Модел, VIN)"
            value={searchText}
            onChange={(e) => { setSearchText(e.target.value); setPage(0); }}
            sx={{ minWidth: 250, flex: 1 }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Статус</InputLabel>
            <Select value={statusFilter} label="Статус" onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}>
              <MenuItem value="">Всички</MenuItem>
              <MenuItem value="active">Активен</MenuItem>
              <MenuItem value="in_repair">В ремонт</MenuItem>
              <MenuItem value="out_of_service">Извън експлоатация</MenuItem>
              <MenuItem value="sold">Продаден</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Гориво</InputLabel>
            <Select value={fuelFilter} label="Гориво" onChange={(e) => { setFuelFilter(e.target.value); setPage(0); }}>
              <MenuItem value="">Всички</MenuItem>
              <MenuItem value="benzin">Бензин</MenuItem>
              <MenuItem value="dizel">Дизел</MenuItem>
              <MenuItem value="electric">Електрически</MenuItem>
              <MenuItem value="hybrid">Хибрид</MenuItem>
              <MenuItem value="lng">LNG</MenuItem>
              <MenuItem value="cng">CNG</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Тип</InputLabel>
            <Select value={typeFilter} label="Тип" onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }}>
              <MenuItem value="">Всички</MenuItem>
              <MenuItem value="car">Лека кола</MenuItem>
              <MenuItem value="truck">Камион</MenuItem>
              <MenuItem value="van">Бус</MenuItem>
            </Select>
          </FormControl>
        </Box>
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
              {!vehiclesData?.vehicles?.vehicles || vehiclesData.vehicles.vehicles.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    Няма регистрирани автомобили. Добавете първия.
                  </TableCell>
                </TableRow>
              ) : (
                vehiclesData.vehicles.vehicles.map((vehicle: { id: number; registrationNumber: string; make: string; model: string; vin: string; year: number; fuelType: string; status: string; initialMileage: number }) => (
                  <TableRow key={vehicle.id}>
                    <TableCell>{vehicle.registrationNumber}</TableCell>
                    <TableCell>{vehicle.make} {vehicle.model}</TableCell>
                    <TableCell>{vehicle.vin || '-'}</TableCell>
                    <TableCell>{vehicle.year || '-'}</TableCell>
                    <TableCell>{vehicle.fuelType}</TableCell>
                    <TableCell>
                      <Chip 
                        label={vehicle.status === 'active' ? 'Активен' : vehicle.status === 'in_repair' ? 'В ремонт' : 'Извън експлоатация'}
                        color={vehicle.status === 'active' ? 'success' : vehicle.status === 'in_repair' ? 'warning' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{vehicle.initialMileage?.toLocaleString() || 0} км</TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => {
                        setSelectedVehicleId(vehicle.id);
                        setDetailTab(0);
                      }}>
                        <ViewIcon />
                      </IconButton>
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
          <TablePagination
            component="div"
            count={vehiclesData?.vehicles?.totalCount || 0}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
            rowsPerPageOptions={[25, 50, 100]}
            labelRowsPerPage="Редове:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} от ${count !== -1 ? count : `повече от ${to}`}`}
          />
        </TableContainer>
      </TabPanel>

      {/* Vehicle Detail View */}
      {selectedVehicleId && (
        <Box sx={{ mt: 4, p: 3, bgcolor: 'background.paper', borderRadius: 2, boxShadow: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <IconButton onClick={() => setSelectedVehicleId(null)} sx={{ mr: 2 }}>
              <BackIcon />
            </IconButton>
            <Typography variant="h5" fontWeight="bold">
              Детайли за автомобил
            </Typography>
          </Box>

          {/* Cost Summary Card */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Гориво</Typography>
                  <Typography variant="h6" color="warning.main">{formatPrice(costData?.vehicleCostSummary?.totalFuel || 0)}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Ремонти</Typography>
                  <Typography variant="h6" color="error.main">{formatPrice(costData?.vehicleCostSummary?.totalRepairs || 0)}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Застраховки</Typography>
                  <Typography variant="h6" color="info.main">{formatPrice(costData?.vehicleCostSummary?.totalInsurances || 0)}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Общо разходи</Typography>
                  <Typography variant="h6" color="primary.main">{formatPrice(costData?.vehicleCostSummary?.grandTotal || 0)}</Typography>
                  {(costData?.vehicleCostSummary?.costPerKm || 0) > 0 && (
                    <Typography variant="body2" color="text.secondary">
                      {costData?.vehicleCostSummary?.costPerKm?.toFixed(2)} лв/км
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Detail Tabs */}
          <Tabs value={detailTab} onChange={(_, v) => setDetailTab(v)} sx={{ mb: 2 }}>
            <Tab label="Километри" />
            <Tab label="Гориво" />
            <Tab label="Ремонти" />
            <Tab label="Застраховки" />
            <Tab label="ГТП" />
            <Tab label="Водачи" />
            <Tab label="Маршрути" />
          </Tabs>

          <TabPanel value={detailTab} index={0}>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell align="right">Километри</TableCell>
                    <TableCell>Забележки</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {mileageData?.vehicleMileage?.map((m: any) => (
                    <TableRow key={m.id}>
                      <TableCell>{formatDate(m.date)}</TableCell>
                      <TableCell align="right">{m.mileage.toLocaleString()} км</TableCell>
                      <TableCell>{m.notes || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {!mileageData?.vehicleMileage?.length && (
                    <TableRow><TableCell colSpan={3} align="center">Няма записи</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={detailTab} index={1}>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell align="right">Литри</TableCell>
                    <TableCell align="right">Цена</TableCell>
                    <TableCell align="right">Общо</TableCell>
                    <TableCell>Гориво</TableCell>
                    <TableCell>Забележки</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {fuelData?.vehicleFuelLogs?.map((f: any) => (
                    <TableRow key={f.id}>
                      <TableCell>{formatDate(f.date)}</TableCell>
                      <TableCell align="right">{f.liters}</TableCell>
                      <TableCell align="right">{formatPrice(f.price)}</TableCell>
                      <TableCell align="right">{formatPrice(f.total)}</TableCell>
                      <TableCell>{f.fuelType}</TableCell>
                      <TableCell>{f.notes || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {!fuelData?.vehicleFuelLogs?.length && (
                    <TableRow><TableCell colSpan={6} align="center">Няма записи</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={detailTab} index={2}>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell>Описание</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell align="right">Стойност</TableCell>
                    <TableCell>Забележки</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {repairData?.vehicleRepairs?.map((r: any) => (
                    <TableRow key={r.id}>
                      <TableCell>{formatDate(r.date)}</TableCell>
                      <TableCell>{r.description}</TableCell>
                      <TableCell>{r.repairType}</TableCell>
                      <TableCell align="right">{formatPrice(r.cost)}</TableCell>
                      <TableCell>{r.notes || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {!repairData?.vehicleRepairs?.length && (
                    <TableRow><TableCell colSpan={5} align="center">Няма записи</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={detailTab} index={3}>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Застраховател</TableCell>
                    <TableCell>Полица №</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell>Начало</TableCell>
                    <TableCell>Край</TableCell>
                    <TableCell align="right">Премиум</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {insuranceData?.vehicleInsurances?.map((i: any) => (
                    <TableRow key={i.id}>
                      <TableCell>{i.provider}</TableCell>
                      <TableCell>{i.policyNumber}</TableCell>
                      <TableCell>{i.insuranceType}</TableCell>
                      <TableCell>{formatDate(i.startDate)}</TableCell>
                      <TableCell>{formatDate(i.endDate)}</TableCell>
                      <TableCell align="right">{formatPrice(i.premium)}</TableCell>
                    </TableRow>
                  ))}
                  {!insuranceData?.vehicleInsurances?.length && (
                    <TableRow><TableCell colSpan={6} align="center">Няма записи</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={detailTab} index={4}>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell>Резултат</TableCell>
                    <TableCell>Валиден до</TableCell>
                    <TableCell align="right">Стойност</TableCell>
                    <TableCell>Протокол №</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {inspectionData?.vehicleInspections?.map((i: any) => (
                    <TableRow key={i.id}>
                      <TableCell>{formatDate(i.date)}</TableCell>
                      <TableCell>{i.result}</TableCell>
                      <TableCell>{formatDate(i.nextDate)}</TableCell>
                      <TableCell align="right">{formatPrice(i.cost)}</TableCell>
                      <TableCell>{i.protocolNumber || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {!inspectionData?.vehicleInspections?.length && (
                    <TableRow><TableCell colSpan={5} align="center">Няма записи</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={detailTab} index={5}>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Водач ID</TableCell>
                    <TableCell>Категория</TableCell>
                    <TableCell>Основен</TableCell>
                    <TableCell>От</TableCell>
                    <TableCell>До</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {driverData?.vehicleDrivers?.map((d: any) => (
                    <TableRow key={d.id}>
                      <TableCell>{d.userId}</TableCell>
                      <TableCell>{d.category}</TableCell>
                      <TableCell>{d.isPrimary ? 'Да' : 'Не'}</TableCell>
                      <TableCell>{formatDate(d.assignedFrom)}</TableCell>
                      <TableCell>{d.assignedTo ? formatDate(d.assignedTo) : '-'}</TableCell>
                    </TableRow>
                  ))}
                  {!driverData?.vehicleDrivers?.length && (
                    <TableRow><TableCell colSpan={5} align="center">Няма записи</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={detailTab} index={6}>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Начало</TableCell>
                    <TableCell>Край</TableCell>
                    <TableCell>От</TableCell>
                    <TableCell>До</TableCell>
                    <TableCell align="right">Км</TableCell>
                    <TableCell>Цел</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tripData?.vehicleTrips?.map((t: any) => (
                    <TableRow key={t.id}>
                      <TableCell>{formatDate(t.startTime)}</TableCell>
                      <TableCell>{formatDate(t.endTime)}</TableCell>
                      <TableCell>{t.startAddress}</TableCell>
                      <TableCell>{t.endAddress}</TableCell>
                      <TableCell align="right">{t.distanceKm}</TableCell>
                      <TableCell>{t.purpose || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {!tripData?.vehicleTrips?.length && (
                    <TableRow><TableCell colSpan={6} align="center">Няма записи</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>
        </Box>
      )}

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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Регистрационен номер на МПС (напр. СА 1234 АА)" />
                      </InputAdornment>
                    )
                  }
                }}
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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Идентификационен номер на превозното средство (17 символа)" />
                      </InputAdornment>
                    )
                  }
                }}
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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Марка на превозното средство (напр. Volkswagen, BMW)" />
                      </InputAdornment>
                    )
                  }
                }}
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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Модел на превозното средство (напр. Passat, 320d)" />
                      </InputAdornment>
                    )
                  }
                }}
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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Година на производство на автомобила" />
                      </InputAdornment>
                    )
                  }
                }}
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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Цвят на каросерията" />
                      </InputAdornment>
                    )
                  }
                }}
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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Начален пробег в километри при добавяне на автомобила" />
                      </InputAdornment>
                    )
                  }
                }}
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
                    <MenuItem value="in_repair">В ремонт</MenuItem>
                    <MenuItem value="out_of_service">Извън експлоатация</MenuItem>
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
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата на отчитане на километрите" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField 
                margin="dense" label="Километри" type="number" fullWidth variant="outlined" 
                value={mileageForm.mileage}
                onChange={(e) => setMileageForm({ ...mileageForm, mileage: parseInt(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Пробег в километри" />
                      </InputAdornment>
                    )
                  }
                }}
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
              <TextField
                autoFocus margin="dense" label="Дата" type="date" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={fuelForm.date}
                onChange={(e) => setFuelForm({ ...fuelForm, date: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата на зареждането" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Километри" type="number" fullWidth variant="outlined"
                value={fuelForm.mileage}
                onChange={(e) => setFuelForm({ ...fuelForm, mileage: parseFloat(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Километри на автомобила при зареждане" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Литри" type="number" fullWidth variant="outlined"
                value={fuelForm.liters}
                onChange={(e) => setFuelForm({ ...fuelForm, liters: parseFloat(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Количество заредено гориво в литри" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Цена" type="number" fullWidth variant="outlined"
                InputProps={{ startAdornment: currencySymbol }}
                value={fuelForm.price}
                onChange={(e) => setFuelForm({ ...fuelForm, price: parseFloat(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Обща стойност на горивото" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип гориво</InputLabel>
                <Select label="Тип гориво" value={fuelForm.fuelType} onChange={(e) => setFuelForm({ ...fuelForm, fuelType: e.target.value })}>
                  <MenuItem value="benzin">Бензин</MenuItem>
                  <MenuItem value="dizel">Дизел</MenuItem>
                  <MenuItem value="lng">LNG</MenuItem>
                  <MenuItem value="cng">CNG</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Бензиностанция" fullWidth variant="outlined"
                value={fuelForm.station}
                onChange={(e) => setFuelForm({ ...fuelForm, station: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Име/локация на бензиностанцията" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" value={fuelForm.notes} onChange={(e) => setFuelForm({ ...fuelForm, notes: e.target.value })} />
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
              <TextField
                autoFocus margin="dense" label="Дата" type="date" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={repairForm.date}
                onChange={(e) => setRepairForm({ ...repairForm, date: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата на извършения ремонт" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Километри" type="number" fullWidth variant="outlined"
                value={repairForm.mileage}
                onChange={(e) => setRepairForm({ ...repairForm, mileage: parseFloat(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Километри на автомобила при ремонта" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Описание" fullWidth multiline rows={2} variant="outlined" value={repairForm.description} onChange={(e) => setRepairForm({ ...repairForm, description: e.target.value })} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Сервиз" fullWidth variant="outlined"
                value={repairForm.service}
                onChange={(e) => setRepairForm({ ...repairForm, service: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Име на сервиза/фирмата извършила ремонта" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Стойност" type="number" fullWidth variant="outlined"
                InputProps={{ startAdornment: currencySymbol }}
                value={repairForm.cost}
                onChange={(e) => setRepairForm({ ...repairForm, cost: parseFloat(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Стойност на ремонта в лева" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип ремонт</InputLabel>
                <Select label="Тип ремонт" value={repairForm.repairType} onChange={(e) => setRepairForm({ ...repairForm, repairType: e.target.value })}>
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
              <TextField margin="dense" label="Забележки" fullWidth multiline rows={2} variant="outlined" value={repairForm.notes} onChange={(e) => setRepairForm({ ...repairForm, notes: e.target.value })} />
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
              <TextField
                autoFocus margin="dense" label="Застрахователна компания" fullWidth variant="outlined"
                value={insuranceForm.provider}
                onChange={(e) => setInsuranceForm({ ...insuranceForm, provider: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Име на застрахователната компания" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Номер на полица" fullWidth variant="outlined"
                value={insuranceForm.policyNumber}
                onChange={(e) => setInsuranceForm({ ...insuranceForm, policyNumber: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Уникален номер на застрахователната полица" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип застраховка</InputLabel>
                <Select label="Тип застраховка" value={insuranceForm.insuranceType} onChange={(e) => setInsuranceForm({ ...insuranceForm, insuranceType: e.target.value })}>
                  <MenuItem value="grazhdanska">Гражданска отговорност</MenuItem>
                  <MenuItem value="avtokasko">Автокаско</MenuItem>
                  <MenuItem value="imot">Имущество</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Начална дата" type="date" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={insuranceForm.startDate}
                onChange={(e) => setInsuranceForm({ ...insuranceForm, startDate: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Начална дата на застрахователната полица" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Крайна дата" type="date" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={insuranceForm.endDate}
                onChange={(e) => setInsuranceForm({ ...insuranceForm, endDate: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Крайна дата на застрахователната полица" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Стойност" type="number" fullWidth variant="outlined"
                InputProps={{ startAdornment: currencySymbol }}
                value={insuranceForm.premium}
                onChange={(e) => setInsuranceForm({ ...insuranceForm, premium: parseFloat(e.target.value) || 0 })}
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Застрахователна премия в лева" />
                      </InputAdornment>
                    )
                  }
                }}
              />
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
              <TextField
                autoFocus margin="dense" label="Дата на преглед" type="date" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={inspectionForm.date}
                onChange={(e) => setInspectionForm({ ...inspectionForm, date: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата на техническия преглед (ГТП)" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Валиден до" type="date" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={inspectionForm.nextDate}
                onChange={(e) => setInspectionForm({ ...inspectionForm, nextDate: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата на изтичане на техническия преглед" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Номер на протокол" fullWidth variant="outlined"
                value={inspectionForm.protocolNumber}
                onChange={(e) => setInspectionForm({ ...inspectionForm, protocolNumber: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Номер на протокола от техническия преглед" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Стойност" type="number" fullWidth variant="outlined"
                InputProps={{ startAdornment: currencySymbol }}
                value={inspectionForm.cost}
                onChange={(e) => setInspectionForm({ ...inspectionForm, cost: parseFloat(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Такса за техническия преглед" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Резултат</InputLabel>
                <Select label="Резултат" value={inspectionForm.result} onChange={(e) => setInspectionForm({ ...inspectionForm, result: e.target.value })}>
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
                  {usersData?.users?.users?.map((user: { id: number; firstName: string; lastName: string; email: string }) => (
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
              <TextField
                autoFocus margin="dense" label="Номер на шофьорска книжка" fullWidth variant="outlined"
                value={driverForm.licenseNumber}
                onChange={(e) => setDriverForm({ ...driverForm, licenseNumber: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Номер на свидетелството за управление" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Валидна до" type="date" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={driverForm.licenseExpiry}
                onChange={(e) => setDriverForm({ ...driverForm, licenseExpiry: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата на изтичане на свидетелството" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Телефон" fullWidth variant="outlined"
                value={driverForm.phone}
                onChange={(e) => setDriverForm({ ...driverForm, phone: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Телефон за връзка с водача" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Категория" fullWidth variant="outlined"
                value={driverForm.category}
                onChange={(e) => setDriverForm({ ...driverForm, category: e.target.value })}
                placeholder="B, C, D..."
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Категория на свидетелството (B, C, D...)" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl margin="dense">
                <FormControlLabel control={<Switch checked={driverForm.isPrimary} onChange={(e) => setDriverForm({ ...driverForm, isPrimary: e.target.checked })} />} label="Основен водач" />
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
                  {usersData?.users?.users?.map((user: { id: number; firstName: string; lastName: string; email: string }) => (
                    <MenuItem key={user.id} value={user.id}>
                      {user.firstName} {user.lastName} ({user.email})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                autoFocus margin="dense" label="Дата тръгване" type="datetime-local" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={tripForm.startDate}
                onChange={(e) => setTripForm({ ...tripForm, startDate: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата и час на тръгване" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Дата връщане" type="datetime-local" fullWidth variant="outlined"
                InputLabelProps={{ shrink: true }}
                value={tripForm.endDate}
                onChange={(e) => setTripForm({ ...tripForm, endDate: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Дата и час на връщане" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Място тръгване" fullWidth variant="outlined"
                value={tripForm.startLocation}
                onChange={(e) => setTripForm({ ...tripForm, startLocation: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Начална локация на маршрута" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Място пристигане" fullWidth variant="outlined"
                value={tripForm.endLocation}
                onChange={(e) => setTripForm({ ...tripForm, endLocation: e.target.value })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Крайна локация на маршрута" />
                      </InputAdornment>
                    )
                  }
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                margin="dense" label="Километри" type="number" fullWidth variant="outlined"
                value={tripForm.distance}
                onChange={(e) => setTripForm({ ...tripForm, distance: parseFloat(e.target.value) || 0 })}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <InfoIcon helpText="Общо изминати километри" />
                      </InputAdornment>
                    )
                  }
                }}
              />
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
