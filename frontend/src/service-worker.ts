/// <reference lib="webworker" />
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

declare let self: ServiceWorkerGlobalScope;

const OFFLINE_URL = '/offline.html';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('offline-cache').then((cache) => cache.add(OFFLINE_URL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    self.clients.claim().then(async () => {
      const cacheNames = await caches.keys();
      const workboxCaches = cacheNames.filter(name => name.startsWith('workbox-'));
      await Promise.all(workboxCaches.map(name => caches.delete(name)));
    })
  );
});

precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

registerRoute(
  ({ request }) => request.mode === 'navigate',
  new NetworkFirst({
    cacheName: 'app-shell',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
    ],
    networkTimeoutSeconds: 3,
  })
);

registerRoute(
  ({ request }) => request.destination === 'font',
  new CacheFirst({
    cacheName: 'fonts',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
      new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 365 * 24 * 60 * 60 }),
    ],
  })
);

registerRoute(
  ({ request }) => request.destination === 'script' || 
                    request.destination === 'style' ||
                    request.destination === 'image' ||
                    request.destination === 'worker' ||
                    request.url.includes('/assets/'),
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 60 * 24 * 60 * 60 }),
    ],
  })
);

// Categorized: GraphQL GET queries (read operations) — 5min cache
registerRoute(
  ({ url, request }) => url.pathname === '/graphql' && request.method === 'GET',
  new StaleWhileRevalidate({
    cacheName: 'graphql-queries',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 5 * 60 }),
    ],
  })
);

// Categorized: API GET endpoints (export/reference data) — 30min cache
registerRoute(
  ({ url, request }) => url.pathname.startsWith('/api/') && request.method === 'GET',
  new StaleWhileRevalidate({
    cacheName: 'api-data',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 30 * 60 }),
    ],
  })
);

registerRoute(
  ({ url }) => url.pathname === '/share',
  new NetworkFirst({
    cacheName: 'share-target',
  })
);

// Categorized: GraphQL POST queries — StaleWhileRevalidate for dynamic data
registerRoute(
  ({ url, request }) => url.pathname === '/graphql' && request.method === 'POST',
  new StaleWhileRevalidate({
    cacheName: 'graphql-dynamic',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 5 * 60 }),
    ],
  })
);

self.addEventListener('fetch', (event) => {
  // Handle Share Target POST
  if (event.request.method === 'POST' && event.request.url.includes('/share')) {
    event.respondWith(
      (async () => {
        const formData = await event.request.formData();
        const title = formData.get('title') || '';
        const text = formData.get('text') || '';
        const url = formData.get('url') || '';

        const params = new URLSearchParams();
        if (title) params.set('title', title.toString());
        if (text) params.set('text', text.toString());
        if (url) params.set('url', url.toString());

        return Response.redirect(`/share?${params.toString()}`, 303);
      })()
    );
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(async () => {
        const cachedResponse = await caches.match(OFFLINE_URL);
        return cachedResponse || new Response('Offline', { status: 503 });
      })
    );
  }
});

// Badge counter persisted via Cache API
async function getBadgeCount(): Promise<number> {
  try {
    const cache = await caches.open('badge-count');
    const response = await cache.match('/__badge_count__');
    if (response) {
      const count = await response.text();
      return parseInt(count, 10) || 0;
    }
  } catch (e) {
    console.error('Failed to get badge count:', e);
  }
  return 0;
}

self.addEventListener('push', (event) => {
  if (!event.data) return;

  try {
    const data = event.data.json();
    const notification = data.notification;

    event.waitUntil(
      (async () => {
        // Set app badge
        if ('setAppBadge' in self.navigator) {
          try {
            const badgeCount = await getBadgeCount();
            await self.navigator.setAppBadge(badgeCount + 1);
          } catch (e) {
            console.error('Badge set failed:', e);
          }
        }

        await self.registration.showNotification(notification.title, {
          body: notification.body,
          icon: notification.icon || '/pwa-192x192.png',
          badge: '/icon16.png',
          data: notification.data
        });
      })()
    );
  } catch (e) {
    console.error("Push data is not JSON or invalid", e);
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    (async () => {
      // Clear app badge when user interacts with notifications
      if ('clearAppBadge' in self.navigator) {
        try {
          await self.navigator.clearAppBadge();
        } catch (e) {
          console.error('Failed to clear badge:', e);
        }
      }

      const urlToOpen = event.notification.data?.url || '/';
      const windowClients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      for (const client of windowClients) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(urlToOpen);
      }
    })()
  );
});

interface PeriodicSyncEvent extends ExtendableEvent {
  tag: string;
}

interface SyncEvent extends ExtendableEvent {
  tag: string;
}

self.addEventListener('periodicsync', ((event: PeriodicSyncEvent) => {
  if (event.tag === 'refresh-data') {
    event.waitUntil(refreshData());
  }
}) as EventListener);

self.addEventListener('sync', ((event: SyncEvent) => {
  if (event.tag === 'sync-clock-logs') {
    event.waitUntil(syncClockLogs());
  } else if (event.tag === 'sync-fleet-logs') {
    event.waitUntil(syncFleetLogs());
  }
}) as EventListener);

async function syncClockLogs() {
  const db = await openIDB('chronos-offline', 1);
  const transaction = db.transaction('clock-logs', 'readwrite');
  const store = transaction.objectStore('clock-logs');
  const request = store.getAll();
  
  return new Promise<void>((resolve, reject) => {
    request.onsuccess = async () => {
      const logs = request.result as Array<Record<string, unknown>>;
      if (logs.length === 0) {
        resolve();
        return;
      }
      
      const failedLogs: Array<Record<string, unknown>> = [];
      
      for (const log of logs) {
        try {
          const response = await fetch('/api/kiosk/clock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(log),
          });
          
          if (!response.ok) throw new Error('Sync failed');
          store.delete(log.id as string);
        } catch {
          failedLogs.push(log);
        }
      }
      
      if (failedLogs.length > 0) {
        reject(new Error(`${failedLogs.length} logs failed to sync`));
      } else {
        resolve();
      }
    };
    
    request.onerror = () => reject(request.error);
  });
}

async function syncFleetLogs() {
  try {
    const db = await openIDB('chronos-fleet-offline', 1);
    const tx = db.transaction('entries', 'readwrite');
    const store = tx.objectStore('entries');
    const index = store.index('syncStatus');
    const entries = await new Promise<any[]>((resolve, reject) => {
      const request = index.getAll('pending');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    for (const entry of entries) {
      try {
        const mutation = entry.type === 'mileage'
          ? `mutation { createVehicleMileage(input: { vehicleId: ${entry.vehicleId}, mileage: ${entry.payload.mileage}, date: "${entry.payload.date}", notes: "${entry.payload.notes || ''}" }) { id } }`
          : `mutation { createVehicleFuel(input: { vehicleId: ${entry.vehicleId}, liters: ${entry.payload.liters}, price: ${entry.payload.price}, total: ${entry.payload.total}, fuelType: "${entry.payload.fuelType || 'dizel'}", date: "${entry.payload.date}", notes: "${entry.payload.notes || ''}", mileage: ${entry.payload.mileage || 0} }) { id } }`;

        const response = await fetch('/graphql', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: mutation }),
        });

        if (response.ok) {
          store.delete(entry.id);
        } else {
          entry.syncStatus = 'failed';
          entry.retryCount += 1;
          store.put(entry);
        }
      } catch (e) {
        console.error('Fleet sync failed for entry:', entry.id, e);
      }
    }
  } catch (e) {
    console.error('Fleet sync error:', e);
  }
}

function openIDB(name: string, version: number): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, version);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (name === 'chronos-offline') {
        if (!db.objectStoreNames.contains('clock-logs')) {
          db.createObjectStore('clock-logs', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('fleet-logs')) {
          db.createObjectStore('fleet-logs', { keyPath: 'id' });
        }
      } else if (name === 'chronos-fleet-offline') {
        if (!db.objectStoreNames.contains('entries')) {
          const store = db.createObjectStore('entries', { keyPath: 'id' });
          store.createIndex('syncStatus', 'syncStatus');
          store.createIndex('vehicleId', 'vehicleId');
          store.createIndex('type', 'type');
        }
      }
    };
  });
}

async function refreshData() {
  const cache = await caches.open('graphql-queries');
  
  try {
    const response = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: `{ me { id firstName lastName role { name } } }`
      })
    });
    
    if (response.ok) {
      await cache.put('/graphql', response.clone());
    }
  } catch (e) {
    console.error('Periodic sync failed:', e);
  }
  
  try {
    const response = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: `{ mySchedule { id date shift { name startTime endTime } } }`
      })
    });
    
    if (response.ok) {
      await cache.put('/graphql?schedules', response.clone());
    }
  } catch (e) {
    console.error('Periodic sync failed:', e);
  }
}
