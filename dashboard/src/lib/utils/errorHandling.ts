/**
 * Enhanced Error Boundary and Global Error Handling
 * Provides comprehensive error tracking, reporting, and recovery
 */

import { writable, type Writable } from 'svelte/store';

export interface ErrorInfo {
  id: string;
  error: Error;
  errorInfo?: any;
  timestamp: Date;
  level: 'error' | 'warning' | 'info';
  source: string;
  stack?: string;
  user?: string;
  url?: string;
  userAgent?: string;
  componentStack?: string;
  recovered?: boolean;
  retryAttempts?: number;
  maxRetries?: number;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: ErrorInfo | null;
  fallbackComponent?: string;
  retryCount: number;
  canRetry: boolean;
}

// Global error store
export const globalErrors: Writable<ErrorInfo[]> = writable([]);
export const criticalErrors: Writable<ErrorInfo[]> = writable([]);

// Error boundary states registry
const errorBoundaries = new Map<string, Writable<ErrorBoundaryState>>();

// Configuration
interface ErrorHandlerConfig {
  maxErrors: number;
  reportToServer: boolean;
  showUserFriendlyMessages: boolean;
  enableErrorRecovery: boolean;
  enableRetry: boolean;
  maxRetries: number;
  enableLogging: boolean;
}

const defaultConfig: ErrorHandlerConfig = {
  maxErrors: 100,
  reportToServer: true,
  showUserFriendlyMessages: true,
  enableErrorRecovery: true,
  enableRetry: true,
  maxRetries: 3,
  enableLogging: true,
};

let config = { ...defaultConfig };

/**
 * Configure global error handling
 */
export function configureErrorHandling(newConfig: Partial<ErrorHandlerConfig>) {
  config = { ...config, ...newConfig };
}

/**
 * Generate unique error ID
 */
function generateErrorId(): string {
  return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Create enhanced error info
 */
function createErrorInfo(
  error: Error,
  source: string,
  level: 'error' | 'warning' | 'info' = 'error',
  additionalInfo?: any
): ErrorInfo {
  return {
    id: generateErrorId(),
    error,
    timestamp: new Date(),
    level,
    source,
    stack: error.stack,
    url: typeof window !== 'undefined' ? window.location.href : undefined,
    userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined,
    ...additionalInfo,
  };
}

/**
 * Log error to console with enhanced formatting
 */
function logError(errorInfo: ErrorInfo) {
  if (!config.enableLogging) return;

  const { error, source, level, timestamp, id } = errorInfo;
  const logMethod =
    level === 'error' ? console.error : level === 'warning' ? console.warn : console.info;

  logMethod(`[${level.toUpperCase()}] ${source} - ${error.message}`, {
    id,
    timestamp: timestamp.toISOString(),
    stack: error.stack,
    errorInfo,
  });
}

/**
 * Report error to server (if configured)
 */
async function reportErrorToServer(errorInfo: ErrorInfo) {
  if (!config.reportToServer || typeof window === 'undefined') return;

  try {
    await fetch('/api/errors/report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...errorInfo,
        error: {
          name: errorInfo.error.name,
          message: errorInfo.error.message,
          stack: errorInfo.error.stack,
        },
      }),
    });
  } catch (reportingError) {
    console.warn('Failed to report error to server:', reportingError);
  }
}

/**
 * Global error handler
 */
export function handleError(
  error: Error,
  source: string,
  level: 'error' | 'warning' | 'info' = 'error',
  additionalInfo?: any
): ErrorInfo {
  const errorInfo = createErrorInfo(error, source, level, additionalInfo);

  // Log error
  logError(errorInfo);

  // Report to server
  if (level === 'error') {
    reportErrorToServer(errorInfo);
  }

  // Add to global error store
  globalErrors.update((errors: ErrorInfo[]) => {
    const newErrors = [errorInfo, ...errors].slice(0, config.maxErrors);
    return newErrors;
  });

  // Add to critical errors if needed
  if (
    level === 'error' &&
    (error.name === 'ChunkLoadError' || error.message.includes('Loading chunk'))
  ) {
    criticalErrors.update((errors: ErrorInfo[]) => [errorInfo, ...errors].slice(0, 10));
  }

  return errorInfo;
}

/**
 * Create or get error boundary store
 */
export function getErrorBoundary(boundaryId: string): Writable<ErrorBoundaryState> {
  if (!errorBoundaries.has(boundaryId)) {
    errorBoundaries.set(
      boundaryId,
      writable({
        hasError: false,
        error: null,
        retryCount: 0,
        canRetry: config.enableRetry,
      })
    );
  }
  return errorBoundaries.get(boundaryId)!;
}

/**
 * Capture error in boundary
 */
export function captureError(boundaryId: string, error: Error, errorInfo?: any): void {
  const boundary = getErrorBoundary(boundaryId);
  const enhancedError = handleError(error, `ErrorBoundary:${boundaryId}`, 'error', errorInfo);

  boundary.update((state: ErrorBoundaryState) => ({
    ...state,
    hasError: true,
    error: enhancedError,
    canRetry: config.enableRetry && state.retryCount < config.maxRetries,
  }));
}

/**
 * Retry from error boundary
 */
export function retryFromError(boundaryId: string): void {
  const boundary = getErrorBoundary(boundaryId);

  boundary.update((state: ErrorBoundaryState) => {
    if (!state.canRetry || state.retryCount >= config.maxRetries) {
      return state;
    }

    return {
      hasError: false,
      error: null,
      retryCount: state.retryCount + 1,
      canRetry: state.retryCount + 1 < config.maxRetries,
    };
  });
}

/**
 * Clear error boundary
 */
export function clearError(boundaryId: string): void {
  const boundary = getErrorBoundary(boundaryId);
  boundary.set({
    hasError: false,
    error: null,
    retryCount: 0,
    canRetry: config.enableRetry,
  });
}

/**
 * Get user-friendly error message
 */
export function getUserFriendlyMessage(error: ErrorInfo): string {
  if (!config.showUserFriendlyMessages) {
    return error.error.message;
  }

  const { error: err } = error;

  // Chunk loading errors
  if (err.name === 'ChunkLoadError' || err.message.includes('Loading chunk')) {
    return 'Application update detected. Please refresh the page to continue.';
  }

  // Network errors
  if (err.message.includes('fetch') || err.message.includes('Network')) {
    return 'Connection problem. Please check your internet connection and try again.';
  }

  // Authentication errors
  if (err.message.includes('401') || err.message.includes('Unauthorized')) {
    return 'Your session has expired. Please log in again.';
  }

  // Permission errors
  if (err.message.includes('403') || err.message.includes('Forbidden')) {
    return 'You do not have permission to perform this action.';
  }

  // Server errors
  if (err.message.includes('500') || err.message.includes('Internal Server Error')) {
    return 'Server error. Please try again later or contact support if the problem persists.';
  }

  // Validation errors
  if (err.message.includes('validation') || err.message.includes('invalid')) {
    return 'Please check your input and try again.';
  }

  // Default message
  return 'An unexpected error occurred. Please try again or contact support if the problem persists.';
}

/**
 * Clear all errors
 */
export function clearAllErrors(): void {
  globalErrors.set([]);
  criticalErrors.set([]);

  // Clear all error boundaries
  for (const [, boundary] of errorBoundaries) {
    boundary.set({
      hasError: false,
      error: null,
      retryCount: 0,
      canRetry: config.enableRetry,
    });
  }
}

/**
 * Setup global error handlers
 */
export function setupGlobalErrorHandlers(): void {
  if (typeof window === 'undefined') return;

  // Unhandled errors
  window.addEventListener('error', (event) => {
    handleError(event.error || new Error(event.message), 'GlobalErrorHandler', 'error', {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });

  // Unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason));
    handleError(error, 'UnhandledPromiseRejection', 'error');
  });

  // Console error interception
  const originalError = console.error;
  console.error = (...args) => {
    if (args[0] instanceof Error) {
      handleError(args[0], 'ConsoleError', 'error');
    }
    originalError.apply(console, args);
  };
}

/**
 * Async error wrapper
 */
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  source: string,
  options: {
    retries?: number;
    retryDelay?: number;
    fallback?: T;
    throwOnFailure?: boolean;
  } = {}
): Promise<T> {
  const { retries = 0, retryDelay = 1000, fallback, throwOnFailure = true } = options;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const isLastAttempt = attempt === retries;
      const errorInfo = handleError(
        error instanceof Error ? error : new Error(String(error)),
        source,
        'error',
        { attempt: attempt + 1, maxAttempts: retries + 1 }
      );

      if (isLastAttempt) {
        if (fallback !== undefined) {
          return fallback;
        }
        if (throwOnFailure) {
          throw error;
        }
        return undefined as T;
      }

      // Wait before retry
      if (retryDelay > 0) {
        await new Promise((resolve) => setTimeout(resolve, retryDelay * (attempt + 1)));
      }
    }
  }

  return undefined as T;
}
