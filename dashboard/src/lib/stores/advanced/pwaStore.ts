/**
 * PWA Store for Progressive Web App features
 * Handles service worker, offline support, and app installation
 */

import { writable, readable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// PWA installation state
export const pwaInstallable = writable(false);
export const pwaInstalled = writable(false);
export const pwaPromptEvent = writable<any>(null);

// Service worker state
export const swRegistered = writable(false);
export const swUpdateAvailable = writable(false);
export const swActivated = writable(false);

// Offline state
export const isOnline = writable(true);
export const wasOffline = writable(false);

// Cache state
export const cacheStats = writable({
    size: 0,
    entries: 0,
    lastUpdated: null as Date | null
});

class PWAStore {
    private swRegistration: ServiceWorkerRegistration | null = null;
    private deferredPrompt: any = null;
    private offlineQueue: Array<{ url: string; options: RequestInit }> = [];

    constructor() {
        if (browser) {
            // Initialize service worker and PWA features
            console.log('[PWA] Initializing PWA features');
            this.initServiceWorker();
            this.initOnlineDetection();
            this.initInstallPrompt();
        }
    }

    // Unregister all service workers
    private async unregisterAllServiceWorkers(): Promise<void> {
        if ('serviceWorker' in navigator) {
            try {
                const registrations = await navigator.serviceWorker.getRegistrations();
                for (const registration of registrations) {
                    console.log('[PWA] Force unregistering service worker:', registration.scope);
                    await registration.unregister();
                }
                console.log('[PWA] All service workers unregistered');
            } catch (error) {
                console.error('[PWA] Error unregistering service workers:', error);
            }
        }
    }

    // Initialize service worker
    private async initServiceWorker(): Promise<void> {
        if ('serviceWorker' in navigator) {
            try {
                // Register service worker
                console.log('[PWA] Registering service worker');

                // Unregister any existing service workers to ensure clean state
                const registrations = await navigator.serviceWorker.getRegistrations();
                for (const registration of registrations) {
                    console.log('[PWA] Unregistering existing service worker');
                    await registration.unregister();
                }

                // Register new service worker
                this.swRegistration = await navigator.serviceWorker.register('/service-worker.js');
                swRegistered.set(true);

                // Listen for updates
                this.swRegistration.addEventListener('updatefound', () => {
                    const newWorker = this.swRegistration?.installing;
                    if (newWorker) {
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                swUpdateAvailable.set(true);
                            }
                            if (newWorker.state === 'activated') {
                                swActivated.set(true);
                            }
                        });
                    }
                });

                // Check for existing service worker
                if (this.swRegistration.active) {
                    swActivated.set(true);
                }

                console.log('Service Worker registered successfully');
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    // Initialize online/offline detection
    private initOnlineDetection(): void {
        // Set initial state
        isOnline.set(navigator.onLine);

        // Listen for online/offline events
        window.addEventListener('online', () => {
            isOnline.set(true);
            this.processOfflineQueue();
        });

        window.addEventListener('offline', () => {
            isOnline.set(false);
            wasOffline.set(true);
        });
    }

    // Initialize installation prompt
    private initInstallPrompt(): void {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            pwaPromptEvent.set(e);
            pwaInstallable.set(true);
        });

        window.addEventListener('appinstalled', () => {
            pwaInstalled.set(true);
            pwaInstallable.set(false);
            this.deferredPrompt = null;
            pwaPromptEvent.set(null);
        });
    }

    // Install PWA
    async installPWA(): Promise<boolean> {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;

            if (outcome === 'accepted') {
                pwaInstalled.set(true);
                pwaInstallable.set(false);
                this.deferredPrompt = null;
                pwaPromptEvent.set(null);
                return true;
            }
        }
        return false;
    }

    // Update service worker
    async updateServiceWorker(): Promise<void> {
        if (this.swRegistration) {
            await this.swRegistration.update();
            window.location.reload();
        }
    }

    // Queue request for offline processing
    queueOfflineRequest(url: string, options: RequestInit): void {
        this.offlineQueue.push({ url, options });

        // Store in localStorage for persistence
        localStorage.setItem('pwa-offline-queue', JSON.stringify(this.offlineQueue));
    }

    // Process offline queue when back online
    private async processOfflineQueue(): Promise<void> {
        // Load from localStorage
        const stored = localStorage.getItem('pwa-offline-queue');
        if (stored) {
            this.offlineQueue = JSON.parse(stored);
        }

        if (this.offlineQueue.length === 0) return;

        console.log(`Processing ${this.offlineQueue.length} offline requests`);

        const processed: Array<{ url: string; options: RequestInit }> = [];

        for (const request of this.offlineQueue) {
            try {
                await fetch(request.url, request.options);
                processed.push(request);
                console.log(`Processed offline request: ${request.url}`);
            } catch (error) {
                console.error(`Failed to process offline request: ${request.url}`, error);
            }
        }

        // Remove processed requests
        this.offlineQueue = this.offlineQueue.filter(req => !processed.includes(req));

        // Update localStorage
        if (this.offlineQueue.length > 0) {
            localStorage.setItem('pwa-offline-queue', JSON.stringify(this.offlineQueue));
        } else {
            localStorage.removeItem('pwa-offline-queue');
        }
    }

    // Get cache information
    async getCacheInfo(): Promise<{ size: number; entries: number }> {
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            let totalSize = 0;
            let totalEntries = 0;

            for (const cacheName of cacheNames) {
                const cache = await caches.open(cacheName);
                const keys = await cache.keys();
                totalEntries += keys.length;

                // Estimate size (rough approximation)
                for (const request of keys) {
                    try {
                        const response = await cache.match(request);
                        if (response) {
                            const blob = await response.blob();
                            totalSize += blob.size;
                        }
                    } catch (error) {
                        // Ignore errors for size calculation
                    }
                }
            }

            const info = { size: totalSize, entries: totalEntries };
            cacheStats.set({
                ...info,
                lastUpdated: new Date()
            });

            return info;
        }

        return { size: 0, entries: 0 };
    }

    // Clear cache
    async clearCache(): Promise<void> {
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            await Promise.all(cacheNames.map(name => caches.delete(name)));

            cacheStats.set({
                size: 0,
                entries: 0,
                lastUpdated: new Date()
            });
        }
    }

    // Check if PWA is running in standalone mode
    isStandalone(): boolean {
        return window.matchMedia('(display-mode: standalone)').matches ||
            (window.navigator as any).standalone ||
            document.referrer.includes('android-app://');
    }

    // Get offline queue size
    getOfflineQueueSize(): number {
        return this.offlineQueue.length;
    }

    // Clear offline queue
    clearOfflineQueue(): void {
        this.offlineQueue = [];
        localStorage.removeItem('pwa-offline-queue');
    }
}

// Create PWA store instance
export const pwaStore = new PWAStore();

// Derived stores
export const isStandalone = readable(false, (set) => {
    if (browser) {
        set(pwaStore.isStandalone());

        // Listen for display mode changes
        const mediaQuery = window.matchMedia('(display-mode: standalone)');
        const handler = (e: MediaQueryListEvent) => set(e.matches);

        mediaQuery.addEventListener('change', handler);

        return () => {
            mediaQuery.removeEventListener('change', handler);
        };
    }
});

export const canInstall = derived(
    [pwaInstallable, pwaInstalled],
    ([$installable, $installed]) => $installable && !$installed
);

export const needsUpdate = derived(
    [swUpdateAvailable, swActivated],
    ([$updateAvailable, $activated]) => $updateAvailable && $activated
);

export const offlineCapable = derived(
    [swRegistered, swActivated],
    ([$registered, $activated]) => $registered && $activated
);

// Utility functions
export const installApp = () => pwaStore.installPWA();
export const updateApp = () => pwaStore.updateServiceWorker();
export const getCacheInfo = () => pwaStore.getCacheInfo();
export const clearAppCache = () => pwaStore.clearCache();
export const queueOfflineRequest = (url: string, options: RequestInit) =>
    pwaStore.queueOfflineRequest(url, options);

// Network-aware fetch wrapper
export const networkAwareFetch = async (
    url: string,
    options: RequestInit = {}
): Promise<Response> => {
    if (navigator.onLine) {
        try {
            return await fetch(url, options);
        } catch (error) {
            // If online but fetch fails, might be network issue
            if (options.method === 'GET') {
                // Try to serve from cache
                const cache = await caches.open('api-cache');
                const cached = await cache.match(url);
                if (cached) {
                    return cached;
                }
            }
            throw error;
        }
    } else {
        // Offline - try cache first
        if (options.method === 'GET') {
            const cache = await caches.open('api-cache');
            const cached = await cache.match(url);
            if (cached) {
                return cached;
            }
        }

        // Queue for later if it's a mutation
        if (options.method !== 'GET') {
            pwaStore.queueOfflineRequest(url, options);
        }

        throw new Error('Offline - request queued');
    }
};

// Cleanup function
export const cleanupPWA = () => {
    pwaStore.clearOfflineQueue();
};
