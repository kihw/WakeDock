/**
 * Security Audit Logger
 * Specialized logging for security-related events with enhanced metadata
 */

import { logger, LogLevel } from './logger';

export enum AuditCategory {
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  DATA_ACCESS = 'data_access',
  CONFIGURATION = 'configuration',
  USER_MANAGEMENT = 'user_management',
  CONTENT_SECURITY = 'content_security',
  SYSTEM = 'system',
}

export enum AuditAction {
  // Authentication actions
  LOGIN_SUCCESS = 'login_success',
  LOGIN_FAILURE = 'login_failure',
  LOGOUT = 'logout',
  TOKEN_REFRESH = 'token_refresh',
  MFA_SUCCESS = 'mfa_success',
  MFA_FAILURE = 'mfa_failure',
  PASSWORD_CHANGE = 'password_change',
  PASSWORD_RESET = 'password_reset',

  // Authorization actions
  ACCESS_GRANTED = 'access_granted',
  ACCESS_DENIED = 'access_denied',
  PERMISSION_CHANGE = 'permission_change',

  // Data actions
  DATA_CREATE = 'data_create',
  DATA_READ = 'data_read',
  DATA_UPDATE = 'data_update',
  DATA_DELETE = 'data_delete',
  DATA_EXPORT = 'data_export',

  // System actions
  CONFIG_CHANGE = 'config_change',
  FEATURE_FLAG_CHANGE = 'feature_flag_change',
  API_KEY_GENERATE = 'api_key_generate',
  API_KEY_REVOKE = 'api_key_revoke',

  // User management
  USER_CREATE = 'user_create',
  USER_UPDATE = 'user_update',
  USER_DELETE = 'user_delete',
  ROLE_CHANGE = 'role_change',

  // Security events
  SUSPICIOUS_ACTIVITY = 'suspicious_activity',
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded',
  XSS_ATTEMPT = 'xss_attempt',
  CSRF_VIOLATION = 'csrf_violation',
  INPUT_VALIDATION_FAILURE = 'input_validation_failure',
}

export interface AuditLogEntry {
  id?: string;
  timestamp?: string;
  category: AuditCategory;
  action: AuditAction;
  status: 'success' | 'failure';
  targetResource?: string;
  targetId?: string;
  details?: Record<string, any>;
  sourceIp?: string;
  userAgent?: string;
  userId?: string;
}

// Storage key specific to audit logs
const AUDIT_STORAGE_KEY = 'wakedock-audit-logs';

// Maximum number of audit logs to keep in storage
const MAX_AUDIT_LOGS = 500;

/**
 * Security Audit Logger Class
 * Records security-relevant events with enhanced contextual information
 */
class AuditLogger {
  /**
   * Log a security audit event
   */
  log(entry: AuditLogEntry): void {
    // Determine log level based on status and category
    const level = this.determineLogLevel(entry);

    // Extract common browser metadata
    const metadata = this.getBrowserMetadata();

    // Build the audit message
    const message = `AUDIT: ${entry.category}/${entry.action} [${entry.status}]${entry.targetResource ? ` on ${entry.targetResource}` : ''}`;

    // Combine all context
    const context = {
      audit: {
        ...entry,
        ...metadata,
      },
    };

    // Log via the regular logger
    logger.logEntry(level, message, context);

    // Store in browser for history
    this.storeAuditLog({
      ...entry,
      ...metadata,
      id: entry.id || this.generateId(),
      timestamp: entry.timestamp || new Date().toISOString(),
      userId: entry.userId || this.getCurrentUserId(),
    });
  }

  /**
   * Determine appropriate log level based on the audit entry
   */
  private determineLogLevel(entry: AuditLogEntry): LogLevel {
    // Failed authentication and suspicious activity are errors
    if (entry.status === 'failure') {
      if (
        entry.category === AuditCategory.AUTHENTICATION ||
        entry.action === AuditAction.SUSPICIOUS_ACTIVITY ||
        entry.action === AuditAction.XSS_ATTEMPT ||
        entry.action === AuditAction.CSRF_VIOLATION
      ) {
        return LogLevel.ERROR;
      }
      return LogLevel.WARN;
    }

    // Data modifications are info
    if (entry.category === AuditCategory.DATA_ACCESS) {
      if (entry.action === AuditAction.DATA_DELETE) {
        return LogLevel.WARN;
      }
      return LogLevel.INFO;
    }

    // Default level for most logs
    return LogLevel.INFO;
  }

  /**
   * Extract browser metadata for audit context
   */
  private getBrowserMetadata(): Partial<AuditLogEntry> {
    if (typeof window === 'undefined') {
      return {};
    }

    return {
      sourceIp: '', // Will be set by server
      userAgent: navigator.userAgent,
    };
  }

  /**
   * Get current user ID from authentication store
   */
  private getCurrentUserId(): string | undefined {
    try {
      if (typeof window !== 'undefined') {
        const authData = localStorage.getItem('auth-user');
        if (authData) {
          const user = JSON.parse(authData);
          return user.id;
        }
      }
    } catch {
      // Ignore parsing errors
    }
    return undefined;
  }

  /**
   * Generate a unique ID for an audit log entry
   */
  private generateId(): string {
    return `audit-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Store audit log in browser storage
   */
  private storeAuditLog(entry: AuditLogEntry & { id: string; timestamp: string }): void {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      // Get existing logs
      const existingLogsJson = localStorage.getItem(AUDIT_STORAGE_KEY);
      let logs: Array<AuditLogEntry & { id: string; timestamp: string }> = [];

      if (existingLogsJson) {
        logs = JSON.parse(existingLogsJson);
      }

      // Add new log
      logs.push(entry);

      // Keep only the most recent logs to prevent storage overflow
      if (logs.length > MAX_AUDIT_LOGS) {
        logs = logs.slice(-MAX_AUDIT_LOGS);
      }

      // Store back to localStorage
      localStorage.setItem(AUDIT_STORAGE_KEY, JSON.stringify(logs));
    } catch (error) {
      console.error('Failed to store audit log:', error);
    }
  }

  /**
   * Get all stored audit logs
   */
  getAllLogs(): Array<AuditLogEntry & { id: string; timestamp: string }> {
    if (typeof window === 'undefined') {
      return [];
    }

    try {
      const logsJson = localStorage.getItem(AUDIT_STORAGE_KEY);
      if (logsJson) {
        return JSON.parse(logsJson);
      }
    } catch (error) {
      console.error('Failed to retrieve audit logs:', error);
    }

    return [];
  }

  /**
   * Clear all stored audit logs
   */
  clearAllLogs(): void {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      localStorage.removeItem(AUDIT_STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear audit logs:', error);
    }
  }

  /**
   * Delete a specific audit log by ID
   */
  deleteLog(id: string): boolean {
    if (typeof window === 'undefined') {
      return false;
    }

    try {
      const logsJson = localStorage.getItem(AUDIT_STORAGE_KEY);
      if (!logsJson) {
        return false;
      }

      const logs = JSON.parse(logsJson);
      const initialLength = logs.length;
      const filteredLogs = logs.filter((log: any) => log.id !== id);

      if (filteredLogs.length === initialLength) {
        return false; // No log was removed
      }

      localStorage.setItem(AUDIT_STORAGE_KEY, JSON.stringify(filteredLogs));
      return true;
    } catch (error) {
      console.error('Failed to delete audit log:', error);
      return false;
    }
  }

  /**
   * Export audit logs to CSV
   */
  exportToCSV(): string {
    const logs = this.getAllLogs();
    if (logs.length === 0) {
      return '';
    }

    // Define CSV headers
    const headers = [
      'ID',
      'Timestamp',
      'Category',
      'Action',
      'Status',
      'Target Resource',
      'Target ID',
      'User ID',
      'Source IP',
      'User Agent',
      'Details',
    ];

    // Convert logs to CSV rows
    const csvRows = logs.map((log) => {
      return [
        log.id || '',
        log.timestamp || '',
        log.category || '',
        log.action || '',
        log.status || '',
        log.targetResource || '',
        log.targetId || '',
        log.userId || '',
        log.sourceIp || '',
        log.userAgent ? `"${log.userAgent.replace(/"/g, '""')}"` : '',
        log.details ? `"${JSON.stringify(log.details).replace(/"/g, '""')}"` : '',
      ].join(',');
    });

    // Combine headers and rows
    return [headers.join(','), ...csvRows].join('\n');
  }

  /**
   * Download audit logs as CSV file
   */
  downloadCSV(): void {
    if (typeof window === 'undefined') {
      return;
    }

    const csv = this.exportToCSV();
    if (!csv) {
      console.warn('No audit logs to export');
      return;
    }

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `wakedock-audit-logs-${timestamp}.csv`);
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Send audit logs to server for permanent storage
   * @param endpoint Server endpoint to send logs to
   * @returns Promise resolving to success status
   */
  async syncWithServer(endpoint: string): Promise<boolean> {
    if (typeof window === 'undefined' || !endpoint) {
      return false;
    }

    try {
      const logs = this.getAllLogs();
      if (logs.length === 0) {
        return true; // Nothing to sync
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      return true;
    } catch (error) {
      console.error('Failed to sync audit logs with server:', error);
      return false;
    }
  }

  /**
   * Helper: Log successful authentication
   */
  logAuthSuccess(userId: string, details?: Record<string, any>): void {
    this.log({
      category: AuditCategory.AUTHENTICATION,
      action: AuditAction.LOGIN_SUCCESS,
      status: 'success',
      targetResource: 'user',
      targetId: userId,
      details,
      userId,
    });
  }

  /**
   * Helper: Log failed authentication
   */
  logAuthFailure(userId: string, details?: Record<string, any>): void {
    this.log({
      category: AuditCategory.AUTHENTICATION,
      action: AuditAction.LOGIN_FAILURE,
      status: 'failure',
      targetResource: 'user',
      targetId: userId,
      details,
      userId,
    });
  }

  /**
   * Helper: Log data access
   */
  logDataAccess(
    action: AuditAction,
    resource: string,
    resourceId: string,
    status: 'success' | 'failure',
    details?: Record<string, any>
  ): void {
    this.log({
      category: AuditCategory.DATA_ACCESS,
      action,
      status,
      targetResource: resource,
      targetId: resourceId,
      details,
    });
  }

  /**
   * Helper: Log security event
   */
  logSecurityEvent(action: AuditAction, details?: Record<string, any>): void {
    this.log({
      category: AuditCategory.CONTENT_SECURITY,
      action,
      status: 'failure',
      details,
    });
  }

  /**
   * Get audit logs for display (alias for getAllLogs)
   */
  getAuditLogs(): AuditLogEntry[] {
    return this.getAllLogs();
  }

  /**
   * Export audit logs to CSV (alias for exportToCSV)
   */
  exportAuditLogs(): string {
    return this.exportToCSV();
  }

  /**
   * Clear all audit logs
   */
  clearAuditLogs(): void {
    this.clearAllLogs();
  }
}

// Export singleton instance
export const auditLogger = new AuditLogger();

// Export a simpler function for component usage
export const securityAudit = {
  log: (
    category: AuditCategory,
    action: AuditAction,
    status: 'success' | 'failure',
    details?: Record<string, any>
  ) => {
    auditLogger.log({ category, action, status, details });
  },
  dataAccess: (action: string, resource: string, details?: Record<string, any>) => {
    auditLogger.logDataAccess(
      action === 'read'
        ? AuditAction.DATA_READ
        : action === 'create'
          ? AuditAction.DATA_CREATE
          : action === 'update'
            ? AuditAction.DATA_UPDATE
            : action === 'delete'
              ? AuditAction.DATA_DELETE
              : AuditAction.DATA_READ,
      'security_dashboard',
      resource,
      'success',
      details
    );
  },
};
