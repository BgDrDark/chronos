import { useState, useEffect, useCallback } from 'react';

interface OfflineFleetLog {
  id: string;
  type: 'mileage' | 'fuel';
  vehicleId: number;
  data: Record<string, any>;
  timestamp: string;
}

const DB_NAME = 'chronos-offline';
const DB_VERSION = 1;
const STORE_NAME = 'fleet-logs';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
  });
}

export function useOfflineFleet() {
  const [queue, setQueue] = useState<OfflineFleetLog[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  async function loadQueue() {
    try {
      const db = await openDB();
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();
      request.onsuccess = () => setQueue(request.result as OfflineFleetLog[]);
    } catch (e) {
      console.error('Failed to load offline fleet queue:', e);
    }
  }

  useEffect(() => {
    loadQueue();
  }, []);

  const addToQueue = useCallback(async (log: Omit<OfflineFleetLog, 'id'>) => {
    const newLog = { ...log, id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}` };

    try {
      const db = await openDB();
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      store.add(newLog);

      transaction.oncomplete = () => {
        setQueue(prev => [...prev, newLog]);
      };

      if ('serviceWorker' in navigator && 'SyncManager' in window) {
        const registration = await navigator.serviceWorker.ready;
        await ((registration as unknown) as { sync: { register: (tag: string) => Promise<void> } }).sync.register('sync-fleet-logs');
      }
    } catch (e) {
      console.error('Failed to add to offline fleet queue:', e);
    }
  }, []);

  const syncNow = useCallback(async () => {
    if (queue.length === 0 || !navigator.onLine) return;

    setIsSyncing(true);
    const failed: OfflineFleetLog[] = [];

    for (const log of queue) {
      try {
        const endpoint = '/graphql';

        const query = log.type === 'fuel'
          ? `mutation AddVehicleFuel($input: VehicleFuelInput!) { addVehicleFuel(input: $input) { id } }`
          : `mutation AddVehicleMileage($vehicleId: Int!, $mileage: Float!) { addVehicleMileage(vehicleId: $vehicleId, mileage: $mileage) { id } }`;

        const variables = log.type === 'fuel'
          ? { input: log.data }
          : { vehicleId: log.vehicleId, mileage: log.data.mileage };

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, variables }),
        });

        if (!response.ok) {
          failed.push(log);
        }
      } catch {
        failed.push(log);
      }
    }

    // Replace queue with failed items only
    const db = await openDB();
    const transaction = db.transaction(STORE_NAME, 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    store.clear();

    for (const log of failed) {
      store.add(log);
    }

    setQueue(failed);
    setIsSyncing(false);
  }, [queue]);

  const getQueueLength = () => queue.length;

  return { addToQueue, syncNow, getQueueLength, isSyncing, queue };
}
