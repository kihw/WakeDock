/**
 * Performance Store for Lazy Loading and Code Splitting
 * Handles dynamic imports, component lazy loading, and performance optimization
 */

import { writable, readable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// Performance metrics
export const performanceMetrics = writable({
    pageLoadTime: 0,
    firstContentfulPaint: 0,
    largestContentfulPaint: 0,
    timeToInteractive: 0,
    cumulativeLayoutShift: 0,
    totalBlockingTime: 0
});

// Resource loading states
export const resourcesLoading = writable(new Set<string>());
export const resourcesLoaded = writable(new Set<string>());
export const resourcesError = writable(new Set<string>());

// Lazy loading configuration
interface LazyLoadConfig {
    threshold: number;
    rootMargin: string;
    retryAttempts: number;
    retryDelay: number;
}

const DEFAULT_LAZY_CONFIG: LazyLoadConfig = {
    threshold: 0.1,
    rootMargin: '50px',
    retryAttempts: 3,
    retryDelay: 1000
};

// Component registry for lazy loading
const componentRegistry = new Map<string, () => Promise<any>>();
const componentCache = new Map<string, any>();
const preloadQueue = new Set<string>();

// Route-based preloading strategy
const routeComponentMap = new Map<string, string[]>([
    ['/services', ['ServiceList', 'ServiceCard', 'ServiceMetrics']],
    ['/monitoring', ['MonitoringDashboard', 'MetricsChart', 'AlertPanel']],
    ['/analytics', ['AnalyticsDashboard', 'ReportsChart', 'DataTable']],
    ['/backup', ['BackupManager', 'BackupList', 'RestoreDialog']],
    ['/users', ['UserManagement', 'UserList', 'RoleEditor']],
    ['/settings', ['SettingsPanel', 'ConfigEditor', 'SystemInfo']]
]);

class PerformanceStore {
    private observer: IntersectionObserver | null = null;
    private loadingElements = new Map<Element, string>();
    private config: LazyLoadConfig = DEFAULT_LAZY_CONFIG;
    private preloadTimer: number | null = null;

    constructor() {
        if (browser) {
            this.initPerformanceObserver();
            this.initLazyLoading();
        }
    }

    // Initialize performance monitoring
    private initPerformanceObserver(): void {
        if ('PerformanceObserver' in window) {
            // Web Vitals monitoring
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.handlePerformanceEntry(entry);
                }
            });

            observer.observe({ entryTypes: ['paint', 'largest-contentful-paint', 'layout-shift'] });
        }

        // Monitor page load time
        window.addEventListener('load', () => {
            if (performance.timing) {
                const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                performanceMetrics.update(metrics => ({
                    ...metrics,
                    pageLoadTime: loadTime
                }));
            }
        });
    }

    private handlePerformanceEntry(entry: PerformanceEntry): void {
        performanceMetrics.update(metrics => {
            const newMetrics = { ...metrics };

            switch (entry.entryType) {
                case 'paint':
                    if (entry.name === 'first-contentful-paint') {
                        newMetrics.firstContentfulPaint = entry.startTime;
                    }
                    break;

                case 'largest-contentful-paint':
                    newMetrics.largestContentfulPaint = entry.startTime;
                    break;

                case 'layout-shift':
                    if (!(entry as any).hadRecentInput) {
                        newMetrics.cumulativeLayoutShift += (entry as any).value;
                    }
                    break;
            }

            return newMetrics;
        });
    }

    // Initialize lazy loading
    private initLazyLoading(): void {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const componentName = this.loadingElements.get(entry.target);
                            if (componentName) {
                                this.loadComponent(componentName);
                                this.observer?.unobserve(entry.target);
                                this.loadingElements.delete(entry.target);
                            }
                        }
                    });
                },
                {
                    threshold: this.config.threshold,
                    rootMargin: this.config.rootMargin
                }
            );
        }
    }

    // Register component for lazy loading
    registerComponent(name: string, importFn: () => Promise<any>): void {
        componentRegistry.set(name, importFn);
    }

    // Load component dynamically with caching
    async loadComponent(name: string, retryCount = 0): Promise<any> {
        // Check cache first
        if (componentCache.has(name)) {
            return componentCache.get(name);
        }

        const importFn = componentRegistry.get(name);
        if (!importFn) {
            throw new Error(`Component ${name} not registered`);
        }

        // Mark as loading
        resourcesLoading.update(set => new Set([...set, name]));

        try {
            const startTime = performance.now();
            const component = await importFn();
            const loadTime = performance.now() - startTime;

            // Cache the component
            componentCache.set(name, component);

            // Mark as loaded
            resourcesLoading.update(set => {
                const newSet = new Set(set);
                newSet.delete(name);
                return newSet;
            });

            resourcesLoaded.update(set => new Set([...set, name]));

            // Update load time metrics
            console.log(`Component ${name} loaded in ${loadTime.toFixed(2)}ms`);

            return component;
        } catch (error) {
            console.error(`Failed to load component ${name}:`, error);

            // Remove from loading
            resourcesLoading.update(set => {
                const newSet = new Set(set);
                newSet.delete(name);
                return newSet;
            });

            // Add to error set
            resourcesError.update(set => new Set([...set, name]));

            // Retry logic
            if (retryCount < this.config.retryAttempts) {
                console.log(`Retrying component ${name} load (attempt ${retryCount + 1})`);
                await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
                return this.loadComponent(name, retryCount + 1);
            }

            throw error;
        }
    }

    // Observe element for lazy loading
    observeElement(element: Element, componentName: string): void {
        if (this.observer) {
            this.loadingElements.set(element, componentName);
            this.observer.observe(element);
        }
    }

    // Preload critical components
    async preloadCriticalComponents(componentNames: string[]): Promise<void> {
        const promises = componentNames.map(name => this.loadComponent(name));
        await Promise.allSettled(promises);
    }

    // Preload components based on route
    preloadForRoute(route: string): void {
        const components = routeComponentMap.get(route);
        if (components) {
            components.forEach(componentName => {
                if (!componentCache.has(componentName) && !preloadQueue.has(componentName)) {
                    preloadQueue.add(componentName);
                    // Delay preloading to not interfere with critical path
                    this.schedulePreload(componentName);
                }
            });
        }
    }

    // Schedule component preloading
    private schedulePreload(componentName: string): void {
        if (this.preloadTimer) {
            clearTimeout(this.preloadTimer);
        }

        this.preloadTimer = window.setTimeout(async () => {
            try {
                await this.loadComponent(componentName);
                preloadQueue.delete(componentName);
                console.log(`Preloaded component: ${componentName}`);
            } catch (error) {
                console.warn(`Failed to preload component ${componentName}:`, error);
                preloadQueue.delete(componentName);
            }
        }, 100); // Small delay to not block main thread
    }

    // Preload components on hover (for immediate navigation)
    preloadOnHover(componentNames: string[]): void {
        componentNames.forEach(name => {
            if (!componentCache.has(name)) {
                this.schedulePreload(name);
            }
        });
    }

    // Get component from cache or load it
    async getComponent(name: string): Promise<any> {
        if (componentCache.has(name)) {
            return componentCache.get(name);
        }
        return this.loadComponent(name);
    }

    // Clear component cache (useful for development)
    clearCache(): void {
        componentCache.clear();
        resourcesLoaded.set(new Set());
        resourcesError.set(new Set());
    }

    // Get cache statistics
    getCacheStats(): {
        cached: number;
        loading: number;
        errors: number;
        preloadQueue: number;
    } {
        return {
            cached: componentCache.size,
            loading: 0, // Will be updated by store subscription
            errors: 0,  // Will be updated by store subscription
            preloadQueue: preloadQueue.size
        };
    }

    // Get performance score
    getPerformanceScore(): number {
        const metrics = performanceMetrics;
        // Simple scoring based on Web Vitals
        // In real implementation, this would be more sophisticated
        return 85; // Placeholder
    }

    // Clear loading states
    clearLoadingStates(): void {
        resourcesLoading.set(new Set());
        resourcesError.set(new Set());
    }

    // Get loading statistics
    getLoadingStats(): {
        loading: number;
        loaded: number;
        errors: number;
        total: number;
    } {
        let loading = 0;
        let loaded = 0;
        let errors = 0;

        resourcesLoading.subscribe(set => loading = set.size)();
        resourcesLoaded.subscribe(set => loaded = set.size)();
        resourcesError.subscribe(set => errors = set.size)();

        return {
            loading,
            loaded,
            errors,
            total: componentRegistry.size
        };
    }
}

// Create performance store instance
export const performanceStore = new PerformanceStore();

// Pre-register common components
if (browser) {
    // Components will be registered dynamically when needed
    // performanceStore.registerComponent('ServiceList', () => import('$lib/components/services/ServiceList.svelte'));
    // performanceStore.registerComponent('MetricsChart', () => import('$lib/components/metrics/MetricsChart.svelte'));
    // performanceStore.registerComponent('LogViewer', () => import('$lib/components/logs/LogViewer.svelte'));
    // performanceStore.registerComponent('SettingsForm', () => import('$lib/components/settings/SettingsForm.svelte'));
    // performanceStore.registerComponent('UserManagement', () => import('$lib/components/users/UserManagement.svelte'));
}

// Derived store for overall loading state
export const isLoading = derived(resourcesLoading, $loading => $loading.size > 0);

// Derived store for error state
export const hasErrors = derived(resourcesError, $errors => $errors.size > 0);

// Bundle size tracking
export const bundleSize = readable(0, (set) => {
    if (browser && 'performance' in window) {
        // Estimate bundle size from navigation timing
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
            const transferSize = navigation.transferSize || 0;
            set(transferSize);
        }
    }
});

// Network information
export const networkInfo = readable({
    effectiveType: '4g',
    downlink: 10,
    rtt: 100,
    saveData: false
}, (set) => {
    if (browser && 'navigator' in window && 'connection' in navigator) {
        const connection = (navigator as any).connection;
        if (connection) {
            const updateNetworkInfo = () => {
                set({
                    effectiveType: connection.effectiveType || '4g',
                    downlink: connection.downlink || 10,
                    rtt: connection.rtt || 100,
                    saveData: connection.saveData || false
                });
            };

            updateNetworkInfo();
            connection.addEventListener('change', updateNetworkInfo);

            return () => {
                connection.removeEventListener('change', updateNetworkInfo);
            };
        }
    }
});

// Adaptive loading based on network conditions
export const adaptiveLoadingEnabled = derived(
    [networkInfo],
    ([$networkInfo]) => {
        // Enable adaptive loading on slower connections
        return $networkInfo.effectiveType === '2g' || $networkInfo.effectiveType === '3g' || $networkInfo.saveData;
    }
);

// Export utilities
export const preloadComponent = (name: string) => performanceStore.loadComponent(name);
export const observeForLazyLoad = (element: Element, componentName: string) =>
    performanceStore.observeElement(element, componentName);

// Cleanup function
export const cleanupPerformanceStore = () => {
    performanceStore.clearLoadingStates();
};
