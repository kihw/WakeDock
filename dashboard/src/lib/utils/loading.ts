/**
 * Loading State Management Utilities
 * Helps manage loading states and prevent blocking states
 */

import { writable, type Writable } from 'svelte/store';

export interface LoadingState {
  isLoading: boolean;
  operation?: string;
  startTime?: Date;
  canCancel?: boolean;
  progress?: number;
}

// Global loading states registry
const loadingStates = new Map<string, Writable<LoadingState>>();

/**
 * Create or get a loading state store
 */
export function getLoadingStore(key: string): Writable<LoadingState> {
  if (!loadingStates.has(key)) {
    loadingStates.set(
      key,
      writable<LoadingState>({
        isLoading: false,
        operation: undefined,
        startTime: undefined,
        canCancel: false,
        progress: undefined,
      })
    );
  }
  return loadingStates.get(key)!;
}

/**
 * Start a loading operation
 */
export function startLoading(
  key: string,
  operation?: string,
  options: { canCancel?: boolean; timeout?: number } = {}
): () => void {
  const store = getLoadingStore(key);
  const startTime = new Date();

  store.set({
    isLoading: true,
    operation,
    startTime,
    canCancel: options.canCancel || false,
    progress: undefined,
  });

  // Auto-timeout for stuck operations
  let timeoutId: number | null = null;
  if (options.timeout) {
    timeoutId = window.setTimeout(() => {
      console.warn(`Loading operation "${operation}" timed out after ${options.timeout}ms`);
      stopLoading(key);
    }, options.timeout) as unknown as number;
  }

  // Return cleanup function
  return () => {
    if (timeoutId) clearTimeout(timeoutId);
    stopLoading(key);
  };
}

/**
 * Stop a loading operation
 */
export function stopLoading(key: string): void {
  const store = getLoadingStore(key);
  store.update((state: LoadingState) => ({
    ...state,
    isLoading: false,
    operation: undefined,
    startTime: undefined,
    progress: undefined,
  }));
}

/**
 * Update loading progress
 */
export function updateProgress(key: string, progress: number): void {
  const store = getLoadingStore(key);
  store.update((state: LoadingState) => ({
    ...state,
    progress: Math.min(100, Math.max(0, progress)),
  }));
}

/**
 * Check if any loading operations are active
 */
export function hasActiveLoading(): boolean {
  for (const [, store] of loadingStates) {
    let isActive = false;
    store.subscribe((state: LoadingState) => {
      isActive = state.isLoading;
    })();
    if (isActive) return true;
  }
  return false;
}

/**
 * Cancel a loading operation if it supports cancellation
 */
export function cancelLoading(key: string): boolean {
  const store = getLoadingStore(key);
  let canCancel = false;

  store.subscribe((state: LoadingState) => {
    canCancel = state.canCancel || false;
  })();

  if (canCancel) {
    stopLoading(key);
    return true;
  }

  return false;
}

/**
 * Higher-order function to wrap async operations with loading state
 */
export function withLoading<T>(
  key: string,
  operation: string,
  asyncFn: () => Promise<T>,
  options: { canCancel?: boolean; timeout?: number; onProgress?: (progress: number) => void } = {}
): Promise<T> {
  return new Promise((resolve, reject) => {
    const cleanup = startLoading(key, operation, options);

    let isCancelled = false;
    const originalAsyncFn = asyncFn;

    // Create a cancellable version if needed
    if (options.canCancel) {
      const cancelHandler = () => {
        isCancelled = true;
        cleanup();
        reject(new Error('Operation cancelled'));
      };

      // Store cancel handler for external access
      const store = getLoadingStore(key);
      store.update((state: LoadingState) => ({
        ...state,
        canCancel: true,
      }));
    }

    originalAsyncFn()
      .then((result) => {
        if (!isCancelled) {
          cleanup();
          resolve(result);
        }
      })
      .catch((error) => {
        if (!isCancelled) {
          cleanup();
          reject(error);
        }
      });
  });
}

/**
 * Debounced loading helper for frequent operations
 */
export function debouncedLoading(
  key: string,
  operation: string,
  asyncFn: () => Promise<any>,
  delay: number = 300
): Promise<any> {
  return new Promise((resolve, reject) => {
    // Clear any existing timeout for this key
    const existingTimeout = loadingTimeouts.get(key);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    // Set new timeout
    const timeoutId = window.setTimeout(() => {
      withLoading(key, operation, asyncFn)
        .then(resolve)
        .catch(reject)
        .finally(() => {
          loadingTimeouts.delete(key);
        });
    }, delay) as unknown as number;

    loadingTimeouts.set(key, timeoutId);
  });
}

// Track debounced timeouts
const loadingTimeouts = new Map<string, number>();

/**
 * Batch loading operations
 */
export class LoadingBatch {
  private operations: Map<string, Promise<any>> = new Map();
  private batchKey: string;

  constructor(batchKey: string) {
    this.batchKey = batchKey;
  }

  add<T>(key: string, operation: string, asyncFn: () => Promise<T>): Promise<T> {
    const promise = withLoading(`${this.batchKey}_${key}`, operation, asyncFn);
    this.operations.set(key, promise);
    return promise;
  }

  async waitAll(): Promise<Map<string, any>> {
    const results = new Map<string, any>();

    for (const [key, promise] of this.operations) {
      try {
        const result = await promise;
        results.set(key, result);
      } catch (error) {
        console.error(`Batch operation ${key} failed:`, error);
        results.set(key, { error });
      }
    }

    return results;
  }

  cancelAll(): void {
    for (const [key] of this.operations) {
      cancelLoading(`${this.batchKey}_${key}`);
    }
  }
}
