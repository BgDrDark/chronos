export type SortOrder = 'asc' | 'desc';
export type PaginationParams = {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: SortOrder;
};

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success?: boolean;
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
  render?: (value: unknown, record: T) => React.ReactNode;
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

import type { ReactNode } from 'react';