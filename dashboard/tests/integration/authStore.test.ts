/**
 * Authentication Store Integration Tests
 * Tests for auth store with API integration and token management
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';
import { auth, isAuthenticated } from '../../src/lib/stores/auth';
import type { User } from '../../src/lib/types/user';

// Mock API
const mockApi = {
    auth: {
        login: vi.fn(),
        logout: vi.fn(),
        getCurrentUser: vi.fn(),
        refreshToken: vi.fn()
    },
    getToken: vi.fn(),
    setToken: vi.fn()
};

vi.mock('../../src/lib/api', () => ({
    api: mockApi
}));

// Mock localStorage
const mockLocalStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage,
    writable: true
});

describe('Auth Store Integration', () => {
    const mockUser: User = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        full_name: 'Test User',
        is_active: true,
        is_superuser: false,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
    };

    beforeEach(() => {
        vi.clearAllMocks();
        // Reset auth store
        auth.logout();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Initialization', () => {
        it('should initialize with token from localStorage', async () => {
            mockApi.getToken.mockReturnValue('existing-token');
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);

            await auth.init();

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toEqual(mockUser);
            expect(authState.token).toBe('existing-token');
            expect(get(isAuthenticated)).toBe(true);
        });

        it('should handle initialization without token', async () => {
            mockApi.getToken.mockReturnValue(null);

            await auth.init();

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toBeNull();
            expect(authState.token).toBeNull();
            expect(get(isAuthenticated)).toBe(false);
        });

        it('should handle invalid token during initialization', async () => {
            mockApi.getToken.mockReturnValue('invalid-token');
            mockApi.auth.getCurrentUser.mockRejectedValue(new Error('Unauthorized'));

            await auth.init();

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toBeNull();
            expect(authState.token).toBeNull();
            expect(mockApi.auth.logout).toHaveBeenCalled();
        });
    });

    describe('Login', () => {
        it('should handle successful login', async () => {
            const loginResponse = {
                access_token: 'new-token',
                token_type: 'bearer',
                expires_in: 3600
            };

            mockApi.auth.login.mockResolvedValue(loginResponse);
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);

            const result = await auth.login('test@example.com', 'password');

            expect(result).toEqual(expect.objectContaining(loginResponse));

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toEqual(mockUser);
            expect(authState.token).toBe('new-token');
            expect(authState.isLoading).toBe(false);
            expect(authState.error).toBeNull();
        });

        it('should handle 2FA requirement', async () => {
            const loginResponse = {
                access_token: 'temp-token',
                token_type: 'bearer',
                expires_in: 3600,
                requiresTwoFactor: true
            };

            // Mock 2FA requirement (admin user)
            const result = await auth.login('admin@wakedock.com', 'password');

            expect(result).toMatchObject({
                requiresTwoFactor: true
            });

            // Should not set user state for 2FA required
            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toBeNull();
            expect(authState.isLoading).toBe(false);
        });

        it('should handle login with 2FA code', async () => {
            const loginResponse = {
                access_token: 'final-token',
                token_type: 'bearer',
                expires_in: 3600
            };

            mockApi.auth.login.mockResolvedValue(loginResponse);
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);

            const result = await auth.login('admin@wakedock.com', 'password', {
                twoFactorCode: '123456'
            });

            expect(result).toEqual(expect.objectContaining(loginResponse));

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toEqual(mockUser);
            expect(authState.token).toBe('final-token');
        });

        it('should handle remember me option', async () => {
            const loginResponse = {
                access_token: 'token',
                token_type: 'bearer',
                expires_in: 3600,
                refresh_token: 'refresh-token'
            };

            mockApi.auth.login.mockResolvedValue(loginResponse);
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);

            await auth.login('test@example.com', 'password', {
                rememberMe: true
            });

            expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
                'wakedock_refresh_token',
                'refresh-token'
            );
        });

        it('should handle login failure', async () => {
            const loginError = new Error('Invalid credentials');
            mockApi.auth.login.mockRejectedValue(loginError);

            await expect(auth.login('test@example.com', 'wrong-password'))
                .rejects.toThrow('Invalid credentials');

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toBeNull();
            expect(authState.token).toBeNull();
            expect(authState.isLoading).toBe(false);
            expect(authState.error).toBe('Invalid credentials');
        });
    });

    describe('Token Refresh', () => {
        it('should refresh token successfully', async () => {
            // Set up initial auth state
            const refreshResponse = {
                access_token: 'new-token',
                token_type: 'bearer',
                expires_in: 3600
            };

            mockApi.auth.refreshToken.mockResolvedValue(refreshResponse);
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);
            mockLocalStorage.getItem.mockReturnValue('refresh-token');

            // Set initial state with expired token
            auth.login('test@example.com', 'password');

            const success = await auth.refreshToken();

            expect(success).toBe(true);

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.token).toBe('new-token');
            expect(authState.isRefreshing).toBe(false);
        });

        it('should handle refresh failure and logout', async () => {
            mockApi.auth.refreshToken.mockRejectedValue(new Error('Refresh failed'));
            mockLocalStorage.getItem.mockReturnValue('invalid-refresh-token');

            const success = await auth.refreshToken();

            expect(success).toBe(false);

            // Should auto-logout after failed refresh
            await new Promise(resolve => setTimeout(resolve, 1100));

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toBeNull();
            expect(authState.token).toBeNull();
        });

        it('should not refresh if already refreshing', async () => {
            // Setup concurrent refresh attempts
            const promise1 = auth.refreshToken();
            const promise2 = auth.refreshToken();

            const [result1, result2] = await Promise.all([promise1, promise2]);

            // Only one should succeed, other should return false
            expect(result1 !== result2).toBe(true);
            expect(mockApi.auth.refreshToken).toHaveBeenCalledTimes(1);
        });
    });

    describe('Logout', () => {
        it('should logout and clear all data', async () => {
            // Setup logged in state
            mockApi.auth.login.mockResolvedValue({
                access_token: 'token',
                token_type: 'bearer',
                expires_in: 3600
            });
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);

            await auth.login('test@example.com', 'password');

            // Logout
            await auth.logout();

            expect(mockApi.auth.logout).toHaveBeenCalled();
            expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('wakedock_refresh_token');
            expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_remember');
            expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_expiry');

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toBeNull();
            expect(authState.token).toBeNull();
            expect(authState.refreshToken).toBeNull();
        });
    });

    describe('Session Management', () => {
        it('should track last activity', () => {
            auth.updateActivity();

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.lastActivity).toBeInstanceOf(Date);
        });

        it('should check session expiry', () => {
            // Mock expired session
            const expiredDate = new Date(Date.now() - 3600000); // 1 hour ago

            // Manually set expired session
            const currentState = get({ subscribe: auth.subscribe });
            auth.subscribe.set?.({
                ...currentState,
                sessionExpiry: expiredDate
            });

            const isExpired = auth.isSessionExpired();
            expect(isExpired).toBe(true);
        });

        it('should check if token needs refresh', () => {
            // Mock token that expires soon
            const soonExpiry = new Date(Date.now() + 60000); // 1 minute from now

            const currentState = get({ subscribe: auth.subscribe });
            auth.subscribe.set?.({
                ...currentState,
                sessionExpiry: soonExpiry,
                token: 'current-token'
            });

            const needsRefresh = auth.needsTokenRefresh();
            expect(needsRefresh).toBe(true);
        });
    });

    describe('Error Handling', () => {
        it('should clear errors', () => {
            // Set error state
            const currentState = get({ subscribe: auth.subscribe });
            auth.subscribe.set?.({
                ...currentState,
                error: 'Some error'
            });

            auth.clearError();

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.error).toBeNull();
        });

        it('should update user info', () => {
            const updatedUser = { ...mockUser, full_name: 'Updated Name' };

            auth.updateUser(updatedUser);

            const authState = get({ subscribe: auth.subscribe });
            expect(authState.user).toEqual(updatedUser);
            expect(authState.lastActivity).toBeInstanceOf(Date);
        });
    });

    describe('Reactive Stores', () => {
        it('should update isAuthenticated derived store', async () => {
            expect(get(isAuthenticated)).toBe(false);

            // Login
            mockApi.auth.login.mockResolvedValue({
                access_token: 'token',
                token_type: 'bearer',
                expires_in: 3600
            });
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);

            await auth.login('test@example.com', 'password');

            expect(get(isAuthenticated)).toBe(true);

            // Logout
            await auth.logout();

            expect(get(isAuthenticated)).toBe(false);
        });

        it('should update loading state correctly', async () => {
            const loadingStates: boolean[] = [];

            const unsubscribe = auth.subscribe(state => {
                loadingStates.push(state.isLoading);
            });

            mockApi.auth.login.mockImplementation(() =>
                new Promise(resolve => setTimeout(() => resolve({
                    access_token: 'token',
                    token_type: 'bearer',
                    expires_in: 3600
                }), 100))
            );
            mockApi.auth.getCurrentUser.mockResolvedValue(mockUser);

            const loginPromise = auth.login('test@example.com', 'password');

            // Should start with loading true
            expect(loadingStates[loadingStates.length - 1]).toBe(true);

            await loginPromise;

            // Should end with loading false
            expect(loadingStates[loadingStates.length - 1]).toBe(false);

            unsubscribe();
        });
    });
});

// Export for other test files
export { mockApi, mockLocalStorage };
