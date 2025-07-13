/**
 * WakeDock Dashboard Service Worker
 * Provides offline functionality and caching for PWA features
 */

/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

declare const self: ServiceWorkerGlobalScope;

// Unified cache configuration
const CACHE_NAME = `wakedock-cache-${version}`;
const STATIC_CACHE_NAME = `wakedock-static-${version}`;
const API_CACHE_NAME = `wakedock-api-${version}`;

// Simplified auth detection
const isAuthPath = (pathname: string) => pathname.includes('/auth/') || pathname.includes('/login');

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
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all([
          // Delete old caches
          ...cacheNames
            .filter((name) => name !== STATIC_CACHE_NAME && name !== API_CACHE_NAME)
            .map((name) => caches.delete(name)),
          // Clear auth cache entries
          clearAuthCache()
        ]);
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - unified request handling
self.addEventListener('fetch', (event: FetchEvent) => {
  const request = event.request;
  const url = new URL(request.url);

  // Auth requests bypass service worker completely
  if (isAuthPath(url.pathname)) {
    return;
  }

  // Handle by request type
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else if (isStaticAsset(url.pathname)) {
    event.respondWith(handleStaticAsset(request));
  } else if (request.mode === 'navigate') {
    event.respondWith(handleNavigation(request));
  } else {
    event.respondWith(
      fetch(request).catch(() => caches.match(request) || new Response('Offline', { status: 503 }))
    );
  }
});

// Simplified API request handling
async function handleApiRequest(request: Request): Promise<Response> {
  const url = new URL(request.url);

  // Cache-first for cacheable endpoints
  const isCacheable = request.method === 'GET' &&
    (url.pathname.includes('/services') || url.pathname.includes('/system') || url.pathname.includes('/health'));

  if (isCacheable) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      // Update cache in background
      fetch(request)
        .then((response) => response.ok && caches.open(API_CACHE_NAME).then((cache) => cache.put(request, response.clone())))
        .catch(() => { });
      return cachedResponse;
    }
  }

  // Network first
  try {
    const response = await fetch(request);
    // Cache successful GET responses
    if (response.ok && request.method === 'GET' && isCacheable) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Fallback to cache for GET requests
    if (request.method === 'GET') {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) return cachedResponse;
    }
    return createErrorResponse('Network Error', (error as Error)?.message || 'Unknown error');
  }
}


// Helper to create consistent error responses
function createErrorResponse(error: string, message: string): Response {
  return new Response(JSON.stringify({ error, message }), {
    status: 503,
    headers: { 'Content-Type': 'application/json' }
  });
}

// Clear auth-related cache entries
async function clearAuthCache(): Promise<void> {
  try {
    const cache = await caches.open(API_CACHE_NAME);
    const keys = await cache.keys();
    const authKeys = keys.filter(key => isAuthPath(new URL(key.url).pathname));
    await Promise.all(authKeys.map(key => cache.delete(key)));
  } catch (error) {
    console.error('[SW] Failed to clear auth cache:', error);
  }
}

// Handle static assets with cache-first strategy
async function handleStaticAsset(request: Request): Promise<Response> {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);

    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    return new Response('Asset not found', { status: 404 });
  }
}

// Handle navigation requests
async function handleNavigation(request: Request): Promise<Response> {
  try {
    const response = await fetch(request);
    return response;
  } catch (error) {
    // Fallback to cached index.html for SPA routing
    const cachedResponse = await caches.match('/');
    if (cachedResponse) {
      return cachedResponse;
    }

    return new Response('Offline', { status: 503 });
  }
}

// Check if URL is a static asset
function isStaticAsset(pathname: string): boolean {
  return (
    pathname.startsWith('/_app/') ||
    pathname.startsWith('/assets/') ||
    pathname.endsWith('.js') ||
    pathname.endsWith('.css') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.jpg') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.ico')
  );
}

// Push notification handling
self.addEventListener('push', (event: PushEvent) => {
  const options = {
    body: 'WakeDock notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    tag: 'wakedock-notification',
    data: { url: '/' },
  };

  event.waitUntil(self.registration.showNotification('WakeDock', options));
});

self.addEventListener('notificationclick', (event: NotificationEvent) => {
  event.notification.close();
  event.waitUntil(self.clients.openWindow('/'));
});

// Message handling for communication with the main application
self.addEventListener('message', (event: ExtendableMessageEvent) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data?.type === 'CLEAR_AUTH_CACHE') {
    clearAuthCache();
  }
});
