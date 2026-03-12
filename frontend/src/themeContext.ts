import { createContext, useContext } from 'react';

export interface DashboardConfig {
  showChart: boolean;
  showWeeklyTable: boolean;
}

export interface ThemeContextType {
  mode: 'light' | 'dark';
  toggleTheme: () => void;
  dashboardConfig: DashboardConfig;
  toggleDashboardWidget: (widget: keyof DashboardConfig) => void;
}

export const ThemeContext = createContext<ThemeContextType>({
  mode: 'light',
  toggleTheme: () => {},
  dashboardConfig: { showChart: true, showWeeklyTable: true },
  toggleDashboardWidget: () => {},
});

export const useAppTheme = () => useContext(ThemeContext);
