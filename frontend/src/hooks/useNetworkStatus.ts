import { useState, useEffect } from 'react';

interface NetworkStatus {
  isOnline: boolean;
  connectionType: string | null;
  isSlowConnection: boolean;
}

export function useNetworkStatus(): NetworkStatus {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [connectionType, setConnectionType] = useState<string | null>(null);
  const [isSlowConnection, setIsSlowConnection] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      updateConnectionInfo();
    };
    const handleOffline = () => {
      setIsOnline(false);
    };

    const updateConnectionInfo = () => {
      const conn = (navigator as any).connection;
      if (conn) {
        setConnectionType(conn.effectiveType || null);
        setIsSlowConnection(
          conn.effectiveType === 'slow-2g' ||
          conn.effectiveType === '2g' ||
          conn.saveData === true
        );
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const conn = (navigator as any).connection;
    if (conn) {
      updateConnectionInfo();
      conn.addEventListener('change', updateConnectionInfo);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (conn) conn.removeEventListener('change', updateConnectionInfo);
    };
  }, []);

  return { isOnline, connectionType, isSlowConnection };
}
