import React, { useState } from 'react';
import {
  Container, Typography, Box, TextField, Button, MenuItem,
  Alert, CircularProgress, Card, CardContent, Divider, Grid, Link, FormControlLabel, Checkbox,
  Switch, type SelectChangeEvent, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  InputLabel, Select, FormControl, InputAdornment
} from '@mui/material';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import PaidIcon from '@mui/icons-material/Paid';
import ReceiptIcon from '@mui/icons-material/Receipt';
import AddIcon from '@mui/icons-material/Add';
import AssessmentIcon from '@mui/icons-material/Assessment';
import { useQuery, useMutation, gql, useLazyQuery } from '@apollo/client';
import { InfoIcon } from '../components/ui/InfoIcon';
import { useForm, Controller, useWatch, FormProvider } from 'react-hook-form';
import { useCurrency, formatCurrencyValue, getCurrencySymbolForCurrency } from '../currencyContext';
import { 
  type PayrollLegalSettings, 
  type UserWithPayroll, 
  type PositionWithPayroll, 
  type PayrollSummaryItem, 
  type PayrollConfig,
  type Bonus,
  type User,
  type Position,
  type ContractTemplate,
  type AnnexTemplate,
  type ClauseTemplate,
  type ContractAnnex,
  getErrorMessage
} from '../types';
import EmploymentContractsList from '../components/EmploymentContractsList';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import PrintIcon from '@mui/icons-material/Print';
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

// Employment Contract Queries
export const GET_EMPLOYMENT_CONTRACTS = gql`
  query GetEmploymentContracts($companyId: Int, $status: String) {
    employmentContracts(companyId: $companyId, status: $status) {
      id
      employeeName
      employeeEgn
      contractNumber
      contractType
      startDate
      endDate
      baseSalary
      workHoursPerWeek
      status
      signedAt
      userId
      company {
        id
        name
      }
      annexes {
        id
        annexNumber
        effectiveDate
        baseSalary
        changeType
        changeDescription
        status
        isSigned
      }
    }
  }
`;

export const CREATE_EMPLOYMENT_CONTRACT = gql`
  mutation CreateEmploymentContract($input: EmploymentContractCreateInput!) {
    createEmploymentContract(input: $input) {
      id
      employeeName
      status
    }
  }
`;

export const SIGN_EMPLOYMENT_CONTRACT = gql`
  mutation SignEmploymentContract($id: Int!) {
    signEmploymentContract(id: $id) {
      id
      status
      signedAt
    }
  }
`;

export const LINK_CONTRACT_TO_USER = gql`
  mutation LinkContractToUser($contractId: Int!, $userId: Int!) {
    linkEmploymentContractToUser(contractId: $contractId, userId: $userId) {
      id
      status
      userId
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

// --- TRZ Templates Queries & Mutations ---
const GET_CONTRACT_TEMPLATES = gql`
  query GetContractTemplates {
    contractTemplates {
      id
      companyId
      name
      description
      contractType
      workHoursPerWeek
      probationMonths
      salaryCalculationType
      paymentDay
      nightWorkRate
      overtimeRate
      holidayRate
      workClass
      isActive
      createdAt
      currentVersion {
        id
        version
        isCurrent
        createdBy
        createdAt
        changeNote
        sections {
          id
          title
          content
          orderIndex
          isRequired
        }
      }
    }
  }
`;

const GET_ANNEX_TEMPLATES = gql`
  query GetAnnexTemplates {
    annexTemplates {
      id
      companyId
      name
      description
      changeType
      newBaseSalary
      newWorkHoursPerWeek
      newNightWorkRate
      newOvertimeRate
      newHolidayRate
      isActive
      createdAt
      currentVersion {
        id
        version
        isCurrent
        createdBy
        createdAt
        changeNote
      }
    }
  }
`;

const GET_CLAUSE_TEMPLATES = gql`
  query GetClauseTemplates($category: String) {
    clauseTemplates(category: $category) {
      id
      companyId
      title
      content
      category
      isActive
      createdAt
    }
  }
`;

const GET_ANNEXES = gql`
  query GetAnnexes($status: String) {
    annexes(status: $status) {
      id
      contractId
      annexNumber
      effectiveDate
      status
      baseSalary
      changeType
      isSigned
      signedByEmployee
      signedByEmployer
      createdAt
    }
  }
`;

const GET_CONTRACTS = gql`
  query GetContracts {
    users(skip: 0, limit: 1000) {
      users {
        id
        firstName
        lastName
        pin
        employmentContract {
          id
          contractNumber
          startDate
          endDate
          isActive
          contractType
          baseSalary
          position {
            id
            title
          }
        }
      }
    }
  }
`;

const CREATE_CONTRACT_ANNEX = gql`
  mutation CreateContractAnnex(
    $contractId: Int!,
    $effectiveDate: Date!,
    $annexNumber: String,
    $baseSalary: Decimal,
    $workHoursPerWeek: Int,
    $nightWorkRate: Decimal,
    $overtimeRate: Decimal,
    $holidayRate: Decimal
  ) {
    createContractAnnex(
      contractId: $contractId,
      effectiveDate: $effectiveDate,
      annexNumber: $annexNumber,
      baseSalary: $baseSalary,
      workHoursPerWeek: $workHoursPerWeek,
      nightWorkRate: $nightWorkRate,
      overtimeRate: $overtimeRate,
      holidayRate: $holidayRate
    ) {
      id
      contractId
      annexNumber
      effectiveDate
      status
    }
  }
`;

const CREATE_CONTRACT_TEMPLATE = gql`
  mutation CreateContractTemplate(
    $name: String!,
    $description: String,
    $contractType: String!,
    $workHoursPerWeek: Int!,
    $probationMonths: Int!,
    $salaryCalculationType: String!,
    $paymentDay: Int!,
    $nightWorkRate: Float!,
    $overtimeRate: Float!,
    $holidayRate: Float!,
    $workClass: String,
    $positionId: Int,
    $departmentId: Int,
    $baseSalary: Float,
    $clauseIds: String
  ) {
    createContractTemplate(
      name: $name,
      description: $description,
      contractType: $contractType,
      workHoursPerWeek: $workHoursPerWeek,
      probationMonths: $probationMonths,
      salaryCalculationType: $salaryCalculationType,
      paymentDay: $paymentDay,
      nightWorkRate: $nightWorkRate,
      overtimeRate: $overtimeRate,
      holidayRate: $holidayRate,
      workClass: $workClass,
      positionId: $positionId,
      departmentId: $departmentId,
      baseSalary: $baseSalary,
      clauseIds: $clauseIds
    ) {
      id
      name
    }
  }
`;

const DELETE_CONTRACT_TEMPLATE = gql`
  mutation DeleteContractTemplate($id: Int!) {
    deleteContractTemplate(id: $id)
  }
`;

const CREATE_ANNEX_TEMPLATE = gql`
  mutation CreateAnnexTemplate(
    $name: String!,
    $description: String,
    $changeType: String!,
    $newBaseSalary: Float,
    $newWorkHoursPerWeek: Int,
    $newNightWorkRate: Float,
    $newOvertimeRate: Float,
    $newHolidayRate: Float
  ) {
    createAnnexTemplate(
      name: $name,
      description: $description,
      changeType: $changeType,
      newBaseSalary: $newBaseSalary,
      newWorkHoursPerWeek: $newWorkHoursPerWeek,
      newNightWorkRate: $newNightWorkRate,
      newOvertimeRate: $newOvertimeRate,
      newHolidayRate: $newHolidayRate
    ) {
      id
      name
    }
  }
`;

const DELETE_ANNEX_TEMPLATE = gql`
  mutation DeleteAnnexTemplate($id: Int!) {
    deleteAnnexTemplate(id: $id)
  }
`;

const CREATE_CLAUSE_TEMPLATE = gql`
  mutation CreateClauseTemplate(
    $title: String!,
    $content: String!,
    $category: String!
  ) {
    createClauseTemplate(
      title: $title,
      content: $content,
      category: $category
    ) {
      id
      title
    }
  }
`;

const DELETE_CLAUSE_TEMPLATE = gql`
  mutation DeleteClauseTemplate($id: Int!) {
    deleteClauseTemplate(id: $id)
  }
`;

// --- Section CRUD Mutations ---
const ADD_SECTION_TO_CONTRACT_TEMPLATE = gql`
  mutation AddSectionToContractTemplate(
    $templateId: Int!,
    $section: ContractTemplateSectionInput!
  ) {
    addSectionToContractTemplate(templateId: $templateId, section: $section) {
      id
      title
      content
      orderIndex
      isRequired
    }
  }
`;

const UPDATE_SECTION_IN_CONTRACT_TEMPLATE = gql`
  mutation UpdateSectionInContractTemplate(
    $sectionId: Int!,
    $section: ContractTemplateSectionUpdateInput!
  ) {
    updateSectionInContractTemplate(sectionId: $sectionId, section: $section) {
      id
      title
      content
      orderIndex
      isRequired
    }
  }
`;

const ADD_SECTION_TO_ANNEX_TEMPLATE = gql`
  mutation AddSectionToAnnexTemplate(
    $templateId: Int!,
    $section: AnnexTemplateSectionInput!
  ) {
    addSectionToAnnexTemplate(templateId: $templateId, section: $section) {
      id
      title
      content
      orderIndex
      isRequired
    }
  }
`;

const UPDATE_SECTION_IN_ANNEX_TEMPLATE = gql`
  mutation UpdateSectionInAnnexTemplate(
    $sectionId: Int!,
    $section: AnnexTemplateSectionUpdateInput!
  ) {
    updateSectionInAnnexTemplate(sectionId: $sectionId, section: $section) {
      id
      title
      content
      orderIndex
      isRequired
    }
  }
`;

const SIGN_CONTRACT_ANNEX = gql`
  mutation SignContractAnnex($annexId: Int!) {
    signContractAnnex(annexId: $annexId) {
      id
      status
      isSigned
      signedAt
    }
  }
`;

// --- Component: Payroll Legal Settings ---
const PayrollLegalSettings: React.FC = () => {
    const { data, loading, refetch } = useQuery(GET_PAYROLL_LEGAL_SETTINGS);
    const [updateLegal, { loading: updating }] = useMutation(UPDATE_PAYROLL_LEGAL_MUTATION);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [defaultTaxResident, setDefaultTaxResident] = useState(true);
    const { currency } = useCurrency();
    const currencySymbol = getCurrencySymbolForCurrency(currency);

    const { control, handleSubmit, reset, setValue } = useForm<PayrollLegalSettings>({
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
            setDefaultTaxResident(data.payrollLegalSettings.defaultTaxResident ?? true);
        }
    }, [data, reset]);

    const handleDefaultTaxResidentChange = (checked: boolean) => {
        setDefaultTaxResident(checked);
        setValue('defaultTaxResident', checked);
    };

    type LegalFormData = PayrollLegalSettings;
    const onSubmitLegal = async (formData: LegalFormData) => {
        setMessage(null);
        try {
            await updateLegal({
                variables: {
                    maxInsuranceBase: Number(formData.maxInsuranceBase),
                    employeeInsuranceRate: Number(formData.employeeInsuranceRate),
                    incomeTaxRate: Number(formData.incomeTaxRate),
                    civilContractCostsRate: Number(formData.civilContractCostsRate),
                    noiCompensationPercent: Number(formData.noiCompensationPercent),
                    employerPaidSickDays: Number(formData.employerPaidSickDays),
                    defaultTaxResident: formData.defaultTaxResident
                }
            });
            setMessage({ type: 'success', text: 'Законовите настройки са обновени успешно!' });
            refetch();
        } catch (e) {
            setMessage({ type: 'error', text: e instanceof Error ? e.message : "Грешка" });
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
          <Box component="form" onSubmit={handleSubmit(onSubmitLegal)}>
                    <Grid container spacing={3}>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <Controller name="maxInsuranceBase" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Макс. осигурителен праг" type="number" size="small" helperText={`${currencySymbol} за месец`} />
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
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Checkbox 
                                    checked={defaultTaxResident}
                                    onChange={e => handleDefaultTaxResidentChange(e.target.checked)}
                                />
                                <Typography variant="body2">Данъчен резидент (Default)</Typography>
                            </Box>
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
        } catch (e) { alert("Грешка при генериране на PDF: " + (e instanceof Error ? e.message : "")); }
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
        } catch (err) { alert(getErrorMessage(err)); }
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
                            <TextField
                                fullWidth type="date" label="От"
                                InputLabelProps={{ shrink: true }}
                                value={startDate}
                                onChange={e => setStartDate(e.target.value)}
                                size="small" placeholder="2026-01-01"
                                slotProps={{
                                    input: {
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <InfoIcon helpText="Начална дата на периода за ведомостта" />
                                            </InputAdornment>
                                        )
                                    }
                                }}
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 3 }}>
                            <TextField
                                fullWidth type="date" label="До"
                                InputLabelProps={{ shrink: true }}
                                value={endDate}
                                onChange={e => setEndDate(e.target.value)}
                                size="small" placeholder="2026-01-31"
                                slotProps={{
                                    input: {
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <InfoIcon helpText="Крайна дата на периода за ведомостта" />
                                            </InputAdornment>
                                        )
                                    }
                                }}
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 4 }}>
                            <TextField
                                select fullWidth label="Служители (по избор)"
                                SelectProps={{
                                    multiple: true,
                                    value: selectedUserIds,
                                    onChange: (e: SelectChangeEvent<unknown>) => setSelectedUserIds(e.target.value as number[])
                                }}
                                size="small"
                                slotProps={{
                                    input: {
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <InfoIcon helpText="Избери конкретни служители или остави празно за всички" />
                                            </InputAdornment>
                                        )
                                    }
                                }}
                            >
                                {usersData?.users?.users.map((u: User) => (
                                    <MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>
                                ))}
                            </TextField>
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
        } catch (err) {
            if (err instanceof Error) alert(err.message);
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
    const { refreshCurrency } = useCurrency();
    const [hasTaxDeduction, setHasTaxDeduction] = useState(false);
    const [hasHealthInsurance, setHasHealthInsurance] = useState(false);

    const { control, handleSubmit, reset, setValue } = useForm<PayrollLegalSettings>({
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

    React.useEffect(() => {
        if (data?.globalPayrollConfig) {
            const conf = data.globalPayrollConfig;
            setHasTaxDeduction(conf.hasTaxDeduction ?? false);
            setHasHealthInsurance(conf.hasHealthInsurance ?? false);
            reset({
                hourlyRate: conf.hourlyRate,
                monthlySalary: conf.monthlySalary,
                currency: conf.currency,
                annualLeaveDays: conf.annualLeaveDays,
                overtimeMultiplier: conf.overtimeMultiplier,
                standardHoursWeekly: conf.standardHoursPerDay * 5,
                taxPercent: conf.taxPercent,
                healthInsurancePercent: conf.healthInsurancePercent,
                hasTaxDeduction: conf.hasTaxDeduction ?? false,
                hasHealthInsurance: conf.hasHealthInsurance ?? false
            });
        }
    }, [data, reset, setHasTaxDeduction, setHasHealthInsurance]);

    type GlobalFormData = PayrollLegalSettings;
    const onSubmitGlobal = async (formData: GlobalFormData) => {
        setMessage(null);
        try {
            await updateConfig({
                variables: {
                    hourlyRate: String(formData.hourlyRate ?? 0),
                    monthlySalary: String(formData.monthlySalary ?? 0),
                    overtimeMultiplier: String(formData.overtimeMultiplier ?? 1),
                    standardHoursPerDay: Math.round((formData.standardHoursWeekly ?? 40) / 5),
                    currency: formData.currency ?? 'EUR',
                    annualLeaveDays: Number(formData.annualLeaveDays ?? 20),
                    taxPercent: String(formData.taxPercent ?? 10),
                    healthInsurancePercent: String(formData.healthInsurancePercent ?? 5),
                    hasTaxDeduction: formData.hasTaxDeduction ?? true,
                    hasHealthInsurance: formData.hasHealthInsurance ?? true
                }
            });
            setMessage({ type: 'success', text: 'Глобалните настройки са обновени!' });
            refreshCurrency(); // Refresh global currency context
        } catch (e) {
            setMessage({ type: 'error', text: e instanceof Error ? e.message : "Грешка" });
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
                <Box component="form" onSubmit={handleSubmit(onSubmitGlobal)}>
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
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Checkbox 
                                    checked={hasTaxDeduction}
                                    onChange={e => {
                                        setHasTaxDeduction(e.target.checked);
                                        setValue('hasTaxDeduction', e.target.checked);
                                    }}
                                />
                                <Typography variant="body2">ДДФЛ</Typography>
                            </Box>
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                            <Controller name="taxPercent" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="ДДФЛ %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!hasTaxDeduction} />
                            )} />
                        </Grid>
                        
                        <Grid size={{ xs: 6, md: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Checkbox 
                                    checked={hasHealthInsurance}
                                    onChange={e => {
                                        setHasHealthInsurance(e.target.checked);
                                        setValue('hasHealthInsurance', e.target.checked);
                                    }}
                                />
                                <Typography variant="body2">Осигуровки</Typography>
                            </Box>
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                            <Controller name="healthInsurancePercent" control={control} render={({ field }) => (
                                <TextField {...field} fullWidth label="Осигуровки %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!hasHealthInsurance} />
                            )} />
                        </Grid>
                    </Grid>
                    {message && <Alert severity={message.type} sx={{ mt: 2 }}>{message.text}</Alert>}
                    
                    <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Button type="submit" variant="contained" disabled={updating}>Запази Глобалните Настройки</Button>
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
        } catch (e) {
            alert("Грешка: " + (e instanceof Error ? e.message : ""));
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
  const { data: globalData } = useQuery(GET_GLOBAL_CONFIG_QUERY);
  const [mode, setMode] = useState<'user' | 'position'>('user');
  const { currency } = useCurrency();
  
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
  const [hasTaxDeduction, setHasTaxDeductionLocal] = useState(false);
  const [hasHealthInsurance, setHasHealthInsuranceLocal] = useState(false);

  const methods = useForm<PayrollLegalSettings>({
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

  const { control, handleSubmit, reset, setValue, getValues } = methods;
  const selectedTargetId = useWatch({ control, name: 'targetId' });
  const watchedSalary = useWatch({ control, name: 'monthlySalary' });
  const autoSaveTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-calculate hourly rate when salary changes and auto-save
  React.useEffect(() => {
    const workDays = workDaysData?.monthlyWorkDays?.daysCount || 22;
    const salary = watchedSalary ?? 0;
    if (salary > 0 && selectedTargetId) {
      const calculatedRate = (salary / workDays) / 8;
      const rate = parseFloat(calculatedRate.toFixed(4));
      setValue('hourlyRate', rate);

      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
      setSaveStatus('saving');
      autoSaveTimer.current = setTimeout(async () => {
        try {
          const vals = getValues();
          const dailyHours = (vals.standardHoursWeekly ?? 40) / 5;
          const variables = {
            hourlyRate: rate.toString(),
            monthlySalary: salary.toString(),
            annualLeaveDays: parseInt(String(vals.annualLeaveDays ?? 0)),
            currency: vals.currency,
            overtimeMultiplier: String(vals.overtimeMultiplier ?? ''),
            standardHoursPerDay: parseInt(String(Math.round(dailyHours))),
            taxPercent: String(vals.taxPercent ?? 0),
            healthInsurancePercent: String(vals.healthInsurancePercent ?? 0),
            hasTaxDeduction: vals.hasTaxDeduction ?? false,
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
    } catch (err) {
      if (err instanceof Error) alert(err.message);
    }
  };

  const handleRemoveBonus = async (id: number) => {
    try {
      await removeBonus({ variables: { id } });
      await refetchBonuses();
    } catch (err) {
      if (err instanceof Error) alert(err.message);
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
        const dailyHours = config.standardHoursPerDay || 8;
        setHasTaxDeductionLocal(config.hasTaxDeduction ?? false);
        setHasHealthInsuranceLocal(config.hasHealthInsurance ?? false);
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
        const g = globalData.globalPayrollConfig;
        setHasTaxDeductionLocal(g.hasTaxDeduction ?? false);
        setHasHealthInsuranceLocal(g.hasHealthInsurance ?? false);
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
        setHasTaxDeductionLocal(false);
        setHasHealthInsuranceLocal(false);
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
  }, [selectedTargetId, mode, data, globalData, reset, setHasTaxDeductionLocal, setHasHealthInsuranceLocal]);

  type IndividualFormData = PayrollLegalSettings;
  const onSubmitIndividual = async (formData: IndividualFormData) => {
    setMessage(null);
    try {
      const dailyHours = (formData.standardHoursWeekly ?? 40) / 5;

      const variables = {
        hourlyRate: String(formData.hourlyRate ?? 0), 
        monthlySalary: formData.monthlySalary ? String(formData.monthlySalary) : null,
        annualLeaveDays: Number(formData.annualLeaveDays ?? 20),
        currency: formData.currency ?? 'EUR',
        overtimeMultiplier: String(formData.overtimeMultiplier ?? 1),
        standardHoursPerDay: Number(Math.round(dailyHours)),
        taxPercent: String(formData.taxPercent ?? 10),
        healthInsurancePercent: String(formData.healthInsurancePercent ?? 5),
        hasTaxDeduction: formData.hasTaxDeduction ?? true,
        hasHealthInsurance: formData.hasHealthInsurance ?? true
      };

      if (mode === 'user') {
        await updateUserPayroll({
          variables: {
            userId: Number(formData.targetId),
            ...variables
          }
        });
      } else {
        await updatePosPayroll({
          variables: {
            positionId: Number(formData.targetId),
            ...variables
          }
        });
      }
      setMessage({ type: 'success', text: 'Настройките са актуализирани успешно!' });
        } catch (e) {
            setMessage({ type: 'error', text: e instanceof Error ? e.message : "Грешка" });
        }
  };

  if (loading) return <CircularProgress />;

  return (
    <FormProvider {...methods}>
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
          
          <Box component="form" onSubmit={handleSubmit(onSubmitIndividual)}>
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
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Checkbox 
                          checked={hasTaxDeduction}
                          onChange={e => {
                              setHasTaxDeductionLocal(e.target.checked);
                              setValue('hasTaxDeduction', e.target.checked);
                          }}
                      />
                      <Typography variant="body2">ДДФЛ</Typography>
                  </Box>
              </Grid>
              <Grid size={{ xs: 6, md: 3 }}>
                  <Controller name="taxPercent" control={control} render={({ field }) => (
                      <TextField {...field} fullWidth label="ДДФЛ %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!hasTaxDeduction} />
                  )} />
              </Grid>
              
              <Grid size={{ xs: 6, md: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Checkbox 
                          checked={hasHealthInsurance}
                          onChange={e => {
                              setHasHealthInsuranceLocal(e.target.checked);
                              setValue('hasHealthInsurance', e.target.checked);
                          }}
                      />
                      <Typography variant="body2">Осигуровки</Typography>
                  </Box>
              </Grid>
              <Grid size={{ xs: 6, md: 3 }}>
                  <Controller name="healthInsurancePercent" control={control} render={({ field }) => (
                      <TextField {...field} fullWidth label="Осигуровки %" type="number" margin="dense" size="small" inputProps={{ step: "0.01" }} disabled={!hasHealthInsurance} />
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
                                            +{Number(b.amount).toFixed(2)} {currency}
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
    </FormProvider>
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
    } catch (e) {
      setResult(`Грешка: ${e instanceof Error ? e.message : ""}`);
    }
  };

  const handleSyncOrthodox = async () => {
    try {
      const res = await syncOrthodoxHolidays({ variables: { year } });
      setResult(`Успешно добавени ${res.data.syncOrthodoxHolidays} нови православни празници за ${year}г.`);
    } catch (e) {
      setResult(`Грешка: ${e instanceof Error ? e.message : ""}`);
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
    'templates': 4,
    'annexes': 5,
    'contracts': 6,
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
      {tabValue === 4 && <TemplatesSettings />}
      {tabValue === 5 && <AnnexesSettings />}
      {tabValue === 6 && <EmploymentContractsList />}
    </Container>
  );
};

// --- Component: Templates Settings ---
const TemplatesSettings: React.FC = () => {
  const [templateType, setTemplateType] = useState<'contracts' | 'annexes' | 'clauses'>('contracts');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { data: contractData, loading: contractLoading, refetch: refetchContracts } = useQuery(GET_CONTRACT_TEMPLATES);
  const { data: annexData, loading: annexLoading, refetch: refetchAnnexes } = useQuery(GET_ANNEX_TEMPLATES);
  const { data: clauseData, loading: clauseLoading, refetch: refetchClauses } = useQuery(GET_CLAUSE_TEMPLATES, {
    variables: { category: null }
  });

  // Зареждане на длъжности и отдели
  const { data: positionsData } = useQuery(gql`
    query GetPositions {
      positions { id title }
    }
  `);
  const { data: departmentsData } = useQuery(gql`
    query GetDepartments {
      departments { id name }
    }
  `);

  const positions: Array<{id: number, title: string}> = positionsData?.positions || [];
  const departments: Array<{id: number, name: string}> = departmentsData?.departments || [];

  const [createContractTemplate] = useMutation(CREATE_CONTRACT_TEMPLATE);
  const [deleteContractTemplate] = useMutation(DELETE_CONTRACT_TEMPLATE);
  const [createAnnexTemplate] = useMutation(CREATE_ANNEX_TEMPLATE);
  const [deleteAnnexTemplate] = useMutation(DELETE_ANNEX_TEMPLATE);
  const [createClauseTemplate] = useMutation(CREATE_CLAUSE_TEMPLATE);
  const [deleteClauseTemplate] = useMutation(DELETE_CLAUSE_TEMPLATE);

  // Section mutations
  const [addSectionToContractTemplate] = useMutation(ADD_SECTION_TO_CONTRACT_TEMPLATE);
  const [updateSectionInContractTemplate] = useMutation(UPDATE_SECTION_IN_CONTRACT_TEMPLATE);
  const [addSectionToAnnexTemplate] = useMutation(ADD_SECTION_TO_ANNEX_TEMPLATE);
  const [updateSectionInAnnexTemplate] = useMutation(UPDATE_SECTION_IN_ANNEX_TEMPLATE);

  const [openDialog, setOpenDialog] = useState<boolean>(false);
  const [editingItem, setEditingItem] = useState<ContractTemplate | AnnexTemplate | ClauseTemplate | null>(null);
  const [openSectionDialog, setOpenSectionDialog] = useState<boolean>(false);
  const [editingSection, setEditingSection] = useState<{ id?: number; title: string; content: string; orderIndex: number; isRequired: boolean } | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<ContractTemplate | AnnexTemplate | null>(null);
  const [selectedClauses, setSelectedClauses] = useState<string[]>([]);

  const contractTypes = [
    { value: 'full_time', label: 'Пълно работно време' },
    { value: 'part_time', label: 'Непълно работно време' },
    { value: 'contractor', label: 'Граждански договор' },
    { value: 'internship', label: 'Стажант' },
  ];

  const changeTypes = [
    { value: 'salary', label: 'Повишение на заплатата' },
    { value: 'position', label: 'Промяна на длъжността' },
    { value: 'hours', label: 'Промяна на работното време' },
    { value: 'rate', label: 'Промяна на надбавки' },
    { value: 'other', label: 'Друго' },
  ];

  const clauseCategories = [
    { value: 'rights_employer', label: 'Права на работодателя' },
    { value: 'rights_employee', label: 'Права на работника' },
    { value: 'work_schedule', label: 'Работно време' },
    { value: 'salary', label: 'Заплащане' },
    { value: 'confidentiality', label: 'Конфиденциалност' },
    { value: 'business_trip', label: 'Командироване' },
    { value: 'termination', label: 'Прекратяване' },
    { value: 'other', label: 'Друго' },
  ];

  const handleCreate = async (formData: Record<string, unknown>) => {
    setError(null);
    setSuccess(null);
    try {
      if (templateType === 'contracts') {
        await createContractTemplate({ variables: formData });
        setSuccess('Шаблонът е създаден успешно');
        await refetchContracts();
      } else if (templateType === 'annexes') {
        await createAnnexTemplate({ variables: formData });
        setSuccess('Шаблонът за анекс е създаден успешно');
        await refetchAnnexes();
      } else if (templateType === 'clauses') {
        await createClauseTemplate({ variables: formData });
        setSuccess('Клаузата е създадена успешно');
        await refetchClauses();
      }
      setOpenDialog(false);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Сигурни ли сте, че искате да изтриете този шаблон?')) return;
    setError(null);
    try {
      if (templateType === 'contracts') {
        await deleteContractTemplate({ variables: { id } });
        setSuccess('Шаблонът е изтрит');
        await refetchContracts();
      } else if (templateType === 'annexes') {
        await deleteAnnexTemplate({ variables: { id } });
        setSuccess('Шаблонът за анекс е изтрит');
        await refetchAnnexes();
      } else if (templateType === 'clauses') {
        await deleteClauseTemplate({ variables: { id } });
        setSuccess('Клаузата е изтрита');
        await refetchClauses();
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleOpenSectionDialog = (section?: { id?: number; title: string; content: string; orderIndex: number; isRequired: boolean }) => {
    setEditingSection(section || { title: '', content: '', orderIndex: 0, isRequired: false });
    setOpenSectionDialog(true);
  };

  const handleSaveSection = async (templateId: number) => {
    if (!editingSection) return;
    setError(null);
    try {
      if (templateType === 'contracts') {
        if (editingSection.id) {
          await updateSectionInContractTemplate({
            variables: {
              sectionId: editingSection.id,
              section: {
                title: editingSection.title,
                content: editingSection.content,
                orderIndex: editingSection.orderIndex,
                isRequired: editingSection.isRequired
              }
            }
          });
        } else {
          await addSectionToContractTemplate({
            variables: {
              templateId,
              section: {
                title: editingSection.title,
                content: editingSection.content,
                orderIndex: editingSection.orderIndex,
                isRequired: editingSection.isRequired
              }
            }
          });
        }
        await refetchContracts();
      } else if (templateType === 'annexes') {
        if (editingSection.id) {
          await updateSectionInAnnexTemplate({
            variables: {
              sectionId: editingSection.id,
              section: {
                title: editingSection.title,
                content: editingSection.content,
                orderIndex: editingSection.orderIndex,
                isRequired: editingSection.isRequired
              }
            }
          });
        } else {
          await addSectionToAnnexTemplate({
            variables: {
              templateId,
              section: {
                title: editingSection.title,
                content: editingSection.content,
                orderIndex: editingSection.orderIndex,
                isRequired: editingSection.isRequired
              }
            }
          });
        }
        await refetchAnnexes();
      }
      setSuccess(editingSection.id ? 'Секцията е обновена' : 'Секцията е добавена');
      setOpenSectionDialog(false);
      setEditingSection(null);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const renderForm = () => {
    const isContracts = templateType === 'contracts';
    const isAnnexes = templateType === 'annexes';
    const isClauses = templateType === 'clauses';

    return (
      <Box component="form" onSubmit={(e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const data: Record<string, unknown> = {};
        
        if (isContracts) {
          data.name = formData.get('name');
          data.description = formData.get('description');
          data.contractType = formData.get('contractType');
          data.workHoursPerWeek = Number(formData.get('workHoursPerWeek'));
          data.probationMonths = Number(formData.get('probationMonths'));
          data.salaryCalculationType = formData.get('salaryCalculationType');
          data.paymentDay = Number(formData.get('paymentDay'));
          data.nightWorkRate = Number(formData.get('nightWorkRate'));
          data.overtimeRate = Number(formData.get('overtimeRate'));
          data.holidayRate = Number(formData.get('holidayRate'));
          data.workClass = formData.get('workClass') || null;
          data.positionId = formData.get('positionId') ? Number(formData.get('positionId')) : null;
          data.departmentId = formData.get('departmentId') ? Number(formData.get('departmentId')) : null;
          data.baseSalary = formData.get('baseSalary') ? Number(formData.get('baseSalary')) : null;
          data.clauseIds = selectedClauses.length > 0 ? JSON.stringify(selectedClauses.map(Number)) : null;
        } else if (isAnnexes) {
          data.name = formData.get('name');
          data.description = formData.get('description');
          data.changeType = formData.get('changeType');
          data.newBaseSalary = formData.get('newBaseSalary') ? Number(formData.get('newBaseSalary')) : null;
          data.newWorkHoursPerWeek = formData.get('newWorkHoursPerWeek') ? Number(formData.get('newWorkHoursPerWeek')) : null;
          data.newNightWorkRate = formData.get('newNightWorkRate') ? Number(formData.get('newNightWorkRate')) : null;
          data.newOvertimeRate = formData.get('newOvertimeRate') ? Number(formData.get('newOvertimeRate')) : null;
          data.newHolidayRate = formData.get('newHolidayRate') ? Number(formData.get('newHolidayRate')) : null;
        } else if (isClauses) {
          data.title = formData.get('title');
          data.content = formData.get('content');
          data.category = formData.get('category');
        }
        
        handleCreate(data);
      }}>
        <Grid container spacing={2}>
          {isContracts && (
            <>
              <Grid size={{ xs: 12 }}>
                <TextField name="name" label="Име на шаблона" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.name} />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField name="description" label="Описание" fullWidth defaultValue={(editingItem as ContractTemplate | null)?.description || ''} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField select name="contractType" label="Вид договор" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.contractType || 'full_time'}>
                  {contractTypes.map((t) => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField name="workHoursPerWeek" label="Работни часа/седмица" type="number" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.workHoursPerWeek || 40} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField name="probationMonths" label="Пробен период (месеци)" type="number" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.probationMonths || 6} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField name="paymentDay" label="Ден за плащане" type="number" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.paymentDay || 25} />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField name="nightWorkRate" label="Нощен труд (%)" type="number" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.nightWorkRate || 0.5} inputProps={{ step: 0.01 }} />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField name="overtimeRate" label="Извънреден труд (множ.)" type="number" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.overtimeRate || 1.5} inputProps={{ step: 0.1 }} />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField name="holidayRate" label="Празничен труд (множ.)" type="number" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.holidayRate || 2.0} inputProps={{ step: 0.1 }} />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField name="salaryCalculationType" select label="Начин на изчисляване" required fullWidth defaultValue={(editingItem as ContractTemplate | null)?.salaryCalculationType || 'gross'}>
                  <MenuItem value="gross">Брутно</MenuItem>
                  <MenuItem value="net">Нетно</MenuItem>
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField name="baseSalary" label="Основна заплата (лв.)" type="number" fullWidth defaultValue={(editingItem as ContractTemplate | null)?.baseSalary || ''} />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField select name="positionId" label="Длъжност" fullWidth value={(editingItem as ContractTemplate | null)?.position?.id || ''}>
                  <MenuItem value="">-- Избери --</MenuItem>
                  {positions.map((p) => <MenuItem key={p.id} value={p.id}>{p.title}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField select name="departmentId" label="Отдел" fullWidth value={(editingItem as ContractTemplate | null)?.department?.id || ''}>
                  <MenuItem value="">-- Избери --</MenuItem>
                  {departments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <FormControl fullWidth>
                  <InputLabel>Клаузи</InputLabel>
                  <Select
                    multiple
                    value={selectedClauses}
                    onChange={(e) => setSelectedClauses(e.target.value as string[])}
                    label="Клаузи"
                  >
                    {clauseData?.clauseTemplates?.map((clause: ClauseTemplate) => (
                      <MenuItem key={clause.id} value={String(clause.id)}>
                        {clause.title} ({clause.category})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </>
          )}
          {isAnnexes && (
            <>
              <Grid size={{ xs: 12 }}>
                <TextField name="name" label="Име на шаблона" required fullWidth defaultValue={(editingItem as AnnexTemplate | null)?.name} />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField name="description" label="Описание" fullWidth defaultValue={(editingItem as AnnexTemplate | null)?.description || ''} />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField select name="changeType" label="Вид промяна" required fullWidth defaultValue={(editingItem as AnnexTemplate | null)?.changeType || 'salary'}>
                  {changeTypes.map((t) => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField name="newBaseSalary" label="Нова заплата" type="number" fullWidth />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField name="newWorkHoursPerWeek" label="Нови часове/седмица" type="number" fullWidth />
              </Grid>
            </>
          )}
          {isClauses && (
            <>
              <Grid size={{ xs: 12 }}>
                <TextField name="title" label="Заглав" required fullWidth defaultValue={(editingItem as ClauseTemplate | null)?.title} />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField select name="category" label="Категория" required fullWidth defaultValue={(editingItem as ClauseTemplate | null)?.category || 'other'}>
                  {clauseCategories.map((c) => <MenuItem key={c.value} value={c.value}>{c.label}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField name="content" label="Съдържание" multiline rows={4} fullWidth defaultValue={(editingItem as ClauseTemplate | null)?.content || ''} />
              </Grid>
            </>
          )}
          <Grid size={{ xs: 12 }}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button variant="outlined" onClick={() => setOpenDialog(false)}>Отказ</Button>
              <Button variant="contained" type="submit">Запиши</Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    );
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">Шаблони</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditingItem(null); setOpenDialog(true); }}>
          Нов {templateType === 'contracts' ? 'шаблон' : templateType === 'annexes' ? 'шаблон за анекс' : 'клауза'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Box sx={{ mb: 3, display: 'flex', gap: 1 }}>
        <Button variant={templateType === 'contracts' ? 'contained' : 'outlined'} onClick={() => setTemplateType('contracts')}>
          Договори
        </Button>
        <Button variant={templateType === 'annexes' ? 'contained' : 'outlined'} onClick={() => setTemplateType('annexes')}>
          Анекси
        </Button>
        <Button variant={templateType === 'clauses' ? 'contained' : 'outlined'} onClick={() => setTemplateType('clauses')}>
          Клаузи
        </Button>
      </Box>

      {templateType === 'contracts' && (
        <Box>
          {contractLoading ? <CircularProgress /> : (
            contractData?.contractTemplates?.length === 0 ? (
              <Alert severity="info">Няма създадени шаблони за договори</Alert>
            ) : (
              contractData?.contractTemplates?.map((template: ContractTemplate) => (
                <Card key={template.id} variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="h6">{template.name}</Typography>
                        <Typography variant="body2" color="text.secondary">{template.description}</Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {template.workHoursPerWeek} часа/седмица | {template.contractType}
                        </Typography>
                        {template.currentVersion && (
                          <Typography variant="caption" color="info.main">
                            Версия {template.currentVersion.version} {template.currentVersion.isCurrent ? '(активна)' : ''}
                          </Typography>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button size="small" variant="outlined" onClick={() => setPreviewTemplate(template)}>Преглед</Button>
                        <Button size="small" variant="outlined" onClick={() => handleOpenSectionDialog()}>Добав секция</Button>
                        <Button size="small" color="error" onClick={() => handleDelete(template.id)}>Изтрий</Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))
            )
          )}
        </Box>
      )}

      {templateType === 'annexes' && (
        <Box>
          {annexLoading ? <CircularProgress /> : (
            annexData?.annexTemplates?.length === 0 ? (
              <Alert severity="info">Няма създадени шаблони за анекси</Alert>
            ) : (
              annexData?.annexTemplates?.map((template: AnnexTemplate) => (
                <Card key={template.id} variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="h6">{template.name}</Typography>
                        <Typography variant="body2" color="text.secondary">{template.description}</Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Вид промяна: {template.changeType}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button size="small" variant="outlined" onClick={() => handleOpenSectionDialog()}>Добав секция</Button>
                        <Button size="small" color="error" onClick={() => handleDelete(template.id)}>Изтрий</Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))
            )
          )}
        </Box>
      )}

      {templateType === 'clauses' && (
        <Box>
          {clauseLoading ? <CircularProgress /> : (
            clauseData?.clauseTemplates?.length === 0 ? (
              <Alert severity="info">Няма създадени клаузи</Alert>
            ) : (
              clauseData?.clauseTemplates?.map((clause: ClauseTemplate) => (
                <Card key={clause.id} variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="h6">{clause.title}</Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{clause.content}</Typography>
                        <Chip label={clause.category} size="small" />
                      </Box>
                      <Box>
                        <Button size="small" color="error" onClick={() => handleDelete(clause.id)}>Изтрий</Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))
            )
          )}
        </Box>
      )}

      {openDialog && (
        <Card sx={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 1000, width: '90%', maxWidth: 600, maxHeight: '90vh', overflow: 'auto' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {editingItem ? 'Редактирай' : 'Създай нов'} {templateType === 'contracts' ? 'шаблон' : templateType === 'annexes' ? 'шаблон за анекс' : 'клауза'}
            </Typography>
            {renderForm()}
          </CardContent>
        </Card>
      )}
      {openDialog && <Box sx={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, bgcolor: 'rgba(0,0,0,0.5)', zIndex: 999 }} onClick={() => setOpenDialog(false)} />}

      {/* Section Dialog */}
      {openSectionDialog && editingSection && (
        <Card sx={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 1000, width: '90%', maxWidth: 600, maxHeight: '90vh', overflow: 'auto' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {editingSection.id ? 'Редактирай секция' : 'Нова секция'}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Заглав"
                value={editingSection.title}
                onChange={(e) => setEditingSection({ ...editingSection, title: e.target.value })}
                fullWidth
              />
              <TextField
                label="Съдържание"
                value={editingSection.content}
                onChange={(e) => setEditingSection({ ...editingSection, content: e.target.value })}
                multiline
                rows={4}
                fullWidth
              />
              <TextField
                label="Ред"
                type="number"
                value={editingSection.orderIndex}
                onChange={(e) => setEditingSection({ ...editingSection, orderIndex: parseInt(e.target.value) || 0 })}
                fullWidth
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={editingSection.isRequired}
                    onChange={(e) => setEditingSection({ ...editingSection, isRequired: e.target.checked })}
                  />
                }
                label="Задължителна секция"
              />
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button variant="outlined" onClick={() => { setOpenSectionDialog(false); setEditingSection(null); }}>
                  Отказ
                </Button>
                <Button variant="contained" onClick={() => {
                  const selectedTemplate = templateType === 'contracts' 
                    ? contractData?.contractTemplates?.[0] 
                    : annexData?.annexTemplates?.[0];
                  if (selectedTemplate?.id) {
                    handleSaveSection(selectedTemplate.id);
                  }
                }}>
                  Запиши
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}
      {openSectionDialog && <Box sx={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, bgcolor: 'rgba(0,0,0,0.5)', zIndex: 999 }} onClick={() => { setOpenSectionDialog(false); setEditingSection(null); }} />}

      {/* Preview Dialog */}
      <Dialog open={!!previewTemplate} onClose={() => setPreviewTemplate(null)} maxWidth="md" fullWidth>
        <DialogTitle>
          Преглед на шаблон: {previewTemplate?.name}
        </DialogTitle>
        <DialogContent>
          {!previewTemplate?.currentVersion?.sections || previewTemplate.currentVersion.sections.length === 0 ? (
            <Alert severity="warning">Няма секции в този шаблон</Alert>
          ) : (
            <Box>
              {[...previewTemplate.currentVersion.sections]
                .sort((a: any, b: any) => a.orderIndex - b.orderIndex)
                .map((section: any, index: number) => (
                  <Box key={section.id || index} sx={{ mb: 3, pb: 2, borderBottom: '1px solid #eee' }}>
                    <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                      {index + 1}. {section.title}
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {section.content}
                    </Typography>
                    {section.isRequired && (
                      <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
                        Задължителна секция
                      </Typography>
                    )}
                  </Box>
                ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewTemplate(null)}>Затвори</Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};

// --- Component: Annexes Settings ---
const AnnexesSettings: React.FC = () => {
  const { currency } = useCurrency();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [openAnnexDialog, setOpenAnnexDialog] = useState(false);
  const [selectedContractId, setSelectedContractId] = useState<number | ''>('');
  const [annexForm, setAnnexForm] = useState({
    annexNumber: '',
    effectiveDate: new Date().toISOString().split('T')[0],
    baseSalary: '',
    workHoursPerWeek: '',
    nightWorkRate: '',
    overtimeRate: '',
    holidayRate: ''
  });

  const { data: annexData, loading: annexLoading, refetch: refetchAnnexes } = useQuery(GET_ANNEXES, {
    variables: { status: statusFilter }
  });

  const { data: contractData } = useQuery(GET_CONTRACTS);

  const [signAnnex] = useMutation(SIGN_CONTRACT_ANNEX);
  const [createAnnex] = useMutation(CREATE_CONTRACT_ANNEX);

  const handleSign = async (annexId: number) => {
    setError(null);
    try {
      await signAnnex({ variables: { annexId } });
      setSuccess('Анексът е подписан');
      await refetchAnnexes();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleCreateAnnex = async () => {
    if (!selectedContractId) {
      setError('Моля, изберете договор');
      return;
    }
    setError(null);
    try {
      await createAnnex({
        variables: {
          contractId: selectedContractId,
          effectiveDate: annexForm.effectiveDate,
          annexNumber: annexForm.annexNumber || null,
          baseSalary: annexForm.baseSalary ? parseFloat(annexForm.baseSalary) : null,
          workHoursPerWeek: annexForm.workHoursPerWeek ? parseInt(annexForm.workHoursPerWeek) : null,
          nightWorkRate: annexForm.nightWorkRate ? parseFloat(annexForm.nightWorkRate) : null,
          overtimeRate: annexForm.overtimeRate ? parseFloat(annexForm.overtimeRate) : null,
          holidayRate: annexForm.holidayRate ? parseFloat(annexForm.holidayRate) : null
        }
      });
      setSuccess('Анексът е създаден успешно');
      setOpenAnnexDialog(false);
      setSelectedContractId('');
      setAnnexForm({
        annexNumber: '',
        effectiveDate: new Date().toISOString().split('T')[0],
        baseSalary: '',
        workHoursPerWeek: '',
        nightWorkRate: '',
        overtimeRate: '',
        holidayRate: ''
      });
      await refetchAnnexes();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'draft': return 'default';
      case 'pending': return 'warning';
      case 'signed': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'draft': return 'Чернова';
      case 'pending': return 'Чакащ';
      case 'signed': return 'Подписан';
      case 'rejected': return 'Отхвърлен';
      default: return status;
    }
  };

  const activeContracts = contractData?.users?.users?.filter((u: User) => u.employmentContract?.isActive) || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight="bold">Допълнителни споразумения (Анекси)</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenAnnexDialog(true)}>
          Нов анекс
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Box sx={{ mb: 3, display: 'flex', gap: 1 }}>
        <Button variant={statusFilter === null ? 'contained' : 'outlined'} onClick={() => setStatusFilter(null)}>
          Всички
        </Button>
        <Button variant={statusFilter === 'draft' ? 'contained' : 'outlined'} onClick={() => setStatusFilter('draft')}>
          Чернови
        </Button>
        <Button variant={statusFilter === 'pending' ? 'contained' : 'outlined'} onClick={() => setStatusFilter('pending')}>
          Чакащи
        </Button>
        <Button variant={statusFilter === 'signed' ? 'contained' : 'outlined'} onClick={() => setStatusFilter('signed')}>
          Подписани
        </Button>
      </Box>

      {annexLoading ? <CircularProgress /> : (
        annexData?.annexes?.length === 0 ? (
          <Alert severity="info">Няма намерени анекси</Alert>
        ) : (
          annexData?.annexes?.map((annex: ContractAnnex) => (
            <Card key={annex.id} variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography variant="h6">
                      Анекс №{annex.annexNumber || annex.id}
                      <Chip 
                        label={getStatusLabel(annex.status)} 
                        size="small" 
                        color={getStatusColor(annex.status)} 
                        sx={{ ml: 1 }} 
                      />
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Дата: {annex.effectiveDate}
                    </Typography>
                    {annex.changeType && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        Вид: {annex.changeType}
                      </Typography>
                    )}
                    {annex.baseSalary && (
                      <Typography variant="body2" color="primary.main">
                        Нова заплата: {formatCurrencyValue(annex.baseSalary, currency)}
                      </Typography>
                    )}
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button 
                      size="small" 
                      variant="outlined" 
                      startIcon={<PrintIcon />}
                      onClick={() => {
                        const printWindow = window.open(`/api/export/trz/annex/${annex.id}/pdf`, '_blank');
                        printWindow?.addEventListener('load', () => {
                          printWindow.print();
                        });
                      }}
                    >
                      Принтирай
                    </Button>
                    <Button 
                      size="small" 
                      variant="outlined" 
                      startIcon={<FileDownloadIcon />}
                      component="a"
                      href={`/api/export/trz/annex/${annex.id}/pdf`}
                      target="_blank"
                    >
                      PDF
                    </Button>
                    {!annex.isSigned && annex.status !== 'signed' && (
                      <Button size="small" variant="contained" onClick={() => handleSign(annex.id)}>
                        Подпиши
                      </Button>
                    )}
                    {annex.isSigned && (
                      <Typography variant="body2" color="success.main">
                        Подписан: {annex.signedAt ? new Date(annex.signedAt).toLocaleDateString() : ''}
                      </Typography>
                    )}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))
        )
      )}

      {/* New Annex Dialog */}
      <Dialog open={openAnnexDialog} onClose={() => setOpenAnnexDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Създаване на нов анекс</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Изберете договор</InputLabel>
              <Select
                value={selectedContractId}
                label="Изберете договор"
                onChange={(e) => setSelectedContractId(e.target.value as number)}
              >
                {activeContracts.map((user: User) => (
                  <MenuItem key={user.employmentContract?.id} value={user.employmentContract?.id}>
                    {user.firstName} {user.lastName} - Договор №{user.employmentContract?.contractNumber}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Номер на анекс"
              value={annexForm.annexNumber}
              onChange={(e) => setAnnexForm({ ...annexForm, annexNumber: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Дата на влизане в сила"
              type="date"
              value={annexForm.effectiveDate}
              onChange={(e) => setAnnexForm({ ...annexForm, effectiveDate: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Нова базова заплата"
              type="number"
              value={annexForm.baseSalary}
              onChange={(e) => setAnnexForm({ ...annexForm, baseSalary: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Работни часове/седмица"
              type="number"
              value={annexForm.workHoursPerWeek}
              onChange={(e) => setAnnexForm({ ...annexForm, workHoursPerWeek: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Процент нощен труд"
              type="number"
              value={annexForm.nightWorkRate}
              onChange={(e) => setAnnexForm({ ...annexForm, nightWorkRate: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Множител извънреден труд"
              type="number"
              value={annexForm.overtimeRate}
              onChange={(e) => setAnnexForm({ ...annexForm, overtimeRate: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Множител празничен труд"
              type="number"
              value={annexForm.holidayRate}
              onChange={(e) => setAnnexForm({ ...annexForm, holidayRate: e.target.value })}
              sx={{ mb: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAnnexDialog(false)}>Отказ</Button>
          <Button onClick={handleCreateAnnex} variant="contained">Създай</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PayrollPage;