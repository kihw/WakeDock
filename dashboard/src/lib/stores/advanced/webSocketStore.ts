/**
 * WebSocket Store for Real-time Updates
 * Handles WebSocket connections, reconnection, and real-time data streaming
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { auth } from '$lib/stores/auth';
import { dashboardStore } from './dashboardStore';
import type { Service, SystemMetrics, LogEntry, WebSocketMessage } from '$lib/types';

// WebSocket connection states
export const wsConnected = writable(false);
export const wsReconnecting = writable(false);
export const wsError = writable<string | null>(null);
export const wsLastMessage = writable<WebSocketMessage | null>(null);

// Real-time data streams
export const realtimeServices = writable<Service[]>([]);
export const realtimeMetrics = writable<SystemMetrics | null>(null);
export const realtimeLogs = writable<LogEntry[]>([]);

// Connection statistics
export const wsStats = writable({
    connected: false,
    reconnectAttempts: 0,
    lastConnected: null as Date | null,
    messagesReceived: 0,
    messagesSent: 0
});

class WebSocketStore {
    private ws: WebSocket | null = null;
    private reconnectInterval: number | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000; // Start with 1 second
    private heartbeatInterval: number | null = null;
    private messageQueue: string[] = [];
    private subscribers = new Set<(message: WebSocketMessage) => void>();

    constructor() {
        if (browser) {
            this.connect();
        }
    }

    connect(): void {
        if (!browser) return;

        try {
            // Get WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = this.onOpen.bind(this);
            this.ws.onmessage = this.onMessage.bind(this);
            this.ws.onclose = this.onClose.bind(this);
            this.ws.onerror = this.onError.bind(this);

            wsReconnecting.set(false);

        } catch (error) {
            console.error('WebSocket connection failed:', error);
            wsError.set(error instanceof Error ? error.message : 'Connection failed');
            this.scheduleReconnect();
        }
    }

    private onOpen(event: Event): void {
        console.log('WebSocket connected');

        wsConnected.set(true);
        wsReconnecting.set(false);
        wsError.set(null);
        this.reconnectAttempts = 0;

        // Update statistics
        wsStats.update(stats => ({
            ...stats,
            connected: true,
            reconnectAttempts: 0,
            lastConnected: new Date()
        }));

        // Send authentication if available
        const authData = get(auth);
        if (authData.token) {
            this.send({
                type: 'auth',
                token: authData.token
            });
        }

        // Send queued messages
        this.sendQueuedMessages();

        // Start heartbeat
        this.startHeartbeat();

        // Subscribe to real-time updates
        this.subscribeToUpdates();
    }

    private onMessage(event: MessageEvent): void {
        try {
            const message: WebSocketMessage = JSON.parse(event.data);

            // Update statistics
            wsStats.update(stats => ({
                ...stats,
                messagesReceived: stats.messagesReceived + 1
            }));

            wsLastMessage.set(message);

            // Handle different message types
            this.handleMessage(message);

            // Notify subscribers
            this.subscribers.forEach(callback => {
                try {
                    callback(message);
                } catch (error) {
                    console.error('Error in WebSocket subscriber:', error);
                }
            });

        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            wsError.set('Invalid message format');
        }
    }

    private handleMessage(message: WebSocketMessage): void {
        switch (message.type) {
            case 'service_update':
                if (message.data) {
                    dashboardStore.updateService(message.data as Service);
                }
                break;

            case 'service_removed':
                if (message.data?.id) {
                    dashboardStore.removeService(message.data.id);
                }
                break;

            case 'metrics_update':
                if (message.data) {
                    const metrics = message.data as SystemMetrics;
                    dashboardStore.updateMetrics(metrics);
                    realtimeMetrics.set(metrics);
                }
                break;

            case 'log_entry':
                if (message.data) {
                    realtimeLogs.update(logs => {
                        const newLogs = [...logs, message.data as LogEntry];
                        // Keep only last 100 log entries
                        return newLogs.slice(-100);
                    });
                }
                break;

            case 'pong':
                // Heartbeat response
                break;

            case 'error':
                wsError.set(message.data?.message || 'Unknown error');
                break;

            case 'notification':
                // Handle notifications
                console.log('Notification:', message.data);
                break;

            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    private onClose(event: CloseEvent): void {
        console.log('WebSocket disconnected:', event.code, event.reason);

        wsConnected.set(false);

        // Update statistics
        wsStats.update(stats => ({
            ...stats,
            connected: false
        }));

        this.cleanup();

        // Try to reconnect unless it was a clean close
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }

    private onError(event: Event): void {
        console.error('WebSocket error:', event);
        wsError.set('Connection error');
    }

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            wsError.set('Connection failed - max attempts reached');
            return;
        }

        this.reconnectAttempts++;
        wsReconnecting.set(true);

        // Update statistics
        wsStats.update(stats => ({
            ...stats,
            reconnectAttempts: this.reconnectAttempts
        }));

        // Exponential backoff
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

        console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);

        this.reconnectInterval = window.setTimeout(() => {
            this.connect();
        }, delay);
    }

    private cleanup(): void {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }

        if (this.reconnectInterval) {
            clearTimeout(this.reconnectInterval);
            this.reconnectInterval = null;
        }
    }

    private startHeartbeat(): void {
        this.heartbeatInterval = window.setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Send ping every 30 seconds
    }

    private subscribeToUpdates(): void {
        // Subscribe to services updates
        this.send({ type: 'subscribe', channel: 'services' });

        // Subscribe to metrics updates
        this.send({ type: 'subscribe', channel: 'metrics' });

        // Subscribe to system logs
        this.send({ type: 'subscribe', channel: 'logs' });
    }

    private sendQueuedMessages(): void {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (message && this.ws?.readyState === WebSocket.OPEN) {
                this.ws.send(message);
            }
        }
    }

    // Public methods
    send(message: any): void {
        const messageStr = JSON.stringify(message);

        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(messageStr);

            // Update statistics
            wsStats.update(stats => ({
                ...stats,
                messagesSent: stats.messagesSent + 1
            }));
        } else {
            // Queue message for later
            this.messageQueue.push(messageStr);
        }
    }

    disconnect(): void {
        this.cleanup();

        if (this.ws) {
            this.ws.close(1000, 'Normal closure');
            this.ws = null;
        }

        wsConnected.set(false);
        wsReconnecting.set(false);
    }

    subscribe(callback: (message: WebSocketMessage) => void): () => void {
        this.subscribers.add(callback);

        return () => {
            this.subscribers.delete(callback);
        };
    }

    // Get connection status
    getConnectionStatus(): 'connected' | 'connecting' | 'disconnected' | 'reconnecting' {
        if (get(wsConnected)) return 'connected';
        if (get(wsReconnecting)) return 'reconnecting';
        if (this.ws?.readyState === WebSocket.CONNECTING) return 'connecting';
        return 'disconnected';
    }

    // Force reconnect
    forceReconnect(): void {
        this.disconnect();
        this.reconnectAttempts = 0;
        this.connect();
    }
}

// Create and export the WebSocket store instance
export const webSocketStore = new WebSocketStore();

// Derived store for connection status
export const connectionStatus = derived(
    [wsConnected, wsReconnecting],
    ([$connected, $reconnecting]) => {
        if ($connected) return 'connected';
        if ($reconnecting) return 'reconnecting';
        return 'disconnected';
    }
);

// Export cleanup function for app teardown
export const cleanupWebSocket = () => {
    webSocketStore.disconnect();
};
