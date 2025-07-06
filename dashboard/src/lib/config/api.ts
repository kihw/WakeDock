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
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    REGISTER: '/auth/register',
  },

  // User Management
  USERS: {
    BASE: '/admin/users',
    BY_ID: (id: number) => `/admin/users/${id}`,
    CREATE: '/admin/users',
    UPDATE: (id: number) => `/admin/users/${id}`,
    DELETE: (id: number) => `/admin/users/${id}`,
  },

  // Services
  SERVICES: {
    BASE: '/services',
    BY_ID: (id: string) => `/services/${id}`,
    CREATE: '/services',
    UPDATE: (id: string) => `/services/${id}`,
    DELETE: (id: string) => `/services/${id}`,
    START: (id: string) => `/services/${id}/start`,
    STOP: (id: string) => `/services/${id}/stop`,
    RESTART: (id: string) => `/services/${id}/restart`,
    LOGS: (id: string, lines: number = 100) => `/services/${id}/logs?lines=${lines}`,
    STATS: (id: string) => `/services/${id}/stats`,
  },

  // System
  SYSTEM: {
    OVERVIEW: '/system/overview',
    HEALTH: '/health',
    STATS: '/system/stats',
    LOGS: '/system/logs',
  },

  // Analytics
  ANALYTICS: {
    OVERVIEW: '/analytics/overview',
    SERVICES: '/analytics/services',
    SYSTEM: '/analytics/system',
    EVENTS: '/analytics/events',
  },

  // Security
  SECURITY: {
    OVERVIEW: '/security/overview',
    LOGS: '/security/logs',
    ALERTS: '/security/alerts',
    SETTINGS: '/security/settings',
  },

  // Settings
  SETTINGS: {
    BASE: '/settings',
    BY_KEY: (key: string) => `/settings/${key}`,
    UPDATE: '/settings',
  },

  // Monitoring
  MONITORING: {
    METRICS: '/monitoring/metrics',
    ALERTS: '/monitoring/alerts',
    HEALTH_CHECKS: '/monitoring/health-checks',
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
  QUICK: 5000, // 5 seconds
  MEDIUM: 15000, // 15 seconds
  LONG: 60000, // 1 minute
  UPLOAD: 300000, // 5 minutes
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
  Accept: 'application/json',
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
