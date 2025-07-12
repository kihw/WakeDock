/**
 * Token Management Service
 * Handles token storage, validation, and refresh logic
 */

export interface TokenPayload {
  sub: string;
  username: string;
  email: string;
  role: string;
  exp: number;
  iat: number;
  [key: string]: any;
}

export interface TokenInfo {
  payload: TokenPayload;
  isExpired: boolean;
  expiresAt: Date;
  needsRefresh: boolean;
}

class TokenService {
  private static instance: TokenService;
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly REFRESH_BUFFER_MINUTES = 5;

  private constructor() {}

  static getInstance(): TokenService {
    if (!TokenService.instance) {
      TokenService.instance = new TokenService();
    }
    return TokenService.instance;
  }

  // Store tokens
  setTokens(accessToken: string, refreshToken?: string): void {
    localStorage.setItem('wakedock_access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('wakedock_refresh_token', refreshToken);
    }
  }

  // Get access token
  getAccessToken(): string | null {
    return localStorage.getItem('wakedock_access_token');
  }

  // Get refresh token
  getRefreshToken(): string | null {
    return localStorage.getItem('wakedock_refresh_token');
  }

  // Clear all tokens
  clearTokens(): void {
    localStorage.removeItem('wakedock_access_token');
    localStorage.removeItem('wakedock_refresh_token');
    this.clearRefreshTimer();
  }

  // Decode JWT token
  decodeToken(token: string): TokenPayload | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('[TokenService] Error decoding token:', error);
      return null;
    }
  }

  // Get token information
  getTokenInfo(token?: string): TokenInfo | null {
    const accessToken = token || this.getAccessToken();
    if (!accessToken) return null;

    const payload = this.decodeToken(accessToken);
    if (!payload) return null;

    const now = Date.now() / 1000;
    const expiresAt = new Date(payload.exp * 1000);
    const isExpired = payload.exp < now;
    const needsRefresh = payload.exp < now + (this.REFRESH_BUFFER_MINUTES * 60);

    return {
      payload,
      isExpired,
      expiresAt,
      needsRefresh
    };
  }

  // Check if token is expired
  isTokenExpired(token?: string): boolean {
    const info = this.getTokenInfo(token);
    return info ? info.isExpired : true;
  }

  // Check if token needs refresh
  needsTokenRefresh(token?: string): boolean {
    const info = this.getTokenInfo(token);
    return info ? info.needsRefresh : true;
  }

  // Schedule automatic token refresh
  scheduleTokenRefresh(token: string, onRefresh: () => Promise<void>): void {
    this.clearRefreshTimer();

    const info = this.getTokenInfo(token);
    if (!info) return;

    const now = Date.now();
    const refreshTime = info.expiresAt.getTime() - (this.REFRESH_BUFFER_MINUTES * 60 * 1000);
    const timeUntilRefresh = refreshTime - now;

    if (timeUntilRefresh > 0) {
      this.refreshTimer = setTimeout(async () => {
        try {
          await onRefresh();
        } catch (error) {
          console.error('[TokenService] Automatic token refresh failed:', error);
        }
      }, timeUntilRefresh);
    }
  }

  // Clear refresh timer
  clearRefreshTimer(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  // Get user data from token
  getUserFromToken(token?: string): any {
    const info = this.getTokenInfo(token);
    if (!info) return null;

    return {
      id: parseInt(info.payload.sub),
      username: info.payload.username,
      email: info.payload.email,
      role: info.payload.role,
      // Add other fields as needed
    };
  }

  // Validate token format
  isValidTokenFormat(token: string): boolean {
    try {
      const parts = token.split('.');
      return parts.length === 3 && parts.every(part => part.length > 0);
    } catch {
      return false;
    }
  }

  // Get token expiration time
  getTokenExpiration(token?: string): Date | null {
    const info = this.getTokenInfo(token);
    return info ? info.expiresAt : null;
  }

  // Check if we have valid tokens
  hasValidTokens(): boolean {
    const accessToken = this.getAccessToken();
    if (!accessToken) return false;

    return !this.isTokenExpired(accessToken);
  }

  // Get token time until expiry in milliseconds
  getTimeUntilExpiry(token?: string): number {
    const info = this.getTokenInfo(token);
    if (!info) return 0;

    const now = Date.now();
    return Math.max(0, info.expiresAt.getTime() - now);
  }
}

export const tokenService = TokenService.getInstance();