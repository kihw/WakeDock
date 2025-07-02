/**
 * Services Store
 * Manages Docker services state with caching and optimistic updates
 */
import { writable, derived, get } from 'svelte/store';
import {
  api,
  type Service,
  type CreateServiceRequest,
  type UpdateServiceRequest,
  type ApiError,
} from '../api.js';
import { notifications, serviceNotifications } from '../services/notifications.js';

interface ServicesState {
  services: Service[];
  selectedService: Service | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  cache: Map<string, { service: Service; timestamp: number }>;
  refreshInterval: NodeJS.Timeout | null;
}

const CACHE_TTL = 30000; // 30 seconds
const AUTO_REFRESH_INTERVAL = 60000; // 1 minute

const initialState: ServicesState = {
  services: [],
  selectedService: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
  cache: new Map(),
  refreshInterval: null,
};

// Create the writable store
const servicesStore = writable<ServicesState>(initialState);
const { subscribe, set, update } = servicesStore;

// Derived stores
export const runningServices = derived({ subscribe }, ($services) =>
  $services.services.filter((s) => s.status === 'running')
);

export const stoppedServices = derived({ subscribe }, ($services) =>
  $services.services.filter((s) => s.status === 'stopped')
);

export const errorServices = derived({ subscribe }, ($services) =>
  $services.services.filter((s) => s.status === 'error')
);

export const serviceStats = derived({ subscribe }, ($services) => ({
  total: $services.services.length,
  running: $services.services.filter((s) => s.status === 'running').length,
  stopped: $services.services.filter((s) => s.status === 'stopped').length,
  error: $services.services.filter((s) => s.status === 'error').length,
}));

// Services store with methods
export const services = {
  subscribe,

  // Initialize store (start auto-refresh)
  init: () => {
    services.load();
    services.startAutoRefresh();
  },

  // Start automatic refresh
  startAutoRefresh: () => {
    update((state) => {
      if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
      }

      const interval = setInterval(() => {
        services.load(true); // Silent refresh
      }, AUTO_REFRESH_INTERVAL);

      return { ...state, refreshInterval: interval };
    });
  },

  // Stop automatic refresh
  stopAutoRefresh: () => {
    update((state) => {
      if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
      }
      return { ...state, refreshInterval: null };
    });
  },

  // Load all services
  load: async (silent: boolean = false) => {
    if (!silent) {
      update((state) => ({ ...state, isLoading: true, error: null }));
    }

    try {
      const servicesList = await api.getServices();
      update((state) => ({
        ...state,
        services: servicesList,
        isLoading: false,
        lastUpdated: new Date(),
        // Update cache
        cache: new Map(servicesList.map((s) => [s.id, { service: s, timestamp: Date.now() }])),
      }));
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to load services';

      update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage,
      }));

      if (!silent) {
        notifications.error('Load Failed', errorMessage);
      }
    }
  },

  // Get single service with caching
  getService: async (id: string, useCache: boolean = true) => {
    // Check cache first if enabled
    if (useCache) {
      const state = get(servicesStore);
      const cached = state.cache.get(id);
      if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        update((state) => ({
          ...state,
          selectedService: cached.service,
        }));
        return cached.service;
      }
    }

    update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const service = await api.getService(id);
      update((state) => {
        // Update cache
        const newCache = new Map(state.cache);
        newCache.set(id, { service, timestamp: Date.now() });

        return {
          ...state,
          selectedService: service,
          isLoading: false,
          // Update in services list if it exists
          services: state.services.map((s) => (s.id === id ? service : s)),
          cache: newCache,
        };
      });
      return service;
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to load service';

      update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage,
      }));

      notifications.error('Service Load Failed', errorMessage);
      throw error;
    }
  },

  // Create new service
  create: async (serviceData: CreateServiceRequest) => {
    update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const newService = await api.createService(serviceData);
      update((state) => {
        // Update cache
        const newCache = new Map(state.cache);
        newCache.set(newService.id, { service: newService, timestamp: Date.now() });

        return {
          ...state,
          services: [...state.services, newService],
          isLoading: false,
          cache: newCache,
        };
      });

      serviceNotifications.created(newService.name);
      return newService;
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to create service';

      update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage,
      }));

      notifications.error('Service Creation Failed', errorMessage);
      throw error;
    }
  },

  // Update existing service
  updateService: async (serviceData: UpdateServiceRequest) => {
    update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const updatedService = await api.updateService(serviceData);
      update((state) => {
        // Update cache
        const newCache = new Map(state.cache);
        newCache.set(updatedService.id, { service: updatedService, timestamp: Date.now() });

        return {
          ...state,
          services: state.services.map((s) => (s.id === serviceData.id ? updatedService : s)),
          selectedService:
            state.selectedService?.id === serviceData.id ? updatedService : state.selectedService,
          isLoading: false,
          cache: newCache,
        };
      });

      notifications.success(
        'Service Updated',
        `${updatedService.name} has been updated successfully`
      );
      return updatedService;
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to update service';

      update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage,
      }));

      notifications.error('Service Update Failed', errorMessage);
      throw error;
    }
  },

  // Delete service
  delete: async (id: string) => {
    const state = get(servicesStore);
    const service = state.services.find((s) => s.id === id);
    const serviceName = service?.name || id;

    update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      await api.deleteService(id);
      update((state) => {
        // Remove from cache
        const newCache = new Map(state.cache);
        newCache.delete(id);

        return {
          ...state,
          services: state.services.filter((s) => s.id !== id),
          selectedService: state.selectedService?.id === id ? null : state.selectedService,
          isLoading: false,
          cache: newCache,
        };
      });

      serviceNotifications.deleted(serviceName);
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to delete service';

      update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage,
      }));

      serviceNotifications.error(serviceName, errorMessage);
      throw error;
    }
  },

  // Start service with optimistic updates
  start: async (id: string) => {
    const state = get(servicesStore);
    const service = state.services.find((s) => s.id === id);
    const serviceName = service?.name || id;

    // Optimistic update
    update((state) => ({
      ...state,
      services: state.services.map((s) =>
        s.id === id ? { ...s, status: 'starting' as const } : s
      ),
    }));

    try {
      await api.startService(id);
      serviceNotifications.started(serviceName);

      // Refresh service details after a short delay
      setTimeout(() => services.getService(id, false), 2000);
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to start service';

      // Revert optimistic update
      services.getService(id, false);

      update((state) => ({
        ...state,
        error: errorMessage,
      }));

      serviceNotifications.error(serviceName, errorMessage);
      throw error;
    }
  },

  // Stop service with optimistic updates
  stop: async (id: string) => {
    const state = get(servicesStore);
    const service = state.services.find((s) => s.id === id);
    const serviceName = service?.name || id;

    // Optimistic update
    update((state) => ({
      ...state,
      services: state.services.map((s) =>
        s.id === id ? { ...s, status: 'stopping' as const } : s
      ),
    }));

    try {
      await api.stopService(id);
      serviceNotifications.stopped(serviceName);

      // Refresh service details after a short delay
      setTimeout(() => services.getService(id, false), 2000);
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to stop service';

      // Revert optimistic update
      services.getService(id, false);

      update((state) => ({
        ...state,
        error: errorMessage,
      }));

      serviceNotifications.error(serviceName, errorMessage);
      throw error;
    }
  },

  // Restart service with optimistic updates
  restart: async (id: string) => {
    const state = get(servicesStore);
    const service = state.services.find((s) => s.id === id);
    const serviceName = service?.name || id;

    // Optimistic update
    update((state) => ({
      ...state,
      services: state.services.map((s) =>
        s.id === id ? { ...s, status: 'starting' as const } : s
      ),
    }));

    try {
      await api.restartService(id);
      serviceNotifications.restarted(serviceName);

      // Refresh service details after a short delay
      setTimeout(() => services.getService(id, false), 3000);
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to restart service';

      // Revert optimistic update
      services.getService(id, false);

      update((state) => ({
        ...state,
        error: errorMessage,
      }));

      serviceNotifications.error(serviceName, errorMessage);
      throw error;
    }
  },

  // Get service logs
  getLogs: async (id: string, lines: number = 100) => {
    try {
      return await api.getServiceLogs(id, lines);
    } catch (error) {
      const apiError = error as ApiError;
      const errorMessage = apiError.message || 'Failed to load service logs';

      notifications.error('Logs Load Failed', errorMessage);
      throw error;
    }
  },

  // Select service
  select: (service: Service | null) => {
    update((state) => ({ ...state, selectedService: service }));
  },

  // Clear error
  clearError: () => {
    update((state) => ({ ...state, error: null }));
  },

  // Refresh services (reload from server)
  refresh: async () => {
    await services.load();
  },

  // Force refresh (bypass cache)
  forceRefresh: async () => {
    update((state) => ({ ...state, cache: new Map() }));
    await services.load();
  },

  // Update service from WebSocket
  updateFromWebSocket: (serviceUpdate: {
    id: string;
    status: Service['status'];
    health_status?: Service['health_status'];
  }) => {
    update((state) => {
      const updatedServices = state.services.map((s) => {
        if (s.id === serviceUpdate.id) {
          return {
            ...s,
            status: serviceUpdate.status,
            health_status: serviceUpdate.health_status || s.health_status,
          };
        }
        return s;
      });

      // Update cache if service exists
      const newCache = new Map(state.cache);
      const cached = newCache.get(serviceUpdate.id);
      if (cached) {
        newCache.set(serviceUpdate.id, {
          service: {
            ...cached.service,
            status: serviceUpdate.status,
            health_status: serviceUpdate.health_status || cached.service.health_status,
          },
          timestamp: Date.now(),
        });
      }

      return {
        ...state,
        services: updatedServices,
        selectedService:
          state.selectedService?.id === serviceUpdate.id
            ? {
                ...state.selectedService,
                status: serviceUpdate.status,
                health_status: serviceUpdate.health_status || state.selectedService.health_status,
              }
            : state.selectedService,
        cache: newCache,
      };
    });
  },

  // Update service status (alias for updateFromWebSocket for convenience)
  updateServiceStatus: (
    serviceId: string,
    status: Service['status'],
    healthStatus?: Service['health_status']
  ) => {
    services.updateFromWebSocket({ id: serviceId, status, health_status: healthStatus });
  },

  // Cleanup (stop auto-refresh)
  cleanup: () => {
    services.stopAutoRefresh();
  },
};
