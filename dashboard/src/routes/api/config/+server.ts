/**
 * Runtime Configuration API
 * Provides frontend configuration from environment variables
 */
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
  // Get environment variables at runtime
  const config = {
    apiUrl: process.env.PUBLIC_API_URL || process.env.WAKEDOCK_API_URL || 'http://195.201.199.226:8000',
    wsUrl: process.env.PUBLIC_WS_URL || process.env.WAKEDOCK_API_URL?.replace('http', 'ws') + '/ws' || 'ws://195.201.199.226:8000/ws',
    isDevelopment: process.env.NODE_ENV === 'development',
    enableDebug: process.env.PUBLIC_ENABLE_DEBUG === 'true' || process.env.NODE_ENV === 'development',
  };

  return json(config);
};