import React, { useState } from 'react';
import {
  Box,
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
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  DateRange as DateIcon,
  DirectionsCar as CarIcon,
  LocalGasStation as FuelIcon,
  Build as RepairIcon,
  Security as InsuranceIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface ReportData {
  id: string;
  vehicle: string;
  date: string;
  type: string;
  amount: number;
  details: string;
}

const FleetReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [reportType, setReportType] = useState('expenses');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [vehicleFilter, setVehicleFilter] = useState('');

  const mockData: ReportData[] = [
    { id: '1', vehicle: 'E1234AB', date: '2026-03-05', type: 'Гориво', amount: 150, details: 'Зареждане - 50 л' },
    { id: '2', vehicle: 'E1234AB', date: '2026-03-01', type: 'Ремонт', amount: 300, details: 'Смяна на гуми' },
    { id: '3', vehicle: 'CA5678CC', date: '2026-02-28', type: 'Застраховка', amount: 450, details: 'Гражданска отговорност' },
    { id: '4', vehicle: 'E1234AB', date: '2026-02-20', type: 'Гориво', amount: 120, details: 'Зареждане - 40 л' },
    { id: '5', vehicle: 'CA5678CC', date: '2026-02-15', type: 'ГТП', amount: 100, details: 'Годишен преглед' },
  ];

  const totalAmount = mockData.reduce((sum, item) => sum + item.amount, 0);

  const handleExport = (format: 'excel' | 'pdf' | 'csv') => {
    alert(`Експорт в ${format.toUpperCase()} - ${mockData.length} записа`);
  };

  const reportTypes = [
    { value: 'expenses', label: 'Разходи по автомобили', icon: <CarIcon /> },
    { value: 'fuel', label: 'Разходи за гориво', icon: <FuelIcon /> },
    { value: 'repairs', label: 'Ремонти и поддръжка', icon: <RepairIcon /> },
    { value: 'insurance', label: 'Застраховки', icon: <InsuranceIcon /> },
    { value: 'mileage', label: 'Километраж', icon: <CarIcon /> },
  ];

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/admin/fleet')}>
          Назад
        </Button>
        <Typography variant="h5" component="div" sx={{ fontWeight: 'bold' }}>
          Справки - Автомобили
        </Typography>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Тип справка</InputLabel>
              <Select
                value={reportType}
                label="Тип справка"
                onChange={(e) => setReportType(e.target.value)}
              >
                {reportTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <TextField
              label="От дата"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <TextField
              label="До дата"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Автомобил</InputLabel>
              <Select
                value={vehicleFilter}
                label="Автомобил"
                onChange={(e) => setVehicleFilter(e.target.value)}
              >
                <MenuItem value="">Всички</MenuItem>
                <MenuItem value="E1234AB">E1234AB - Toyota Corolla</MenuItem>
                <MenuItem value="CA5678CC">CA5678CC - VW Passat</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Button variant="contained" fullWidth>
              Търси
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Общо записи</Typography>
              <Typography variant="h4">{mockData.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Обща сума</Typography>
              <Typography variant="h4" color="primary.main">{totalAmount} лв</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Автомобили</Typography>
              <Typography variant="h4">2</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Export Buttons */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('excel')}
        >
          Excel
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('pdf')}
        >
          PDF
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('csv')}
        >
          CSV
        </Button>
        <Button
          variant="outlined"
          startIcon={<PrintIcon />}
          onClick={() => window.print()}
        >
          Печат
        </Button>
      </Box>

      {/* Report Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Автомобил</TableCell>
              <TableCell>Дата</TableCell>
              <TableCell>Тип</TableCell>
              <TableCell>Детайли</TableCell>
              <TableCell align="right">Сума</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockData.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.vehicle}</TableCell>
                <TableCell>{row.date}</TableCell>
                <TableCell>
                  <Chip 
                    label={row.type} 
                    size="small" 
                    color={
                      row.type === 'Гориво' ? 'primary' :
                      row.type === 'Ремонт' ? 'warning' :
                      row.type === 'Застраховка' ? 'info' : 'default'
                    } 
                  />
                </TableCell>
                <TableCell>{row.details}</TableCell>
                <TableCell align="right">{row.amount} лв</TableCell>
              </TableRow>
            ))}
            <TableRow sx={{ fontWeight: 'bold' }}>
              <TableCell colSpan={4} align="right">Общо:</TableCell>
              <TableCell align="right">{totalAmount} лв</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      {mockData.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Няма данни за избрания период
        </Alert>
      )}
    </Box>
  );
};

export default FleetReportsPage;
