/**
 * Store Index
 * Exports all stores and related types
 */

// Re-export all stores
export { auth, isAuthenticated, isLoading as isAuthLoading } from './auth.js';
export {
  services,
  runningServices,
  stoppedServices,
  errorServices,
  serviceStats,
} from './services.js';
export {
  system,
  systemStats,
  dockerStatus,
  caddyStatus,
  servicesOverview,
  isSystemHealthy,
} from './system.js';
export { ui } from './ui.js';

// Re-export types
export type { Notification, Modal } from './ui.js';

// Combined store for common operations
import { auth } from './auth.js';
import { services } from './services.js';
import { system } from './system.js';
import { ui } from './ui.js';

export const stores = {
  auth,
  services,
  system,
  ui,
} as const;

// Initialize all stores
export const initializeStores = async () => {
  try {
    // Initialize theme
    ui.initTheme();

    // Initialize auth
    await auth.init();

    // Load initial system data
    await system.load();

    // Load services if authenticated
    const authState = await new Promise((resolve) => {
      const unsubscribe = auth.subscribe((state) => {
        unsubscribe();
        resolve(state);
      });
    });

    if ((authState as any).user) {
      await services.load();

      // Enable auto-refresh for system data
      system.enableAutoRefresh(30);
    }

    ui.showSuccess('WakeDock initialized successfully');
  } catch (error) {
    console.error('Store initialization failed:', error);
    ui.showError('Initialization failed', 'Some features may not work correctly');
  }
};
