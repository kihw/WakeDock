/**
 * Users API
 * Handles user management operations
 */

import { API_ENDPOINTS } from '../config/api.js';
import { BaseApiClient } from './base-client.js';
import type { User, CreateUserRequest, UpdateUserRequest } from '../types/api.js';

export class UsersApi extends BaseApiClient {
  /**
   * Get all users
   */
  async getAll(): Promise<User[]> {
    return this.request<User[]>(API_ENDPOINTS.USERS.BASE);
  }

  /**
   * Get user by ID
   */
  async getById(id: number): Promise<User> {
    return this.request<User>(API_ENDPOINTS.USERS.BY_ID(id));
  }

  /**
   * Create new user
   */
  async create(userData: CreateUserRequest): Promise<User> {
    return this.request<User>(API_ENDPOINTS.USERS.CREATE, {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  /**
   * Update existing user
   */
  async update(id: number, userData: UpdateUserRequest): Promise<User> {
    return this.request<User>(API_ENDPOINTS.USERS.UPDATE(id), {
      method: 'PUT',
      body: JSON.stringify(userData)
    });
  }

  /**
   * Delete user
   */
  async delete(id: number): Promise<void> {
    return this.request<void>(API_ENDPOINTS.USERS.DELETE(id), {
      method: 'DELETE'
    });
  }

  /**
   * Change user password
   */
  async changePassword(id: number, oldPassword: string, newPassword: string): Promise<void> {
    return this.request<void>(`${API_ENDPOINTS.USERS.BASE}/${id}/password`, {
      method: 'PUT',
      body: JSON.stringify({ oldPassword, newPassword })
    });
  }

  /**
   * Update user permissions
   */
  async updatePermissions(id: number, permissions: string[]): Promise<User> {
    return this.request<User>(`${API_ENDPOINTS.USERS.BASE}/${id}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({ permissions })
    });
  }

  /**
   * Enable/disable user
   */
  async setEnabled(id: number, enabled: boolean): Promise<User> {
    return this.request<User>(`${API_ENDPOINTS.USERS.BASE}/${id}/enabled`, {
      method: 'PUT',
      body: JSON.stringify({ enabled })
    });
  }
}