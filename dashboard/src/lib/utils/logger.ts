/**
 * Logger Utility
 * Structured logging for the application
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4,
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
  error?: Error;
  userId?: string;
  sessionId?: string;
}

export interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  enableStorage: boolean;
  maxStorageEntries: number;
  includeStackTrace: boolean;
}

class Logger {
  private config: LoggerConfig;
  private storageKey = 'wakedock-logs';
  private sessionId: string;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      level: LogLevel.INFO,
      enableConsole: true,
      enableStorage: true,
      maxStorageEntries: 1000,
      includeStackTrace: false,
      ...config,
    };

    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private shouldLog(level: LogLevel): boolean {
    return level >= this.config.level;
  }

  private formatMessage(level: LogLevel, message: string, context?: Record<string, any>): string {
    const timestamp = new Date().toISOString();
    const levelName = LogLevel[level];
    const contextStr = context ? ` ${JSON.stringify(context)}` : '';

    return `[${timestamp}] ${levelName}: ${message}${contextStr}`;
  }

  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      error,
      sessionId: this.sessionId,
      userId: this.getCurrentUserId(),
    };
  }

  private getCurrentUserId(): string | undefined {
    // Essayer de récupérer l'ID utilisateur depuis le store ou le localStorage
    try {
      if (typeof window !== 'undefined') {
        const authData = localStorage.getItem('auth-user');
        if (authData) {
          const user = JSON.parse(authData);
          return user.id;
        }
      }
    } catch {
      // Ignorer les erreurs de parsing
    }
    return undefined;
  }

  private writeToConsole(entry: LogEntry): void {
    if (!this.config.enableConsole) return;

    const formattedMessage = this.formatMessage(entry.level, entry.message, entry.context);

    switch (entry.level) {
      case LogLevel.DEBUG:
        console.debug(formattedMessage);
        break;
      case LogLevel.INFO:
        console.info(formattedMessage);
        break;
      case LogLevel.WARN:
        console.warn(formattedMessage);
        break;
      case LogLevel.ERROR:
      case LogLevel.FATAL:
        if (entry.error && this.config.includeStackTrace) {
          console.error(formattedMessage, entry.error);
        } else {
          console.error(formattedMessage);
        }
        break;
    }
  }

  private writeToStorage(entry: LogEntry): void {
    if (!this.config.enableStorage || typeof window === 'undefined') return;

    try {
      const existingLogs = this.getStoredLogs();
      existingLogs.push(entry);

      // Limiter le nombre d'entrées stockées
      if (existingLogs.length > this.config.maxStorageEntries) {
        existingLogs.splice(0, existingLogs.length - this.config.maxStorageEntries);
      }

      localStorage.setItem(this.storageKey, JSON.stringify(existingLogs));
    } catch (error) {
      // En cas d'erreur de stockage, écrire au moins dans la console
      console.error('Failed to store log entry:', error);
    }
  }

  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): void {
    if (!this.shouldLog(level)) return;

    const entry = this.createLogEntry(level, message, context, error);

    this.writeToConsole(entry);
    this.writeToStorage(entry);
  }

  /**
   * Public log method that can be used by other loggers
   * @param level Log level
   * @param message Log message
   * @param context Additional context
   * @param error Optional error object
   */
  public logEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): void {
    this.log(level, message, context, error);
  }

  /**
   * Log niveau DEBUG
   */
  debug(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  /**
   * Log niveau INFO
   */
  info(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, context);
  }

  /**
   * Log niveau WARN
   */
  warn(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, context);
  }

  /**
   * Log niveau ERROR
   */
  error(message: string, error?: Error, context?: Record<string, any>): void {
    this.log(LogLevel.ERROR, message, context, error);
  }

  /**
   * Log niveau FATAL
   */
  fatal(message: string, error?: Error, context?: Record<string, any>): void {
    this.log(LogLevel.FATAL, message, context, error);
  }

  /**
   * Récupère les logs stockés
   */
  getStoredLogs(): LogEntry[] {
    if (typeof window === 'undefined') return [];

    try {
      const stored = localStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  /**
   * Vide les logs stockés
   */
  clearStoredLogs(): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.removeItem(this.storageKey);
    } catch (error) {
      this.error(
        'Failed to clear stored logs',
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Exporte les logs sous forme de chaîne
   */
  exportLogs(): string {
    const logs = this.getStoredLogs();
    return logs
      .map((entry) => this.formatMessage(entry.level, entry.message, entry.context))
      .join('\n');
  }

  /**
   * Configure le logger
   */
  configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Obtient la configuration actuelle
   */
  getConfig(): LoggerConfig {
    return { ...this.config };
  }
}

// Instance singleton du logger
export const logger = new Logger();

// Helpers pour différents contextes
export const apiLogger = {
  request: (method: string, url: string, data?: any) => {
    // Only log non-polling requests to reduce noise
    if (!url.includes('/health') && !url.includes('/ping')) {
      logger.debug(`API Request: ${method} ${url}`, { method, url, data });
    }
  },
  response: (method: string, url: string, status: number, data?: any) => {
    // Only log non-polling responses and errors
    if (!url.includes('/health') && !url.includes('/ping')) {
      if (status >= 400) {
        logger.warn(`API Response: ${method} ${url} - ${status}`, { method, url, status, data });
      } else {
        logger.debug(`API Response: ${method} ${url} - ${status}`, { method, url, status });
      }
    }
  },
  error: (method: string, url: string, error: Error) => {
    logger.error(`API Error: ${method} ${url}`, error, { method, url });
  },
};

export const uiLogger = {
  action: (component: string, action: string, data?: any) => {
    logger.debug(`UI Action: ${component}.${action}`, { component, action, data });
  },
  error: (component: string, error: Error, context?: any) => {
    logger.error(`UI Error in ${component}`, error, { component, context });
  },
};

export const performanceLogger = {
  measure: (name: string, startTime: number, endTime?: number) => {
    const end = endTime || performance.now();
    const duration = end - startTime;
    logger.info(`Performance: ${name} took ${duration.toFixed(2)}ms`, { name, duration });
  },
  mark: (name: string) => {
    const timestamp = performance.now();
    logger.debug(`Performance Mark: ${name}`, { name, timestamp });
    return timestamp;
  },
};

// Configuration pour différents environnements
export const loggerConfigs = {
  development: {
    level: LogLevel.DEBUG,
    enableConsole: true,
    enableStorage: true,
    includeStackTrace: true,
  },
  production: {
    level: LogLevel.ERROR,
    enableConsole: false,
    enableStorage: false,
    includeStackTrace: false,
  },
  test: {
    level: LogLevel.ERROR,
    enableConsole: false,
    enableStorage: false,
    includeStackTrace: true,
  },
};

// Auto-configuration basée sur l'environnement
if (typeof window !== 'undefined') {
  const isDev = process.env.NODE_ENV === 'development' || 
    window.location.hostname === 'localhost' || 
    window.location.hostname === '127.0.0.1';
  const isTest = process.env.NODE_ENV === 'test' || window.location.search.includes('test=true');

  if (isTest) {
    logger.configure(loggerConfigs.test);
  } else if (isDev) {
    logger.configure(loggerConfigs.development);
  } else {
    logger.configure(loggerConfigs.production);
  }
}
