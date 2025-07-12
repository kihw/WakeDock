/**
 * Services API
 * Handles Docker services management
 */

import { API_ENDPOINTS } from '../config/api.js';
import { BaseApiClient } from './base-client.js';
import type { 
  DockerService, 
  CreateServiceRequest, 
  UpdateServiceRequest,
  ServiceAction 
} from '../types/api.js';

export class ServicesApi extends BaseApiClient {
  /**
   * Get all services - using direct fetch to avoid service worker issues
   */
  async getAll(): Promise<DockerService[]> {
    await this.ensureInitialized();
    
    const response = await window.fetch(`${this.baseUrl}${API_ENDPOINTS.SERVICES.BASE}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      credentials: 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`Get services failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get service by ID
   */
  async getById(id: string): Promise<DockerService> {
    return this.request<DockerService>(API_ENDPOINTS.SERVICES.BY_ID(id));
  }

  /**
   * Create new service
   */
  async create(service: CreateServiceRequest): Promise<DockerService> {
    return this.request<DockerService>(API_ENDPOINTS.SERVICES.CREATE, {
      method: 'POST',
      body: JSON.stringify(service)
    });
  }

  /**
   * Update existing service
   */
  async update(service: UpdateServiceRequest): Promise<DockerService> {
    const { id, ...updateData } = service;
    return this.request<DockerService>(API_ENDPOINTS.SERVICES.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(updateData)
    });
  }

  /**
   * Delete service
   */
  async delete(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.DELETE(id), {
      method: 'DELETE'
    });
  }

  /**
   * Start service
   */
  async start(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.START(id), {
      method: 'POST'
    });
  }

  /**
   * Stop service
   */
  async stop(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.STOP(id), {
      method: 'POST'
    });
  }

  /**
   * Restart service
   */
  async restart(id: string): Promise<void> {
    return this.request<void>(API_ENDPOINTS.SERVICES.RESTART(id), {
      method: 'POST'
    });
  }

  /**
   * Get service logs
   */
  async getLogs(id: string, lines: number = 100): Promise<string[]> {
    const response = await this.request<{ logs: string[] }>(
      API_ENDPOINTS.SERVICES.LOGS(id, lines)
    );
    return response.logs;
  }

  /**
   * Execute action on service
   */
  async executeAction(id: string, action: ServiceAction): Promise<void> {
    return this.request<void>(`${API_ENDPOINTS.SERVICES.BASE}/${id}/action`, {
      method: 'POST',
      body: JSON.stringify(action)
    });
  }

  /**
   * Get service statistics
   */
  async getStats(id: string): Promise<any> {
    return this.request(`${API_ENDPOINTS.SERVICES.BASE}/${id}/stats`);
  }
}