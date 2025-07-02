/**
 * Route Constants
 * Centralized route definitions and navigation helpers
 */

// Base routes
export const ROUTES = {
  // Public routes
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',

  // Dashboard routes
  DASHBOARD: '/dashboard',

  // Service management
  SERVICES: '/services',
  SERVICES_NEW: '/services/new',
  SERVICE_DETAIL: (id: string) => `/services/${id}`,
  SERVICE_EDIT: (id: string) => `/services/${id}/edit`,
  SERVICE_LOGS: (id: string) => `/services/${id}/logs`,
  SERVICE_STATS: (id: string) => `/services/${id}/stats`,

  // Container management
  CONTAINERS: '/containers',
  CONTAINER_DETAIL: (id: string) => `/containers/${id}`,
  CONTAINER_LOGS: (id: string) => `/containers/${id}/logs`,
  CONTAINER_STATS: (id: string) => `/containers/${id}/stats`,
  CONTAINER_EXEC: (id: string) => `/containers/${id}/exec`,

  // Image management
  IMAGES: '/images',
  IMAGE_DETAIL: (id: string) => `/images/${id}`,
  IMAGE_BUILD: '/images/build',
  IMAGE_PULL: '/images/pull',

  // Network management
  NETWORKS: '/networks',
  NETWORKS_NEW: '/networks/new',
  NETWORK_DETAIL: (id: string) => `/networks/${id}`,

  // Volume management
  VOLUMES: '/volumes',
  VOLUMES_NEW: '/volumes/new',
  VOLUME_DETAIL: (id: string) => `/volumes/${id}`,

  // System management
  SYSTEM: '/system',
  SYSTEM_INFO: '/system/info',
  SYSTEM_EVENTS: '/system/events',
  SYSTEM_PRUNE: '/system/prune',

  // User management
  USERS: '/users',
  USERS_NEW: '/users/new',
  USER_DETAIL: (id: string) => `/users/${id}`,
  USER_EDIT: (id: string) => `/users/${id}/edit`,
  PROFILE: '/profile',

  // Analytics and monitoring
  ANALYTICS: '/analytics',
  MONITORING: '/monitoring',
  PERFORMANCE: '/analytics/performance',
  USAGE: '/analytics/usage',

  // Security
  SECURITY: '/security',
  AUDIT_LOGS: '/security/audit',
  VULNERABILITIES: '/security/vulnerabilities',
  POLICIES: '/security/policies',

  // Settings
  SETTINGS: '/settings',
  SETTINGS_GENERAL: '/settings/general',
  SETTINGS_DOCKER: '/settings/docker',
  SETTINGS_NOTIFICATIONS: '/settings/notifications',
  SETTINGS_SECURITY: '/settings/security',
  SETTINGS_BACKUP: '/settings/backup',

  // Health and status
  HEALTH: '/health',
  STATUS: '/status',

  // Help and documentation
  HELP: '/help',
  DOCS: '/docs',
  API_DOCS: '/docs/api',

  // Error pages
  NOT_FOUND: '/404',
  SERVER_ERROR: '/500',
  UNAUTHORIZED: '/401',
  FORBIDDEN: '/403',

  // Authentication
  LOGOUT: '/logout',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  VERIFY_EMAIL: '/verify-email',

  // API routes (for reference)
  API: {
    BASE: '/api/v1',
    AUTH: '/api/v1/auth',
    SERVICES: '/api/v1/services',
    CONTAINERS: '/api/v1/containers',
    IMAGES: '/api/v1/images',
    NETWORKS: '/api/v1/networks',
    VOLUMES: '/api/v1/volumes',
    SYSTEM: '/api/v1/system',
    USERS: '/api/v1/users',
    ANALYTICS: '/api/v1/analytics',
    SECURITY: '/api/v1/security',
    SETTINGS: '/api/v1/settings',
    HEALTH: '/api/v1/health',
  },
} as const;

// Route groups for navigation and permissions
export const ROUTE_GROUPS = {
  PUBLIC: [
    ROUTES.HOME,
    ROUTES.LOGIN,
    ROUTES.REGISTER,
    ROUTES.FORGOT_PASSWORD,
    ROUTES.RESET_PASSWORD,
    ROUTES.VERIFY_EMAIL,
  ],

  AUTHENTICATED: [ROUTES.DASHBOARD, ROUTES.PROFILE, ROUTES.LOGOUT],

  SERVICES: [ROUTES.SERVICES, ROUTES.SERVICES_NEW],

  CONTAINERS: [ROUTES.CONTAINERS],

  IMAGES: [ROUTES.IMAGES, ROUTES.IMAGE_BUILD, ROUTES.IMAGE_PULL],

  NETWORKS: [ROUTES.NETWORKS, ROUTES.NETWORKS_NEW],

  VOLUMES: [ROUTES.VOLUMES, ROUTES.VOLUMES_NEW],

  SYSTEM: [ROUTES.SYSTEM, ROUTES.SYSTEM_INFO, ROUTES.SYSTEM_EVENTS, ROUTES.SYSTEM_PRUNE],

  USERS: [ROUTES.USERS, ROUTES.USERS_NEW],

  ANALYTICS: [ROUTES.ANALYTICS, ROUTES.MONITORING, ROUTES.PERFORMANCE, ROUTES.USAGE],

  SECURITY: [ROUTES.SECURITY, ROUTES.AUDIT_LOGS, ROUTES.VULNERABILITIES, ROUTES.POLICIES],

  SETTINGS: [
    ROUTES.SETTINGS,
    ROUTES.SETTINGS_GENERAL,
    ROUTES.SETTINGS_DOCKER,
    ROUTES.SETTINGS_NOTIFICATIONS,
    ROUTES.SETTINGS_SECURITY,
    ROUTES.SETTINGS_BACKUP,
  ],

  ADMIN: [ROUTES.USERS, ROUTES.USERS_NEW, ROUTES.SECURITY, ROUTES.AUDIT_LOGS, ROUTES.SETTINGS],

  ERROR: [ROUTES.NOT_FOUND, ROUTES.SERVER_ERROR, ROUTES.UNAUTHORIZED, ROUTES.FORBIDDEN],
} as const;

// Navigation items with metadata
export const NAVIGATION_ITEMS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    route: ROUTES.DASHBOARD,
    icon: 'home',
    order: 1,
    group: 'main',
  },
  {
    id: 'services',
    label: 'Services',
    route: ROUTES.SERVICES,
    icon: 'layers',
    order: 2,
    group: 'docker',
    children: [
      {
        id: 'services-list',
        label: 'All Services',
        route: ROUTES.SERVICES,
        icon: 'list',
      },
      {
        id: 'services-new',
        label: 'Create Service',
        route: ROUTES.SERVICES_NEW,
        icon: 'plus',
      },
    ],
  },
  {
    id: 'containers',
    label: 'Containers',
    route: ROUTES.CONTAINERS,
    icon: 'box',
    order: 3,
    group: 'docker',
  },
  {
    id: 'images',
    label: 'Images',
    route: ROUTES.IMAGES,
    icon: 'disc',
    order: 4,
    group: 'docker',
    children: [
      {
        id: 'images-list',
        label: 'All Images',
        route: ROUTES.IMAGES,
        icon: 'list',
      },
      {
        id: 'images-pull',
        label: 'Pull Image',
        route: ROUTES.IMAGE_PULL,
        icon: 'download',
      },
      {
        id: 'images-build',
        label: 'Build Image',
        route: ROUTES.IMAGE_BUILD,
        icon: 'settings',
      },
    ],
  },
  {
    id: 'networks',
    label: 'Networks',
    route: ROUTES.NETWORKS,
    icon: 'network',
    order: 5,
    group: 'docker',
  },
  {
    id: 'volumes',
    label: 'Volumes',
    route: ROUTES.VOLUMES,
    icon: 'hard-drive',
    order: 6,
    group: 'docker',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    route: ROUTES.ANALYTICS,
    icon: 'bar-chart-3',
    order: 7,
    group: 'monitoring',
    children: [
      {
        id: 'analytics-overview',
        label: 'Overview',
        route: ROUTES.ANALYTICS,
        icon: 'trending-up',
      },
      {
        id: 'analytics-performance',
        label: 'Performance',
        route: ROUTES.PERFORMANCE,
        icon: 'activity',
      },
      {
        id: 'analytics-usage',
        label: 'Usage',
        route: ROUTES.USAGE,
        icon: 'pie-chart',
      },
    ],
  },
  {
    id: 'security',
    label: 'Security',
    route: ROUTES.SECURITY,
    icon: 'shield',
    order: 8,
    group: 'admin',
    requiredPermissions: ['security.read'],
  },
  {
    id: 'users',
    label: 'Users',
    route: ROUTES.USERS,
    icon: 'users',
    order: 9,
    group: 'admin',
    requiredPermissions: ['users.read'],
  },
  {
    id: 'system',
    label: 'System',
    route: ROUTES.SYSTEM,
    icon: 'cpu',
    order: 10,
    group: 'admin',
    requiredPermissions: ['system.read'],
  },
  {
    id: 'settings',
    label: 'Settings',
    route: ROUTES.SETTINGS,
    icon: 'settings',
    order: 11,
    group: 'admin',
  },
] as const;

// Breadcrumb configuration
export const BREADCRUMB_CONFIG = {
  [ROUTES.DASHBOARD]: [{ label: 'Dashboard', href: ROUTES.DASHBOARD }],
  [ROUTES.SERVICES]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Services', href: ROUTES.SERVICES },
  ],
  [ROUTES.SERVICES_NEW]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Services', href: ROUTES.SERVICES },
    { label: 'Create Service', href: ROUTES.SERVICES_NEW },
  ],
  [ROUTES.CONTAINERS]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Containers', href: ROUTES.CONTAINERS },
  ],
  [ROUTES.IMAGES]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Images', href: ROUTES.IMAGES },
  ],
  [ROUTES.NETWORKS]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Networks', href: ROUTES.NETWORKS },
  ],
  [ROUTES.VOLUMES]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Volumes', href: ROUTES.VOLUMES },
  ],
  [ROUTES.ANALYTICS]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Analytics', href: ROUTES.ANALYTICS },
  ],
  [ROUTES.SECURITY]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Security', href: ROUTES.SECURITY },
  ],
  [ROUTES.USERS]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Users', href: ROUTES.USERS },
  ],
  [ROUTES.SYSTEM]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'System', href: ROUTES.SYSTEM },
  ],
  [ROUTES.SETTINGS]: [
    { label: 'Dashboard', href: ROUTES.DASHBOARD },
    { label: 'Settings', href: ROUTES.SETTINGS },
  ],
} as const;

// Route permissions
export const ROUTE_PERMISSIONS = {
  [ROUTES.SERVICES]: ['services.read'],
  [ROUTES.SERVICES_NEW]: ['services.create'],
  [ROUTES.CONTAINERS]: ['containers.read'],
  [ROUTES.IMAGES]: ['images.read'],
  [ROUTES.NETWORKS]: ['networks.read'],
  [ROUTES.VOLUMES]: ['volumes.read'],
  [ROUTES.ANALYTICS]: ['analytics.read'],
  [ROUTES.SECURITY]: ['security.read'],
  [ROUTES.USERS]: ['users.read'],
  [ROUTES.USERS_NEW]: ['users.create'],
  [ROUTES.SYSTEM]: ['system.read'],
  [ROUTES.SETTINGS]: ['settings.read'],
} as const;

// Helper functions
export function isPublicRoute(route: string): boolean {
  return ROUTE_GROUPS.PUBLIC.includes(route as any);
}

export function requiresAuth(route: string): boolean {
  return !isPublicRoute(route);
}

export function getRoutePermissions(route: string): readonly string[] {
  return ROUTE_PERMISSIONS[route as keyof typeof ROUTE_PERMISSIONS] || [];
}

export function matchesRoute(current: string, target: string): boolean {
  if (current === target) return true;

  // Check for dynamic routes
  if (target.includes(':')) {
    const targetParts = target.split('/');
    const currentParts = current.split('/');

    if (targetParts.length !== currentParts.length) return false;

    return targetParts.every((part, index) => {
      return part.startsWith(':') || part === currentParts[index];
    });
  }

  return false;
}

export function buildRoute(template: string, params: Record<string, string>): string {
  let route = template;

  Object.entries(params).forEach(([key, value]) => {
    route = route.replace(`:${key}`, value);
  });

  return route;
}

export function parseRoute(route: string): { path: string; params: Record<string, string> } {
  const url = new URL(route, 'http://localhost');
  const searchParams = Object.fromEntries(url.searchParams.entries());

  return {
    path: url.pathname,
    params: searchParams,
  };
}

export function getRouteTitle(route: string): string {
  const navItem = NAVIGATION_ITEMS.find((item) => item.route === route);
  return navItem?.label || 'WakeDock';
}

export function getParentRoute(route: string): string | null {
  const parts = route.split('/').filter(Boolean);
  if (parts.length <= 1) return null;

  parts.pop();
  return '/' + parts.join('/');
}

export function isChildRoute(child: string, parent: string): boolean {
  return child.startsWith(parent) && child !== parent;
}

export type RouteKey = keyof typeof ROUTES;
export type RouteValue = (typeof ROUTES)[RouteKey];
export type NavigationItem = (typeof NAVIGATION_ITEMS)[number];
