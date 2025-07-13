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
import { config } from './config/environment.js';
import { API_ENDPOINTS, getApiUrl } from './config/api.js';
import { csrf, rateLimit, securityValidate } from './utils/validation.js';
import { memoryUtils } from './utils/storage.js';
import { apiMonitor } from './monitoring/api-monitor.js';

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
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

    // Load config directly without causing circular dependency
    try {
      // Use window.fetch directly to avoid using this API client for config
      const configResponse = await window.fetch('/api/config', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin', // Match backend allow_credentials=True
        cache: 'no-cache'
      });

      if (configResponse.ok) {
        const runtimeConfig = await configResponse.json();
        console.log('✅ Runtime config loaded directly:', runtimeConfig);
        // Update baseUrl directly from config
        const newBaseUrl = (runtimeConfig.apiUrl || '/api/v1').replace(/\/$/, '');
        if (newBaseUrl !== this.baseUrl) {
          console.log('🔄 Updating ApiClient baseUrl from', this.baseUrl, 'to', newBaseUrl);
          this.baseUrl = newBaseUrl;
        }
      } else {
        console.warn('⚠️ Runtime config not available, using default baseUrl:', this.baseUrl);
      }
    } catch (error) {
      console.warn('⚠️ Failed to load runtime config, using defaults:', error);
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

  private shouldRetry(error: unknown, attempt: number, endpoint: string): boolean {
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
    console.error('🔥 [REQUEST_START] Starting API request:', {
      path,
      method: options.method || 'GET',
      retryAttempt,
      timestamp: new Date().toISOString()
    });

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

    // Skip complex validation for auth endpoints
    const isAuthEndpoint = path.startsWith('/auth/');
    
    // Check circuit breaker (skip for auth endpoints)
    if (!isAuthEndpoint && this.circuitBreaker.isOpen(path)) {
      throw new Error(`Circuit breaker open for ${path} - too many recent failures`);
    }

    // Check network status (skip for auth endpoints)
    if (!isAuthEndpoint && !this.networkStatus.isOnline) {
      throw new Error('Network offline - check your connection');
    }

    // Rate limiting check
    if (!options.skipRateLimit && !isAuthEndpoint) {
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

    // Add CSRF token for state-changing operations (skip for auth endpoints)
    if (
      !options.skipCSRF &&
      !isAuthEndpoint &&
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
      if (config.enableDebug) {
        console.log('🚀 API Request START:', {
          url,
          method: options.method || 'GET',
          timestamp: new Date().toISOString(),
          timeoutMs: endpointTimeout,
          headers: Object.keys(headers)
        });
      }

      const requestStart = Date.now();

      console.error('🔄 About to make fetch request:', {
        url,
        headers,
        body: options.body,
        method: options.method
      });

      const response = await window.fetch(url, {
        ...options,
        headers,
        signal: combinedSignal,
      });

      const requestDuration = Date.now() - requestStart;
      console.error('✅ API Response received:', {
        url,
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries()),
        duration: requestDuration + 'ms',
        timestamp: new Date().toISOString()
      });

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
        let errorData: Record<string, unknown> = { message: 'An error occurred' };

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
      console.error('📄 Processing response:', {
        contentType,
        hasContent: !!contentType,
        status: response.status,
        statusText: response.statusText
      });

      if (contentType && contentType.includes('application/json')) {
        console.error('📦 Parsing JSON response...');

        let responseData;
        try {
          responseData = await response.json();
          console.error('✅ JSON parsed successfully:', responseData);
        } catch (parseError: unknown) {
          console.error('❌ JSON parsing failed:', parseError);
          // If JSON parsing fails, try to get the raw text for debugging
          try {
            const responseText = await response.text();
            console.error('📄 Raw response text:', responseText);
          } catch (textError) {
            console.error('❌ Failed to get response text:', textError);
          }
          throw new Error(`Failed to parse JSON response: ${parseError?.message || 'Unknown parsing error'}`);
        }

        // Basic response validation
        if (typeof responseData === 'object' && responseData !== null) {
          try {
            // Remove any potentially dangerous properties
            delete responseData.__proto__;
            delete responseData.constructor;
            console.error('✅ Response validation passed');
          } catch (validationError) {
            console.error('❌ Response validation failed:', validationError);
          }
        }

        // Record success in circuit breaker
        this.circuitBreaker.recordSuccess(path);

        // Record success in monitoring
        const requestDuration = Date.now() - requestStart;
        apiMonitor.recordSuccess(path, requestDuration);

        console.error('🎉 Returning response data:', responseData);
        return responseData;
      } else {
        console.error('📄 Non-JSON response, returning empty object');

        // Record success in circuit breaker
        this.circuitBreaker.recordSuccess(path);

        // Record success in monitoring
        const requestDuration = Date.now() - requestStart;
        apiMonitor.recordSuccess(path, requestDuration);

        return {} as T;
      }
    } catch (error: unknown) {
      // Record failure in circuit breaker
      this.circuitBreaker.recordFailure(path);

      // Record error in monitoring
      apiMonitor.recordError(path, error);

      // Add detailed error logging
      console.error('❌ API request failed:', {
        url,
        error: error,
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack,
        timeout: endpointTimeout,
        retryAttempt,
        circuitBreakerFailures: this.circuitBreaker.failures.get(path) || 0,
        errorType: typeof error,
        errorConstructor: error.constructor?.name
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
        console.error('🌐 NETWORK ERROR DETECTED:', {
          url,
          originalError: error.message,
          errorName: error.name,
          errorStack: error.stack
        });
        const networkError: ApiError = {
          message: 'Network error - please check your connection',
          code: 'NETWORK_ERROR',
          details: { url, originalError: error.message },
        };
        error = networkError;
      }

      // Retry logic (skip for auth endpoints to avoid token conflicts)
      const isAuthEndpoint = path.startsWith('/auth/');
      if (!isAuthEndpoint && this.shouldRetry(error, retryAttempt, path)) {
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
        // Use direct fetch for auth to avoid service worker and complex validation
        await this.ensureInitialized();
        
        const response = await window.fetch(`${this.baseUrl}${API_ENDPOINTS.AUTH.LOGIN}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(credentials),
          credentials: 'same-origin'
        });

        if (!response.ok) {
          throw new Error(`Login failed: ${response.status} ${response.statusText}`);
        }

        const loginResponse = await response.json();
        this.token = loginResponse.access_token;

        if (typeof window !== 'undefined' && this.token) {
          localStorage.setItem(config.tokenKey, this.token);
        }

        return loginResponse;
      },

      logout: async (): Promise<void> => {
        this.token = null;
        if (typeof window !== 'undefined') {
          localStorage.removeItem(config.tokenKey);
          
          // Clear auth cache in service worker
          if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
              type: 'CLEAR_AUTH_CACHE'
            });
          }
        }
      },

      getCurrentUser: async (): Promise<User> => {
        // Use direct fetch for auth to avoid service worker issues
        await this.ensureInitialized();
        
        const response = await window.fetch(`${this.baseUrl}${API_ENDPOINTS.AUTH.ME}`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Authorization': this.token ? `Bearer ${this.token}` : ''
          },
          credentials: 'same-origin'
        });

        if (!response.ok) {
          throw new Error(`Get current user failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
      },

      refreshToken: (): Promise<LoginResponse> => {
        return this.request<LoginResponse>(API_ENDPOINTS.AUTH.REFRESH, {
          method: 'POST',
          skipCSRF: true,
          timeout: 5000
        });
      },
    };
  }

  // System methods
  async getSystemOverview(): Promise<SystemOverview> {
    // Use direct fetch to avoid service worker issues
    await this.ensureInitialized();
    
    const response = await window.fetch(`${this.baseUrl}${API_ENDPOINTS.SYSTEM.OVERVIEW}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      credentials: 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`Get system overview failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  async getHealth(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>(API_ENDPOINTS.SYSTEM.HEALTH);
  }

  // Service methods
  async getServices(): Promise<Service[]> {
    // Use direct fetch to avoid service worker issues
    await this.ensureInitialized();
    
    const response = await window.fetch(`${this.baseUrl}${API_ENDPOINTS.SERVICES.BASE}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      credentials: 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`Get services failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
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

  async post<T>(path: string, body?: unknown): Promise<{ ok: boolean; data?: T }> {
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
    // Return cached token if available
    if (this.token) {
      return this.token;
    }
    
    // Try to get token from localStorage
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('wakedock_token');
      if (storedToken) {
        this.token = storedToken;
        return storedToken;
      }
    }
    
    return null;
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing or custom instances
export { ApiClient };
