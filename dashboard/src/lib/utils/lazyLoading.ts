/**
 * Lazy Loading Utilities
 * Dynamic imports and component lazy loading
 */

import { writable } from 'svelte/store';

// Track loaded modules to prevent duplicate loading
const loadedModules = new Map<string, Promise<any>>();

// Loading states for lazy components
export const lazyLoadingStates = writable<Record<string, boolean>>({});

/**
 * Lazy load a Svelte component
 */
export async function lazyLoadComponent<T = any>(
  importFn: () => Promise<{ default: T }>,
  componentId?: string
): Promise<T> {
  const moduleKey = componentId || importFn.toString();

  // Return cached module if already loaded
  if (loadedModules.has(moduleKey)) {
    return loadedModules.get(moduleKey)!.then((module) => module.default);
  }

  // Set loading state
  if (componentId) {
    lazyLoadingStates.update((states) => ({
      ...states,
      [componentId]: true,
    }));
  }

  // Create loading promise
  const loadingPromise = importFn()
    .then((module) => {
      // Clear loading state
      if (componentId) {
        lazyLoadingStates.update((states) => ({
          ...states,
          [componentId]: false,
        }));
      }
      return module;
    })
    .catch((error) => {
      // Clear loading state on error
      if (componentId) {
        lazyLoadingStates.update((states) => ({
          ...states,
          [componentId]: false,
        }));
      }

      console.error(`Failed to load component ${componentId || 'unknown'}:`, error);
      throw error;
    });

  // Cache the promise
  loadedModules.set(moduleKey, loadingPromise);

  const module = await loadingPromise;
  return module.default;
}

/**
 * Preload components that are likely to be needed soon
 */
export function preloadComponent(importFn: () => Promise<any>, componentId?: string): void {
  // Only preload if not already loaded/loading
  const moduleKey = componentId || importFn.toString();
  if (!loadedModules.has(moduleKey)) {
    // Start loading but don't await
    lazyLoadComponent(importFn, componentId).catch(() => {
      // Ignore preload errors
    });
  }
}

/**
 * Lazy load route components with preloading
 */
export class RoutePreloader {
  private static instance: RoutePreloader;
  private preloadTimeouts = new Map<string, number>();

  static getInstance(): RoutePreloader {
    if (!RoutePreloader.instance) {
      RoutePreloader.instance = new RoutePreloader();
    }
    return RoutePreloader.instance;
  }

  /**
   * Preload a route component after a delay
   */
  schedulePreload(route: string, importFn: () => Promise<any>, delay: number = 100): void {
    // Clear existing timeout
    const existingTimeout = this.preloadTimeouts.get(route);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    // Schedule preload
    const timeout = window.setTimeout(() => {
      preloadComponent(importFn, `route:${route}`);
      this.preloadTimeouts.delete(route);
    }, delay) as unknown as number;

    this.preloadTimeouts.set(route, timeout);
  }

  /**
   * Cancel scheduled preload
   */
  cancelPreload(route: string): void {
    const timeout = this.preloadTimeouts.get(route);
    if (timeout) {
      clearTimeout(timeout);
      this.preloadTimeouts.delete(route);
    }
  }

  /**
   * Preload routes that are likely to be visited
   */
  preloadLikelyRoutes(currentRoute: string): void {
    const routeMap: Record<string, string[]> = {
      '/': ['/services', '/analytics', '/security'],
      '/services': ['/services/new', '/analytics'],
      '/services/new': ['/services'],
      '/analytics': ['/services', '/security'],
      '/security': ['/analytics', '/services'],
    };

    const likelyRoutes = routeMap[currentRoute] || [];

    likelyRoutes.forEach((route, index) => {
      this.schedulePreload(
        route,
        () => import(`../routes${route}/+page.svelte`),
        (index + 1) * 200 // Stagger preloads
      );
    });
  }
}

/**
 * Virtual scrolling for large lists
 */
export class VirtualScrollManager {
  private container: HTMLElement;
  private items: any[];
  private itemHeight: number;
  private visibleRange: { start: number; end: number } = { start: 0, end: 10 };
  private scrollTop = 0;

  constructor(container: HTMLElement, items: any[], itemHeight: number = 60) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;

    this.setupScrollListener();
  }

  private setupScrollListener(): void {
    this.container.addEventListener('scroll', () => {
      this.updateVisibleRange();
    });
  }

  private updateVisibleRange(): void {
    const containerHeight = this.container.clientHeight;
    const scrollTop = this.container.scrollTop;

    const startIndex = Math.floor(scrollTop / this.itemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / this.itemHeight) + 2, // +2 for buffer
      this.items.length
    );

    this.visibleRange = {
      start: Math.max(0, startIndex - 2), // -2 for buffer
      end: endIndex,
    };
  }

  getVisibleItems(): { items: any[]; totalHeight: number; offsetY: number } {
    const visibleItems = this.items.slice(this.visibleRange.start, this.visibleRange.end);
    const totalHeight = this.items.length * this.itemHeight;
    const offsetY = this.visibleRange.start * this.itemHeight;

    return {
      items: visibleItems,
      totalHeight,
      offsetY,
    };
  }

  updateItems(newItems: any[]): void {
    this.items = newItems;
    this.updateVisibleRange();
  }
}

/**
 * Intersection Observer for lazy loading elements
 */
export class LazyElementObserver {
  private observer: IntersectionObserver;
  private elements = new Map<Element, () => void>();

  constructor(options: IntersectionObserverInit = {}) {
    this.observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const loadFn = this.elements.get(entry.target);
            if (loadFn) {
              loadFn();
              this.unobserve(entry.target);
            }
          }
        });
      },
      {
        rootMargin: '50px',
        threshold: 0.1,
        ...options,
      }
    );
  }

  observe(element: Element, loadFn: () => void): void {
    this.elements.set(element, loadFn);
    this.observer.observe(element);
  }

  unobserve(element: Element): void {
    this.elements.delete(element);
    this.observer.unobserve(element);
  }

  disconnect(): void {
    this.observer.disconnect();
    this.elements.clear();
  }
}

/**
 * Image lazy loading with WebP support
 */
export function createLazyImage(
  src: string,
  alt: string = '',
  options: {
    placeholder?: string;
    webpSrc?: string;
    loadingStrategy?: 'lazy' | 'eager';
    sizes?: string;
  } = {}
): HTMLImageElement {
  const img = document.createElement('img');

  // Set basic attributes
  img.alt = alt;
  img.loading = options.loadingStrategy || 'lazy';

  if (options.sizes) {
    img.sizes = options.sizes;
  }

  // Use WebP if supported and available
  const supportsWebP = (() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/webp').startsWith('data:image/webp');
  })();

  const imageSrc = supportsWebP && options.webpSrc ? options.webpSrc : src;

  // Set placeholder if provided
  if (options.placeholder) {
    img.src = options.placeholder;
  }

  // Load actual image
  const actualImg = new Image();
  actualImg.onload = () => {
    img.src = imageSrc;
    img.classList.add('loaded');
  };
  actualImg.onerror = () => {
    // Fallback to original src if WebP fails
    if (imageSrc !== src) {
      img.src = src;
    }
  };

  actualImg.src = imageSrc;

  return img;
}

/**
 * Code splitting utility for dynamic imports
 */
export async function dynamicImport<T>(
  moduleFactory: () => Promise<T>,
  fallback?: () => T,
  retries: number = 3
): Promise<T> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await moduleFactory();
    } catch (error) {
      console.warn(`Dynamic import failed (attempt ${attempt}/${retries}):`, error);

      if (attempt === retries) {
        if (fallback) {
          console.info('Using fallback for failed dynamic import');
          return fallback();
        }
        throw new Error(`Failed to load module after ${retries} attempts: ${error}`);
      }

      // Exponential backoff
      await new Promise((resolve) => setTimeout(resolve, Math.pow(2, attempt) * 100));
    }
  }

  throw new Error('Unexpected error in dynamic import');
}

// Export singleton instances
export const routePreloader = RoutePreloader.getInstance();
