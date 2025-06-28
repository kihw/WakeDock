/**
 * Authentication Store
 * Manages user authentication state
 */
import { writable, derived, get } from 'svelte/store';
import { api, type ApiError } from '../api.js';
import { type User } from '../types/user.js';

interface LoginResponse {
    user: User;
    token: string;
}

interface AuthState {
    user: User | null;
    token: string | null;
    refreshToken: string | null;
    isLoading: boolean;
    error: string | null;
    isRefreshing: boolean;
    lastActivity: Date | null;
    sessionExpiry: Date | null;
}

const initialState: AuthState = {
    user: null,
    token: null,
    refreshToken: null,
    isLoading: false,
    error: null,
    isRefreshing: false,
    lastActivity: null,
    sessionExpiry: null,
};

// Create the writable store
const { subscribe, set, update } = writable<AuthState>(initialState);

// Derived store for authentication status
export const isAuthenticated = derived(
    { subscribe },
    ($auth) => $auth.user !== null && $auth.token !== null
);

// Derived store for loading state
export const isLoading = derived(
    { subscribe },
    ($auth) => $auth.isLoading
);

// Auth store with methods
export const auth = {
    subscribe,

    // Initialize auth state from localStorage
    init: async () => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            const token = api.getToken();
            if (token) {
                const user = await api.auth.getCurrentUser();
                set({
                    user,
                    token,
                    refreshToken: null, // TODO: récupérer depuis localStorage si disponible
                    isLoading: false,
                    error: null,
                    isRefreshing: false,
                    lastActivity: new Date(),
                    sessionExpiry: null, // TODO: calculer à partir du token
                });
            } else {
                set({
                    user: null,
                    token: null,
                    refreshToken: null,
                    isLoading: false,
                    error: null,
                    isRefreshing: false,
                    lastActivity: null,
                    sessionExpiry: null,
                });
            }
        } catch (error) {
            console.error('Auth initialization failed:', error);
            // Clear invalid token
            await api.auth.logout();
            set({
                user: null,
                token: null,
                refreshToken: null,
                isLoading: false,
                error: null,
                isRefreshing: false,
                lastActivity: null,
                sessionExpiry: null,
            });
        }
    },

    // Login method
    login: async (emailOrUsername: string, password: string): Promise<void> => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            const response: LoginResponse = await api.auth.login({ username: emailOrUsername, password });
            set({
                user: response.user,
                token: response.token,
                refreshToken: null, // TODO: ajouter refresh_token à LoginResponse
                isLoading: false,
                error: null,
                isRefreshing: false,
                lastActivity: new Date(),
                sessionExpiry: null, // TODO: calculate based on token expiry
            });
        } catch (error) {
            const apiError = error as ApiError;
            update(state => ({
                ...state,
                isLoading: false,
                error: apiError.message || 'Login failed',
            }));
            throw error;
        }
    },

    // Logout method
    logout: async (): Promise<void> => {
        await api.auth.logout();
        set({
            user: null,
            token: null,
            refreshToken: null,
            isLoading: false,
            error: null,
            isRefreshing: false,
            lastActivity: null,
            sessionExpiry: null,
        });
    },

    // Clear error
    clearError: () => {
        update(state => ({ ...state, error: null }));
    },

    // Update user info
    updateUser: (user: User) => {
        update(state => ({ ...state, user, lastActivity: new Date() }));
    },

    // Refresh token
    refreshToken: async (): Promise<boolean> => {
        return new Promise((resolve) => {
            update(state => {
                if (state.isRefreshing) {
                    resolve(false);
                    return state;
                }

                if (!state.refreshToken) {
                    resolve(false);
                    return state;
                }

                return { ...state, isRefreshing: true };
            });

            // TODO: Implémenter l'appel API pour refresh token
            // Pour l'instant, simuler un échec
            setTimeout(() => {
                update(state => ({
                    ...state,
                    isRefreshing: false,
                    token: null,
                    refreshToken: null,
                    user: null,
                    sessionExpiry: null
                }));
                resolve(false);
            }, 1000);
        });
    },

    // Update last activity
    updateActivity: () => {
        update(state => ({ ...state, lastActivity: new Date() }));
    },

    // Check if session is expired
    isSessionExpired: (): boolean => {
        const state = get({ subscribe });
        if (!state.sessionExpiry) return false;
        return new Date() > state.sessionExpiry;
    },

    // Check if token needs refresh (within 5 minutes of expiry)
    needsTokenRefresh: (): boolean => {
        const state = get({ subscribe });
        if (!state.sessionExpiry) return false;
        const fiveMinutes = 5 * 60 * 1000;
        return new Date().getTime() > (state.sessionExpiry.getTime() - fiveMinutes);
    },
};
