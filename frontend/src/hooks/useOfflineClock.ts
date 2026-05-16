import { useState, useEffect, useCallback } from 'react';

interface OfflineClockLog {
  id: string;
  type: 'clock-in' | 'clock-out';
  timestamp: string;
  userId?: number;
  terminalId?: string;
  latitude?: number;
  longitude?: number;
}

const DB_NAME = 'chronos-offline';
const DB_VERSION = 1;
const STORE_NAME = 'clock-logs';

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

export function useOfflineClock() {
  const [queue, setQueue] = useState<OfflineClockLog[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    try {
      const db = await openDB();
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();
      request.onsuccess = () => setQueue(request.result as OfflineClockLog[]);
    } catch (e) {
      console.error('Failed to load offline queue:', e);
    }
  };

  const addToQueue = useCallback(async (log: Omit<OfflineClockLog, 'id'>) => {
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
        await ((registration as unknown) as { sync: { register: (tag: string) => Promise<void> } }).sync.register('sync-clock-logs');
      }
    } catch (e) {
      console.error('Failed to add to offline queue:', e);
    }
  }, []);

  const syncNow = useCallback(async () => {
    if (queue.length === 0 || !navigator.onLine) return;
    
    setIsSyncing(true);
    try {
      const db = await openDB();
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();
      
      request.onsuccess = async () => {
        const logs = request.result as OfflineClockLog[];
        const failedLogs: OfflineClockLog[] = [];
        
        for (const log of logs) {
          try {
            const response = await fetch('/api/kiosk/clock', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(log),
            });
            
            if (!response.ok) throw new Error('Sync failed');
            store.delete(log.id);
          } catch (e) {
            failedLogs.push(log);
          }
        }
        
        setQueue(failedLogs);
        setIsSyncing(false);
      };
    } catch (e) {
      console.error('Sync failed:', e);
      setIsSyncing(false);
    }
  }, [queue]);

  return { queue, isSyncing, addToQueue, syncNow };
}
