/**
 * API Configuration
 * Centralized API endpoint configuration
 */
import { config } from './environment.js';

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
    // Authentication
    AUTH: {
        LOGIN: '/api/v1/auth/token',
        LOGOUT: '/api/v1/auth/logout',
        REFRESH: '/api/v1/auth/refresh',
        ME: '/api/v1/auth/me',
        REGISTER: '/api/v1/auth/register',
    },

    // User Management
    USERS: {
        BASE: '/api/v1/admin/users',
        BY_ID: (id: number) => `/api/v1/admin/users/${id}`,
        CREATE: '/api/v1/admin/users',
        UPDATE: (id: number) => `/api/v1/admin/users/${id}`,
        DELETE: (id: number) => `/api/v1/admin/users/${id}`,
    },

    // Services
    SERVICES: {
        BASE: '/api/v1/services',
        BY_ID: (id: string) => `/api/v1/services/${id}`,
        CREATE: '/api/v1/services',
        UPDATE: (id: string) => `/api/v1/services/${id}`,
        DELETE: (id: string) => `/api/v1/services/${id}`,
        START: (id: string) => `/api/v1/services/${id}/start`,
        STOP: (id: string) => `/api/v1/services/${id}/stop`,
        RESTART: (id: string) => `/api/v1/services/${id}/restart`,
        LOGS: (id: string, lines: number = 100) => `/api/v1/services/${id}/logs?lines=${lines}`,
        STATS: (id: string) => `/api/v1/services/${id}/stats`,
    },

    // System
    SYSTEM: {
        OVERVIEW: '/api/v1/system/overview',
        HEALTH: '/api/v1/health',
        STATS: '/api/v1/system/stats',
        LOGS: '/api/v1/system/logs',
    },

    // Analytics
    ANALYTICS: {
        OVERVIEW: '/api/v1/analytics/overview',
        SERVICES: '/api/v1/analytics/services',
        SYSTEM: '/api/v1/analytics/system',
        EVENTS: '/api/v1/analytics/events',
    },

    // Security
    SECURITY: {
        OVERVIEW: '/api/v1/security/overview',
        LOGS: '/api/v1/security/logs',
        ALERTS: '/api/v1/security/alerts',
        SETTINGS: '/api/v1/security/settings',
    },

    // Settings
    SETTINGS: {
        BASE: '/api/v1/settings',
        BY_KEY: (key: string) => `/api/v1/settings/${key}`,
        UPDATE: '/api/v1/settings',
    },

    // Monitoring
    MONITORING: {
        METRICS: '/api/v1/monitoring/metrics',
        ALERTS: '/api/v1/monitoring/alerts',
        HEALTH_CHECKS: '/api/v1/monitoring/health-checks',
    },
} as const;

/**
 * WebSocket Endpoints
 */
export const WS_ENDPOINTS = {
    SERVICES: '/ws/services',
    SYSTEM: '/ws/system',
    LOGS: '/ws/logs',
    NOTIFICATIONS: '/ws/notifications',
} as const;

/**
 * HTTP Methods
 */
export const HTTP_METHODS = {
    GET: 'GET',
    POST: 'POST',
    PUT: 'PUT',
    PATCH: 'PATCH',
    DELETE: 'DELETE',
} as const;

/**
 * Request timeout configurations
 */
export const TIMEOUTS = {
    DEFAULT: config.apiTimeout,
    QUICK: 5000,     // 5 seconds
    MEDIUM: 15000,   // 15 seconds
    LONG: 60000,     // 1 minute
    UPLOAD: 300000,  // 5 minutes
} as const;

/**
 * API Response Status Codes
 */
export const STATUS_CODES = {
    OK: 200,
    CREATED: 201,
    NO_CONTENT: 204,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    CONFLICT: 409,
    UNPROCESSABLE_ENTITY: 422,
    INTERNAL_SERVER_ERROR: 500,
    SERVICE_UNAVAILABLE: 503,
} as const;

/**
 * API Error Codes
 */
export const ERROR_CODES = {
    NETWORK_ERROR: 'NETWORK_ERROR',
    TIMEOUT: 'TIMEOUT',
    UNAUTHORIZED: 'UNAUTHORIZED',
    FORBIDDEN: 'FORBIDDEN',
    NOT_FOUND: 'NOT_FOUND',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    CONFLICT: 'CONFLICT',
    INTERNAL_ERROR: 'INTERNAL_ERROR',
    SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
} as const;

/**
 * Default headers for API requests
 */
export const DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
} as const;

/**
 * Pagination defaults
 */
export const PAGINATION = {
    DEFAULT_PAGE: 1,
    DEFAULT_LIMIT: 20,
    MAX_LIMIT: 100,
} as const;

/**
 * Get full API URL
 */
export function getApiUrl(endpoint: string): string {
    const baseUrl = config.apiUrl.replace(/\/$/, '');
    const cleanEndpoint = endpoint.replace(/^\//, '');
    return `${baseUrl}/${cleanEndpoint}`;
}

/**
 * Get WebSocket URL
 */
export function getWsUrl(endpoint: string): string {
    const baseUrl = config.wsUrl.replace(/\/$/, '');
    const cleanEndpoint = endpoint.replace(/^\//, '');
    return `${baseUrl}/${cleanEndpoint}`;
}

/**
 * Build query string from parameters
 */
export function buildQueryString(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            searchParams.append(key, String(value));
        }
    });

    const queryString = searchParams.toString();
    return queryString ? `?${queryString}` : '';
}

/**
 * API request configuration factory
 */
export function createRequestConfig(
    method: string = HTTP_METHODS.GET,
    body?: any,
    headers?: Record<string, string>,
    timeout?: number
): RequestInit {
    const config: RequestInit = {
        method,
        headers: {
            ...DEFAULT_HEADERS,
            ...headers,
        },
    };

    if (body && method !== HTTP_METHODS.GET) {
        config.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    // Note: fetch doesn't have a built-in timeout, 
    // but we can use AbortController for this in the API client

    return config;
}
