import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Dashboard from './+page.svelte';
import { auth } from '$lib/stores/auth.js';
import { api } from '$lib/api.js';

// Mock the API
vi.mock('$lib/api.js', () => ({
  api: {
    isAuthenticated: vi.fn(() => true),
    services: {
      getAll: vi.fn(() => Promise.resolve([
        {
          id: '1',
          name: 'test-service',
          image: 'nginx:alpine',
          status: 'running',
          ports: [{ host: 80, container: 80, protocol: 'tcp' }],
          environment: {},
          volumes: [],
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
          health_status: 'healthy',
          restart_policy: 'always',
          labels: {}
        }
      ]))
    },
    getSystemOverview: vi.fn(() => Promise.resolve({
      services: { total: 1, running: 1, stopped: 0, error: 0 },
      system: { cpu_usage: 25, memory_usage: 50, disk_usage: 30, uptime: 12345 }
    })),
    startService: vi.fn(() => Promise.resolve()),
    stopService: vi.fn(() => Promise.resolve())
  }
}));

// Mock WebSocket client
vi.mock('$lib/websocket.js', () => ({
  websocketClient: {
    serviceUpdates: {
      subscribe: vi.fn(() => vi.fn())
    },
    systemUpdates: {
      subscribe: vi.fn(() => vi.fn())
    }
  }
}));

// Mock auth store with authenticated user
vi.mock('$lib/stores/auth.js', () => ({
  auth: {
    subscribe: vi.fn(),
    user: { id: '1', username: 'testuser', email: 'test@example.com' }
  }
}));

// Mock navigation
vi.mock('$app/navigation', () => ({
  goto: vi.fn()
}));

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard title', async () => {
    render(Dashboard);

    await waitFor(() => {
      expect(screen.getByText('WakeDock Dashboard')).toBeInTheDocument();
    });
  });

  it('loads and displays services', async () => {
    render(Dashboard);

    await waitFor(() => {
      expect(api.services.getAll).toHaveBeenCalled();
    });
  });

  it('loads system overview', async () => {
    render(Dashboard);

    await waitFor(() => {
      expect(api.getSystemOverview).toHaveBeenCalled();
    });
  });

  it('displays service stats', async () => {
    render(Dashboard);

    await waitFor(() => {
      expect(screen.getByText('Total Services')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  it('handles search functionality', async () => {
    const { component } = render(Dashboard);

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/search services/i);
      expect(searchInput).toBeInTheDocument();
    });
  });

  it('handles status filtering', async () => {
    render(Dashboard);

    await waitFor(() => {
      expect(screen.getByText('All Services')).toBeInTheDocument();
    });
  });

  it('displays error state when API fails', async () => {
    // Mock API failure
    vi.mocked(api.services.getAll).mockRejectedValueOnce(new Error('API Error'));

    render(Dashboard);

    await waitFor(() => {
      expect(screen.getByText(/Unable to connect to WakeDock API/)).toBeInTheDocument();
    });
  });
});
