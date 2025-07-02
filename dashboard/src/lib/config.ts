/**
 * Server Configuration
 * Centralized configuration for the WakeDock dashboard
 */

interface ServerConfig {
  api: {
    baseUrl: string;
    timeout: number;
    retryAttempts: number;
  };
  websocket: {
    url: string;
    reconnectAttempts: number;
    reconnectInterval: number;
  };
  security: {
    csrfEnabled: boolean;
    sessionTimeout: number;
    maxLoginAttempts: number;
  };
  features: {
    enableMetrics: boolean;
    enableNotifications: boolean;
    enableAuditLog: boolean;
  };
}

const defaultConfig: ServerConfig = {
  api: {
    baseUrl: '/api',
    timeout: 30000,
    retryAttempts: 3,
  },
  websocket: {
    url: '/ws',
    reconnectAttempts: 5,
    reconnectInterval: 3000,
  },
  security: {
    csrfEnabled: true,
    sessionTimeout: 3600,
    maxLoginAttempts: 5,
  },
  features: {
    enableMetrics: true,
    enableNotifications: true,
    enableAuditLog: true,
  },
};

// Load config from environment or use defaults
export const serverConfig: ServerConfig = {
  ...defaultConfig,
  // Override with environment variables if available
  ...(typeof window !== 'undefined' && (window as any).__SERVER_CONFIG__
    ? (window as any).__SERVER_CONFIG__
    : {}),
};

export default serverConfig;
