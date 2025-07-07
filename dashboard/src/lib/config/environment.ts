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
  // API Configuration - use relative URLs for internal routing
  apiUrl: '/api/v1',  // Always use relative URL for internal routing
  apiTimeout: 30000, // 30 seconds

  // Authentication
  tokenKey: 'wakedock_token',
  sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours

  // WebSocket - use relative URLs for internal routing
  wsUrl: '/ws',  // Always use relative WebSocket URL for internal routing
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
      const response = await fetch('/api/config');
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
  // Force relative URLs - ignore build-time environment variables
  return {
    ...defaultConfig,
    // Force relative URLs for internal routing
    apiUrl: defaultConfig.apiUrl,
    wsUrl: defaultConfig.wsUrl,

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
