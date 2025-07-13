/**
 * WebSocket Client
 * Real-time updates for WakeDock Dashboard
 */
import { writable, type Writable } from 'svelte/store';
import { config, debugLog } from './config/environment.js';
import { WS_ENDPOINTS, getWsUrl } from './config/api.js';
import type { Service } from './api.js';
import { WebSocketBatchManager, MessageCompressor, type WebSocketMessage as BatchMessage, type BatchedMessage } from './websocket-batch.js';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface ServiceUpdate {
  id: string;
  status: Service['status'];
  health_status?: Service['health_status'];
  stats?: {
    cpu_usage: number;
    memory_usage: number;
    network_io: { rx: number; tx: number };
  };
}

export interface SystemUpdate {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  uptime: number;
  services_count: {
    total: number;
    running: number;
    stopped: number;
    error: number;
  };
}

export interface LogEntry {
  id: string;
  service_id?: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: string;
}

export interface NotificationMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  persistent?: boolean;
}

// WebSocket connection states
export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  RECONNECTING = 'reconnecting',
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = config.wsMaxReconnectAttempts;
  private reconnectInterval = config.wsReconnectInterval;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private subscriptions = new Set<string>();
  private eventCallbacks = new Map<string, ((data: any) => void)[]>();
  private messageQueue: WebSocketMessage[] = [];
  private lastSequenceNumber = 0;
  private heartbeatInterval = 30000; // 30 seconds
  private connectionStartTime = 0;
  private isReconnecting = false;

  // Batching system
  private batchManager: WebSocketBatchManager;
  private batchingEnabled = true;

  // Stores
  public connectionState: Writable<ConnectionState> = writable(ConnectionState.DISCONNECTED);
  public serviceUpdates: Writable<ServiceUpdate[]> = writable([]);
  public systemUpdates: Writable<SystemUpdate | null> = writable(null);
  public logs: Writable<LogEntry[]> = writable([]);
  public notifications: Writable<NotificationMessage[]> = writable([]);
  public lastError: Writable<string | null> = writable(null);
  public connectionStats: Writable<{
    reconnectAttempts: number;
    uptime: number;
    lastPing: number;
    messagesReceived: number;
    messagesSent: number;
  }> = writable({
    reconnectAttempts: 0,
    uptime: 0,
    lastPing: 0,
    messagesReceived: 0,
    messagesSent: 0,
  });

  constructor() {
    // Initialize batch manager
    this.batchManager = new WebSocketBatchManager();

    // Only initialize in browser environment if not on login page
    if (typeof window !== 'undefined' && !this.isOnLoginPage()) {
      this.connect();
    }
  }

  /**
   * Check if we're on the login page
   */
  private isOnLoginPage(): boolean {
    if (typeof window === 'undefined') return false;
    return window.location.pathname.includes('/login') || window.location.pathname.includes('/auth');
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    // Prevent multiple concurrent connection attempts
    if (this.isReconnecting) {
      return;
    }

    try {
      this.isReconnecting = true;
      this.connectionState.set(
        this.reconnectAttempts > 0 ? ConnectionState.RECONNECTING : ConnectionState.CONNECTING
      );

      debugLog('Connecting to WebSocket:', config.wsUrl);
      this.connectionStartTime = Date.now();

      this.ws = new WebSocket(config.wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.connectionState.set(ConnectionState.ERROR);
      this.lastError.set(error instanceof Error ? error.message : 'Connection failed');
      this.scheduleReconnect();
    } finally {
      this.isReconnecting = false;
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.connectionState.set(ConnectionState.ERROR);
      this.lastError.set('Max reconnection attempts reached');
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    // Exponential backoff with jitter
    const delay = Math.min(
      this.reconnectInterval * Math.pow(2, this.reconnectAttempts) + Math.random() * 1000,
      30000 // Max 30 seconds
    );

    this.reconnectAttempts++;
    this.updateConnectionStats();

    debugLog(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Update connection statistics
   */
  private updateConnectionStats(): void {
    this.connectionStats.update((stats: any) => ({
      ...stats,
      reconnectAttempts: this.reconnectAttempts,
      uptime: this.connectionStartTime ? Date.now() - this.connectionStartTime : 0,
    }));
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.connectionState.set(ConnectionState.DISCONNECTED);
    this.reconnectAttempts = 0;
  }

  /**
   * Subscribe to specific event types with optional callback
   */
  subscribe(eventType: string, callback?: (data: any) => void): void {
    this.subscriptions.add(eventType);

    // Store callback if provided
    if (callback) {
      if (!this.eventCallbacks.has(eventType)) {
        this.eventCallbacks.set(eventType, []);
      }
      this.eventCallbacks.get(eventType)!.push(callback);
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({
        type: 'subscribe',
        data: { event_type: eventType },
      });
    }
  }

  /**
   * Unsubscribe from specific event types
   */
  unsubscribe(eventType: string): void {
    this.subscriptions.delete(eventType);
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({
        type: 'unsubscribe',
        data: { event_type: eventType },
      });
    }
  }

  /**
   * Send message to WebSocket server
   */
  private send(message: any, priority: 'low' | 'normal' | 'high' | 'critical' = 'normal'): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const batchMessage: BatchMessage = {
        type: message.type,
        data: message.data || message,
        timestamp: message.timestamp || new Date().toISOString(),
        priority
      };

      if (this.batchingEnabled && priority !== 'critical') {
        // Use batching for non-critical messages
        this.batchManager.queueMessage(batchMessage);
      } else {
        // Send immediately for critical messages or when batching disabled
        this.batchManager.sendImmediate(batchMessage);
      }
    } else {
      debugLog('WebSocket not connected, cannot send message:', message);
    }
  }

  /**
   * Send message with high priority (bypasses normal batching)
   */
  sendHighPriority(message: any): void {
    this.send(message, 'critical');
  }

  /**
   * Enable or disable message batching
   */
  setBatchingEnabled(enabled: boolean): void {
    this.batchingEnabled = enabled;
    if (!enabled) {
      // Flush any queued messages immediately
      this.batchManager.flushAll();
    }
  }

  /**
   * Get batching statistics
   */
  getBatchingStats() {
    return this.batchManager.getStats();
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      debugLog('WebSocket connected');
      this.connectionState.set(ConnectionState.CONNECTED);
      this.reconnectAttempts = 0;
      this.lastError.set(null);

      // Setup batch manager with the connected WebSocket
      if (this.ws) {
        this.batchManager.setWebSocket(this.ws);
      }

      // Resubscribe to events
      this.subscriptions.forEach((eventType) => {
        this.send({
          type: 'subscribe',
          data: { event_type: eventType },
        });
      });

      // Start ping/pong for connection health
      this.startPing();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = event.data;
        let message: WebSocketMessage | BatchedMessage;

        // Check if message is compressed or batched
        if (typeof data === 'string' && data.startsWith('batch:')) {
          // Handle batched messages
          const batchData = data.substring(6); // Remove 'batch:' prefix
          message = MessageCompressor.decompress(batchData, true);

          if (message.type === 'batch') {
            // Process each message in the batch
            (message as BatchedMessage).messages.forEach(msg => {
              this.handleMessage({
                ...msg,
                timestamp: msg.timestamp || new Date().toISOString()
              });
            });
            return;
          }
        } else {
          message = JSON.parse(data);
        }

        this.handleMessage(message as WebSocketMessage);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      debugLog('WebSocket disconnected:', event.code, event.reason);
      this.connectionState.set(ConnectionState.DISCONNECTED);

      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }

      // Attempt reconnection if not a normal closure
      if (event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connectionState.set(ConnectionState.ERROR);
      this.lastError.set('Connection error occurred');
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    debugLog('WebSocket message received:', message);

    // Call registered callbacks for this message type
    const callbacks = this.eventCallbacks.get(message.type);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(message.data);
        } catch (error) {
          console.error('Error in WebSocket callback:', error);
        }
      });
    }

    switch (message.type) {
      case 'service_update':
      case 'service_status':
        this.handleServiceUpdate(message.data);
        break;

      case 'system_update':
      case 'system_metrics':
        this.handleSystemUpdate(message.data);
        break;

      case 'log_entry':
      case 'service_logs':
        this.handleLogEntry(message.data);
        break;

      case 'notification':
        this.handleNotification(message.data);
        break;

      case 'security_event':
        // Handle security events - can be extended as needed
        break;

      case 'session_update':
        // Handle session updates - can be extended as needed
        break;

      case 'request_metrics':
        // Handle request metrics - can be extended as needed
        break;

      case 'pong':
        debugLog('Received pong from server');
        break;

      default:
        debugLog('Unknown message type:', message.type);
    }
  }

  /**
   * Handle service update messages
   */
  private handleServiceUpdate(data: ServiceUpdate): void {
    this.serviceUpdates.update((updates: ServiceUpdate[]) => {
      const existingIndex = updates.findIndex((u: ServiceUpdate) => u.id === data.id);
      if (existingIndex >= 0) {
        updates[existingIndex] = { ...updates[existingIndex], ...data };
      } else {
        updates.push(data);
      }
      return updates;
    });
  }

  /**
   * Handle system update messages
   */
  private handleSystemUpdate(data: SystemUpdate): void {
    this.systemUpdates.set(data);
  }

  /**
   * Handle log entry messages
   */
  private handleLogEntry(data: LogEntry): void {
    this.logs.update((logs: LogEntry[]) => {
      // Keep only the last 1000 log entries
      const newLogs = [data, ...logs].slice(0, 1000);
      return newLogs;
    });
  }

  /**
   * Handle notification messages
   */
  private handleNotification(data: NotificationMessage): void {
    this.notifications.update((notifications: NotificationMessage[]) => [data, ...notifications]);
  }

  /**
   * Start ping/pong mechanism
   */
  private startPing(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', data: {} });
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Clear old data
   */
  clearLogs(): void {
    this.logs.set([]);
  }

  clearNotifications(): void {
    this.notifications.set([]);
  }

  /**
   * Start WebSocket connection manually
   */
  public startConnection(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }
    this.connect();
  }

  /**
   * Stop WebSocket connection manually
   */
  public stopConnection(): void {
    this.disconnect();
  }
}

// Create and export the WebSocket client
export const websocketClient = new WebSocketClient();

// Export for backward compatibility
export default websocketClient;

// Export with different names for compatibility
export const websocket = websocketClient;

// Export individual stores for easier access
export const { connectionState, serviceUpdates, systemUpdates, logs, notifications, lastError } =
  websocketClient;

// Convenience functions
export function subscribeToServices(): void {
  websocketClient.subscribe('service_updates');
}

export function subscribeToSystem(): void {
  websocketClient.subscribe('system_updates');
}

export function subscribeToLogs(): void {
  websocketClient.subscribe('log_entries');
}

export function subscribeToNotifications(): void {
  websocketClient.subscribe('notifications');
}

export function connectWebSocket(): void {
  websocketClient.connect();
}

export function disconnectWebSocket(): void {
  websocketClient.disconnect();
}
