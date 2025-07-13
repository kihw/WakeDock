/**
 * WebSocket Batching Performance Tests
 * Test suite for message batching optimization
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { WebSocketBatchManager, MessageCompressor, type WebSocketMessage } from '../../src/lib/websocket-batch';

// Mock WebSocket
class MockWebSocket {
    readyState = WebSocket.OPEN;
    sentMessages: string[] = [];

    send(data: string) {
        this.sentMessages.push(data);
    }

    getSentMessages() {
        return this.sentMessages;
    }

    clearSentMessages() {
        this.sentMessages = [];
    }
}

describe('WebSocket Batching Performance', () => {
    let batchManager: WebSocketBatchManager;
    let mockWebSocket: MockWebSocket;

    beforeEach(() => {
        mockWebSocket = new MockWebSocket();
        batchManager = new WebSocketBatchManager(mockWebSocket as any);
        vi.useFakeTimers();
    });

    afterEach(() => {
        batchManager.destroy();
        vi.useRealTimers();
    });

    describe('Message Batching', () => {
        test('should batch messages within time window', async () => {
            const messages: WebSocketMessage[] = [
                { type: 'service_update', data: { id: '1', status: 'running' } },
                { type: 'service_update', data: { id: '2', status: 'stopped' } },
                { type: 'metric_update', data: { cpu: 50, memory: 60 } }
            ];

            // Queue messages
            messages.forEach(msg => batchManager.queueMessage(msg));

            // Should not send immediately
            expect(mockWebSocket.getSentMessages()).toHaveLength(0);

            // Fast-forward past batch interval
            vi.advanceTimersByTime(150); // 150ms > 100ms batch interval

            // Should have sent one batched message
            expect(mockWebSocket.getSentMessages()).toHaveLength(1);

            const sentMessage = JSON.parse(mockWebSocket.getSentMessages()[0]);
            expect(sentMessage.type).toBe('batch');
            expect(sentMessage.messages).toHaveLength(3);
            expect(sentMessage.count).toBe(3);
        });

        test('should flush immediately when batch size reached', () => {
            // Queue 10 messages (batch size limit)
            for (let i = 0; i < 10; i++) {
                batchManager.queueMessage({
                    type: 'test',
                    data: { index: i }
                });
            }

            // Should send immediately without waiting for timer
            expect(mockWebSocket.getSentMessages()).toHaveLength(1);

            const sentMessage = JSON.parse(mockWebSocket.getSentMessages()[0]);
            expect(sentMessage.messages).toHaveLength(10);
        });

        test('should handle high priority messages separately', async () => {
            // Queue normal priority message
            batchManager.queueMessage({
                type: 'normal',
                data: { test: 'data' },
                priority: 'normal'
            });

            // Queue high priority message
            batchManager.queueMessage({
                type: 'critical',
                data: { alert: 'urgent' },
                priority: 'critical'
            });

            // High priority should be sent faster
            vi.advanceTimersByTime(60); // 60ms > 50ms high priority interval

            expect(mockWebSocket.getSentMessages()).toHaveLength(1);

            // Normal priority should still be queued
            vi.advanceTimersByTime(50); // Total 110ms > 100ms normal interval

            expect(mockWebSocket.getSentMessages()).toHaveLength(2);
        });
    });

    describe('Message Compression', () => {
        test('should compress large messages', () => {
            const largeData = 'x'.repeat(2000); // 2KB string
            const message = { type: 'large_data', data: { content: largeData } };

            const compressed = MessageCompressor.compress(message);
            const isCompressed = MessageCompressor.shouldCompress(JSON.stringify(message));

            expect(isCompressed).toBe(true);
            expect(compressed.length).toBeLessThan(JSON.stringify(message).length);
        });

        test('should not compress small messages', () => {
            const smallData = { type: 'small', data: { value: 42 } };
            const result = MessageCompressor.compress(smallData);
            const isCompressed = MessageCompressor.shouldCompress(JSON.stringify(smallData));

            expect(isCompressed).toBe(false);
            expect(result).toBe(JSON.stringify(smallData));
        });

        test('should decompress correctly', () => {
            const originalData = { test: 'data', array: [1, 2, 3], nested: { value: 'test' } };
            const compressed = MessageCompressor.compress(originalData);
            const decompressed = MessageCompressor.decompress(compressed, true);

            expect(decompressed).toEqual(originalData);
        });
    });

    describe('Performance Metrics', () => {
        test('should track batching statistics', () => {
            // Send some messages
            for (let i = 0; i < 15; i++) {
                batchManager.queueMessage({
                    type: 'test',
                    data: { index: i }
                });
            }

            // Flush remaining messages
            batchManager.flushAll();

            const stats = batchManager.getStats();

            expect(stats.messagesSent).toBe(15);
            expect(stats.batchesSent).toBeGreaterThan(0);
            expect(stats.averageBatchSize).toBeGreaterThan(0);
        });

        test('should measure compression savings', () => {
            const largeMessage = {
                type: 'large_data',
                data: { content: 'x'.repeat(2000) }
            };

            batchManager.sendImmediate(largeMessage);

            const stats = batchManager.getStats();
            expect(stats.compressionSaved).toBeGreaterThan(0);
        });
    });

    describe('Error Handling', () => {
        test('should handle WebSocket disconnect gracefully', () => {
            mockWebSocket.readyState = WebSocket.CLOSED;

            batchManager.queueMessage({
                type: 'test',
                data: { value: 'test' }
            });

            // Should not throw error
            vi.advanceTimersByTime(150);
            expect(mockWebSocket.getSentMessages()).toHaveLength(0);
        });

        test('should prevent memory buildup with max batch size', () => {
            // Queue more than max batch size
            for (let i = 0; i < 60; i++) { // 60 > 50 max batch size
                batchManager.queueMessage({
                    type: 'test',
                    data: { index: i }
                });
            }

            // Should have sent messages automatically to prevent buildup
            expect(mockWebSocket.getSentMessages().length).toBeGreaterThan(0);
        });
    });

    describe('Performance Benchmarks', () => {
        test('should batch efficiently under load', () => {
            const startTime = performance.now();

            // Simulate high message load
            for (let i = 0; i < 1000; i++) {
                batchManager.queueMessage({
                    type: 'load_test',
                    data: {
                        index: i,
                        timestamp: Date.now(),
                        data: Math.random().toString(36)
                    }
                });
            }

            const queueTime = performance.now() - startTime;
            expect(queueTime).toBeLessThan(100); // Should queue 1000 messages in < 100ms

            // Flush all messages
            const flushStartTime = performance.now();
            batchManager.flushAll();
            const flushTime = performance.now() - flushStartTime;

            expect(flushTime).toBeLessThan(50); // Should flush quickly

            const stats = batchManager.getStats();
            expect(stats.messagesSent).toBe(1000);
            expect(stats.averageBatchSize).toBeGreaterThan(5); // Should achieve good batching
        });

        test('should maintain low latency for critical messages', () => {
            const startTime = performance.now();

            batchManager.sendImmediate({
                type: 'critical',
                data: { alert: 'immediate' },
                priority: 'critical'
            });

            const latency = performance.now() - startTime;
            expect(latency).toBeLessThan(10); // Should send critical messages < 10ms
            expect(mockWebSocket.getSentMessages()).toHaveLength(1);
        });
    });
});

describe('Message Compression Performance', () => {
    test('should compress efficiently', () => {
        const testSizes = [500, 1000, 2000, 5000, 10000]; // bytes

        testSizes.forEach(size => {
            const testData = {
                type: 'performance_test',
                data: {
                    content: 'x'.repeat(size),
                    metadata: { size, timestamp: Date.now() }
                }
            };

            const startTime = performance.now();
            const compressed = MessageCompressor.compress(testData);
            const compressionTime = performance.now() - startTime;

            // Compression should be fast
            expect(compressionTime).toBeLessThan(20); // < 20ms

            // Should achieve some compression for larger messages
            if (size > 1000) {
                expect(compressed.length).toBeLessThan(JSON.stringify(testData).length);
            }
        });
    });

    test('should decompress efficiently', () => {
        const largeData = {
            type: 'large_test',
            data: {
                content: 'test data '.repeat(1000), // ~10KB
                array: Array.from({ length: 100 }, (_, i) => ({ id: i, value: Math.random() }))
            }
        };

        const compressed = MessageCompressor.compress(largeData);

        const startTime = performance.now();
        const decompressed = MessageCompressor.decompress(compressed, true);
        const decompressionTime = performance.now() - startTime;

        expect(decompressionTime).toBeLessThan(10); // < 10ms
        expect(decompressed).toEqual(largeData);
    });
});
