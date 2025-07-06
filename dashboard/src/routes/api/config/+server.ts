/**
 * Runtime Configuration API
 * Provides frontend configuration from environment variables
 */
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
  // Get environment variables at runtime
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  // Get API URLs from environment or use relative URLs as fallback
  const publicApiUrl = process.env.PUBLIC_API_URL;
  const publicWsUrl = process.env.PUBLIC_WS_URL;

  // Configuration adapts to deployment environment
  const config = isDevelopment
    ? {
      apiUrl: '/api/v1',  // Development: use proxy from dev server
      wsUrl: '/ws',       // Development: use proxy from dev server
      isDevelopment: true,
      enableDebug: process.env.PUBLIC_ENABLE_DEBUG === 'true' || true,
    }
    : {
      // Production: prefer environment variables, fallback to relative URLs
      apiUrl: publicApiUrl ? `${publicApiUrl}/api/v1` : '/api/v1',
      wsUrl: publicWsUrl ? publicWsUrl.replace('http', 'ws') + '/ws' : '/ws',
      isDevelopment: false,
      enableDebug: process.env.PUBLIC_ENABLE_DEBUG === 'true' || false,
    };

  return json(config);
};