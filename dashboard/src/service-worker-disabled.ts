/**
 * WakeDock Dashboard Service Worker - TEMPORARILY DISABLED FOR DEBUGGING
 */

/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

// Service worker context
declare const self: ServiceWorkerGlobalScope;

// Cache configuration
const CACHE_NAME = `wakedock-cache-${version}`;
const STATIC_CACHE_NAME = `wakedock-static-${version}`;

// Cache static assets on install
const staticAssets = ['/', ...build, ...files];

// Install event - cache static assets
self.addEventListener('install', (event: ExtendableEvent) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches
      .open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(staticAssets);
      })
      .then(() => {
        console.log('[SW] Installation complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event: ExtendableEvent) => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name.startsWith('wakedock-') && name !== CACHE_NAME && name !== STATIC_CACHE_NAME)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Activation complete');
        return self.clients.claim();
      })
      .catch((error) => {
        console.error('[SW] Activation failed:', error);
      })
  );
});

// Fetch event - COMPLETELY DISABLED FOR DEBUGGING
self.addEventListener('fetch', (event: FetchEvent) => {
  console.log('[SW] DISABLED - All requests pass through natively');
  // Do nothing - let browser handle all requests natively
});
