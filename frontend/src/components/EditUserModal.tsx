import React, { useState, useEffect } from 'react';
import {
  Modal,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Switch,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Grid,
  Checkbox
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { gql, useMutation, useQuery } from '@apollo/client';
import { type User, type Role, type Company, type Department, type Position, type UpdateUserInput } from '../types';

// Zod schema for validation
const updateUserSchema = z.object({
  id: z.number(),
  email: z.string().email('Невалиден имейл адрес').optional().or(z.literal('')),
  username: z.string().min(3, 'Потребителското име трябва да е поне 3 символа').optional().or(z.literal('')),
  password: z.string().optional().or(z.literal('')),
  firstName: z.string().optional().or(z.literal('')),
  surname: z.string().optional().or(z.literal('')),
  lastName: z.string().optional().or(z.literal('')),
  phoneNumber: z.string().optional().or(z.literal('')),
  address: z.string().optional().or(z.literal('')),
  egn: z.string().max(10).optional().or(z.literal('')),
  birthDate: z.string().optional().or(z.literal('')),
  iban: z.string().optional().or(z.literal('')),
  companyId: z.number().optional().nullable(),
  departmentId: z.number().optional().nullable(),
  positionId: z.number().optional().nullable(),
  roleId: z.number().optional().nullable(),
  isActive: z.boolean().optional(),
  passwordForceChange: z.boolean().optional(),
  // Contract fields
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
  // TRZ разширение
  paymentDay: z.number().min(1).max(31).optional(),
  nightWorkRate: z.number().min(0).optional(),
  overtimeRate: z.number().min(0).optional(),
  holidayRate: z.number().min(0).optional(),
  workClass: z.string().optional().or(z.literal('')),
  dangerousWork: z.boolean().optional(),
});

type UpdateUserFormData = z.infer<typeof updateUserSchema>;

const UPDATE_USER_MUTATION = gql`
  mutation UpdateUser($userInput: UpdateUserInput!) {
    updateUser(userInput: $userInput) {
      id
      email
      username
    }
  }
`;

const GET_DATA_QUERY = gql`
  query GetData {
    roles { id name description }
    companies { id name }
    departments { id name companyId }
    positions { id title departmentId }
  }
`;

interface EditUserModalProps {
  open: boolean;
  onClose: () => void;
  user: User | null;
  refetchUsers: () => void;
}

interface OrgData {
  roles: Role[];
  companies: Company[];
  departments: Department[];
  positions: Position[];
}

const style = {
  position: 'absolute' as const,
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: { xs: '95%', sm: 800 },
  maxHeight: '90vh',
  overflowY: 'auto',
  bgcolor: 'background.paper',
  borderRadius: 3,
  boxShadow: 24,
  p: 4,
};

const EditUserModal: React.FC<EditUserModalProps> = ({ open, onClose, user, refetchUsers }) => {
  const [apiError, setApiError] = useState('');

  // Local state for checkboxes (like FleetPage - direct onChange)
  const [isActive, setIsActive] = useState(true);
  const [passwordForceChange, setPasswordForceChange] = useState(false);
  const [taxResident, setTaxResident] = useState(true);
  const [hasIncomeTax, setHasIncomeTax] = useState(true);
  const [insuranceContributor, setInsuranceContributor] = useState(true);
  const [dangerousWork, setDangerousWork] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { isSubmitting },
  } = useForm<UpdateUserFormData>({
    resolver: zodResolver(updateUserSchema),
  });

  const [updateUser] = useMutation(UPDATE_USER_MUTATION);
  const { data: orgData, loading: dataLoading } = useQuery<OrgData>(GET_DATA_QUERY);

  useEffect(() => {
    if (user && open) {
      const contract = user.employmentContract;
      // Set local checkbox states from user data
      setIsActive(user.isActive ?? true);
      setPasswordForceChange(false);
      setTaxResident(true);
      setHasIncomeTax(contract?.hasIncomeTax ?? true);
      setInsuranceContributor(contract?.insuranceContributor ?? true);
      setDangerousWork(contract?.dangerousWork ?? false);
      
      reset({
        id: user.id ? Number(user.id) : undefined,
        email: '', // Keep email empty for privacy
        username: user.username || '',
        firstName: user.firstName || '',
        surname: user.surname || '',
        lastName: user.lastName || '',
        phoneNumber: user.phoneNumber || '',
        address: user.address || '',
        egn: user.egn || '',
        birthDate: user.birthDate || '',
        iban: user.iban || '',
        companyId: user.company?.id ? Number(user.company.id) : null,
        departmentId: user.department?.id ? Number(user.department.id) : null,
        positionId: user.position?.id ? Number(user.position.id) : null,
        roleId: user.role?.id ? Number(user.role.id) : null,
        isActive: user.isActive ?? true,
        passwordForceChange: user.passwordForceChange ?? false,
        password: '',
        // ТРЗ данни от employment contract
        contractType: contract?.contractType || 'full_time',
        contractNumber: contract?.contractNumber || '',
        contractStartDate: contract?.startDate || '',
        contractEndDate: contract?.endDate || '',
        baseSalary: contract?.baseSalary !== undefined && contract?.baseSalary !== null ? Number(contract.baseSalary) : null,
        workHoursPerWeek: contract?.workHoursPerWeek || 40,
        probationMonths: contract?.probationMonths || 0,
        salaryCalculationType: contract?.salaryCalculationType || 'gross',
        hasIncomeTax: contract?.hasIncomeTax ?? true,
        insuranceContributor: contract?.insuranceContributor ?? true,
        salaryInstallmentsCount: contract?.salaryInstallmentsCount || 1,
        monthlyAdvanceAmount: contract?.monthlyAdvanceAmount !== undefined && contract?.monthlyAdvanceAmount !== null ? Number(contract.monthlyAdvanceAmount) : 0,
        taxResident: contract?.taxResident ?? true,
        // ТРЗ Разширение
        paymentDay: contract?.paymentDay || 25,
        nightWorkRate: contract?.nightWorkRate !== undefined && contract?.nightWorkRate !== null ? Number(contract.nightWorkRate) : 0.50,
        overtimeRate: contract?.overtimeRate !== undefined && contract?.overtimeRate !== null ? Number(contract.overtimeRate) : 1.50,
        holidayRate: contract?.holidayRate !== undefined && contract?.holidayRate !== null ? Number(contract.holidayRate) : 2.00,
        workClass: contract?.workClass || '',
        dangerousWork: contract?.dangerousWork ?? false,
      });
    }
  }, [user, open, reset]);

  const filteredDepartments = orgData?.departments.filter((d) => 
    selectedCompanyId ? d.companyId === selectedCompanyId : true
  ) || [];

  const filteredPositions = orgData?.positions.filter((p) => 
    selectedDepartmentId ? p.departmentId === selectedDepartmentId : true
  ) || [];

  const onSubmit = async (formData: UpdateUserFormData) => {
    setApiError('');
    try {
      const input: UpdateUserInput = {
        id: formData.id,
        firstName: formData.firstName,
        surname: formData.surname || null,
        lastName: formData.lastName,
        phoneNumber: formData.phoneNumber,
        address: formData.address,
        egn: formData.egn,
        birthDate: formData.birthDate || null,
        iban: formData.iban,
        companyId: formData.companyId,
        departmentId: formData.departmentId,
        positionId: formData.positionId,
        roleId: formData.roleId,
        isActive: formData.isActive,
        passwordForceChange: formData.passwordForceChange,
        contractType: formData.contractType,
        contractNumber: formData.contractNumber || null,
        contractStartDate: formData.contractStartDate || null,
        contractEndDate: formData.contractEndDate || null,
        baseSalary: formData.baseSalary,
        workHoursPerWeek: formData.workHoursPerWeek,
        probationMonths: formData.probationMonths,
        salaryCalculationType: formData.salaryCalculationType,
        hasIncomeTax: formData.hasIncomeTax,
        insuranceContributor: formData.insuranceContributor,
        salaryInstallmentsCount: formData.salaryInstallmentsCount,
        monthlyAdvanceAmount: formData.monthlyAdvanceAmount,
        taxResident: formData.taxResident,
        // ТРЗ разширение
        paymentDay: formData.paymentDay || 25,
        nightWorkRate: formData.nightWorkRate,
        overtimeRate: formData.overtimeRate,
        holidayRate: formData.holidayRate,
        workClass: formData.workClass || null,
        dangerousWork: formData.dangerousWork,
      };

      if (formData.email !== user?.email && formData.email !== '') {
          input.email = formData.email;
      }
      if (formData.username !== user?.username && formData.username !== '') {
          input.username = formData.username;
      }
      if (formData.password) {
          input.password = formData.password;
      }

      await updateUser({ variables: { userInput: input } });
      refetchUsers();
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setApiError(err.message);
      } else {
        setApiError('Възникна неочаквана грешка');
      }
    }
  };

  if (dataLoading) return <Box sx={{ p: 4, textAlign: 'center' }}><CircularProgress /></Box>;

  return (
    <Modal open={open} onClose={onClose} aria-labelledby="edit-user-modal-title">
      <Box sx={style}>
        <Typography id="edit-user-modal-title" variant="h6" sx={{ mb: 3, fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon color="primary" /> Редактиране на служител: {user?.firstName} {user?.lastName}
        </Typography>

        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
          <Grid container spacing={2}>
            
            {/* --- СЕКЦИЯ 1: ЛИЧНИ ДАННИ --- */}
            <Grid size={{ xs: 12 }}>
              <Alert severity="success" variant="outlined" icon={false} sx={{ py: 0, fontWeight: 'bold' }}>
                ЛИЧНИ ДАННИ
              </Alert>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Първо име" {...register('firstName')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Презиме" {...register('surname')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Фамилия" {...register('lastName')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="ЕГН" {...register('egn')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Телефон" {...register('phoneNumber')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Дата на раждане" type="date" {...register('birthDate')} InputLabelProps={{ shrink: true }} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="IBAN" {...register('iban')} size="small" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Адрес" {...register('address')} size="small" />
            </Grid>

            {/* --- СЕКЦИЯ 2: АКАУНТ --- */}
            <Grid size={{ xs: 12 }} sx={{ mt: 1 }}>
              <Alert severity="info" variant="outlined" icon={false} sx={{ py: 0, fontWeight: 'bold' }}>АКАУНТ И ДОСТЪП</Alert>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Потребителско име" {...register('username')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Имейл" {...register('email')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Нова парола" type="password" {...register('password')} size="small" placeholder="Остави празно" />
            </Grid>
            <Grid size={{ xs: 12, sm: 8 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Роля в системата</InputLabel>
                <Controller
                  name="roleId"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} label="Роля в системата" value={field.value || ''}>
                      {orgData?.roles?.map((role) => {
                        const roleTranslations: Record<string, string> = {
                          'admin': 'Администратор',
                          'super_admin': 'Главен Администратор',
                          'user': 'Служител',
                          'accountant': 'Счетоводител',
                          'manager': 'Мениджър',
                          'kiosk': 'Терминал (Kiosk)'
                        };
                        const displayName = roleTranslations[role.name.toLowerCase()] || role.description || role.name.toUpperCase();
                        return <MenuItem key={role.id} value={role.id}>{displayName}</MenuItem>;
                      })}
                    </Select>
                  )}
                />
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Switch
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    size="small"
                  />
                  <Typography variant="body2" sx={{ ml: 1 }}>Активен акаунт</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Checkbox
                    checked={passwordForceChange}
                    onChange={(e) => setPasswordForceChange(e.target.checked)}
                    size="small"
                  />
                  <Typography variant="body2">Смяна на парола</Typography>
                </Box>
            </Grid>

            {/* --- СЕКЦИЯ 3: ОРГАНИЗАЦИЯ --- */}
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
                    >
                      <MenuItem value=""><em>Няма</em></MenuItem>
                      {orgData?.companies.map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
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
                    >
                      <MenuItem value=""><em>Няма</em></MenuItem>
                      {filteredDepartments.map((d) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
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
                      {filteredPositions.map((p) => <MenuItem key={p.id} value={p.id}>{p.title}</MenuItem>)}
                    </Select>
                  )}
                />
              </FormControl>
            </Grid>

            {/* --- СЕКЦИЯ 4: ДОГОВОР И ФИНАНСИ --- */}
            <Grid size={{ xs: 12 }} sx={{ mt: 1 }}>
              <Alert severity="warning" variant="outlined" icon={false} sx={{ py: 0, fontWeight: 'bold' }}>ДОГОВОР И ФИНАНСИ</Alert>
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
              <TextField fullWidth label="Номер на договор" {...register('contractNumber')} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 3 }}>
              <TextField fullWidth label="Ден за плащане" type="number" {...register('paymentDay', { valueAsNumber: true })} size="small" inputProps={{ min: 1, max: 31 }} />
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
              <TextField fullWidth label="Основна заплата" type="number" {...register('baseSalary', { valueAsNumber: true })} size="small" />
            </Grid>

            <Grid size={{ xs: 12, sm: 3 }}>
              <TextField fullWidth label="Часове/седмица" type="number" {...register('workHoursPerWeek', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 3 }}>
              <TextField fullWidth label="Изпитателен срок" type="number" {...register('probationMonths', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Старт" type="date" {...register('contractStartDate')} InputLabelProps={{ shrink: true }} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Край" type="date" {...register('contractEndDate')} InputLabelProps={{ shrink: true }} size="small" />
            </Grid>
            
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Брой вноски" type="number" {...register('salaryInstallmentsCount', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Фиксиран аванс" type="number" {...register('monthlyAdvanceAmount', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Checkbox
                  checked={taxResident}
                  onChange={(e) => setTaxResident(e.target.checked)}
                  size="small"
                />
                <Typography variant="body2">Данъчен резидент</Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Checkbox
                  checked={hasIncomeTax}
                  onChange={(e) => setHasIncomeTax(e.target.checked)}
                  size="small"
                />
                <Typography variant="body2">Удържай ДОД (10%)</Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Checkbox
                  checked={insuranceContributor}
                  onChange={(e) => setInsuranceContributor(e.target.checked)}
                  size="small"
                />
                <Typography variant="body2">Осигурено лице</Typography>
              </Box>
            </Grid>

            {/* --- СЕКЦИЯ 5: ТРЗ СПЕЦИФИЧНИ --- */}
            <Grid size={{ xs: 12 }} sx={{ mt: 1 }}>
              <Alert severity="info" variant="outlined" icon={false} sx={{ py: 0, fontWeight: 'bold' }}>ТРЗ ПАРАМЕТРИ (СТАВКИ)</Alert>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Нощен труд (множ.)" type="number" inputProps={{ step: 0.1 }} {...register('nightWorkRate', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Извънреден (множ.)" type="number" inputProps={{ step: 0.1 }} {...register('overtimeRate', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField fullWidth label="Празници (множ.)" type="number" inputProps={{ step: 0.1 }} {...register('holidayRate', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField fullWidth label="Трудов клас / Категория" {...register('workClass')} size="small" placeholder="Напр. I, II, III" />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Checkbox
                  checked={dangerousWork}
                  onChange={(e) => setDangerousWork(e.target.checked)}
                  size="small"
                />
                <Typography variant="body2">Вредни условия на труд</Typography>
              </Box>
            </Grid>
          </Grid>

          {apiError && <Alert severity="error" sx={{ mt: 2 }}>{apiError}</Alert>}

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button type="submit" fullWidth variant="contained" disabled={isSubmitting} sx={{ py: 1.2 }}>
              {isSubmitting ? <CircularProgress size={24} /> : 'Запази промените'}
            </Button>
            <Button fullWidth variant="outlined" onClick={onClose} color="inherit">Отказ</Button>
          </Box>
        </Box>
      </Box>
    </Modal>
  );
};

export default EditUserModal;
