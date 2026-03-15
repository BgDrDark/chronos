import MedicalServicesIcon from '@mui/icons-material/MedicalServices';
import BeachAccessIcon from '@mui/icons-material/BeachAccess';
import WeekendIcon from '@mui/icons-material/Weekend';
import WorkIcon from '@mui/icons-material/Work';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import WarningIcon from '@mui/icons-material/Warning';
import CelebrationIcon from '@mui/icons-material/Celebration';
import EditIcon from '@mui/icons-material/Edit';
import type { CSSProperties } from 'react';

interface IconProps {
  style?: CSSProperties;
  [key: string]: unknown;
}

// Colors mapped to shift types
export const ShiftTypeColors: Record<string, string> = {
  regular: '#3f51b5',      // Indigo
  paid_leave: '#ed6c02',   // Orange
  sick_leave: '#d32f2f',   // Red
  unpaid_leave: '#9e9e9e', // Grey
  day_off: '#2e7d32',      // Green
  missing: '#f44336',      // Red (Alert)
  manual_log: '#f50057',   // Vivid Pink (More visible)
  auto_log: '#009688',     // Teal
  public_holiday: '#ffc107' // Amber
};

// Labels in Bulgarian
export const ShiftTypeLabels: Record<string, string> = {
  regular: 'Редовна смяна',
  paid_leave: 'Платен отпуск',
  sick_leave: 'Болничен',
  unpaid_leave: 'Неплатен отпуск',
  day_off: 'Почивен ден',
  missing: 'Липсваща смяна',
  manual_log: 'Ръчен запис',
  auto_log: 'Автоматичен запис',
  public_holiday: 'Официален празник'
};

// Helper to get Icon component
export const getShiftIcon = (type: string, props: IconProps = {}): React.ReactElement => {
  const style = { fontSize: '1rem', ...props.style };
  
  switch (type) {
    case 'sick_leave': return <MedicalServicesIcon style={style} {...props} />;
    case 'paid_leave': return <BeachAccessIcon style={style} {...props} />;
    case 'unpaid_leave': return <WeekendIcon style={style} {...props} />;
    case 'day_off': return <WeekendIcon style={style} {...props} />; // Same as unpaid/weekend
    case 'regular': return <WorkIcon style={style} {...props} />;
    case 'missing': return <WarningIcon style={style} {...props} />;
    case 'manual_log': return <EditIcon style={style} {...props} />;
    case 'auto_log': return <AccessTimeIcon style={style} {...props} />;
    case 'public_holiday': return <CelebrationIcon style={style} {...props} />;
    default: return <WorkIcon style={style} {...props} />;
  }
};

export const getShiftStyle = (type: string) => {
  return {
    color: ShiftTypeColors[type] || ShiftTypeColors.regular,
    label: ShiftTypeLabels[type] || type,
    icon: getShiftIcon(type)
  };
};
