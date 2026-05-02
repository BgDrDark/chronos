import React from 'react';
import { Box, List, ListItem, ListItemButton, ListItemText, Divider, Typography, Paper } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';

export interface NavItem {
  label: string;
  path: string;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

interface GroupedSidebarNavProps {
  groups: NavGroup[];
  children: React.ReactNode;
  title?: string;
}

export const GroupedSidebarNav: React.FC<GroupedSidebarNavProps> = ({
  groups,
  children,
  title,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const allItems = groups.flatMap(g => g.items);
  const activePath = allItems.find(item => location.pathname === item.path)?.path;

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ display: 'flex', gap: 3, width: '100%' }}>
      <Paper
        sx={{
          width: 240,
          flexShrink: 0,
          p: 2,
          height: 'fit-content',
          position: 'sticky',
          top: 80,
          borderRadius: 2,
        }}
      >
        {title && (
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, px: 1 }}>
            {title}
          </Typography>
        )}
        <List disablePadding>
          {groups.map((group, groupIndex) => (
            <React.Fragment key={group.title}>
              {groupIndex > 0 && <Divider sx={{ my: 1.5 }} />}
              <Typography
                variant="caption"
                sx={{
                  px: 1,
                  py: 0.5,
                  display: 'block',
                  color: 'text.secondary',
                  fontWeight: 'bold',
                  textTransform: 'uppercase',
                  fontSize: '0.65rem',
                  letterSpacing: '0.5px',
                }}
              >
                {group.title}
              </Typography>
              {group.items.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <ListItem disablePadding key={item.path} sx={{ mb: 0.25 }}>
                    <ListItemButton
                      onClick={() => handleNavigate(item.path)}
                      selected={isActive}
                      sx={{
                        borderRadius: 1.5,
                        py: 0.6,
                        px: 1.5,
                        '&.Mui-selected': {
                          backgroundColor: 'primary.main',
                          color: 'primary.contrastText',
                          '&:hover': { backgroundColor: 'primary.dark' },
                        },
                        '&:hover': {
                          backgroundColor: isActive ? 'primary.dark' : 'action.hover',
                        },
                      }}
                    >
                      <ListItemText
                        primary={item.label}
                        primaryTypographyProps={{
                          variant: 'body2',
                          fontWeight: isActive ? 'bold' : 'regular',
                          fontSize: '0.8rem',
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </React.Fragment>
          ))}
        </List>
      </Paper>

      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
        {children}
      </Box>
    </Box>
  );
};
