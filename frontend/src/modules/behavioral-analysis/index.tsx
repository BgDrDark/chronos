import { lazy } from 'react';

const BehavioralAnalysisPage = lazy(() => import('./components/BehavioralAnalysisPage'));
const RuleBuilderPage = lazy(() => import('./components/RuleBuilderPage'));
const SettingsPage = lazy(() => import('./components/SettingsPage'));
const OrganizationalHealthPage = lazy(() => import('./components/OrganizationalHealthPage'));
const BiasMonitorPage = lazy(() => import('./components/BiasMonitorPage'));
const EmployeeProfilePage = lazy(() => import('./components/EmployeeProfilePage'));
const SystemHealthPage = lazy(() => import('./components/SystemHealthPage'));
const MyBehavioralProfilePage = lazy(() => import('./components/MyBehavioralProfilePage'));

export const behavioralAnalysisModule = {
  code: 'behavioral_analysis',
  name: 'Поведенчески анализ',
  icon: 'Psychology',
  routes: [
    { path: '/admin/behavioral-analysis', element: <BehavioralAnalysisPage /> },
    { path: '/admin/behavioral-analysis/rules', element: <RuleBuilderPage /> },
    { path: '/admin/behavioral-analysis/settings', element: <SettingsPage /> },
    { path: '/admin/behavioral-analysis/health', element: <OrganizationalHealthPage /> },
    { path: '/admin/behavioral-analysis/bias', element: <BiasMonitorPage /> },
    { path: '/admin/behavioral-analysis/employee/:id', element: <EmployeeProfilePage /> },
    { path: '/admin/behavioral-analysis/system', element: <SystemHealthPage /> },
    { path: '/my-behavioral-profile', element: <MyBehavioralProfilePage /> },
  ],
  isVisible: (userRole: string, moduleStatus: boolean) => 
    (userRole === 'admin' || userRole === 'super_admin') && moduleStatus,
};

export const myBehavioralProfileRoute = {
  path: '/my-behavioral-profile',
  element: <MyBehavioralProfilePage />,
  isVisible: (_userRole: string, moduleStatus: boolean) => moduleStatus,
};

export * from './types';
export * from './api/queries';
export * from './api/mutations';
