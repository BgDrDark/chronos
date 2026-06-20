import React, { createContext, useContext, useState, ReactNode } from 'react';

interface DriverModeContextType {
  isDriverMode: boolean;
  toggleDriverMode: () => void;
}

const DriverModeContext = createContext<DriverModeContextType | undefined>(undefined);

export const DriverModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isDriverMode, setIsDriverMode] = useState(() => {
    return localStorage.getItem('driverMode') === 'true';
  });

  const toggleDriverMode = () => {
    setIsDriverMode(prev => {
      const newVal = !prev;
      localStorage.setItem('driverMode', String(newVal));
      return newVal;
    });
  };

  return (
    <DriverModeContext.Provider value={{ isDriverMode, toggleDriverMode }}>
      {children}
    </DriverModeContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useDriverMode = () => {
  const context = useContext(DriverModeContext);
  if (!context) {
    throw new Error('useDriverMode must be used within a DriverModeProvider');
  }
  return context;
};
