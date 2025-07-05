import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { auth } from './auth';

// Mock the API module completely
vi.mock('../api', () => ({
  api: {
    auth: {
      login: vi.fn(),
      logout: vi.fn(),
      getCurrentUser: vi.fn(),
    },
    getToken: vi.fn(),
  },
}));

// Import after mocking
const { api } = await import('../api');

describe('Auth Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should initialize with default state', () => {
    const state = get(auth);

    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should handle successful login', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'user' as const,
      roles: ['user'],
      permissions: ['service:read'],
      active: true,
      isActive: true,
      lastLogin: undefined,
      last_login: undefined,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      createdAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
    };

    const mockResponse = {
      user: mockUser,
      access_token: 'test-token',
      token_type: 'Bearer',
      expires_in: 3600,
    };

    vi.mocked(api.auth.login).mockResolvedValue(mockResponse);
    vi.mocked(api.auth.getCurrentUser).mockResolvedValue(mockUser);

    await auth.login('testuser', 'password');

    const state = get(auth);
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe('test-token'); // The store should extract access_token and store as token
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should handle login error', async () => {
    const error = new Error('Invalid credentials');
    vi.mocked(api.auth.login).mockRejectedValue(error);

    await expect(auth.login('wrong', 'wrong')).rejects.toThrow('Invalid credentials');

    const state = get(auth);
    expect(state.user).toBeFalsy();
    expect(state.token).toBeFalsy();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Invalid credentials');
  });

  it('should handle logout', async () => {
    // First login to set some state
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'user' as const,
      roles: ['user'],
      permissions: ['service:read'],
      active: true,
      isActive: true,
      lastLogin: undefined,
      last_login: undefined,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      createdAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
    };

    const mockResponse = {
      user: mockUser,
      access_token: 'test-token',
      token_type: 'Bearer',
      expires_in: 3600,
    };

    vi.mocked(api.auth.login).mockResolvedValue(mockResponse);
    await auth.login('testuser', 'password');

    // Mock logout
    vi.mocked(api.auth.logout).mockResolvedValue(undefined);

    await auth.logout();

    const state = get(auth);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should clear errors', () => {
    // Set an error first
    const state = get(auth);
    auth.clearError();

    const newState = get(auth);
    expect(newState.error).toBeNull();
  });

  it('should update user info', () => {
    const mockUser = {
      id: 1,
      username: 'updateduser',
      email: 'updated@example.com',
      firstName: 'Updated',
      lastName: 'User',
      role: 'admin' as const,
      roles: ['admin'],
      permissions: ['service:read', 'service:write'],
      active: true,
      isActive: true,
      lastLogin: undefined,
      last_login: undefined,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      createdAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
    };

    auth.updateUser(mockUser);

    const state = get(auth);
    expect(state.user).toEqual(mockUser);
  });
});
