import React, { useState } from 'react';
import { IconButton, Badge, Menu, MenuItem, ListItemText, Typography, Box, Divider, Button } from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import CheckAllIcon from '@mui/icons-material/DoneAll';
import { useQuery, useMutation } from '@apollo/client';
import { useNavigate } from 'react-router-dom';
import {
  GET_MY_NOTIFICATIONS,
  MARK_NOTIFICATION_READ,
  MARK_ALL_NOTIFICATIONS_READ,
} from '../graphql/notifications';
import { formatDate } from '../utils/dateUtils';

const NotificationBell: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { data, loading, refetch } = useQuery(GET_MY_NOTIFICATIONS, {
    variables: { unreadOnly: false, offset: 0, limit: 10 },
    pollInterval: 30000,
  });
  const [markRead] = useMutation(MARK_NOTIFICATION_READ);
  const [markAllRead] = useMutation(MARK_ALL_NOTIFICATIONS_READ);

  const navigate = useNavigate();
  const notifications = data?.myNotifications || [];
  const unreadCount = notifications.filter((n: any) => !n.isRead).length;

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationClick = async (id: number) => {
    await markRead({ variables: { id } });
    refetch();
  };

  const handleMarkAllRead = async () => {
    await markAllRead();
    refetch();
  };

  const handleViewAll = () => {
    handleClose();
    navigate('/admin/notifications/events');
  };

  return (
    <>
      <IconButton color="inherit" onClick={handleClick}>
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        slotProps={{ paper: { sx: { width: 360, maxHeight: 420 } } }}
      >
        <Box sx={{ px: 2, py: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle2" fontWeight="bold">Уведомления</Typography>
          {unreadCount > 0 && (
            <Button size="small" startIcon={<CheckAllIcon />} onClick={handleMarkAllRead}>
              Всички прочетени
            </Button>
          )}
        </Box>
        <Divider />
        {loading ? (
          <MenuItem><Typography>Зареждане...</Typography></MenuItem>
        ) : notifications.length === 0 ? (
          <MenuItem><Typography color="text.secondary">Няма уведомления</Typography></MenuItem>
        ) : (
          notifications.map((n: any) => (
            <MenuItem
              key={n.id}
              onClick={() => handleNotificationClick(n.id)}
              sx={{
                bgcolor: n.isRead ? 'transparent' : 'rgba(25, 118, 210, 0.08)',
                whiteSpace: 'normal',
                py: 1.5,
              }}
            >
              <ListItemText
                primary={<Typography variant="body2" fontWeight={n.isRead ? 'normal' : 'medium'}>{n.message}</Typography>}
                secondary={formatDate(n.createdAt)}
              />
            </MenuItem>
          ))
        )}
        <Divider />
        <MenuItem onClick={handleViewAll} sx={{ justifyContent: 'center' }}>
          <Typography variant="body2" color="primary" fontWeight="medium">
            Виж всички
          </Typography>
        </MenuItem>
      </Menu>
    </>
  );
};

export default NotificationBell;
