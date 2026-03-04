import React from 'react';
import { AppBar, Toolbar, Typography, Button, CircularProgress, Box } from '@mui/material';
import HourglassFullIcon from '@mui/icons-material/HourglassFull';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
// @ts-ignore
import { useQuery, gql, useApolloClient } from '@apollo/client';

const ME_QUERY = gql`
  query Me {
    me {
      id
      email
      firstName
      lastName
      role {
        name
      }
    }
  }
`;

const Header: React.FC = () => {
  const navigate = useNavigate();
  const client = useApolloClient();
  const { loading, data } = useQuery(ME_QUERY);

  const handleLogout = async () => {
    const envUrl = import.meta.env.VITE_API_URL;
    const baseUrl = envUrl ? (envUrl.endsWith('/') ? envUrl : `${envUrl}/`) : '/';
    try {
      await fetch(`${baseUrl}auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      await client.resetStore();
      navigate('/login');
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const isAdmin = data && data.me && data.me.role && ['admin', 'super_admin'].includes(data.me.role.name);
  const displayName = data && data.me ? (data.me.firstName && data.me.lastName ? `${data.me.firstName} ${data.me.lastName}` : data.me.email) : '';

  return (
    <AppBar position="static">
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <HourglassFullIcon sx={{ mr: 1 }} />
          <Typography variant="h6" component="div">
            Chronos
          </Typography>
        </Box>
        {loading ? (
          <CircularProgress color="inherit" size={24} />
        ) : data && data.me ? (
          <>
            {isAdmin && (
              <>
                <Button color="inherit" component={RouterLink} to="/admin/users">
                  Потребители
                </Button>
                <Button color="inherit" component={RouterLink} to="/admin/schedules">
                  Графици
                </Button>
                <Button color="inherit" component={RouterLink} to="/admin/payroll">
                  Отдел финанси
                </Button>
              </>
            )}
            <Button color="inherit" component={RouterLink} to="/settings">
              Настройки
            </Button>
            <Typography variant="body1" sx={{ mr: 2, ml: 2 }}>
              {displayName}
            </Typography>
            <Button color="inherit" onClick={handleLogout}>
              Изход
            </Button>
          </>
        ) : (
          <>
            <Button color="inherit" component={RouterLink} to="/login">
              Вход
            </Button>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;
