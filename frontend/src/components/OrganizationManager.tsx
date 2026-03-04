import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Grid, Card, CardContent, Button, 
  TextField, Dialog, DialogTitle, DialogContent, DialogActions,
  List, ListItem, ListItemText, IconButton,
  MenuItem, Divider, CircularProgress, Alert
} from '@mui/material';
import { useQuery, useMutation, gql } from '@apollo/client';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import BusinessIcon from '@mui/icons-material/Business';
import GroupsIcon from '@mui/icons-material/Groups';
import BadgeIcon from '@mui/icons-material/Badge';

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
    users { # To select department manager
      users {
        id
        firstName
        lastName
        email
        username
        passwordForceChange
      }
    }
  }
`;

const CREATE_COMPANY = gql`
  mutation CreateCompany($input: CompanyCreateInput!) {
    createCompany(input: $input) {
      id
      name
      eik
      bulstat
      vatNumber
      address
      molName
    }
  }
`;

const UPDATE_COMPANY = gql`
  mutation UpdateCompany($input: CompanyUpdateInput!) {
    updateCompany(input: $input) {
      id
      name
      eik
      bulstat
      vatNumber
      address
      molName
    }
  }
`;

const CREATE_DEPARTMENT = gql`
  mutation CreateDepartment($input: DepartmentCreateInput!) {
    createDepartment(input: $input) {
      id
      name
      manager { id firstName lastName }
    }
  }
`;

const UPDATE_DEPARTMENT = gql`
  mutation UpdateDepartment($input: DepartmentUpdateInput!) {
    updateDepartment(input: $input) {
      id
      name
      manager { id firstName lastName }
    }
  }
`;

const CREATE_POSITION = gql`
  mutation CreatePosition($title: String!, $departmentId: Int!) {
    createPosition(title: $title, departmentId: $departmentId) {
      id
      title
    }
  }
`;

interface CompanyData {
    id: number;
    name: string;
    eik?: string;
    bulstat?: string;
    vatNumber?: string;
    address?: string;
    molName?: string;
}

interface DepartmentData {
    id: number;
    name: string;
    company: { id: number; name: string; };
    manager?: { id: number; firstName: string; lastName: string; email: string; };
}

interface UserData {
    id: number;
    firstName?: string;
    lastName?: string;
    email: string;
}

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

  // Company Form States
  const [companyName, setCompanyName] = useState('');
  const [companyEik, setCompanyEik] = useState('');
  const [companyBulstat, setCompanyBulstat] = useState('');
  const [companyVat, setCompanyVat] = useState('');
  const [companyAddress, setCompanyAddress] = useState('');
  const [companyMol, setCompanyMol] = useState('');
  const [editingCompany, setEditingCompany] = useState<CompanyData | null>(null);

  // Department Form States
  const [deptName, setDeptName] = useState('');
  const [selectedCompanyForDept, setSelectedCompanyForDept] = useState<string>('');
  const [selectedManagerForDept, setSelectedManagerForDept] = useState<string>('');
  const [editingDepartment, setEditingDepartment] = useState<DepartmentData | null>(null);

  // Position Form States
  const [posTitle, setPosTitle] = useState('');
  const [selectedDeptForPos, setSelectedDeptForPos] = useState<string>('');

  useEffect(() => {
    if (editingCompany) {
      setCompanyName(editingCompany.name);
      setCompanyEik(editingCompany.eik || '');
      setCompanyBulstat(editingCompany.bulstat || '');
      setCompanyVat(editingCompany.vatNumber || '');
      setCompanyAddress(editingCompany.address || '');
      setCompanyMol(editingCompany.molName || '');
    }
  }, [editingCompany]);

  useEffect(() => {
    if (editingDepartment) {
      setDeptName(editingDepartment.name);
      setSelectedCompanyForDept(String(editingDepartment.company.id));
      setSelectedManagerForDept(String(editingDepartment.manager?.id || ''));
    }
  }, [editingDepartment]);

  const resetCompanyForm = () => {
    setCompanyName('');
    setCompanyEik('');
    setCompanyBulstat('');
    setCompanyVat('');
    setCompanyAddress('');
    setCompanyMol('');
    setEditingCompany(null);
    setApiError(null);
  };

  const resetDeptForm = () => {
    setDeptName('');
    setSelectedCompanyForDept('');
    setSelectedManagerForDept('');
    setEditingDepartment(null);
    setApiError(null);
  };

  const resetPosForm = () => {
    setPosTitle('');
    setSelectedDeptForPos('');
    setApiError(null);
  };

  const handleCreateCompany = async () => {
    setApiError(null);
    try {
        await createCompany({ variables: { 
            input: {
                name: companyName, eik: companyEik || null, bulstat: companyBulstat || null, 
                vatNumber: companyVat || null, address: companyAddress || null, molName: companyMol || null
            }
        }});
        setOpenCompanyDialog(false);
        resetCompanyForm();
        refetch();
    } catch (e: any) { setApiError(e.message); }
  };

  const handleUpdateCompany = async () => {
    setApiError(null);
    if (!editingCompany) return;
    try {
        await updateCompany({ variables: { 
            input: {
                id: editingCompany.id, name: companyName, eik: companyEik || null, bulstat: companyBulstat || null, 
                vatNumber: companyVat || null, address: companyAddress || null, molName: companyMol || null
            }
        }});
        setOpenEditCompanyDialog(false);
        resetCompanyForm();
        refetch();
    } catch (e: any) { setApiError(e.message); }
  };

  const handleCreateDept = async () => {
    setApiError(null);
    try {
        await createDepartment({ variables: { 
            input: {
                name: deptName, 
                companyId: parseInt(selectedCompanyForDept), 
                managerId: selectedManagerForDept ? parseInt(selectedManagerForDept) : null
            }
        }});
        setOpenDeptDialog(false);
        resetDeptForm();
        refetch();
    } catch (e: any) { setApiError(e.message); }
  };

  const handleUpdateDept = async () => {
    setApiError(null);
    if (!editingDepartment) return;
    try {
        await updateDepartment({ variables: { 
            input: {
                id: editingDepartment.id, 
                name: deptName, 
                managerId: selectedManagerForDept ? parseInt(selectedManagerForDept) : null
            }
        }});
        setOpenEditDeptDialog(false);
        resetDeptForm();
        refetch();
    } catch (e: any) { setApiError(e.message); }
  };

  const handleCreatePos = async () => {
    setApiError(null);
    try {
        await createPosition({ variables: { title: posTitle, departmentId: parseInt(selectedDeptForPos) } });
        setOpenPosDialog(false);
        resetPosForm();
        refetch();
    } catch (e: any) { setApiError(e.message); }
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
        <Grid size={{ xs: 12, md: 4 }}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BusinessIcon color="primary" />
                    <Typography variant="h6">Фирми</Typography>
                </Box>
                <IconButton color="primary" onClick={() => { resetCompanyForm(); setOpenCompanyDialog(true); }}>
                  <AddIcon />
                </IconButton>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {data?.companies.map((c: CompanyData) => (
                  <ListItem key={c.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1, border: '1px solid #eee' }}
                    secondaryAction={
                        <IconButton edge="end" aria-label="edit" onClick={() => { setEditingCompany(c); setOpenEditCompanyDialog(true); }}>
                          <EditIcon />
                        </IconButton>
                      }
                  >
                    <ListItemText primary={c.name} secondary={`ЕИК: ${c.eik || 'N/A'}`} />
                  </ListItem>
                ))}
                {data?.companies.length === 0 && <Typography variant="caption" color="text.secondary">Няма добавени фирми.</Typography>}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* DEPARTMENTS */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <GroupsIcon color="secondary" />
                    <Typography variant="h6">Отдели</Typography>
                </Box>
                <IconButton color="secondary" onClick={() => { resetDeptForm(); setOpenDeptDialog(true); }}>
                  <AddIcon />
                </IconButton>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {data?.departments.map((d: DepartmentData) => (
                  <ListItem key={d.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1, border: '1px solid #eee' }}
                    secondaryAction={
                        <IconButton edge="end" aria-label="edit" onClick={() => { setEditingDepartment(d); setOpenEditDeptDialog(true); }}>
                          <EditIcon />
                        </IconButton>
                      }
                  >
                    <ListItemText 
                        primary={d.name} 
                        secondary={
                            <>
                                {d.company ? `към ${d.company.name}` : 'Без фирма'}
                                {d.manager && ` (Началник: ${d.manager.firstName} ${d.manager.lastName})`}
                            </>
                        } 
                    />
                  </ListItem>
                ))}
                 {data?.departments.length === 0 && <Typography variant="caption" color="text.secondary">Няма добавени отдели.</Typography>}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* POSITIONS */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
               <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BadgeIcon color="success" />
                    <Typography variant="h6">Длъжности</Typography>
                </Box>
                <IconButton color="success" onClick={() => { resetPosForm(); setOpenPosDialog(true); }}>
                  <AddIcon />
                </IconButton>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {data?.positions.map((p: any) => (
                  <ListItem key={p.id} sx={{ bgcolor: 'background.paper', mb: 1, borderRadius: 1, border: '1px solid #eee' }}>
                    <ListItemText 
                        primary={p.title} 
                        secondary={p.department ? `${p.department.name} (${p.department.company?.name || ''})` : 'Без отдел'} 
                    />
                  </ListItem>
                ))}
                 {data?.positions.length === 0 && <Typography variant="caption" color="text.secondary">Няма добавени длъжности.</Typography>}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ my: 4 }} />

      {/* --- DIALOGS --- */}

      {/* Create Company Dialog */}
      <Dialog open={openCompanyDialog} onClose={() => { setOpenCompanyDialog(false); resetCompanyForm(); }} maxWidth="sm" fullWidth>
        <DialogTitle>Нова Фирма</DialogTitle>
        <DialogContent>
            {apiError && <Alert severity="error" sx={{ mb: 2 }}>{apiError}</Alert>}
            <TextField autoFocus margin="dense" label="Име на фирмата" fullWidth sx={{ mb: 2 }}
                value={companyName} onChange={(e) => setCompanyName(e.target.value)} 
            />
            <TextField margin="dense" label="ЕИК" fullWidth sx={{ mb: 2 }}
                value={companyEik} onChange={(e) => setCompanyEik(e.target.value)} 
            />
            <TextField margin="dense" label="БУЛСТАТ" fullWidth sx={{ mb: 2 }}
                value={companyBulstat} onChange={(e) => setCompanyBulstat(e.target.value)} 
            />
            <TextField margin="dense" label="ДДС Номер" fullWidth sx={{ mb: 2 }}
                value={companyVat} onChange={(e) => setCompanyVat(e.target.value)} 
            />
            <TextField margin="dense" label="Адрес на управление" fullWidth multiline rows={2} sx={{ mb: 2 }}
                value={companyAddress} onChange={(e) => setCompanyAddress(e.target.value)} 
            />
            <TextField margin="dense" label="МОЛ (Материално отговорно лице)" fullWidth
                value={companyMol} onChange={(e) => setCompanyMol(e.target.value)} 
            />
        </DialogContent>
        <DialogActions>
            <Button onClick={() => { setOpenCompanyDialog(false); resetCompanyForm(); }}>Отказ</Button>
            <Button onClick={handleCreateCompany} variant="contained" disabled={!companyName}>Създай</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Company Dialog */}
      <Dialog open={openEditCompanyDialog} onClose={() => { setOpenEditCompanyDialog(false); resetCompanyForm(); }} maxWidth="sm" fullWidth>
        <DialogTitle>Редактиране на Фирма</DialogTitle>
        <DialogContent>
            {apiError && <Alert severity="error" sx={{ mb: 2 }}>{apiError}</Alert>}
            <TextField autoFocus margin="dense" label="Име на фирмата" fullWidth sx={{ mb: 2 }}
                value={companyName} onChange={(e) => setCompanyName(e.target.value)} 
            />
            <TextField margin="dense" label="ЕИК" fullWidth sx={{ mb: 2 }}
                value={companyEik} onChange={(e) => setCompanyEik(e.target.value)} 
            />
            <TextField margin="dense" label="БУЛСТАТ" fullWidth sx={{ mb: 2 }}
                value={companyBulstat} onChange={(e) => setCompanyBulstat(e.target.value)} 
            />
            <TextField margin="dense" label="ДДС Номер" fullWidth sx={{ mb: 2 }}
                value={companyVat} onChange={(e) => setCompanyVat(e.target.value)} 
            />
            <TextField margin="dense" label="Адрес на управление" fullWidth multiline rows={2} sx={{ mb: 2 }}
                value={companyAddress} onChange={(e) => setCompanyAddress(e.target.value)} 
            />
            <TextField margin="dense" label="МОЛ (Материално отговорно лице)" fullWidth
                value={companyMol} onChange={(e) => setCompanyMol(e.target.value)} 
            />
        </DialogContent>
        <DialogActions>
            <Button onClick={() => { setOpenEditCompanyDialog(false); resetCompanyForm(); }}>Отказ</Button>
            <Button onClick={handleUpdateCompany} variant="contained" disabled={!companyName}>Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Create Department Dialog */}
      <Dialog open={openDeptDialog} onClose={() => { setOpenDeptDialog(false); resetDeptForm(); }} maxWidth="sm" fullWidth>
        <DialogTitle>Нов Отдел</DialogTitle>
        <DialogContent>
            {apiError && <Alert severity="error" sx={{ mb: 2 }}>{apiError}</Alert>}
            <TextField 
                margin="dense" label="Име на отдела" fullWidth sx={{ mb: 2 }}
                value={deptName} onChange={(e) => setDeptName(e.target.value)} 
            />
            <TextField
                select fullWidth label="Към Фирма" sx={{ mb: 2 }}
                value={selectedCompanyForDept} onChange={(e) => setSelectedCompanyForDept(e.target.value)}
            >
                {data?.companies?.length > 0 ? data.companies.map((c: CompanyData) => (
                    <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                )) : <MenuItem disabled value="">Няма налични фирми</MenuItem>}
            </TextField>
            <TextField
                select fullWidth label="Началник Отдел"
                value={selectedManagerForDept} onChange={(e) => setSelectedManagerForDept(e.target.value)}
                helperText="Изберете служител, който да бъде назначен за началник на отдела."
            >
                <MenuItem value=""><em>Не е избран</em></MenuItem>
                {data?.users?.users?.length > 0 ? data.users.users.map((u: UserData) => (
                    <MenuItem key={u.id} value={u.id}>
                        {u.firstName} {u.lastName} ({u.email})
                    </MenuItem>
                )) : <MenuItem disabled value="">Няма налични служители</MenuItem>}
            </TextField>
        </DialogContent>
        <DialogActions>
            <Button onClick={() => { setOpenDeptDialog(false); resetDeptForm(); }}>Отказ</Button>
            <Button onClick={handleCreateDept} variant="contained" disabled={!deptName || !selectedCompanyForDept}>Създай</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Department Dialog */}
      <Dialog open={openEditDeptDialog} onClose={() => { setOpenEditDeptDialog(false); resetDeptForm(); }} maxWidth="sm" fullWidth>
        <DialogTitle>Редактиране на Отдел</DialogTitle>
        <DialogContent>
            {apiError && <Alert severity="error" sx={{ mb: 2 }}>{apiError}</Alert>}
            <TextField 
                margin="dense" label="Име на отдела" fullWidth sx={{ mb: 2 }}
                value={deptName} onChange={(e) => setDeptName(e.target.value)} 
            />
            <TextField
                select fullWidth label="Към Фирма" sx={{ mb: 2 }} disabled
                value={selectedCompanyForDept}
            >
                 {data?.companies?.map((c: CompanyData) => (
                    <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
            </TextField>
            <TextField
                select fullWidth label="Началник Отдел"
                value={selectedManagerForDept} onChange={(e) => setSelectedManagerForDept(e.target.value)}
                helperText="Изберете служител, който да бъде назначен за началник на отдела."
            >
                <MenuItem value=""><em>Не е избран</em></MenuItem>
                {data?.users?.users?.length > 0 ? data.users.users.map((u: UserData) => (
                    <MenuItem key={u.id} value={u.id}>
                        {u.firstName} {u.lastName} ({u.email})
                    </MenuItem>
                )) : <MenuItem disabled value="">Няма налични служители</MenuItem>}
            </TextField>
        </DialogContent>
        <DialogActions>
            <Button onClick={() => { setOpenEditDeptDialog(false); resetDeptForm(); }}>Отказ</Button>
            <Button onClick={handleUpdateDept} variant="contained" disabled={!deptName || !selectedCompanyForDept}>Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Create Position Dialog */}
      <Dialog open={openPosDialog} onClose={() => { setOpenPosDialog(false); resetPosForm(); }} maxWidth="xs" fullWidth>
        <DialogTitle>Нова Длъжност</DialogTitle>
        <DialogContent>
            {apiError && <Alert severity="error" sx={{ mb: 2 }}>{apiError}</Alert>}
            <TextField 
                margin="dense" label="Наименование на длъжността" fullWidth sx={{ mb: 2 }}
                value={posTitle} onChange={(e) => setPosTitle(e.target.value)} 
            />
             <TextField
                select fullWidth label="Към Отдел"
                value={selectedDeptForPos} onChange={(e) => setSelectedDeptForPos(e.target.value)}
            >
                {data?.departments?.length > 0 ? data.departments.map((d: DepartmentData) => (
                    <MenuItem key={d.id} value={d.id}>
                        {d.name} {d.company ? `(${d.company.name})` : ''}
                    </MenuItem>
                )) : <MenuItem disabled value="">Няма налични отдели</MenuItem>}
            </TextField>
        </DialogContent>
        <DialogActions>
            <Button onClick={() => { setOpenPosDialog(false); resetPosForm(); }}>Отказ</Button>
            <Button onClick={handleCreatePos} variant="contained" disabled={!posTitle || !selectedDeptForPos}>Създай</Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};

export default OrganizationManager;
