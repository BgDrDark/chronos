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
  FormControlLabel,
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

// Zod schema for validation
const updateUserSchema = z.object({
  id: z.number(),
  email: z.string().email('Невалиден имейл адрес').optional().or(z.literal('')),
  username: z.string().min(3, 'Потребителското име трябва да е поне 3 символа').optional().or(z.literal('')),
  password: z.string().optional().or(z.literal('')),
  firstName: z.string().optional().or(z.literal('')),
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
  // Contract fields
  contractType: z.string().optional().or(z.literal('')),
  contractStartDate: z.string().optional().or(z.literal('')),
  contractEndDate: z.string().nullable().optional().or(z.literal('')),
  baseSalary: z.number().nullable().optional(),
  hasIncomeTax: z.boolean().optional(),
  salaryInstallmentsCount: z.number().min(1),
  monthlyAdvanceAmount: z.number().min(0),
  taxResident: z.boolean(),
  // ТРЗ разширение
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
  user: any;
  refetchUsers: () => void;
}

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: { xs: '90%', sm: 600 },
  maxHeight: '90vh',
  overflowY: 'auto',
  bgcolor: 'background.paper',
  borderRadius: 3,
  boxShadow: 24,
  p: 4,
};

const EditUserModal: React.FC<EditUserModalProps> = ({ open, onClose, user, refetchUsers }) => {
  const [apiError, setApiError] = useState('');

  const {
    register,
    handleSubmit,
    reset,
    control,
    watch,
    formState: { isSubmitting },
  } = useForm<UpdateUserFormData>({
    resolver: zodResolver(updateUserSchema),
  });

  const [updateUser] = useMutation(UPDATE_USER_MUTATION);
  const { data: orgData, loading: dataLoading } = useQuery(GET_DATA_QUERY);

  useEffect(() => {
    if (user) {
      const contract = user.employmentContract;
      reset({
        id: parseInt(user.id),
        email: user.email || '',
        username: user.username || '',
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        phoneNumber: user.phoneNumber || '',
        address: user.address || '',
        egn: user.egn || '',
        birthDate: user.birthDate || '',
        iban: user.iban || '',
        companyId: user.company?.id || null,
        departmentId: user.department?.id || null,
        positionId: user.position?.id || null,
        roleId: user.role?.id || null,
        isActive: user.isActive,
        password: '',
        // ТРЗ данни от employment contract
        contractType: contract?.contractType || 'full_time',
        contractStartDate: contract?.startDate || '',
        contractEndDate: contract?.endDate || '',
        baseSalary: contract?.baseSalary || null,
        hasIncomeTax: contract?.hasIncomeTax ?? true,
        salaryInstallmentsCount: contract?.salaryInstallmentsCount || 1,
        monthlyAdvanceAmount: contract?.monthlyAdvanceAmount || 0,
        taxResident: contract?.taxResident ?? true,
      });
    }
  }, [user, reset]);

  const selectedCompanyId = watch('companyId');
  const selectedDepartmentId = watch('departmentId');

  const filteredDepartments = orgData?.departments.filter((d: any) => 
    selectedCompanyId ? d.companyId === selectedCompanyId : true
  ) || [];

  const filteredPositions = orgData?.positions.filter((p: any) => 
    selectedDepartmentId ? p.departmentId === selectedDepartmentId : true
  ) || [];

  const onSubmit = async (formData: UpdateUserFormData) => {
    setApiError('');
    try {
      const input: any = {
        id: formData.id,
        email: formData.email || null,
        username: formData.username || null,
        firstName: formData.firstName,
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
        contractType: formData.contractType,
        contractStartDate: formData.contractStartDate || null,
        contractEndDate: formData.contractEndDate || null,
        baseSalary: formData.baseSalary,
        hasIncomeTax: formData.hasIncomeTax,
        salaryInstallmentsCount: formData.salaryInstallmentsCount,
        monthlyAdvanceAmount: formData.monthlyAdvanceAmount,
        taxResident: formData.taxResident,
        // ТРЗ разширение
        nightWorkRate: formData.nightWorkRate || 0.5,
        overtimeRate: formData.overtimeRate || 1.5,
        holidayRate: formData.holidayRate || 2.0,
        workClass: formData.workClass || null,
        dangerousWork: formData.dangerousWork || false,
      };

      if (formData.email !== user?.email) {
          input.email = formData.email;
      }
      if (formData.password) {
          input.password = formData.password;
      }

      await updateUser({ variables: { userInput: input } });
      refetchUsers();
      onClose();
    } catch (err: any) {
      setApiError(err.message);
    }
  };

  if (dataLoading) return null;

  return (
    <Modal open={open} onClose={onClose} aria-labelledby="edit-user-modal-title">
      <Box sx={style}>
        <Typography id="edit-user-modal-title" variant="h6" sx={{ mb: 3, fontWeight: 'bold' }}>
          Редактиране на служител: {user?.firstName} {user?.lastName}
        </Typography>

        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
          <Grid container spacing={2}>
            
            {/* --- СЕКЦИЯ 1: ЛИЧНИ ДАННИ --- */}
            <Grid size={{ xs: 12 }}>
              <Alert severity="success" variant="outlined" icon={<PersonIcon fontSize="small" />} sx={{ py: 0 }}>
                Лични данни
              </Alert>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Име" {...register('firstName')} size="small" />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Фамилия" {...register('lastName')} size="small" />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="ЕГН" {...register('egn')} size="small" />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Телефон" {...register('phoneNumber')} size="small" />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Дата на раждане" type="date" {...register('birthDate')} InputLabelProps={{ shrink: true }} size="small" />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="IBAN" {...register('iban')} size="small" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth label="Адрес" {...register('address')} size="small" />
            </Grid>

            {/* --- СЕКЦИЯ 2: АКАУНТ --- */}
            <Grid size={{ xs: 12 }} sx={{ mt: 1 }}>
              <Alert severity="info" variant="outlined" icon={false} sx={{ py: 0 }}>Акаунт и Роля</Alert>
            </Grid>
            <Grid size={{ xs: 4 }}>
              <TextField fullWidth label="Потребителско име" {...register('username')} size="small" />
            </Grid>
            <Grid size={{ xs: 4 }}>
              <TextField fullWidth label="Имейл" {...register('email')} size="small" />
            </Grid>
            <Grid size={{ xs: 4 }}>
              <TextField fullWidth label="Нова парола" type="password" {...register('password')} size="small" placeholder="Остави празно" />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Роля в системата</InputLabel>
                <Controller
                  name="roleId"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} label="Роля в системата" value={field.value || ''}>
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
            <Grid size={{ xs: 12 }}>
                <FormControlLabel
                    control={<Controller name="isActive" control={control} render={({ field }) => <Switch checked={!!field.value} onChange={e => field.onChange(e.target.checked)} />} />}
                    label="Активен акаунт"
                />
            </Grid>

            {/* --- СЕКЦИЯ 3: ОРГАНИЗАЦИЯ --- */}
            <Grid size={{ xs: 12, sm: 4 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Фирма</InputLabel>
                <Controller
                  name="companyId"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} label="Фирма" value={field.value ?? ''}>
                      <MenuItem value=""><em>Няма</em></MenuItem>
                      {orgData?.companies.map((c: any) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
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
                      {filteredDepartments.map((d: any) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
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
                      {filteredPositions.map((p: any) => <MenuItem key={p.id} value={p.id}>{p.title}</MenuItem>)}
                    </Select>
                  )}
                />
              </FormControl>
            </Grid>

            {/* --- СЕКЦИЯ 4: ДОГОВОР --- */}
            <Grid size={{ xs: 12 }} sx={{ mt: 1 }}>
              <Alert severity="warning" variant="outlined" icon={false} sx={{ py: 0 }}>Договор и Финанси</Alert>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Основна заплата" type="number" {...register('baseSalary', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 6 }}>
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
                    </Select>
                  )}
                />
              </FormControl>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Старт" type="date" {...register('contractStartDate')} InputLabelProps={{ shrink: true }} size="small" />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField fullWidth label="Край" type="date" {...register('contractEndDate')} InputLabelProps={{ shrink: true }} size="small" />
            </Grid>
            
            <Grid size={{ xs: 4 }}>
              <TextField fullWidth label="Вноски" type="number" {...register('salaryInstallmentsCount', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 4 }}>
              <TextField fullWidth label="Аванс" type="number" {...register('monthlyAdvanceAmount', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 4 }} display="flex" alignItems="center">
              <FormControlLabel
                control={<Controller name="taxResident" control={control} render={({ field }) => <Checkbox checked={!!field.value} onChange={e => field.onChange(e.target.checked)} />} />}
                label="Резидент"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={<Controller name="hasIncomeTax" control={control} render={({ field }) => <Checkbox checked={!!field.value} onChange={e => field.onChange(e.target.checked)} />} />}
                label="Удържай ДОД (10%)"
              />
            </Grid>

            {/* --- СЕКЦИЯ 4: ТРЗ --- */}
            <Grid size={{ xs: 12 }} sx={{ mt: 1 }}>
              <Alert severity="success" variant="outlined" icon={false} sx={{ py: 0 }}>ТРЗ - Трудови Права</Alert>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField fullWidth label="Нощен труд (%)" type="number" inputProps={{ step: 0.1, min: 0 }} {...register('nightWorkRate', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField fullWidth label="Извънреден (множ.)" type="number" inputProps={{ step: 0.1, min: 1 }} {...register('overtimeRate', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField fullWidth label="Празници (множ.)" type="number" inputProps={{ step: 0.1, min: 1 }} {...register('holidayRate', { valueAsNumber: true })} size="small" />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Клас</InputLabel>
                <Controller
                  name="workClass"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} label="Клас" value={field.value || ''}>
                      <MenuItem value="I">Клас I</MenuItem>
                      <MenuItem value="II">Клас II</MenuItem>
                      <MenuItem value="III">Клас III</MenuItem>
                      <MenuItem value="IV">Клас IV</MenuItem>
                    </Select>
                  )}
                />
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={<Controller name="dangerousWork" control={control} render={({ field }) => <Checkbox checked={!!field.value} onChange={e => field.onChange(e.target.checked)} />} />}
                label="Вредни условия на труд"
              />
            </Grid>
          </Grid>

          {apiError && <Alert severity="error" sx={{ mt: 2 }}>{apiError}</Alert>}

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button type="submit" fullWidth variant="contained" disabled={isSubmitting}>
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