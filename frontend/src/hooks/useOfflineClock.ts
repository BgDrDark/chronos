import { useEffect, useCallback, useState } from 'react';
import { getPendingEntries, markSynced, markFailed, getPendingCount, saveClockEntry } from '../db/clock-offline-store';
import { useNetworkStatus } from './useNetworkStatus';

export function useOfflineClock() {
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
          const key = entry.payload.idempotency_key || null;
          const mutation = entry.type === 'clock-in'
            ? `mutation ClockIn($lat: Float, $lon: Float, $key: String) { clockIn(latitude: $lat, longitude: $lon, idempotencyKey: $key) { id startTime } }`
            : `mutation ClockOut($lat: Float, $lon: Float, $key: String) { clockOut(latitude: $lat, longitude: $lon, idempotencyKey: $key) { id endTime } }`;

          const response = await fetch('/graphql', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query: mutation,
              variables: {
                lat: entry.payload.latitude || null,
                lon: entry.payload.longitude || null,
                key,
              },
            }),
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
      syncAll();
    }
  }, [isOnline, syncAll]);

  useEffect(() => {
    refreshPendingCount();
    const interval = setInterval(refreshPendingCount, 30000);
    return () => clearInterval(interval);
  }, [refreshPendingCount]);

  return { pendingCount, syncing, syncAll, refreshPendingCount, saveClockEntry };
}
