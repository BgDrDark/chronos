# PWA Development Plan - Chronos Working Time

## Current State Summary

| Component | Status | Notes |
|-----------|--------|-------|
| vite-plugin-pwa | ✅ Installed | v1.2.0, injectManifest strategy |
| Service Worker | ✅ Exists | `src/service-worker.ts` - precache + push + notification click |
| SW Registration | ✅ Working | `main.tsx` with `registerSW()` auto-update |
| Push Notifications | ✅ Working | VAPID subscription, preferences, backend integration |
| Manifest | ✅ Configured | In vite config with shortcuts |
| Icons | ✅ Present | 10 files in `public/` |
| Kiosk Offline Queue | ✅ Partial | localStorage queue, manual sync |
| Install Prompt | ❌ Missing | No `beforeinstallprompt` handler |
| Offline Fallback | ❌ Missing | White screen when offline |
| Network Status | ❌ Missing | No global indicator |
| Runtime Caching | ❌ Missing | Only precache, no API caching |
| Splash Screens | ❌ Missing | No iOS splash images |

---

## Фаза 1: Критични поправки (~2 часа)

### 1.1 Fix Icon Sizes в Manifest
**Файл:** `vite.config.ts`

```typescript
// Грешно (текущо):
{ src: 'pwa-192x192.png', sizes: '128x128', ... }
{ src: 'pwa-512x512.png', sizes: '128x128', ... }

// Правилно:
{ src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
{ src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
```

**Защо:** Грешните размери водят до blurry icons на Android home screen и лош PWA score в Lighthouse.

### 1.2 Премахни Двойната SW Регистрация
**Файл:** `src/components/PushNotificationManager.tsx`

```typescript
// Премахни ред 105:
// registration = await navigator.serviceWorker.register('/service-worker.js', { type: 'module' });

// Използвай само:
const registration = await navigator.serviceWorker.ready;
```

**Защо:** `main.tsx` вече регистрира SW чрез `registerSW()`. Двойна регистрация води до конфликти и wasted resources.

### 1.3 Оптимизирай Activate Handler
**Файл:** `src/service-worker.ts`

```typescript
// Текущо (изтрива ВСИЧКИ cache-ове):
caches.keys().then((cacheNames) => {
  cacheNames.forEach((cacheName) => caches.delete(cacheName));
});

// Оптимизирано (само стари workbox cache-ове):
const cacheNames = await caches.keys();
const workboxCaches = cacheNames.filter(name => name.startsWith('workbox-'));
await Promise.all(workboxCaches.map(name => caches.delete(name)));
```

**Защо:** Текущият код изтрива precache при всеки update → бавно зареждане. Трябва да запазим precache и да изтрием само старите runtime cache-ове.

### 1.4 Добави Manifest Link в index.html
**Файл:** `frontend/index.html`

```html
<head>
  <!-- Добави след favicon линковете -->
  <link rel="manifest" href="/manifest.webmanifest" />
  <meta name="theme-color" content="#3f51b5" />
</head>
```

**Защо:** `vite-plugin-pwa` генерира `manifest.webmanifest` автоматично, но трябва да е линкнат в HTML за да работи install prompt.

---

## Фаза 2: Install Prompt (~3 часа)

### 2.1 Създай `usePWAInstall` Hook
**Файл:** `src/hooks/usePWAInstall.ts` (нов)

```typescript
import { useState, useEffect, useCallback } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function usePWAInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isInstallable, setIsInstallable] = useState(false);

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
    }

    // Listen for install prompt
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setIsInstallable(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Listen for app installed
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setDeferredPrompt(null);
    });

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      window.removeEventListener('appinstalled', () => {});
    };
  }, []);

  const install = useCallback(async () => {
    if (!deferredPrompt) return false;
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
      setIsInstallable(false);
      setIsInstalled(true);
    }
    
    return outcome === 'accepted';
  }, [deferredPrompt]);

  return { install, isInstalled, isInstallable };
}
```

**Отговорности:**
- Прихваща `beforeinstallprompt` event
- Detects ако app е вече инсталиран (`display-mode: standalone`)
- Предоставя `install()` метод
- Track-ва състоянието

### 2.2 Създай `PWAInstallBanner` Компонент
**Файл:** `src/components/PWAInstallBanner.tsx` (нов)

```typescript
import React from 'react';
import { usePWAInstall } from '../hooks/usePWAInstall';
import { Snackbar, Alert, Button, Box, Typography, IconButton } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import CloseIcon from '@mui/icons-material/Close';

export const PWAInstallBanner: React.FC = () => {
  const { install, isInstallable, isInstalled } = usePWAInstall();
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    if (isInstallable && !isInstalled) {
      // Покажи banner след 3 секунди
      const timer = setTimeout(() => setOpen(true), 3000);
      return () => clearTimeout(timer);
    }
  }, [isInstallable, isInstalled]);

  const handleInstall = async () => {
    await install();
    setOpen(false);
  };

  if (!isInstallable || isInstalled) return null;

  return (
    <Snackbar
      open={open}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      autoHideDuration={30000}
      onClose={() => setOpen(false)}
    >
      <Alert
        severity="info"
        variant="filled"
        sx={{ width: '100%', maxWidth: 400 }}
        action={
          <IconButton size="small" color="inherit" onClick={() => setOpen(false)}>
            <CloseIcon />
          </IconButton>
        }
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DownloadIcon />
          <Typography variant="body2" sx={{ flexGrow: 1 }}>
            Инсталирай Chronos за бърз достъп
          </Typography>
          <Button size="small" color="inherit" onClick={handleInstall} sx={{ fontWeight: 'bold' }}>
            Инсталирай
          </Button>
        </Box>
      </Alert>
    </Snackbar>
  );
};
```

**Функционалности:**
- Auto-show след 3 секунди при първо посещение
- Auto-dismiss след 30 секунди
- Manual dismiss бутон
- "Инсталирай" CTA бутон
- Не се показва ако вече е инсталирано

### 2.3 Интегрирай в App.tsx
**Файл:** `src/App.tsx`

```typescript
// Добави import:
import { PWAInstallBanner } from './components/PWAInstallBanner';

// Добави в main layout (преди ErrorProvider):
return (
  <>
    <PWAInstallBanner />
    <ErrorProvider>
      <MainLayout>
        {/* ... routes ... */}
      </MainLayout>
    </ErrorProvider>
  </>
);
```

---

## Фаза 3: Offline Support (~6 часа)

### 3.1 Offline Fallback Страница
**Файл:** `public/offline.html` (нов)

```html
<!DOCTYPE html>
<html lang="bg">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chronos - Офлайн</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      background: #f5f5f5;
      color: #333;
    }
    .icon { font-size: 64px; margin-bottom: 16px; }
    h1 { margin: 0 0 8px; color: #3f51b5; }
    p { margin: 0 0 24px; color: #666; text-align: center; max-width: 300px; }
    button {
      padding: 12px 24px;
      background: #3f51b5;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
    }
    button:hover { background: #303f9f; }
  </style>
</head>
<body>
  <div class="icon">📡</div>
  <h1>Няма връзка с интернет</h1>
  <p>Проверете вашата мрежова връзка и опитайте отново.</p>
  <button onclick="window.location.reload()">Опитай отново</button>
</body>
</html>
```

**Файл:** `src/service-worker.ts` - добави runtime caching

```typescript
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

declare let self: ServiceWorkerGlobalScope;

// Precache
precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// Offline fallback
const OFFLINE_URL = '/offline.html';

// Cache offline page on install
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('offline-cache').then((cache) => cache.add(OFFLINE_URL))
  );
  self.skipWaiting();
});

// Network-first за HTML навигация с offline fallback
registerRoute(
  ({ request }) => request.mode === 'navigate',
  new NetworkFirst({
    cacheName: 'pages-cache',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
    ],
    networkTimeoutSeconds: 3,
  })
);

// Cache-first за static assets (JS, CSS, images)
registerRoute(
  ({ request }) => request.destination === 'script' || 
                    request.destination === 'style' ||
                    request.destination === 'image',
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
      new ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 30 * 24 * 60 * 60 }),
    ],
  })
);

// Stale-while-revalidate за GraphQL API
registerRoute(
  ({ url }) => url.pathname === '/graphql',
  new StaleWhileRevalidate({
    cacheName: 'api-cache',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
      new ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 5 * 60 }), // 5 минути
    ],
  })
);

// Offline fallback handler
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
  }
});

// Push notifications (existing)
self.addEventListener('push', (event) => { /* ... */ });
self.addEventListener('notificationclick', (event) => { /* ... */ });
```

**Какво прави:**
- `NetworkFirst` за HTML - опитва мрежата, fallback към cache
- `CacheFirst` за static assets - бързо зареждане от cache
- `StaleWhileRevalidate` за GraphQL - показва cached данни докато refresh-ва
- Offline fallback страница при липса на интернет

### 3.2 Глобален NetworkStatus Индикатор
**Файл:** `src/hooks/useNetworkStatus.ts` (нов)

```typescript
import { useState, useEffect } from 'react';

export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingOperations, setPendingOperations] = useState(0);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOnline, pendingOperations, setPendingOperations };
}
```

**Файл:** `src/components/NetworkStatusBanner.tsx` (нов)

```typescript
import React from 'react';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { Alert, Box, Typography } from '@mui/material';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import WifiIcon from '@mui/icons-material/Wifi';

export const NetworkStatusBanner: React.FC = () => {
  const { isOnline, pendingOperations } = useNetworkStatus();

  if (isOnline && pendingOperations === 0) return null;

  return (
    <Alert
      severity={isOnline ? 'success' : 'error'}
      variant="filled"
      sx={{ borderRadius: 0, position: 'sticky', top: 0, zIndex: 9999 }}
      icon={isOnline ? <WifiIcon /> : <WifiOffIcon />}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {isOnline ? (
          <>
            <Typography variant="body2">
              Връзката е възстановена
            </Typography>
            {pendingOperations > 0 && (
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                Синхронизиране на {pendingOperations} операции...
              </Typography>
            )}
          </>
        ) : (
          <Typography variant="body2">
            Няма интернет връзка. Някои функции може да не работят.
          </Typography>
        )}
      </Box>
    </Alert>
  );
};
```

**Файл:** `src/App.tsx` - интегрирай banner

```typescript
import { NetworkStatusBanner } from './components/NetworkStatusBanner';

// В MainLayout или глобално:
<NetworkStatusBanner />
```

### 3.3 Background Sync за Clock-In/Out
**Файл:** `src/service-worker.ts` - добави sync handler

```typescript
// Background Sync handler
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-clock-logs') {
    event.waitUntil(syncClockLogs());
  }
});

async function syncClockLogs() {
  // Get offline queue from IndexedDB
  const db = await openDB('chronos-offline', 1);
  const logs = await db.getAll('clock-logs');
  
  if (logs.length === 0) return;
  
  // Try to sync each log
  const failedLogs = [];
  for (const log of logs) {
    try {
      const response = await fetch('/api/kiosk/clock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(log),
      });
      
      if (!response.ok) throw new Error('Sync failed');
      
      // Remove synced log
      await db.delete('clock-logs', log.id);
    } catch (e) {
      failedLogs.push(log);
    }
  }
  
  // If any failed, they'll be retried on next sync
  if (failedLogs.length > 0) {
    throw new Error(`${failedLogs.length} logs failed to sync`);
  }
}

// Helper to open IndexedDB
function openDB(name: string, version: number) {
  return new Promise<IDBDatabase>((resolve, reject) => {
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
```

**Файл:** `src/hooks/useOfflineClock.ts` (нов)

```typescript
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

export function useOfflineClock() {
  const [queue, setQueue] = useState<OfflineClockLog[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // Load queue from IndexedDB on mount
  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    try {
      const db = await openDB('chronos-offline', 1);
      const logs = await db.getAll('clock-logs');
      setQueue(logs);
    } catch (e) {
      console.error('Failed to load offline queue:', e);
    }
  };

  const addToQueue = useCallback(async (log: Omit<OfflineClockLog, 'id'>) => {
    const newLog = { ...log, id: Date.now().toString() };
    
    try {
      const db = await openDB('chronos-offline', 1);
      await db.add('clock-logs', newLog);
      setQueue(prev => [...prev, newLog]);
      
      // Request background sync if available
      if ('serviceWorker' in navigator && 'SyncManager' in window) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-clock-logs');
      }
    } catch (e) {
      console.error('Failed to add to offline queue:', e);
    }
  }, []);

  const syncNow = useCallback(async () => {
    if (queue.length === 0 || !navigator.onLine) return;
    
    setIsSyncing(true);
    try {
      const db = await openDB('chronos-offline', 1);
      const logs = await db.getAll('clock-logs');
      
      const failedLogs = [];
      for (const log of logs) {
        try {
          const response = await fetch('/api/kiosk/clock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(log),
          });
          
          if (!response.ok) throw new Error('Sync failed');
          await db.delete('clock-logs', log.id);
        } catch (e) {
          failedLogs.push(log);
        }
      }
      
      setQueue(failedLogs);
    } catch (e) {
      console.error('Sync failed:', e);
    } finally {
      setIsSyncing(false);
    }
  }, [queue]);

  return { queue, isSyncing, addToQueue, syncNow };
}

// IndexedDB helper
function openDB(name: string, version: number) {
  return new Promise<IDBDatabase>((resolve, reject) => {
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
```

**Какво прави:**
- Съхранява clock-in/out операции в IndexedDB при offline
- Автоматичен sync чрез Background Sync API при връщане online
- Manual sync бутон за потребителите
- Показва брой pending операции

---

## Фаза 4: Разширения (~8 часа)

### 4.1 iOS Splash Screens

**Проблем:** iOS не използва manifest icons за splash screens. Трябват отделни изображения за всеки iPhone/iPad размер.

**Решение:** Генерирай splash screens с `pwa-asset-generator`

**Стъпка 1: Инсталирай генератор**
```bash
npm install -D pwa-asset-generator
```

**Стъпка 2: Създай скрипт за генериране**
**Файл:** `scripts/generate-splash.js` (нов)

```javascript
const { generateSplashScreens } = require('pwa-asset-generator');

async function main() {
  await generateSplashScreens(
    'public/pwa-512x512.png',  // Source icon
    'public/splash',             // Output directory
    {
      pathOverride: '/splash',
      xhtml: true,
      quality: 100,
      background: '#3f51b5',     // Theme color
      padding: '10%',
      landscape: true,
      portrait: true,
    }
  );
}

main().catch(console.error);
```

**Стъпка 3: Добави в package.json**
```json
{
  "scripts": {
    "generate:splash": "node scripts/generate-splash.js"
  }
}
```

**Стъпка 4: Run генератора**
```bash
npm run generate:splash
```

**Стъпка 5: Добави линкове в index.html**
```html
<!-- iOS Splash Screens -->
<link rel="apple-touch-startup-image" href="/splash/apple-splash-2048-2732.jpg" media="(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="/splash/apple-splash-2732-2048.jpg" media="(device-width: 1366px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)">
<!-- ... more splash screens for different devices ... -->
```

**Генерирани файлове:**
- `public/splash/apple-splash-*.jpg` - ~20 файла за различни iPhone/iPad размери
- Автоматично media queries за всеки device

**Алтернатива (ръчно):**
Ако не искаш да използваш генератор, създай ръчно:
- `apple-splash-2048-2732.jpg` (iPad Pro 12.9")
- `apple-splash-1668-2388.jpg` (iPad Pro 11")
- `apple-splash-1290-2796.jpg` (iPhone 14 Pro Max)
- `apple-splash-1179-2556.jpg` (iPhone 14/13/12)
- `apple-splash-1170-2532.jpg` (iPhone 13/12 mini)

### 4.2 Periodic Background Sync

**Какво е:** Автоматично refresh на данни във фонов режим, дори когато app-а не е отворен.

**Поддръжка:** Само Chrome/Edge на Android. iOS Safari НЕ поддържа.

**Файл:** `src/service-worker.ts` - добави periodic sync

```typescript
// Periodic Background Sync handler
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'refresh-data') {
    event.waitUntil(refreshData());
  }
});

async function refreshData() {
  const cache = await caches.open('api-cache');
  
  // Refresh user data
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
  
  // Refresh schedules
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
```

**Файл:** `src/hooks/usePeriodicSync.ts` (нов)

```typescript
import { useEffect } from 'react';

export function usePeriodicSync() {
  useEffect(() => {
    if ('periodicSync' in navigator) {
      // Request periodic sync (minimum interval: 24 hours)
      navigator.serviceWorker.ready.then(async (registration) => {
        try {
          await registration.periodicSync.register('refresh-data', {
            minInterval: 24 * 60 * 60 * 1000, // 24 hours
          });
          console.log('Periodic sync registered');
        } catch (e) {
          console.error('Periodic sync registration failed:', e);
        }
      });
    }
  }, []);
}
```

**Файл:** `src/App.tsx` - интегрирай

```typescript
import { usePeriodicSync } from './hooks/usePeriodicSync';

function App() {
  usePeriodicSync();
  // ...
}
```

**Какво прави:**
- Автоматично refresh на user data и schedules на 24 часа
- Работи дори когато app-а е затворен
- Само за Chrome/Edge на Android
- Graceful fallback за други браузъри

### 4.3 File Handling API

**Какво е:** Позволява на PWA да се асоциира с файлови типове и да ги отваря директно.

**Поддръжка:** Chrome/Edge на desktop. Мобилните браузъри НЕ поддържат.

**Use case за Chronos:** Отваряне на PDF/IMG документи за отпуски директно в PWA.

**Стъпка 1: Добави file handlers в manifest**
**Файл:** `vite.config.ts`

```typescript
VitePWA({
  // ... existing config
  manifest: {
    // ... existing manifest
    file_handlers: [
      {
        action: '/documents/view',
        accept: {
          'application/pdf': ['.pdf'],
          'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
        },
        launch_type: 'single-client',
      }
    ],
  },
})
```

**Стъпка 2: Създай Document Viewer страница**
**Файл:** `src/pages/DocumentViewerPage.tsx` (нов)

```typescript
import React, { useEffect, useState } from 'react';
import { Box, Typography, CircularProgress, IconButton } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useNavigate } from 'react-router-dom';

const DocumentViewerPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    // Handle launched files
    const handleLaunchQueue = async () => {
      if ('launchQueue' in window) {
        (window as any).launchQueue.setConsumer(async (launchParams: any) => {
          if (!launchParams.files.length) return;
          
          const fileHandle = launchParams.files[0];
          const file = await fileHandle.getFile();
          setFile(file);
          
          // Create preview URL
          const url = URL.createObjectURL(file);
          setPreviewUrl(url);
          
          launchParams.resolve();
        });
      }
    };

    handleLaunchQueue();
  }, []);

  if (!file) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const isImage = file.type.startsWith('image/');
  const isPdf = file.type === 'application/pdf';

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate(-1)}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6">{file.name}</Typography>
      </Box>

      {isImage && (
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <img src={previewUrl} alt={file.name} style={{ maxWidth: '100%', maxHeight: '80vh' }} />
        </Box>
      )}

      {isPdf && (
        <Box sx={{ height: '80vh' }}>
          <iframe src={previewUrl} style={{ width: '100%', height: '100%', border: 'none' }} />
        </Box>
      )}
    </Box>
  );
};

export default DocumentViewerPage;
```

**Стъпка 3: Добави route в App.tsx**
```typescript
<Route path="/documents/view" element={<DocumentViewerPage />} />
```

**Какво прави:**
- Асоциира PWA с PDF и image файлове
- Когато потребителят кликне на PDF → отваря се в Chronos
- Вграден viewer за images и PDFs
- Само за Chrome/Edge desktop

### 4.4 Contact Picker API

**Какво е:** Позволява на PWA да достъпи контактите на устройството (само с permission).

**Поддръжка:** Chrome на Android. iOS и desktop НЕ поддържат.

**Use case за Chronos:** Споделяне на графици с колеги чрез контактите им.

**Файл:** `src/hooks/useContactPicker.ts` (нов)

```typescript
import { useState, useCallback } from 'react';

interface Contact {
  name: string;
  email?: string;
  phone?: string;
  photo?: Blob;
}

export function useContactPicker() {
  const [isSupported] = useState('contacts' in navigator);

  const pickContacts = useCallback(async (
    options: { multiple?: boolean; includeFields?: string[] } = {}
  ): Promise<Contact[]> => {
    if (!isSupported) {
      throw new Error('Contact Picker API is not supported in this browser');
    }

    const { multiple = false, includeFields = ['name', 'email', 'tel'] } = options;

    try {
      const contacts = await (navigator as any).contacts.select(
        includeFields,
        { multiple }
      );

      return contacts.map((contact: any) => ({
        name: contact.name?.[0] || '',
        email: contact.email?.[0] || undefined,
        phone: contact.tel?.[0] || undefined,
        photo: contact.photo?.[0] || undefined,
      }));
    } catch (e) {
      if ((e as Error).name === 'AbortError') {
        throw new Error('Изборът на контакт беше отменен');
      }
      throw e;
    }
  }, [isSupported]);

  return { pickContacts, isSupported };
}
```

**Файл:** `src/components/ShareScheduleDialog.tsx` (нов)

```typescript
import React, { useState } from 'react';
import { useContactPicker } from '../hooks/useContactPicker';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, List, ListItem, ListItemText, ListItemAvatar,
  Avatar, Typography, Box, CircularProgress, Alert
} from '@mui/material';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import ShareIcon from '@mui/icons-material/Share';

interface ShareScheduleDialogProps {
  open: boolean;
  onClose: () => void;
  scheduleId: number;
}

export const ShareScheduleDialog: React.FC<ShareScheduleDialogProps> = ({
  open,
  onClose,
  scheduleId,
}) => {
  const { pickContacts, isSupported } = useContactPicker();
  const [selectedContacts, setSelectedContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handlePickContacts = async () => {
    try {
      setError(null);
      const contacts = await pickContacts({ multiple: true });
      setSelectedContacts(contacts);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleShare = async () => {
    if (selectedContacts.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      // TODO: Implement actual sharing logic
      // For now, just simulate
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 2000);
    } catch (e) {
      setError('Грешка при споделяне: ' + (e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  if (!isSupported) {
    return (
      <Dialog open={open} onClose={onClose}>
        <DialogTitle>Сподели график</DialogTitle>
        <DialogContent>
          <Alert severity="info">
            Contact Picker API не се поддържа в този браузър.
            Използвайте Chrome на Android за тази функционалност.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Затвори</Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Сподели график</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<PersonAddIcon />}
            onClick={handlePickContacts}
            fullWidth
          >
            Избери контакти
          </Button>
        </Box>

        {selectedContacts.length > 0 && (
          <List>
            {selectedContacts.map((contact, index) => (
              <ListItem key={index}>
                <ListItemAvatar>
                  <Avatar>
                    {contact.name?.[0] || '?'}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={contact.name}
                  secondary={
                    <>
                      {contact.email && <Typography variant="body2">{contact.email}</Typography>}
                      {contact.phone && <Typography variant="body2">{contact.phone}</Typography>}
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}

        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mt: 2 }}>Графикът е споделен успешно!</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отказ</Button>
        <Button
          variant="contained"
          startIcon={<ShareIcon />}
          onClick={handleShare}
          disabled={selectedContacts.length === 0 || loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Сподели'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

**Какво прави:**
- Позволява избор на контакти от устройството
- Споделяне на графици с избрани контакти
- Graceful fallback за unsupported браузъри
- Само за Chrome на Android

---

## Обобщение на всички фази

| Фаза | Време | Файлове | Приоритет |
|------|-------|---------|-----------|
| **Фаза 1: Критични поправки** | ~2 часа | 4 файла | 🔴 Висок |
| **Фаза 2: Install Prompt** | ~3 часа | 3 файла | 🔴 Висок |
| **Фаза 3: Offline Support** | ~6 часа | 6 файла | 🟡 Среден |
| **Фаза 4.1: iOS Splash Screens** | ~2 часа | 3 файла + ~20 изображения | 🟢 Нисък |
| **Фаза 4.2: Periodic Background Sync** | ~2 часа | 3 файла | 🟢 Нисък |
| **Фаза 4.3: File Handling API** | ~2 часа | 3 файла | 🟢 Нисък |
| **Фаза 4.4: Contact Picker API** | ~2 часа | 3 файла | 🟢 Нисък |
| **Общо** | **~22 часа** | **28 файла** | - |

---

## Препоръчителен ред на изпълнение

1. **Фаза 1** - Критични поправки (направи веднага)
2. **Фаза 2** - Install Prompt (най-видимо за потребителите)
3. **Фаза 3** - Offline Support (най-сложно, най-ценно)
4. **Фаза 4** - Разширения (по желание, в зависимост от нуждите)

---

## Тестване

### Lighthouse PWA Audit
```bash
# Инсталирай Lighthouse CLI
npm install -g lighthouse

# Run audit
lighthouse https://dev.oblak24.org --only-categories=pwa --output html --output-path pwa-report.html
```

### Chrome DevTools PWA Checks
1. Отвори DevTools → Application → Manifest
2. Провери всички checkmarks да са зелени
3. Тествай install prompt
4. Тествай offline mode (Network → Offline)

### Тестови сценарии

| Тест | Стъпки | Очакван резултат |
|------|--------|------------------|
| Install Prompt | Отвори app в Chrome → Изчакай 3 сек | Banner се показва |
| Install App | Кликни "Инсталирай" | App се инсталира, banner изчезва |
| Offline Mode | DevTools → Network → Offline → Reload | Offline страница се показва |
| Push Notifications | Subscribe → Изпрати test notification | Notification се показва |
| Background Sync | Offline → Clock-in → Online | Log се sync-ва автоматично |
| iOS Splash | Отвори от home screen на iPhone | Splash screen се показва |

---

## Бележки за поддръжка

### Service Worker Updates
- SW се update-ва автоматично при нов build
- Потребителите виждат prompt за refresh
- Старите cache-ове се изчистват автоматично

### Cache Management
- Precache: Всички static assets (JS, CSS, images)
- Runtime cache: API responses (5 минути TTL)
- Offline cache: Offline fallback page
- IndexedDB: Offline clock logs

### Browser Support
| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| PWA Install | ✅ | ❌ | ✅ | ✅ |
| Push Notifications | ✅ | ✅ | ❌ | ✅ |
| Background Sync | ✅ | ❌ |  | ✅ |
| Periodic Sync | ✅ | ❌ | ❌ | ✅ |
| File Handling | ✅ (desktop) | ❌ | ❌ | ✅ (desktop) |
| Contact Picker | ✅ (Android) | ❌ | ❌ | ❌ |
