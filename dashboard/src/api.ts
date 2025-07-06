// Simplified API client - use main api.ts from lib instead
import { api as mainApi } from './lib/api.js';

// Re-export the main API client for backward compatibility
export const api = mainApi;
export { ApiError } from './lib/api.js';

// This file now acts as a compatibility layer
// All functionality is provided by ./lib/api.ts
