/**
 * System Store
 * Manages system information and health status
 */
import { writable, derived } from 'svelte/store';
import { api, type SystemOverview, type ApiError } from '../api.js';

export interface SystemNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: string;
  read: boolean;
}

interface SystemState {
  overview: SystemOverview | null;
  health: Record<string, any> | null;
  services: any[] | null;
  status: string | null;
  notifications: SystemNotification[] | null;
  isLoading: boolean;
  error: string | null;
  // Additional properties needed by components
  system: {
    status: string;
  } | null;
  metrics: {
    cpu: number;
    memory: number;
    disk: number;
  } | null;
  uptime: number | null;
  memoryUsed: number | null;
  lastUpdated: Date | null;
  autoRefresh: boolean;
  refreshInterval: number; // in seconds
}

const initialState: SystemState = {
  overview: null,
  health: null,
  services: null,
  status: null,
  notifications: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  autoRefresh: false,
  refreshInterval: 30,
  // Initialize additional properties
  system: null,
  metrics: null,
  uptime: null,
  memoryUsed: null,
};

// Create the writable store
const { subscribe, set, update } = writable<SystemState>(initialState);

// Derived stores
export const systemStats = derived({ subscribe }, ($system) => $system.overview?.system || null);

export const dockerStatus = derived({ subscribe }, ($system) => $system.overview?.docker || null);

export const caddyStatus = derived({ subscribe }, ($system) => $system.overview?.caddy || null);

export const servicesOverview = derived(
  { subscribe },
  ($system) => $system.overview?.services || null
);

export const isSystemHealthy = derived({ subscribe }, ($system) => {
  if (!$system.overview) return null;

  const { docker, caddy } = $system.overview;
  return docker.status === 'healthy' && caddy.status === 'healthy';
});

// Auto-refresh functionality
let refreshTimer: NodeJS.Timeout | null = null;

const startAutoRefresh = (intervalSeconds: number) => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }

  refreshTimer = setInterval(() => {
    system.loadOverview();
    system.loadHealth();
  }, intervalSeconds * 1000);
};

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
};

// System store with methods
export const system = {
  subscribe,

  // Load system overview
  loadOverview: async () => {
    update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const overview = await api.getSystemOverview();
      update((state) => ({
        ...state,
        overview,
        isLoading: false,
        lastUpdated: new Date(),
      }));
    } catch (error) {
      const apiError = error as ApiError;
      update((state) => ({
        ...state,
        isLoading: false,
        error: apiError.message || 'Failed to load system overview',
      }));
    }
  },

  // Load health status
  loadHealth: async () => {
    try {
      const health = await api.getHealth();
      update((state) => ({ ...state, health }));
    } catch (error) {
      const apiError = error as ApiError;
      console.error('Failed to load health status:', apiError.message);
      // Don't update error state for health checks to avoid spam
    }
  },

  // Load both overview and health
  load: async () => {
    await Promise.all([system.loadOverview(), system.loadHealth()]);
  },

  // Enable auto-refresh
  enableAutoRefresh: (intervalSeconds: number = 30) => {
    update((state) => ({
      ...state,
      autoRefresh: true,
      refreshInterval: intervalSeconds,
    }));

    startAutoRefresh(intervalSeconds);
  },

  // Disable auto-refresh
  disableAutoRefresh: () => {
    update((state) => ({ ...state, autoRefresh: false }));
    stopAutoRefresh();
  },

  // Update refresh interval
  setRefreshInterval: (intervalSeconds: number) => {
    update((state) => {
      const newState = { ...state, refreshInterval: intervalSeconds };

      if (state.autoRefresh) {
        stopAutoRefresh();
        startAutoRefresh(intervalSeconds);
      }

      return newState;
    });
  },

  // Clear error
  clearError: () => {
    update((state) => ({ ...state, error: null }));
  },

  // Manual refresh
  refresh: async () => {
    await system.load();
  },

  // Cleanup (call when component unmounts)
  cleanup: () => {
    stopAutoRefresh();
  },

  // Load system info (alias for load)
  loadSystemInfo: async () => {
    await system.load();
  },

  // Update services
  updateServices: (newServices: any[]) => {
    update((state) => ({ ...state, services: newServices }));
  },

  // Update system status
  updateStatus: (newStatus: string) => {
    update((state) => ({ ...state, status: newStatus }));
  },

  // Update notifications
  updateNotifications: (newNotifications: any[]) => {
    update((state) => ({ ...state, notifications: newNotifications }));
  },
};

// Alias for compatibility
export const systemStore = system;
