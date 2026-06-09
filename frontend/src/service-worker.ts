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

registerRoute(
  ({ url }) => url.pathname === '/graphql',
  new StaleWhileRevalidate({
    cacheName: 'graphql-cache',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 5 * 60 }),
    ],
  })
);

self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(async () => {
        const cachedResponse = await caches.match(OFFLINE_URL);
        return cachedResponse || new Response('Offline', { status: 503 });
      })
    );
  }
});

self.addEventListener('push', (event) => {
  if (!event.data) return;

  try {
    const data = event.data.json();
    const notification = data.notification;

    event.waitUntil(
      self.registration.showNotification(notification.title, {
        body: notification.body,
        icon: notification.icon || '/pwa-192x192.png',
        badge: '/icon16.png',
        data: notification.data
      })
    );
  } catch (e) {
    console.error("Push data is not JSON or invalid", e);
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(urlToOpen);
      }
    })
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
        } catch (e) {
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

function openIDB(name: string, version: number): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, version);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains('clock-logs')) {
        db.createObjectStore('clock-logs', { keyPath: 'id' });
      }
    };
  });
}

async function refreshData() {
  const cache = await caches.open('graphql-cache');
  
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
