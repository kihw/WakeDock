/**
 * Production-safe logging utility
 * Replaces console.log statements with proper logging for production
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: string;
  metadata?: Record<string, any>;
  error?: Error;
}

class ProductionLogger {
  private isProduction = typeof window !== 'undefined'
    ? window.location.hostname !== 'localhost'
    : process.env.NODE_ENV === 'production';

  private isDevelopment = !this.isProduction;
  private remoteEndpoint?: string;
  private buffer: LogEntry[] = [];
  private maxBufferSize = 100;

  /**
   * Log debug information (development only)
   */
  debug(message: string, context?: string, metadata?: Record<string, any>): void {
    if (this.isDevelopment) {
      this.log('debug', message, context, metadata);
    }
  }

  /**
   * Log informational messages
   */
  info(message: string, context?: string, metadata?: Record<string, any>): void {
    this.log('info', message, context, metadata);
  }

  /**
   * Log warning messages
   */
  warn(message: string, context?: string, metadata?: Record<string, any>): void {
    this.log('warn', message, context, metadata);
  }

  /**
   * Log error messages
   */
  error(message: string, error?: Error, context?: string, metadata?: Record<string, any>): void {
    this.log('error', message, context, metadata, error);
  }

  /**
   * Internal logging method
   */
  private log(
    level: LogLevel,
    message: string,
    context?: string,
    metadata?: Record<string, any>,
    error?: Error
  ): void {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      metadata,
      error
    };

    // In development, use console methods
    if (this.isDevelopment) {
      const prefix = context ? `[${context}]` : '';
      const fullMessage = `${prefix} ${message}`;

      switch (level) {
        case 'debug':
          console.debug(fullMessage, metadata || '');
          break;
        case 'info':
          console.info(fullMessage, metadata || '');
          break;
        case 'warn':
          console.warn(fullMessage, metadata || '');
          break;
        case 'error':
          if (error) {
            console.error(fullMessage, error, metadata || '');
          } else {
            console.error(fullMessage, metadata || '');
          }
          break;
      }
    } else {
      // In production, send to logging service or suppress
      this.sendToLoggingService(logEntry);
    }
  }

  /**
   * Configure remote logging endpoint
   */
  setRemoteEndpoint(endpoint: string): void {
    this.remoteEndpoint = endpoint;
  }

  /**
   * Send logs to remote endpoint
   */
  private async sendToRemote(entry: LogEntry): Promise<void> {
    if (!this.remoteEndpoint || !this.isProduction) return;

    try {
      await fetch(this.remoteEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(entry)
      });
    } catch (error) {
      // Fallback to console in case of remote logging failure
      console.error('Failed to send log to remote endpoint:', error);
    }
  }

  /**
   * Send logs to external logging service in production
   */
  private sendToLoggingService(logEntry: LogEntry): void {
    // Only log warnings and errors in production
    if (logEntry.level === 'warn' || logEntry.level === 'error') {
      try {
        // Send to logging service (implement based on your logging infrastructure)
        // For now, we'll suppress most logs in production
        if (typeof window !== 'undefined' && window.navigator.sendBeacon) {
          const payload = JSON.stringify(logEntry);
          window.navigator.sendBeacon('/api/logs', payload);
        }
      } catch (error) {
        // Silently fail in production to prevent logging loops
      }
    }
  }

  /**
   * Performance timing helper
   */
  time(label: string): void {
    if (this.isDevelopment) {
      console.time(label);
    }
  }

  /**
   * End performance timing
   */
  timeEnd(label: string): void {
    if (this.isDevelopment) {
      console.timeEnd(label);
    }
  }

  /**
   * Group related log messages (development only)
   */
  group(label: string): void {
    if (this.isDevelopment) {
      console.group(label);
    }
  }

  /**
   * End log group
   */
  groupEnd(): void {
    if (this.isDevelopment) {
      console.groupEnd();
    }
  }
}

// Create singleton instance
export const logger = new ProductionLogger();

// Convenience functions for common patterns
export const logApiRequest = (method: string, url: string, duration?: number) => {
  logger.debug(`API ${method} ${url}`, 'API', { method, url, duration });
};

export const logApiError = (method: string, url: string, error: Error, status?: number) => {
  logger.error(`API ${method} ${url} failed`, error, 'API', { method, url, status });
};

export const logPerformance = (operation: string, duration: number, metadata?: Record<string, any>) => {
  if (duration > 1000) {
    logger.warn(`Slow operation: ${operation} took ${duration}ms`, 'Performance', metadata);
  } else {
    logger.debug(`${operation} completed in ${duration}ms`, 'Performance', metadata);
  }
};

export const logWebSocket = (event: string, data?: any) => {
  logger.debug(`WebSocket ${event}`, 'WebSocket', data);
};

export const logWebSocketError = (error: Error, context?: string) => {
  logger.error(`WebSocket error: ${context || 'Unknown'}`, error, 'WebSocket');
};

// Security logging helpers
export const logSecurityEvent = (event: string, details: Record<string, any>) => {
  logger.warn(`Security event: ${event}`, 'Security', details);
};

export const logSecurityError = (event: string, error: Error, details: Record<string, any>) => {
  logger.error(`Security error: ${event}`, error, 'Security', details);
};

// Component lifecycle logging
export const logComponentMount = (componentName: string, props?: Record<string, any>) => {
  logger.debug(`Component mounted: ${componentName}`, 'Component', props);
};

export const logComponentError = (componentName: string, error: Error, props?: Record<string, any>) => {
  logger.error(`Component error: ${componentName}`, error, 'Component', props);
};

// Default export
export default logger;