/**
 * Authentication Store
 * Manages user authentication state using token service
 */
import { writable, derived, get } from 'svelte/store';
import { api, type ApiError } from '../api.js';
import { type User, type LoginResponse as ApiLoginResponse, type LoginRequest } from '../types/user.js';
import { tokenService } from '../services/token.js';
import { logger } from '../utils/logger.js';

interface ExtendedLoginResponse extends ApiLoginResponse {
  refresh_token?: string;
  requiresTwoFactor?: boolean;
  twoFactorToken?: string;
}

interface LoginOptions {
  rememberMe?: boolean;
  device?: string;
  fingerprint?: string;
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

// Session timeout timer
let sessionTimer: ReturnType<typeof setTimeout> | null = null;

// Helper to schedule session timeout
function scheduleSessionTimeout(expiryDate: Date) {
  if (sessionTimer) {
    clearTimeout(sessionTimer);
  }

  const timeUntilExpiry = expiryDate.getTime() - Date.now();

  if (timeUntilExpiry > 0) {
    sessionTimer = setTimeout(async () => {
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
      const token = tokenService.getAccessToken();
      if (token && !tokenService.isTokenExpired(token)) {
        const user = await api.auth.getCurrentUser();
        const tokenInfo = tokenService.getTokenInfo(token);
        
        set({
          user,
          token,
          refreshToken: tokenService.getRefreshToken(),
          isAuthenticated: true,
          isLoading: false,
          error: null,
          isRefreshing: false,
          lastActivity: new Date(),
          sessionExpiry: tokenInfo?.expiresAt || null,
        });

        // Schedule automatic token refresh
        tokenService.scheduleTokenRefresh(token, async () => {
          try {
            await auth.refreshToken();
          } catch (error) {
            console.error('Automatic token refresh failed:', error);
            await auth.logout();
          }
        });

        // Schedule session timeout
        if (tokenInfo?.expiresAt) {
          scheduleSessionTimeout(tokenInfo.expiresAt);
        }
      } else {
        // Clear invalid or expired token
        tokenService.clearTokens();
        set(initialState);
      }
    } catch (error) {
      logger.error('Auth initialization failed', error as Error);
      tokenService.clearTokens();
      await api.auth.logout();
      set(initialState);
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
      // Create clean login request with only required fields for API
      // Map usernameOrEmail to username for API compatibility
      const loginRequest: LoginRequest = {
        username: emailOrUsername, // Dashboard uses usernameOrEmail, API expects username
        password,
      };

      // Debug information for development
      logger.debug('Attempting login', { username: emailOrUsername, hasPassword: !!password });

      const response: ApiLoginResponse = await api.auth.login(loginRequest);

      // Store tokens using token service
      tokenService.setTokens(response.access_token, response.refresh_token);

      // No 2FA support in backend, continue with normal flow
      const extendedResponse: ExtendedLoginResponse = {
        ...response,
        requiresTwoFactor: false,
      };

      // Get current user with retry logic
      let user;
      try {
        user = await api.auth.getCurrentUser();
      } catch (userError) {
        logger.warn('getCurrentUser failed, using data from token', userError);
        // Fallback: extract user data from token
        const userData = tokenService.getUserFromToken(response.access_token);
        user = response.user || userData || null;
      }

      // Get token info
      const tokenInfo = tokenService.getTokenInfo(response.access_token);

      // Set auth state
      const authState: AuthState = {
        user,
        token: response.access_token,
        refreshToken: tokenService.getRefreshToken(),
        isAuthenticated: true,
        isLoading: false,
        error: null,
        isRefreshing: false,
        lastActivity: new Date(),
        sessionExpiry: tokenInfo?.expiresAt || null,
      };

      set(authState);

      // Schedule automatic token refresh
      tokenService.scheduleTokenRefresh(response.access_token, async () => {
        try {
          await auth.refreshToken();
        } catch (error) {
          logger.error('Automatic token refresh failed', error as Error);
          await auth.logout();
        }
      });

      // Schedule session timeout if applicable
      if (tokenInfo?.expiresAt) {
        scheduleSessionTimeout(tokenInfo.expiresAt);
      }

      return extendedResponse;
    } catch (error) {
      logger.error('Auth store login error', error as Error, {
        message: (error as any)?.message,
        status: (error as any)?.status,
        response: (error as any)?.response
      });

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
    tokenService.clearRefreshTimer();
    if (sessionTimer) {
      clearTimeout(sessionTimer);
      sessionTimer = null;
    }

    // Clear tokens
    tokenService.clearTokens();

    // Clear additional localStorage items
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
      const refreshToken = tokenService.getRefreshToken();

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      // Call API to refresh token
      const response = await api.auth.refreshToken();

      // Store new tokens
      tokenService.setTokens(response.access_token, response.refresh_token);

      // Get updated user info
      const user = await api.auth.getCurrentUser();

      // Get token info
      const tokenInfo = tokenService.getTokenInfo(response.access_token);

      // Update auth state
      update((state: AuthState) => ({
        ...state,
        user,
        token: response.access_token,
        refreshToken: tokenService.getRefreshToken(),
        isRefreshing: false,
        lastActivity: new Date(),
        sessionExpiry: tokenInfo?.expiresAt || null,
        error: null,
      }));

      // Schedule next refresh
      tokenService.scheduleTokenRefresh(response.access_token, async () => {
        try {
          await auth.refreshToken();
        } catch (error) {
          logger.error('Automatic token refresh failed', error as Error);
          await auth.logout();
        }
      });

      return true;
    } catch (error) {
      logger.error('Token refresh failed', error as Error);

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
    const token = tokenService.getAccessToken();
    return !token || tokenService.isTokenExpired(token);
  },

  // Check if token needs refresh
  needsTokenRefresh: (): boolean => {
    const token = tokenService.getAccessToken();
    return !token || tokenService.needsTokenRefresh(token);
  },

  // Verify token validity
  verifyToken: async (): Promise<boolean> => {
    try {
      const token = tokenService.getAccessToken();
      if (!token || tokenService.isTokenExpired(token)) {
        return false;
      }

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
      logger.error('Token verification failed', error as Error);
      await auth.logout();
      return false;
    }
  },
};

// Alias for compatibility
export const authStore = auth;
