import { useEffect, useCallback, useState } from 'react';
import { getPendingEntries, markSynced, markFailed, getPendingCount } from '../db/fleet-offline-store';
import { useNetworkStatus } from './useNetworkStatus';

export function useBackgroundSync() {
  const { isOnline } = useNetworkStatus();
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);

  const refreshPendingCount = useCallback(async () => {
    const count = await getPendingCount();
    setPendingCount(count);
  }, []);

  const syncAll = useCallback(async () => {
    if (!isOnline || syncing) return;
    setSyncing(true);
    try {
      const entries = await getPendingEntries();
      for (const entry of entries) {
        try {
          const mutation = entry.type === 'mileage'
            ? `mutation { createVehicleMileage(input: {
                vehicleId: ${entry.vehicleId},
                mileage: ${entry.payload.mileage},
                date: "${entry.payload.date}",
                notes: "${entry.payload.notes || ''}"
              }) { id } }`
            : `mutation { createVehicleFuel(input: {
                vehicleId: ${entry.vehicleId},
                liters: ${entry.payload.liters},
                price: ${entry.payload.price},
                total: ${entry.payload.total},
                fuelType: "${entry.payload.fuelType || 'dizel'}",
                date: "${entry.payload.date}",
                notes: "${entry.payload.notes || ''}",
                mileage: ${entry.payload.mileage || 0}
              }) { id } }`;

          const response = await fetch('/graphql', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: mutation }),
          });

          if (response.ok) {
            await markSynced(entry.id);
          } else {
            await markFailed(entry.id);
          }
        } catch {
          await markFailed(entry.id);
        }
      }
    } finally {
      setSyncing(false);
      await refreshPendingCount();
    }
  }, [isOnline, syncing, refreshPendingCount]);

  useEffect(() => {
    if (isOnline && pendingCount > 0) {
      const timer = setTimeout(() => syncAll(), 0);
      return () => clearTimeout(timer);
    }
  }, [isOnline, pendingCount, syncAll]);

  useEffect(() => {
    const timer = setTimeout(() => refreshPendingCount(), 0);
    const interval = setInterval(() => refreshPendingCount(), 30000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [refreshPendingCount]);

  return { pendingCount, syncing, syncAll, refreshPendingCount };
}
