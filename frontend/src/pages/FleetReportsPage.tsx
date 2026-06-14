import React, { useState, useMemo } from 'react';
import { useQuery, gql } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../currencyContext';
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
  InputAdornment,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  DirectionsCar as CarIcon,
  LocalGasStation as FuelIcon,
  Build as RepairIcon,
  Security as InsuranceIcon,
  Assessment as ChartIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { InfoIcon } from '../components/ui/InfoIcon';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface ReportData {
  id: string;
  vehicle: string;
  vehicleId: number;
  date: string;
  type: string;
  amount: number;
  details: string;
}

const GET_ALL_VEHICLES = gql`
  query GetAllVehicles {
    vehicles {
      vehicles {
        id
        registrationNumber
        make
        model
      }
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

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const FleetReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const { currency } = useCurrency();
  const [reportType, setReportType] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [vehicleFilter, setVehicleFilter] = useState('');

  const inspectionResultLabels: Record<string, string> = {
    passed: 'Минал',
    failed: 'Не минал',
    pending: 'В изчакване',
  };

  const insuranceTypeLabels: Record<string, string> = {
    civil: 'Гражданска отговорност',
    kasko: 'Автокаско',
    border: 'Гранична застраховка',
  };

  const { data: vehiclesData, loading: vehiclesLoading } = useQuery(GET_ALL_VEHICLES);
  const vehicles = vehiclesData?.vehicles?.vehicles || [];

  const { data: fuelData, loading: fuelLoading } = useQuery(GET_VEHICLE_FUEL, {
    variables: { vehicleId: vehicleFilter ? parseInt(vehicleFilter) : vehicles[0]?.id || 1 },
    skip: !vehicles.length,
  });

  const { data: repairsData, loading: repairsLoading } = useQuery(GET_VEHICLE_REPAIRS, {
    variables: { vehicleId: vehicleFilter ? parseInt(vehicleFilter) : vehicles[0]?.id || 1 },
    skip: !vehicles.length,
  });

  const { data: insurancesData, loading: insurancesLoading } = useQuery(GET_VEHICLE_INSURANCES, {
    variables: { vehicleId: vehicleFilter ? parseInt(vehicleFilter) : vehicles[0]?.id || 1 },
    skip: !vehicles.length,
  });

  const { data: inspectionsData, loading: inspectionsLoading } = useQuery(GET_VEHICLE_INSPECTIONS, {
    variables: { vehicleId: vehicleFilter ? parseInt(vehicleFilter) : vehicles[0]?.id || 1 },
    skip: !vehicles.length,
  });

  const loading = vehiclesLoading || fuelLoading || repairsLoading || insurancesLoading || inspectionsLoading;

  const reportData = useMemo(() => {
    const data: ReportData[] = [];
    const vehicleId = vehicleFilter ? parseInt(vehicleFilter) : null;
    const selectedVehicles = vehicleId ? vehicles.filter((v: any) => v.id === vehicleId) : vehicles;

    selectedVehicles.forEach((vehicle: any) => {
      const vehicleLabel = `${vehicle.registrationNumber} - ${vehicle.make} ${vehicle.model}`;

      if (reportType === 'all' || reportType === 'fuel') {
        (fuelData?.vehicleFuelLogs || []).forEach((log: any) => {
          data.push({
            id: `fuel-${log.id}`,
            vehicle: vehicleLabel,
            vehicleId: vehicle.id,
            date: log.date,
            type: 'Гориво',
            amount: parseFloat(log.total) || 0,
            details: `${log.liters} л @ ${log.price} лв/л`,
          });
        });
      }

      if (reportType === 'all' || reportType === 'repairs') {
        (repairsData?.vehicleRepairs || []).forEach((repair: any) => {
          data.push({
            id: `repair-${repair.id}`,
            vehicle: vehicleLabel,
            vehicleId: vehicle.id,
            date: repair.date,
            type: 'Ремонт',
            amount: parseFloat(repair.cost) || 0,
            details: repair.description,
          });
        });
      }

      if (reportType === 'all' || reportType === 'insurance') {
        (insurancesData?.vehicleInsurances || []).forEach((ins: any) => {
          data.push({
            id: `insurance-${ins.id}`,
            vehicle: vehicleLabel,
            vehicleId: vehicle.id,
            date: ins.startDate,
            type: 'Застраховка',
            amount: parseFloat(ins.premium) || 0,
            details: `${insuranceTypeLabels[ins.insuranceType] || ins.insuranceType} - ${ins.provider}`,
          });
        });
      }

      if (reportType === 'all' || reportType === 'inspections') {
        (inspectionsData?.vehicleInspections || []).forEach((insp: any) => {
          data.push({
            id: `inspection-${insp.id}`,
            vehicle: vehicleLabel,
            vehicleId: vehicle.id,
            date: insp.date,
            type: 'ГТП',
            amount: parseFloat(insp.cost) || 0,
            details: `Резултат: ${inspectionResultLabels[insp.result] || insp.result}`,
          });
        });
      }
    });

    return data
      .filter((item) => {
        if (dateFrom && item.date < dateFrom) return false;
        if (dateTo && item.date > dateTo) return false;
        return true;
      })
      .sort((a, b) => b.date.localeCompare(a.date));
  }, [vehicles, fuelData, repairsData, insurancesData, inspectionsData, reportType, dateFrom, dateTo, vehicleFilter]);

  const totalAmount = reportData.reduce((sum, item) => sum + item.amount, 0);
  const uniqueVehicles = new Set(reportData.map((item) => item.vehicleId)).size;

  const chartData = useMemo(() => {
    const byType: Record<string, number> = {};
    reportData.forEach((item) => {
      byType[item.type] = (byType[item.type] || 0) + item.amount;
    });
    return Object.entries(byType).map(([name, value]) => ({ name, value }));
  }, [reportData]);

  const monthlyData = useMemo(() => {
    const byMonth: Record<string, number> = {};
    reportData.forEach((item) => {
      const month = item.date.substring(0, 7);
      byMonth[month] = (byMonth[month] || 0) + item.amount;
    });
    return Object.entries(byMonth)
      .map(([month, amount]) => ({ month, amount }))
      .sort((a, b) => a.month.localeCompare(b.month));
  }, [reportData]);

  const handleExport = (format: 'csv' | 'excel' | 'pdf') => {
    if (format === 'csv') {
      const headers = ['Автомобил', 'Дата', 'Тип', 'Детайли', 'Сума'];
      const rows = reportData.map((row) => [
        row.vehicle,
        row.date,
        row.type,
        row.details,
        row.amount.toFixed(2),
      ]);
      const csv = [headers, ...rows].map((r) => r.join(',')).join('\n');
      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `fleet-report-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
    } else {
      alert(`Експорт в ${format.toUpperCase()} - ${reportData.length} записа (в разработка)`);
    }
  };

  const setQuickFilter = (days: number) => {
    const to = new Date();
    const from = new Date();
    from.setDate(from.getDate() - days);
    setDateFrom(from.toISOString().split('T')[0]);
    setDateTo(to.toISOString().split('T')[0]);
  };

  const reportTypes = [
    { value: 'all', label: 'Всички разходи', icon: <ChartIcon /> },
    { value: 'fuel', label: 'Разходи за гориво', icon: <FuelIcon /> },
    { value: 'repairs', label: 'Ремонти и поддръжка', icon: <RepairIcon /> },
    { value: 'insurance', label: 'Застраховки', icon: <InsuranceIcon /> },
    { value: 'inspections', label: 'ГТП прегледи', icon: <CarIcon /> },
  ];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

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
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {type.icon}
                      {type.label}
                    </Box>
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
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoIcon helpText="Начална дата за справката" />
                    </InputAdornment>
                  )
                }
              }}
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
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoIcon helpText="Крайна дата за справката" />
                    </InputAdornment>
                  )
                }
              }}
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
                {vehicles.map((vehicle: any) => (
                  <MenuItem key={vehicle.id} value={vehicle.id}>
                    {vehicle.registrationNumber} - {vehicle.make} {vehicle.model}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Button variant="contained" fullWidth onClick={() => setReportType(reportType)}>
              Търси
            </Button>
          </Grid>
        </Grid>

        {/* Quick Filters */}
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Chip label="Последните 7 дни" onClick={() => setQuickFilter(7)} clickable />
          <Chip label="Последните 30 дни" onClick={() => setQuickFilter(30)} clickable />
          <Chip label="Последните 90 дни" onClick={() => setQuickFilter(90)} clickable />
          <Chip label="Тази година" onClick={() => {
            const year = new Date().getFullYear();
            setDateFrom(`${year}-01-01`);
            setDateTo(`${year}-12-31`);
          }} clickable />
          {(dateFrom || dateTo) && (
            <Chip label="Изчисти" onClick={() => { setDateFrom(''); setDateTo(''); }} color="error" />
          )}
        </Box>
      </Paper>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Общо записи</Typography>
              <Typography variant="h4">{reportData.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Обща сума</Typography>
              <Typography variant="h4" color="primary.main">{formatCurrencyValue(totalAmount, currency)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Автомобили</Typography>
              <Typography variant="h4">{uniqueVehicles}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      {reportData.length > 0 && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Разходи по тип</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => formatCurrencyValue(value, currency)} />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Месечни разходи</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => formatCurrencyValue(value, currency)} />
                  <Legend />
                  <Bar dataKey="amount" fill="#8884d8" name="Сума" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Export Buttons */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('csv')}
        >
          CSV
        </Button>
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
            {reportData.map((row) => (
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
                      row.type === 'Застраховка' ? 'info' :
                      row.type === 'ГТП' ? 'success' : 'default'
                    } 
                  />
                </TableCell>
                <TableCell>{row.details}</TableCell>
                <TableCell align="right">{formatCurrencyValue(row.amount, currency)}</TableCell>
              </TableRow>
            ))}
            {reportData.length > 0 && (
              <TableRow sx={{ fontWeight: 'bold', backgroundColor: 'action.hover' }}>
                <TableCell colSpan={4} align="right"><strong>Общо:</strong></TableCell>
                <TableCell align="right"><strong>{formatCurrencyValue(totalAmount, currency)}</strong></TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {reportData.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Няма данни за избрания период
        </Alert>
      )}
    </Box>
  );
};

export default FleetReportsPage;
