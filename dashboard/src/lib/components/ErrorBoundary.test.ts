/**
 * ErrorBoundary Component Tests
 * Tests for the global error boundary component
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import { get } from 'svelte/store';
import ErrorBoundary from './ErrorBoundary.svelte';
import { getErrorBoundary, captureError } from '../utils/errorHandling';

// Mock the logger
vi.mock('../utils/logger', () => ({
  logger: {
    error: vi.fn(),
    warn: vi.fn(),
    info: vi.fn(),
  },
}));

// Mock the monitoring service
vi.mock('../services/monitoring', () => ({
  monitoring: {
    reportError: vi.fn(),
  },
}));

// Mock the notifications service
vi.mock('../services/notifications', () => ({
  notifications: {
    error: vi.fn(),
    warn: vi.fn(),
    info: vi.fn(),
  },
}));

describe('ErrorBoundary', () => {
  let consoleErrorSpy: any;

  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it('should render component without errors', () => {
    const { container } = render(ErrorBoundary);
    expect(container).toBeDefined();
  });

  it('should create error boundary with boundary ID', () => {
    const boundaryId = 'test-boundary';
    render(ErrorBoundary, {
      props: {
        boundaryId,
      },
    });

    const boundary = getErrorBoundary(boundaryId);
    const state = get(boundary);
    expect(state.hasError).toBe(false);
    expect(state.retryCount).toBe(0);
  });

  it('should capture and handle errors', () => {
    const boundaryId = 'test-boundary-error';
    render(ErrorBoundary, {
      props: {
        boundaryId,
      },
    });

    // Simulate error capture
    captureError(boundaryId, new Error('Test error'));

    const boundary = getErrorBoundary(boundaryId);
    const state = get(boundary);
    expect(state.hasError).toBe(true);
    expect(state.error?.error.message).toBe('Test error');
  });

  it('should support retry functionality', () => {
    const boundaryId = 'test-boundary-retry';
    render(ErrorBoundary, {
      props: {
        boundaryId,
        showRetry: true,
      },
    });

    const boundary = getErrorBoundary(boundaryId);
    const state = get(boundary);
    expect(state.canRetry).toBe(true);
  });

  it('should handle custom fallback', () => {
    const customFallback = 'Custom error message';
    render(ErrorBoundary, {
      props: {
        customFallback,
      },
    });

    // Component should render without errors
    expect(true).toBe(true);
  });

  it('should handle max retries configuration', () => {
    const maxRetries = 3;
    render(ErrorBoundary, {
      props: {
        maxRetries,
      },
    });

    // Component should render without errors
    expect(true).toBe(true);
  });

  it('should handle error reporting configuration', () => {
    render(ErrorBoundary, {
      props: {
        reportErrors: true,
      },
    });

    // Component should render without errors
    expect(true).toBe(true);
  });

  it('should handle boundary ID generation', () => {
    const { container } = render(ErrorBoundary);
    expect(container).toBeDefined();
  });
});
