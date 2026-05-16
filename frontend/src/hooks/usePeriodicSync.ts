import { useEffect } from 'react';

export function usePeriodicSync() {
  useEffect(() => {
    if ('periodicSync' in navigator) {
      navigator.serviceWorker.ready.then(async (registration) => {
        try {
          await (registration as any).periodicSync.register('refresh-data', {
            minInterval: 24 * 60 * 60 * 1000,
          });
          console.log('Periodic sync registered');
        } catch (e) {
          console.error('Periodic sync registration failed:', e);
        }
      });
    }
  }, []);
}
