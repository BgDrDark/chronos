import React, { useState } from 'react';
import { 
  TextField, Button, Box, Alert, CircularProgress, 
  MenuItem, FormControl, InputLabel, Select, Grid,
  Checkbox, Dialog, DialogTitle, DialogContent, DialogActions,
  IconButton, Typography, InputAdornment, OutlinedInput
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { gql, useMutation, useQuery } from '@apollo/client';
import PersonIcon from '@mui/icons-material/Person';
import { InfoIcon } from './ui/InfoIcon';
import { userFieldsHelp } from './ui/fieldsHelpText';

const CREATE_COMPANY_MUTATION = gql`
  mutation CreateCompany($input: CompanyCreateInput!) {
    createCompany(input: $input) {
      id
      name
    }
  }
`;

const CREATE_DEPARTMENT_MUTATION = gql`
  mutation CreateDepartment($input: DepartmentCreateInput!) {
    createDepartment(input: $input) {
      id
      name
    }
  }
`;

const CREATE_POSITION_MUTATION = gql`
  mutation CreatePosition($title: String!, $departmentId: Int!) {
    createPosition(title: $title, departmentId: $departmentId) {
      id
      title
    }
  }
`;

const GET_ORG_DATA = gql`
  query GetOrgData {
    roles {
      id
      name
      description
    }
    companies {
      id
      name
    }
    departments {
      id
      name
      companyId
    }
    positions {
      id
      title
      departmentId
    }
  }
`;

// Zod schema for validation
const createUserSchema = z.object({
  email: z.string().email('Невалиден имейл адрес'),
  username: z.string().min(3, 'Потребителското име трябва да е поне 3 символа').optional().or(z.literal('')),
  password: z.string().min(8, 'Паролата трябва да е поне 8 символа'),
  firstName: z.string().min(1, 'Полето е задължително'),
  surname: z.string().optional().or(z.literal('')),
  lastName: z.string().min(1, 'Полето е задължително'),
  phoneNumber: z.string()
    .optional()
    .or(z.literal(''))
    .refine((val) => !val || /^(\+?359|0)[89]\d{7,8}$/.test(val), {
      message: 'Невалиден телефонен номер (очакван формат: +359888123456, 0888123456 или 359888123456)'
    }),
  address: z.string().optional().or(z.literal('')),
  egn: z.string().max(10).optional().or(z.literal('')),
  birthDate: z.string().optional().or(z.literal('')),
  iban: z.string().optional().or(z.literal('')),
  roleId: z.number().nullable().optional(),
  companyId: z.number().nullable().optional(),
  departmentId: z.number().nullable().optional(),
  positionId: z.number().nullable().optional(),
  passwordForceChange: z.boolean().optional(),
  contractType: z.string().optional().or(z.literal('')),
  contractNumber: z.string().optional().or(z.literal('')),
  contractStartDate: z.string().optional().or(z.literal('')),
  contractEndDate: z.string().nullable().optional().or(z.literal('')),
  baseSalary: z.number().nullable().optional(),
  workHoursPerWeek: z.number().min(1).max(168).optional(),
  probationMonths: z.number().min(0).max(12).optional(),
  salaryCalculationType: z.string().optional(),
  hasIncomeTax: z.boolean().optional(),
  insuranceContributor: z.boolean().optional(),
  salaryInstallmentsCount: z.number().min(1),
  monthlyAdvanceAmount: z.number().min(0),
  taxResident: z.boolean(),
  paymentDay: z.number().min(1).max(31).optional(),
  // TRZ Extension
  nightWorkRate: z.number().min(0).optional(),
  overtimeRate: z.number().min(0).optional(),
  holidayRate: z.number().min(0).optional(),
  workClass: z.string().optional().or(z.literal('')),
  dangerousWork: z.boolean().optional(),
});

interface CreateUserFormData {
  email: string;
  username?: string;
  password: string;
  firstName: string;
  surname?: string;
  lastName: string;
  phoneNumber?: string;
  address?: string;
  egn?: string;
  birthDate?: string;
  iban?: string;
  roleId?: number | null;
  companyId?: number | null;
  departmentId?: number | null;
  positionId?: number | null;
  passwordForceChange?: boolean;
  contractType?: string;
  contractNumber?: string;
  contractStartDate?: string;
  contractEndDate?: string | null;
  baseSalary?: number | null;
  workHoursPerWeek?: number;
  probationMonths?: number;
  salaryCalculationType?: string;
  hasIncomeTax?: boolean;
  insuranceContributor?: boolean;
  salaryInstallmentsCount: number;
  monthlyAdvanceAmount: number;
  taxResident: boolean;
  paymentDay?: number;
  // TRZ Extension
  nightWorkRate?: number;
  overtimeRate?: number;
  holidayRate?: number;
  workClass?: string;
  dangerousWork?: boolean;
}

// GraphQL Mutations & Queries
const CREATE_USER_MUTATION = gql`
  mutation CreateUser(
    $email: String!
    $username: String
    $password: String!
    $firstName: String
    $surname: String
    $lastName: String
    $phoneNumber: String
    $address: String
    $egn: String
    $birthDate: Date
    $iban: String
    $roleId: Int
    $companyId: Int
    $departmentId: Int
    $positionId: Int
    $passwordForceChange: Boolean
    $contractType: String
    $contractNumber: String
    $contractStartDate: Date
    $contractEndDate: Date
    $baseSalary: Decimal
    $workHoursPerWeek: Int
    $probationMonths: Int
    $salaryCalculationType: String
    $hasIncomeTax: Boolean
    $insuranceContributor: Boolean
    $salaryInstallmentsCount: Int
    $monthlyAdvanceAmount: Decimal
    $taxResident: Boolean
    $paymentDay: Int
    $nightWorkRate: Decimal
    $overtimeRate: Decimal
    $holidayRate: Decimal
    $workClass: String
    $dangerousWork: Boolean
  ) {
    createUser(
      userInput: { 
        email: $email
        username: $username
        password: $password
        firstName: $firstName
        surname: $surname
        lastName: $lastName
        phoneNumber: $phoneNumber
        address: $address
        egn: $egn
        birthDate: $birthDate
        iban: $iban
        roleId: $roleId
        companyId: $companyId
        departmentId: $departmentId
        positionId: $positionId
        passwordForceChange: $passwordForceChange
        contractType: $contractType
        contractNumber: $contractNumber
        contractStartDate: $contractStartDate
        contractEndDate: $contractEndDate
        baseSalary: $baseSalary
        workHoursPerWeek: $workHoursPerWeek
        probationMonths: $probationMonths
        salaryCalculationType: $salaryCalculationType
        hasIncomeTax: $hasIncomeTax
        insuranceContributor: $insuranceContributor
        salaryInstallmentsCount: $salaryInstallmentsCount
        monthlyAdvanceAmount: $monthlyAdvanceAmount
        taxResident: $taxResident
        paymentDay: $paymentDay
        nightWorkRate: $nightWorkRate
        overtimeRate: $overtimeRate
        holidayRate: $holidayRate
        workClass: $workClass
        dangerousWork: $dangerousWork
      }
    ) {
      id
      email
    }
  }
`;

interface CreateUserFormProps {
  onCreated?: () => void;
}

interface OrgData {
  companies: Array<{ id: number; name: string }>;
  departments: Array<{ id: number; name: string; companyId: number }>;
  positions: Array<{ id: number; title: string; departmentId: number }>;
  roles: Array<{ id: number; name: string; description?: string }>;
}

const CreateUserForm: React.FC<CreateUserFormProps> = ({ onCreated }) => {
  const [apiError, setApiError] = useState('');
  const [apiSuccess, setApiSuccess] = useState('');

  const [companyDialogOpen, setCompanyDialogOpen] = useState(false);
  const [departmentDialogOpen, setDepartmentDialogOpen] = useState(false);
  const [positionDialogOpen, setPositionDialogOpen] = useState(false);

  const [companyForm, setCompanyForm] = useState({ name: '', eik: '', bulstat: '', address: '', molName: '' });
  const [departmentForm, setDepartmentForm] = useState({ name: '', companyId: '' });
  const [positionForm, setPositionForm] = useState({ title: '', departmentId: '' });

  const [savingCompany, setSavingCompany] = useState(false);
  const [savingDepartment, setSavingDepartment] = useState(false);
  const [savingPosition, setSavingPosition] = useState(false);

  // Local state for checkboxes (like FleetPage - direct onChange)
  const [passwordForceChange, setPasswordForceChange] = useState(false);
  const [taxResident, setTaxResident] = useState(true);
  const [hasIncomeTax, setHasIncomeTax] = useState(true);
  const [insuranceContributor, setInsuranceContributor] = useState(true);
  const [dangerousWork, setDangerousWork] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | null>(null);

  const { data: orgData, loading: orgLoading, refetch: refetchOrg } = useQuery<OrgData>(GET_ORG_DATA);

  const [createCompany] = useMutation(CREATE_COMPANY_MUTATION);
  const [createDepartment] = useMutation(CREATE_DEPARTMENT_MUTATION);
  const [createPosition] = useMutation(CREATE_POSITION_MUTATION);

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: '',
      username: '',
      password: '',
      firstName: '',
      surname: '',
      lastName: '',
      phoneNumber: '',
      address: '',
      egn: '',
      birthDate: '',
      iban: '',
      roleId: null,
      companyId: null,
      departmentId: null,
      positionId: null,
      passwordForceChange: false,
      contractType: 'full_time',
      contractNumber: '',
      contractStartDate: new Date().toISOString().split('T')[0],
      contractEndDate: '',
      baseSalary: null,
      workHoursPerWeek: 40,
      probationMonths: 6,
      salaryCalculationType: 'gross',
      hasIncomeTax: true,
      insuranceContributor: true,
      salaryInstallmentsCount: 1,
      monthlyAdvanceAmount: 0,
      taxResident: true,
      paymentDay: 25,
      // TRZ Defaults
      nightWorkRate: 0.50,
      overtimeRate: 1.50,
      holidayRate: 2.00,
      workClass: '',
      dangerousWork: false,
    },
  });

  const filteredDepartments = orgData?.departments.filter((d) => 
    selectedCompanyId ? d.companyId === selectedCompanyId : true
  ) || [];

  const filteredPositions = orgData?.positions.filter((p) => 
    selectedDepartmentId ? p.departmentId === selectedDepartmentId : true
  ) || [];

  const [createUser] = useMutation(CREATE_USER_MUTATION);

  const handleSaveCompany = async () => {
    if (!companyForm.name) return;
    setSavingCompany(true);
    try {
      const { data } = await createCompany({
        variables: {
          input: {
            name: companyForm.name,
            eik: companyForm.eik || null,
            bulstat: companyForm.bulstat || null,
            address: companyForm.address || null,
            molName: companyForm.molName || null,
          }
        }
      });
      if (data?.createCompany) {
        await refetchOrg();
        setCompanyDialogOpen(false);
        setCompanyForm({ name: '', eik: '', bulstat: '', address: '', molName: '' });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSavingCompany(false);
    }
  };

  const handleSaveDepartment = async () => {
    if (!departmentForm.name || !departmentForm.companyId) return;
    setSavingDepartment(true);
    try {
      const { data } = await createDepartment({
        variables: {
          input: {
            name: departmentForm.name,
            companyId: parseInt(departmentForm.companyId),
          }
        }
      });
      if (data?.createDepartment) {
        await refetchOrg();
        setDepartmentDialogOpen(false);
        setDepartmentForm({ name: '', companyId: '' });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSavingDepartment(false);
    }
  };

  const handleSavePosition = async () => {
    if (!positionForm.title || !positionForm.departmentId) return;
    setSavingPosition(true);
    try {
      const { data } = await createPosition({
        variables: {
          title: positionForm.title,
          departmentId: parseInt(positionForm.departmentId),
        }
      });
      if (data?.createPosition) {
        await refetchOrg();
        setPositionDialogOpen(false);
        setPositionForm({ title: '', departmentId: '' });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSavingPosition(false);
    }
  };

  const onSubmit = async (data: CreateUserFormData) => {
    setApiError('');
    setApiSuccess('');
    try {
      await createUser({
        variables: {
          ...data,
          firstName: data.firstName || null,
          surname: data.surname || null,
          lastName: data.lastName || null,
          egn: data.egn || null,
          phoneNumber: data.phoneNumber || null,
          birthDate: data.birthDate || null,
          iban: data.iban || null,
          address: data.address || null,
          username: data.username || null,
          email: data.email || null,
          roleId: data.roleId ? parseInt(data.roleId.toString()) : null,
          companyId: data.companyId || null,
          departmentId: data.departmentId || null,
          positionId: data.positionId || null,
          passwordForceChange: !!data.passwordForceChange,
          contractType: data.contractType || null,
          contractNumber: data.contractNumber || null,
          contractStartDate: data.contractStartDate || null,
          contractEndDate: data.contractEndDate || null,
          baseSalary: data.baseSalary || null,
          workHoursPerWeek: data.workHoursPerWeek ? parseInt(data.workHoursPerWeek.toString()) : 40,
          probationMonths: data.probationMonths ? parseInt(data.probationMonths.toString()) : 0,
          salaryCalculationType: data.salaryCalculationType || 'gross',
          hasIncomeTax: data.hasIncomeTax ?? true,
          insuranceContributor: data.insuranceContributor ?? true,
          salaryInstallmentsCount: parseInt(data.salaryInstallmentsCount.toString()),
          monthlyAdvanceAmount: parseFloat(data.monthlyAdvanceAmount.toString()),
          taxResident: data.taxResident ?? true,
          // TRZ fields
          paymentDay: data.paymentDay || 25,
          nightWorkRate: data.nightWorkRate ? parseFloat(data.nightWorkRate.toString()) : 0.50,
          overtimeRate: data.overtimeRate ? parseFloat(data.overtimeRate.toString()) : 1.50,
          holidayRate: data.holidayRate ? parseFloat(data.holidayRate.toString()) : 2.00,
          workClass: data.workClass || null,
          dangerousWork: !!data.dangerousWork,
        },
      });
      setApiSuccess('Потребителят е създаден успешно!');
      reset();
      if (onCreated) onCreated();
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Възникна грешка');
    }
  };

  if (orgLoading) return <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress size={24} /></Box>;

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ mt: 1 }}>
      <Grid container spacing={2}>
        {/* --- СЕКЦИЯ 1: ЛИЧНИ ДАННИ --- */}
        <Grid size={{ xs: 12 }}>
          <Alert severity="success" variant="outlined" icon={<PersonIcon fontSize="small" />}>
            Лични данни на служителя
          </Alert>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Първо име *"
            size="small"
            {...register('firstName')}
            error={!!errors.firstName}
            helperText={errors.firstName?.message}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.firstName} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Презиме"
            size="small"
            {...register('surname')}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.surname} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Фамилия *"
            size="small"
            {...register('lastName')}
            error={!!errors.lastName}
            helperText={errors.lastName?.message}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.lastName} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="ЕГН"
            size="small"
            {...register('egn')}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.egn} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Телефон"
            size="small"
            {...register('phoneNumber')}
            error={!!errors.phoneNumber}
            helperText={errors.phoneNumber?.message}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.phoneNumber} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Дата на раждане"
            type="date"
            InputLabelProps={{ shrink: true }}
            {...register('birthDate')}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.birthDate} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="IBAN"
            size="small"
            {...register('iban')}
            InputLabelProps={{ shrink: true }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.iban} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12 }}>
          <TextField
            fullWidth
            label="Адрес"
            size="small"
            {...register('address')}
            InputLabelProps={{ shrink: true }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.address} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>

        {/* --- СЕКЦИЯ 2: АКАУНТ И РОЛЯ --- */}
        <Grid size={{ xs: 12 }} sx={{ mt: 2 }}>
          <Alert severity="info" variant="outlined" icon={false}>Акаунт и Достъп</Alert>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Потребителско име"
            {...register('username')}
            error={!!errors.username}
            helperText={errors.username?.message}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.username} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            required
            fullWidth
            label="Имейл адрес"
            {...register('email')}
            error={!!errors.email}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.email} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            required
            fullWidth
            label="Парола"
            type="password"
            {...register('password')}
            error={!!errors.password}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.password} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 8 }}>
          <FormControl fullWidth size="small">
            <InputLabel id="role-label">Роля в системата</InputLabel>
            <Controller
              name="roleId"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  labelId="role-label"
                  label="Роля в системата"
                  value={field.value || ''}
                  onChange={(e) => field.onChange(e.target.value)}
                >
                  {orgData?.roles?.map((role) => {
                    const roleTranslations: Record<string, string> = {
                      'super_admin': 'Супер администратор',
                      'admin': 'Администратор',
                      'global_accountant': 'Главен счетоводител',
                      'accountant': 'Счетоводител',
                      'logistics_manager': 'Логистичен мениджър',
                      'fleet_manager': 'Мениджър автопарк',
                      'hr_manager': 'HR мениджър',
                      'manager': 'Мениджър',
                      'driver': 'Шофьор',
                      'employee': 'Служител',
                      'viewer': 'Наблюдател',
                      'kiosk': 'Терминал (Kiosk)'
                    };
                    const displayName = roleTranslations[role.name.toLowerCase()] || role.description || role.name.toUpperCase();
                    
                    return (
                      <MenuItem key={role.id} value={role.id}>
                        {displayName}
                      </MenuItem>
                    );
                  })}
                </Select>
              )}
            />
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Checkbox
              checked={passwordForceChange}
              onChange={(e) => setPasswordForceChange(e.target.checked)}
            />
            <Typography variant="body2">Задължителна смяна на парола</Typography>
          </Box>
        </Grid>

        {/* --- СЕКЦИЯ 3: ОРГАНИЗАЦИОННИ --- */}
        <Grid size={{ xs: 12, sm: 4 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Фирма</InputLabel>
            <Controller
              name="companyId"
              control={control}
              render={({ field }) => (
                <Select 
                  {...field} 
                  label="Фирма" 
                  value={field.value ?? ''} 
                  onChange={(e) => {
                    const value = e.target.value;
                    field.onChange(value);
                    setSelectedCompanyId(value ? Number(value) : null);
                    setSelectedDepartmentId(null);
                  }}
                  endAdornment={
                    <IconButton size="small" onClick={() => setCompanyDialogOpen(true)} sx={{ mr: 4 }}>
                      <AddIcon />
                    </IconButton>
                  }
                >
                  <MenuItem value=""><em>Няма</em></MenuItem>
                  {orgData?.companies.map((c) => (
                    <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                  ))}
                </Select>
              )}
            />
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Отдел</InputLabel>
            <Controller
              name="departmentId"
              control={control}
              render={({ field }) => (
                <Select 
                  {...field} 
                  label="Отдел" 
                  value={field.value ?? ''} 
                  onChange={(e) => {
                    const value = e.target.value;
                    field.onChange(value);
                    setSelectedDepartmentId(value ? Number(value) : null);
                  }}
                  endAdornment={
                    <IconButton size="small" onClick={() => setDepartmentDialogOpen(true)} sx={{ mr: 4 }}>
                      <AddIcon />
                    </IconButton>
                  }
                >
                  <MenuItem value=""><em>Няма</em></MenuItem>
                  {filteredDepartments.map((d) => (
                    <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>
                  ))}
                </Select>
              )}
            />
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Длъжност</InputLabel>
            <Controller
              name="positionId"
              control={control}
              render={({ field }) => (
                <Select {...field} label="Длъжност" value={field.value ?? ''} endAdornment={
                  <IconButton size="small" onClick={() => setPositionDialogOpen(true)} sx={{ mr: 4 }}>
                    <AddIcon />
                  </IconButton>
                }>
                  <MenuItem value=""><em>Няма</em></MenuItem>
                  {filteredPositions.map((p) => (
                    <MenuItem key={p.id} value={p.id}>{p.title}</MenuItem>
                  ))}
                </Select>
              )}
            />
          </FormControl>
        </Grid>

        {/* --- СЕКЦИЯ 4: ДОГОВОР И ЗАПЛАЩАНЕ --- */}
        <Grid size={{ xs: 12 }} sx={{ mt: 2 }}>
          <Alert severity="warning" variant="outlined" icon={false}>Договор и Финансови параметри</Alert>
        </Grid>

        <Grid size={{ xs: 12, sm: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Тип договор</InputLabel>
            <Controller
              name="contractType"
              control={control}
              render={({ field }) => (
                <Select {...field} label="Тип договор">
                  <MenuItem value="full_time">Пълно работно време</MenuItem>
                  <MenuItem value="part_time">Непълно работно време</MenuItem>
                  <MenuItem value="contractor">Граждански договор</MenuItem>
                  <MenuItem value="internship">Стажант</MenuItem>
                </Select>
              )}
            />
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <TextField
            fullWidth label="Дата на изплащане (ден от месеца)" type="number"
            {...register('paymentDay', { valueAsNumber: true })} size="small"
            inputProps={{ min: 1, max: 31 }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Вид изчисление</InputLabel>
            <Controller
              name="salaryCalculationType"
              control={control}
              render={({ field }) => (
                <Select {...field} label="Вид изчисление">
                  <MenuItem value="gross">Бруто</MenuItem>
                  <MenuItem value="net">Нето</MenuItem>
                </Select>
              )}
            />
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Основна заплата"
            type="number"
            {...register('baseSalary', { valueAsNumber: true })}
            error={!!errors.baseSalary}
            helperText={errors.baseSalary?.message}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.baseSalary} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 3 }}>
          <TextField
            fullWidth
            label="Часове/седмица"
            type="number"
            {...register('workHoursPerWeek', { valueAsNumber: true })}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.workHoursPerWeek} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <TextField
            fullWidth
            label="Изпитателен срок (мес.)"
            type="number"
            {...register('probationMonths', { valueAsNumber: true })}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.probationMonths} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <TextField
            fullWidth
            label="Дата на започване"
            type="date"
            InputLabelProps={{ shrink: true }}
            {...register('contractStartDate')}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.contractStartDate} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <TextField
            fullWidth
            label="Дата на изтичане"
            type="date"
            InputLabelProps={{ shrink: true }}
            {...register('contractEndDate')}
            size="small"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.contractEndDate} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth label="Брой вноски" type="number"
            {...register('salaryInstallmentsCount', { valueAsNumber: true })}
            size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth label="Фиксиран аванс" type="number"
            {...register('monthlyAdvanceAmount', { valueAsNumber: true })}
            size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Checkbox
              checked={taxResident}
              onChange={(e) => setTaxResident(e.target.checked)}
            />
            <Typography variant="body2">Данъчен резидент</Typography>
          </Box>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Checkbox
              checked={hasIncomeTax}
              onChange={(e) => setHasIncomeTax(e.target.checked)}
            />
            <Typography variant="body2">Удържай ДОД (10%)</Typography>
          </Box>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Checkbox
              checked={insuranceContributor}
              onChange={(e) => setInsuranceContributor(e.target.checked)}
            />
            <Typography variant="body2">Осигурено лице</Typography>
          </Box>
        </Grid>

        {/* --- СЕКЦИЯ 5: ТРЗ СПЕЦИФИЧНИ (НАДБАВКИ) --- */}
        <Grid size={{ xs: 12 }} sx={{ mt: 2 }}>
          <Alert severity="info" variant="outlined" icon={false}>ТРЗ Настройки (Ставки и Надбавки)</Alert>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Множител Нощен труд"
            type="number"
            {...register('nightWorkRate', { valueAsNumber: true })}
            size="small"
            helperText="Напр. 0.50 за +50%"
            InputLabelProps={{ shrink: true }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.nightWorkRate} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Множител Извънреден"
            type="number"
            {...register('overtimeRate', { valueAsNumber: true })}
            size="small"
            helperText="Напр. 1.50 за +50%"
            InputLabelProps={{ shrink: true }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.overtimeRate} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Множител Празник"
            type="number"
            {...register('holidayRate', { valueAsNumber: true })}
            size="small"
            helperText="Напр. 2.00 за +100%"
            InputLabelProps={{ shrink: true }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <InfoIcon helpText={userFieldsHelp.holidayRate} />
                  </InputAdornment>
                )
              }
            }}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Трудов клас / Категория"
            {...register('workClass')}
            size="small"
            placeholder="Напр. I, II, III"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Checkbox
              checked={dangerousWork}
              onChange={(e) => setDangerousWork(e.target.checked)}
            />
            <Typography variant="body2">Вредни условия на труд</Typography>
          </Box>
        </Grid>
      </Grid>

      {apiError && <Alert severity="error" sx={{ width: '100%', mt: 2 }}>{apiError}</Alert>}
      {apiSuccess && <Alert severity="success" sx={{ width: '100%', mt: 2 }}>{apiSuccess}</Alert>}
      
      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, mb: 2, py: 1.5, borderRadius: 2 }}
        disabled={isSubmitting}
      >
        {isSubmitting ? <CircularProgress size={24} color="inherit" /> : 'Създай потребител'}
      </Button>

      {/* Create Company Dialog */}
      <Dialog open={companyDialogOpen} onClose={() => setCompanyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова фирма</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Име *" value={companyForm.name} onChange={(e) => setCompanyForm({...companyForm, name: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="ЕИК" value={companyForm.eik} onChange={(e) => setCompanyForm({...companyForm, eik: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Булстат" value={companyForm.bulstat} onChange={(e) => setCompanyForm({...companyForm, bulstat: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Адрес" value={companyForm.address} onChange={(e) => setCompanyForm({...companyForm, address: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="МОЛ" value={companyForm.molName} onChange={(e) => setCompanyForm({...companyForm, molName: e.target.value})} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompanyDialogOpen(false)}>Отказ</Button>
          <Button onClick={handleSaveCompany} variant="contained" disabled={savingCompany || !companyForm.name}>
            {savingCompany ? <CircularProgress size={20} /> : 'Създай'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Department Dialog */}
      <Dialog open={departmentDialogOpen} onClose={() => setDepartmentDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нов отдел</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Име *" value={departmentForm.name} onChange={(e) => setDepartmentForm({...departmentForm, name: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Фирма *</InputLabel>
                <Select value={departmentForm.companyId} label="Фирма *" onChange={(e) => setDepartmentForm({...departmentForm, companyId: e.target.value as string})}>
                  {orgData?.companies.map((c) => (
                    <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDepartmentDialogOpen(false)}>Отказ</Button>
          <Button onClick={handleSaveDepartment} variant="contained" disabled={savingDepartment || !departmentForm.name || !departmentForm.companyId}>
            {savingDepartment ? <CircularProgress size={20} /> : 'Създай'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Position Dialog */}
      <Dialog open={positionDialogOpen} onClose={() => setPositionDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова длъжност</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Име *" value={positionForm.title} onChange={(e) => setPositionForm({...positionForm, title: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Отдел *</InputLabel>
                <Select value={positionForm.departmentId} label="Отдел *" onChange={(e) => setPositionForm({...positionForm, departmentId: e.target.value as string})}>
                  {filteredDepartments.map((d) => (
                    <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPositionDialogOpen(false)}>Отказ</Button>
          <Button onClick={handleSavePosition} variant="contained" disabled={savingPosition || !positionForm.title || !positionForm.departmentId}>
            {savingPosition ? <CircularProgress size={20} /> : 'Създай'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CreateUserForm;
