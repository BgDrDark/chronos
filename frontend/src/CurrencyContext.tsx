import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery, gql } from '@apollo/client';

// Simple query to just get the currency
const GET_GLOBAL_CURRENCY = gql`
  query GetGlobalCurrency {
    globalPayrollConfig {
      currency
    }
  }
`;

interface CurrencyContextType {
  currency: string;
  refreshCurrency: () => void;
}

const CurrencyContext = createContext<CurrencyContextType>({
  currency: 'EUR', // Default fallback
  refreshCurrency: () => {},
});

export const useCurrency = () => useContext(CurrencyContext);

export const CurrencyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currency, setCurrency] = useState('EUR');
  const { data, refetch } = useQuery(GET_GLOBAL_CURRENCY, {
    fetchPolicy: 'cache-and-network',
    onCompleted: (data) => {
        if (data?.globalPayrollConfig?.currency) {
            setCurrency(data.globalPayrollConfig.currency);
        }
    }
  });

  const refreshCurrency = () => {
      refetch().then(res => {
          if (res.data?.globalPayrollConfig?.currency) {
              setCurrency(res.data.globalPayrollConfig.currency);
          }
      });
  };

  // Also update if data changes automatically
  useEffect(() => {
      if (data?.globalPayrollConfig?.currency) {
          setCurrency(data.globalPayrollConfig.currency);
      }
  }, [data]);

  return (
    <CurrencyContext.Provider value={{ currency, refreshCurrency }}>
      {children}
    </CurrencyContext.Provider>
  );
};
