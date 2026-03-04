import React, { useState } from 'react';
import { 
  TextField, Button, Box, Alert, CircularProgress, 
  MenuItem, FormControl, InputLabel, Select, Grid,
  FormControlLabel, Checkbox
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { gql, useMutation, useQuery } from '@apollo/client';
import PersonIcon from '@mui/icons-material/Person';

// Zod schema for validation
const createUserSchema = z.object({
  email: z.string().email('Невалиден имейл адрес').optional().or(z.literal('')),
  username: z.string().min(3, 'Потребителското име трябва да е поне 3 символа').optional().or(z.literal('')),
  password: z.string().min(8, 'Паролата трябва да е поне 8 символа'),
  firstName: z.string().optional().or(z.literal('')),
  lastName: z.string().optional().or(z.literal('')),
  phoneNumber: z.string().optional().or(z.literal('')),
  address: z.string().optional().or(z.literal('')),
  egn: z.string().max(10).optional().or(z.literal('')),
  birthDate: z.string().optional().or(z.literal('')),
  iban: z.string().optional().or(z.literal('')),
  roleId: z.number().nullable().optional(),
  companyId: z.number().nullable().optional(),
  departmentId: z.number().nullable().optional(),
  positionId: z.number().nullable().optional(),
  contractType: z.string().optional().or(z.literal('')),
  contractStartDate: z.string().optional().or(z.literal('')),
  contractEndDate: z.string().nullable().optional().or(z.literal('')),
  baseSalary: z.number().nullable().optional(),
  hasIncomeTax: z.boolean().optional(),
  salaryInstallmentsCount: z.number().min(1),
  monthlyAdvanceAmount: z.number().min(0),
  taxResident: z.boolean(),
});

interface CreateUserFormData {
  email?: string;
  username?: string;
  password: string;
  firstName?: string;
  lastName?: string;
  phoneNumber?: string;
  address?: string;
  egn?: string;
  birthDate?: string;
  iban?: string;
  roleId?: number | null;
  companyId?: number | null;
  departmentId?: number | null;
  positionId?: number | null;
  contractType?: string;
  contractStartDate?: string;
  contractEndDate?: string | null;
  baseSalary?: number | null;
  hasIncomeTax?: boolean;
  salaryInstallmentsCount: number;
  monthlyAdvanceAmount: number;
  taxResident: boolean;
}

// GraphQL Mutations & Queries
const CREATE_USER_MUTATION = gql`
  mutation CreateUser(
    $email: String
    $username: String
    $password: String!
    $firstName: String
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
    $contractType: String
    $contractStartDate: Date
    $contractEndDate: Date
    $baseSalary: Decimal
    $hasIncomeTax: Boolean
    $salaryInstallmentsCount: Int
    $monthlyAdvanceAmount: Decimal
    $taxResident: Boolean
  ) {
    createUser(
      userInput: { 
        email: $email
        username: $username
        password: $password
        firstName: $firstName
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
        contractType: $contractType
        contractStartDate: $contractStartDate
        contractEndDate: $contractEndDate
        baseSalary: $baseSalary
        hasIncomeTax: $hasIncomeTax
        salaryInstallmentsCount: $salaryInstallmentsCount
        monthlyAdvanceAmount: $monthlyAdvanceAmount
        taxResident: $taxResident
      }
    ) {
      id
      email
    }
  }
`;

const GET_ORG_DATA = gql`
  query GetOrgData {
    companies { id name }
    departments { id name companyId }
    positions { id title departmentId }
    roles { id name description }
  }
`;

interface CreateUserFormProps {
  onCreated?: () => void;
}

const CreateUserForm: React.FC<CreateUserFormProps> = ({ onCreated }) => {
  const [apiError, setApiError] = useState('');
  const [apiSuccess, setApiSuccess] = useState('');

  const { data: orgData, loading: orgLoading } = useQuery(GET_ORG_DATA);

  const {
    register,
    handleSubmit,
    reset,
    control,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: '',
      username: '',
      password: '',
      firstName: '',
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
      contractType: 'full_time',
      contractStartDate: new Date().toISOString().split('T')[0],
      contractEndDate: '',
      baseSalary: null,
      hasIncomeTax: true,
      salaryInstallmentsCount: 1,
      monthlyAdvanceAmount: 0,
      taxResident: true,
    },
  });

  const selectedCompanyId = watch('companyId');
  const selectedDepartmentId = watch('departmentId');

  const filteredDepartments = orgData?.departments.filter((d: any) => 
    selectedCompanyId ? d.companyId === selectedCompanyId : true
  ) || [];

  const filteredPositions = orgData?.positions.filter((p: any) => 
    selectedDepartmentId ? p.departmentId === selectedDepartmentId : true
  ) || [];

  const [createUser] = useMutation(CREATE_USER_MUTATION);

  const onSubmit = async (data: CreateUserFormData) => {
    setApiError('');
    setApiSuccess('');
    try {
      await createUser({
        variables: {
          ...data,
          firstName: data.firstName || null,
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
          contractType: data.contractType || null,
          contractStartDate: data.contractStartDate || null,
          contractEndDate: data.contractEndDate || null,
          baseSalary: data.baseSalary || null,
          hasIncomeTax: data.hasIncomeTax ?? true,
          salaryInstallmentsCount: parseInt(data.salaryInstallmentsCount.toString()),
          monthlyAdvanceAmount: parseFloat(data.monthlyAdvanceAmount.toString()),
          taxResident: data.taxResident ?? true,
        },
      });
      setApiSuccess('Потребителят е създаден успешно!');
      reset();
      if (onCreated) onCreated();
    } catch (err: any) {
      setApiError(err.message);
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
        
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Първо име"
            {...register('firstName')}
            error={!!errors.firstName} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Фамилия"
            {...register('lastName')}
            error={!!errors.lastName} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="ЕГН"
            {...register('egn')} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Телефон"
            {...register('phoneNumber')} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Дата на раждане" type="date"
            {...register('birthDate')} InputLabelProps={{ shrink: true }} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="IBAN"
            {...register('iban')} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12 }}>
          <TextField
            fullWidth label="Адрес"
            {...register('address')} size="small"
          />
        </Grid>

        {/* --- СЕКЦИЯ 2: АКАУНТ И РОЛЯ --- */}
        <Grid size={{ xs: 12 }} sx={{ mt: 2 }}>
          <Alert severity="info" variant="outlined" icon={false}>Акаунт и Достъп</Alert>
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth label="Потребителско име"
            {...register('username')}
            error={!!errors.username}
            helperText={errors.username?.message}
            size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth label="Имейл адрес"
            {...register('email')} error={!!errors.email} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            required fullWidth label="Парола" type="password"
            {...register('password')} error={!!errors.password} size="small"
          />
        </Grid>

        <Grid size={{ xs: 12 }}>
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
                  {orgData?.roles.map((role: any) => {
                    const roleTranslations: Record<string, string> = {
                      'admin': 'Администратор',
                      'super_admin': 'Главен Администратор',
                      'user': 'Служител',
                      'accountant': 'Счетоводител',
                      'manager': 'Мениджър',
                      'kiosk': 'Терминал (Kiosk)'
                    };
                    // Priority: Translation -> Description -> Uppercase Name
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

        {/* --- СЕКЦИЯ 3: ОРГАНИЗАЦИОННИ --- */}
        <Grid size={{ xs: 12, sm: 4 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Фирма</InputLabel>
            <Controller
              name="companyId"
              control={control}
              render={({ field }) => (
                <Select {...field} label="Фирма" value={field.value ?? ''}>
                  <MenuItem value=""><em>Няма</em></MenuItem>
                  {orgData?.companies.map((c: any) => (
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
                <Select {...field} label="Отдел" value={field.value ?? ''}>
                  <MenuItem value=""><em>Няма</em></MenuItem>
                  {filteredDepartments.map((d: any) => (
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
                <Select {...field} label="Длъжност" value={field.value ?? ''}>
                  <MenuItem value=""><em>Няма</em></MenuItem>
                  {filteredPositions.map((p: any) => (
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

        <Grid size={{ xs: 12, sm: 6 }}>
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
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Основна заплата" type="number"
            {...register('baseSalary', { valueAsNumber: true })}
            error={!!errors.baseSalary}
            helperText={errors.baseSalary?.message}
            size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Дата на започване" type="date"
            InputLabelProps={{ shrink: true }}
            {...register('contractStartDate')} size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth label="Дата на изтичане" type="date"
            InputLabelProps={{ shrink: true }}
            {...register('contractEndDate')} size="small"
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
        <Grid size={{ xs: 12, sm: 4 }} display="flex" alignItems="center">
          <FormControlLabel
            control={<Controller name="taxResident" control={control} render={({ field }) => <Checkbox {...field} checked={field.value} />} />}
            label="Данъчен резидент"
          />
        </Grid>
        <Grid size={{ xs: 12 }}>
          <FormControlLabel
            control={<Controller name="hasIncomeTax" control={control} render={({ field }) => <Checkbox {...field} checked={field.value} />} />}
            label="Удържай ДОД (10%)"
          />
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
    </Box>
  );
};

export default CreateUserForm;
