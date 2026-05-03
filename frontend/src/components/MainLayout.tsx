import React, { useState, useEffect } from 'react';
import {
  AppBar, Box, CssBaseline, Divider, Drawer as MuiDrawer, IconButton,
  Toolbar, Typography, Alert, AlertTitle, styled, type Theme, type CSSObject
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Logout as LogoutIcon,
  CalendarMonth as CalendarIcon,
  Settings as SettingsIcon,
  FlightTakeoff as FlightTakeoffIcon,
  AssignmentInd as AssignmentIndIcon,
  ErrorOutline as ErrorIcon,
  HelpOutline as HelpOutlineIcon,
  AccountCircle as AccountCircleIcon,
  QrCodeScanner as QrCodeScannerIcon,
  Warehouse as WarehouseIcon,
  RestaurantMenu as RecipeIcon,
  AddShoppingCart as OrderIcon,
  Assignment as TaskIcon,
  Notifications as NotificationsIcon,
  Receipt as ReceiptIcon,
  MeetingRoom as DoorIcon,
  LocalShipping as LogisticsIcon,
  DirectionsCar as FleetIcon,
  Assessment as ReportsIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Work as WorkIcon,
  AttachMoney as MoneyIcon,
  Kitchen as KitchenIcon,
} from '@mui/icons-material';
import { Link as RouterLink, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useApolloClient } from '@apollo/client';
import { ME_QUERY, MODULES_QUERY } from '../graphql/queries';
import useSessionActivity from '../hooks/useSessionActivity';
import { SidebarMenu, type MenuItem } from './SidebarMenu';

const drawerWidth = 260;
const collapsedDrawerWidth = 72;

const openedMixin = (theme: Theme): CSSObject => ({
  width: drawerWidth,
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: 'hidden',
  borderRight: `1px solid ${theme.palette.divider}`,
});

const closedMixin = (theme: Theme): CSSObject => ({
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  overflowX: 'hidden',
  width: collapsedDrawerWidth,
  borderRight: `1px solid ${theme.palette.divider}`,
});

const Drawer = styled(MuiDrawer, { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open }) => ({
    width: drawerWidth,
    flexShrink: 0,
    whiteSpace: 'nowrap',
    boxSizing: 'border-box',
    ...(open && {
      ...openedMixin(theme),
      '& .MuiDrawer-paper': openedMixin(theme),
    }),
    ...(!open && {
      ...closedMixin(theme),
      '& .MuiDrawer-paper': closedMixin(theme),
    }),
  }),
);

const SessionTimer: React.FC = () => {
    const [seconds, setSeconds] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setSeconds(s => s + 1);
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    const formatTime = (totalSeconds: number) => {
        const h = Math.floor(totalSeconds / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);
        const s = totalSeconds % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
            Сесия: {formatTime(seconds)}
        </Typography>
    );
};

interface Props {
  children: React.ReactNode;
}

const MainLayout: React.FC<Props> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('sidebarCollapsed') === 'true';
  });
  const [smtpAlertOpen, setSmtpAlertOpen] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const navigate = useNavigate();
  const location = useLocation();
  const client = useApolloClient();
  
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', isCollapsed.toString());
  }, [isCollapsed]);

  useEffect(() => {
    const newExpanded = new Set<string>();
    menuItems.forEach(item => {
      if (item.children && item.children.some(child => child.path === location.pathname)) {
        newExpanded.add(item.text);
      }
    });
    setExpandedSections(newExpanded);
  }, [location.pathname]);

  // Session activity hook - auto refresh and idle timeout
  useSessionActivity({
    idleTimeoutMs: 15 * 60 * 1000,
    refreshBeforeMs: 5 * 60 * 1000,
    onIdleTimeout: () => {
      client.clearStore().then(() => {
        window.location.href = '/login';
      });
    },
    onRefreshNeeded: () => {
      console.log('Session auto-refreshed due to inactivity');
    }
  });

  const { data } = useQuery(ME_QUERY);
  const { data: modulesData } = useQuery(MODULES_QUERY);
  const user = data?.me;

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleCollapseToggle = () => {
    setIsCollapsed(!isCollapsed);
    if (!isCollapsed) {
      setExpandedSections(new Set());
    }
  };

  // Read CSRF token from cookie
  const getCsrfToken = (): string | null => {
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) === 0) {
        return c.substring(name.length, c.length);
      }
    }
    return null;
  };

  const handleLogout = async () => {
    const csrfToken = getCsrfToken();
    const envUrl = import.meta.env.VITE_API_URL;
    const baseUrl = envUrl ? (envUrl.endsWith('/') ? envUrl : `${envUrl}/`) : '/';
    try {
      await fetch(`${baseUrl}auth/logout`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken || '',
        },
        credentials: 'include',
      });
    } catch (err) {
      console.error("Server logout failed:", err);
    } finally {
      navigate('/login', { replace: true });
      await client.clearStore();
    }
  };

  const isAdmin = user?.role && ['admin', 'super_admin'].includes(user.role.name);
  const modules = modulesData?.modules || [];

  interface Module {
    code: string;
    isEnabled: boolean;
  }

  const isEnabled = (code: string) => {
    const mod = modules.find((m: Module) => m.code === code);
    return mod ? mod.isEnabled : true;
  };

  const showSmtpWarning = isAdmin && user?.isSmtpConfigured === false && smtpAlertOpen;
  const publicPages = ['/login', '/forgot-password', '/reset-password', '/kiosk', '/kiosk/terminal', '/my-card'];
  const isPublicPage = publicPages.includes(location.pathname);
  const displayName = user ? (user.firstName && user.lastName ? `${user.firstName} ${user.lastName}` : user.email) : '';

  const menuItems = [
    { text: 'Табло', icon: <DashboardIcon />, path: '/', visible: !!user },
    { text: 'Профил', icon: <AccountCircleIcon />, path: '/profile', visible: !!user },
    { text: 'Моят график', icon: <CalendarIcon />, path: '/my-schedule', visible: !!user && isEnabled('shifts') },
    { 
      text: 'Отпуски', 
      icon: <FlightTakeoffIcon />, 
      visible: !!user && isEnabled('shifts'),
      children: [
        { text: 'Моите заявки', path: '/leaves/my-requests', visible: !!user },
        { text: 'Одобрения', path: '/leaves/approvals', visible: isAdmin },
        { text: 'Всички заявки', path: '/leaves/all', visible: isAdmin },
      ]
    },
    { 
      text: 'Табло присъствие', 
      icon: <AssignmentIndIcon />, 
      visible: isAdmin && isEnabled('shifts'),
      children: [
        { text: 'Присъствие', path: '/admin/presence/attendance', visible: true },
        { text: 'Анализи и KPI', path: '/admin/presence/analytics', visible: true },
      ]
    },
    { 
      text: 'Графици', 
      icon: <CalendarIcon />, 
      visible: isAdmin && isEnabled('shifts'),
      children: [
        { text: 'Календар', path: '/admin/schedules/calendar', visible: true },
        { text: 'Текущ график', path: '/admin/schedules/current', visible: true },
        { text: 'Управление на смени', path: '/admin/schedules/shifts', visible: true },
        { text: 'Шаблони и Ротации', path: '/admin/schedules/templates', visible: true },
        { text: 'Масово назначаване', path: '/admin/schedules/bulk', visible: true },
      ]
    },
    { 
      text: 'Потребители', 
      icon: <PeopleIcon />, 
      visible: isAdmin,
      children: [
        { text: 'Списък служители', path: '/admin/users/list', visible: true },
        { text: 'Организационна структура', path: '/admin/users/org-structure', visible: true },
      ]
    },
    { 
      text: 'Отдел ТРЗ', 
      icon: <WorkIcon />, 
      visible: isAdmin && isEnabled('salaries'),
      children: [
        { text: 'ТРЗ Настройки', path: '/admin/payroll/trz-settings', visible: true },
        { text: 'Шаблони', path: '/admin/payroll/templates', visible: true },
        { text: 'Допълнителни споразумения', path: '/admin/payroll/annexes', visible: true },
        { text: 'Трудови договори', path: '/admin/payroll/contracts', visible: true },
        { text: 'Плащания', path: '/admin/payroll/payments', visible: true },
        { text: 'Празници', path: '/admin/payroll/declarations', visible: true },
        { text: 'Справки', path: '/admin/payroll/reports', visible: true },
        { text: 'Настройки', path: '/admin/payroll/settings', visible: true },
      ]
    },
    { 
      text: 'Счетоводство', 
      icon: <ReceiptIcon />, 
      visible: isAdmin && isEnabled('accounting'),
      children: [
        { text: 'Входящи фактури', path: '/admin/accounting/incoming', visible: true },
        { text: 'Изходящи фактури', path: '/admin/accounting/outgoing', visible: true },
        { text: 'Проформа фактури', path: '/admin/accounting/proforma', visible: true },
        { text: 'Корекции', path: '/admin/accounting/corrections', visible: true },
        { text: 'Банка', path: '/admin/accounting/bank', visible: true },
        { text: 'Сметкоплан', path: '/admin/accounting/accounts', visible: true },
        { text: 'Касов дневник', path: '/admin/accounting/cash-journal', visible: true },
        { text: 'Операции', path: '/admin/accounting/operations', visible: true },
        { text: 'Счетоводни записи', path: '/admin/accounting/accounting-entries', visible: true },
        { text: 'ДДС регистри', path: '/admin/accounting/vat', visible: true },
        { text: 'SAF-T', path: '/admin/accounting/saft', visible: true },
        { text: 'Дневен отчет', path: '/admin/accounting/daily', visible: true },
        { text: 'Месечен отчет', path: '/admin/accounting/monthly', visible: true },
        { text: 'Годишен отчет', path: '/admin/accounting/yearly', visible: true },
      ]
    },
    { 
      text: 'Уведомления', 
      icon: <NotificationsIcon />, 
      visible: isAdmin && isEnabled('notifications'),
      children: [
        { text: 'Събития и Уведомления', path: '/admin/notifications/events', visible: true },
        { text: 'SMTP Настройки', path: '/admin/notifications/smtp', visible: true },
      ]
    },
    { text: 'Настройки', icon: <SettingsIcon />, path: '/settings', visible: isAdmin },
    { text: 'Документация', icon: <HelpOutlineIcon />, path: '/documentation', visible: isAdmin && isEnabled('integrations') },
    { 
      text: 'Отдел КД', 
      icon: <QrCodeScannerIcon />, 
      visible: isAdmin && isEnabled('kiosk'),
      children: [
        { text: 'Конфигурация', path: '/admin/kiosk/config', visible: true },
        { text: 'Терминали', path: '/admin/kiosk/terminals', visible: true },
        { text: 'Gateways', path: '/admin/kiosk/gateways', visible: true },
        { text: 'Зони за достъп', path: '/admin/kiosk/zones', visible: true },
        { text: 'Врати', path: '/admin/kiosk/doors', visible: true },
        { text: 'Кодове', path: '/admin/kiosk/codes', visible: true },
        { text: 'Логове', path: '/admin/kiosk/logs', visible: true },
        { text: 'Потребители', path: '/admin/kiosk/users', visible: true },
      ]
    },
    { text: 'Склад', icon: <WarehouseIcon />, path: '/admin/warehouse', visible: isAdmin && isEnabled('confectionery') },
    { text: 'Рецепти', icon: <RecipeIcon />, path: '/admin/recipes', visible: isAdmin && isEnabled('confectionery') },
    { text: 'Цени Рецепти', icon: <MoneyIcon />, path: '/admin/menu-pricing', visible: isAdmin && isEnabled('confectionery') },
    { text: 'Поръчки', icon: <OrderIcon />, path: '/admin/orders', visible: isAdmin && isEnabled('confectionery') },
    { text: 'Контрол', icon: <TaskIcon />, path: '/admin/production/control', visible: isAdmin && isEnabled('confectionery') },
    { text: 'Логистика', icon: <LogisticsIcon />, path: '/admin/logistics', visible: isAdmin },
    { text: 'Автомобили', icon: <FleetIcon />, path: '/admin/fleet', visible: isAdmin },
    { text: 'Справки', icon: <ReportsIcon />, path: '/admin/fleet/reports', visible: isAdmin },
    { text: 'Терминал за присъствие', icon: <QrCodeScannerIcon />, path: '/kiosk', visible: isAdmin },
    { text: 'Терминал за достъп', icon: <DoorIcon />, path: '/kiosk/terminal', visible: isAdmin },
    { text: 'Производствен терминал', icon: <KitchenIcon />, path: '/admin/production/kiosk', visible: isAdmin && isEnabled('confectionery') },
  ];

  const handleToggleSection = (text: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(text)) {
        next.delete(text);
      } else {
        next.add(text);
      }
      return next;
    });
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      <Toolbar sx={{ display: 'flex', alignItems: 'center', justifyContent: isCollapsed ? 'center' : 'space-between', px: [1] }}>
        {!isCollapsed && (
          <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold', color: 'primary.main', ml: 1 }}>
            Работно Време
          </Typography>
        )}
        <IconButton onClick={handleCollapseToggle} sx={{ display: { xs: 'none', sm: 'inline-flex' } }}>
          {isCollapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
        </IconButton>
      </Toolbar>
      <Divider />
      <SidebarMenu
        items={menuItems}
        expandedSections={expandedSections}
        onToggleSection={handleToggleSection}
        isCollapsed={isCollapsed}
        onNavigate={() => { if (mobileOpen) setMobileOpen(false); }}
      />
      <Divider />
      <Box sx={{ p: 2, textAlign: 'center' }}>
        {!isCollapsed && (
          <Typography variant="caption" display="block" sx={{ color: 'text.secondary', mb: 1 }}>
            © Oblak24 Team © {new Date().getFullYear()}
          </Typography>
        )}
        <SessionTimer />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: isPublicPage ? '100%' : `calc(100% - ${isCollapsed ? collapsedDrawerWidth : drawerWidth}px)` },
          ml: { sm: isPublicPage ? 0 : `${isCollapsed ? collapsedDrawerWidth : drawerWidth}px` },
          transition: (theme) => theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          boxShadow: 'none',
          backgroundColor: 'background.default',
          borderBottom: '1px solid',
          borderColor: 'divider',
          color: 'text.primary',
          display: isPublicPage ? 'none' : 'flex',
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 'medium' }}>
            {(() => {
              const findMenuText = (items: MenuItem[]): string | null => {
                for (const item of items) {
                  if (item.path === location.pathname) {
                    return item.text;
                  }
                  if (item.children) {
                    const childMatch = item.children.find(c => c.path === location.pathname);
                    if (childMatch) {
                      return `${item.text} > ${childMatch.text}`;
                    }
                  }
                }
                return null;
              };
              return findMenuText(menuItems) || 'Работно Време';
            })()}
          </Typography>
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ display: { xs: 'none', md: 'block' }, textAlign: 'right' }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>{displayName}</Typography>
                <Typography variant="caption" color="text.secondary">{user.role?.description || user.role?.name}</Typography>
              </Box>
              <IconButton color="error" onClick={handleLogout} title="Изход" sx={{ bgcolor: 'error.lighter' }}>
                <LogoutIcon />
              </IconButton>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ 
            width: { sm: isPublicPage ? 0 : (isCollapsed ? collapsedDrawerWidth : drawerWidth) }, 
            flexShrink: { sm: 0 }, 
            display: isPublicPage ? 'none' : 'block' 
        }}
      >
        <MuiDrawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawerContent}
        </MuiDrawer>
        <Drawer
          variant="permanent"
          sx={{ display: { xs: 'none', sm: 'block' } }}
          open={!isCollapsed}
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          width: { sm: isPublicPage ? '100%' : `calc(100% - ${isCollapsed ? collapsedDrawerWidth : drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: (theme) => theme.palette.background.default,
          transition: (theme) => theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        }}
      >
        <Toolbar />
        
        {showSmtpWarning && (
            <Alert 
                severity="warning" 
                onClose={() => setSmtpAlertOpen(false)}
                sx={{ mb: 3, borderRadius: 2, border: '1px solid #ff9800', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}
                icon={<ErrorIcon fontSize="inherit" />}
            >
                <AlertTitle sx={{ fontWeight: 'bold' }}>Липсващи SMTP настройки</AlertTitle>
                Системата няма въведени данни за имейл сървър. Потребителите няма да получават уведомления и писма за забравена парола. 
                Моля, конфигурирайте ги в <RouterLink to="/admin/notifications/smtp" style={{ color: 'inherit', fontWeight: 'bold' }}>Уведомления</RouterLink>.
            </Alert>
        )}

        <Box sx={{ maxWidth: '1600px', margin: '0 auto' }}>
            {children}
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;
