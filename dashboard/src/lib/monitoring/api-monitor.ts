/**
 * API Performance Monitoring
 * Tracks API response times, errors, and circuit breaker status
 */

export interface ApiMetrics {
    requestCount: number;
    errorCount: number;
    averageResponseTime: number;
    circuitBreakerStatus: Record<string, {
        failures: number;
        isOpen: boolean;
        lastFailure: number | null;
    }>;
    networkStatus: {
        isOnline: boolean;
        lastCheck: number;
    };
}

export class ApiMonitor {
    private metrics: Map<string, {
        requestCount: number;
        errorCount: number;
        totalResponseTime: number;
        lastRequestTime: number;
    }> = new Map();

    private circuitBreakerStats: Map<string, {
        failures: number;
        isOpen: boolean;
        lastFailure: number | null;
    }> = new Map();

    private networkStatus = {
        isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
        lastCheck: Date.now()
    };

    constructor() {
        // Monitor network status
        if (typeof window !== 'undefined') {
            window.addEventListener('online', () => {
                this.networkStatus.isOnline = true;
                this.networkStatus.lastCheck = Date.now();
            });

            window.addEventListener('offline', () => {
                this.networkStatus.isOnline = false;
                this.networkStatus.lastCheck = Date.now();
            });
        }
    }

    /**
     * Record successful API request
     */
    recordSuccess(endpoint: string, responseTime: number): void {
        const stats = this.metrics.get(endpoint) || {
            requestCount: 0,
            errorCount: 0,
            totalResponseTime: 0,
            lastRequestTime: 0
        };

        stats.requestCount++;
        stats.totalResponseTime += responseTime;
        stats.lastRequestTime = Date.now();

        this.metrics.set(endpoint, stats);

        // Reset circuit breaker on success
        this.circuitBreakerStats.set(endpoint, {
            failures: 0,
            isOpen: false,
            lastFailure: null
        });
    }

    /**
     * Record failed API request
     */
    recordError(endpoint: string, error: any): void {
        const stats = this.metrics.get(endpoint) || {
            requestCount: 0,
            errorCount: 0,
            totalResponseTime: 0,
            lastRequestTime: 0
        };

        stats.requestCount++;
        stats.errorCount++;
        stats.lastRequestTime = Date.now();

        this.metrics.set(endpoint, stats);

        // Update circuit breaker stats
        const cbStats = this.circuitBreakerStats.get(endpoint) || {
            failures: 0,
            isOpen: false,
            lastFailure: null
        };

        cbStats.failures++;
        cbStats.lastFailure = Date.now();
        cbStats.isOpen = cbStats.failures >= 5; // Threshold

        this.circuitBreakerStats.set(endpoint, cbStats);
    }

    /**
     * Get metrics for a specific endpoint
     */
    getEndpointMetrics(endpoint: string): {
        requestCount: number;
        errorCount: number;
        errorRate: number;
        averageResponseTime: number;
        lastRequestTime: number;
    } | null {
        const stats = this.metrics.get(endpoint);
        if (!stats) return null;

        return {
            requestCount: stats.requestCount,
            errorCount: stats.errorCount,
            errorRate: stats.requestCount > 0 ? (stats.errorCount / stats.requestCount) * 100 : 0,
            averageResponseTime: stats.requestCount > 0 ? stats.totalResponseTime / stats.requestCount : 0,
            lastRequestTime: stats.lastRequestTime
        };
    }

    /**
     * Get overall API metrics
     */
    getOverallMetrics(): ApiMetrics {
        let totalRequests = 0;
        let totalErrors = 0;
        let totalResponseTime = 0;

        for (const stats of this.metrics.values()) {
            totalRequests += stats.requestCount;
            totalErrors += stats.errorCount;
            totalResponseTime += stats.totalResponseTime;
        }

        const circuitBreakerStatus: Record<string, {
            failures: number;
            isOpen: boolean;
            lastFailure: number | null;
        }> = {};

        for (const [endpoint, stats] of this.circuitBreakerStats.entries()) {
            circuitBreakerStatus[endpoint] = { ...stats };
        }

        return {
            requestCount: totalRequests,
            errorCount: totalErrors,
            averageResponseTime: totalRequests > 0 ? totalResponseTime / totalRequests : 0,
            circuitBreakerStatus,
            networkStatus: { ...this.networkStatus }
        };
    }

    /**
     * Get endpoints with high error rates
     */
    getProblematicEndpoints(errorRateThreshold: number = 10): string[] {
        const problematic: string[] = [];

        for (const [endpoint, stats] of this.metrics.entries()) {
            const errorRate = stats.requestCount > 0 ? (stats.errorCount / stats.requestCount) * 100 : 0;
            if (errorRate >= errorRateThreshold && stats.requestCount >= 5) {
                problematic.push(endpoint);
            }
        }

        return problematic;
    }

    /**
     * Get slow endpoints
     */
    getSlowEndpoints(responseTimeThreshold: number = 5000): string[] {
        const slow: string[] = [];

        for (const [endpoint, stats] of this.metrics.entries()) {
            const avgResponseTime = stats.requestCount > 0 ? stats.totalResponseTime / stats.requestCount : 0;
            if (avgResponseTime >= responseTimeThreshold && stats.requestCount >= 3) {
                slow.push(endpoint);
            }
        }

        return slow;
    }

    /**
     * Generate performance report
     */
    generateReport(): string {
        const overall = this.getOverallMetrics();
        const problematic = this.getProblematicEndpoints();
        const slow = this.getSlowEndpoints();

        const lines = [
            '=== API Performance Report ===',
            `Generated at: ${new Date().toISOString()}`,
            '',
            '--- Overall Statistics ---',
            `Total requests: ${overall.requestCount}`,
            `Total errors: ${overall.errorCount}`,
            `Error rate: ${overall.requestCount > 0 ? ((overall.errorCount / overall.requestCount) * 100).toFixed(2) : 0}%`,
            `Average response time: ${overall.averageResponseTime.toFixed(2)}ms`,
            `Network status: ${overall.networkStatus.isOnline ? 'Online' : 'Offline'}`,
            '',
            '--- Circuit Breaker Status ---'
        ];

        if (Object.keys(overall.circuitBreakerStatus).length > 0) {
            for (const [endpoint, status] of Object.entries(overall.circuitBreakerStatus)) {
                lines.push(`${endpoint}: ${status.isOpen ? 'OPEN' : 'CLOSED'} (${status.failures} failures)`);
            }
        } else {
            lines.push('No circuit breakers active');
        }

        lines.push('');
        lines.push('--- Problematic Endpoints ---');
        if (problematic.length > 0) {
            for (const endpoint of problematic) {
                const metrics = this.getEndpointMetrics(endpoint);
                if (metrics) {
                    lines.push(`${endpoint}: ${metrics.errorRate.toFixed(2)}% error rate (${metrics.errorCount}/${metrics.requestCount})`);
                }
            }
        } else {
            lines.push('No problematic endpoints detected');
        }

        lines.push('');
        lines.push('--- Slow Endpoints ---');
        if (slow.length > 0) {
            for (const endpoint of slow) {
                const metrics = this.getEndpointMetrics(endpoint);
                if (metrics) {
                    lines.push(`${endpoint}: ${metrics.averageResponseTime.toFixed(2)}ms average`);
                }
            }
        } else {
            lines.push('No slow endpoints detected');
        }

        lines.push('');
        lines.push('--- Endpoint Details ---');
        for (const [endpoint, stats] of this.metrics.entries()) {
            const metrics = this.getEndpointMetrics(endpoint);
            if (metrics) {
                lines.push(`${endpoint}:`);
                lines.push(`  Requests: ${metrics.requestCount}`);
                lines.push(`  Errors: ${metrics.errorCount} (${metrics.errorRate.toFixed(2)}%)`);
                lines.push(`  Avg response: ${metrics.averageResponseTime.toFixed(2)}ms`);
                lines.push(`  Last request: ${new Date(metrics.lastRequestTime).toISOString()}`);
                lines.push('');
            }
        }

        return lines.join('\n');
    }

    /**
     * Export metrics as JSON
     */
    exportMetrics(): object {
        const overall = this.getOverallMetrics();
        const endpoints: Record<string, any> = {};

        for (const [endpoint, stats] of this.metrics.entries()) {
            endpoints[endpoint] = this.getEndpointMetrics(endpoint);
        }

        return {
            timestamp: new Date().toISOString(),
            overall,
            endpoints,
            problematicEndpoints: this.getProblematicEndpoints(),
            slowEndpoints: this.getSlowEndpoints()
        };
    }

    /**
     * Clear all metrics
     */
    clear(): void {
        this.metrics.clear();
        this.circuitBreakerStats.clear();
    }
}

// Global API monitor instance
export const apiMonitor = new ApiMonitor();

// Expose to window for debugging
if (typeof window !== 'undefined') {
    (window as any).__WAKEDOCK_API_MONITOR__ = apiMonitor;
}
