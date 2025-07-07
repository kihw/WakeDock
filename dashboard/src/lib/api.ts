/**
 * WakeDock API Client
 * Typed API client with error handling and authentication
 */

import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  LoginRequest,
  LoginResponse,
} from './types/user';
import { config, updateConfigFromRuntime } from './config/environment.js';
import { API_ENDPOINTS, getApiUrl } from './config/api.js';
import { csrf, rateLimit, securityValidate } from './utils/validation.js';
import { memoryUtils } from './utils/storage.js';
import { apiMonitor } from './monitoring/api-monitor.js';

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export interface Service {
  id: string;
  name: string;
  subdomain: string; // Add missing subdomain property
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

export interface CreateServiceRequest {
  name: string;
  image: string;
  ports?: Array<{
    host: number;
    container: number;
    protocol?: 'tcp' | 'udp';
  }>;
  environment?: Record<string, string>;
  volumes?: Array<{
    host: string;
    container: string;
    mode?: 'rw' | 'ro';
  }>;
  restart_policy?: 'no' | 'always' | 'on-failure' | 'unless-stopped';
  labels?: Record<string, string>;
}

export interface UpdateServiceRequest extends Partial<CreateServiceRequest> {
  id: string;
}

// Security headers utility
export const securityHeaders = {
  /**
   * Get default security headers for API requests
   */
  getDefaults(): Record<string, string> {
    return {
      'X-Frame-Options': 'DENY',
      'X-Content-Type-Options': 'nosniff',
      'X-XSS-Protection': '1; mode=block',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
      'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    };
  },

  /**
   * Validate response headers for security
   */
  validateResponse(headers: Headers): string[] {
    const warnings: string[] = [];

    if (!headers.get('X-Frame-Options') && !headers.get('x-frame-options')) {
      warnings.push('Missing X-Frame-Options header');
    }

    if (!headers.get('X-Content-Type-Options') && !headers.get('x-content-type-options')) {
      warnings.push('Missing X-Content-Type-Options header');
    }

    return warnings;
  },
};

// Enhanced request options for security
export interface SecureRequestOptions extends RequestInit {
  skipCSRF?: boolean;
  skipRateLimit?: boolean;
  timeout?: number;
  retries?: number;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;
  private maxRetries: number = 3;
  private retryDelay: number = 1000; // Base delay in ms
  private timeout: number = 30000; // 30 seconds - reasonable timeout
  private _initialized: boolean = false;

  // Optimized timeouts per endpoint
  private endpointTimeouts: Record<string, number> = {
    '/auth/login': 8000,      // 8s pour auth (optimisé)
    '/auth/register': 8000,   // 8s pour auth (optimisé)
    '/auth/refresh': 3000,    // 3s pour refresh (optimisé)
    '/services': 15000,       // 15s pour services (optimisé)
    '/services/create': 25000, // 25s pour création
    '/services/update': 20000, // 20s pour mise à jour (optimisé)
    '/services/logs': 10000,  // 10s pour logs (optimisé)
    '/system': 25000,         // 25s pour system (optimisé)
    '/system/overview': 12000, // 12s pour overview (optimisé)
    '/health': 3000,          // 3s pour health check (optimisé)
    default: 10000            // 10s par défaut (optimisé)
  };

  // Circuit breaker implementation
  private circuitBreaker = {
    failures: new Map<string, number>(),
    lastFailureTime: new Map<string, number>(),
    failureThreshold: 5,
    recoveryTimeout: 30000, // 30s recovery
    halfOpenTimeout: 10000, // 10s half-open

    isOpen: (endpoint: string): boolean => {
      const failures = this.circuitBreaker.failures.get(endpoint) || 0;
      const lastFailure = this.circuitBreaker.lastFailureTime.get(endpoint) || 0;
      const now = Date.now();

      // Circuit is open if we exceeded failure threshold and not enough time has passed
      if (failures >= this.circuitBreaker.failureThreshold) {
        return (now - lastFailure) < this.circuitBreaker.recoveryTimeout;
      }

      return false;
    },

    recordFailure: (endpoint: string): void => {
      const failures = (this.circuitBreaker.failures.get(endpoint) || 0) + 1;
      this.circuitBreaker.failures.set(endpoint, failures);
      this.circuitBreaker.lastFailureTime.set(endpoint, Date.now());
    },

    recordSuccess: (endpoint: string): void => {
      this.circuitBreaker.failures.set(endpoint, 0);
      this.circuitBreaker.lastFailureTime.delete(endpoint);
    }
  };

  // Network status detection
  private networkStatus = {
    isOnline: true,
    lastOnlineCheck: Date.now(),
    checkInterval: 5000, // Check every 5s when offline

    updateStatus: (): void => {
      const wasOnline = this.networkStatus.isOnline;
      this.networkStatus.isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;
      this.networkStatus.lastOnlineCheck = Date.now();

      if (!wasOnline && this.networkStatus.isOnline) {
        console.log('🌐 Network connection restored');
      } else if (wasOnline && !this.networkStatus.isOnline) {
        console.log('🔌 Network connection lost');
      }
    }
  };

  constructor(baseUrl: string = '') {
    // Initialize with default config (always relative URLs)
    this.baseUrl = baseUrl || config.apiUrl;
    this.baseUrl = this.baseUrl.replace(/\/$/, ''); // Remove trailing slash

    // Try to load token from localStorage
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem(config.tokenKey);

      // Set up network status monitoring
      window.addEventListener('online', this.networkStatus.updateStatus);
      window.addEventListener('offline', this.networkStatus.updateStatus);
      this.networkStatus.updateStatus();
    }

    console.log('🔧 ApiClient initialized with baseUrl:', this.baseUrl);
  }

  /**
   * Ensure the API client is properly initialized with runtime config
   */
  private async ensureInitialized(): Promise<void> {
    if (this._initialized) {
      return;
    }

    console.log('🚀 Initializing ApiClient with runtime configuration...');

    // Update configuration from runtime API if available
    await updateConfigFromRuntime();

    // Update baseUrl with new configuration
    const newBaseUrl = config.apiUrl.replace(/\/$/, '');
    if (newBaseUrl !== this.baseUrl) {
      console.log('🔄 Updating ApiClient baseUrl from', this.baseUrl, 'to', newBaseUrl);
      this.baseUrl = newBaseUrl;
    }

    this._initialized = true;
    console.log('✅ ApiClient initialized successfully with baseUrl:', this.baseUrl);
  }

  /**
   * Force re-initialization of the API client
   */
  public async reinitialize(): Promise<void> {
    this._initialized = false;
    await this.ensureInitialized();
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get timeout for specific endpoint
   */
  private getTimeout(endpoint: string): number {
    // Check for exact match first
    if (this.endpointTimeouts[endpoint]) {
      return this.endpointTimeouts[endpoint];
    }

    // Check for partial matches
    for (const [pattern, timeout] of Object.entries(this.endpointTimeouts)) {
      if (pattern !== 'default' && endpoint.startsWith(pattern)) {
        return timeout;
      }
    }

    return this.endpointTimeouts.default;
  }

  private shouldRetry(error: any, attempt: number, endpoint: string): boolean {
    if (attempt >= this.maxRetries) return false;

    // Don't retry if circuit breaker is open
    if (this.circuitBreaker.isOpen(endpoint)) {
      console.warn(`Circuit breaker open for ${endpoint}, skipping retry`);
      return false;
    }

    // Don't retry if offline
    if (!this.networkStatus.isOnline) {
      console.warn('Network offline, skipping retry');
      return false;
    }

    // Retry on network errors, timeouts, and 5xx server errors
    if (error.name === 'TypeError' || error.name === 'NetworkError') return true;
    if (error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT') return true;
    if (error.details?.status >= 500) return true;

    return false;
  }

  private createTimeoutController(timeoutMs: number): AbortController {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), timeoutMs);
    return controller;
  }

  private async request<T>(
    path: string,
    options: SecureRequestOptions = {},
    retryAttempt: number = 0
  ): Promise<T> {
    // Ensure API client is initialized before making requests
    await this.ensureInitialized();

    const url = `${this.baseUrl}${path}`;

    console.log('📡 Making API request:', {
      url,
      method: options.method || 'GET',
      baseUrl: this.baseUrl,
      path,
      initialized: this._initialized,
      credentials: this.token ? 'Bearer token present' : 'No token'
    });

    // Check circuit breaker
    if (this.circuitBreaker.isOpen(path)) {
      throw new Error(`Circuit breaker open for ${path} - too many recent failures`);
    }

    // Check network status
    if (!this.networkStatus.isOnline) {
      throw new Error('Network offline - check your connection');
    }

    // Rate limiting check
    if (!options.skipRateLimit) {
      const rateLimitKey = `api_${path}_${this.token ? 'auth' : 'anon'}`;
      if (rateLimit.isLimited(rateLimitKey)) {
        throw new Error('Rate limit exceeded. Please try again later.');
      }
    }

    const headers: Record<string, string> = {
      ...securityHeaders.getDefaults(),
    };

    // Merge existing headers if they exist first
    if (options.headers) {
      const existingHeaders = new Headers(options.headers);
      existingHeaders.forEach((value, key) => {
        headers[key] = value;
      });
    }

    // Only set Content-Type if not already set and not using FormData or URLSearchParams
    if (!headers['Content-Type'] && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
      headers['Content-Type'] = 'application/json';
    }

    // Add CSRF token for state-changing operations
    if (
      !options.skipCSRF &&
      ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase() || 'GET')
    ) {
      const csrfToken = csrf.getToken();
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    // Validate request origin (only in browser)
    if (typeof window !== 'undefined') {
      headers.Origin = window.location.origin;
      headers.Referer = window.location.href;
    }

    // Create timeout controller with endpoint-specific timeout
    const endpointTimeout = options.timeout || this.getTimeout(path);
    const timeoutController = this.createTimeoutController(endpointTimeout);
    const originalSignal = options.signal;

    // Combine timeout signal with any existing signal
    let combinedSignal = timeoutController.signal;
    if (originalSignal) {
      const combinedController = new AbortController();
      const abortBoth = () => combinedController.abort();

      timeoutController.signal.addEventListener('abort', abortBoth);
      originalSignal.addEventListener('abort', abortBoth);

      combinedSignal = combinedController.signal;
    }

    try {
      // DEBUG: Log request start only in development mode
      if (config.enableDebug || process.env.NODE_ENV === 'development') {
        console.log('🚀 API Request START:', {
          url,
          method: options.method || 'GET',
          timestamp: new Date().toISOString(),
          timeoutMs: endpointTimeout,
          headers: Object.keys(headers)
        });
      }

      const requestStart = Date.now();
      const response = await fetch(url, {
        ...options,
        headers,
        signal: combinedSignal,
      });

      const requestDuration = Date.now() - requestStart;
      if (config.enableDebug || process.env.NODE_ENV === 'development') {
        console.log('✅ API Response received:', {
          url,
          status: response.status,
          duration: requestDuration + 'ms',
          timestamp: new Date().toISOString()
        });
      }

      // Clear timeout since request completed
      if (!timeoutController.signal.aborted) {
        timeoutController.abort();
      }

      // Validate response headers for security
      const securityWarnings = securityHeaders.validateResponse(response.headers);
      if (securityWarnings.length > 0) {
        console.warn('Security warnings for response:', securityWarnings);
      }

      // Validate response origin if applicable (only in browser)
      if (typeof window !== 'undefined') {
        const responseOrigin = response.headers.get('Access-Control-Allow-Origin');
        if (responseOrigin && responseOrigin !== '*' && responseOrigin !== window.location.origin) {
          console.warn('Response origin mismatch:', responseOrigin);
        }
      }

      if (!response.ok) {
        let errorData: any = { message: 'An error occurred' };

        try {
          const responseText = await response.text();
          // Sanitize error response to prevent XSS
          const sanitizedText = responseText.replace(/<[^>]*>/g, '').substring(0, 1000);
          errorData = JSON.parse(sanitizedText);
        } catch {
          errorData = { message: response.statusText };
        }

        const error: ApiError = {
          message: errorData.detail || errorData.message || response.statusText,
          code: errorData.code,
          details: { ...errorData, status: response.status },
        };

        // Throw error to potentially trigger retry
        throw error;
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const responseData = await response.json();

        // Basic response validation
        if (typeof responseData === 'object' && responseData !== null) {
          // Remove any potentially dangerous properties
          delete responseData.__proto__;
          delete responseData.constructor;
        }

        // Record success in circuit breaker
        this.circuitBreaker.recordSuccess(path);

        // Record success in monitoring
        const requestDuration = Date.now() - requestStart;
        apiMonitor.recordSuccess(path, requestDuration);

        return responseData;
      } else {
        // Record success in circuit breaker
        this.circuitBreaker.recordSuccess(path);

        // Record success in monitoring
        const requestDuration = Date.now() - requestStart;
        apiMonitor.recordSuccess(path, requestDuration);

        return {} as T;
      }
    } catch (error: any) {
      // Record failure in circuit breaker
      this.circuitBreaker.recordFailure(path);

      // Record error in monitoring
      apiMonitor.recordError(path, error);

      // Add detailed error logging
      console.error('API request failed:', {
        url,
        error: error,
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack,
        timeout: endpointTimeout,
        retryAttempt,
        circuitBreakerFailures: this.circuitBreaker.failures.get(path) || 0
      });

      // Handle timeout specifically
      if (error.name === 'AbortError') {
        console.error('⏰ TIMEOUT DETECTED:', {
          url,
          timeoutMs: endpointTimeout,
          timestamp: new Date().toISOString(),
          errorName: error.name
        });
        const timeoutError: ApiError = {
          message: `Request timeout after ${endpointTimeout}ms`,
          code: 'TIMEOUT',
          details: { url, timeout: endpointTimeout },
        };
        error = timeoutError;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError: ApiError = {
          message: 'Network error - please check your connection',
          code: 'NETWORK_ERROR',
          details: { url, originalError: error.message },
        };
        error = networkError;
      }

      // Retry logic
      if (this.shouldRetry(error, retryAttempt, path)) {
        const delay = this.retryDelay * Math.pow(2, retryAttempt); // Exponential backoff
        console.warn(
          `API request failed (attempt ${retryAttempt + 1}/${this.maxRetries}), retrying in ${delay}ms:`,
          error
        );

        await this.sleep(delay);
        return this.request<T>(path, options, retryAttempt + 1);
      }

      throw error;
    }
  }

  // User management methods
  get users() {
    return {
      getAll: (): Promise<User[]> => {
        return this.request<User[]>(API_ENDPOINTS.USERS.BASE);
      },

      getById: (id: number): Promise<User> => {
        return this.request<User>(API_ENDPOINTS.USERS.BY_ID(id));
      },

      create: (userData: CreateUserRequest): Promise<User> => {
        return this.request<User>(API_ENDPOINTS.USERS.CREATE, {
          method: 'POST',
          body: JSON.stringify(userData),
        });
      },

      update: (id: number, userData: UpdateUserRequest): Promise<User> => {
        return this.request<User>(API_ENDPOINTS.USERS.UPDATE(id), {
          method: 'PUT',
          body: JSON.stringify(userData),
        });
      },

      delete: (id: number): Promise<void> => {
        return this.request<void>(API_ENDPOINTS.USERS.DELETE(id), {
          method: 'DELETE',
        });
      },
    };
  }

  // Authentication methods
  get auth() {
    return {
      login: async (credentials: LoginRequest): Promise<LoginResponse> => {
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        const response = await this.request<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: formData,
        });

        this.token = response.access_token;

        if (typeof window !== 'undefined') {
          localStorage.setItem(config.tokenKey, this.token);
        }

        return response;
      },

      logout: async (): Promise<void> => {
        this.token = null;
        if (typeof window !== 'undefined') {
          localStorage.removeItem(config.tokenKey);
        }
      },

      getCurrentUser: (): Promise<User> => {
        return this.request<User>(API_ENDPOINTS.AUTH.ME);
      },

      refreshToken: (): Promise<LoginResponse> => {
        return this.request<LoginResponse>(API_ENDPOINTS.AUTH.REFRESH, {
          method: 'POST',
        });
      },
    };
  }

  // System methods
  async getSystemOverview(): Promise<SystemOverview> {
    return this.request<SystemOverview>(API_ENDPOINTS.SYSTEM.OVERVIEW);
  }

  async getHealth(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>(API_ENDPOINTS.SYSTEM.HEALTH);
  }

  // Service methods
  async getServices(): Promise<Service[]> {
    return this.request<Service[]>(API_ENDPOINTS.SERVICES.BASE);
  }

  async getService(id: string): Promise<Service> {
    return this.request<Service>(API_ENDPOINTS.SERVICES.BY_ID(id));
  }

  async createService(service: CreateServiceRequest): Promise<Service> {
    return this.request<Service>(API_ENDPOINTS.SERVICES.CREATE, {
      method: 'POST',
      body: JSON.stringify(service),
    });
  }

  async updateService(service: UpdateServiceRequest): Promise<Service> {
    const { id, ...updateData } = service;
    return this.request<Service>(API_ENDPOINTS.SERVICES.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async deleteService(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.DELETE(id), {
      method: 'DELETE',
    });
  }

  async startService(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.START(id), {
      method: 'POST',
    });
  }

  async stopService(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.STOP(id), {
      method: 'POST',
    });
  }

  async restartService(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.RESTART(id), {
      method: 'POST',
    });
  }

  async getServiceLogs(id: string, lines: number = 100): Promise<string[]> {
    const response = await this.request<{ logs: string[] }>(API_ENDPOINTS.SERVICES.LOGS(id, lines));
    return response.logs;
  }

  // Services API object for compatibility
  services = {
    getAll: () => this.getServices(),
    getById: (id: string) => this.getService(id),
    create: (service: CreateServiceRequest) => this.createService(service),
    update: (service: UpdateServiceRequest) => this.updateService(service),
    delete: (id: string) => this.deleteService(id),
    start: (id: string) => this.startService(id),
    stop: (id: string) => this.stopService(id),
    restart: (id: string) => this.restartService(id),
    getLogs: (id: string, lines?: number) => this.getServiceLogs(id, lines),
  };

  // General-purpose HTTP methods
  async get<T>(path: string): Promise<{ ok: boolean; data?: T }> {
    try {
      const data = await this.request<T>(path, { method: 'GET' });
      return { ok: true, data };
    } catch (error) {
      console.error('GET request failed:', error);
      return { ok: false };
    }
  }

  async post<T>(path: string, body?: any): Promise<{ ok: boolean; data?: T }> {
    try {
      const data = await this.request<T>(path, {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined,
      });
      return { ok: true, data };
    } catch (error) {
      console.error('POST request failed:', error);
      return { ok: false };
    }
  }

  // Utility methods
  isAuthenticated(): boolean {
    return this.token !== null;
  }

  setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('wakedock_token', token);
    }
  }

  getToken(): string | null {
    return this.token;
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing or custom instances
export { ApiClient };
