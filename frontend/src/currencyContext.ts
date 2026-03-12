import { createContext, useContext } from 'react';

export interface CurrencyContextType {
  currency: string;
  refreshCurrency: () => void;
}

export const CurrencyContext = createContext<CurrencyContextType>({
  currency: 'EUR',
  refreshCurrency: () => {},
});

export const useCurrency = () => useContext(CurrencyContext);
