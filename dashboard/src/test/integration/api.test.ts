import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import { api } from '../../lib/api';

// Mock WebSocket for integration tests
vi.mock('$lib/websocket.js', () => ({
  websocketClient: {
    serviceUpdates: {
      subscribe: vi.fn(() => vi.fn()),
    },
    systemUpdates: {
      subscribe: vi.fn(() => vi.fn()),
    },
    logs: {
      subscribe: vi.fn(() => vi.fn()),
    },
  },
}));

describe('API Integration Tests', () => {
  beforeAll(() => {
    // Setup test environment
    // In a real scenario, you'd start a test server or use a test database
  });

  afterAll(() => {
    // Cleanup
  });

  describe('Authentication', () => {
    it('should login successfully with valid credentials', async () => {
      // Mock successful login response
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: { id: '1', username: 'testuser', email: 'test@example.com' },
          access_token: 'mock-jwt-token',
        }),
      });

      const response = await api.auth.login({
        username: 'testuser',
        password: 'password123',
      });

      expect(response.user.username).toBe('testuser');
      expect(response.access_token).toBe('mock-jwt-token');
    }, 10000);

    it('should fail login with invalid credentials', async () => {
      // Mock failed login response
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          message: 'Invalid credentials',
        }),
      });

      await expect(
        api.auth.login({
          username: 'testuser',
          password: 'wrongpassword',
        })
      ).rejects.toThrow();
    });

    it('should get current user when authenticated', async () => {
      // Mock successful user fetch
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'admin',
        }),
      });

      api.setToken('mock-jwt-token');
      const user = await api.auth.getCurrentUser();

      expect(user.username).toBe('testuser');
      expect(user.role).toBe('admin');
    }, 10000);
  });

  describe('Services Management', () => {
    beforeAll(() => {
      // Set up authenticated state
      api.setToken('mock-jwt-token');
    });

    it('should fetch all services', async () => {
      const mockServices = [
        {
          id: '1',
          name: 'nginx-proxy',
          subdomain: 'nginx',
          image: 'nginx:alpine',
          status: 'running',
          ports: [{ host: 80, container: 80, protocol: 'tcp' }],
          environment: {},
          volumes: [],
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
          health_status: 'healthy',
          restart_policy: 'always',
          labels: {},
        },
      ];

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockServices,
      });

      const services = await api.services.getAll();

      expect(services).toHaveLength(1);
      expect(services[0].name).toBe('nginx-proxy');
      expect(services[0].status).toBe('running');
    }, 10000);

    it('should get service by id', async () => {
      const mockService = {
        id: '1',
        name: 'nginx-proxy',
        subdomain: 'nginx',
        image: 'nginx:alpine',
        status: 'running',
        ports: [{ host: 80, container: 80, protocol: 'tcp' }],
        environment: {},
        volumes: [],
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        health_status: 'healthy',
        restart_policy: 'always',
        labels: {},
      };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockService,
      });

      const service = await api.services.getById('1');

      expect(service.id).toBe('1');
      expect(service.name).toBe('nginx-proxy');
    }, 10000);

    it('should start a service', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Service started' }),
      });

      await api.services.start('1');
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/services/1/start'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    }, 10000);

    it('should stop a service', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Service stopped' }),
      });

      await api.services.stop('1');
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/services/1/stop'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    }, 10000);

    it('should restart a service', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, message: 'Service restarted' }),
      });

      await api.services.restart('1');
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/services/1/restart'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    }, 10000);

    it('should get service logs', async () => {
      const mockLogs = [
        '2023-01-01T00:00:00Z INFO Starting nginx...',
        '2023-01-01T00:00:01Z INFO Server started successfully',
      ];

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ logs: mockLogs }),
      });

      const logs = await api.getServiceLogs('1', 100);

      expect(logs).toHaveLength(2);
      expect(logs[0]).toContain('Starting nginx');
    }, 10000);
  });

  describe('System Overview', () => {
    beforeAll(() => {
      api.setToken('mock-jwt-token');
    });

    it('should fetch system overview', async () => {
      const mockOverview = {
        services: { total: 5, running: 3, stopped: 2, error: 0 },
        system: {
          cpu_usage: 25.5,
          memory_usage: 60.2,
          disk_usage: 45.8,
          uptime: 123456,
        },
      };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockOverview,
      });

      const overview = await api.getSystemOverview();

      expect(overview.services.total).toBe(5);
      expect(overview.services.running).toBe(3);
      expect(overview.system.cpu_usage).toBe(25.5);
    }, 10000);
  });

  describe('User Management', () => {
    beforeAll(() => {
      api.setToken('mock-jwt-token');
    });

    it('should fetch all users', async () => {
      const mockUsers = [
        {
          id: '1',
          username: 'admin',
          email: 'admin@example.com',
          role: 'admin',
          created_at: '2023-01-01T00:00:00Z',
          last_login: '2023-01-02T00:00:00Z',
        },
        {
          id: '2',
          username: 'user',
          email: 'user@example.com',
          role: 'user',
          created_at: '2023-01-01T00:00:00Z',
          last_login: null,
        },
      ];

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsers,
      });

      const users = await api.users.getAll();

      expect(users).toHaveLength(2);
      expect(users[0].role).toBe('admin');
      expect(users[1].role).toBe('user');
    }, 10000);

    it('should create a new user', async () => {
      const newUser = {
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'password123',
        role: 'user' as const,
        active: true,
      };

      const mockCreatedUser = {
        id: '3',
        ...newUser,
        created_at: '2023-01-03T00:00:00Z',
        last_login: null,
      };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockCreatedUser,
      });

      const createdUser = await api.users.create(newUser);

      expect(createdUser.id).toBe('3');
      expect(createdUser.username).toBe('newuser');
      expect(createdUser.role).toBe('user');
    }, 10000);
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'));

      await expect(api.services.getAll()).rejects.toThrow('Network error');
    }, 10000);

    it('should handle HTTP errors', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          message: 'Internal server error',
        }),
      });

      await expect(api.services.getAll()).rejects.toThrow();
    }, 10000);

    it('should handle authentication errors', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          message: 'Unauthorized',
        }),
      });

      await expect(api.services.getAll()).rejects.toThrow();
    }, 10000);
  });
});
