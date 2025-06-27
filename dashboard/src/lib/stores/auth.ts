/**
 * Authentication Store
 * Manages user authentication state
 */
import { writable, derived } from 'svelte/store';
import { api, type User, type AuthResponse, type ApiError } from '../api.js';

interface AuthState {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    error: string | null;
}

const initialState: AuthState = {
    user: null,
    token: null,
    isLoading: false,
    error: null,
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
                const user = await api.getCurrentUser();
                set({
                    user,
                    token,
                    isLoading: false,
                    error: null,
                });
            } else {
                set({
                    user: null,
                    token: null,
                    isLoading: false,
                    error: null,
                });
            }
        } catch (error) {
            console.error('Auth initialization failed:', error);
            // Clear invalid token
            api.logout();
            set({
                user: null,
                token: null,
                isLoading: false,
                error: null,
            });
        }
    },

    // Login method
    login: async (username: string, password: string): Promise<void> => {
        update(state => ({ ...state, isLoading: true, error: null }));

        try {
            const response: AuthResponse = await api.login(username, password);
            set({
                user: response.user,
                token: response.access_token,
                isLoading: false,
                error: null,
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
        await api.logout();
        set({
            user: null,
            token: null,
            isLoading: false,
            error: null,
        });
    },

    // Clear error
    clearError: () => {
        update(state => ({ ...state, error: null }));
    },

    // Update user info
    updateUser: (user: User) => {
        update(state => ({ ...state, user }));
    },
};
