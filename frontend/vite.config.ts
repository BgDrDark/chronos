import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'service-worker.ts',
      registerType: 'autoUpdate',
      injectManifest: {
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5 MB
      },
      devOptions: {
        enabled: true,
        type: 'module',
        navigateFallback: 'index.html',
        suppressWarnings: true
      },
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
      manifest: {
        name: 'Chronos Working Time',
        short_name: 'Chronos',
        description: 'Система за отчитане на работно време и заплати',
        theme_color: '#3f51b5',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        scope: '/',
        shortcuts: [
          {
            name: 'Вход',
            short_name: 'Вход',
            description: 'Вход в системата',
            url: '/',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          },
          {
            name: 'Карта за достъп',
            short_name: 'Карта',
            description: 'Отвори QR кода за маркиране',
            url: '/my-card',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          },
          {
            name: 'Kiosk Достъп',
            short_name: 'Достъп',
            description: 'Терминал за достъп и отчитане',
            url: '/kiosk/terminal',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          },
          {
            name: 'Kiosk Clock',
            short_name: 'Clock',
            description: 'Терминал за отчитане на работно време',
            url: '/kiosk',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          },
          {
            name: 'Производство 1',
            short_name: 'Цех 1',
            description: 'Производствен терминал - Цех 1',
            url: '/production-kiosk?terminal=1',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          },
          {
            name: 'Производство 2',
            short_name: 'Цех 2',
            description: 'Производствен терминал - Цех 2',
            url: '/production-kiosk?terminal=2',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          }
        ],
        icons: [
          {
            src: 'icon16.png',
            sizes: '16x16',
            type: 'image/png'
          },
          {
            src: 'icons32.png',
            sizes: '32x32',
            type: 'image/png'
          },
          {
            src: 'icons64.png',
            sizes: '64x64',
            type: 'image/png'
          },
          {
            src: 'icons128.png',
            sizes: '128x128',
            type: 'image/png'
          },
          {
            src: 'pwa-192x192.png',
            sizes: '128x128',
            type: 'image/png',
            purpose: 'any maskable'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '128x128',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      }
    })
  ],
  server: {
    port: 5173,
    host: '0.0.0.0',
  },
  esbuild: {
    drop: ['console', 'debugger'],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
  build: {
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
  },
});
