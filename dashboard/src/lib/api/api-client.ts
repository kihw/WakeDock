/**
 * Main API Client
 * Combines all API services into a single client
 */

import { AuthService } from './auth-service.js';
import { ServicesApi } from './services-api.js';
import { SystemApi } from './system-api.js';
import { UsersApi } from './users-api.js';

export class ApiClient {
  public auth: AuthService;
  public services: ServicesApi;
  public system: SystemApi;
  public users: UsersApi;

  constructor(baseUrl?: string) {
    this.auth = new AuthService(baseUrl);
    this.services = new ServicesApi(baseUrl);
    this.system = new SystemApi(baseUrl);
    this.users = new UsersApi(baseUrl);
  }

  /**
   * Set authentication token for all services
   */
  setToken(token: string): void {
    this.auth.setToken(token);
    this.services.setToken(token);
    this.system.setToken(token);
    this.users.setToken(token);
  }

  /**
   * Clear authentication token from all services
   */
  clearToken(): void {
    this.auth.clearToken();
    this.services.clearToken();
    this.system.clearToken();
    this.users.clearToken();
  }

  /**
   * Check if any service is authenticated
   */
  isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.auth.getToken();
  }

  // Legacy compatibility methods
  async getServices() {
    return this.services.getAll();
  }

  async getSystemOverview() {
    return this.system.getOverview();
  }

  async getHealth() {
    return this.system.getHealth();
  }

  async getService(id: string) {
    return this.services.getById(id);
  }

  async createService(service: any) {
    return this.services.create(service);
  }

  async updateService(service: any) {
    return this.services.update(service);
  }

  async deleteService(id: string) {
    return this.services.delete(id);
  }

  async startService(id: string) {
    return this.services.start(id);
  }

  async stopService(id: string) {
    return this.services.stop(id);
  }

  async restartService(id: string) {
    return this.services.restart(id);
  }

  async getServiceLogs(id: string, lines?: number) {
    return this.services.getLogs(id, lines);
  }

  // HTTP utility methods for backward compatibility
  async get<T>(path: string): Promise<{ ok: boolean; data?: T }> {
    try {
      const data = await this.system.request<T>(path, { method: 'GET' });
      return { ok: true, data };
    } catch (error) {
      console.error('GET request failed:', error);
      return { ok: false };
    }
  }

  async post<T>(path: string, body?: any): Promise<{ ok: boolean; data?: T }> {
    try {
      const data = await this.system.request<T>(path, {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined
      });
      return { ok: true, data };
    } catch (error) {
      console.error('POST request failed:', error);
      return { ok: false };
    }
  }
}