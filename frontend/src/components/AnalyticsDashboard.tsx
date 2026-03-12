import React from 'react';
import { useQuery, gql } from '@apollo/client';
import { 
  Box, Typography, Grid, Card, CardContent, CircularProgress, Alert 
} from '@mui/material';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  LineChart, Line
} from 'recharts';
import { useCurrency } from '../currencyContext';

const GET_STATS = gql`
  query GetManagementStats {
    managementStats {
      overtimeByMonth {
        month
        amount
      }
      latenessByUser {
        userName
        count
      }
    }
  }
`;

const AnalyticsDashboard: React.FC = () => {
    const { data, loading, error } = useQuery(GET_STATS, { fetchPolicy: 'network-only' });
    const { currency } = useCurrency();

    if (loading) return <CircularProgress />;
    if (error) return <Alert severity="error">{error.message}</Alert>;

    const otData = data?.managementStats.overtimeByMonth || [];
    const lateData = data?.managementStats.latenessByUser || [];

    return (
        <Box sx={{ mt: 2 }}>
            <Grid container spacing={3}>
                {/* Overtime Cost Chart */}
                <Grid size={{ xs: 12, md: 7 }}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h6" gutterBottom fontWeight="bold">
                                Разходи за извънреден труд ({currency})
                            </Typography>
                            <Box sx={{ width: '100%', height: 300, minWidth: 0 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={otData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="month" />
                                        <YAxis />
                                        <Tooltip />
                                        <Line type="monotone" dataKey="amount" stroke="#f44336" strokeWidth={3} name="Сума" />
                                    </LineChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Lateness Leaderboard */}
                <Grid size={{ xs: 12, md: 5 }}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h6" gutterBottom fontWeight="bold">
                                Топ 10 закъснения (последни 30 дни)
                            </Typography>
                            <Box sx={{ width: '100%', height: 300, minWidth: 0 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={lateData} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis type="number" />
                                        <YAxis dataKey="userName" type="category" width={120} />
                                        <Tooltip />
                                        <Bar dataKey="count" fill="#ff9800" name="Брой закъснения" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default AnalyticsDashboard;