import React, { useState } from 'react';
import { Box, Typography, Paper, Card, CardContent, Grid, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, CircularProgress, Chip, FormControl, InputLabel, Select, MenuItem, Stepper, Step, StepLabel } from '@mui/material';
import { DirectionsCar as CarIcon, LocalGasStation as FuelIcon, Speed as SpeedIcon, Assignment as ChecklistIcon } from '@mui/icons-material';
import { gql, useMutation, useQuery } from '@apollo/client';
import { useDriverMode } from '../context/DriverModeContext';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { saveOfflineEntry } from '../db/fleet-offline-store';

const GET_VEHICLES = gql`
  query GetVehiclesForDriver {
    vehicles(skip: 0, limit: 50) {
      vehicles {
        id registrationNumber make model year fuelType status color initialMileage
      }
    }
  }
`;

const CREATE_MILEAGE = gql`
  mutation CreateMileage($input: VehicleMileageCreateInput!) {
    createVehicleMileage(input: $input) { id }
  }
`;

const CREATE_FUEL = gql`
  mutation CreateFuel($input: VehicleFuelInput!) {
    createVehicleFuel(input: $input) { id }
  }
`;

const CHECKLIST_ITEMS = [
  'Гуми (налягане и състояние)',
  'Ниво на гориво',
  'Ниво на масло',
  'Охладителна течност',
  'Спирачки',
  'Осветление (фарове, стопове, мигачи)',
  'Чистачки и стъкла',
  'Огледала',
  'Ремъци и маркучи',
  'Документи (ТАЛОН, талон за ГТП, застраховка)',
];

const DriverDashboard: React.FC = () => {
  const { isDriverMode } = useDriverMode();
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(null);
  const [showFuelForm, setShowFuelForm] = useState(false);
  const [showMileageForm, setShowMileageForm] = useState(false);
  const [showChecklist, setShowChecklist] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [checkedItems, setCheckedItems] = useState<Record<number, boolean>>({});
  const [fuelLiters, setFuelLiters] = useState(0);
  const [fuelPrice, setFuelPrice] = useState(0);
  const [fuelType, setFuelType] = useState('dizel');
  const [fuelNotes, setFuelNotes] = useState('');
  const [mileageValue, setMileageValue] = useState(0);
  const [mileageNotes, setMileageNotes] = useState('');

  const { data: vehiclesData, loading: vehiclesLoading } = useQuery(GET_VEHICLES);
  const [createMileage, { loading: savingMileage }] = useMutation(CREATE_MILEAGE, { refetchQueries: ['GetVehicleMileage'] });
  const [createFuel, { loading: savingFuel }] = useMutation(CREATE_FUEL, { refetchQueries: ['GetVehicleFuel'] });

  const vehicles = vehiclesData?.vehicles?.vehicles || [];
  const { isOnline } = useNetworkStatus();

  const handleMileageSave = async () => {
    if (!selectedVehicleId || !mileageValue) return;
    try {
      if (isOnline) {
        await createMileage({ variables: { input: { vehicleId: selectedVehicleId, mileage: mileageValue, date: new Date().toISOString().split('T')[0], notes: mileageNotes } } });
      } else {
        await saveOfflineEntry('mileage', selectedVehicleId, {
          mileage: mileageValue,
          date: new Date().toISOString().split('T')[0],
          notes: mileageNotes,
        });
      }
      setShowMileageForm(false);
      setMileageValue(0);
      setMileageNotes('');
    } catch (e) { console.error(e); }
  };

  const handleFuelSave = async () => {
    if (!selectedVehicleId || !fuelLiters || !fuelPrice) return;
    try {
      if (isOnline) {
        await createFuel({ variables: { input: { vehicleId: selectedVehicleId, liters: fuelLiters, price: fuelPrice, fuelType, total: fuelLiters * fuelPrice, date: new Date().toISOString().split('T')[0], notes: fuelNotes, mileage: 0 } } });
      } else {
        await saveOfflineEntry('fuel', selectedVehicleId, {
          liters: fuelLiters,
          price: fuelPrice,
          fuelType,
          total: fuelLiters * fuelPrice,
          date: new Date().toISOString().split('T')[0],
          notes: fuelNotes,
          mileage: 0,
        });
      }
      setShowFuelForm(false);
      setFuelLiters(0);
      setFuelPrice(0);
      setFuelNotes('');
    } catch (e) { console.error(e); }
  };

  const handleChecklistToggle = (idx: number) => {
    setCheckedItems(prev => ({ ...prev, [idx]: !prev[idx] }));
    if (activeStep < CHECKLIST_ITEMS.length - 1 && checkedItems[idx]) {
      setActiveStep(prev => Math.min(prev + 1, CHECKLIST_ITEMS.length - 1));
    }
  };

  const handleChecklistComplete = () => {
    setShowChecklist(false);
    setCheckedItems({});
    setActiveStep(0);
  };

  if (!isDriverMode) {
    return null;
  }

  if (vehiclesLoading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
  }

  return (
    <Box sx={{ width: '100%', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>Шофьорски режим</Typography>
        <Button variant="outlined" startIcon={<ChecklistIcon />} onClick={() => setShowChecklist(true)}>
          Предпътна проверка
        </Button>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {vehicles.filter((v: { status: string }) => v.status === 'active').map((v: { id: number; registrationNumber: string; make: string; model: string; year: number; fuelType: string; color: string }) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={v.id}>
            <Card
              sx={{
                cursor: 'pointer',
                border: selectedVehicleId === v.id ? 2 : 0,
                borderColor: 'primary.main',
                bgcolor: selectedVehicleId === v.id ? 'action.selected' : 'background.paper',
              }}
              onClick={() => setSelectedVehicleId(v.id)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <CarIcon color="primary" />
                  <Typography variant="h6">{v.registrationNumber}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {v.make} {v.model} ({v.year})
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Chip label={v.fuelType} size="small" />
                  {v.color && <Chip label={v.color} size="small" />}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {selectedVehicleId && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Бързи действия</Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button variant="contained" startIcon={<SpeedIcon />} onClick={() => setShowMileageForm(true)}>
              Въведи километраж
            </Button>
            <Button variant="contained" color="secondary" startIcon={<FuelIcon />} onClick={() => setShowFuelForm(true)}>
              Въведи гориво
            </Button>
          </Box>
        </Paper>
      )}

      <Dialog open={showMileageForm} onClose={() => setShowMileageForm(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Въведи километраж</DialogTitle>
        <DialogContent>
          <TextField margin="dense" label="Километри" type="number" fullWidth value={mileageValue} onChange={e => setMileageValue(parseFloat(e.target.value) || 0)} />
          <TextField margin="dense" label="Бележки" fullWidth value={mileageNotes} onChange={e => setMileageNotes(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowMileageForm(false)}>Отказ</Button>
          <Button onClick={handleMileageSave} variant="contained" disabled={!mileageValue || savingMileage}>Запази</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={showFuelForm} onClose={() => setShowFuelForm(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Въведи гориво</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 6 }}>
              <TextField margin="dense" label="Литри" type="number" fullWidth value={fuelLiters} onChange={e => setFuelLiters(parseFloat(e.target.value) || 0)} />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField margin="dense" label="Цена за литър" type="number" fullWidth value={fuelPrice} onChange={e => setFuelPrice(parseFloat(e.target.value) || 0)} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth margin="dense">
                <InputLabel>Тип гориво</InputLabel>
                <Select value={fuelType} onChange={e => setFuelType(e.target.value)} label="Тип гориво">
                  <MenuItem value="dizel">Дизел</MenuItem>
                  <MenuItem value="gasoline">Бензин</MenuItem>
                  <MenuItem value="lpg">Газ</MenuItem>
                  <MenuItem value="electric">Електричество</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField margin="dense" label="Бележки" fullWidth multiline rows={2} value={fuelNotes} onChange={e => setFuelNotes(e.target.value)} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFuelForm(false)}>Отказ</Button>
          <Button onClick={handleFuelSave} variant="contained" disabled={!fuelLiters || !fuelPrice || savingFuel}>Запази</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={showChecklist} onClose={() => setShowChecklist(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Предпътна проверка</DialogTitle>
        <DialogContent>
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
            {CHECKLIST_ITEMS.map((_, i) => (
              <Step key={i} completed={!!checkedItems[i]}>
                <StepLabel />
              </Step>
            ))}
          </Stepper>
          <Typography variant="h6" gutterBottom>{CHECKLIST_ITEMS[activeStep]}</Typography>
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Button variant="contained" color="success" onClick={() => handleChecklistToggle(activeStep)} sx={{ mr: 1 }}>
              {checkedItems[activeStep] ? 'Отметни' : 'Проверено'}
            </Button>
            {activeStep < CHECKLIST_ITEMS.length - 1 && (
              <Button onClick={() => setActiveStep(prev => Math.min(prev + 1, CHECKLIST_ITEMS.length - 1))}>
                  Пропусни
              </Button>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setShowChecklist(false); setCheckedItems({}); setActiveStep(0); }}>Затвори</Button>
          {Object.keys(checkedItems).length === CHECKLIST_ITEMS.length && (
            <Button onClick={handleChecklistComplete} variant="contained" color="success">Завърши проверката</Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DriverDashboard;
