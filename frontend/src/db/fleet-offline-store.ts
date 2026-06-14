interface OfflineEntry {
  id: string;
  type: 'mileage' | 'fuel' | 'pre-trip';
  payload: Record<string, unknown>;
  createdAt: string;
  vehicleId: number;
  syncStatus: 'pending' | 'syncing' | 'failed';
  retryCount: number;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('chronos-fleet-offline', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains('entries')) {
        const store = db.createObjectStore('entries', { keyPath: 'id' });
        store.createIndex('syncStatus', 'syncStatus');
        store.createIndex('vehicleId', 'vehicleId');
        store.createIndex('type', 'type');
      }
    };
  });
}

export async function saveOfflineEntry(
  type: OfflineEntry['type'],
  vehicleId: number,
  payload: Record<string, unknown>
): Promise<string> {
  const db = await openDB();
  const id = `${type}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const entry: OfflineEntry = {
    id,
    type,
    vehicleId,
    payload,
    createdAt: new Date().toISOString(),
    syncStatus: 'pending',
    retryCount: 0,
  };
  return new Promise((resolve, reject) => {
    const tx = db.transaction('entries', 'readwrite');
    const store = tx.objectStore('entries');
    const request = store.add(entry);
    request.onsuccess = () => resolve(id);
    request.onerror = () => reject(request.error);
  });
}

export async function getPendingEntries(): Promise<OfflineEntry[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('entries', 'readonly');
    const store = tx.objectStore('entries');
    const index = store.index('syncStatus');
    const request = index.getAll('pending');
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function markSynced(id: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('entries', 'readwrite');
    const store = tx.objectStore('entries');
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function markFailed(id: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('entries', 'readwrite');
    const store = tx.objectStore('entries');
    const getRequest = store.get(id);
    getRequest.onsuccess = () => {
      const entry = getRequest.result;
      if (entry) {
        entry.syncStatus = 'failed';
        entry.retryCount += 1;
        store.put(entry);
      }
      resolve();
    };
    getRequest.onerror = () => reject(getRequest.error);
  });
}

export async function getPendingCount(): Promise<number> {
  const entries = await getPendingEntries();
  return entries.length;
}

export async function clearAllEntries(): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('entries', 'readwrite');
    const store = tx.objectStore('entries');
    const request = store.clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}
