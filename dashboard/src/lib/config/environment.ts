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
  // API Configuration - use relative URLs in production, absolute in development
  apiUrl: typeof window !== 'undefined' && window.location.port === '3001'
    ? 'http://195.201.199.226:8000'  // Development: direct to backend base URL
    : '',  // Production: use relative URLs (handled by proxy)
  apiTimeout: 30000, // 30 seconds

  // Authentication
  tokenKey: 'wakedock_token',
  sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours

  // WebSocket - adapt based on environment
  wsUrl: typeof window !== 'undefined' && window.location.port === '3001'
    ? 'ws://195.201.199.226:8000'  // Development: direct to backend base
    : '',  // Production: relative WebSocket through proxy
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
      const response = await fetch('/api/config');
      if (response.ok) {
        const runtimeConfig = await response.json();
        return {
          ...defaultConfig,
          apiUrl: runtimeConfig.apiUrl,
          wsUrl: runtimeConfig.wsUrl,
          isDevelopment: runtimeConfig.isDevelopment,
          enableDebug: runtimeConfig.enableDebug,
        };
      }
    } catch (error) {
      console.debug('Runtime config not available, using build-time config:', error);
    }
  }
  return null;
}

/**
 * Load configuration from environment variables
 */
function loadConfig(): EnvironmentConfig {
  return {
    // API Configuration
    apiUrl: getEnvVar('PUBLIC_API_URL', defaultConfig.apiUrl),
    apiTimeout: getNumberEnvVar('PUBLIC_API_TIMEOUT', defaultConfig.apiTimeout),

    // Authentication
    tokenKey: getEnvVar('PUBLIC_TOKEN_KEY', defaultConfig.tokenKey),
    sessionTimeout: getNumberEnvVar('PUBLIC_SESSION_TIMEOUT', defaultConfig.sessionTimeout),

    // WebSocket
    wsUrl: getEnvVar('PUBLIC_WS_URL', defaultConfig.wsUrl),
    wsReconnectInterval: getNumberEnvVar(
      'PUBLIC_WS_RECONNECT_INTERVAL',
      defaultConfig.wsReconnectInterval
    ),
    wsMaxReconnectAttempts: getNumberEnvVar(
      'PUBLIC_WS_MAX_RECONNECT_ATTEMPTS',
      defaultConfig.wsMaxReconnectAttempts
    ),

    // UI Configuration
    theme: (getEnvVar('PUBLIC_THEME', defaultConfig.theme) as any) || defaultConfig.theme,
    refreshInterval: getNumberEnvVar('PUBLIC_REFRESH_INTERVAL', defaultConfig.refreshInterval),

    // Development
    isDevelopment:
      getBooleanEnvVar('NODE_ENV') !== false
        ? getEnvVar('NODE_ENV', 'development') === 'development'
        : defaultConfig.isDevelopment,
    enableDebug: getBooleanEnvVar('PUBLIC_ENABLE_DEBUG', defaultConfig.enableDebug),

    // Feature Flags
    features: {
      analytics: getBooleanEnvVar('PUBLIC_FEATURE_ANALYTICS', defaultConfig.features.analytics),
      notifications: getBooleanEnvVar(
        'PUBLIC_FEATURE_NOTIFICATIONS',
        defaultConfig.features.notifications
      ),
      realTimeUpdates: getBooleanEnvVar(
        'PUBLIC_FEATURE_REALTIME',
        defaultConfig.features.realTimeUpdates
      ),
    },
  };
}

// Export the configuration
export let config = loadConfig();

/**
 * Update configuration at runtime
 */
export async function updateConfigFromRuntime(): Promise<void> {
  const runtimeConfig = await loadRuntimeConfig();
  if (runtimeConfig) {
    config = runtimeConfig;
    console.log('Configuration updated from runtime:', config);
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
