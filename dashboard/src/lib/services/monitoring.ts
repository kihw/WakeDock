/**
 * Client-side Monitoring Service
 * Performance and error monitoring for the dashboard
 */

import { writable, derived, get } from 'svelte/store';
import { logger, performanceLogger } from '../utils/logger';
import { performanceMonitor } from '../utils/performance';
import type { Writable, Readable } from 'svelte/store';

export interface MonitoringMetric {
  name: string;
  value: number;
  timestamp: Date;
  tags?: Record<string, string>;
  type: 'counter' | 'gauge' | 'histogram' | 'timer';
}

export interface ErrorReport {
  id: string;
  error: Error;
  timestamp: Date;
  context?: Record<string, any>;
  userAgent: string;
  url: string;
  userId?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface PerformanceReport {
  id: string;
  timestamp: Date;
  metrics: {
    loadTime: number;
    domContentLoaded: number;
    firstPaint: number;
    firstContentfulPaint: number;
    largestContentfulPaint?: number;
    firstInputDelay?: number;
    cumulativeLayoutShift?: number;
  };
  resources: {
    count: number;
    totalSize: number;
    totalDuration: number;
  };
  memory?: {
    used: number;
    total: number;
  };
}

export interface UserInteraction {
  id: string;
  type: 'click' | 'navigation' | 'form_submit' | 'api_call' | 'error';
  timestamp: Date;
  element?: string;
  page: string;
  duration?: number;
  success?: boolean;
  metadata?: Record<string, any>;
}

export interface MonitoringConfig {
  enableErrorTracking: boolean;
  enablePerformanceTracking: boolean;
  enableUserTracking: boolean;
  sampleRate: number; // 0-1
  maxErrors: number;
  maxMetrics: number;
  maxInteractions: number;
  reportingInterval: number; // en ms
  enableReporting: boolean;
  reportingEndpoint?: string;
}

class MonitoringService {
  private config: MonitoringConfig;
  private metrics: Writable<MonitoringMetric[]> = writable([]);
  private errors: Writable<ErrorReport[]> = writable([]);
  private performance: Writable<PerformanceReport[]> = writable([]);
  private interactions: Writable<UserInteraction[]> = writable([]);
  private reportingTimer?: number;

  constructor(config: Partial<MonitoringConfig> = {}) {
    this.config = {
      enableErrorTracking: true,
      enablePerformanceTracking: true,
      enableUserTracking: true,
      sampleRate: 1.0,
      maxErrors: 100,
      maxMetrics: 1000,
      maxInteractions: 500,
      reportingInterval: 60000, // 1 minute
      enableReporting: false,
      ...config,
    };

    this.init();
  }

  private init(): void {
    if (typeof window === 'undefined') return;

    // Écouter les erreurs globales
    if (this.config.enableErrorTracking) {
      this.setupErrorTracking();
    }

    // Surveiller les performances
    if (this.config.enablePerformanceTracking) {
      this.setupPerformanceTracking();
    }

    // Suivre les interactions utilisateur
    if (this.config.enableUserTracking) {
      this.setupUserTracking();
    }

    // Démarrer le reporting périodique
    if (this.config.enableReporting) {
      this.startReporting();
    }
  }

  private setupErrorTracking(): void {
    // Erreurs JavaScript non capturées
    window.addEventListener('error', (event) => {
      this.reportError(event.error || new Error(event.message), {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      });
    });

    // Promesses rejetées non capturées
    window.addEventListener('unhandledrejection', (event) => {
      this.reportError(
        event.reason instanceof Error ? event.reason : new Error(String(event.reason)),
        { type: 'unhandled_rejection' }
      );
    });
  }

  private setupPerformanceTracking(): void {
    // Mesurer les performances de navigation
    if (document.readyState === 'complete') {
      this.collectNavigationMetrics();
    } else {
      window.addEventListener('load', () => {
        setTimeout(() => this.collectNavigationMetrics(), 100);
      });
    }

    // Observer les changements de performance
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.processPerformanceEntry(entry);
        }
      });

      try {
        observer.observe({
          entryTypes: ['navigation', 'paint', 'largest-contentful-paint', 'first-input'],
        });
      } catch (error) {
        logger.warn('Performance observer failed to start', { error });
      }
    }
  }

  private setupUserTracking(): void {
    // Suivre les clics
    document.addEventListener('click', (event) => {
      if (Math.random() > this.config.sampleRate) return;

      const target = event.target as HTMLElement;
      this.trackInteraction('click', {
        element: this.getElementSelector(target),
        x: event.clientX,
        y: event.clientY,
      });
    });

    // Suivre les changements de page (pour les SPAs)
    let currentPath = window.location.pathname;
    const checkPathChange = () => {
      if (window.location.pathname !== currentPath) {
        this.trackInteraction('navigation', {
          from: currentPath,
          to: window.location.pathname,
        });
        currentPath = window.location.pathname;
      }
    };

    // Vérifier les changements de route
    setInterval(checkPathChange, 1000);
  }

  private getElementSelector(element: HTMLElement): string {
    if (element.id) return `#${element.id}`;
    if (element.className) return `.${element.className.split(' ')[0]}`;
    return element.tagName.toLowerCase();
  }

  private processPerformanceEntry(entry: PerformanceEntry): void {
    const metric: MonitoringMetric = {
      name: entry.name,
      value: entry.duration || entry.startTime,
      timestamp: new Date(),
      type: 'timer',
      tags: {
        entryType: entry.entryType,
      },
    };

    this.addMetric(metric);
  }

  private collectNavigationMetrics(): void {
    const navMetrics = performanceMonitor.getNavigationMetrics();
    if (!navMetrics) return;

    Object.entries(navMetrics).forEach(([name, value]) => {
      this.addMetric({
        name: `navigation.${name}`,
        value,
        timestamp: new Date(),
        type: 'timer',
      });
    });

    // Collecter les métriques de mémoire si disponibles
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.addMetric({
        name: 'memory.used',
        value: memory.usedJSHeapSize,
        timestamp: new Date(),
        type: 'gauge',
      });
    }

    // Créer un rapport de performance
    this.createPerformanceReport();
  }

  private createPerformanceReport(): void {
    const navigationEntries = performance.getEntriesByType(
      'navigation'
    ) as PerformanceNavigationTiming[];
    if (navigationEntries.length === 0) return;

    const nav = navigationEntries[0];
    const report: PerformanceReport = {
      id: this.generateId(),
      timestamp: new Date(),
      metrics: {
        loadTime: nav.loadEventEnd - nav.fetchStart,
        domContentLoaded: nav.domContentLoadedEventEnd - nav.fetchStart,
        firstPaint: 0,
        firstContentfulPaint: 0,
      },
      resources: {
        count: performance.getEntriesByType('resource').length,
        totalSize: 0,
        totalDuration: 0,
      },
    };

    // Ajouter les métriques Paint
    const paintEntries = performance.getEntriesByType('paint');
    paintEntries.forEach((entry) => {
      if (entry.name === 'first-paint') {
        report.metrics.firstPaint = entry.startTime;
      } else if (entry.name === 'first-contentful-paint') {
        report.metrics.firstContentfulPaint = entry.startTime;
      }
    });

    // Ajouter les métriques de mémoire
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      report.memory = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
      };
    }

    this.addPerformanceReport(report);
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private addMetric(metric: MonitoringMetric): void {
    this.metrics.update((metrics) => {
      const updated = [metric, ...metrics];
      if (updated.length > this.config.maxMetrics) {
        updated.splice(this.config.maxMetrics);
      }
      return updated;
    });
  }

  private addPerformanceReport(report: PerformanceReport): void {
    this.performance.update((reports) => [report, ...reports.slice(0, 19)]); // Garder max 20 rapports
  }

  private startReporting(): void {
    if (this.reportingTimer) {
      clearInterval(this.reportingTimer);
    }

    this.reportingTimer = window.setInterval(() => {
      this.sendReport();
    }, this.config.reportingInterval);
  }

  private async sendReport(): Promise<void> {
    if (!this.config.reportingEndpoint) return;

    const data = {
      timestamp: new Date().toISOString(),
      metrics: get(this.metrics).slice(0, 50), // Dernières 50 métriques
      errors: get(this.errors).slice(0, 10), // Dernières 10 erreurs
      performance: get(this.performance).slice(0, 5), // Derniers 5 rapports
      interactions: get(this.interactions).slice(0, 20), // Dernières 20 interactions
    };

    try {
      await fetch(this.config.reportingEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      logger.debug('Monitoring report sent successfully');
    } catch (error) {
      logger.error(
        'Failed to send monitoring report',
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Signaler une erreur
   */
  reportError(
    error: Error,
    context?: Record<string, any>,
    severity: ErrorReport['severity'] = 'medium'
  ): string {
    const report: ErrorReport = {
      id: this.generateId(),
      error,
      timestamp: new Date(),
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
      severity,
    };

    this.errors.update((errors) => {
      const updated = [report, ...errors];
      if (updated.length > this.config.maxErrors) {
        updated.splice(this.config.maxErrors);
      }
      return updated;
    });

    logger.error('Error reported to monitoring', error, context);
    return report.id;
  }

  /**
   * Enregistrer une métrique personnalisée
   */
  recordMetric(
    name: string,
    value: number,
    type: MonitoringMetric['type'] = 'gauge',
    tags?: Record<string, string>
  ): void {
    if (Math.random() > this.config.sampleRate) return;

    this.addMetric({
      name,
      value,
      timestamp: new Date(),
      type,
      tags,
    });
  }

  /**
   * Suivre une interaction utilisateur
   */
  trackInteraction(type: UserInteraction['type'], metadata?: Record<string, any>): string {
    if (Math.random() > this.config.sampleRate) return '';

    const interaction: UserInteraction = {
      id: this.generateId(),
      type,
      timestamp: new Date(),
      page: window.location.pathname,
      metadata,
    };

    this.interactions.update((interactions) => {
      const updated = [interaction, ...interactions];
      if (updated.length > this.config.maxInteractions) {
        updated.splice(this.config.maxInteractions);
      }
      return updated;
    });

    return interaction.id;
  }

  /**
   * Mesurer la durée d'une opération
   */
  async measureOperation<T>(
    name: string,
    operation: () => Promise<T>,
    tags?: Record<string, string>
  ): Promise<T> {
    const startTime = performance.now();
    const startMark = performanceLogger.mark(name);

    try {
      const result = await operation();
      const duration = performance.now() - startTime;

      this.recordMetric(`operation.${name}`, duration, 'timer', {
        ...tags,
        status: 'success',
      });

      performanceLogger.measure(name, startMark);
      return result;
    } catch (error) {
      const duration = performance.now() - startTime;

      this.recordMetric(`operation.${name}`, duration, 'timer', {
        ...tags,
        status: 'error',
      });

      this.reportError(error instanceof Error ? error : new Error(String(error)), {
        operation: name,
        duration,
      });

      throw error;
    }
  }

  /**
   * Obtenir les métriques agrégées
   */
  getAggregatedMetrics(
    timeWindow: number = 300000
  ): Record<string, { avg: number; min: number; max: number; count: number }> {
    const cutoff = new Date(Date.now() - timeWindow);
    const recentMetrics = get(this.metrics).filter((m) => m.timestamp > cutoff);

    const aggregated: Record<string, { values: number[] }> = {};

    recentMetrics.forEach((metric) => {
      if (!aggregated[metric.name]) {
        aggregated[metric.name] = { values: [] };
      }
      aggregated[metric.name].values.push(metric.value);
    });

    const result: Record<string, { avg: number; min: number; max: number; count: number }> = {};

    Object.entries(aggregated).forEach(([name, data]) => {
      const values = data.values;
      result[name] = {
        avg: values.reduce((a, b) => a + b, 0) / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        count: values.length,
      };
    });

    return result;
  }

  /**
   * Stores réactifs
   */
  get metricsStore(): Readable<MonitoringMetric[]> {
    return this.metrics;
  }

  get errorsStore(): Readable<ErrorReport[]> {
    return this.errors;
  }

  get performanceStore(): Readable<PerformanceReport[]> {
    return this.performance;
  }

  get interactionsStore(): Readable<UserInteraction[]> {
    return this.interactions;
  }

  /**
   * Store dérivé pour les statistiques d'erreurs
   */
  get errorStats(): Readable<{
    total: number;
    byType: Record<string, number>;
    bySeverity: Record<string, number>;
  }> {
    return derived(this.errors, ($errors) => {
      const byType: Record<string, number> = {};
      const bySeverity: Record<string, number> = {};

      $errors.forEach((error) => {
        const type = error.error.name || 'Unknown';
        byType[type] = (byType[type] || 0) + 1;
        bySeverity[error.severity] = (bySeverity[error.severity] || 0) + 1;
      });

      return {
        total: $errors.length,
        byType,
        bySeverity,
      };
    });
  }

  /**
   * Configurer le service
   */
  configure(newConfig: Partial<MonitoringConfig>): void {
    this.config = { ...this.config, ...newConfig };

    // Redémarrer le reporting si nécessaire
    if (this.config.enableReporting && !this.reportingTimer) {
      this.startReporting();
    } else if (!this.config.enableReporting && this.reportingTimer) {
      clearInterval(this.reportingTimer);
      this.reportingTimer = undefined;
    }
  }

  /**
   * Nettoyer les ressources
   */
  destroy(): void {
    if (this.reportingTimer) {
      clearInterval(this.reportingTimer);
    }
  }
}

// Instance globale
export const monitoring = new MonitoringService();
