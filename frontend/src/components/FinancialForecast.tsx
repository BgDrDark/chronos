import React, { useState } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, TextField, MenuItem, 
  CircularProgress, Alert 
} from '@mui/material';
import { useQuery, gql } from '@apollo/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import { useCurrency } from '../currencyContext';

const GET_FORECAST = gql`
  query GetForecast($year: Int!, $month: Int!) {
    payrollForecast(year: $year, month: $month) {
      totalAmount
      byDepartment {
        departmentName
        amount
      }
    }
  }
`;

const FinancialForecast: React.FC = () => {
    const today = new Date();
    const [year, setYear] = useState(today.getFullYear());
    const [month, setMonth] = useState(today.getMonth() + 1);
    const { currency } = useCurrency();

    const { data, loading, error } = useQuery(GET_FORECAST, {
        variables: { year, month },
        fetchPolicy: "network-only" // Always fresh
    });

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('bg-BG', { style: 'currency', currency: currency }).format(val);
    };

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

    return (
        <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUpIcon color="primary" />
                    Финансова Прогноза
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField 
                        select size="small" label="Година"
                        value={year} onChange={e => setYear(Number(e.target.value))}
                        sx={{ width: 100 }}
                    >
                        {[2024, 2025, 2026, 2027].map(y => <MenuItem key={y} value={y}>{y}</MenuItem>)}
                    </TextField>
                    <TextField 
                        select size="small" label="Месец"
                        value={month} onChange={e => setMonth(Number(e.target.value))}
                        sx={{ width: 120 }}
                    >
                        {Array.from({length: 12}, (_, i) => i + 1).map(m => (
                            <MenuItem key={m} value={m}>{new Date(2000, m-1, 1).toLocaleDateString('bg-BG', { month: 'long' })}</MenuItem>
                        ))}
                    </TextField>
                </Box>
            </Box>

            {loading && <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>}
            {error && <Alert severity="error">Грешка при зареждане: {error.message}</Alert>}

            {data && (
                <Grid container spacing={3}>
                    {/* TOTAL CARD */}
                    <Grid size={{ xs: 12, md: 4 }}>
                        <Card sx={{ height: '100%', bgcolor: 'primary.dark', color: 'white', borderRadius: 3 }}>
                            <CardContent sx={{ textAlign: 'center', py: 4 }}>
                                <AccountBalanceWalletIcon sx={{ fontSize: 60, opacity: 0.8 }} />
                                <Typography variant="h6" sx={{ mt: 2, opacity: 0.9 }}>
                                    Прогнозни Разходи (Нетно)
                                </Typography>
                                <Typography variant="h3" fontWeight="bold">
                                    {formatCurrency(data.payrollForecast.totalAmount)}
                                </Typography>
                                <Typography variant="caption" sx={{ opacity: 0.7, mt: 1, display: 'block' }}>
                                    Включва реално отработено до момента + планирани смени до края на месеца.
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* CHART */}
                    <Grid size={{ xs: 12, md: 8 }}>
                        <Card sx={{ height: '100%', borderRadius: 3 }}>
                            <CardContent>
                                <Typography variant="subtitle1" gutterBottom fontWeight="bold">Разбивка по Отдели</Typography>
                                <Box sx={{ height: 300, width: '100%', minWidth: 0 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={data.payrollForecast.byDepartment}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                            <XAxis dataKey="departmentName" />
                                            <YAxis />
                                            <Tooltip formatter={(value: any) => formatCurrency(Number(value))} />
                                            <Bar dataKey="amount" fill="#3f51b5" radius={[4, 4, 0, 0]}>
                                                {data.payrollForecast.byDepartment.map((_: any, index: number) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}
        </Box>
    );
};

export default FinancialForecast;
