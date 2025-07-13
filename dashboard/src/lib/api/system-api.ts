/**
 * System API
 * Handles system information and health checks
 */

import { API_ENDPOINTS } from '../config/api.js';
import { BaseApiClient } from './base-client.js';
import type { SystemInfo, SystemStats } from '../types/api.js';

export interface SystemOverview {
  services: {
    total: number;
    running: number;
    stopped: number;
    error: number;
  };
  system: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    uptime: number;
  };
  docker: {
    version: string;
    api_version: string;
    status: 'healthy' | 'unhealthy';
  };
  caddy: {
    version: string;
    status: 'healthy' | 'unhealthy';
    active_routes: number;
  };
}

export class SystemApi extends BaseApiClient {
  /**
   * Get system overview - using direct fetch to avoid service worker issues
   */
  async getOverview(): Promise<SystemOverview> {
    await this.ensureInitialized();
    
    const response = await window.fetch(`${this.baseUrl}${API_ENDPOINTS.SYSTEM.OVERVIEW}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      credentials: 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`Get system overview failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get detailed system information
   */
  async getInfo(): Promise<SystemInfo> {
    return this.request<SystemInfo>(API_ENDPOINTS.SYSTEM.INFO);
  }

  /**
   * Get system statistics
   */
  async getStats(): Promise<SystemStats> {
    return this.request<SystemStats>(API_ENDPOINTS.SYSTEM.STATS);
  }

  /**
   * Get system health check
   */
  async getHealth(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>(API_ENDPOINTS.SYSTEM.HEALTH);
  }

  /**
   * Get Docker information
   */
  async getDockerInfo(): Promise<any> {
    return this.request(`${API_ENDPOINTS.SYSTEM.BASE}/docker/info`);
  }

  /**
   * Get Docker version
   */
  async getDockerVersion(): Promise<any> {
    return this.request(`${API_ENDPOINTS.SYSTEM.BASE}/docker/version`);
  }

  /**
   * Get system events
   */
  async getEvents(since?: string, until?: string): Promise<any[]> {
    const params = new URLSearchParams();
    if (since) params.append('since', since);
    if (until) params.append('until', until);
    
    const query = params.toString();
    const url = `${API_ENDPOINTS.SYSTEM.BASE}/events${query ? `?${query}` : ''}`;
    
    return this.request<any[]>(url);
  }

  /**
   * Get resource usage metrics
   */
  async getResourceUsage(): Promise<any> {
    return this.request(`${API_ENDPOINTS.SYSTEM.BASE}/resources`);
  }

  /**
   * Get system settings
   */
  async getSettings(): Promise<any> {
    return this.request(`${API_ENDPOINTS.SYSTEM.BASE}/settings`);
  }

  /**
   * Update system settings
   */
  async updateSettings(settings: any): Promise<any> {
    return this.request(`${API_ENDPOINTS.SYSTEM.BASE}/settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}