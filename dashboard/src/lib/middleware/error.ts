/**
 * Error Middleware
 * Global error handling and boundary
 */
import { error, type RequestEvent } from '@sveltejs/kit';
import type { ApiError } from '../api.js';

export interface ErrorContext {
  request: RequestEvent;
  userAgent?: string;
  timestamp: string;
  userId?: number;
}

/**
 * Global error handler middleware
 */
export async function errorMiddleware(
  event: RequestEvent,
  next: () => Promise<Response>
): Promise<Response> {
  try {
    // Add error context to locals
    (event.locals as any).errorContext = {
      request: event,
      userAgent: event.request.headers.get('user-agent') || undefined,
      timestamp: new Date().toISOString(),
      userId: (event.locals as any).user?.id,
    };

    return await next();
  } catch (err) {
    console.error('Error in request:', err);

    // Handle different types of errors
    if (isApiError(err)) {
      return handleApiError(err, event);
    }

    if (err instanceof Error) {
      return handleGenericError(err, event);
    }

    // Unknown error type
    throw error(500, 'Internal Server Error');
  }
}

/**
 * Handle API errors
 */
function handleApiError(apiError: ApiError, event: RequestEvent): Response {
  console.error('API Error:', {
    message: apiError.message,
    code: apiError.code,
    details: apiError.details,
    url: event.url.pathname,
    method: event.request.method,
    timestamp: new Date().toISOString(),
  });

  // Map API error codes to HTTP status codes
  const statusMap: Record<string, number> = {
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    VALIDATION_ERROR: 400,
    NETWORK_ERROR: 503,
  };

  const status = statusMap[apiError.code || ''] || 500;

  throw error(status, apiError.message);
}

/**
 * Handle generic errors
 */
function handleGenericError(err: Error, event: RequestEvent): Response {
  console.error('Generic Error:', {
    message: err.message,
    stack: err.stack,
    url: event.url.pathname,
    method: event.request.method,
    timestamp: new Date().toISOString(),
  });

  // Don't expose internal error details in production
  const isDevelopment = process.env.NODE_ENV === 'development';

  throw error(500, isDevelopment ? err.message : 'Internal Server Error');
}

/**
 * Type guard for API errors
 */
function isApiError(err: unknown): err is ApiError {
  return (
    typeof err === 'object' &&
    err !== null &&
    'message' in err &&
    typeof (err as any).message === 'string'
  );
}

/**
 * Client-side error handler for components
 */
export function handleClientError(error: unknown, context?: string): void {
  console.error(`Client Error${context ? ` in ${context}` : ''}:`, error);

  // You can extend this to send errors to a logging service
  // or show user-friendly notifications
}

/**
 * Async error wrapper for component methods
 */
export function asyncErrorHandler<T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  context?: string
) {
  return async (...args: T): Promise<R | undefined> => {
    try {
      return await fn(...args);
    } catch (error) {
      handleClientError(error, context);
      return undefined;
    }
  };
}

/**
 * Error boundary for wrapping dangerous operations
 */
export async function errorBoundary<T>(
  operation: () => Promise<T>,
  fallback?: T,
  context?: string
): Promise<T | undefined> {
  try {
    return await operation();
  } catch (error) {
    handleClientError(error, context);
    return fallback;
  }
}
