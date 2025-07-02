/**
 * Performance Utilities
 * Client-side performance monitoring and optimization tools
 */

export interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  type: 'timing' | 'counter' | 'gauge';
  tags?: Record<string, string>;
}

export interface PerformanceConfig {
  enableMetrics: boolean;
  sampleRate: number; // 0-1, percentage of metrics to capture
  maxMetrics: number;
  enableResourceTiming: boolean;
  enableUserTiming: boolean;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private config: PerformanceConfig;
  private observer?: PerformanceObserver;

  constructor(config: Partial<PerformanceConfig> = {}) {
    this.config = {
      enableMetrics: true,
      sampleRate: 1.0,
      maxMetrics: 1000,
      enableResourceTiming: true,
      enableUserTiming: true,
      ...config,
    };

    if (this.config.enableMetrics) {
      this.initializeObserver();
    }
  }

  private initializeObserver(): void {
    if (typeof PerformanceObserver === 'undefined') {
      console.warn('PerformanceObserver not available');
      return;
    }

    this.observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => this.processEntry(entry));
    });

    const entryTypes = ['navigation', 'measure', 'mark'];
    if (this.config.enableResourceTiming) {
      entryTypes.push('resource');
    }

    try {
      this.observer.observe({ entryTypes });
    } catch (error) {
      console.warn('Failed to observe performance entries:', error);
    }
  }

  private processEntry(entry: PerformanceEntry): void {
    if (!this.shouldSample()) return;

    const metric: PerformanceMetric = {
      name: entry.name,
      value: entry.duration || 0,
      timestamp: entry.startTime,
      type: 'timing',
      tags: {
        entryType: entry.entryType,
      },
    };

    this.addMetric(metric);
  }

  private shouldSample(): boolean {
    return Math.random() < this.config.sampleRate;
  }

  private addMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);

    // Limiter le nombre de métriques stockées
    if (this.metrics.length > this.config.maxMetrics) {
      this.metrics.shift();
    }
  }

  /**
   * Marque le début d'une mesure
   */
  mark(name: string): void {
    if (!this.config.enableUserTiming || typeof window.performance === 'undefined') return;

    try {
      window.performance.mark(name);
    } catch (error) {
      console.warn('Failed to create performance mark:', error);
    }
  }

  /**
   * Mesure le temps entre deux marques
   */
  measure(name: string, startMark: string, endMark?: string): number | null {
    if (!this.config.enableUserTiming || typeof window.performance === 'undefined') return null;

    try {
      window.performance.measure(name, startMark, endMark);
      const entries = window.performance.getEntriesByName(name, 'measure');
      const lastEntry = entries[entries.length - 1];
      return lastEntry ? lastEntry.duration : null;
    } catch (error) {
      console.warn('Failed to create performance measure:', error);
      return null;
    }
  }

  /**
   * Mesure la durée d'exécution d'une fonction
   */
  async measureFunction<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const startMark = `${name}-start`;
    const endMark = `${name}-end`;

    this.mark(startMark);
    const startTime = window.performance.now();

    try {
      const result = await fn();
      const endTime = window.performance.now();

      this.mark(endMark);
      this.measure(name, startMark, endMark);

      // Ajouter notre propre métrique
      this.addMetric({
        name,
        value: endTime - startTime,
        timestamp: startTime,
        type: 'timing',
        tags: { type: 'function' },
      });

      return result;
    } catch (error) {
      const endTime = window.performance.now();
      this.addMetric({
        name: `${name}-error`,
        value: endTime - startTime,
        timestamp: startTime,
        type: 'timing',
        tags: { type: 'function', error: 'true' },
      });
      throw error;
    }
  }

  /**
   * Enregistre une métrique personnalisée
   */
  recordMetric(
    name: string,
    value: number,
    type: 'timing' | 'counter' | 'gauge' = 'gauge',
    tags?: Record<string, string>
  ): void {
    if (!this.config.enableMetrics || !this.shouldSample()) return;

    this.addMetric({
      name,
      value,
      timestamp: window.performance.now(),
      type,
      tags,
    });
  }

  /**
   * Obtient les métriques de navigation
   */
  getNavigationMetrics(): Record<string, number> | null {
    if (typeof window.performance === 'undefined' || !window.performance.getEntriesByType)
      return null;

    const navEntries = window.performance.getEntriesByType(
      'navigation'
    ) as PerformanceNavigationTiming[];
    if (navEntries.length === 0) return null;

    const nav = navEntries[0];
    return {
      'dns-lookup': nav.domainLookupEnd - nav.domainLookupStart,
      'tcp-connect': nav.connectEnd - nav.connectStart,
      'ssl-handshake':
        nav.secureConnectionStart > 0 ? nav.connectEnd - nav.secureConnectionStart : 0,
      ttfb: nav.responseStart - nav.requestStart,
      download: nav.responseEnd - nav.responseStart,
      'dom-processing': nav.domComplete - nav.responseEnd,
      'total-load': nav.loadEventEnd - nav.fetchStart,
    };
  }

  /**
   * Obtient les métriques de ressources
   */
  getResourceMetrics(): PerformanceResourceTiming[] {
    if (typeof window.performance === 'undefined' || !window.performance.getEntriesByType)
      return [];

    return window.performance.getEntriesByType('resource') as PerformanceResourceTiming[];
  }

  /**
   * Obtient les Core Web Vitals
   */
  getCoreWebVitals(): Record<string, number> {
    const vitals: Record<string, number> = {};

    // LCP (Largest Contentful Paint)
    try {
      const lcpEntries = window.performance.getEntriesByType('largest-contentful-paint');
      if (lcpEntries.length > 0) {
        vitals.lcp = lcpEntries[lcpEntries.length - 1].startTime;
      }
    } catch {}

    // FID sera disponible via PerformanceObserver avec 'first-input'
    // CLS sera disponible via PerformanceObserver avec 'layout-shift'

    return vitals;
  }

  /**
   * Obtient toutes les métriques collectées
   */
  getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  /**
   * Filtre les métriques par nom
   */
  getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter((metric) => metric.name === name);
  }

  /**
   * Calcule des statistiques sur une métrique
   */
  getMetricStats(name: string): { min: number; max: number; avg: number; count: number } | null {
    const metrics = this.getMetricsByName(name);
    if (metrics.length === 0) return null;

    const values = metrics.map((m) => m.value);
    return {
      min: Math.min(...values),
      max: Math.max(...values),
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      count: values.length,
    };
  }

  /**
   * Vide les métriques
   */
  clearMetrics(): void {
    this.metrics = [];

    if (typeof window.performance !== 'undefined' && window.performance.clearMeasures) {
      window.performance.clearMeasures();
    }
    if (typeof window.performance !== 'undefined' && window.performance.clearMarks) {
      window.performance.clearMarks();
    }
  }

  /**
   * Exporte les métriques
   */
  exportMetrics(): string {
    return JSON.stringify(
      {
        timestamp: Date.now(),
        navigation: this.getNavigationMetrics(),
        coreWebVitals: this.getCoreWebVitals(),
        customMetrics: this.metrics,
      },
      null,
      2
    );
  }

  /**
   * Arrête la surveillance
   */
  stop(): void {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = undefined;
    }
  }
}

// Instance par défaut
export const performanceMonitor = new PerformanceMonitor();

// Utilitaires de performance
export const performanceUtils = {
  /**
   * Mesure le temps de rendu d'un composant
   */
  measureRender: (componentName: string) => {
    const startMark = `${componentName}-render-start`;
    const endMark = `${componentName}-render-end`;

    return {
      start: () => performanceMonitor.mark(startMark),
      end: () => {
        performanceMonitor.mark(endMark);
        return performanceMonitor.measure(`${componentName}-render`, startMark, endMark);
      },
    };
  },

  /**
   * Débounce une fonction pour améliorer les performances
   */
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): ((...args: Parameters<T>) => void) => {
    let timeout: number;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = window.setTimeout(() => func(...args), wait);
    };
  },

  /**
   * Throttle une fonction
   */
  throttle: <T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        window.setTimeout(() => (inThrottle = false), limit);
      }
    };
  },

  /**
   * Lazy loading d'images
   */
  lazyLoadImage: (img: HTMLImageElement, src: string) => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          img.src = src;
          observer.unobserve(img);
        }
      });
    });
    observer.observe(img);
    return observer;
  },

  /**
   * Précharge des ressources
   */
  preloadResource: (href: string, as: string = 'fetch') => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = href;
    link.as = as;
    document.head.appendChild(link);
    return link;
  },
};

// Types déjà exportés
