/**
 * WakeDock Dashboard Service Worker
 * Provides offline functionality and caching for PWA features
 */

import { build, files, version } from '$service-worker';

const CACHE_NAME = `wakedock-dashboard-${version}`;
const STATIC_CACHE_NAME = `wakedock-static-${version}`;
const RUNTIME_CACHE_NAME = `wakedock-runtime-${version}`;

// Files to cache on install
const STATIC_ASSETS = [
  ...build,
  ...files,
  '/offline.html'
];

// API endpoints that should be cached
const API_CACHE_PATTERNS = [
  /^\/api\/services$/,
  /^\/api\/system\/overview$/,
  /^\/api\/users$/
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      }),
      caches.open(RUNTIME_CACHE_NAME).then((cache) => {
        console.log('[SW] Runtime cache created');
        return cache;
      })
    ]).then(() => {
      console.log('[SW] Service worker installed successfully');
      // Skip waiting to activate immediately
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (
            cacheName !== CACHE_NAME &&
            cacheName !== STATIC_CACHE_NAME &&
            cacheName !== RUNTIME_CACHE_NAME
          ) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Service worker activated');
      // Take control of all pages immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - handle network requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip chrome-extension requests
  if (url.protocol === 'chrome-extension:') return;

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static assets
  if (isStaticAsset(url)) {
    event.respondWith(handleStaticAsset(request));
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigation(request));
    return;
  }

  // Default: try network first, then cache
  event.respondWith(
    fetch(request).catch(() => {
      return caches.match(request);
    })
  );
});

// Handle API requests with cache-first strategy for cacheable endpoints
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const isCacheable = API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));

  if (isCacheable) {
    try {
      // Try network first
      const networkResponse = await fetch(request);

      if (networkResponse.ok) {
        // Clone and cache the response
        const cache = await caches.open(RUNTIME_CACHE_NAME);
        cache.put(request, networkResponse.clone());
        return networkResponse;
      }
    } catch (error) {
      console.log('[SW] Network request failed, trying cache:', error);
    }

    // Fallback to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
  }

  // For non-cacheable or failed requests, just try network
  return fetch(request);
}

// Handle static assets with cache-first strategy
async function handleStaticAsset(request) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Failed to fetch static asset:', error);

    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }

    throw error;
  }
}

// Handle navigation requests
async function handleNavigation(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('[SW] Navigation request failed, returning offline page:', error);

    // Return cached version or offline page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    return caches.match('/offline.html');
  }
}

// Check if URL is a static asset
function isStaticAsset(url) {
  return (
    url.pathname.startsWith('/_app/') ||
    url.pathname.startsWith('/static/') ||
    url.pathname.includes('.') // Files with extensions
  );
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);

  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  console.log('[SW] Performing background sync...');

  try {
    // Sync any pending actions stored in IndexedDB
    // This would include service start/stop commands that failed while offline
    const pendingActions = await getPendingActions();

    for (const action of pendingActions) {
      try {
        await fetch(action.url, action.options);
        await removePendingAction(action.id);
        console.log('[SW] Successfully synced action:', action.id);
      } catch (error) {
        console.log('[SW] Failed to sync action:', action.id, error);
      }
    }
  } catch (error) {
    console.log('[SW] Background sync failed:', error);
  }
}

// Notification handling
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  if (event.data) {
    const data = event.data.json();

    const options = {
      body: data.body,
      icon: '/favicon.png',
      badge: '/favicon.png',
      tag: data.tag || 'wakedock-notification',
      data: data.data || {},
      actions: data.actions || []
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.notification.tag);

  event.notification.close();

  // Handle notification action
  if (event.action) {
    // Handle specific actions defined in the notification
    console.log('[SW] Notification action:', event.action);
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Utility functions for IndexedDB operations
async function getPendingActions() {
  // This would implement IndexedDB operations to retrieve pending actions
  // For now, return empty array
  return [];
}

async function removePendingAction(id) {
  // This would implement IndexedDB operations to remove a pending action
  console.log('[SW] Removing pending action:', id);
}

// Message handling for communication with the main application
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version });
  }
});
