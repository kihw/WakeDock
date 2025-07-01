/**
 * Test Factories
 * Provides factories for creating consistent test data
 */

/**
 * Create a mock service
 * @param overrides Properties to override in the default service
 */
export const createMockService = (overrides = {}) => ({
  id: 'service-1',
  name: 'test-service',
  status: 'running',
  image: 'docker/image:latest',
  ports: ['8080:80'],
  volumes: [],
  environment: {},
  created: new Date().toISOString(),
  updated: new Date().toISOString(),
  ...overrides
});

/**
 * Create a mock user
 * @param overrides Properties to override in the default user
 */
export const createMockUser = (overrides = {}) => ({
  id: 'user-1',
  username: 'testuser',
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  created: new Date().toISOString(),
  lastLogin: new Date().toISOString(),
  ...overrides
});

/**
 * Create a mock security event
 * @param overrides Properties to override in the default security event
 */
export const createMockSecurityEvent = (overrides = {}) => ({
  id: `event-${Date.now()}`,
  type: 'info',
  message: 'Test security event',
  timestamp: new Date().toISOString(),
  ipAddress: '127.0.0.1',
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  userId: 'user-1',
  ...overrides
});

/**
 * Create a mock audit log entry
 * @param overrides Properties to override in the default audit log
 */
export const createMockAuditLog = (overrides = {}) => ({
  id: `audit-${Date.now()}`,
  timestamp: new Date().toISOString(),
  category: 'authentication',
  action: 'login_success',
  status: 'success',
  targetResource: 'user',
  targetId: 'user-1',
  sourceIp: '127.0.0.1',
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  details: {},
  ...overrides
});

/**
 * Create multiple mock services
 * @param count Number of services to create
 * @param factory Factory function to use for creation
 */
export const createMany = (count: number, factory: (index: number) => any) => {
  return Array.from({ length: count }, (_, index) => factory(index));
};

/**
 * Create multiple mock services
 * @param count Number of services to create
 * @param overrides Properties to override in all services
 */
export const createMockServices = (count: number, overrides = {}) => {
  return createMany(count, (index) =>
    createMockService({
      id: `service-${index + 1}`,
      name: `test-service-${index + 1}`,
      ...overrides
    })
  );
};

/**
 * Create multiple mock audit logs
 * @param count Number of logs to create
 * @param overrides Properties to override in all logs
 */
export const createMockAuditLogs = (count: number, overrides = {}) => {
  return createMany(count, (index) =>
    createMockAuditLog({
      id: `audit-${index + 1}`,
      timestamp: new Date(Date.now() - index * 3600000).toISOString(),
      ...overrides
    })
  );
};
