/**
 * API Module Exports
 * Main entry point for the refactored API client
 */

// Export main client
export { ApiClient } from './api-client.js';

// Export individual services for advanced usage
export { BaseApiClient } from './base-client.js';
export { AuthService } from './auth-service.js';
export { ServicesApi } from './services-api.js';
export { SystemApi } from './system-api.js';
export { UsersApi } from './users-api.js';

// Export types
export type { RequestOptions } from './base-client.js';

// Create and export singleton instance
import { ApiClient } from './api-client.js';
export const api = new ApiClient();

// Re-export types for backward compatibility
export type { 
  ApiError,
  User,
  LoginRequest,
  LoginResponse,
  CreateUserRequest,
  UpdateUserRequest,
  DockerService,
  CreateServiceRequest,
  UpdateServiceRequest,
  SystemInfo,
  SystemStats
} from '../types/api.js';

// Re-export interfaces for backward compatibility (from old api.ts)
export interface Service {
  id: string;
  name: string;
  subdomain: string;
  image: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  ports: Array<{
    host: number;
    container: number;
    protocol: 'tcp' | 'udp';
  }>;
  environment: Record<string, string>;
  volumes: Array<{
    host: string;
    container: string;
    mode: 'rw' | 'ro';
  }>;
  created_at: string;
  updated_at: string;
  health_status?: 'healthy' | 'unhealthy' | 'unknown';
  restart_policy: 'no' | 'always' | 'on-failure' | 'unless-stopped';
  labels: Record<string, string>;
  last_accessed?: string;
  resource_usage?: {
    cpu_usage: number;
    memory_usage: number;
    network_io: { rx: number; tx: number };
  };
}

export interface SystemOverview {
  services: {
    total: number;
    running: number;
    stopped: number;
    error: number;
  };
  system: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    uptime: number;
  };
  docker: {
    version: string;
    api_version: string;
    status: 'healthy' | 'unhealthy';
  };
  caddy: {
    version: string;
    status: 'healthy' | 'unhealthy';
    active_routes: number;
  };
}