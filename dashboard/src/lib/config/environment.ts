/**
 * Environment Configuration
 * Handles environment variables and application configuration
 */
import { browser } from '$app/environment';

export interface EnvironmentConfig {
  // API Configuration
  apiUrl: string;
  apiTimeout: number;

  // Authentication
  tokenKey: string;
  sessionTimeout: number;

  // WebSocket
  wsUrl: string;
  wsReconnectInterval: number;
  wsMaxReconnectAttempts: number;

  // UI Configuration
  theme: 'light' | 'dark' | 'auto';
  refreshInterval: number;

  // Development
  isDevelopment: boolean;
  enableDebug: boolean;

  // Feature Flags
  features: {
    analytics: boolean;
    notifications: boolean;
    realTimeUpdates: boolean;
  };
}

// Default configuration
const defaultConfig: EnvironmentConfig = {
  // API Configuration - use relative URLs for reverse proxy
  apiUrl: '/api/v1',  // Use relative URL for reverse proxy
  apiTimeout: 30000, // 30 seconds

  // Authentication
  tokenKey: 'wakedock_token',
  sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours

  // WebSocket - use relative URLs for reverse proxy
  wsUrl: '/ws',  // Use relative URL for reverse proxy
  wsReconnectInterval: 5000, // 5 seconds
  wsMaxReconnectAttempts: 10,

  // UI Configuration
  theme: 'auto',
  refreshInterval: 30000, // 30 seconds

  // Development
  isDevelopment: true,
  enableDebug: true,

  // Feature Flags
  features: {
    analytics: true,
    notifications: true,
    realTimeUpdates: true,
  },
};

/**
 * Get environment variable with fallback
 */
function getEnvVar(key: string, fallback: string = ''): string {
  if (browser) {
    // Client-side: use window.env or fallback
    return (window as any)?.env?.[key] || fallback;
  }
  // Server-side: use process.env
  return process.env[key] || fallback;
}

/**
 * Get boolean environment variable
 */
function getBooleanEnvVar(key: string, fallback: boolean = false): boolean {
  const value = getEnvVar(key).toLowerCase();
  return value === 'true' || value === '1' || value === 'yes';
}

/**
 * Get number environment variable
 */
function getNumberEnvVar(key: string, fallback: number = 0): number {
  const value = getEnvVar(key);
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? fallback : parsed;
}

/**
 * Load configuration from runtime API if available, fallback to environment variables
 */
async function loadRuntimeConfig(): Promise<EnvironmentConfig | null> {
  if (browser) {
    try {
      console.log('🔄 Fetching runtime configuration from /api/config...');
      // Use native fetch directly to avoid circular dependency with API client
      const response = await fetch('/api/config', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin', // Include cookies if needed
        cache: 'no-cache' // Always get fresh config
      });
      
      if (response.ok) {
        const runtimeConfig = await response.json();
        console.log('✅ Runtime config received:', runtimeConfig);
        return {
          ...defaultConfig,
          apiUrl: runtimeConfig.apiUrl || defaultConfig.apiUrl,
          wsUrl: runtimeConfig.wsUrl || defaultConfig.wsUrl,
          isDevelopment: runtimeConfig.isDevelopment ?? defaultConfig.isDevelopment,
          enableDebug: runtimeConfig.enableDebug ?? defaultConfig.enableDebug,
        };
      } else {
        console.warn('⚠️ Runtime config endpoint returned:', response.status, response.statusText);
      }
    } catch (error) {
      console.warn('⚠️ Runtime config not available, using defaults:', error);
    }
  }
  return null;
}

/**
 * Load configuration from environment variables (DEPRECATED - use loadRuntimeConfig instead)
 */
function loadConfig(): EnvironmentConfig {
  // Use relative URLs for reverse proxy setup
  return {
    ...defaultConfig,
    // Use relative URLs for internal routing
    apiUrl: '/api/v1',
    wsUrl: '/ws',

    // Keep non-URL configuration from environment
    isDevelopment: getBooleanEnvVar('NODE_ENV') !== false
      ? getEnvVar('NODE_ENV', 'development') === 'development'
      : defaultConfig.isDevelopment,
    enableDebug: getBooleanEnvVar('PUBLIC_ENABLE_DEBUG', defaultConfig.enableDebug),
  };
}

// Initialize with default config that always uses relative URLs
export let config = defaultConfig;

/**
 * Update configuration at runtime
 */
export async function updateConfigFromRuntime(): Promise<void> {
  console.log('🔄 Updating configuration from runtime...');
  const runtimeConfig = await loadRuntimeConfig();
  if (runtimeConfig) {
    config = runtimeConfig;
    console.log('✅ Configuration updated from runtime:', {
      apiUrl: config.apiUrl,
      wsUrl: config.wsUrl,
      isDevelopment: config.isDevelopment
    });
  } else {
    console.log('⚠️ Runtime config not available, using defaults:', {
      apiUrl: config.apiUrl,
      wsUrl: config.wsUrl,
      isDevelopment: config.isDevelopment
    });
  }
}

// Debug function to log current configuration
export function debugConfig(): void {
  console.log('WakeDock Configuration:', {
    apiUrl: config.apiUrl,
    wsUrl: config.wsUrl,
    isDevelopment: config.isDevelopment,
    environment: {
      NODE_ENV: getEnvVar('NODE_ENV'),
      PUBLIC_API_URL: getEnvVar('PUBLIC_API_URL'),
      PUBLIC_WS_URL: getEnvVar('PUBLIC_WS_URL'),
    }
  });
}

// Environment-specific utilities
export const isDevelopment = config.isDevelopment;
export const isProduction = !config.isDevelopment;

/**
 * Debug logger (only works in development)
 */
export function debugLog(...args: any[]): void {
  if (config.isDevelopment && config.enableDebug) {
    console.log('[WakeDock Debug]', ...args);
  }
}

/**
 * Get API URL with path
 */
export function getApiUrl(path: string = ''): string {
  const url = config.apiUrl.replace(/\/$/, '');
  const cleanPath = path.replace(/^\//, '');
  return cleanPath ? `${url}/${cleanPath}` : url;
}

/**
 * Get WebSocket URL
 */
export function getWsUrl(path: string = ''): string {
  const url = config.wsUrl.replace(/\/$/, '');
  const cleanPath = path.replace(/^\//, '');
  return cleanPath ? `${url}/${cleanPath}` : url;
}
