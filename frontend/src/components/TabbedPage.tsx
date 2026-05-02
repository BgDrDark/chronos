import React, { useMemo } from 'react';
import { Box, Tabs, Tab, Paper } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';

export interface TabItem {
  label: string;
  path: string;
  icon?: React.ReactElement;
}

interface TabbedPageProps {
  tabs: TabItem[];
  defaultTabPath: string;
  children: React.ReactNode;
  basePath?: string;
}

export const TabbedPage: React.FC<TabbedPageProps> = ({
  tabs,
  defaultTabPath,
  children,
  basePath,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const currentTabIndex = useMemo(() => {
    const currentPath = location.pathname;
    const index = tabs.findIndex(tab => currentPath === tab.path || currentPath.startsWith(tab.path + '/'));
    return index >= 0 ? index : 0;
  }, [location.pathname, tabs]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    const targetTab = tabs[newValue];
    if (targetTab) {
      navigate(targetTab.path);
    }
  };

  React.useEffect(() => {
    if (basePath && location.pathname === basePath) {
      navigate(defaultTabPath, { replace: true });
    }
  }, [basePath, defaultTabPath, location.pathname, navigate]);

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ mb: 2, borderRadius: 2 }}>
        <Tabs
          value={currentTabIndex}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            '& .MuiTab-root': {
              minHeight: 48,
              fontSize: '0.875rem',
              fontWeight: 500,
              textTransform: 'none',
            },
            '& .Mui-selected': {
              fontWeight: 'bold',
            },
          }}
        >
          {tabs.map((tab) => (
            <Tab
              key={tab.path}
              label={tab.label}
              icon={tab.icon}
              iconPosition="start"
            />
          ))}
        </Tabs>
      </Paper>
      <Box sx={{ mt: 2 }}>
        {children}
      </Box>
    </Box>
  );
};
