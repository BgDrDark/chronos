import { createContext, useContext } from 'react';

export interface CurrencyContextType {
  currency: string;
  refreshCurrency: () => void;
  formatCurrency: (value: number | string | null | undefined) => string;
  getCurrencySymbol: () => string;
}

export const CurrencyContext = createContext<CurrencyContextType>({
  currency: 'EUR',
  refreshCurrency: () => {},
  formatCurrency: (value) => {
    if (value === null || value === undefined) return '-';
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    if (isNaN(num)) return '-';
    return `${num.toFixed(2)} €`;
  },
  getCurrencySymbol: () => '€',
});

export const useCurrency = () => useContext(CurrencyContext);

export const formatCurrencyValue = (
  value: number | string | null | undefined,
  currency: string = 'EUR'
): string => {
  if (value === null || value === undefined) return '-';
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  if (isNaN(num)) return '-';
  
  const symbol = getCurrencySymbolForCurrency(currency);
  return `${num.toFixed(2)} ${symbol}`;
};

export const getCurrencySymbolForCurrency = (currency: string): string => {
  switch (currency.toUpperCase()) {
    case 'EUR':
      return '€';
    case 'USD':
      return '$';
    case 'BGN':
      return 'лв.';
    default:
      return currency;
  }
};
