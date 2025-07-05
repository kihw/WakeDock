/**
 * Advanced Dashboard Store with optimized state management
 * Implements intelligent caching, real-time updates, and offline support
 */

import { writable, derived, readable } from 'svelte/store';
import { browser } from '$app/environment';
import type { Service, SystemMetrics, User } from '$lib/types';

// WebSocket connection state
export const wsConnected = writable(false);
export const wsReconnecting = writable(false);

// Cache configuration
const CACHE_DURATION = {
    services: 30 * 1000, // 30 seconds
    metrics: 10 * 1000,  // 10 seconds
    users: 5 * 60 * 1000, // 5 minutes
    settings: 10 * 60 * 1000 // 10 minutes
};

// Cache entry interface
interface CacheEntry<T> {
    data: T;
    timestamp: number;
    expiresAt: number;
}

// Generic cache store
class CacheStore<T> {
    private cache = new Map<string, CacheEntry<T>>();
    private store = writable<Map<string, T>>(new Map());

    constructor(private cacheDuration: number = 60000) { }

    set(key: string, value: T): void {
        const timestamp = Date.now();
        const entry: CacheEntry<T> = {
            data: value,
            timestamp,
            expiresAt: timestamp + this.cacheDuration
        };

        this.cache.set(key, entry);
        this.updateStore();
    }

    get(key: string): T | null {
        const entry = this.cache.get(key);
        if (!entry) return null;

        if (Date.now() > entry.expiresAt) {
            this.cache.delete(key);
            this.updateStore();
            return null;
        }

        return entry.data;
    }

    has(key: string): boolean {
        return this.get(key) !== null;
    }

    delete(key: string): void {
        this.cache.delete(key);
        this.updateStore();
    }

    clear(): void {
        this.cache.clear();
        this.updateStore();
    }

    invalidateExpired(): void {
        const now = Date.now();
        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expiresAt) {
                this.cache.delete(key);
            }
        }
        this.updateStore();
    }

    private updateStore(): void {
        const dataMap = new Map<string, T>();
        for (const [key, entry] of this.cache.entries()) {
            dataMap.set(key, entry.data);
        }
        this.store.set(dataMap);
    }

    subscribe = this.store.subscribe;
}

// Dashboard State Management
class DashboardStore {
    private servicesCache = new CacheStore<Service[]>(CACHE_DURATION.services);
    private metricsCache = new CacheStore<SystemMetrics>(CACHE_DURATION.metrics);
    private usersCache = new CacheStore<User[]>(CACHE_DURATION.users);

    // Loading states
    public servicesLoading = writable(false);
    public metricsLoading = writable(false);
    public usersLoading = writable(false);

    // Error states
    public servicesError = writable<string | null>(null);
    public metricsError = writable<string | null>(null);
    public usersError = writable<string | null>(null);

    // Data stores
    public services = writable<Service[]>([]);
    public metrics = writable<SystemMetrics | null>(null);
    public users = writable<User[]>([]);

    // Derived stores
    public runningServices = derived(this.services, $services =>
        $services.filter(service => service.status === 'running')
    );

    public failedServices = derived(this.services, $services =>
        $services.filter(service => service.status === 'failed')
    );

    public servicesStats = derived(this.services, $services => ({
        total: $services.length,
        running: $services.filter(s => s.status === 'running').length,
        stopped: $services.filter(s => s.status === 'stopped').length,
        failed: $services.filter(s => s.status === 'failed').length
    }));

    constructor() {
        // Initialize cleanup interval
        if (browser) {
            setInterval(() => {
                this.servicesCache.invalidateExpired();
                this.metricsCache.invalidateExpired();
                this.usersCache.invalidateExpired();
            }, 60000); // Clean up every minute
        }
    }

    // Services management
    async loadServices(force: boolean = false): Promise<Service[]> {
        const cacheKey = 'all';

        if (!force && this.servicesCache.has(cacheKey)) {
            const cached = this.servicesCache.get(cacheKey);
            if (cached) {
                this.services.set(cached);
                return cached;
            }
        }

        try {
            this.servicesLoading.set(true);
            this.servicesError.set(null);

            const response = await fetch('/api/v1/services');
            if (!response.ok) {
                throw new Error(`Failed to load services: ${response.statusText}`);
            }

            const services: Service[] = await response.json();

            // Cache and update store
            this.servicesCache.set(cacheKey, services);
            this.services.set(services);

            return services;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.servicesError.set(errorMessage);
            throw error;
        } finally {
            this.servicesLoading.set(false);
        }
    }

    // Real-time services update
    updateService(service: Service): void {
        this.services.update(services => {
            const index = services.findIndex(s => s.id === service.id);
            if (index !== -1) {
                services[index] = service;
            } else {
                services.push(service);
            }

            // Update cache
            this.servicesCache.set('all', services);

            return services;
        });
    }

    // Remove service
    removeService(serviceId: string): void {
        this.services.update(services => {
            const filtered = services.filter(s => s.id !== serviceId);
            this.servicesCache.set('all', filtered);
            return filtered;
        });
    }

    // Metrics management
    async loadMetrics(force: boolean = false): Promise<SystemMetrics | null> {
        const cacheKey = 'current';

        if (!force && this.metricsCache.has(cacheKey)) {
            const cached = this.metricsCache.get(cacheKey);
            if (cached) {
                this.metrics.set(cached);
                return cached;
            }
        }

        try {
            this.metricsLoading.set(true);
            this.metricsError.set(null);

            const response = await fetch('/api/v1/system/metrics');
            if (!response.ok) {
                throw new Error(`Failed to load metrics: ${response.statusText}`);
            }

            const metrics: SystemMetrics = await response.json();

            // Cache and update store
            this.metricsCache.set(cacheKey, metrics);
            this.metrics.set(metrics);

            return metrics;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.metricsError.set(errorMessage);
            throw error;
        } finally {
            this.metricsLoading.set(false);
        }
    }

    // Real-time metrics update
    updateMetrics(metrics: SystemMetrics): void {
        this.metricsCache.set('current', metrics);
        this.metrics.set(metrics);
    }

    // Users management
    async loadUsers(force: boolean = false): Promise<User[]> {
        const cacheKey = 'all';

        if (!force && this.usersCache.has(cacheKey)) {
            const cached = this.usersCache.get(cacheKey);
            if (cached) {
                this.users.set(cached);
                return cached;
            }
        }

        try {
            this.usersLoading.set(true);
            this.usersError.set(null);

            const response = await fetch('/api/v1/users');
            if (!response.ok) {
                throw new Error(`Failed to load users: ${response.statusText}`);
            }

            const users: User[] = await response.json();

            // Cache and update store
            this.usersCache.set(cacheKey, users);
            this.users.set(users);

            return users;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.usersError.set(errorMessage);
            throw error;
        } finally {
            this.usersLoading.set(false);
        }
    }

    // Clear all caches
    clearCache(): void {
        this.servicesCache.clear();
        this.metricsCache.clear();
        this.usersCache.clear();
    }

    // Get cache statistics
    getCacheStats(): Record<string, any> {
        return {
            services: this.servicesCache.has('all') ? 'cached' : 'empty',
            metrics: this.metricsCache.has('current') ? 'cached' : 'empty',
            users: this.usersCache.has('all') ? 'cached' : 'empty'
        };
    }
}

// Create and export the dashboard store instance
export const dashboardStore = new DashboardStore();

// Export additional utilities
export { CacheStore };
