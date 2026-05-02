export * from './auth.types';
export * from './accounting.types';
export * from './inventory.types';
export * from './production.types';
export * from './access.types';
export * from './hr.types';
export * from './common.types';

export type ContractStatus = 'draft' | 'signed' | 'linked';
export type ContractType = 'full_time' | 'part_time' | 'contractor' | 'internship';

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success?: boolean;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ErrorResponse {
  code?: string;
  message: string;
  details?: Record<string, string[]>;
}

export interface Option {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface SelectOption extends Option {
  group?: string;
}

export interface TableColumn<T = unknown> {
  key: keyof T | string;
  title: string;
  sortable?: boolean;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, record: T) => unknown;
}

export interface FilterConfig {
  field: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'daterange' | 'number' | 'boolean';
  options?: Option[];
  placeholder?: string;
  defaultValue?: unknown;
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: unknown;
  message: string;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export interface OrderStatus {
  id: number;
  name: string;
  color?: string;
}

export interface ScheduleLog {
  id: number;
  logId?: number;
  userId: number;
  date: string;
  shiftName?: string;
  startTime?: string;
  endTime?: string;
  start?: string | Date;
  end?: string | Date;
  isManual?: boolean;
}

export interface SaftResult {
  xmlContent?: string;
  fileName?: string;
  validationResult?: unknown;
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  
  if (typeof error === 'object' && error !== null) {
    const err = error as { 
      response?: { data?: { detail?: string | { message?: string } } }; 
      message?: string;
      graphQLErrors?: Array<{ message?: string }>;
      networkError?: { message?: string };
    };
    
    if (err.graphQLErrors && err.graphQLErrors.length > 0) {
      return err.graphQLErrors[0].message || 'Грешка от сървъра';
    }
    
    if (err.networkError) {
      return 'Няма връзка със сървъра';
    }
    
    if (err.response?.data?.detail) {
      if (typeof err.response.data.detail === 'string') return err.response.data.detail;
      if (err.response.data.detail.message) return err.response.data.detail.message;
    }
    if (err.message) return err.message;
  }
  
  return 'Неизвестна грешка';
}