import type { User, LoginCredentials } from './lib/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
    constructor(
        message: string,
        public status: number,
        public response?: any
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

async function makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    const token = localStorage.getItem('auth_token');
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new ApiError(
                errorData.message || `HTTP ${response.status}: ${response.statusText}`,
                response.status,
                errorData
            );
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return {} as T;
    } catch (error) {
        if (error instanceof ApiError) {
            throw error;
        }
        throw new ApiError(
            error instanceof Error ? error.message : 'Network error',
            0
        );
    }
}

export const api = {
    auth: {
        async login(credentials: LoginCredentials): Promise<{ user: User; token: string }> {
            return makeRequest('/auth/login', {
                method: 'POST',
                body: JSON.stringify(credentials),
            });
        },

        async logout(): Promise<void> {
            await makeRequest('/auth/logout', {
                method: 'POST',
            });
        },

        async refresh(): Promise<{ token: string }> {
            return makeRequest('/auth/refresh', {
                method: 'POST',
            });
        },

        async me(): Promise<User> {
            return makeRequest('/auth/me');
        },
    },

    services: {
        async list(): Promise<any[]> {
            return makeRequest('/services');
        },

        async get(id: string): Promise<any> {
            return makeRequest(`/services/${id}`);
        },

        async create(service: any): Promise<any> {
            return makeRequest('/services', {
                method: 'POST',
                body: JSON.stringify(service),
            });
        },

        async update(id: string, service: any): Promise<any> {
            return makeRequest(`/services/${id}`, {
                method: 'PUT',
                body: JSON.stringify(service),
            });
        },

        async delete(id: string): Promise<void> {
            await makeRequest(`/services/${id}`, {
                method: 'DELETE',
            });
        },

        async start(id: string): Promise<void> {
            await makeRequest(`/services/${id}/start`, {
                method: 'POST',
            });
        },

        async stop(id: string): Promise<void> {
            await makeRequest(`/services/${id}/stop`, {
                method: 'POST',
            });
        },

        async restart(id: string): Promise<void> {
            await makeRequest(`/services/${id}/restart`, {
                method: 'POST',
            });
        },

        async logs(id: string, tail?: number): Promise<string[]> {
            const params = tail ? `?tail=${tail}` : '';
            return makeRequest(`/services/${id}/logs${params}`);
        },
    },

    monitoring: {
        async getMetrics(): Promise<any> {
            return makeRequest('/monitoring/metrics');
        },

        async getSystemInfo(): Promise<any> {
            return makeRequest('/monitoring/system');
        },
    },
};

export { ApiError };
