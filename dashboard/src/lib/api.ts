/**
 * WakeDock API Client (Refactored)
 * 
 * This file now exports the new modular API client.
 * The original 920+ line implementation has been split into focused modules:
 * 
 * - BaseApiClient: Core HTTP functionality
 * - AuthService: Authentication handling
 * - ServicesApi: Docker services management  
 * - SystemApi: System information and health
 * - UsersApi: User management
 * 
 * For backward compatibility, all exports remain the same.
 */

// Export everything from the new modular API
export * from './api/index.js';

// The api singleton is still available as before
import { api } from './api/index.js';
export { api };

// Backward compatibility - these exports ensure existing imports continue to work
export { api as default };