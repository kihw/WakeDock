/**
 * Base API Client
 * Core HTTP client with authentication and request handling
 */

import { config } from '../config/environment.js';
import { API_ENDPOINTS } from '../config/api.js';
import type { ApiError } from '../types/api.js';

export interface RequestOptions extends RequestInit {
  timeout?: number;
  skipAuth?: boolean;
}

export class BaseApiClient {
  protected baseUrl: string;
  protected token: string | null = null;
  private _initialized: boolean = false;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl || config.apiUrl;
    this.baseUrl = this.baseUrl.replace(/\/$/, '');

    // Load token from localStorage
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem(config.tokenKey);
    }
  }

  /**
   * Initialize client with runtime configuration
   */
  protected async ensureInitialized(): Promise<void> {
    if (this._initialized) return;

    try {
      const response = await window.fetch('/api/config', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        cache: 'no-cache'
      });

      if (response.ok) {
        const runtimeConfig = await response.json();
        const newBaseUrl = (runtimeConfig.apiUrl || '/api/v1').replace(/\/$/, '');
        if (newBaseUrl !== this.baseUrl) {
          this.baseUrl = newBaseUrl;
        }
      }
    } catch (error) {
      console.warn('Failed to load runtime config, using defaults:', error);
    }

    this._initialized = true;
  }

  /**
   * Core request method with simplified error handling
   */
  public async request<T>(
    path: string,
    options: RequestOptions = {}
  ): Promise<T> {
    await this.ensureInitialized();

    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };

    // Add authorization header if token exists and not skipped
    if (this.token && !options.skipAuth) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    // Merge with provided headers
    if (options.headers) {
      Object.assign(headers, options.headers);
    }

    try {
      const response = await window.fetch(url, {
        ...options,
        headers,
        credentials: 'same-origin'
      });

      if (!response.ok) {
        const errorData = await this.parseErrorResponse(response);
        throw this.createApiError(errorData, response.status);
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }

      return {} as T;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw this.createApiError({
          message: 'Network error - please check your connection'
        }, 503);
      }
      throw error;
    }
  }

  /**
   * Parse error response from API
   */
  private async parseErrorResponse(response: Response): Promise<any> {
    try {
      return await response.json();
    } catch {
      return { message: response.statusText };
    }
  }

  /**
   * Create standardized API error
   */
  private createApiError(errorData: any, status: number): ApiError {
    return {
      message: errorData.detail || errorData.message || 'An error occurred',
      code: errorData.code,
      details: { ...errorData, status }
    };
  }

  /**
   * Set authentication token
   */
  public setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem(config.tokenKey, token);
    }
  }

  /**
   * Clear authentication token
   */
  public clearToken(): void {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem(config.tokenKey);
    }
  }

  /**
   * Check if client is authenticated
   */
  public isAuthenticated(): boolean {
    return this.token !== null;
  }

  /**
   * Get current token
   */
  public getToken(): string | null {
    return this.token;
  }
}