/**
 * Authentication Store
 * Manages user authentication state
 */
import { writable, derived, get } from 'svelte/store';
import { api, type ApiError } from '../api.js';
import { type User, type LoginResponse as ApiLoginResponse } from '../types/user.js';

interface ExtendedLoginResponse extends ApiLoginResponse {
  refresh_token?: string;
  requiresTwoFactor?: boolean;
  twoFactorToken?: string;
}

interface LoginOptions {
  twoFactorCode?: string;
  rememberMe?: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
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
  isAuthenticated: false,
  isLoading: false,
  error: null,
  isRefreshing: false,
  lastActivity: null,
  sessionExpiry: null,
};

// Create the writable store
const { subscribe, set, update } = writable<AuthState>(initialState);

// Token refresh timeout
let refreshTimer: ReturnType<typeof setTimeout> | null = null;
let sessionTimer: ReturnType<typeof setTimeout> | null = null;

// Helper to decode JWT token
function decodeToken(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(function (c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
}

// Helper to check if token is expired
function isTokenExpired(token: string): boolean {
  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) return true;

  const now = Date.now() / 1000;
  // Check if token expires within 5 minutes
  return decoded.exp < now + 300;
}

// Helper to schedule token refresh
function scheduleTokenRefresh(token: string) {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
  }

  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) return;

  const now = Date.now() / 1000;
  const timeUntilRefresh = (decoded.exp - now - 300) * 1000; // Refresh 5 minutes before expiry

  if (timeUntilRefresh > 0) {
    refreshTimer = setTimeout(async () => {
      try {
        await auth.refreshToken();
      } catch (error) {
        console.error('Automatic token refresh failed:', error);
        await auth.logout();
      }
    }, timeUntilRefresh);
  }
}

// Helper to schedule session timeout
function scheduleSessionTimeout(expiryDate: Date) {
  if (sessionTimer) {
    clearTimeout(sessionTimer);
  }

  const now = Date.now();
  const timeUntilExpiry = expiryDate.getTime() - now;

  if (timeUntilExpiry > 0) {
    sessionTimer = setTimeout(async () => {
      console.warn('Session expired');
      await auth.logout();
    }, timeUntilExpiry);
  }
}

// Derived store for authentication status
export const isAuthenticated = derived(
  { subscribe },
  ($auth: AuthState) => $auth.user !== null && $auth.token !== null
);

// Derived store for loading state
export const isLoading = derived({ subscribe }, ($auth: AuthState) => $auth.isLoading);

// Auth store with methods
export const auth = {
  subscribe,

  // Initialize auth state from localStorage
  init: async () => {
    update((state: AuthState) => ({ ...state, isLoading: true, error: null }));

    try {
      const token = api.getToken();
      if (token) {
        const user = await api.auth.getCurrentUser();
        set({
          user,
          token,
          refreshToken: null, // TODO: récupérer depuis localStorage si disponible
          isAuthenticated: true,
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
          isAuthenticated: false,
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
        isAuthenticated: false,
        isLoading: false,
        error: null,
        isRefreshing: false,
        lastActivity: null,
        sessionExpiry: null,
      });
    }
  },

  // Login method
  login: async (
    emailOrUsername: string,
    password: string,
    options?: LoginOptions
  ): Promise<ExtendedLoginResponse | void> => {
    update((state: AuthState) => ({ ...state, isLoading: true, error: null }));

    try {
      const loginRequest = {
        username: emailOrUsername,
        password,
        twoFactorCode: options?.twoFactorCode,
        rememberMe: options?.rememberMe,
      };

      const response: ApiLoginResponse = await api.auth.login(loginRequest);

      // Check if 2FA is required (mock implementation - should come from API)
      const extendedResponse: ExtendedLoginResponse = {
        ...response,
        requiresTwoFactor: !options?.twoFactorCode && emailOrUsername === 'admin@wakedock.com', // Mock condition
      };

      // If 2FA is required and not provided, return the response without setting auth state
      if (extendedResponse.requiresTwoFactor && !options?.twoFactorCode) {
        update((state: AuthState) => ({
          ...state,
          isLoading: false,
          error: null,
        }));
        return extendedResponse;
      }

      // Get current user
      const user = await api.auth.getCurrentUser();

      // Calculate session expiry
      const decoded = decodeToken(response.access_token);
      const sessionExpiry = decoded?.exp ? new Date(decoded.exp * 1000) : null;

      // Set auth state
      const authState: AuthState = {
        user,
        token: response.access_token,
        refreshToken: extendedResponse.refresh_token || null,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        isRefreshing: false,
        lastActivity: new Date(),
        sessionExpiry,
      };

      set(authState);

      // Store refresh token if remember me is enabled
      if (options?.rememberMe && extendedResponse.refresh_token) {
        localStorage.setItem('wakedock_refresh_token', extendedResponse.refresh_token);
      }

      // Schedule token refresh
      scheduleTokenRefresh(response.access_token);

      // Schedule session timeout if applicable
      if (sessionExpiry && !options?.rememberMe) {
        scheduleSessionTimeout(sessionExpiry);
      }

      return extendedResponse;
    } catch (error) {
      const apiError = error as ApiError;
      update((state: AuthState) => ({
        ...state,
        isLoading: false,
        error: apiError.message || 'Login failed',
      }));
      throw error;
    }
  },

  // Logout method
  logout: async (): Promise<void> => {
    // Clear timers
    if (refreshTimer) {
      clearTimeout(refreshTimer);
      refreshTimer = null;
    }
    if (sessionTimer) {
      clearTimeout(sessionTimer);
      sessionTimer = null;
    }

    // Clear localStorage
    localStorage.removeItem('wakedock_refresh_token');
    localStorage.removeItem('auth_remember');
    localStorage.removeItem('auth_expiry');

    await api.auth.logout();
    set(initialState);
  },

  // Clear error
  clearError: () => {
    update((state: AuthState) => ({ ...state, error: null }));
  },

  // Update user info
  updateUser: (user: User) => {
    update((state: AuthState) => ({ ...state, user, lastActivity: new Date() }));
  },

  // Refresh token
  refreshToken: async (): Promise<boolean> => {
    const currentState = get({ subscribe });

    if (currentState.isRefreshing) {
      return false;
    }

    update((state: AuthState) => ({ ...state, isRefreshing: true }));

    try {
      // Try to get refresh token from localStorage or current state
      const refreshToken =
        currentState.refreshToken || localStorage.getItem('wakedock_refresh_token');

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      // Call API to refresh token
      const response = await api.auth.refreshToken();

      // Get updated user info
      const user = await api.auth.getCurrentUser();

      // Calculate new session expiry
      const decoded = decodeToken(response.access_token);
      const sessionExpiry = decoded?.exp ? new Date(decoded.exp * 1000) : null;

      // Update auth state
      update((state: AuthState) => ({
        ...state,
        user,
        token: response.access_token,
        isRefreshing: false,
        lastActivity: new Date(),
        sessionExpiry,
        error: null,
      }));

      // Schedule next refresh
      scheduleTokenRefresh(response.access_token);

      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);

      // If refresh fails, logout user
      update((state: AuthState) => ({
        ...state,
        isRefreshing: false,
        error: 'Session expired. Please login again.',
      }));

      // Auto logout after failed refresh
      setTimeout(() => auth.logout(), 1000);

      return false;
    }
  },

  // Update last activity
  updateActivity: () => {
    update((state: AuthState) => ({ ...state, lastActivity: new Date() }));
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
    return new Date().getTime() > state.sessionExpiry.getTime() - fiveMinutes;
  },

  // Verify token validity
  verifyToken: async (): Promise<boolean> => {
    try {
      const state = get({ subscribe });
      if (!state.token) return false;

      const user = await api.auth.getCurrentUser();
      if (user) {
        update((currentState: AuthState) => ({
          ...currentState,
          user,
          isAuthenticated: true,
          lastActivity: new Date(),
        }));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token verification failed:', error);
      await auth.logout();
      return false;
    }
  },
};

// Alias for compatibility
export const authStore = auth;
