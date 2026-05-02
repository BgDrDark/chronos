import { formatDate } from '../../utils/dateUtils';
export const getInvoiceStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    draft: 'Чернова',
    sent: 'Изпратена',
    paid: 'Платена',
    overdue: 'Просрочена',
    cancelled: 'Анулирана',
  };
  return statusMap[status] || status;
};

export const getInvoiceStatusColor = (
  status: string
): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
  const colorMap: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning'> = {
    draft: 'default',
    sent: 'info',
    paid: 'success',
    overdue: 'warning',
    cancelled: 'error',
  };
  return colorMap[status] || 'default';
};

export const isInvoiceReadOnly = (status: string): boolean => {
  return ['paid', 'cancelled', 'corrected'].includes(status);
};

export interface BatchInfo {
  batchNumber: string;
  expiryDate: string;
}

export const getBatchInfo = (batch: unknown): BatchInfo => {
  if (!batch || typeof batch !== 'object') return { batchNumber: '-', expiryDate: '-' };
  const b = batch as Record<string, unknown>;
  return {
    batchNumber: (b.batchNumber as string) || '-',
    expiryDate: b.expiryDate
      ? formatDate(b.expiryDate as string)
      : '-',
  };
};