/**
 * Advanced Store Management - Phase 2 Frontend Modernization
 * Exports all advanced stores and utilities
 */

// Dashboard store with intelligent caching
export { dashboardStore, CacheStore } from './dashboardStore';

// WebSocket store for real-time updates  
export {
    webSocketStore,
    wsConnected,
    wsReconnecting,
    wsError,
    wsLastMessage,
    wsStats,
    connectionStatus,
    cleanupWebSocket
} from './webSocketStore';

// Performance store for lazy loading and optimization
export {
    performanceStore,
    performanceMetrics,
    resourcesLoading,
    resourcesLoaded,
    resourcesError,
    isLoading,
    hasErrors,
    bundleSize,
    networkInfo,
    adaptiveLoadingEnabled,
    preloadComponent,
    observeForLazyLoad,
    cleanupPerformanceStore
} from './performanceStore';

// PWA store for offline support
export {
    pwaStore,
    pwaInstallable,
    pwaInstalled,
    pwaPromptEvent,
    swRegistered,
    swUpdateAvailable,
    swActivated,
    isOnline,
    wasOffline,
    cacheStats,
    isStandalone,
    canInstall,
    needsUpdate,
    offlineCapable,
    installApp,
    updateApp,
    getCacheInfo,
    clearAppCache,
    queueOfflineRequest,
    networkAwareFetch,
    cleanupPWA
} from './pwaStore';

// Advanced store integration utilities
import { dashboardStore } from './dashboardStore';
import { webSocketStore } from './webSocketStore';
import { performanceStore } from './performanceStore';
import { pwaStore } from './pwaStore';

// Initialize all stores
export const initializeAdvancedStores = () => {
    console.log('Initializing advanced store management...');

    // Initialize performance monitoring
    performanceStore.preloadCriticalComponents(['Dashboard', 'ServiceList']);

    // Get initial cache info
    pwaStore.getCacheInfo();

    // Load critical dashboard data
    dashboardStore.loadServices();
    dashboardStore.loadMetrics();

    console.log('Advanced stores initialized successfully');
};

// Cleanup all stores
export const cleanupAdvancedStores = () => {
    console.log('Cleaning up advanced stores...');

    // Clear caches
    dashboardStore.clearCache();

    // Disconnect WebSocket
    webSocketStore.disconnect();

    // Clear performance data
    performanceStore.clearLoadingStates();

    // Clear PWA offline queue
    pwaStore.clearOfflineQueue();

    console.log('Advanced stores cleaned up');
};
