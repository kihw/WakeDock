/**
 * WakeDock API Client
 * Typed API client with error handling and authentication
 */

import type { User, CreateUserRequest, UpdateUserRequest, LoginRequest, LoginResponse } from './types/user';
import { config } from './config/environment.js';
import { API_ENDPOINTS, getApiUrl } from './config/api.js';

export interface ApiError {
    message: string;
    code?: string;
    details?: any;
}

export interface Service {
    id: string;
    name: string;
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

class ApiClient {
    private baseUrl: string;
    private token: string | null = null;

    constructor(baseUrl: string = '') {
        // Use configuration from environment
        this.baseUrl = baseUrl || config.apiUrl;
        this.baseUrl = this.baseUrl.replace(/\/$/, ''); // Remove trailing slash

        // Try to load token from localStorage
        if (typeof window !== 'undefined') {
            this.token = localStorage.getItem(config.tokenKey);
        }
    }

    private async request<T>(
        path: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${path}`;
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };

        // Merge existing headers if they exist
        if (options.headers) {
            const existingHeaders = new Headers(options.headers);
            existingHeaders.forEach((value, key) => {
                headers[key] = value;
            });
        }

        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (!response.ok) {
                let errorData: any = { message: 'An error occurred' };

                try {
                    errorData = await response.json();
                } catch {
                    errorData = { message: response.statusText };
                }

                const error: ApiError = {
                    message: errorData.detail || errorData.message || response.statusText,
                    code: errorData.code,
                    details: errorData,
                };

                throw error;
            }

            // Handle empty responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return {} as T;
            }
        } catch (error) {
            if (error instanceof TypeError) {
                // Network error
                throw {
                    message: 'Network error. Please check your connection.',
                    code: 'NETWORK_ERROR',
                } as ApiError;
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
            }
        };
    }

    // Authentication methods
    get auth() {
        return {
            login: async (credentials: LoginRequest): Promise<LoginResponse> => {
                const formData = new FormData();
                formData.append('username', credentials.username);
                formData.append('password', credentials.password);

                const response = await this.request<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, {
                    method: 'POST',
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
            }
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
        const response = await this.request<{ logs: string[] }>(
            API_ENDPOINTS.SERVICES.LOGS(id, lines)
        );
        return response.logs;
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
