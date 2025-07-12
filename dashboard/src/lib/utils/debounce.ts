/**
 * Debounce Utility
 * Optimizes performance by delaying function execution
 */

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;

  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func(...args);
    }
  };
}

// Debounced value store for Svelte
export function createDebouncedValue(initialValue: string, delay: number = 300) {
  let value = $state(initialValue);
  let debouncedValue = $state(initialValue);
  let timeoutId: ReturnType<typeof setTimeout>;

  return {
    get value() {
      return value;
    },
    set value(newValue: string) {
      value = newValue;
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        debouncedValue = newValue;
      }, delay);
    },
    get debouncedValue() {
      return debouncedValue;
    }
  };
}

// Performance optimization for reactive statements
export function createMemoized<T>(fn: () => T, deps: any[]): () => T {
  let lastDeps: any[] = [];
  let lastResult: T;
  let initialized = false;

  return () => {
    if (!initialized || !depsEqual(deps, lastDeps)) {
      lastResult = fn();
      lastDeps = [...deps];
      initialized = true;
    }
    return lastResult;
  };
}

function depsEqual(a: any[], b: any[]): boolean {
  if (a.length !== b.length) return false;
  return a.every((val, index) => val === b[index]);
}

// Visibility API utilities for optimization
export function onPageVisible(callback: () => void): () => void {
  function handleVisibilityChange() {
    if (!document.hidden) {
      callback();
    }
  }

  document.addEventListener('visibilitychange', handleVisibilityChange);

  return () => {
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  };
}

// Intersection Observer for lazy loading
export function createIntersectionObserver(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options?: IntersectionObserverInit
): IntersectionObserver {
  return new IntersectionObserver(callback, {
    rootMargin: '10px',
    threshold: 0.1,
    ...options
  });
}