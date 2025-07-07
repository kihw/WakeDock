/**
 * Server Hooks
 * Handle authentication and security on the server side
 */
import type { Handle, RequestEvent } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { authMiddleware } from './lib/middleware/auth.js';
import { errorMiddleware } from './lib/middleware/error.js';

/**
 * Authentication hook
 */
const authHandle: Handle = async ({ event, resolve }) => {
  // Apply authentication middleware for protected routes
  const protectedRoutes = ['/services', '/users', '/settings', '/security', '/analytics'];

  const adminRoutes = ['/users', '/settings/system', '/security/settings'];

  const isProtectedRoute = protectedRoutes.some((route) => event.url.pathname.startsWith(route));

  const isAdminRoute = adminRoutes.some((route) => event.url.pathname.startsWith(route));

  if (isProtectedRoute) {
    try {
      await authMiddleware(event, {
        requireAuth: true,
        requireAdmin: isAdminRoute,
        redirectTo: '/login',
      });
    } catch (redirect) {
      // Middleware will throw redirect, let it pass through
      throw redirect;
    }
  } else if (event.url.pathname !== '/login' && event.url.pathname !== '/register') {
    // For non-protected routes, still try to get user info if available
    try {
      await authMiddleware(event, { requireAuth: false });
    } catch (error) {
      // Ignore errors for optional auth
      (event.locals as any).user = null;
      (event.locals as any).isAuthenticated = false;
    }
  }

  return await resolve(event);
};

/**
 * Security headers hook
 */
const securityHandle: Handle = async ({ event, resolve }) => {
  const response = await resolve(event);

  // Add security headers
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  // CSP header for dashboard
  const isDevelopment = process.env.NODE_ENV === 'development';

  // Get API URLs from environment variables
  const publicApiUrl = process.env.PUBLIC_API_URL || process.env.WAKEDOCK_API_URL;
  const publicWsUrl = process.env.PUBLIC_WS_URL;

  // Build connect-src directive based on configuration
  let connectSrc = "'self'";

  if (isDevelopment) {
    // Development: allow all common development URLs
    connectSrc += ` http://localhost:* https://localhost:* http://wakedock-core:* https://wakedock-core:* http://wakedock:* https://wakedock:* ws://localhost:* wss://localhost:* ws://wakedock-core:* wss://wakedock-core:* ws://wakedock:* wss://wakedock:*`;
    if (publicApiUrl) {
      const apiHost = new URL(publicApiUrl).host;
      connectSrc += ` http://${apiHost} https://${apiHost} ws://${apiHost} wss://${apiHost}`;
    }
  } else {
    // Production: allow specific API URLs if configured
    if (publicApiUrl) {
      try {
        const apiUrl = new URL(publicApiUrl);
        connectSrc += ` ${apiUrl.protocol}//${apiUrl.host}`;
        // Add WebSocket equivalent
        const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        connectSrc += ` ${wsProtocol}//${apiUrl.host}`;
      } catch (e) {
        console.warn('Invalid PUBLIC_API_URL format:', publicApiUrl);
      }
    }
  }

  const cspDirectives = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Note: unsafe-eval needed for Svelte in dev
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    `connect-src ${connectSrc}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ];

  response.headers.set('Content-Security-Policy', cspDirectives.join('; '));

  return response;
};

/**
 * Error handling hook
 */
const errorHandle: Handle = async ({ event, resolve }) => {
  return await errorMiddleware(event, async () => await resolve(event));
};

/**
 * CORS handling for API requests
 */
const corsHandle: Handle = async ({ event, resolve }) => {
  // Handle CORS preflight requests
  if (event.request.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400',
      },
    });
  }

  const response = await resolve(event);

  // Add CORS headers to actual responses if needed
  if (event.url.pathname.startsWith('/api/')) {
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  }

  return response;
};

/**
 * Logging hook
 */
const loggingHandle: Handle = async ({ event, resolve }) => {
  const start = Date.now();

  try {
    const response = await resolve(event);
    const duration = Date.now() - start;

    console.log(
      `${event.request.method} ${event.url.pathname} - ${response.status} (${duration}ms)`
    );

    return response;
  } catch (error) {
    const duration = Date.now() - start;
    console.error(`${event.request.method} ${event.url.pathname} - ERROR (${duration}ms):`, error);
    throw error;
  }
};

// Combine all hooks in sequence
export const handle = sequence(loggingHandle, corsHandle, securityHandle, authHandle, errorHandle);

/**
 * Handle server errors
 */
export function handleError({ error, event }: { error: any; event: RequestEvent }) {
  console.error('Server error:', {
    error: error.message,
    stack: error.stack,
    url: event.url.pathname,
    method: event.request.method,
    timestamp: new Date().toISOString(),
    user: (event.locals as any).user?.id || 'anonymous',
  });

  // Don't expose internal error details in production
  const isDevelopment = process.env.NODE_ENV === 'development';

  return {
    message: isDevelopment ? error.message : 'Internal Server Error',
    code: isDevelopment ? error.code : undefined,
  };
}
