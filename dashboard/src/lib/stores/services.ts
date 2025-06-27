/**
 * Services Store
 * Manages Docker services state
 */
import { writable, derived } from 'svelte/store';
import { api, type Service, type CreateServiceRequest, type UpdateServiceRequest, type ApiError } from '../api.js';

interface ServicesState {
    services: Service[];
    selectedService: Service | null;
    isLoading: boolean;
    error: string | null;
    lastUpdated: Date | null;
}

const initialState: ServicesState = {
    services: [],
    selectedService: null,
    isLoading: false,
    error: null,
    lastUpdated: null,
};

// Create the writable store
const { subscribe, set, update } = writable<ServicesState>(initialState);

// Derived stores
export const runningServices = derived(
    { subscribe },
    ($services) => $services.services.filter(s => s.status === 'running')
);

export const stoppedServices = derived(
    { subscribe },
    ($services) => $services.services.filter(s => s.status === 'stopped')
);

export const errorServices = derived(
    { subscribe },
    ($services) => $services.services.filter(s => s.status === 'error')
);

export const serviceStats = derived(
    { subscribe },
    ($services) => ({
        total: $services.services.length,
        running: $services.services.filter(s => s.status === 'running').length,
        stopped: $services.services.filter(s => s.status === 'stopped').length,
        error: $services.services.filter(s => s.status === 'error').length,
    })
);

// Services store with methods
export const services = {
    subscribe,

    // Load all services
    load: async () => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            const servicesList = await api.getServices();
            update(state => ({
                ...state,
                services: servicesList,
                isLoading: false,
                lastUpdated: new Date(),
            }));
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                isLoading: false,
                error: apiError.message || 'Failed to load services',
            }));
        }
    },

    // Get single service
    getService: async (id: string) => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            const service = await api.getService(id);
            update(state => ({
                ...state,
                selectedService: service,
                isLoading: false,
                // Update in services list if it exists
                services: state.services.map(s => s.id === id ? service : s),
            }));
            return service;
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                isLoading: false,
                error: apiError.message || 'Failed to load service',
            }));
            throw error;
        }
    },

    // Create new service
    create: async (serviceData: CreateServiceRequest) => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            const newService = await api.createService(serviceData);
            update(state => ({
                ...state,
                services: [...state.services, newService],
                isLoading: false,
            }));
            return newService;
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                isLoading: false,
                error: apiError.message || 'Failed to create service',
            }));
            throw error;
        }
    },

    // Update existing service
    update: async (serviceData: UpdateServiceRequest) => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            const updatedService = await api.updateService(serviceData);
            update(state => ({
                ...state,
                services: state.services.map(s => s.id === serviceData.id ? updatedService : s),
                selectedService: state.selectedService?.id === serviceData.id ? updatedService : state.selectedService,
                isLoading: false,
            }));
            return updatedService;
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                isLoading: false,
                error: apiError.message || 'Failed to update service',
            }));
            throw error;
        }
    },

    // Delete service
    delete: async (id: string) => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            await api.deleteService(id);
            update(state => ({
                ...state,
                services: state.services.filter(s => s.id !== id),
                selectedService: state.selectedService?.id === id ? null : state.selectedService,
                isLoading: false,
            }));
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                isLoading: false,
                error: apiError.message || 'Failed to delete service',
            }));
            throw error;
        }
    },

    // Start service
    start: async (id: string) => {
        try {
            await api.startService(id);
            // Update service status optimistically
            update(state => ({
                ...state,
                services: state.services.map(s =>
                    s.id === id ? { ...s, status: 'starting' as const } : s
                ),
            }));

            // Refresh service details after a short delay
            setTimeout(() => services.getService(id), 2000);
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                error: apiError.message || 'Failed to start service',
            }));
            throw error;
        }
    },

    // Stop service
    stop: async (id: string) => {
        try {
            await api.stopService(id);
            // Update service status optimistically
            update(state => ({
                ...state,
                services: state.services.map(s =>
                    s.id === id ? { ...s, status: 'stopping' as const } : s
                ),
            }));

            // Refresh service details after a short delay
            setTimeout(() => services.getService(id), 2000);
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                error: apiError.message || 'Failed to stop service',
            }));
            throw error;
        }
    },

    // Restart service
    restart: async (id: string) => {
        try {
            await api.restartService(id);
            // Update service status optimistically
            update(state => ({
                ...state,
                services: state.services.map(s =>
                    s.id === id ? { ...s, status: 'starting' as const } : s
                ),
            }));

            // Refresh service details after a short delay
            setTimeout(() => services.getService(id), 3000);
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                error: apiError.message || 'Failed to restart service',
            }));
            throw error;
        }
    },

    // Select service
    select: (service: Service | null) => {
        update(state => ({ ...state, selectedService: service }));
    },

    // Clear error
    clearError: () => {
        update(state => ({ ...state, error: null }));
    },

    // Refresh services (reload from server)
    refresh: async () => {
        await services.load();
    },
};
