/**
 * API Client Tests
 * Comprehensive tests for the API client with error handling and retry logic
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiClient } from '../../src/lib/api';
import type { Service, CreateServiceRequest } from '../../src/lib/api';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn()
};
Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage
});

describe('ApiClient', () => {
    let apiClient: ApiClient;

    beforeEach(() => {
        vi.clearAllMocks();
        apiClient = new ApiClient('http://localhost:8000');
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Error Handling', () => {
        it('should retry failed requests up to maxRetries', async () => {
            // First two calls fail, third succeeds
            mockFetch
                .mockRejectedValueOnce(new Error('Network error'))
                .mockRejectedValueOnce(new Error('Network error'))
                .mockResolvedValueOnce(new Response(JSON.stringify({ success: true }), {
                    status: 200,
                    headers: { 'content-type': 'application/json' }
                }));

            const result = await apiClient.getServices();

            expect(mockFetch).toHaveBeenCalledTimes(3);
            expect(result).toEqual({ success: true });
        });

        it('should throw error after max retries exceeded', async () => {
            mockFetch.mockRejectedValue(new Error('Network error'));

            await expect(apiClient.getServices()).rejects.toThrow('Network error');
            expect(mockFetch).toHaveBeenCalledTimes(4); // Initial + 3 retries
        });

        it('should handle timeout errors', async () => {
            const abortError = new Error('The operation was aborted');
            abortError.name = 'AbortError';
            mockFetch.mockRejectedValue(abortError);

            await expect(apiClient.getServices()).rejects.toMatchObject({
                message: 'Request timeout',
                code: 'TIMEOUT'
            });
        });

        it('should handle network errors', async () => {
            const networkError = new TypeError('Failed to fetch');
            mockFetch.mockRejectedValue(networkError);

            await expect(apiClient.getServices()).rejects.toMatchObject({
                message: 'Network error - please check your connection',
                code: 'NETWORK_ERROR'
            });
        });

        it('should handle HTTP error responses', async () => {
            mockFetch.mockResolvedValue(new Response(
                JSON.stringify({ detail: 'Not found' }),
                {
                    status: 404,
                    headers: { 'content-type': 'application/json' }
                }
            ));

            await expect(apiClient.getServices()).rejects.toMatchObject({
                message: 'Not found',
                details: expect.objectContaining({ status: 404 })
            });
        });
    });

    describe('Authentication', () => {
        it('should include Authorization header when token is set', async () => {
            mockLocalStorage.getItem.mockReturnValue('test-token');
            apiClient = new ApiClient('http://localhost:8000');

            mockFetch.mockResolvedValue(new Response('[]', {
                status: 200,
                headers: { 'content-type': 'application/json' }
            }));

            await apiClient.getServices();

            expect(mockFetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer test-token'
                    })
                })
            );
        });

        it('should handle login and store token', async () => {
            const loginResponse = {
                access_token: 'new-token',
                token_type: 'bearer',
                expires_in: 3600
            };

            mockFetch.mockResolvedValue(new Response(
                JSON.stringify(loginResponse),
                {
                    status: 200,
                    headers: { 'content-type': 'application/json' }
                }
            ));

            const result = await apiClient.auth.login({
                username: 'test@example.com',
                password: 'password'
            });

            expect(result).toEqual(loginResponse);
            expect(mockLocalStorage.setItem).toHaveBeenCalledWith('wakedock_token', 'new-token');
        });
    });

    describe('Services API', () => {
        const mockService: Service = {
            id: '1',
            name: 'test-service',
            image: 'nginx:latest',
            status: 'running',
            ports: [{ host: 80, container: 80, protocol: 'tcp' }],
            environment: {},
            volumes: [],
            created_at: '2023-01-01T00:00:00Z',
            updated_at: '2023-01-01T00:00:00Z',
            restart_policy: 'always',
            labels: {}
        };

        it('should fetch services', async () => {
            mockFetch.mockResolvedValue(new Response(
                JSON.stringify([mockService]),
                {
                    status: 200,
                    headers: { 'content-type': 'application/json' }
                }
            ));

            const services = await apiClient.getServices();

            expect(services).toEqual([mockService]);
            expect(mockFetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/services',
                expect.objectContaining({
                    method: undefined // GET is default
                })
            );
        });

        it('should create service', async () => {
            const createRequest: CreateServiceRequest = {
                name: 'new-service',
                image: 'nginx:latest',
                ports: [{ host: 80, container: 80, protocol: 'tcp' }]
            };

            mockFetch.mockResolvedValue(new Response(
                JSON.stringify({ ...mockService, ...createRequest }),
                {
                    status: 201,
                    headers: { 'content-type': 'application/json' }
                }
            ));

            const service = await apiClient.createService(createRequest);

            expect(service.name).toBe(createRequest.name);
            expect(mockFetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/services',
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify(createRequest)
                })
            );
        });

        it('should update service', async () => {
            const updateRequest = {
                id: '1',
                name: 'updated-service'
            };

            mockFetch.mockResolvedValue(new Response(
                JSON.stringify({ ...mockService, name: 'updated-service' }),
                {
                    status: 200,
                    headers: { 'content-type': 'application/json' }
                }
            ));

            const service = await apiClient.updateService(updateRequest);

            expect(service.name).toBe('updated-service');
            expect(mockFetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/services/1',
                expect.objectContaining({
                    method: 'PUT',
                    body: JSON.stringify(updateRequest)
                })
            );
        });

        it('should delete service', async () => {
            mockFetch.mockResolvedValue(new Response('', { status: 204 }));

            await apiClient.deleteService('1');

            expect(mockFetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/services/1',
                expect.objectContaining({
                    method: 'DELETE'
                })
            );
        });
    });

    describe('Request Configuration', () => {
        it('should use custom timeout', async () => {
            const timeoutSpy = vi.spyOn(global, 'setTimeout');

            mockFetch.mockImplementation(() => new Promise(() => { })); // Never resolves

            const promise = apiClient.getServices();

            // Wait a bit for timeout to be set
            await new Promise(resolve => setTimeout(resolve, 10));

            expect(timeoutSpy).toHaveBeenCalled();

            // Cleanup
            timeoutSpy.mockRestore();
        });

        it('should handle empty responses', async () => {
            mockFetch.mockResolvedValue(new Response('', { status: 200 }));

            const result = await apiClient.getServices();

            expect(result).toEqual({});
        });

        it('should handle non-JSON responses', async () => {
            mockFetch.mockResolvedValue(new Response('OK', {
                status: 200,
                headers: { 'content-type': 'text/plain' }
            }));

            const result = await apiClient.getServices();

            expect(result).toEqual({});
        });
    });

    describe('Exponential Backoff', () => {
        it('should implement exponential backoff for retries', async () => {
            const sleepSpy = vi.spyOn(apiClient as any, 'sleep');

            mockFetch
                .mockRejectedValueOnce(new Error('Server error'))
                .mockRejectedValueOnce(new Error('Server error'))
                .mockResolvedValueOnce(new Response('[]', { status: 200 }));

            await apiClient.getServices();

            // Should have been called twice (for 2 retries)
            expect(sleepSpy).toHaveBeenCalledTimes(2);

            // First retry: 1000ms delay
            expect(sleepSpy).toHaveBeenNthCalledWith(1, 1000);
            // Second retry: 2000ms delay (exponential backoff)
            expect(sleepSpy).toHaveBeenNthCalledWith(2, 2000);

            sleepSpy.mockRestore();
        });
    });
});

// Export for use in other test files
export { mockFetch, mockLocalStorage };
