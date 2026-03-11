import { createContext } from 'react';

export interface CurrencyContextType {
  currency: string;
  refreshCurrency: () => void;
}

export const CurrencyContext = createContext<CurrencyContextType>({
  currency: 'EUR',
  refreshCurrency: () => {},
});
