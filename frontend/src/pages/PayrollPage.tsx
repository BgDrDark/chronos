import React, { useState } from 'react';
import {
  Container, Typography, Box, TextField, Button, MenuItem,
  Alert, CircularProgress, Card, CardContent, Divider, Grid, Link, FormControlLabel, Checkbox,
  Tooltip, Switch, type SelectChangeEvent
} from '@mui/material';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import PaidIcon from '@mui/icons-material/Paid';
import ReceiptIcon from '@mui/icons-material/Receipt';
import AddIcon from '@mui/icons-material/Add';
import AssessmentIcon from '@mui/icons-material/Assessment';
// @ts-expect-error Apollo types conflict with local interfaces
import { useQuery, useMutation, gql, useLazyQuery } from '@apollo/client';
import { useForm, Controller } from 'react-hook-form';
import { useCurrency } from '../currencyContext';
import { 
  type PayrollLegalSettings, 
  type UserWithPayroll, 
  type PositionWithPayroll, 
  type PayrollSummaryItem, 
  type PayrollConfig,
  type Bonus,
  type User,
  type Position
} from '../types';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import SecurityIcon from '@mui/icons-material/Security';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloudSyncIcon from '@mui/icons-material/CloudSync';

// --- GraphQL Queries & Mutations ---
const GET_PAYROLL_LEGAL_SETTINGS = gql`
  query GetPayrollLegal {
    payrollLegalSettings {
      maxInsuranceBase
      employeeInsuranceRate
      incomeTaxRate
      civilContractCostsRate
      noiCompensationPercent
      employerPaidSickDays
      defaultTaxResident
    }
  }
`;

const GET_PAYROLL_SUMMARY = gql`
  query GetPayrollSummary($startDate: Date!, $endDate: Date!, $userIds: [Int!]) {
    payrollSummary(startDate: $startDate, endDate: $endDate, userIds: $userIds) {
      userId
      email
      fullName
      grossAmount
      netAmount
      taxAmount
      insuranceAmount
      bonusAmount
      advances
      loanDeductions
      totalDeductions
      netPayable
      contractType
      installments {
        count
        amountPerInstallment
      }
    }
  }
`;

const UPDATE_PAYROLL_LEGAL_MUTATION = gql`
  mutation UpdatePayrollLegal($maxInsuranceBase: Float!, $employeeInsuranceRate: Float!, $incomeTaxRate: Float!, $civilContractCostsRate: Float!, $noiCompensationPercent: Float!, $employerPaidSickDays: Int!, $defaultTaxResident: Boolean!) {
    updatePayrollLegalSettings(maxInsuranceBase: $maxInsuranceBase, employeeInsuranceRate: $employeeInsuranceRate, incomeTaxRate: $incomeTaxRate, civilContractCostsRate: $civilContractCostsRate, noiCompensationPercent: $noiCompensationPercent, employerPaidSickDays: $employerPaidSickDays, defaultTaxResident: $defaultTaxResident) {
      maxInsuranceBase
      employeeInsuranceRate
      incomeTaxRate
      civilContractCostsRate
      noiCompensationPercent
      employerPaidSickDays
      defaultTaxResident
    }
  }
`;

const GET_DATA_QUERY = gql`
  query GetData {
    users(limit: 100) {
      users { 
        id email firstName lastName 
        position { title }
        payrolls { 
            hourlyRate monthlySalary currency annualLeaveDays overtimeMultiplier standardHoursPerDay
            taxPercent healthInsurancePercent hasTaxDeduction hasHealthInsurance
        }
      }
    }
    positions { 
      id title 
      payrolls { 
          hourlyRate monthlySalary currency annualLeaveDays overtimeMultiplier standardHoursPerDay 
          taxPercent healthInsurancePercent hasTaxDeduction hasHealthInsurance
      }
    }
  }
`;

const GET_GLOBAL_CONFIG_QUERY = gql`
  query GetGlobalConfig {
    globalPayrollConfig {
      hourlyRate
      monthlySalary
      currency
      annualLeaveDays
      overtimeMultiplier
      standardHoursPerDay
      taxPercent
      healthInsurancePercent
      hasTaxDeduction
      hasHealthInsurance
    }
  }
`;

const UPDATE_USER_PAYROLL_MUTATION = gql`
  mutation UpdateUserPayroll($userId: Int!, $hourlyRate: Decimal!, $overtimeMultiplier: Decimal!, $standardHoursPerDay: Int!, $monthlySalary: Decimal, $annualLeaveDays: Int, $currency: String, $taxPercent: Decimal, $healthInsurancePercent: Decimal, $hasTaxDeduction: Boolean, $hasHealthInsurance: Boolean) {
    updateUserPayroll(userId: $userId, hourlyRate: $hourlyRate, overtimeMultiplier: $overtimeMultiplier, standardHoursPerDay: $standardHoursPerDay, monthlySalary: $monthlySalary, annualLeaveDays: $annualLeaveDays, currency: $currency, taxPercent: $taxPercent, healthInsurancePercent: $healthInsurancePercent, hasTaxDeduction: $hasTaxDeduction, hasHealthInsurance: $hasHealthInsurance) {
      id
    }
  }
`;

const UPDATE_POSITION_PAYROLL_MUTATION = gql`
  mutation UpdatePositionPayroll($positionId: Int!, $hourlyRate: Decimal!, $overtimeMultiplier: Decimal!, $standardHoursPerDay: Int!, $monthlySalary: Decimal, $annualLeaveDays: Int, $currency: String, $taxPercent: Decimal, $healthInsurancePercent: Decimal, $hasTaxDeduction: Boolean, $hasHealthInsurance: Boolean) {
    updatePositionPayroll(positionId: $positionId, hourlyRate: $hourlyRate, overtimeMultiplier: $overtimeMultiplier, standardHoursPerDay: $standardHoursPerDay, monthlySalary: $monthlySalary, annualLeaveDays: $annualLeaveDays, currency: $currency, taxPercent: $taxPercent, healthInsurancePercent: $healthInsurancePercent, hasTaxDeduction: $hasTaxDeduction, hasHealthInsurance: $hasHealthInsurance) {
      id
    }
  }
`;

const UPDATE_GLOBAL_CONFIG_MUTATION = gql`
  mutation UpdateGlobalPayrollConfig($hourlyRate: Decimal!, $overtimeMultiplier: Decimal!, $standardHoursPerDay: Int!, $monthlySalary: Decimal!, $annualLeaveDays: Int!, $currency: String!, $taxPercent: Decimal!, $healthInsurancePercent: Decimal!, $hasTaxDeduction: Boolean!, $hasHealthInsurance: Boolean!) {
    updateGlobalPayrollConfig(hourlyRate: $hourlyRate, overtimeMultiplier: $overtimeMultiplier, standard_hours_per_day: $standardHoursPerDay, monthlySalary: $monthlySalary, annualLeaveDays: $annualLeaveDays, currency: $currency, taxPercent: $taxPercent, healthInsurancePercent: $healthInsurancePercent, hasTaxDeduction: $hasTaxDeduction, hasHealthInsurance: $hasHealthInsurance) {
      hourlyRate
    }
  }
`;

const CREATE_ADVANCE_MUTATION = gql`
  mutation CreateAdvance($userId: Int!, $amount: Float!, $paymentDate: Date!, $description: String) {
    createAdvancePayment(userId: $userId, amount: $amount, paymentDate: $paymentDate, description: $description) {
      id
    }
  }
`;

const CREATE_LOAN_MUTATION = gql`
  mutation CreateLoan($userId: Int!, $totalAmount: Float!, $installmentsCount: Int!, $startDate: Date!, $description: String) {
    createServiceLoan(userId: $userId, totalAmount: $totalAmount, installmentsCount: $installmentsCount, startDate: $startDate, description: $description) {
      id
    }
  }
`;

const SET_MONTHLY_WORK_DAYS = gql`
  mutation SetMonthlyWorkDays($year: Int!, $month: Int!, $daysCount: Int!) {
    setMonthlyWorkDays(input: { year: $year, month: $month, daysCount: $daysCount }) {
      id
    }
  }
`;

const SYNC_HOLIDAYS_MUTATION = gql`
  mutation SyncHolidays($year: Int!) {
    syncHolidays(year: $year)
  }
`;

const SYNC_ORTHODOX_HOLIDAYS_MUTATION = gql`
  mutation SyncOrthodoxHolidays($year: Int!) {
    syncOrthodoxHolidays(year: $year)
  }
`;

const GENERATE_PAYSLIP_MUTATION = gql`
  mutation GeneratePayslip($userId: Int!, $startDate: Date!, $endDate: Date!) {
    generatePayslip(userId: $userId, startDate: $startDate, endDate: $endDate) {
      id
      periodStart
      periodEnd
      totalRegularHours
      totalOvertimeHours
      regularAmount
      overtimeAmount
      bonusAmount
      taxAmount
      insuranceAmount
      sickDays
      leaveDays
      totalAmount
      generatedAt
    }
  }
`;

const ADD_BONUS_MUTATION = gql`
  mutation AddBonus($userId: Int!, $amount: Float!, $date: Date!, $description: String) {
    addBonus(input: { userId: $userId, amount: $amount, date: $date, description: $description }) {
      id
      amount
      date
      description
    }
  }
`;

const REMOVE_BONUS_MUTATION = gql`
  mutation RemoveBonus($id: Int!) {
    removeBonus(id: $id)
  }
`;

const GET_USER_BONUSES = gql`
  query GetUserBonuses($userId: Int!) {
    user(id: $userId) {
      id
      bonuses {
        id
        amount
        date
        description
      }
    }
  }
`;

const GET_MONTHLY_WORK_DAYS = gql`
  query GetMonthlyWorkDays($year: Int!, $month: Int!) {
    monthlyWorkDays(year: $year, month: $month) {
      id
      daysCount
    }
  }
`;

// --- Component: Payroll Legal Settings ---
const PayrollLegalSettings: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_PAYROLL_LEGAL_SETTINGS);
    const [updateLegal, { loading: updating }] = useMutation(UPDATE_PAYROLL_LEGAL_MUTATION);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    const { control, handleSubmit, reset } = useForm({
        defaultValues: {
            maxInsuranceBase: 3750.0,
            employeeInsuranceRate: 13.78,
            incomeTaxRate: 10.0,
            civilContractCostsRate: 25.0,
            noiCompensationPercent: 80.0,
            employerPaidSickDays: 3,
            defaultTaxResident: true
        }
    });

    React.useEffect(() => {
        if (data?.payrollLegalSettings) {
            reset(data.payrollLegalSettings);
        }
    }, [data, reset]);

    const onSubmit = async (formData: PayrollLegalSettings) => {
        setMessage(null);
        try {
            await updateLegal({
                variables: {
                    maxInsuranceBase: parseFloat(formData.maxInsuranceBase),
                    employeeInsuranceRate: parseFloat(formData.employeeInsuranceRate),
                    incomeTaxRate: parseFloat(formData.incomeTaxRate),
                    civilContractCostsRate: parseFloat(formData.civilContractCostsRate),
                    noiCompensationPercent: parseFloat(formData.noiCompensationPercent),
                    employerPaidSickDays: parseInt(formData.employerPaidSickDays),
                    defaultTaxResident: formData.defaultTaxResident
                }
            });
            setMessage({ type: 'success', text: 'Законовите настройки са обновени успешно!' });
            refetch();
        } catch {
            setMessage({ type: 'error', text: (err instanceof Error ? _err.message : "Грешка") });
        }
    };

    if (loading) return <CircularProgress />;

    return (
        <Card variant="outlined" sx={{ mb: 3, border: '1px solid #d32f2f' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom color="error.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SecurityIcon color="error" /> Законови параметри и Прагове
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Тук се задават стойностите, определени от законодателството. Променяйте ги само при официални промени в законите!
                </Typography>
                <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                    <Grid container spacing={3}>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <Controller name="maxInsuranceBase" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Макс. осигурителен праг" type="number" size="small" helperText="лв. за месец" />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <Controller name="employeeInsuranceRate" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Лични осигуровки %" type="number" size="small" />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <Controller name="incomeTaxRate" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="ДОД %" type="number" size="small" />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <Controller name="civilContractCostsRate" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Признати разходи %" type="number" size="small" />
                            )} />
                        </Grid>
                        
                        {/* New Fields */}
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <Controller name="noiCompensationPercent" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Обезщетение НОЙ %" type="number" size="small" helperText="Обикновено 80%" />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <Controller name="employerPaidSickDays" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Дни от работодател" type="number" size="small" helperText="Първите X дни" />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <FormControlLabel
                                control={<Controller name="defaultTaxResident" control={control} render={({ field }) => <Checkbox {...field} checked={field.value} />} />}
                                label="Данъчен резидент (Default)"
                            />
                        </Grid>
                    </Grid>
                    {message && <Alert severity={message.type} sx={{ mt: 2 }}>{message.text}</Alert>}
                    <Button type="submit" variant="contained" color="error" sx={{ mt: 3 }} disabled={updating}>
                        Актуализирай Законови Параметри
                    </Button>
                </Box>
            </CardContent>
        </Card>
    );
};

// --- Component: Payroll Reports ---
const PayrollReports: React.FC = () => {
    const { data: usersData } = useQuery(GET_DATA_QUERY);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
    
    const [getSummary, { data, loading }] = useLazyQuery(GET_PAYROLL_SUMMARY);
    const [generatePayslip, { loading: generatingPdf }] = useMutation(GENERATE_PAYSLIP_MUTATION);
    const { currency } = useCurrency();

    const handleDownloadPdf = async (userId: number) => {
        try {
            const res = await generatePayslip({
                variables: {
                    userId,
                    startDate,
                    endDate
                }
            });
            const payslipId = res.data.generatePayslip.id;
            const token = localStorage.getItem('token');
            const pdfRes = await fetch(`${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/export/payslip/${payslipId}/pdf`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!pdfRes.ok) throw new Error('Failed to download');
            const blob = await pdfRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `payslip_${userId}_${startDate}.pdf`;
            a.click();
        } catch { alert("Грешка при генериране на PDF: " + e.message); }
    };

    const exportToXLSX = async () => {
        if (!startDate || !endDate) return;
        try {
            const token = localStorage.getItem('token');
            const url = `${import.meta.env.VITE_API_URL || 'https://dev.oblak24.org'}/export/payroll/xlsx?start_date=${startDate}&end_date=${endDate}`;
            const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!res.ok) throw new Error('Грешка при генериране');
            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `payroll_report_${startDate}_${endDate}.xlsx`;
            a.click();
        } catch { if (_err instanceof Error) if (_err instanceof Error) if (_err instanceof Error) alert(__err.message); }
    };

    const handleGenerate = () => {
        if (!startDate || !endDate) {
            alert("Моля, изберете период.");
            return;
        }
        getSummary({
            variables: {
                startDate,
                endDate,
                userIds: selectedUserIds.length > 0 ? selectedUserIds : null
            }
        });
    };

    const exportToCSV = () => {
        if (!data?.payrollSummary) return;
        
        const headers = ["Име", "Имейл", "Договор", "Бруто", "Осигуровки", "Данък", "Бонуси", "Удръжки", "НЕТО ЗА ПЛАЩАНЕ"];
        const rows = data.payrollSummary.map((item: PayrollSummaryItem) => [
            item.fullName,
            item.email,
            item.contractType,
            item.grossAmount.toFixed(2),
            item.insuranceAmount.toFixed(2),
            item.taxAmount.toFixed(2),
            item.bonusAmount.toFixed(2),
            item.totalDeductions.toFixed(2),
            item.netPayable.toFixed(2)
        ]);

        const csvContent = "\uFEFF" + [headers, ...rows].map(e => e.join(",")).join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `payroll_report_${startDate}_${endDate}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <Box sx={{ mt: 2 }}>
            <Card variant="outlined" sx={{ mb: 4, border: '1px solid #1976d2' }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AssessmentIcon color="primary" /> Справки и Експорт
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                        Генерирайте детайлни справки за заплати, данъци и осигуровки за избран период.
                    </Typography>
                    <Grid container spacing={2} alignItems="center">
                        <Grid size={{ xs: 12, sm: 3 }}>
                            <Tooltip title="Начална дата на периода за ведомостта" arrow>
                                <TextField fullWidth type="date" label="От" InputLabelProps={{ shrink: true }} value={startDate} onChange={e => setStartDate(e.target.value)} size="small" placeholder="2026-01-01" />
                            </Tooltip>
                        </Grid>
                        <Grid size={{ xs: 12, sm: 3 }}>
                            <Tooltip title="Крайна дата на периода за ведомостта" arrow>
                                <TextField fullWidth type="date" label="До" InputLabelProps={{ shrink: true }} value={endDate} onChange={e => setEndDate(e.target.value)} size="small" placeholder="2026-01-31" />
                            </Tooltip>
                        </Grid>
                        <Grid size={{ xs: 12, sm: 4 }}>
                            <Tooltip title="Избери конкретни служители или остави празно за всички" arrow>
                                <TextField 
                                    select fullWidth label="Служители (по избор)" 
                                    SelectProps={{ 
                                        multiple: true, 
                                        value: selectedUserIds, 
                                        onChange: (e: SelectChangeEvent<unknown>) => setSelectedUserIds(e.target.value as number[]) 
                                    }}
                                    size="small"
                                >
                                    {usersData?.users?.users.map((u: User) => (
                                        <MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>
                                    ))}
                                </TextField>
                            </Tooltip>
                        </Grid>
                        <Grid size={{ xs: 12, sm: 2 }}>
                            <Button variant="contained" fullWidth onClick={handleGenerate} disabled={loading}>Генерирай</Button>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>

            {loading && <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>}
            
            {data?.payrollSummary && (
                <Card sx={{ borderRadius: 2, boxShadow: 3 }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                            <Typography variant="h6" fontWeight="bold">Резултати за периода</Typography>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button startIcon={<FileDownloadIcon />} variant="outlined" color="success" onClick={exportToCSV}>
                                    CSV
                                </Button>
                                <Button startIcon={<FileDownloadIcon />} variant="contained" color="success" onClick={exportToXLSX}>
                                    XLSX (Excel)
                                </Button>
                            </Box>
                        </Box>
                        <Box sx={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ textAlign: 'left', borderBottom: '2px solid #1976d2', backgroundColor: 'rgba(25, 118, 210, 0.05)' }}>
                                        <th style={{ padding: '12px' }}>Служител</th>
                                        <th style={{ padding: '12px' }}>Бруто</th>
                                        <th style={{ padding: '12px' }}>Осигуровки</th>
                                        <th style={{ padding: '12px' }}>Данък</th>
                                        <th style={{ padding: '12px' }}>Бонуси</th>
                                        <th style={{ padding: '12px' }}>Нето</th>
                                        <th style={{ padding: '12px' }}>Действия</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.payrollSummary.map((item: PayrollSummaryItem) => (
                                        <tr key={item.userId} style={{ borderBottom: '1px solid #eee' }}>
                                            <td style={{ padding: '12px' }}>
                                                <Typography variant="body2" fontWeight="bold">{item.fullName}</Typography>
                                                <Typography variant="caption" color="text.secondary">{item.contractType}</Typography>
                                            </td>
                                            <td style={{ padding: '12px' }}>{item.grossAmount.toFixed(2)} {currency}</td>
                                            <td style={{ padding: '12px', color: '#d32f2f' }}>-{item.insuranceAmount.toFixed(2)}</td>
                                            <td style={{ padding: '12px', color: '#d32f2f' }}>-{item.taxAmount.toFixed(2)}</td>
                                            <td style={{ padding: '12px', color: '#2e7d32' }}>+{item.bonusAmount.toFixed(2)}</td>
                                            <td style={{ padding: '12px' }}>
                                                <Typography variant="body1" fontWeight="900" color="primary">
                                                    {item.netPayable.toFixed(2)} {currency}
                                                </Typography>
                                            </td>
                                            <td style={{ padding: '12px' }}>
                                                <Button 
                                                    size="small" 
                                                    variant="outlined" 
                                                    startIcon={<ReceiptIcon />}
                                                    onClick={() => handleDownloadPdf(item.userId)}
                                                    disabled={generatingPdf}
                                                >
                                                    Фиш (PDF)
                                                </Button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot style={{ backgroundColor: '#f5f5f5', fontWeight: 'bold' }}>
                                    <tr>
                                        <td style={{ padding: '12px' }}>ОБЩО:</td>
                                        <td style={{ padding: '12px' }}>{data.payrollSummary.reduce((a: number, b: PayrollSummaryItem) => a + b.grossAmount, 0).toFixed(2)}</td>
                                        <td style={{ padding: '12px', color: '#d32f2f' }}>-{data.payrollSummary.reduce((a: number, b: PayrollSummaryItem) => a + b.insuranceAmount, 0).toFixed(2)}</td>
                                        <td style={{ padding: '12px', color: '#d32f2f' }}>-{data.payrollSummary.reduce((a: number, b: PayrollSummaryItem) => a + b.taxAmount, 0).toFixed(2)}</td>
                                        <td style={{ padding: '12px', color: '#2e7d32' }}>+{data.payrollSummary.reduce((a: number, b: PayrollSummaryItem) => a + b.bonusAmount, 0).toFixed(2)}</td>
                                        <td style={{ padding: '12px', color: '#1976d2', fontSize: '1.1rem' }}>{data.payrollSummary.reduce((a: number, b: PayrollSummaryItem) => a + b.netPayable, 0).toFixed(2)} {currency}</td>
                                        <td style={{ padding: '12px' }}></td>
                                    </tr>
                                </tfoot>
                            </table>
                        </Box>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
};

// --- Component: Monthly Work Days Settings ---
const MonthlyWorkDaysSettings: React.FC = () => {
    const [setMonthlyWorkDays] = useMutation(SET_MONTHLY_WORK_DAYS);
    const [year, setYear] = useState(new Date().getFullYear());
    const [month, setMonth] = useState(new Date().getMonth() + 1);
    const [daysCount, setDaysCount] = useState<number>(22);
    const [message, setMessage] = useState<string | null>(null);

    const { data, refetch } = useQuery(GET_MONTHLY_WORK_DAYS, {
        variables: { year, month },
        fetchPolicy: 'network-only'
    });

    React.useEffect(() => {
        if (data?.monthlyWorkDays) {
            setDaysCount(data.monthlyWorkDays.daysCount);
        } else {
            setDaysCount(22); // Default fallback
        }
    }, [data]);

    const handleSave = async () => {
        try {
            await setMonthlyWorkDays({ variables: { year, month, daysCount } });
            setMessage('Запазено успешно!');
            refetch(); // Refetch to confirm save
            setTimeout(() => setMessage(null), 3000);
        } catch {
            if (_err instanceof Error) if (_err instanceof Error) if (_err instanceof Error) alert(__err.message);
        }
    };

    return (
        <Card variant="outlined">
            <CardContent>
                <Typography variant="h6" gutterBottom>Работни дни за месеца</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Задайте глобалния брой работни дни за всеки месец. Тази стойност се използва за изчисляване на надниците при месечна заплата. 
                    <Link href="https://kik-info.com/spravochnik/calendar/2026/" target="_blank" rel="noopener" sx={{ ml: 1, fontWeight: 'bold' }}>
                        Проверка на работно време (KIK-info)
                    </Link>
                </Typography>
                <Grid container spacing={2} alignItems="center">
                    <Grid size={{ xs: 12, sm: 3 }}>
                        <TextField fullWidth type="number" label="Година" size="small" value={year} onChange={(e) => setYear(parseInt(e.target.value))} />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 3 }}>
                        <TextField select fullWidth label="Месец" size="small" value={month} onChange={(e) => setMonth(parseInt(e.target.value as string))}>
                             {Array.from({ length: 12 }, (_, i) => (
                                <MenuItem key={i + 1} value={i + 1}>
                                {new Date(0, i).toLocaleString('bg-BG', { month: 'long' })}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 3 }}>
                        <TextField fullWidth type="number" label="Дни" size="small" value={daysCount} onChange={(e) => setDaysCount(parseInt(e.target.value))} />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 3 }}>
                        <Button variant="contained" fullWidth onClick={handleSave}>Запази</Button>
                    </Grid>
                </Grid>
                {message && <Typography color="success.main" sx={{ mt: 1 }}>{message}</Typography>}
            </CardContent>
        </Card>
    );
};

// --- Component: Global Payroll Settings ---
const GlobalPayrollSettings: React.FC = () => {
    const { data, loading } = useQuery(GET_GLOBAL_CONFIG_QUERY);
    const [updateConfig, { loading: updating }] = useMutation(UPDATE_GLOBAL_CONFIG_MUTATION);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
    const { refreshCurrency } = useCurrency();

    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;
    const { data: workDaysData } = useQuery(GET_MONTHLY_WORK_DAYS, {
      variables: { year: currentYear, month: currentMonth }
    });

    const { control, handleSubmit, reset, watch, setValue, getValues } = useForm({
        defaultValues: {
            hourlyRate: 0,
            monthlySalary: 0,
            currency: 'BGN',
            annualLeaveDays: 20,
            overtimeMultiplier: 1.5,
            standardHoursWeekly: 40,
            taxPercent: 10.0,
            healthInsurancePercent: 13.78,
            hasTaxDeduction: false, 
            hasHealthInsurance: false 
        }
    });

    const watchedSalary = watch('monthlySalary');
    const autoSaveTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

    React.useEffect(() => {
        const workDays = workDaysData?.monthlyWorkDays?.daysCount || 22;
        if (watchedSalary > 0) {
            const calculatedRate = (watchedSalary / workDays) / 8;
            const rate = parseFloat(calculatedRate.toFixed(4));
            setValue('hourlyRate', rate);

            if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
            setSaveStatus('saving');
            autoSaveTimer.current = setTimeout(async () => {
                try {
                    const vals = getValues();
                    await updateConfig({
                        variables: {
                            hourlyRate: rate.toString(),
                            monthlySalary: watchedSalary.toString(),
                            overtimeMultiplier: vals.overtimeMultiplier.toString(),
                            standardHoursPerDay: Math.round(vals.standardHoursWeekly / 5),
                            currency: vals.currency,
                            annualLeaveDays: parseInt(vals.annualLeaveDays.toString()),
                            taxPercent: vals.taxPercent.toString(),
                            healthInsurancePercent: vals.healthInsurancePercent.toString(),
                            hasTaxDeduction: vals.hasTaxDeduction,
                            hasHealthInsurance: vals.hasHealthInsurance
                        }
                    });
                    setSaveStatus('saved');
                    setTimeout(() => setSaveStatus('idle'), 3000);
                } catch (e) { 
                    console.error("Global auto-save failed", e); 
                    setSaveStatus('error');
                }
            }, 2000);
        }
    }, [watchedSalary, workDaysData, setValue, getValues, updateConfig]);

    React.useEffect(() => {
        if (data?.globalPayrollConfig) {
            const conf = data.globalPayrollConfig;
            reset({
                hourlyRate: conf.hourlyRate,
                monthlySalary: conf.monthlySalary,
                currency: conf.currency,
                annualLeaveDays: conf.annualLeaveDays,
                overtimeMultiplier: conf.overtimeMultiplier,
                standardHoursWeekly: conf.standardHoursPerDay * 5,
                taxPercent: conf.taxPercent,
                healthInsurancePercent: conf.healthInsurancePercent,
                hasTaxDeduction: conf.hasTaxDeduction,
                hasHealthInsurance: conf.hasHealthInsurance
            });
        }
    }, [data, reset]);

    const onSubmit = async (formData: PayrollLegalSettings) => {
        setMessage(null);
        try {
            await updateConfig({
                variables: {
                    hourlyRate: formData.hourlyRate.toString(),
                    monthlySalary: formData.monthlySalary.toString(),
                    overtimeMultiplier: formData.overtimeMultiplier.toString(),
                    standardHoursPerDay: Math.round(formData.standardHoursWeekly / 5),
                    currency: formData.currency,
                    annualLeaveDays: parseInt(formData.annualLeaveDays),
                    taxPercent: formData.taxPercent.toString(),
                    healthInsurancePercent: formData.healthInsurancePercent.toString(),
                    hasTaxDeduction: formData.hasTaxDeduction,
                    hasHealthInsurance: formData.hasHealthInsurance
                }
            });
            setMessage({ type: 'success', text: 'Глобалните настройки са обновени!' });
            refreshCurrency(); // Refresh global currency context
        } catch {
            setMessage({ type: 'error', text: (err instanceof Error ? _err.message : "Грешка") });
        }
    };

    if (loading) return <CircularProgress />;

    return (
        <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
                <Typography variant="h6" gutterBottom>Глобални параметри (По подразбиране)</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Тези настройки важат за всички служители, които нямат индивидуална конфигурация.
                </Typography>
                <Box component="form" onSubmit={handleSubmit(onSubmit)}>
                    <Grid container spacing={2}>
                        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                            <Controller name="hourlyRate" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Часова ставка" type="number" margin="normal" size="small" inputProps={{ step: "0.01" }} />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                            <Controller name="monthlySalary" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Месечна заплата" type="number" margin="normal" size="small" inputProps={{ step: "0.01" }} />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                            <Controller name="standardHoursWeekly" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Часове/седмица" type="number" margin="normal" size="small" />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                            <Controller name="currency" control={control} render={({ field }) => (
                                <TextField {...field} select fullWidth label="Валута" margin="normal" size="small">
                                    <MenuItem value="BGN">BGN</MenuItem>
                                    <MenuItem value="EUR">EUR</MenuItem>
                                    <MenuItem value="USD">USD</MenuItem>
                                </TextField>
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                            <Controller name="annualLeaveDays" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Отпуск (дни)" type="number" margin="normal" size="small" />
                            )} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                            <Controller name="overtimeMultiplier" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Коеф. Извънреден" type="number" margin="normal" size="small" inputProps={{ step: "0.1" }} />
                            )} />
                        </Grid>
                        
                        {/* Deductions Row */}
                        <Grid size={{ xs: 12 }}>
                            <Divider sx={{ my: 1 }}><Typography variant="caption">Удръжки (Данъци и Осигуровки)</Typography></Divider>
                        </Grid>
                        
                        <Grid size={{ xs: 6, md: 3 }}>
                            <FormControlLabel
                                control={<Controller name="hasTaxDeduction" control={control} render={({ field }) => <Checkbox {...field} checked={field.value} />} />}
                                label="ДДФЛ"
                            />
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                            <Controller name="taxPercent" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="ДДФЛ %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!watch('hasTaxDeduction')} />
                            )} />
                        </Grid>
                        
                        <Grid size={{ xs: 6, md: 3 }}>
                            <FormControlLabel
                                control={<Controller name="hasHealthInsurance" control={control} render={({ field }) => <Checkbox {...field} checked={field.value} />} />}
                                label="Осигуровки"
                            />
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                            <Controller name="healthInsurancePercent" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Осигуровки %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!watch('hasHealthInsurance')} />
                            )} />
                        </Grid>
                    </Grid>
                    {message && <Alert severity={message.type} sx={{ mt: 2 }}>{message.text}</Alert>}
                    
                    <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Button type="submit" variant="contained" disabled={updating}>Запази Глобалните Настройки</Button>
                        
                        {saveStatus === 'saving' && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'info.main' }}>
                                <CloudSyncIcon sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />
                                <Typography variant="caption">Записване...</Typography>
                            </Box>
                        )}
                        {saveStatus === 'saved' && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'success.main' }}>
                                <CheckCircleIcon fontSize="small" />
                                <Typography variant="caption">Глобалните промени са записани автоматично</Typography>
                            </Box>
                        )}
                        {saveStatus === 'error' && (
                            <Typography variant="caption" color="error">Грешка при автоматичен запис</Typography>
                        )}
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
};

// --- Component: Payroll Settings (User & Position) ---
const AdvanceLoanManager: React.FC = () => {
    const { data: usersData } = useQuery(GET_DATA_QUERY);
    const [createAdvance] = useMutation(CREATE_ADVANCE_MUTATION);
    const [createLoan] = useMutation(CREATE_LOAN_MUTATION);
    
    const [userId, setUserId] = useState<string>('');
    const [mode, setMode] = useState<'advance' | 'loan'>('advance');
    const [amount, setAmount] = useState<string>('');
    const [installments, setInstallments] = useState<string>('6');
    const [date, setDate] = useState<string>(new Date().toISOString().split('T')[0]);
    const [desc, setDesc] = useState<string>('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        if (!userId || !amount || !date) return;
        setLoading(true);
        try {
            if (mode === 'advance') {
                await createAdvance({
                    variables: {
                        userId: parseInt(userId),
                        amount: parseFloat(amount),
                        paymentDate: date,
                        description: desc
                    }
                });
            } else {
                await createLoan({
                    variables: {
                        userId: parseInt(userId),
                        totalAmount: parseFloat(amount),
                        installmentsCount: parseInt(installments),
                        startDate: date,
                        description: desc
                    }
                });
            }
            alert("Записано успешно!");
            setAmount('');
            setDesc('');
        } catch {
            alert("Грешка: " + e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card variant="outlined" sx={{ mb: 3, border: '1px solid #1976d2' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom color="primary">Управление на Аванси и Заеми</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Добавете еднократен аванс за текущия месец или дългосрочен заем, който ще се удържа автоматично на равни вноски.
                </Typography>
                <Grid container spacing={2} alignItems="flex-start">
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                            select fullWidth label="Служител" size="small"
                            value={userId} onChange={e => setUserId(e.target.value)}
                        >
                            {usersData?.users?.users.map((u: User) => (
                                <MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>
                            ))}
                        </TextField>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                            select fullWidth label="Тип" size="small"
                            value={mode} onChange={e => setMode(e.target.value as 'advance' | 'loan')}
                        >
                            <MenuItem value="advance">Еднократен аванс</MenuItem>
                            <MenuItem value="loan">Служебен аванс (на вноски)</MenuItem>
                        </TextField>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                            fullWidth label={mode === 'advance' ? "Сума" : "Обща сума на заема"} 
                            type="number" size="small"
                            value={amount} onChange={e => setAmount(e.target.value)}
                        />
                    </Grid>
                    {mode === 'loan' && (
                        <Grid size={{ xs: 12, sm: 4 }}>
                            <TextField
                                fullWidth label="Брой вноски (месеци)" 
                                type="number" size="small"
                                value={installments} onChange={e => setInstallments(e.target.value)}
                            />
                        </Grid>
                    )}
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                            fullWidth label="Начална дата" 
                            type="date" size="small" InputLabelProps={{ shrink: true }}
                            value={date} onChange={e => setDate(e.target.value)}
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                            fullWidth label="Коментар / Описание" 
                            size="small"
                            value={desc} onChange={e => setDesc(e.target.value)}
                        />
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                        <Button 
                            variant="contained" color="primary" 
                            onClick={handleSubmit} disabled={loading || !userId || !amount}
                        >
                            {loading ? 'Запис...' : 'Добави'}
                        </Button>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
};

const PayrollSettings: React.FC = () => {
  const { data, loading } = useQuery(GET_DATA_QUERY);
  const { data: globalData } = useQuery(GET_GLOBAL_CONFIG_QUERY); // Fetch globals to use as defaults
  const [mode, setMode] = useState<'user' | 'position'>('user');
  const { currency } = useCurrency(); // Get global currency
  
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;
  const { data: workDaysData } = useQuery(GET_MONTHLY_WORK_DAYS, {
    variables: { year: currentYear, month: currentMonth }
  });

  const [updateUserPayroll, { loading: updatingUser }] = useMutation(UPDATE_USER_PAYROLL_MUTATION, {
    refetchQueries: [{ query: GET_DATA_QUERY }]
  });
  const [updatePosPayroll, { loading: updatingPos }] = useMutation(UPDATE_POSITION_PAYROLL_MUTATION, {
    refetchQueries: [{ query: GET_DATA_QUERY }]
  });
  
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const { control, handleSubmit, reset, watch, setValue, getValues } = useForm({
    defaultValues: {
      targetId: '',
      hourlyRate: 0,
      monthlySalary: 0,
      currency: 'BGN',
      annualLeaveDays: 20,
      overtimeMultiplier: 1.0,
      standardHoursPerDay: 8,
      standardHoursWeekly: 40,
      taxPercent: 10.0,
      healthInsurancePercent: 13.78,
      hasTaxDeduction: false, 
      hasHealthInsurance: false 
    }
  });

  const selectedTargetId = watch('targetId');
  const watchedSalary = watch('monthlySalary');
  const autoSaveTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-calculate hourly rate when salary changes and auto-save
  React.useEffect(() => {
    const workDays = workDaysData?.monthlyWorkDays?.daysCount || 22;
    if (watchedSalary > 0 && selectedTargetId) {
      const calculatedRate = (watchedSalary / workDays) / 8;
      const rate = parseFloat(calculatedRate.toFixed(4));
      setValue('hourlyRate', rate);

      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
      setSaveStatus('saving');
      autoSaveTimer.current = setTimeout(async () => {
        try {
          const vals = getValues();
          const dailyHours = vals.standardHoursWeekly / 5;
          const variables = {
            hourlyRate: rate.toString(),
            monthlySalary: watchedSalary.toString(),
            annualLeaveDays: parseInt(vals.annualLeaveDays.toString()),
            currency: vals.currency,
            overtimeMultiplier: vals.overtimeMultiplier.toString(),
            standardHoursPerDay: parseInt(Math.round(dailyHours).toString()),
            taxPercent: vals.taxPercent.toString(),
            healthInsurancePercent: vals.healthInsurancePercent.toString(),
            hasTaxDeduction: vals.hasTaxDeduction,
            hasHealthInsurance: vals.hasHealthInsurance
          };

          if (mode === 'user') {
            await updateUserPayroll({ variables: { userId: parseInt(selectedTargetId), ...variables } });
          } else {
            await updatePosPayroll({ variables: { positionId: parseInt(selectedTargetId), ...variables } });
          }
          setSaveStatus('saved');
          setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (e) { 
            console.error("Auto-save failed", e); 
            setSaveStatus('error');
        }
      }, 2000);
    }
  }, [watchedSalary, workDaysData, setValue, getValues, selectedTargetId, mode, updateUserPayroll, updatePosPayroll]);

  // Bonus Logic
  const [addBonus] = useMutation(ADD_BONUS_MUTATION);
  const [removeBonus] = useMutation(REMOVE_BONUS_MUTATION);
  const [bonusAmount, setBonusAmount] = useState('');
  const [bonusDate, setBonusDate] = useState(new Date().toISOString().split('T')[0]);
  const [bonusDescription, setBonusDescription] = useState('');

  const { data: bonusData, refetch: refetchBonuses, loading: loadingBonuses } = useQuery(GET_USER_BONUSES, {
    variables: { userId: selectedTargetId ? parseInt(selectedTargetId) : 0 },
    skip: mode !== 'user' || !selectedTargetId,
    fetchPolicy: 'network-only' 
  });

  const handleAddBonus = async () => {
    if (!selectedTargetId || !bonusAmount) return;
    try {
      await addBonus({
        variables: {
          userId: parseInt(selectedTargetId),
          amount: parseFloat(bonusAmount),
          date: bonusDate,
          description: bonusDescription,
        },
      });
      setBonusAmount('');
      setBonusDescription('');
      await refetchBonuses();
    } catch {
      if (_err instanceof Error) if (_err instanceof Error) alert(__err.message);
    }
  };

  const handleRemoveBonus = async (id: number) => {
    try {
      await removeBonus({ variables: { id } });
      await refetchBonuses();
    } catch {
      if (_err instanceof Error) if (_err instanceof Error) alert(__err.message);
    }
  };

  React.useEffect(() => {
    if (!selectedTargetId || !data) return;

    let config: PayrollConfig | null = null;
    const targetIdInt = parseInt(selectedTargetId);

    if (mode === 'user') {
        const user = data.users?.users.find((u: UserWithPayroll) => u.id === targetIdInt);
        if (user && user.payrolls && user.payrolls.length > 0) {
            config = user.payrolls[0];
        }
    } else {
        const position = data.positions?.find((p: PositionWithPayroll) => p.id === targetIdInt);
        if (position && position.payrolls && position.payrolls.length > 0) {
            config = position.payrolls[0];
        }
    }

    if (config) {
        // Use individual config
        const dailyHours = config.standardHoursPerDay || 8;
        reset({
            targetId: selectedTargetId,
            hourlyRate: config.hourlyRate,
            monthlySalary: config.monthlySalary || 0,
            currency: config.currency || 'BGN',
            annualLeaveDays: config.annualLeaveDays || 20,
            overtimeMultiplier: config.overtimeMultiplier || 1.0,
            standardHoursPerDay: dailyHours,
            standardHoursWeekly: dailyHours * 5,
            taxPercent: config.taxPercent,
            healthInsurancePercent: config.healthInsurancePercent,
            hasTaxDeduction: config.hasTaxDeduction,
            hasHealthInsurance: config.hasHealthInsurance
        });
    } else if (globalData?.globalPayrollConfig) {
        // Fallback to Global Defaults if no individual config
        const g = globalData.globalPayrollConfig;
        reset({
            targetId: selectedTargetId,
            hourlyRate: g.hourlyRate,
            monthlySalary: g.monthlySalary,
            currency: g.currency,
            annualLeaveDays: g.annualLeaveDays,
            overtimeMultiplier: g.overtimeMultiplier,
            standardHoursPerDay: g.standardHoursPerDay,
            standardHoursWeekly: g.standardHoursPerDay * 5,
            taxPercent: g.taxPercent,
            healthInsurancePercent: g.healthInsurancePercent,
            hasTaxDeduction: g.hasTaxDeduction,
            hasHealthInsurance: g.hasHealthInsurance
        });
    } else {
        // Hard fallback
        reset({
            targetId: selectedTargetId,
            hourlyRate: 0,
            monthlySalary: 0,
            currency: 'BGN',
            annualLeaveDays: 20,
            overtimeMultiplier: 1.0,
            standardHoursPerDay: 8,
            standardHoursWeekly: 40,
            taxPercent: 10.0,
            healthInsurancePercent: 13.78,
            hasTaxDeduction: false, 
            hasHealthInsurance: false 
        });
    }
  }, [selectedTargetId, mode, data, globalData, reset]);

  const onSubmit = async (formData: PayrollLegalSettings) => {
    setMessage(null);
    try {
      const dailyHours = formData.standardHoursWeekly / 5;

      const variables = {
        hourlyRate: formData.hourlyRate.toString(), 
        monthlySalary: formData.monthlySalary ? formData.monthlySalary.toString() : null,
        annualLeaveDays: parseInt(formData.annualLeaveDays),
        currency: formData.currency,
        overtimeMultiplier: formData.overtimeMultiplier.toString(),
        standardHoursPerDay: parseInt(Math.round(dailyHours).toString()),
        taxPercent: formData.taxPercent.toString(),
        healthInsurancePercent: formData.healthInsurancePercent.toString(),
        hasTaxDeduction: formData.hasTaxDeduction,
        hasHealthInsurance: formData.hasHealthInsurance
      };

      if (mode === 'user') {
        await updateUserPayroll({
          variables: {
            userId: parseInt(formData.targetId),
            ...variables
          }
        });
      } else {
        await updatePosPayroll({
          variables: {
            positionId: parseInt(formData.targetId),
            ...variables
          }
        });
      }
      setMessage({ type: 'success', text: 'Настройките са актуализирани успешно!' });
    } catch {
      setMessage({ type: 'error', text: (err instanceof Error ? _err.message : "Грешка") });
    }
  };

  if (loading) return <CircularProgress />;

  return (
    <Box sx={{ maxWidth: 900 }}>
      <Box sx={{ mb: 3 }}>
        <Button 
          variant={mode === 'user' ? 'contained' : 'outlined'} 
          onClick={() => { setMode('user'); reset({ targetId: '' }); }}
          sx={{ mr: 2 }}
        >
          Индивидуални
        </Button>
        <Button 
          variant={mode === 'position' ? 'contained' : 'outlined'} 
          onClick={() => { setMode('position'); reset({ targetId: '' }); }}
        >
          По Длъжност
        </Button>
      </Box>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {mode === 'user' ? 'Конфигуриране за служител' : 'Конфигуриране за длъжност'}
          </Typography>
          
          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <Controller
              name="targetId"
              control={control}
              rules={{ required: "Полето е задължително" }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  fullWidth
                  label={mode === 'user' ? "Изберете служител" : "Изберете длъжност"}
                  margin="normal"
                  required
                >
                  {mode === 'user' 
                    ? data?.users?.users.map((u: User) => (
                        <MenuItem key={u.id} value={u.id}>
                          {u.firstName} {u.lastName} ({u.email}) - {u.position?.title || 'Без длъжност'}
                        </MenuItem>
                      ))
                    : data?.positions.map((p: Position) => (
                        <MenuItem key={p.id} value={p.id}>{p.title}</MenuItem>
                      ))
                  }
                </TextField>
              )}
            />
            
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                <Controller
                  name="hourlyRate"
                  control={control}
                  rules={{ required: true, min: 0 }}
                  render={({ field }) => (
                    <TextField {...field} fullWidth label="Часова ставка" type="number" margin="normal" size="small" inputProps={{ step: "0.01" }} required />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                <Controller
                  name="monthlySalary"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} fullWidth label="Месечна заплата" type="number" margin="normal" size="small" inputProps={{ step: "0.01" }} />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                <Controller
                  name="standardHoursWeekly"
                  control={control}
                  rules={{ required: true, min: 0 }}
                  render={({ field }) => (
                    <TextField 
                        {...field} 
                        fullWidth 
                        label="Часове/седмица" 
                        type="number" 
                        margin="normal"
                        size="small"
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                <Controller
                  name="currency"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} select fullWidth label="Валута" margin="normal" size="small">
                      <MenuItem value="BGN">BGN</MenuItem>
                      <MenuItem value="EUR">EUR</MenuItem>
                      <MenuItem value="USD">USD</MenuItem>
                    </TextField>
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                <Controller
                  name="annualLeaveDays"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} fullWidth label="Отпуск (дни)" type="number" margin="normal" size="small" />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                <Controller
                  name="overtimeMultiplier"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} fullWidth label="Коеф. Извънреден" type="number" margin="normal" size="small" inputProps={{ step: "0.1" }} />
                  )}
                />
              </Grid>

              {/* Deductions Row */}
              <Grid size={{ xs: 12 }}>
                  <Divider sx={{ my: 1 }}><Typography variant="caption">Удръжки</Typography></Divider>
              </Grid>
              
              <Grid size={{ xs: 6, md: 3 }}>
                  <FormControlLabel
                      control={<Controller name="hasTaxDeduction" control={control} render={({ field }) => <Checkbox {...field} checked={field.value} />} />}
                      label="ДДФЛ"
                  />
              </Grid>
              <Grid size={{ xs: 6, md: 3 }}>
                  <Controller name="taxPercent" control={control} render={({ field }) => (
                      <TextField {...field} fullWidth label="ДДФЛ %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!watch('hasTaxDeduction')} />
                  )} />
              </Grid>
              
              <Grid size={{ xs: 6, md: 3 }}>
                  <FormControlLabel
                      control={<Controller name="hasHealthInsurance" control={control} render={({ field }) => <Checkbox {...field} checked={field.value} />} />}
                      label="Осигуровки"
                  />
              </Grid>
              <Grid size={{ xs: 6, md: 3 }}>
                  <Controller name="healthInsurancePercent" control={control} render={({ field }) => (
                      <TextField {...field} fullWidth label="Осигуровки %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!watch('hasHealthInsurance')} />
                  )} />
              </Grid>
            </Grid>
            
            {message && <Alert severity={message.type} sx={{ mt: 2 }}>{message.text}</Alert>}
            
            <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
                <Button type="submit" variant="contained" disabled={updatingUser || updatingPos}>
                Запази настройките
                </Button>
                
                {saveStatus === 'saving' && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'info.main' }}>
                        <CloudSyncIcon sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />
                        <Typography variant="caption">Записване...</Typography>
                    </Box>
                )}
                {saveStatus === 'saved' && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'success.main' }}>
                        <CheckCircleIcon fontSize="small" />
                        <Typography variant="caption">Промените са записани автоматично</Typography>
                    </Box>
                )}
                {saveStatus === 'error' && (
                    <Typography variant="caption" color="error">Грешка при автоматичен запис</Typography>
                )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Bonus Section */}
      {mode === 'user' && selectedTargetId && (
        <Card variant="outlined" sx={{ mt: 3, border: '1px solid #e0e0e0' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PaidIcon color="success" /> Бонуси и допълнителни плащания
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Добавете бонуси, които ще бъдат включени в следващия генериран фиш за този служител.
                </Typography>
                
                {/* List */}
                <Box sx={{ mb: 3, maxHeight: 250, overflowY: 'auto', bgcolor: '#fafafa', p: 1, borderRadius: 1 }}>
                    {loadingBonuses ? <CircularProgress size={24} sx={{ display: 'block', mx: 'auto', my: 2 }} /> : (
                        (!bonusData?.user?.bonuses || bonusData.user.bonuses.length === 0) ? (
                            <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 3 }}>
                                Няма добавени бонуси за този потребител.
                            </Typography>
                        ) : (
                            bonusData.user.bonuses.map((b: Bonus) => (
                                <Box key={b.id} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1.5, borderBottom: '1px solid #e0e0e0', bgcolor: 'white', mb: 1, borderRadius: 1, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                                    <Box>
                                        <Typography variant="body1" fontWeight="bold" color="success.main">
                                            +{parseFloat(b.amount).toFixed(2)} {currency}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" display="block">
                                            Дата: {b.date} {b.description ? `| ${b.description}` : ''}
                                        </Typography>
                                    </Box>
                                    <Button size="small" color="error" variant="outlined" onClick={() => handleRemoveBonus(b.id)}>
                                        Изтрий
                                    </Button>
                                </Box>
                            ))
                        )
                    )}
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Add Form */}
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>Добави нов бонус:</Typography>
                <Grid container spacing={2} alignItems="flex-start">
                    <Grid size={{ xs: 12, sm: 3 }}>
                        <TextField fullWidth size="small" label="Сума" type="number" value={bonusAmount} onChange={(e) => setBonusAmount(e.target.value)} />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 3 }}>
                        <TextField fullWidth size="small" type="date" label="Дата" InputLabelProps={{ shrink: true }} value={bonusDate} onChange={(e) => setBonusDate(e.target.value)} />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField fullWidth size="small" label="Описание (опционално)" value={bonusDescription} onChange={(e) => setBonusDescription(e.target.value)} />
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                        <Button variant="contained" color="success" onClick={handleAddBonus} disabled={!bonusAmount} startIcon={<AddIcon />}>
                            Добави бонус
                        </Button>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
      )}
    </Box>
  );
};

// --- Component: Holiday Sync ---
const HolidaySettings: React.FC = () => {
  const [year, setYear] = useState(new Date().getFullYear());
  const [syncHolidays, { loading: loadingPublic }] = useMutation(SYNC_HOLIDAYS_MUTATION);
  const [syncOrthodoxHolidays, { loading: loadingOrthodox }] = useMutation(SYNC_ORTHODOX_HOLIDAYS_MUTATION);
  const [result, setResult] = useState<string | null>(null);
  const [includeOrthodox, setIncludeOrthodox] = useState(() => {
    return localStorage.getItem('include_orthodox_holidays') === 'true';
  });

  const handleSyncPublic = async () => {
    try {
      const res = await syncHolidays({ variables: { year } });
      setResult(`Успешно добавени ${res.data.syncHolidays} нови официални празници за ${year}г.`);
    } catch {
      setResult(`Грешка: ${e.message}`);
    }
  };

  const handleSyncOrthodox = async () => {
    try {
      const res = await syncOrthodoxHolidays({ variables: { year } });
      setResult(`Успешно добавени ${res.data.syncOrthodoxHolidays} нови православни празници за ${year}г.`);
    } catch {
      setResult(`Грешка: ${e.message}`);
    }
  };

  const handleToggleOrthodox = (event: React.ChangeEvent<HTMLInputElement>) => {
    const checked = event.target.checked;
    setIncludeOrthodox(checked);
    localStorage.setItem('include_orthodox_holidays', String(checked));
  };

  return (
    <Box sx={{ maxWidth: 700 }}>
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Официални празници</Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Синхронизация на официалните почивни дни за България от външен източник (Nager API). 
            Това позволява на системата да не ги брои като работни дни.
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
            <TextField 
              label="Година" 
              type="number" 
              value={year} 
              onChange={(e) => setYear(parseInt(e.target.value))}
              size="small"
              sx={{ width: 120 }}
            />
            <Button variant="contained" onClick={handleSyncPublic} disabled={loadingPublic} startIcon={<CalendarMonthIcon />}>
              {loadingPublic ? 'Синхронизиране...' : 'Синхронизирай'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Православни празници</Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Синхронизация на православните празници за България (Великден, Коледа, Петровден, Голяма Богородица и др.).
            Тези празници НЕ са неработни дни по закон, но могат да бъдат включени в графиците.
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2, mb: 2 }}>
            <TextField 
              label="Година" 
              type="number" 
              value={year} 
              onChange={(e) => setYear(parseInt(e.target.value))}
              size="small"
              sx={{ width: 120 }}
            />
            <Button variant="outlined" onClick={handleSyncOrthodox} disabled={loadingOrthodox} startIcon={<CalendarMonthIcon />}>
              {loadingOrthodox ? 'Синхронизиране...' : 'Синхронизирай'}
            </Button>
          </Box>

          <FormControlLabel
            control={
              <Switch 
                checked={includeOrthodox} 
                onChange={handleToggleOrthodox}
                color="primary"
              />
            }
            label="Включи православните празници в графиците"
          />
          <Typography variant="body2" color="text.secondary">
            Когато е включено, правoslavните празници ще се показват в календара като неработни дни (жълт цвят).
          </Typography>
        </CardContent>
      </Card>
      
      {result && <Alert severity={result.includes('Грешка') ? 'error' : 'success'} sx={{ mt: 2 }}>{result}</Alert>}
    </Box>
  );
};
  
  const PayrollPageTabMap: Record<string, number> = {
    'reports': 3,
    'payments': 1,
    'declarations': 2,
    'settings': 0,
  };

  interface Props {
    tab?: string;
  }

  const PayrollPage: React.FC<Props> = ({ tab }) => {
    const initialTab = tab ? (PayrollPageTabMap[tab] ?? 0) : 0;
    const [tabValue, setTabValue] = useState(initialTab);
    
    React.useEffect(() => {
      const newTab = tab ? (PayrollPageTabMap[tab] ?? 0) : 0;
      setTabValue(newTab);
    }, [tab]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">Отдел финанси</Typography>
      
      {tabValue === 0 && (
          <Box sx={{ maxWidth: 900 }}>
              <PayrollLegalSettings />
              <Divider sx={{ my: 4 }} />
              <GlobalPayrollSettings />
              <MonthlyWorkDaysSettings />
          </Box>
      )}
      {tabValue === 1 && (
          <Box sx={{ maxWidth: 900 }}>
              <PayrollSettings />
              <Divider sx={{ my: 4 }} />
              <AdvanceLoanManager />
          </Box>
      )}
      {tabValue === 2 && <HolidaySettings />}
      {tabValue === 3 && <PayrollReports />}
    </Container>
  );
};

export default PayrollPage;