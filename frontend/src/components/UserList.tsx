import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  CircularProgress,
  Box,
  Alert,
  IconButton,
  useTheme,
  useMediaQuery,
  Card,
  CardContent,
  Stack,
  Chip,
  TablePagination,
  TableSortLabel,
  TextField,
  InputAdornment
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import SearchIcon from '@mui/icons-material/Search';
import CorporateFareIcon from '@mui/icons-material/CorporateFare';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useNavigate } from 'react-router-dom';
// @ts-ignore
import { useQuery, gql, useMutation } from '@apollo/client';
import EditUserModal from './EditUserModal';

const GET_USERS_QUERY = gql`
  query GetUsers($skip: Int, $limit: Int, $search: String, $sortBy: String, $sortOrder: String) {
    users(skip: $skip, limit: $limit, search: $search, sortBy: $sortBy, sortOrder: $sortOrder) {
      users {
        id
        email
        firstName
        lastName
        phoneNumber
        address
        egn
        birthDate
        iban
        isActive
        createdAt
        lastLogin
        company { id name }
        department { id name }
        position { id title }
        role { id name description }
        employmentContract {
          id
          contractType
          startDate
          endDate
          baseSalary
          workHoursPerWeek
          salaryInstallmentsCount
          monthlyAdvanceAmount
          taxResident
          hasIncomeTax
          nightWorkRate
          overtimeRate
          holidayRate
          workClass
          dangerousWork
        }
      }
      totalCount
    }
  }
`;

const DELETE_USER_MUTATION = gql`
  mutation DeleteUser($id: Int!) {
    deleteUser(id: $id)
  }
`;

interface UserData {
  id: number;
  email: string;
  firstName?: string | null;
  lastName?: string | null;
  isActive: boolean;
  company?: { id: number; name: string } | null;
  department?: { id: number; name: string } | null;
  position?: { id: number; title: string } | null;
  createdAt: string;
  lastLogin?: string | null;
  role: { id: number; name: string };
}

const UserList: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const navigate = useNavigate();
  
  // Table State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('id');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const { loading, error, data, refetch } = useQuery(GET_USERS_QUERY, {
    variables: {
      skip: page * rowsPerPage,
      limit: rowsPerPage,
      search: search || null,
      sortBy,
      sortOrder
    }
  });

  const [deleteUser] = useMutation(DELETE_USER_MUTATION, {
    onCompleted: () => refetch(),
    onError: (err: any) => console.error("Error deleting user:", err.message),
  });

  const [editModalOpen, setEditModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserData | null>(null);

  const handleDeleteUser = async (userId: number) => {
    if (window.confirm('Сигурни ли сте, че искате да изтриете този потребител?')) {
      try {
        await deleteUser({ variables: { id: userId } });
      } catch (err: any) {
        alert(`Грешка при изтриване: ${err.message}`);
      }
    }
  };

  const handleEditUser = (user: UserData) => {
    setCurrentUser(user);
    setEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setEditModalOpen(false);
    setCurrentUser(null);
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSort = (property: string) => {
    const isAsc = sortBy === property && sortOrder === 'asc';
    setSortOrder(isAsc ? 'desc' : 'asc');
    setSortBy(property);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value);
    setPage(0);
  };

  if (loading && !data) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 4 }}>Грешка при зареждане на потребители: {error.message}</Alert>
    );
  }

  const users = data?.users?.users || [];
  const totalCount = data?.users?.totalCount || 0;

  const renderMobileView = () => (
    <Stack spacing={2}>
      {users.map((user: UserData) => (
        <Card key={user.id} variant="outlined" sx={{ borderRadius: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Typography variant="subtitle1" fontWeight="bold" sx={{ wordBreak: 'break-all' }}>
                {user.firstName} {user.lastName}
              </Typography>
              <Chip 
                label={user.isActive ? 'Активен' : 'Неактивен'} 
                color={user.isActive ? 'success' : 'default'} 
                size="small" 
                variant="outlined"
              />
            </Box>
            
            <Typography variant="body2" gutterBottom>{user.email}</Typography>
            
            <Stack direction="row" spacing={1} sx={{ mt: 1, mb: 1 }}>
               <Chip size="small" icon={<CorporateFareIcon />} label={user.company?.name || 'Няма фирма'} variant="outlined" />
               <Chip size="small" label={user.position?.title || 'Няма длъжност'} variant="outlined" />
            </Stack>

            <Typography variant="body2" color="text.secondary">
              Роля: {user.role ? (['admin', 'super_admin'].includes(user.role.name) ? 'Админ' : 'Потребител') : 'N/A'}
            </Typography>
            
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
              <IconButton 
                size="small" 
                color="info" 
                onClick={() => navigate(`/profile/${user.id}`)} 
                sx={{ border: '1px solid', borderColor: 'info.main', borderRadius: 1 }}
              >
                <VisibilityIcon fontSize="small" />
              </IconButton>
              <IconButton 
                size="small" 
                color="primary" 
                onClick={() => handleEditUser(user)} 
                sx={{ border: '1px solid', borderColor: 'primary.main', borderRadius: 1 }}
              >
                <EditIcon fontSize="small" />
              </IconButton>
              <IconButton 
                size="small" 
                color="error" 
                onClick={() => handleDeleteUser(user.id)}
                sx={{ border: '1px solid', borderColor: 'error.main', borderRadius: 1 }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );

  const renderDesktopView = () => (
    <TableContainer component={Paper} sx={{ borderRadius: 3, overflow: 'hidden' }}>
      <Table sx={{ minWidth: 650 }} aria-label="user list table" size="small">
        <TableHead>
          <TableRow sx={{ backgroundColor: 'rgba(0,0,0,0.02)' }}>
            <TableCell>
              <TableSortLabel
                active={sortBy === 'id'}
                direction={sortBy === 'id' ? sortOrder : 'asc'}
                onClick={() => handleSort('id')}
              >
                ID
              </TableSortLabel>
            </TableCell>
            <TableCell>Име</TableCell>
            <TableCell>Имейл</TableCell>
            <TableCell>Фирма/Отдел</TableCell>
            <TableCell>Длъжност</TableCell>
            <TableCell>Роля</TableCell>
            <TableCell>Статус</TableCell>
            <TableCell align="right">Действия</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map((user: UserData) => (
            <TableRow key={user.id} hover>
              <TableCell>{user.id}</TableCell>
              <TableCell>{user.firstName} {user.lastName}</TableCell>
              <TableCell>{user.email}</TableCell>
              <TableCell>
                <Typography variant="body2">{user.company?.name || '—'}</Typography>
                <Typography variant="caption" color="text.secondary">{user.department?.name || '—'}</Typography>
              </TableCell>
              <TableCell>{user.position?.title || '—'}</TableCell>
              <TableCell>{user.role ? (['admin', 'super_admin'].includes(user.role.name) ? 'Админ' : 'Служител') : 'N/A'}</TableCell>
              <TableCell>
                {user.isActive ? 
                  <Chip size="small" icon={<CheckCircleIcon />} label="Активен" color="success" variant="outlined" /> : 
                  <Chip size="small" icon={<CancelIcon />} label="Неактивен" color="default" variant="outlined" />
                }
              </TableCell>
              <TableCell align="right">
                <IconButton color="info" onClick={() => navigate(`/profile/${user.id}`)} title="Преглед на досие" size="small">
                  <VisibilityIcon fontSize="small" />
                </IconButton>
                <IconButton color="primary" onClick={() => handleEditUser(user)} title="Редактирай" size="small">
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton color="error" onClick={() => handleDeleteUser(user.id)} title="Изтрий" size="small">
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
          Списък със служители
        </Typography>
        <TextField
          size="small"
          placeholder="Търсене..."
          value={search}
          onChange={handleSearchChange}
          sx={{ width: { xs: '100%', sm: 300 } }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {loading && (
        <Box sx={{ textAlign: 'center', my: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {isMobile ? renderMobileView() : renderDesktopView()}
      
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        labelRowsPerPage="Редове на страница:"
        labelDisplayedRows={({ from, to, count }) => `${from}-${to} от ${count}`}
      />
      
      {currentUser && (
        <EditUserModal
          open={editModalOpen}
          onClose={handleCloseEditModal}
          user={currentUser}
          refetchUsers={refetch}
        />
      )}
    </Box>
  );
};

export default UserList;
