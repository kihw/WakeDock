/**
 * Advanced Monitoring and Quality Gates Configuration
 * Provides comprehensive monitoring, error tracking, and quality metrics
 */

import { browser } from '$app/environment';
import { featureFlags } from './flags';

export interface PerformanceMetrics {
  // Core Web Vitals
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  timeToInteractive: number;

  // Custom metrics
  apiResponseTime: number;
  bundleSize: number;
  memoryUsage: number;
  errorCount: number;
}

export interface QualityGate {
  name: string;
  metric: keyof PerformanceMetrics;
  threshold: number;
  operator: 'lt' | 'gt' | 'eq' | 'lte' | 'gte';
  critical: boolean;
}

export interface MonitoringConfig {
  enabled: boolean;
  apiEndpoint: string;
  reportInterval: number;
  bufferSize: number;
  qualityGates: QualityGate[];
  enableRealUserMonitoring: boolean;
  enableErrorTracking: boolean;
  enablePerformanceTracking: boolean;
}

class AdvancedMonitoring {
  private config: MonitoringConfig;
  private metricsBuffer: PerformanceMetrics[] = [];
  private performanceObserver?: PerformanceObserver;
  private errorCount = 0;
  private startTime = Date.now();

  constructor(config: MonitoringConfig) {
    this.config = config;

    if (browser && this.config.enabled) {
      this.initializeMonitoring();
    }
  }

  private initializeMonitoring(): void {
    // Initialize Web Vitals monitoring
    if (this.config.enablePerformanceTracking) {
      this.initializeWebVitals();
    }

    // Initialize error tracking
    if (this.config.enableErrorTracking) {
      this.initializeErrorTracking();
    }

    // Initialize real user monitoring
    if (this.config.enableRealUserMonitoring) {
      this.initializeRUM();
    }

    // Start reporting interval
    setInterval(() => {
      this.reportMetrics();
    }, this.config.reportInterval);
  }

  private initializeWebVitals(): void {
    // First Contentful Paint
    this.observePerformanceEntry('paint', (entries) => {
      const fcpEntry = entries.find((entry) => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        this.recordMetric('firstContentfulPaint', fcpEntry.startTime);
      }
    });

    // Largest Contentful Paint
    this.observePerformanceEntry('largest-contentful-paint', (entries) => {
      const lcpEntry = entries[entries.length - 1];
      if (lcpEntry) {
        this.recordMetric('largestContentfulPaint', lcpEntry.startTime);
      }
    });

    // Cumulative Layout Shift
    this.observePerformanceEntry('layout-shift', (entries) => {
      let clsValue = 0;
      entries.forEach((entry) => {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      });
      this.recordMetric('cumulativeLayoutShift', clsValue);
    });

    // First Input Delay
    this.observePerformanceEntry('first-input', (entries) => {
      const fidEntry = entries[0] as any;
      if (fidEntry && fidEntry.processingStart) {
        const fid = fidEntry.processingStart - fidEntry.startTime;
        this.recordMetric('firstInputDelay', fid);
      }
    });

    // Time to Interactive (approximation)
    if ('performance' in window && 'getEntriesByType' in performance) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const navEntry = performance.getEntriesByType(
            'navigation'
          )[0] as PerformanceNavigationTiming;
          if (navEntry) {
            const tti = navEntry.domInteractive - navEntry.fetchStart;
            this.recordMetric('timeToInteractive', tti);
          }
        }, 0);
      });
    }
  }

  private initializeErrorTracking(): void {
    // Global error handler
    window.addEventListener('error', (event) => {
      this.errorCount++;
      this.recordError({
        type: 'javascript',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: Date.now(),
      });
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.errorCount++;
      this.recordError({
        type: 'promise',
        message: event.reason?.message || 'Unhandled promise rejection',
        reason: event.reason,
        timestamp: Date.now(),
      });
    });

    // Network error tracking
    this.interceptFetch();
  }

  private initializeRUM(): void {
    // Track user interactions
    ['click', 'scroll', 'keydown'].forEach((eventType) => {
      document.addEventListener(eventType, this.trackUserInteraction.bind(this), { passive: true });
    });

    // Track memory usage
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        if (memory) {
          this.recordMetric('memoryUsage', memory.usedJSHeapSize);
        }
      }, 30000); // Every 30 seconds
    }

    // Track bundle size
    if ('getEntriesByType' in performance) {
      const resourceEntries = performance.getEntriesByType(
        'resource'
      ) as PerformanceResourceTiming[];
      const jsResources = resourceEntries.filter(
        (entry) => entry.name.includes('.js') && !entry.name.includes('node_modules')
      );
      const totalSize = jsResources.reduce((sum, entry) => sum + (entry.transferSize || 0), 0);
      this.recordMetric('bundleSize', totalSize);
    }
  }

  private observePerformanceEntry(
    entryType: string,
    callback: (entries: PerformanceEntry[]) => void
  ): void {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries());
      });
      observer.observe({ entryTypes: [entryType] });
    }
  }

  private recordMetric(metric: keyof PerformanceMetrics, value: number): void {
    // Add to current metrics
    const currentMetrics = this.getCurrentMetrics();
    currentMetrics[metric] = value;

    // Check quality gates
    this.checkQualityGates(metric, value);

    // Buffer metrics for reporting
    if (this.metricsBuffer.length >= this.config.bufferSize) {
      this.metricsBuffer.shift();
    }
    this.metricsBuffer.push(currentMetrics);
  }

  private getCurrentMetrics(): PerformanceMetrics {
    return {
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      cumulativeLayoutShift: 0,
      firstInputDelay: 0,
      timeToInteractive: 0,
      apiResponseTime: 0,
      bundleSize: 0,
      memoryUsage: 0,
      errorCount: this.errorCount,
    };
  }

  private checkQualityGates(metric: keyof PerformanceMetrics, value: number): void {
    const applicableGates = this.config.qualityGates.filter((gate) => gate.metric === metric);

    for (const gate of applicableGates) {
      const passed = this.evaluateGate(gate, value);

      if (!passed) {
        const alert = {
          gate: gate.name,
          metric: gate.metric,
          value: value,
          threshold: gate.threshold,
          critical: gate.critical,
          timestamp: Date.now(),
        };

        if (gate.critical) {
          console.error('🚨 Critical Quality Gate Failed:', alert);
          // Could trigger alerts, notifications, etc.
        } else {
          console.warn('⚠️ Quality Gate Warning:', alert);
        }

        // Report quality gate violation
        this.reportQualityGateViolation(alert);
      }
    }
  }

  private evaluateGate(gate: QualityGate, value: number): boolean {
    switch (gate.operator) {
      case 'lt':
        return value < gate.threshold;
      case 'lte':
        return value <= gate.threshold;
      case 'gt':
        return value > gate.threshold;
      case 'gte':
        return value >= gate.threshold;
      case 'eq':
        return value === gate.threshold;
      default:
        return false;
    }
  }

  private recordError(error: any): void {
    // Send error to monitoring service
    if (featureFlags.isEnabled('performance-monitoring')) {
      console.error('Recorded error:', error);
      // In a real implementation, this would send to an error tracking service
    }
  }

  private interceptFetch(): void {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();

      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const responseTime = endTime - startTime;

        this.recordMetric('apiResponseTime', responseTime);

        if (!response.ok) {
          this.errorCount++;
          this.recordError({
            type: 'http',
            status: response.status,
            statusText: response.statusText,
            url: args[0],
            responseTime,
            timestamp: Date.now(),
          });
        }

        return response;
      } catch (error) {
        const endTime = performance.now();
        const responseTime = endTime - startTime;

        this.errorCount++;
        this.recordError({
          type: 'network',
          message: error instanceof Error ? error.message : 'Network error',
          url: args[0],
          responseTime,
          timestamp: Date.now(),
        });

        throw error;
      }
    };
  }

  private trackUserInteraction(event: Event): void {
    // Track user interaction patterns for UX analysis
    if (featureFlags.isEnabled('advanced-monitoring')) {
      // This could be sent to analytics service
      console.debug('User interaction:', {
        type: event.type,
        target: (event.target as Element)?.tagName,
        timestamp: Date.now(),
      });
    }
  }

  private reportMetrics(): void {
    if (this.metricsBuffer.length === 0) return;

    const aggregatedMetrics = this.aggregateMetrics();

    if (featureFlags.isEnabled('performance-monitoring')) {
      console.log('📊 Performance Metrics:', aggregatedMetrics);

      // In a real implementation, send to monitoring service
      // fetch(this.config.apiEndpoint, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(aggregatedMetrics)
      // });
    }

    // Clear buffer
    this.metricsBuffer = [];
  }

  private aggregateMetrics(): any {
    if (this.metricsBuffer.length === 0) return null;

    const latest = this.metricsBuffer[this.metricsBuffer.length - 1];
    const uptime = Date.now() - this.startTime;

    return {
      ...latest,
      uptime,
      sessionId: this.generateSessionId(),
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
  }

  private reportQualityGateViolation(alert: any): void {
    // In a real implementation, this would send alerts to monitoring service
    console.log('Quality Gate Alert:', alert);
  }

  private generateSessionId(): string {
    return Math.random().toString(36).substr(2, 9);
  }

  // Public API
  public getMetrics(): PerformanceMetrics | null {
    return this.metricsBuffer.length > 0 ? this.metricsBuffer[this.metricsBuffer.length - 1] : null;
  }

  public forceReport(): void {
    this.reportMetrics();
  }

  public updateConfig(newConfig: Partial<MonitoringConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

// Default monitoring configuration
export const defaultMonitoringConfig: MonitoringConfig = {
  enabled: true,
  apiEndpoint: '/api/monitoring/metrics',
  reportInterval: 60000, // 1 minute
  bufferSize: 10,
  enableRealUserMonitoring: true,
  enableErrorTracking: true,
  enablePerformanceTracking: true,
  qualityGates: [
    {
      name: 'First Contentful Paint',
      metric: 'firstContentfulPaint',
      threshold: 1500, // 1.5 seconds
      operator: 'lt',
      critical: false,
    },
    {
      name: 'Largest Contentful Paint',
      metric: 'largestContentfulPaint',
      threshold: 2500, // 2.5 seconds
      operator: 'lt',
      critical: true,
    },
    {
      name: 'Cumulative Layout Shift',
      metric: 'cumulativeLayoutShift',
      threshold: 0.1,
      operator: 'lt',
      critical: false,
    },
    {
      name: 'First Input Delay',
      metric: 'firstInputDelay',
      threshold: 100, // 100ms
      operator: 'lt',
      critical: false,
    },
    {
      name: 'Bundle Size',
      metric: 'bundleSize',
      threshold: 500000, // 500KB
      operator: 'lt',
      critical: false,
    },
    {
      name: 'API Response Time',
      metric: 'apiResponseTime',
      threshold: 2000, // 2 seconds
      operator: 'lt',
      critical: true,
    },
    {
      name: 'Error Count',
      metric: 'errorCount',
      threshold: 5,
      operator: 'lt',
      critical: true,
    },
  ],
};

// Global monitoring instance
export const monitoring = new AdvancedMonitoring(defaultMonitoringConfig);

// Development utilities
export const monitoringDevTools = {
  getMetrics: () => monitoring.getMetrics(),
  forceReport: () => monitoring.forceReport(),
  getConfig: () => defaultMonitoringConfig,
  simulateError: () => {
    throw new Error('Simulated error for testing');
  },
  simulateSlowAPI: async () => {
    const start = performance.now();
    await new Promise((resolve) => setTimeout(resolve, 3000));
    const end = performance.now();
    console.log(`Simulated slow API took ${end - start}ms`);
  },
};

// Make dev tools available in development
if (browser && window.location.hostname === 'localhost') {
  (window as any).__monitoring = monitoringDevTools;
}
