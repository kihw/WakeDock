/**
 * Enhanced E2E Tests for Service Management
 * Comprehensive end-to-end testing with real user workflows
 */

import { test, expect, type Page, type BrowserContext } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';

// Test data
const TEST_USER = {
    username: 'test@wakedock.local',
    password: 'testpassword123'
};

const TEST_SERVICE = {
    name: 'test-nginx',
    image: 'nginx:alpine',
    ports: [{ host: 8080, container: 80, protocol: 'tcp' }],
    environment: { ENV: 'test' },
    restart_policy: 'always'
};

// Helper functions
async function loginUser(page: Page) {
    await page.goto(`${BASE_URL}/login`);

    await page.fill('[data-testid="username-input"]', TEST_USER.username);
    await page.fill('[data-testid="password-input"]', TEST_USER.password);
    await page.click('[data-testid="login-button"]');

    // Wait for redirect to dashboard
    await page.waitForURL(`${BASE_URL}/`);
    await page.waitForSelector('[data-testid="dashboard-container"]');
}

async function waitForApiCall(page: Page, urlPattern: string | RegExp) {
    return page.waitForResponse(response =>
        response.url().match(urlPattern) && response.ok()
    );
}

async function mockApiResponse(page: Page, url: string, response: any) {
    await page.route(url, route =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(response)
        })
    );
}

test.describe('Service Management E2E', () => {
    test.beforeEach(async ({ page }) => {
        // Mock authentication
        await mockApiResponse(page, `${API_URL}/api/auth/login`, {
            access_token: 'mock-token',
            token_type: 'bearer',
            expires_in: 3600
        });

        await mockApiResponse(page, `${API_URL}/api/auth/me`, {
            id: 1,
            username: TEST_USER.username,
            email: TEST_USER.username,
            is_active: true,
            is_superuser: true
        });

        // Mock initial services list
        await mockApiResponse(page, `${API_URL}/api/services`, []);

        // Mock system overview
        await mockApiResponse(page, `${API_URL}/api/system/overview`, {
            services: { total: 0, running: 0, stopped: 0, error: 0 },
            system: { cpu_usage: 25.5, memory_usage: 45.2, disk_usage: 32.1, uptime: 86400 },
            docker: { version: '20.10.17', api_version: '1.41', status: 'healthy' },
            caddy: { version: '2.6.2', status: 'healthy', active_routes: 0 }
        });
    });

    test.describe('Service Creation', () => {
        test('should create a new service successfully', async ({ page }) => {
            await loginUser(page);

            // Navigate to service creation
            await page.click('[data-testid="services-nav-link"]');
            await page.waitForURL(`${BASE_URL}/services`);

            await page.click('[data-testid="new-service-button"]');
            await page.waitForURL(`${BASE_URL}/services/new`);

            // Fill service form
            await page.fill('[data-testid="service-name-input"]', TEST_SERVICE.name);
            await page.fill('[data-testid="service-image-input"]', TEST_SERVICE.image);

            // Add port mapping
            await page.click('[data-testid="add-port-button"]');
            await page.fill('[data-testid="port-host-input-0"]', TEST_SERVICE.ports[0].host.toString());
            await page.fill('[data-testid="port-container-input-0"]', TEST_SERVICE.ports[0].container.toString());

            // Add environment variable
            await page.click('[data-testid="add-env-button"]');
            await page.fill('[data-testid="env-key-input-0"]', 'ENV');
            await page.fill('[data-testid="env-value-input-0"]', 'test');

            // Mock service creation response
            const createdService = {
                id: 'service-1',
                ...TEST_SERVICE,
                status: 'creating',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };

            await mockApiResponse(page, `${API_URL}/api/services`, createdService);

            // Submit form
            const createPromise = waitForApiCall(page, `${API_URL}/api/services`);
            await page.click('[data-testid="create-service-button"]');
            await createPromise;

            // Should redirect to services list
            await page.waitForURL(`${BASE_URL}/services`);

            // Should show success notification
            await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
            await expect(page.locator('[data-testid="toast-success"]')).toContainText('Service created successfully');
        });

        test('should validate required fields', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services/new`);

            // Try to submit without required fields
            await page.click('[data-testid="create-service-button"]');

            // Should show validation errors
            await expect(page.locator('[data-testid="service-name-error"]')).toBeVisible();
            await expect(page.locator('[data-testid="service-image-error"]')).toBeVisible();
        });

        test('should handle API errors gracefully', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services/new`);

            // Fill valid form
            await page.fill('[data-testid="service-name-input"]', TEST_SERVICE.name);
            await page.fill('[data-testid="service-image-input"]', TEST_SERVICE.image);

            // Mock API error
            await page.route(`${API_URL}/api/services`, route =>
                route.fulfill({
                    status: 400,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        detail: 'Service name already exists'
                    })
                })
            );

            await page.click('[data-testid="create-service-button"]');

            // Should show error notification
            await expect(page.locator('[data-testid="toast-error"]')).toBeVisible();
            await expect(page.locator('[data-testid="toast-error"]')).toContainText('Service name already exists');
        });
    });

    test.describe('Service Management', () => {
        test.beforeEach(async ({ page }) => {
            // Mock services list with test service
            const mockServices = [{
                id: 'service-1',
                name: 'test-nginx',
                image: 'nginx:alpine',
                status: 'running',
                ports: [{ host: 8080, container: 80, protocol: 'tcp' }],
                environment: { ENV: 'test' },
                volumes: [],
                restart_policy: 'always',
                labels: {},
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z',
                health_status: 'healthy'
            }];

            await mockApiResponse(page, `${API_URL}/api/services`, mockServices);
        });

        test('should display services list', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services`);

            // Should display service card
            await expect(page.locator('[data-testid="service-card-service-1"]')).toBeVisible();
            await expect(page.locator('[data-testid="service-name-service-1"]')).toContainText('test-nginx');
            await expect(page.locator('[data-testid="service-status-service-1"]')).toContainText('running');
        });

        test('should start/stop service', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services`);

            // Mock service stop
            await page.route(`${API_URL}/api/services/service-1/stop`, route =>
                route.fulfill({ status: 200, body: '{}' })
            );

            const stopPromise = waitForApiCall(page, `${API_URL}/api/services/service-1/stop`);
            await page.click('[data-testid="stop-service-service-1"]');
            await stopPromise;

            // Should show success notification
            await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
        });

        test('should delete service with confirmation', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services`);

            // Click delete button
            await page.click('[data-testid="delete-service-service-1"]');

            // Should show confirmation dialog
            await expect(page.locator('[data-testid="confirm-dialog"]')).toBeVisible();
            await expect(page.locator('[data-testid="confirm-dialog"]')).toContainText('Are you sure');

            // Mock service deletion
            await page.route(`${API_URL}/api/services/service-1`, route =>
                route.fulfill({ status: 204 })
            );

            const deletePromise = waitForApiCall(page, `${API_URL}/api/services/service-1`);
            await page.click('[data-testid="confirm-delete-button"]');
            await deletePromise;

            // Should show success notification
            await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();

            // Service card should disappear
            await expect(page.locator('[data-testid="service-card-service-1"]')).not.toBeVisible();
        });

        test('should filter services', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services`);

            // Use search filter
            await page.fill('[data-testid="services-search-input"]', 'nginx');

            // Should show filtered results
            await expect(page.locator('[data-testid="service-card-service-1"]')).toBeVisible();

            // Search for non-existent service
            await page.fill('[data-testid="services-search-input"]', 'nonexistent');

            // Should show no results
            await expect(page.locator('[data-testid="service-card-service-1"]')).not.toBeVisible();
            await expect(page.locator('[data-testid="no-services-message"]')).toBeVisible();
        });
    });

    test.describe('Service Details', () => {
        test.beforeEach(async ({ page }) => {
            // Mock service details
            const mockService = {
                id: 'service-1',
                name: 'test-nginx',
                image: 'nginx:alpine',
                status: 'running',
                ports: [{ host: 8080, container: 80, protocol: 'tcp' }],
                environment: { ENV: 'test' },
                volumes: [],
                restart_policy: 'always',
                labels: {},
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z',
                health_status: 'healthy'
            };

            await mockApiResponse(page, `${API_URL}/api/services/service-1`, mockService);

            // Mock service logs
            await mockApiResponse(page, `${API_URL}/api/services/service-1/logs`, [
                {
                    id: 'log-1',
                    timestamp: '2023-01-01T12:00:00Z',
                    level: 'info',
                    message: 'Server started successfully'
                }
            ]);
        });

        test('should display service details', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services/service-1`);

            // Should display service information
            await expect(page.locator('[data-testid="service-name"]')).toContainText('test-nginx');
            await expect(page.locator('[data-testid="service-image"]')).toContainText('nginx:alpine');
            await expect(page.locator('[data-testid="service-status"]')).toContainText('running');

            // Should display port mappings
            await expect(page.locator('[data-testid="port-mapping-0"]')).toContainText('8080:80/tcp');

            // Should display environment variables
            await expect(page.locator('[data-testid="env-variable-ENV"]')).toContainText('test');
        });

        test('should display service logs', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services/service-1`);

            // Switch to logs tab
            await page.click('[data-testid="logs-tab"]');

            // Should display log entries
            await expect(page.locator('[data-testid="log-entry-log-1"]')).toBeVisible();
            await expect(page.locator('[data-testid="log-entry-log-1"]')).toContainText('Server started successfully');
        });

        test('should update service configuration', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services/service-1`);

            // Click edit button
            await page.click('[data-testid="edit-service-button"]');

            // Should enable edit mode
            await expect(page.locator('[data-testid="service-name-input"]')).toBeEditable();

            // Update service name
            await page.fill('[data-testid="service-name-input"]', 'updated-nginx');

            // Mock service update
            await page.route(`${API_URL}/api/services/service-1`, route =>
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        id: 'service-1',
                        name: 'updated-nginx',
                        image: 'nginx:alpine',
                        status: 'running'
                    })
                })
            );

            const updatePromise = waitForApiCall(page, `${API_URL}/api/services/service-1`);
            await page.click('[data-testid="save-service-button"]');
            await updatePromise;

            // Should show success notification
            await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();

            // Should display updated name
            await expect(page.locator('[data-testid="service-name"]')).toContainText('updated-nginx');
        });
    });

    test.describe('Real-time Updates', () => {
        test('should receive WebSocket updates', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services`);

            // Mock WebSocket connection
            await page.addInitScript(() => {
                class MockWebSocket {
                    constructor(url) {
                        this.url = url;
                        this.readyState = WebSocket.CONNECTING;
                        setTimeout(() => {
                            this.readyState = WebSocket.OPEN;
                            if (this.onopen) this.onopen({});
                        }, 100);
                    }

                    send(data) {
                        // Simulate sending
                    }

                    close() {
                        this.readyState = WebSocket.CLOSED;
                        if (this.onclose) this.onclose({});
                    }

                    // Helper to simulate receiving messages
                    simulateMessage(data) {
                        if (this.onmessage) {
                            this.onmessage({ data: JSON.stringify(data) });
                        }
                    }
                }

                window.WebSocket = MockWebSocket;
            });

            // Wait for WebSocket connection
            await page.waitForTimeout(200);

            // Simulate service status update
            await page.evaluate(() => {
                const ws = window.wsClient?.ws;
                if (ws && ws.simulateMessage) {
                    ws.simulateMessage({
                        type: 'service_update',
                        data: {
                            id: 'service-1',
                            status: 'stopped'
                        },
                        timestamp: new Date().toISOString()
                    });
                }
            });

            // Should update service status in real-time
            await expect(page.locator('[data-testid="service-status-service-1"]')).toContainText('stopped');
        });
    });

    test.describe('Accessibility', () => {
        test('should be keyboard navigable', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services`);

            // Tab through service actions
            await page.keyboard.press('Tab');
            await page.keyboard.press('Tab');
            await page.keyboard.press('Tab');

            // Should focus on service action button
            const focusedElement = await page.locator(':focus');
            await expect(focusedElement).toHaveAttribute('data-testid', /service-action/);

            // Should be able to activate with Enter
            await page.keyboard.press('Enter');
        });

        test('should have proper ARIA labels', async ({ page }) => {
            await loginUser(page);

            await page.goto(`${BASE_URL}/services`);

            // Check ARIA labels on service cards
            await expect(page.locator('[data-testid="service-card-service-1"]')).toHaveAttribute('aria-label');
            await expect(page.locator('[data-testid="start-service-service-1"]')).toHaveAttribute('aria-label');
            await expect(page.locator('[data-testid="stop-service-service-1"]')).toHaveAttribute('aria-label');
        });
    });

    test.describe('Performance', () => {
        test('should load services list quickly', async ({ page }) => {
            await loginUser(page);

            const startTime = Date.now();
            await page.goto(`${BASE_URL}/services`);

            // Wait for services to be loaded
            await page.waitForSelector('[data-testid="services-container"]');

            const loadTime = Date.now() - startTime;
            expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds
        });

        test('should handle large service lists', async ({ page }) => {
            // Mock large service list
            const largeServiceList = Array.from({ length: 100 }, (_, i) => ({
                id: `service-${i}`,
                name: `service-${i}`,
                image: 'nginx:alpine',
                status: 'running',
                ports: [],
                environment: {},
                volumes: [],
                restart_policy: 'always',
                labels: {},
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            }));

            await mockApiResponse(page, `${API_URL}/api/services`, largeServiceList);

            await loginUser(page);

            const startTime = Date.now();
            await page.goto(`${BASE_URL}/services`);

            // Should still load reasonably fast with many services
            await page.waitForSelector('[data-testid="services-container"]');

            const loadTime = Date.now() - startTime;
            expect(loadTime).toBeLessThan(5000); // Should load within 5 seconds even with 100 services
        });
    });
});

// Helper for visual regression testing
test.describe('Visual Regression', () => {
    test('services page layout', async ({ page }) => {
        await loginUser(page);
        await page.goto(`${BASE_URL}/services`);

        await page.waitForSelector('[data-testid="services-container"]');

        // Take screenshot for visual comparison
        await expect(page).toHaveScreenshot('services-page.png');
    });

    test('service creation form', async ({ page }) => {
        await loginUser(page);
        await page.goto(`${BASE_URL}/services/new`);

        await page.waitForSelector('[data-testid="service-form"]');

        // Take screenshot for visual comparison
        await expect(page).toHaveScreenshot('service-creation-form.png');
    });
});
