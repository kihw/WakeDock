/**
 * WebSocket Client Tests
 * Tests for WebSocket connection, reconnection, and message handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketClient } from '../../src/lib/websocket';
import type { WebSocketMessage, ServiceUpdate, SystemUpdate } from '../../src/lib/websocket';

// Mock WebSocket
class MockWebSocket {
    public static CONNECTING = 0;
    public static OPEN = 1;
    public static CLOSING = 2;
    public static CLOSED = 3;

    public readyState = MockWebSocket.CONNECTING;
    public onopen: ((event: Event) => void) | null = null;
    public onclose: ((event: CloseEvent) => void) | null = null;
    public onmessage: ((event: MessageEvent) => void) | null = null;
    public onerror: ((event: Event) => void) | null = null;

    constructor(public url: string) {
        // Simulate connection delay
        setTimeout(() => {
            this.readyState = MockWebSocket.OPEN;
            if (this.onopen) {
                this.onopen(new Event('open'));
            }
        }, 10);
    }

    send(data: string) {
        if (this.readyState !== MockWebSocket.OPEN) {
            throw new Error('WebSocket is not open');
        }
        // Simulate sending
    }

    close(code?: number, reason?: string) {
        this.readyState = MockWebSocket.CLOSED;
        if (this.onclose) {
            this.onclose(new CloseEvent('close', { code, reason }));
        }
    }

    // Helper method to simulate receiving messages
    simulateMessage(data: any) {
        if (this.onmessage) {
            this.onmessage(new MessageEvent('message', {
                data: typeof data === 'string' ? data : JSON.stringify(data)
            }));
        }
    }

    // Helper method to simulate errors
    simulateError() {
        if (this.onerror) {
            this.onerror(new Event('error'));
        }
    }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket as any;

describe('WebSocketClient', () => {
    let wsClient: WebSocketClient;
    let mockWs: MockWebSocket;

    beforeEach(() => {
        vi.clearAllMocks();
        wsClient = new WebSocketClient();

        // Get reference to the mock WebSocket instance
        vi.spyOn(global, 'WebSocket').mockImplementation((url: string) => {
            mockWs = new MockWebSocket(url);
            return mockWs as any;
        });
    });

    afterEach(() => {
        wsClient.disconnect();
        vi.restoreAllMocks();
    });

    describe('Connection Management', () => {
        it('should connect to WebSocket server', async () => {
            await wsClient.connect();

            expect(global.WebSocket).toHaveBeenCalledWith(
                expect.stringContaining('ws://') || expect.stringContaining('wss://')
            );
        });

        it('should handle connection state changes', async () => {
            const stateChanges: string[] = [];

            wsClient.connectionState.subscribe(state => {
                stateChanges.push(state);
            });

            await wsClient.connect();

            // Wait for connection to establish
            await new Promise(resolve => setTimeout(resolve, 20));

            expect(stateChanges).toContain('connecting');
            expect(stateChanges).toContain('connected');
        });

        it('should disconnect properly', async () => {
            await wsClient.connect();
            await new Promise(resolve => setTimeout(resolve, 20));

            wsClient.disconnect();

            expect(mockWs.readyState).toBe(MockWebSocket.CLOSED);
        });
    });

    describe('Reconnection Logic', () => {
        it('should attempt reconnection on connection loss', async () => {
            await wsClient.connect();
            await new Promise(resolve => setTimeout(resolve, 20));

            // Simulate connection loss
            mockWs.simulateError();
            mockWs.close(1006, 'Connection lost');

            // Wait for reconnection attempt
            await new Promise(resolve => setTimeout(resolve, 100));

            // Should attempt to reconnect
            expect(global.WebSocket).toHaveBeenCalledTimes(2);
        });

        it('should implement exponential backoff for reconnections', async () => {
            const setTimeoutSpy = vi.spyOn(global, 'setTimeout');

            await wsClient.connect();

            // Simulate multiple connection failures
            for (let i = 0; i < 3; i++) {
                mockWs.simulateError();
                mockWs.close(1006, 'Connection lost');
                await new Promise(resolve => setTimeout(resolve, 10));
            }

            // Check that timeout delays increase (exponential backoff)
            const delays = setTimeoutSpy.mock.calls
                .filter(call => typeof call[1] === 'number')
                .map(call => call[1] as number)
                .sort((a, b) => a - b);

            expect(delays.length).toBeGreaterThan(1);
            // Later delays should be longer
            expect(delays[delays.length - 1]).toBeGreaterThan(delays[0]);
        });

        it('should stop reconnecting after max attempts', async () => {
            await wsClient.connect();

            // Simulate many connection failures
            for (let i = 0; i < 10; i++) {
                mockWs.simulateError();
                mockWs.close(1006, 'Connection lost');
                await new Promise(resolve => setTimeout(resolve, 10));
            }

            // Should not exceed max reconnection attempts
            expect(global.WebSocket).toHaveBeenCalledTimes(4); // Initial + 3 max retries
        });
    });

    describe('Message Handling', () => {
        beforeEach(async () => {
            await wsClient.connect();
            await new Promise(resolve => setTimeout(resolve, 20));
        });

        it('should handle service update messages', async () => {
            const serviceUpdates: ServiceUpdate[] = [];

            wsClient.serviceUpdates.subscribe(updates => {
                serviceUpdates.push(...updates);
            });

            const updateMessage: WebSocketMessage = {
                type: 'service_update',
                data: {
                    id: 'service-1',
                    status: 'running',
                    health_status: 'healthy'
                },
                timestamp: new Date().toISOString()
            };

            mockWs.simulateMessage(updateMessage);

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(serviceUpdates).toHaveLength(1);
            expect(serviceUpdates[0]).toMatchObject({
                id: 'service-1',
                status: 'running',
                health_status: 'healthy'
            });
        });

        it('should handle system update messages', async () => {
            let systemUpdate: SystemUpdate | null = null;

            wsClient.systemUpdates.subscribe(update => {
                systemUpdate = update;
            });

            const updateMessage: WebSocketMessage = {
                type: 'system_update',
                data: {
                    cpu_usage: 45.2,
                    memory_usage: 68.5,
                    disk_usage: 32.1,
                    uptime: 86400,
                    services_count: {
                        total: 5,
                        running: 4,
                        stopped: 1,
                        error: 0
                    }
                },
                timestamp: new Date().toISOString()
            };

            mockWs.simulateMessage(updateMessage);

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(systemUpdate).toMatchObject({
                cpu_usage: 45.2,
                memory_usage: 68.5,
                disk_usage: 32.1,
                uptime: 86400
            });
        });

        it('should handle log entry messages', async () => {
            const logs: any[] = [];

            wsClient.logs.subscribe(logEntries => {
                logs.push(...logEntries);
            });

            const logMessage: WebSocketMessage = {
                type: 'log_entry',
                data: {
                    id: 'log-1',
                    service_id: 'service-1',
                    level: 'info',
                    message: 'Service started successfully',
                    timestamp: new Date().toISOString()
                },
                timestamp: new Date().toISOString()
            };

            mockWs.simulateMessage(logMessage);

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(logs).toHaveLength(1);
            expect(logs[0]).toMatchObject({
                id: 'log-1',
                service_id: 'service-1',
                level: 'info',
                message: 'Service started successfully'
            });
        });

        it('should limit log entries to prevent memory issues', async () => {
            const logs: any[] = [];

            wsClient.logs.subscribe(logEntries => {
                logs.length = 0; // Clear previous
                logs.push(...logEntries);
            });

            // Send 1500 log messages (more than the 1000 limit)
            for (let i = 0; i < 1500; i++) {
                const logMessage: WebSocketMessage = {
                    type: 'log_entry',
                    data: {
                        id: `log-${i}`,
                        service_id: 'service-1',
                        level: 'info',
                        message: `Log message ${i}`,
                        timestamp: new Date().toISOString()
                    },
                    timestamp: new Date().toISOString()
                };

                mockWs.simulateMessage(logMessage);
            }

            await new Promise(resolve => setTimeout(resolve, 50));

            // Should be limited to 1000 entries
            expect(logs).toHaveLength(1000);
            // Should contain the most recent entries
            expect(logs[0].id).toBe('log-1499');
        });
    });

    describe('Subscription Management', () => {
        beforeEach(async () => {
            await wsClient.connect();
            await new Promise(resolve => setTimeout(resolve, 20));
        });

        it('should send subscription messages', () => {
            const sendSpy = vi.spyOn(mockWs, 'send');

            wsClient.subscribe('service_updates');

            expect(sendSpy).toHaveBeenCalledWith(
                JSON.stringify({
                    type: 'subscribe',
                    data: { event_type: 'service_updates' }
                })
            );
        });

        it('should send unsubscription messages', () => {
            const sendSpy = vi.spyOn(mockWs, 'send');

            wsClient.unsubscribe('service_updates');

            expect(sendSpy).toHaveBeenCalledWith(
                JSON.stringify({
                    type: 'unsubscribe',
                    data: { event_type: 'service_updates' }
                })
            );
        });

        it('should resubscribe after reconnection', async () => {
            const sendSpy = vi.spyOn(mockWs, 'send');

            // Subscribe to events
            wsClient.subscribe('service_updates');
            wsClient.subscribe('system_updates');

            sendSpy.mockClear();

            // Simulate connection loss and reconnection
            mockWs.close(1006, 'Connection lost');
            await new Promise(resolve => setTimeout(resolve, 100));

            // Should resubscribe to all previous subscriptions
            expect(sendSpy).toHaveBeenCalledWith(
                expect.stringContaining('service_updates')
            );
            expect(sendSpy).toHaveBeenCalledWith(
                expect.stringContaining('system_updates')
            );
        });
    });

    describe('Error Handling', () => {
        it('should handle malformed JSON messages gracefully', async () => {
            await wsClient.connect();
            await new Promise(resolve => setTimeout(resolve, 20));

            const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

            // Send invalid JSON
            mockWs.simulateMessage('invalid json {');

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(errorSpy).toHaveBeenCalled();
            errorSpy.mockRestore();
        });

        it('should handle unknown message types', async () => {
            await wsClient.connect();
            await new Promise(resolve => setTimeout(resolve, 20));

            const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => { });

            const unknownMessage = {
                type: 'unknown_type',
                data: { some: 'data' },
                timestamp: new Date().toISOString()
            };

            mockWs.simulateMessage(unknownMessage);

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(warnSpy).toHaveBeenCalledWith(
                expect.stringContaining('Unknown message type')
            );
            warnSpy.mockRestore();
        });
    });

    describe('Connection Statistics', () => {
        it('should track connection statistics', async () => {
            let stats: any = null;

            wsClient.connectionStats.subscribe(s => {
                stats = s;
            });

            await wsClient.connect();
            await new Promise(resolve => setTimeout(resolve, 20));

            expect(stats).toMatchObject({
                reconnectAttempts: 0,
                uptime: expect.any(Number),
                lastPing: expect.any(Number),
                messagesReceived: expect.any(Number),
                messagesSent: expect.any(Number)
            });
        });
    });
});

// Export mocks for other tests
export { MockWebSocket };
