/**
 * Tests for Enhanced API Client
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { ApiClient } from '../api.js';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock AbortController
global.AbortController = class AbortController {
    signal = { aborted: false, addEventListener: vi.fn() };
    abort = vi.fn(() => { this.signal.aborted = true; });
};

// Mock window
Object.defineProperty(window, 'location', {
    value: {
        origin: 'https://test.wakedock.com',
        href: 'https://test.wakedock.com/dashboard'
    }
});

Object.defineProperty(window, 'localStorage', {
    value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn()
    }
});

Object.defineProperty(window, 'navigator', {
    value: {
        onLine: true
    }
});

describe('Enhanced API Client', () => {
    let apiClient: ApiClient;

    beforeEach(() => {
        vi.clearAllMocks();
        apiClient = new ApiClient('https://api.test.com');
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('Timeout Configuration', () => {
        test('should use endpoint-specific timeout for auth', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ access_token: 'test-token' }),
                headers: new Headers()
            });

            await apiClient.auth.login({
                username: 'test@example.com',
                password: 'password'
            });

            expect(mockFetch).toHaveBeenCalledWith(
                'https://api.test.com/auth/login',
                expect.objectContaining({
                    method: 'POST'
                })
            );
        });

        test('should use endpoint-specific timeout for services', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ([]),
                headers: new Headers()
            });

            await apiClient.getServices();

            expect(mockFetch).toHaveBeenCalledWith(
                'https://api.test.com/services',
                expect.objectContaining({
                    method: 'GET'
                })
            );
        });

        test('should use default timeout for unknown endpoints', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({}),
                headers: new Headers()
            });

            await apiClient.get('/unknown-endpoint');

            expect(mockFetch).toHaveBeenCalledWith(
                'https://api.test.com/unknown-endpoint',
                expect.objectContaining({
                    method: 'GET'
                })
            );
        });
    });

    describe('Circuit Breaker', () => {
        test('should open circuit after repeated failures', async () => {
            // Mock 5 consecutive failures
            mockFetch.mockRejectedValue(new Error('Network error'));

            // First 5 attempts should be made
            for (let i = 0; i < 5; i++) {
                try {
                    await apiClient.get('/test');
                } catch (error) {
                    // Expected to fail
                }
            }

            expect(mockFetch).toHaveBeenCalledTimes(15); // 5 initial + 10 retries (2 per attempt)

            // Next attempt should be blocked by circuit breaker
            try {
                await apiClient.get('/test');
                expect.fail('Should have thrown circuit breaker error');
            } catch (error) {
                expect(error.message).toContain('Circuit breaker open');
            }
        });

        test('should record success and reset circuit breaker', async () => {
            // First fail to increment failure count
            mockFetch.mockRejectedValueOnce(new Error('Network error'));

            try {
                await apiClient.get('/test');
            } catch (error) {
                // Expected failure
            }

            // Then succeed
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({}),
                headers: new Headers()
            });

            const result = await apiClient.get('/test');
            expect(result.ok).toBe(true);
        });
    });

    describe('Network Status', () => {
        test('should throw error when offline', async () => {
            // Mock offline
            Object.defineProperty(window.navigator, 'onLine', {
                value: false,
                configurable: true
            });

            // Create new client to trigger offline detection
            const offlineClient = new ApiClient('https://api.test.com');

            try {
                await offlineClient.get('/test');
                expect.fail('Should have thrown offline error');
            } catch (error) {
                expect(error.message).toContain('Network offline');
            }
        });
    });

    describe('Retry Logic', () => {
        test('should retry on network errors', async () => {
            mockFetch
                .mockRejectedValueOnce(new TypeError('Network error'))
                .mockRejectedValueOnce(new TypeError('Network error'))
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({}),
                    headers: new Headers()
                });

            const result = await apiClient.get('/test');
            expect(result.ok).toBe(true);
            expect(mockFetch).toHaveBeenCalledTimes(3);
        });

        test('should retry on 5xx errors', async () => {
            mockFetch
                .mockResolvedValueOnce({
                    ok: false,
                    status: 500,
                    statusText: 'Internal Server Error',
                    text: async () => '{"message": "Server error"}',
                    headers: new Headers()
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({}),
                    headers: new Headers()
                });

            const result = await apiClient.get('/test');
            expect(result.ok).toBe(true);
            expect(mockFetch).toHaveBeenCalledTimes(2);
        });

        test('should not retry on 4xx errors', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                text: async () => '{"message": "Bad request"}',
                headers: new Headers()
            });

            const result = await apiClient.get('/test');
            expect(result.ok).toBe(false);
            expect(mockFetch).toHaveBeenCalledTimes(1);
        });

        test('should use exponential backoff for retries', async () => {
            const startTime = Date.now();

            mockFetch
                .mockRejectedValueOnce(new TypeError('Network error'))
                .mockRejectedValueOnce(new TypeError('Network error'))
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({}),
                    headers: new Headers()
                });

            await apiClient.get('/test');

            const endTime = Date.now();
            // Should take at least 1000ms (first retry) + 2000ms (second retry) = 3000ms
            expect(endTime - startTime).toBeGreaterThan(2900);
        });
    });

    describe('Error Handling', () => {
        test('should handle timeout errors properly', async () => {
            // Mock AbortError (timeout)
            const abortError = new Error('AbortError');
            abortError.name = 'AbortError';

            mockFetch.mockRejectedValueOnce(abortError);

            try {
                await apiClient.get('/test');
                expect.fail('Should have thrown timeout error');
            } catch (error) {
                expect(error.message).toContain('Request timeout');
                expect(error.code).toBe('TIMEOUT');
            }
        });

        test('should handle network errors properly', async () => {
            mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

            try {
                await apiClient.get('/test');
                expect.fail('Should have thrown network error');
            } catch (error) {
                expect(error.message).toContain('Network error');
                expect(error.code).toBe('NETWORK_ERROR');
            }
        });

        test('should sanitize error responses', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                text: async () => '{"message": "<script>alert(\'xss\')</script>"}',
                headers: new Headers()
            });

            try {
                await apiClient.get('/test');
                expect.fail('Should have thrown error');
            } catch (error) {
                expect(error.message).not.toContain('<script>');
                expect(error.message).toContain('alert(\\\'xss\\\')');
            }
        });
    });

    describe('Security Headers', () => {
        test('should include security headers in requests', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({}),
                headers: new Headers()
            });

            await apiClient.get('/test');

            expect(mockFetch).toHaveBeenCalledWith(
                'https://api.test.com/test',
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'X-Frame-Options': 'DENY',
                        'X-Content-Type-Options': 'nosniff',
                        'X-XSS-Protection': '1; mode=block',
                        'Referrer-Policy': 'strict-origin-when-cross-origin',
                        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
                    })
                })
            );
        });

        test('should validate response headers', async () => {
            const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => { });

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({}),
                headers: new Headers() // No security headers
            });

            await apiClient.get('/test');

            expect(consoleSpy).toHaveBeenCalledWith(
                'Security warnings for response:',
                expect.arrayContaining([
                    'Missing X-Frame-Options header',
                    'Missing X-Content-Type-Options header'
                ])
            );

            consoleSpy.mockRestore();
        });
    });

    describe('Authentication', () => {
        test('should store token after successful login', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    access_token: 'test-token',
                    user: { id: 1, email: 'test@example.com' }
                }),
                headers: new Headers()
            });

            const response = await apiClient.auth.login({
                username: 'test@example.com',
                password: 'password'
            });

            expect(response.access_token).toBe('test-token');
            expect(window.localStorage.setItem).toHaveBeenCalledWith(
                'wakedock_token',
                'test-token'
            );
        });

        test('should include authorization header when authenticated', async () => {
            // Set token
            apiClient.setToken('test-token');

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({}),
                headers: new Headers()
            });

            await apiClient.get('/test');

            expect(mockFetch).toHaveBeenCalledWith(
                'https://api.test.com/test',
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer test-token'
                    })
                })
            );
        });
    });
});
