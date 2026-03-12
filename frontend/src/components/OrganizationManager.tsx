import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Grid, Card, CardContent, Button, 
  TextField, Dialog, DialogTitle, DialogContent, DialogActions,
  List, ListItem, ListItemText, IconButton,
  MenuItem, Divider, CircularProgress, Alert
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import { useForm, Controller } from 'react-hook-form';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import BusinessIcon from '@mui/icons-material/Business';
import GroupsIcon from '@mui/icons-material/Groups';
import BadgeIcon from '@mui/icons-material/Badge';
import { type Company, type Department, type Position, type User } from '../types';

// --- GraphQL ---
const GET_STRUCTURE_QUERY = gql`
  query GetStructure {
    companies {
      id
      name
      eik
      bulstat
      vatNumber
      address
      molName
    }
    departments {
      id
      name
      company {
        id
        name
      }
      manager {
        id
        firstName
        lastName
        email
      }
    }
    positions {
      id
      title
      department {
        id
        name
        company {
          id
          name
        }
      }
    }
    users {
      users {
        id
        firstName
        lastName
        email
      }
    }
  }
`;

const CREATE_COMPANY = gql`
  mutation CreateCompany($input: CompanyCreateInput!) {
    createCompany(input: $input) { id name }
  }
`;

const UPDATE_COMPANY = gql`
  mutation UpdateCompany($input: CompanyUpdateInput!) {
    updateCompany(input: $input) { id name }
  }
`;

const CREATE_DEPARTMENT = gql`
  mutation CreateDepartment($input: DepartmentCreateInput!) {
    createDepartment(input: $input) { id name }
  }
`;

const UPDATE_DEPARTMENT = gql`
  mutation UpdateDepartment($input: DepartmentUpdateInput!) {
    updateDepartment(input: $input) { id name }
  }
`;

const CREATE_POSITION = gql`
  mutation CreatePosition($title: String!, $departmentId: Int!) {
    createPosition(title: $title, departmentId: $departmentId) { id title }
  }
`;

const OrganizationManager: React.FC = () => {
  const { data, loading, error, refetch } = useQuery(GET_STRUCTURE_QUERY);
  
  const [createCompany] = useMutation(CREATE_COMPANY);
  const [updateCompany] = useMutation(UPDATE_COMPANY);
  const [createDepartment] = useMutation(CREATE_DEPARTMENT);
  const [updateDepartment] = useMutation(UPDATE_DEPARTMENT);
  const [createPosition] = useMutation(CREATE_POSITION);

  const [apiError, setApiError] = useState<string | null>(null);

  // Dialog States
  const [openCompanyDialog, setOpenCompanyDialog] = useState(false);
  const [openEditCompanyDialog, setOpenEditCompanyDialog] = useState(false);
  const [openDeptDialog, setOpenDeptDialog] = useState(false);
  const [openEditDeptDialog, setOpenEditDeptDialog] = useState(false);
  const [openPosDialog, setOpenPosDialog] = useState(false);

  // Form Management
  const companyForm = useForm({
    defaultValues: { name: '', eik: '', bulstat: '', vatNumber: '', address: '', molName: '' }
  });

  const deptForm = useForm({
    defaultValues: { name: '', companyId: '', managerId: '' }
  });

  const posForm = useForm({
    defaultValues: { title: '', departmentId: '' }
  });

  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);

  // Reset/Initialize forms when editing state changes
  useEffect(() => {
    if (editingCompany) {
      companyForm.reset({
        name: editingCompany.name,
        eik: editingCompany.eik || '',
        bulstat: editingCompany.bulstat || '',
        vatNumber: editingCompany.vatNumber || '',
        address: editingCompany.address || '',
        molName: editingCompany.molName || ''
      });
    } else {
      companyForm.reset({ name: '', eik: '', bulstat: '', vatNumber: '', address: '', molName: '' });
    }
  }, [editingCompany, companyForm]);

  useEffect(() => {
    if (editingDepartment) {
      deptForm.reset({
        name: editingDepartment.name,
        companyId: String(editingDepartment.company?.id || ''),
        managerId: String(editingDepartment.manager?.id || '')
      });
    } else {
      deptForm.reset({ name: '', companyId: '', managerId: '' });
    }
  }, [editingDepartment, deptForm]);

  const handleCompanySubmit = async (formData: { name: string, eik?: string, bulstat?: string, vatNumber?: string, address?: string, molName?: string }) => {
    setApiError(null);
    try {
        const input = { ...formData, eik: formData.eik || null, bulstat: formData.bulstat || null, vatNumber: formData.vatNumber || null, address: formData.address || null, molName: formData.molName || null };
        if (editingCompany) {
            await updateCompany({ variables: { input: { id: editingCompany.id, ...input } } });
            setOpenEditCompanyDialog(false);
        } else {
            await createCompany({ variables: { input } });
            setOpenCompanyDialog(false);
        }
        setEditingCompany(null);
        refetch();
    } catch (err: unknown) { 
        if (err instanceof Error) setApiError(err.message);
        else setApiError('Възникна неочаквана грешка');
    }
  };

  const handleDeptSubmit = async (formData: { name: string, companyId: string, managerId: string }) => {
    setApiError(null);
    try {
        if (editingDepartment) {
            await updateDepartment({ variables: { 
                input: { 
                    id: editingDepartment.id, 
                    name: formData.name, 
                    managerId: formData.managerId ? parseInt(formData.managerId) : null 
                } 
            }});
            setOpenEditDeptDialog(false);
        } else {
            await createDepartment({ variables: { 
                input: { 
                    name: formData.name, 
                    companyId: parseInt(formData.companyId), 
                    managerId: formData.managerId ? parseInt(formData.managerId) : null 
                } 
            }});
            setOpenDeptDialog(false);
        }
        setEditingDepartment(null);
        refetch();
    } catch (err: unknown) { 
        if (err instanceof Error) setApiError(err.message);
        else setApiError('Възникна неочаквана грешка');
    }
  };

  const handlePosSubmit = async (formData: { title: string, departmentId: string }) => {
    setApiError(null);
    try {
        await createPosition({ variables: { 
            title: formData.title, 
            departmentId: parseInt(formData.departmentId) 
        }});
        setOpenPosDialog(false);
        posForm.reset();
        refetch();
    } catch (err: unknown) { 
        if (err instanceof Error) setApiError(err.message);
        else setApiError('Възникна неочаквана грешка');
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Грешка при зареждане: {error.message}</Alert>;

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom fontWeight="bold">Организационна Структура</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Тук дефинирате йерархията на организацията. Първо създайте Фирма, после Отдел към нея, и накрая Длъжности към отдела.
      </Typography>

      {apiError && <Alert severity="error" sx={{ mb: 2 }}>{apiError}</Alert>}

      <Grid container spacing={3}>
        {/* COMPANIES */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BusinessIcon color="primary" />
                    <Typography variant="h6">Фирми</Typography>
                </Box>
                <IconButton color="primary" onClick={() => { setEditingCompany(null); setOpenCompanyDialog(true); }}>
                  <AddIcon />
                </IconButton>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {data?.companies.map((c: Company) => (
                  <ListItem key={c.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1, border: '1px solid #eee' }}
                    secondaryAction={
                        <IconButton edge="end" onClick={() => { setEditingCompany(c); setOpenEditCompanyDialog(true); }}>
                          <EditIcon />
                        </IconButton>
                      }
                  >
                    <ListItemText primary={c.name} secondary={`ЕИК: ${c.eik || 'N/A'}`} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* DEPARTMENTS */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <GroupsIcon color="secondary" />
                    <Typography variant="h6">Отдели</Typography>
                </Box>
                <IconButton color="secondary" onClick={() => { setEditingDepartment(null); setOpenDeptDialog(true); }}>
                  <AddIcon />
                </IconButton>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {data?.departments.map((d: Department) => (
                  <ListItem key={d.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1, border: '1px solid #eee' }}
                    secondaryAction={
                        <IconButton edge="end" onClick={() => { setEditingDepartment(d); setOpenEditDeptDialog(true); }}>
                          <EditIcon />
                        </IconButton>
                      }
                  >
                    <ListItemText primary={d.name} secondary={d.company?.name || 'Без фирма'} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* POSITIONS */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
               <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BadgeIcon color="success" />
                    <Typography variant="h6">Длъжности</Typography>
                </Box>
                <IconButton color="success" onClick={() => setOpenPosDialog(true)}>
                  <AddIcon />
                </IconButton>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {data?.positions.map((p: Position) => (
                  <ListItem key={p.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1, border: '1px solid #eee' }}>
                    <ListItemText primary={p.title} secondary={p.department?.name || 'Без отдел'} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* --- DIALOGS --- */}

      {/* Company Dialog (Create/Edit) */}
      <Dialog open={openCompanyDialog || openEditCompanyDialog} onClose={() => { setOpenCompanyDialog(false); setOpenEditCompanyDialog(false); setEditingCompany(null); }} maxWidth="sm" fullWidth>
        <DialogTitle>{editingCompany ? 'Редактиране на Фирма' : 'Нова Фирма'}</DialogTitle>
        <Box component="form" onSubmit={companyForm.handleSubmit(handleCompanySubmit)}>
            <DialogContent dividers>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <Controller name="name" control={companyForm.control} render={({ field }) => <TextField {...field} fullWidth label="Име на фирмата" size="small" required />} />
                    </Grid>
                    <Grid item xs={6}>
                        <Controller name="eik" control={companyForm.control} render={({ field }) => <TextField {...field} fullWidth label="ЕИК" size="small" />} />
                    </Grid>
                    <Grid item xs={6}>
                        <Controller name="bulstat" control={companyForm.control} render={({ field }) => <TextField {...field} fullWidth label="БУЛСТАТ" size="small" />} />
                    </Grid>
                    <Grid item xs={12}>
                        <Controller name="vatNumber" control={companyForm.control} render={({ field }) => <TextField {...field} fullWidth label="ДДС Номер" size="small" />} />
                    </Grid>
                    <Grid item xs={12}>
                        <Controller name="address" control={companyForm.control} render={({ field }) => <TextField {...field} fullWidth label="Адрес" size="small" multiline rows={2} />} />
                    </Grid>
                    <Grid item xs={12}>
                        <Controller name="molName" control={companyForm.control} render={({ field }) => <TextField {...field} fullWidth label="МОЛ" size="small" />} />
                    </Grid>
                </Grid>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => { setOpenCompanyDialog(false); setOpenEditCompanyDialog(false); setEditingCompany(null); }}>Отказ</Button>
                <Button type="submit" variant="contained">{editingCompany ? 'Запази' : 'Създай'}</Button>
            </DialogActions>
        </Box>
      </Dialog>

      {/* Department Dialog */}
      <Dialog open={openDeptDialog || openEditDeptDialog} onClose={() => { setOpenDeptDialog(false); setOpenEditDeptDialog(false); setEditingDepartment(null); }} maxWidth="sm" fullWidth>
        <DialogTitle>{editingDepartment ? 'Редактиране на Отдел' : 'Нов Отдел'}</DialogTitle>
        <Box component="form" onSubmit={deptForm.handleSubmit(handleDeptSubmit)}>
            <DialogContent dividers>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <Controller name="name" control={deptForm.control} render={({ field }) => <TextField {...field} fullWidth label="Име на отдела" size="small" required />} />
                    </Grid>
                    <Grid item xs={12}>
                        <Controller name="companyId" control={deptForm.control} render={({ field }) => (
                            <TextField {...field} select fullWidth label="Фирма" size="small" disabled={!!editingDepartment}>
                                {data?.companies.map((c: Company) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
                            </TextField>
                        )} />
                    </Grid>
                    <Grid item xs={12}>
                        <Controller name="managerId" control={deptForm.control} render={({ field }) => (
                            <TextField {...field} select fullWidth label="Началник Отдел" size="small">
                                <MenuItem value=""><em>Не е избран</em></MenuItem>
                                {data?.users.users.map((u: User) => <MenuItem key={u.id} value={u.id}>{u.firstName} {u.lastName}</MenuItem>)}
                            </TextField>
                        )} />
                    </Grid>
                </Grid>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => { setOpenDeptDialog(false); setOpenEditDeptDialog(false); setEditingDepartment(null); }}>Отказ</Button>
                <Button type="submit" variant="contained">{editingDepartment ? 'Запази' : 'Създай'}</Button>
            </DialogActions>
        </Box>
      </Dialog>

      {/* Position Dialog */}
      <Dialog open={openPosDialog} onClose={() => setOpenPosDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Нова Длъжност</DialogTitle>
        <Box component="form" onSubmit={posForm.handleSubmit(handlePosSubmit)}>
            <DialogContent dividers>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <Controller name="title" control={posForm.control} render={({ field }) => <TextField {...field} fullWidth label="Наименование" size="small" required />} />
                    </Grid>
                    <Grid item xs={12}>
                        <Controller name="departmentId" control={posForm.control} render={({ field }) => (
                            <TextField {...field} select fullWidth label="Към Отдел" size="small">
                                {data?.departments.map((d: Department) => <MenuItem key={d.id} value={d.id}>{d.name} ({d.company?.name})</MenuItem>)}
                            </TextField>
                        )} />
                    </Grid>
                </Grid>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setOpenPosDialog(false)}>Отказ</Button>
                <Button type="submit" variant="contained">Създай</Button>
            </DialogActions>
        </Box>
      </Dialog>

    </Box>
  );
};

export default OrganizationManager;
