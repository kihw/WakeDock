/**
 * Runtime Configuration API
 * Provides frontend configuration from environment variables
 */
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
  // Get environment variables at runtime
  const isDevelopment = process.env.NODE_ENV === 'development';

  // Get API URLs from environment (for debugging only)
  const publicApiUrl = process.env.PUBLIC_API_URL;
  const publicWsUrl = process.env.PUBLIC_WS_URL;

  console.log('📡 Config endpoint called:', { 
    isDevelopment, 
    publicApiUrl, 
    publicWsUrl,
    timestamp: new Date().toISOString()
  });

  // ALWAYS use relative URLs for internal Docker routing
  // This ensures proper internal service communication
  const config = {
    apiUrl: '/api/v1',  // Always use relative URL for internal routing
    wsUrl: '/ws',       // Always use relative URL for internal routing  
    isDevelopment: isDevelopment,
    enableDebug: process.env.PUBLIC_ENABLE_DEBUG === 'true' || isDevelopment,
  };

  console.log('✅ Returning config:', config);

  return json(config);
};