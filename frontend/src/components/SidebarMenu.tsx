import React from 'react';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Box,
  Tooltip,
} from '@mui/material';
import { ExpandMore, ExpandLess } from '@mui/icons-material';
import { Link as RouterLink, useLocation } from 'react-router-dom';

export interface MenuItem {
  text: string;
  icon?: React.ReactNode;
  path?: string;
  visible: boolean;
  children?: Omit<MenuItem, 'icon' | 'children'>[];
}

interface SidebarMenuProps {
  items: MenuItem[];
  expandedSections: Set<string>;
  onToggleSection: (text: string) => void;
  isCollapsed: boolean;
  onNavigate: () => void;
}

export const SidebarMenu: React.FC<SidebarMenuProps> = ({
  items,
  expandedSections,
  onToggleSection,
  isCollapsed,
  onNavigate,
}) => {
  const location = useLocation();

  const isItemActive = (item: MenuItem): boolean => {
    if (item.path && location.pathname === item.path) return true;
    if (item.children) {
      return item.children.some(child => child.path === location.pathname);
    }
    return false;
  };

  const isChildActive = (child: MenuItem): boolean => {
    return child.path === location.pathname;
  };

  return (
    <List sx={{ flexGrow: 1, pt: 1, overflowY: 'auto', overflowX: 'hidden' }}>
      {items.filter(item => item.visible).map((item) => {
        const hasChildren = item.children && item.children.length > 0;
        const isExpanded = expandedSections.has(item.text);
        const isActive = isItemActive(item);

        const buttonContent = (
          <ListItemButton
            component={item.path && !hasChildren ? RouterLink : 'div'}
            to={item.path && !hasChildren ? item.path : undefined}
            onClick={() => {
              if (hasChildren) {
                onToggleSection(item.text);
              }
              onNavigate();
            }}
            selected={isActive}
            sx={{
              minHeight: 48,
              justifyContent: isCollapsed ? 'center' : 'initial',
              px: 2.5,
              mx: isCollapsed ? 0.5 : 1,
              my: 0.25,
              borderRadius: isCollapsed ? '50%' : 2,
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                '& .MuiListItemIcon-root': { color: 'primary.contrastText' },
                '&:hover': { backgroundColor: 'primary.dark' }
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 0,
                mr: isCollapsed ? 'auto' : 2,
                justifyContent: 'center',
              }}
            >
              {item.icon}
            </ListItemIcon>
            {!isCollapsed && (
              <ListItemText 
                primary={item.text} 
                primaryTypographyProps={{ 
                  variant: 'body2', 
                  fontWeight: isActive ? 'bold' : 'medium',
                  noWrap: true
                }} 
              />
            )}
            {hasChildren && !isCollapsed && (
              isExpanded ? <ExpandLess sx={{ fontSize: '1.2rem', ml: 1 }} /> : <ExpandMore sx={{ fontSize: '1.2rem', ml: 1 }} />
            )}
          </ListItemButton>
        );

        return (
          <Box key={item.text}>
            <ListItem disablePadding sx={{ display: 'block' }}>
              {isCollapsed && hasChildren ? (
                <Tooltip title={item.text} placement="right" arrow>
                  {buttonContent}
                </Tooltip>
              ) : (
                buttonContent
              )}
            </ListItem>
            
            {hasChildren && item.children && !isCollapsed && (
              <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                <List disablePadding sx={{ mb: 1 }}>
                  {item.children
                    .filter(child => child.visible)
                    .map((child) => {
                      const isActiveChild = isChildActive(child);
                      return (
                        <ListItem key={child.text} disablePadding sx={{ display: 'block' }}>
                          <ListItemButton
                            component={child.path ? RouterLink : 'div'}
                            to={child.path}
                            selected={isActiveChild}
                            onClick={onNavigate}
                            sx={{
                              minHeight: 36,
                              pl: 6,
                              pr: 2,
                              mx: 1,
                              my: 0.25,
                              borderRadius: 1.5,
                              '&.Mui-selected': {
                                backgroundColor: 'action.selected',
                                color: 'primary.main',
                                fontWeight: 'bold',
                                '&:hover': { backgroundColor: 'action.hover' }
                              },
                            }}
                          >
                            <ListItemText 
                              primary={child.text} 
                              primaryTypographyProps={{ 
                                variant: 'body2', 
                                fontSize: '0.8rem',
                                fontWeight: isActiveChild ? 'bold' : 'regular',
                                noWrap: true
                              }} 
                            />
                          </ListItemButton>
                        </ListItem>
                      );
                    })}
                </List>
              </Collapse>
            )}
          </Box>
        );
      })}
    </List>
  );
};
