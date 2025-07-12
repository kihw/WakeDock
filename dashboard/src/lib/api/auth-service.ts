/**
 * Authentication Service
 * Handles login, logout, and user authentication
 */

import { API_ENDPOINTS } from '../config/api.js';
import { BaseApiClient } from './base-client.js';
import type { LoginRequest, LoginResponse, User } from '../types/api.js';

export class AuthService extends BaseApiClient {
  /**
   * Login user with credentials
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      body: JSON.stringify(credentials),
      skipAuth: true
    });

    this.setToken(response.access_token);
    return response;
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    this.clearToken();

    // Clear auth cache in service worker
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'CLEAR_AUTH_CACHE'
      });
    }
  }

  /**
   * Get current authenticated user - using direct fetch to avoid service worker issues
   */
  async getCurrentUser(): Promise<User> {
    await this.ensureInitialized();
    
    const response = await window.fetch(`${this.baseUrl}${API_ENDPOINTS.AUTH.ME}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      credentials: 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`Get current user failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>(API_ENDPOINTS.AUTH.REFRESH, {
      method: 'POST'
    });

    this.setToken(response.access_token);
    return response;
  }

  /**
   * Verify token validity
   */
  async verifyToken(): Promise<boolean> {
    if (!this.isAuthenticated()) {
      return false;
    }

    try {
      await this.getCurrentUser();
      return true;
    } catch {
      this.clearToken();
      return false;
    }
  }
}