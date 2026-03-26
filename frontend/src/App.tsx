import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { ErrorProvider } from './context/ErrorContext';
import MainLayout from './components/MainLayout';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import UserManagementPage from './pages/UserManagementPage';
import PayrollPage from './pages/PayrollPage';
import SchedulesPage from './pages/SchedulesPage';
import SettingsPage from './pages/SettingsPage';
import MySchedulePage from './pages/MySchedulePage';
import LeavesPage from './pages/LeavesPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import DocumentationPage from './pages/DocumentationPage';
import ProfilePage from './pages/ProfilePage';
import KioskAdminPage from './pages/KioskAdminPage';
import KioskTerminalPage from './pages/KioskTerminalPage';
import UnifiedKiosk from './pages/UnifiedKiosk';
import GatewayAdminPage from './pages/GatewayAdminPage';
import MyCardPage from './pages/MyCardPage';
import WarehousePage from './pages/WarehousePage';
import RecipesPage from './pages/RecipesPage';
import MenuPricingPage from './pages/MenuPricingPage';
import OrdersPage from './pages/OrdersPage';
import ProductionControlPage from './pages/ProductionControlPage';
import AccountingPage from './pages/AccountingPage';
import NotificationsPage from './pages/NotificationsPage';
import LogisticsPage from './pages/LogisticsPage';
import FleetPage from './pages/FleetPage';
import VehicleProfilePage from './pages/VehicleProfilePage';
import FleetReportsPage from './pages/FleetReportsPage';
import TRZSettingsPage from './pages/TRZSettingsPage';
import { useQuery } from '@apollo/client';
import { ME_QUERY } from './graphql/queries';

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading, data } = useQuery(ME_QUERY);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data || !data.me || !['admin', 'super_admin'].includes(data.me.role.name)) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  const location = useLocation();
  const isKioskMode = location.pathname === '/kiosk';
  const isCardMode = location.pathname === '/my-card';
  const isTerminalMode = location.pathname === '/kiosk/terminal';

  if (isKioskMode || isTerminalMode) {
    return (
      <AdminRoute>
        <Routes>
          <Route path="/kiosk" element={<UnifiedKiosk />} />
          <Route path="/kiosk/terminal" element={<UnifiedKiosk />} />
        </Routes>
      </AdminRoute>
    );
  }

  if (isCardMode) {
    return (
      <Routes>
        <Route path="/my-card" element={<MyCardPage />} />
      </Routes>
    );
  }

  if (location.pathname === '/login') {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    );
  }

  return (
    <ErrorProvider>
      <MainLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/profile/:id" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/my-schedule" element={<MySchedulePage />} />
        
        {/* Отпуски - само подменюта без главен таб */}
        <Route path="/leaves/my-requests" element={<LeavesPage tab="my-requests" />} />
        <Route path="/leaves/approvals" element={<LeavesPage tab="approvals" />} />
        <Route path="/leaves/all" element={<LeavesPage tab="all" />} />
        
        <Route
          path="/documentation"
          element={
            <AdminRoute>
              <DocumentationPage />
            </AdminRoute>
          }
        />
        
        {/* Табло присъствие */}
        <Route
          path="/admin/presence"
          element={
            <AdminRoute>
              <AdminDashboardPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/presence/attendance"
          element={
            <AdminRoute>
              <AdminDashboardPage tab="attendance" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/presence/analytics"
          element={
            <AdminRoute>
              <AdminDashboardPage tab="analytics" />
            </AdminRoute>
          }
        />
        
        {/* Потребители */}
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <UserManagementPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/users/list"
          element={
            <AdminRoute>
              <UserManagementPage tab="list" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/users/org-structure"
          element={
            <AdminRoute>
              <UserManagementPage tab="org-structure" />
            </AdminRoute>
          }
        />
        
        <Route
          path="/admin/payroll"
          element={
            <AdminRoute>
              <PayrollPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/payroll/settings"
          element={
            <AdminRoute>
              <PayrollPage tab="settings" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/payroll/payments"
          element={
            <AdminRoute>
              <PayrollPage tab="payments" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/payroll/declarations"
          element={
            <AdminRoute>
              <PayrollPage tab="declarations" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/payroll/reports"
          element={
            <AdminRoute>
              <PayrollPage tab="reports" />
            </AdminRoute>
          }
        />
        
        {/* Графици */}
        <Route
          path="/admin/schedules"
          element={
            <AdminRoute>
              <SchedulesPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/schedules/calendar"
          element={
            <AdminRoute>
              <SchedulesPage tab="calendar" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/schedules/current"
          element={
            <AdminRoute>
              <SchedulesPage tab="current" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/schedules/shifts"
          element={
            <AdminRoute>
              <SchedulesPage tab="shifts" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/schedules/templates"
          element={
            <AdminRoute>
              <SchedulesPage tab="templates" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/schedules/bulk"
          element={
            <AdminRoute>
              <SchedulesPage tab="bulk" />
            </AdminRoute>
          }
        />
        
        <Route
          path="/admin/kiosk"
          element={
            <AdminRoute>
              <KioskAdminPage tab="kiosk" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/gateways"
          element={
            <AdminRoute>
              <KioskAdminPage tab="gateways" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/zones"
          element={
            <AdminRoute>
              <KioskAdminPage tab="zones" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/doors"
          element={
            <AdminRoute>
              <KioskAdminPage tab="doors" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/codes"
          element={
            <AdminRoute>
              <KioskAdminPage tab="codes" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/logs"
          element={
            <AdminRoute>
              <KioskAdminPage tab="logs" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/users"
          element={
            <AdminRoute>
              <KioskAdminPage tab="users" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/terminals"
          element={
            <AdminRoute>
              <KioskAdminPage tab="terminals" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/kiosk/terminal"
          element={
            <AdminRoute>
              <KioskTerminalPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/gateways"
          element={
            <AdminRoute>
              <GatewayAdminPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/warehouse"
          element={
            <AdminRoute>
              <WarehousePage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/recipes"
          element={
            <AdminRoute>
              <RecipesPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/menu-pricing"
          element={
            <AdminRoute>
              <MenuPricingPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/orders"
          element={
            <AdminRoute>
              <OrdersPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/production/control"
          element={
            <AdminRoute>
              <ProductionControlPage />
            </AdminRoute>
          }
        />
        
        {/* Счетоводство */}
        <Route
          path="/admin/accounting"
          element={
            <AdminRoute>
              <AccountingPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/incoming"
          element={
            <AdminRoute>
              <AccountingPage tab="incoming" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/outgoing"
          element={
            <AdminRoute>
              <AccountingPage tab="outgoing" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/cash-journal"
          element={
            <AdminRoute>
              <AccountingPage tab="cash-journal" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/operations"
          element={
            <AdminRoute>
              <AccountingPage tab="operations" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/daily"
          element={
            <AdminRoute>
              <AccountingPage tab="daily" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/monthly"
          element={
            <AdminRoute>
              <AccountingPage tab="monthly" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/yearly"
          element={
            <AdminRoute>
              <AccountingPage tab="yearly" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/proforma"
          element={
            <AdminRoute>
              <AccountingPage tab="proforma" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/corrections"
          element={
            <AdminRoute>
              <AccountingPage tab="corrections" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/bank"
          element={
            <AdminRoute>
              <AccountingPage tab="bank" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/accounts"
          element={
            <AdminRoute>
              <AccountingPage tab="accounts" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/vat"
          element={
            <AdminRoute>
              <AccountingPage tab="vat" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/accounting/saft"
          element={
            <AdminRoute>
              <AccountingPage tab="saft" />
            </AdminRoute>
          }
        />
        
        {/* Уведомления */}
        <Route
          path="/admin/notifications"
          element={
            <AdminRoute>
              <NotificationsPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/notifications/events"
          element={
            <AdminRoute>
              <NotificationsPage tab="events" />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/notifications/smtp"
          element={
            <AdminRoute>
              <NotificationsPage tab="smtp" />
            </AdminRoute>
          }
        />
        
        {/* Логистика */}
        <Route
          path="/admin/logistics"
          element={
            <AdminRoute>
              <LogisticsPage />
            </AdminRoute>
          }
        />
        
        {/* Автомобили (Fleet) */}
        <Route
          path="/admin/fleet"
          element={
            <AdminRoute>
              <FleetPage />
            </AdminRoute>
          }
        />
        
        {/* Профил на автомобил */}
        <Route
          path="/admin/fleet/:id"
          element={
            <AdminRoute>
              <VehicleProfilePage />
            </AdminRoute>
          }
        />
        
        {/* Справки - Автомобили */}
        <Route
          path="/admin/fleet/reports"
          element={
            <AdminRoute>
              <FleetReportsPage />
            </AdminRoute>
          }
        />
        
        {/* ТРЗ Настройки */}
        <Route
          path="/admin/payroll/trz-settings"
          element={
            <AdminRoute>
              <TRZSettingsPage />
            </AdminRoute>
          }
        />
        
        {/* Шаблони */}
        <Route
          path="/admin/payroll/templates"
          element={
            <AdminRoute>
              <PayrollPage tab="templates" />
            </AdminRoute>
          }
        />
        
        {/* Допълнителни споразумения */}
        <Route
          path="/admin/payroll/annexes"
          element={
            <AdminRoute>
              <PayrollPage tab="annexes" />
            </AdminRoute>
          }
        />
        
        {/* Трудови договори */}
        <Route
          path="/admin/payroll/contracts"
          element={
            <AdminRoute>
              <PayrollPage tab="contracts" />
            </AdminRoute>
          }
        />
        </Routes>
      </MainLayout>
    </ErrorProvider>
  );
}

export default App;