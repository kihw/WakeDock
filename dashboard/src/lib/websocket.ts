/**
 * WebSocket Client
 * Real-time updates for WakeDock Dashboard
 */
import { writable, type Writable } from 'svelte/store';
import { config, debugLog } from './config/environment.js';
import { WS_ENDPOINTS, getWsUrl } from './config/api.js';
import type { Service } from './api.js';

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
    private messageQueue: WebSocketMessage[] = [];
    private lastSequenceNumber = 0;
    private heartbeatInterval = 30000; // 30 seconds
    private connectionStartTime = 0;
    private isReconnecting = false;

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
        messagesSent: 0
    });

    constructor() {
        // Only initialize in browser environment
        if (typeof window !== 'undefined') {
            this.connect();
        }
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
            uptime: this.connectionStartTime ? Date.now() - this.connectionStartTime : 0
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
     * Subscribe to specific event types
     */
    subscribe(eventType: string): void {
        this.subscriptions.add(eventType);
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.send({
                type: 'subscribe',
                data: { event_type: eventType }
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
                data: { event_type: eventType }
            });
        }
    }

    /**
     * Send message to WebSocket server
     */
    private send(message: any): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            debugLog('WebSocket not connected, cannot send message:', message);
        }
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

            // Resubscribe to events
            this.subscriptions.forEach(eventType => {
                this.send({
                    type: 'subscribe',
                    data: { event_type: eventType }
                });
            });

            // Start ping/pong for connection health
            this.startPing();
        };

        this.ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                this.handleMessage(message);
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

        switch (message.type) {
            case 'service_update':
                this.handleServiceUpdate(message.data);
                break;

            case 'system_update':
                this.handleSystemUpdate(message.data);
                break;

            case 'log_entry':
                this.handleLogEntry(message.data);
                break;

            case 'notification':
                this.handleNotification(message.data);
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
}

// Export singleton instance
export const wsClient = new WebSocketClient();

// Export individual stores for easier access
export const {
    connectionState,
    serviceUpdates,
    systemUpdates,
    logs,
    notifications,
    lastError
} = wsClient;

// Convenience functions
export function subscribeToServices(): void {
    wsClient.subscribe('service_updates');
}

export function subscribeToSystem(): void {
    wsClient.subscribe('system_updates');
}

export function subscribeToLogs(): void {
    wsClient.subscribe('log_entries');
}

export function subscribeToNotifications(): void {
    wsClient.subscribe('notifications');
}

export function connectWebSocket(): void {
    wsClient.connect();
}

export function disconnectWebSocket(): void {
    wsClient.disconnect();
}
