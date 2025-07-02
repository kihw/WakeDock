/**
 * Advanced Notification Service
 * Manages toast notifications, alerts, and system notifications
 */
import { writable, type Writable } from 'svelte/store';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  duration?: number; // Auto-dismiss after milliseconds, 0 for persistent
  persistent?: boolean; // Don't auto-dismiss
  actions?: NotificationAction[];
  icon?: string;
  dismissible?: boolean;
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

export interface NotificationOptions {
  type?: Notification['type'];
  duration?: number;
  persistent?: boolean;
  actions?: NotificationAction[];
  icon?: string;
  dismissible?: boolean;
}

class NotificationService {
  private notifications: Writable<Notification[]> = writable([]);
  private timers = new Map<string, NodeJS.Timeout>();

  constructor() {
    // Cleanup timers when notifications are removed
    this.notifications.subscribe((notifications) => {
      // Remove timers for notifications that no longer exist
      const existingIds = new Set(notifications.map((n) => n.id));
      for (const [id, timer] of this.timers.entries()) {
        if (!existingIds.has(id)) {
          clearTimeout(timer);
          this.timers.delete(id);
        }
      }
    });
  }

  /**
   * Get notifications store
   */
  get store(): Writable<Notification[]> {
    return this.notifications;
  }

  /**
   * Generate unique ID for notification
   */
  private generateId(): string {
    return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Add a notification
   */
  private addNotification(
    title: string,
    message: string,
    options: NotificationOptions = {}
  ): string {
    const id = this.generateId();
    const defaultDuration = this.getDefaultDuration(options.type || 'info');

    const notification: Notification = {
      id,
      type: options.type || 'info',
      title,
      message,
      timestamp: new Date(),
      duration: options.duration ?? defaultDuration,
      persistent: options.persistent || false,
      actions: options.actions || [],
      icon: options.icon,
      dismissible: options.dismissible ?? true,
    };

    this.notifications.update((notifications) => [notification, ...notifications]);

    // Set auto-dismiss timer if not persistent
    if (!notification.persistent && notification.duration && notification.duration > 0) {
      const timer = setTimeout(() => {
        this.dismiss(id);
      }, notification.duration);

      this.timers.set(id, timer);
    }

    return id;
  }

  /**
   * Get default duration based on notification type
   */
  private getDefaultDuration(type: Notification['type']): number {
    switch (type) {
      case 'error':
        return 8000; // 8 seconds
      case 'warning':
        return 6000; // 6 seconds
      case 'success':
        return 4000; // 4 seconds
      case 'info':
      default:
        return 5000; // 5 seconds
    }
  }

  /**
   * Show info notification
   */
  info(title: string, message: string, options?: Omit<NotificationOptions, 'type'>): string {
    return this.addNotification(title, message, { ...options, type: 'info' });
  }

  /**
   * Show success notification
   */
  success(title: string, message: string, options?: Omit<NotificationOptions, 'type'>): string {
    return this.addNotification(title, message, { ...options, type: 'success' });
  }

  /**
   * Show warning notification
   */
  warning(title: string, message: string, options?: Omit<NotificationOptions, 'type'>): string {
    return this.addNotification(title, message, { ...options, type: 'warning' });
  }

  /**
   * Show error notification
   */
  error(title: string, message: string, options?: Omit<NotificationOptions, 'type'>): string {
    return this.addNotification(title, message, { ...options, type: 'error' });
  }

  /**
   * Dismiss a notification by ID
   */
  dismiss(id: string): void {
    this.notifications.update((notifications) => notifications.filter((n) => n.id !== id));

    // Clear timer if exists
    const timer = this.timers.get(id);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(id);
    }
  }

  /**
   * Dismiss all notifications
   */
  dismissAll(): void {
    this.notifications.set([]);

    // Clear all timers
    for (const timer of this.timers.values()) {
      clearTimeout(timer);
    }
    this.timers.clear();
  }

  /**
   * Dismiss all notifications of a specific type
   */
  dismissType(type: Notification['type']): void {
    this.notifications.update((notifications) => {
      const remaining = notifications.filter((n) => n.type !== type);
      const dismissed = notifications.filter((n) => n.type === type);

      // Clear timers for dismissed notifications
      dismissed.forEach((n) => {
        const timer = this.timers.get(n.id);
        if (timer) {
          clearTimeout(timer);
          this.timers.delete(n.id);
        }
      });

      return remaining;
    });
  }

  /**
   * Update a notification
   */
  update(id: string, updates: Partial<Omit<Notification, 'id' | 'timestamp'>>): void {
    this.notifications.update((notifications) =>
      notifications.map((n) => (n.id === id ? { ...n, ...updates } : n))
    );
  }

  /**
   * Get notification count by type
   */
  getCount(type?: Notification['type']): number {
    let count = 0;
    this.notifications.subscribe((notifications) => {
      count = type ? notifications.filter((n) => n.type === type).length : notifications.length;
    })();
    return count;
  }

  /**
   * Check if there are any unread notifications
   */
  hasUnread(): boolean {
    return this.getCount() > 0;
  }

  /**
   * Show a notification with action buttons
   */
  confirm(
    title: string,
    message: string,
    onConfirm: () => void,
    onCancel?: () => void,
    options?: Omit<NotificationOptions, 'actions' | 'persistent'>
  ): string {
    const actions: NotificationAction[] = [
      {
        label: 'Confirm',
        action: () => {
          onConfirm();
          // Don't auto-dismiss, let the action handler decide
        },
        style: 'primary',
      },
    ];

    if (onCancel) {
      actions.push({
        label: 'Cancel',
        action: () => {
          onCancel();
          // Don't auto-dismiss, let the action handler decide
        },
        style: 'secondary',
      });
    }

    return this.addNotification(title, message, {
      ...options,
      type: options?.type || 'warning',
      actions,
      persistent: true, // Don't auto-dismiss confirmation dialogs
    });
  }

  /**
   * Show a loading notification
   */
  loading(title: string, message: string): string {
    return this.addNotification(title, message, {
      type: 'info',
      persistent: true,
      dismissible: false,
      icon: '⏳',
    });
  }

  /**
   * Show system notification (browser notification API)
   */
  async showSystemNotification(
    title: string,
    message: string,
    options?: NotificationOptions
  ): Promise<void> {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
      console.warn('Browser does not support system notifications');
      return;
    }

    // Request permission if not granted
    if (Notification.permission === 'default') {
      await Notification.requestPermission();
    }

    // Show system notification if permission granted
    if (Notification.permission === 'granted') {
      const notification = new Notification(title, {
        body: message,
        icon: '/favicon.png',
        badge: '/favicon.png',
        tag: 'wakedock-notification',
      });

      // Auto-close after duration
      const duration = options?.duration || this.getDefaultDuration(options?.type || 'info');
      setTimeout(() => notification.close(), duration);
    }

    // Also show in-app notification
    this.addNotification(title, message, options);
  }
}

// Export singleton instance
export const notifications = new NotificationService();

// Convenience functions for quick access
export const {
  info: notifyInfo,
  success: notifySuccess,
  warning: notifyWarning,
  error: notifyError,
  dismiss: dismissNotification,
  dismissAll: dismissAllNotifications,
} = notifications;

// WebSocket integration helpers
export function handleWebSocketNotification(data: any): void {
  if (data.type && data.title && data.message) {
    notifications[data.type as Notification['type']](data.title, data.message, {
      persistent: data.persistent,
      duration: data.duration,
    });
  }
}

// API error notification helper
export function notifyApiError(error: any, context?: string): void {
  const title = context ? `${context} Failed` : 'Operation Failed';
  const message = error?.message || 'An unexpected error occurred';

  notifications.error(title, message, {
    persistent: true, // Keep error notifications until dismissed
  });
}

// Service operation notifications
export const serviceNotifications = {
  started: (serviceName: string) =>
    notifications.success('Service Started', `${serviceName} is now running`),

  stopped: (serviceName: string) =>
    notifications.info('Service Stopped', `${serviceName} has been stopped`),

  restarted: (serviceName: string) =>
    notifications.success('Service Restarted', `${serviceName} has been restarted`),

  deleted: (serviceName: string) =>
    notifications.warning('Service Deleted', `${serviceName} has been removed`),

  created: (serviceName: string) =>
    notifications.success('Service Created', `${serviceName} has been created successfully`),

  error: (serviceName: string, error: string) =>
    notifications.error('Service Error', `${serviceName}: ${error}`, { persistent: true }),
};
