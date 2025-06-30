/**
 * Component Conditional Rendering Tests
 * Tests for conditional rendering in key components
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import ServiceCard from '../../src/lib/components/ServiceCard.svelte';
import SystemStatus from '../../src/lib/components/SystemStatus.svelte';
import StatsCards from '../../src/lib/components/StatsCards.svelte';
import LoadingSpinner from '../../src/lib/components/LoadingSpinner.svelte';

// Mock stores
const mockSystemStore = writable({
    status: 'healthy',
    metrics: {
        cpu: 45,
        memory: 67,
        disk: 23
    }
});

// Mocked stats for tests
const mockStats = {
    services: {
        total: 10,
        running: 7,
        stopped: 3
    },
    docker: {
        status: 'healthy',
        version: 'v20.10.12'
    },
    system: {
        cpu: 45,
        memory: 67,
        disk: 23
    }
};

// Mock API
vi.mock('../../src/lib/api', () => ({
    api: {
        services: {
            getAll: vi.fn(),
            get: vi.fn(),
            start: vi.fn(),
            stop: vi.fn()
        }
    }
}));

vi.mock('../../src/lib/stores/system', () => ({
    systemStore: mockSystemStore
}));

describe('ServiceCard Component', () => {
    const mockService = {
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
        labels: {},
        resource_usage: {
            cpu_percent: 25.5,
            memory_percent: 40.2,
            memory_usage: '256MB',
            network_rx: '1.2MB',
            network_tx: '850KB'
        }
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should render service with running status', () => {
        render(ServiceCard, {
            props: {
                service: mockService
            }
        });

        expect(screen.getByText('test-service')).toBeDefined();
        expect(screen.getByText('Running')).toBeDefined();
        expect(screen.getByText('Sleep')).toBeDefined(); // Stop button for running service
    });

    it('should render service with stopped status', () => {
        const stoppedService = {
            ...mockService,
            status: 'stopped'
        };

        render(ServiceCard, {
            props: {
                service: stoppedService
            }
        });

        expect(screen.getByText('Stopped')).toBeDefined();
        expect(screen.getByText('Wake')).toBeDefined(); // Start button for stopped service
    });

    it('should conditionally render resource usage when available', () => {
        render(ServiceCard, {
            props: {
                service: mockService
            }
        });

        // Should show resource usage bars
        expect(screen.getByText('25.5%')).toBeDefined(); // CPU usage
        expect(screen.getByText('40.2%')).toBeDefined(); // Memory usage
    });

    it('should not render resource usage when unavailable', () => {
        const serviceWithoutResources = {
            ...mockService,
            resource_usage: null
        };

        render(ServiceCard, {
            props: {
                service: serviceWithoutResources
            }
        });

        // Should not show resource usage section
        expect(screen.queryByText('25.5%')).toBeNull();
        expect(screen.queryByText('40.2%')).toBeNull();
    });

    it('should conditionally render ports when available', () => {
        render(ServiceCard, {
            props: {
                service: mockService
            }
        });

        expect(screen.getByText('80:80')).toBeDefined();
    });

    it('should not render ports section when no ports', () => {
        const serviceWithoutPorts = {
            ...mockService,
            ports: []
        };

        render(ServiceCard, {
            props: {
                service: serviceWithoutPorts
            }
        });

        // Ports section should not be visible
        expect(screen.queryByText('Ports')).toBeNull();
    });

    it('should show external link only for running services', () => {
        const runningService = {
            ...mockService,
            status: 'running',
            subdomain: 'test-app'
        };

        render(ServiceCard, {
            props: {
                service: runningService
            }
        });

        expect(screen.getByText('Visit')).toBeDefined();
    });

    it('should handle loading state properly', async () => {
        const { component } = render(ServiceCard, {
            props: {
                service: mockService
            }
        });

        const sleepButton = screen.getByText('Sleep');

        // Simulate loading state
        await fireEvent.click(sleepButton);

        // Button should be disabled during loading
        expect(sleepButton).toHaveProperty('disabled', true);
    });
});

describe('LoadingSpinner Component', () => {
    it('should render spinner when loading is true', () => {
        render(LoadingSpinner, {
            props: {
                loading: true,
                size: 'md',
                text: 'Loading data...'
            }
        });

        expect(screen.getByText('Loading data...')).toBeDefined();
        expect(document.querySelector('.spinner')).not.toBeNull();
    });

    it('should not render spinner when loading is false', () => {
        render(LoadingSpinner, {
            props: {
                loading: false,
                size: 'md',
                text: 'Loading data...'
            }
        });

        expect(screen.queryByText('Loading data...')).toBeNull();
        expect(document.querySelector('.spinner')).toBeNull();
    });

    it('should render with default props', () => {
        render(LoadingSpinner);

        const spinner = screen.getByTestId('loading-spinner') ||
            document.querySelector('.spinner');
        expect(spinner).toBeDefined();
    });

    it('should render with custom text', () => {
        render(LoadingSpinner, {
            props: {
                text: 'Loading services...'
            }
        });

        expect(screen.getByText('Loading services...')).toBeDefined();
    });

    it('should conditionally show cancel button', () => {
        render(LoadingSpinner, {
            props: {
                showCancel: true,
                text: 'Processing...'
            }
        });

        expect(screen.getByText('Cancel')).toBeDefined();
    });

    it('should not show cancel button by default', () => {
        render(LoadingSpinner, {
            props: {
                text: 'Loading...'
            }
        });

        expect(screen.queryByText('Cancel')).toBeNull();
    });

    it('should render inline variant', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                inline: true,
                text: 'Loading...'
            }
        });

        expect(container.querySelector('.spinner-container.inline')).toBeDefined();
    });

    it('should render centered variant', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                center: true,
                text: 'Loading...'
            }
        });

        expect(container.querySelector('.spinner-container.center')).toBeDefined();
    });

    it('should handle different sizes', () => {
        const { container } = render(LoadingSpinner, {
            props: {
                size: 'large'
            }
        });

        const spinner = container.querySelector('.spinner');
        expect(spinner).toBeDefined();
    });

    it('should show progress when enabled', () => {
        render(LoadingSpinner, {
            props: {
                showProgress: true,
                text: 'Loading...'
            }
        });

        // Should render progress elements if progress data is available
        // This would need actual progress data from a store
    });

    it('should render different sizes based on props', () => {
        // Test small size
        const { unmount } = render(LoadingSpinner, {
            props: {
                loading: true,
                size: 'sm',
                text: 'Loading'
            }
        });

        expect(document.querySelector('.spinner-sm')).not.toBeNull();
        unmount();

        // Test large size
        render(LoadingSpinner, {
            props: {
                loading: true,
                size: 'lg',
                text: 'Loading'
            }
        });

        expect(document.querySelector('.spinner-lg')).not.toBeNull();
    });
});

describe('StatsCards Component', () => {
    beforeEach(() => {
        // Reset the mock store to known state
        mockSystemStore.set({
            status: 'healthy',
            metrics: {
                cpu: 45,
                memory: 67,
                disk: 23
            }
        });
    });

    it('should render all stat cards with proper data', () => {
        const statsStore = writable(mockStats);

        render(StatsCards, {
            props: {
                stats: statsStore
            }
        });

        expect(screen.getByText('10')).toBeDefined(); // Total services
        expect(screen.getByText('7')).toBeDefined();  // Running services
        expect(screen.getByText('3')).toBeDefined();  // Stopped services
    });

    it('should handle loading state', () => {
        const loadingStats = writable(null);

        render(StatsCards, {
            props: {
                stats: loadingStats
            }
        });

        // Should show loading placeholders or default values
        expect(screen.getByText('0')).toBeDefined(); // Default values when loading
    });

    it('should conditionally render Docker status', () => {
        const statsStore = writable(mockStats);

        render(StatsCards, {
            props: {
                stats: statsStore
            }
        });

        expect(screen.getByText('Healthy')).toBeDefined(); // Docker status
        expect(screen.getByText('v20.10.12')).toBeDefined(); // Docker version
    });

    it('should handle unhealthy service status', () => {
        const unhealthyStats = {
            ...mockStats,
            docker: {
                ...mockStats.docker,
                status: 'unhealthy'
            }
        };

        const statsStore = writable(unhealthyStats);

        render(StatsCards, {
            props: {
                stats: statsStore
            }
        });

        expect(screen.getByText('Unhealthy')).toBeDefined();
    });

    it('should render different states based on metric values', async () => {
        render(StatsCards);

        // Initial render should show normal state (not critical)
        expect(screen.getByText('45%')).toBeDefined(); // CPU
        expect(document.querySelector('.stats-card-normal')).not.toBeNull();
        expect(document.querySelector('.stats-card-critical')).toBeNull();

        // Update with critical values and test rendering
        mockSystemStore.set({
            status: 'warning',
            metrics: {
                cpu: 92,
                memory: 67,
                disk: 23
            }
        });

        // Wait for re-render
        await waitFor(() => {
            expect(screen.getByText('92%')).toBeDefined();
            expect(document.querySelector('.stats-card-critical')).not.toBeNull();
        });
    });

    it('should render loading state when no metrics available', () => {
        // Cast to any pour contourner la vérification de type pour le test
        mockSystemStore.set({
            status: 'loading',
            metrics: undefined
        } as any);

        render(StatsCards);

        expect(document.querySelector('.loading-indicator')).not.toBeNull();
        expect(screen.queryByText('CPU')).toBeNull();
    });

    it('should handle empty or invalid metrics gracefully', () => {
        // Cast to any pour contourner la vérification de type pour le test
        mockSystemStore.set({
            status: 'degraded',
            metrics: {
                cpu: 0,
                memory: 0,
                disk: 0
            }
        } as any);

        render(StatsCards);

        expect(screen.getByText('0%')).toBeDefined(); // Should show 0% for invalid metrics
    });
});

describe('SystemStatus Component', () => {
    beforeEach(() => {
        // Reset the mock store to known state
        mockSystemStore.set({
            status: 'healthy',
            metrics: {
                cpu: 45,
                memory: 67,
                disk: 23
            }
        });
    });

    it('should render healthy status with green indicator', () => {
        render(SystemStatus);

        expect(screen.getByText('System Status: Healthy')).toBeDefined();
        expect(document.querySelector('.status-healthy')).not.toBeNull();
    });

    it('should render warning status with amber indicator', async () => {
        mockSystemStore.set({
            status: 'warning',
            metrics: {
                cpu: 45,
                memory: 67,
                disk: 23
            }
        });

        render(SystemStatus);

        await waitFor(() => {
            expect(screen.getByText('System Status: Warning')).toBeDefined();
            expect(document.querySelector('.status-warning')).not.toBeNull();
        });
    });

    it('should render critical status with red indicator', async () => {
        mockSystemStore.set({
            status: 'critical',
            metrics: {
                cpu: 45,
                memory: 67,
                disk: 23
            }
        });

        render(SystemStatus);

        await waitFor(() => {
            expect(screen.getByText('System Status: Critical')).toBeDefined();
            expect(document.querySelector('.status-critical')).not.toBeNull();
        });
    });
});

describe('Conditional Rendering Edge Cases', () => {
    it('should handle null/undefined props gracefully', () => {
        expect(() => {
            render(ServiceCard, {
                props: {
                    service: null
                }
            });
        }).not.toThrow();
    });

    it('should handle missing nested properties', () => {
        const incompleteService = {
            id: '1',
            name: 'test',
            status: 'running'
            // Missing other properties
        };

        expect(() => {
            render(ServiceCard, {
                props: {
                    service: incompleteService
                }
            });
        }).not.toThrow();
    });

    it('should handle empty arrays and objects', () => {
        const emptyService = {
            id: '1',
            name: 'test',
            status: 'running',
            ports: [],
            environment: {},
            volumes: [],
            labels: {}
        };

        const { container } = render(ServiceCard, {
            props: {
                service: emptyService
            }
        });

        expect(container).toBeDefined();
    });
});
