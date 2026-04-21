import React, { useState } from 'react';
import { useQuery, gql } from '@apollo/client';
import { 
  CurrencyContext, 
  formatCurrencyValue, 
  getCurrencySymbolForCurrency,
  type CurrencyContextType 
} from './currencyContext';

const GET_GLOBAL_CURRENCY = gql`
  query GetGlobalCurrency {
    globalPayrollConfig {
      currency
    }
  }
`;

export const CurrencyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currency, setCurrency] = useState('EUR');
  const { refetch } = useQuery(GET_GLOBAL_CURRENCY, {
    fetchPolicy: 'cache-and-network',
    onCompleted: (data) => {
      if (data?.globalPayrollConfig?.currency) {
        setCurrency(data.globalPayrollConfig.currency);
      }
    },
  });

  const refreshCurrency = () => {
    refetch().then((res) => {
      if (res.data?.globalPayrollConfig?.currency) {
        setCurrency(res.data.globalPayrollConfig.currency);
      }
    });
  };

  const formatCurrency: CurrencyContextType['formatCurrency'] = (value) => {
    return formatCurrencyValue(value, currency);
  };

  const getCurrencySymbol: CurrencyContextType['getCurrencySymbol'] = () => {
    return getCurrencySymbolForCurrency(currency);
  };

  return (
    <CurrencyContext.Provider value={{ 
      currency, 
      refreshCurrency,
      formatCurrency,
      getCurrencySymbol 
    }}>
      {children}
    </CurrencyContext.Provider>
  );
};
