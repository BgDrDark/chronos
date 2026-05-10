import React, { useState, useEffect } from 'react';
import { IconButton, Badge, Menu, MenuItem, ListItemText, Typography, Box } from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { useQuery, useMutation } from '@apollo/client';
import { GET_MY_NOTIFICATIONS, MARK_NOTIFICATION_READ } from '../graphql/notifications';
import { formatDate } from '../utils/dateUtils';

const NotificationBell: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { data, loading, refetch } = useQuery(GET_MY_NOTIFICATIONS, {
    pollInterval: 30000, // Poll every 30 seconds
  });
  const [markRead] = useMutation(MARK_NOTIFICATION_READ);

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
        PaperProps={{ sx: { width: 320, maxHeight: 400 } }}
      >
        {loading ? (
          <MenuItem><Typography>Зареждане...</Typography></MenuItem>
        ) : notifications.length === 0 ? (
          <MenuItem><Typography>Няма нови уведомления</Typography></MenuItem>
        ) : (
          notifications.map((n: any) => (
            <MenuItem 
              key={n.id} 
              onClick={() => handleNotificationClick(n.id)}
              sx={{ 
                bgcolor: n.isRead ? 'transparent' : 'rgba(25, 118, 210, 0.08)',
                whiteSpace: 'normal',
                py: 1.5 
              }}
            >
              <ListItemText
                primary={<Typography variant="body2">{n.message}</Typography>}
                secondary={formatDate(n.createdAt)}
              />
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  );
};

export default NotificationBell;
