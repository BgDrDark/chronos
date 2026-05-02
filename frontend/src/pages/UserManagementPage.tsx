import React, { useState } from 'react';
import { Typography, Box, Button, Dialog, DialogTitle, DialogContent, Tooltip } from '@mui/material';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import CreateUserForm from '../components/CreateUserForm';
import UserList from '../components/UserList';
import OrganizationManager from '../components/OrganizationManager';
import { TabbedPage } from '../components/TabbedPage';

interface Props {
  tab?: string;
}

const UserManagementPage: React.FC<Props> = ({ tab }) => {
  const [open, setOpen] = useState(false);

  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const tabs = [
    { label: 'Списък служители', path: '/admin/users/list' },
    { label: 'Организационна структура', path: '/admin/users/org-structure' },
  ];

  return (
    <TabbedPage tabs={tabs} defaultTabPath="/admin/users/list">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          Управление на ресурси
        </Typography>
        {tab !== 'org-structure' && (
          <Tooltip title="Добави нов служител в системата" arrow>
            <Button
              variant="contained"
              startIcon={<PersonAddIcon />}
              onClick={handleOpen}
            >
              Нов потребител
            </Button>
          </Tooltip>
        )}
      </Box>

      {tab === 'org-structure' ? (
        <OrganizationManager />
      ) : (
        <UserList />
      )}

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: 'bold' }}>Създаване на нов потребител</DialogTitle>
        <DialogContent dividers>
          <CreateUserForm onCreated={() => {
              handleClose();
              window.location.reload(); 
          }} />
        </DialogContent>
      </Dialog>
    </TabbedPage>
  );
};

export default UserManagementPage;
