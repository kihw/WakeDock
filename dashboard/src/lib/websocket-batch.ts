/**
 * WebSocket Message Batching System
 * Optimizes real-time communication by batching messages
 */

export interface WebSocketMessage {
    type: string;
    data: any;
    timestamp?: string;
    priority?: 'low' | 'normal' | 'high' | 'critical';
}

export interface BatchedMessage {
    type: 'batch';
    messages: WebSocketMessage[];
    count: number;
    timestamp: string;
    compressed?: boolean;
}

export class MessageCompressor {
    private static readonly COMPRESSION_THRESHOLD = 1024; // 1KB

    static shouldCompress(data: string): boolean {
        return data.length > this.COMPRESSION_THRESHOLD;
    }

    static compress(data: any): string {
        const jsonStr = JSON.stringify(data);

        if (this.shouldCompress(jsonStr)) {
            // Simple compression for demo - in production use pako or similar
            return this.simpleCompress(jsonStr);
        }

        return jsonStr;
    }

    static decompress(data: string, isCompressed: boolean): any {
        if (isCompressed) {
            const decompressed = this.simpleDecompress(data);
            return JSON.parse(decompressed);
        }

        return JSON.parse(data);
    }

    private static simpleCompress(str: string): string {
        // Basic compression - replace with proper compression library
        return btoa(str);
    }

    private static simpleDecompress(str: string): string {
        return atob(str);
    }
}

export class WebSocketBatchManager {
    private batchQueue: WebSocketMessage[] = [];
    private highPriorityQueue: WebSocketMessage[] = [];
    private batchTimer: number | null = null;
    private ws: WebSocket | null = null;

    // Configuration
    private readonly BATCH_SIZE = 10;
    private readonly BATCH_INTERVAL = 100; // 100ms
    private readonly HIGH_PRIORITY_INTERVAL = 50; // 50ms for critical messages
    private readonly MAX_BATCH_SIZE = 50;

    // Metrics
    private messagesSent = 0;
    private batchesSent = 0;
    private compressionSaved = 0;

    constructor(websocket: WebSocket | null = null) {
        this.ws = websocket;
    }

    setWebSocket(websocket: WebSocket): void {
        this.ws = websocket;
    }

    /**
     * Queue a message for batching
     */
    queueMessage(message: WebSocketMessage): void {
        // Add timestamp if not present
        if (!message.timestamp) {
            message.timestamp = new Date().toISOString();
        }

        // Handle high priority messages separately
        if (message.priority === 'critical' || message.priority === 'high') {
            this.highPriorityQueue.push(message);
            this.scheduleHighPriorityFlush();
            return;
        }

        // Regular batching
        this.batchQueue.push(message);

        // Flush immediately if batch is full
        if (this.batchQueue.length >= this.BATCH_SIZE) {
            this.flushBatch();
        } else if (!this.batchTimer) {
            this.scheduleBatchFlush();
        }

        // Safety valve - prevent memory buildup
        if (this.batchQueue.length >= this.MAX_BATCH_SIZE) {
            console.warn('WebSocket batch queue exceeded maximum size, flushing');
            this.flushBatch();
        }
    }

    /**
     * Send a message immediately (bypasses batching)
     */
    sendImmediate(message: WebSocketMessage): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not ready, queueing message');
            this.queueMessage(message);
            return;
        }

        const messageStr = MessageCompressor.compress(message);
        const isCompressed = MessageCompressor.shouldCompress(messageStr);

        if (isCompressed) {
            this.compressionSaved += messageStr.length - MessageCompressor.compress(message).length;
        }

        this.ws.send(messageStr);
        this.messagesSent++;
    }

    /**
     * Flush all queued messages immediately
     */
    flushAll(): void {
        this.flushHighPriorityBatch();
        this.flushBatch();
    }

    private scheduleBatchFlush(): void {
        this.batchTimer = window.setTimeout(() => {
            this.flushBatch();
        }, this.BATCH_INTERVAL);
    }

    private scheduleHighPriorityFlush(): void {
        // High priority messages get their own faster timer
        setTimeout(() => {
            this.flushHighPriorityBatch();
        }, this.HIGH_PRIORITY_INTERVAL);
    }

    private flushBatch(): void {
        if (this.batchQueue.length === 0) {
            return;
        }

        this.clearBatchTimer();

        const messages = this.batchQueue.splice(0);
        this.sendBatch(messages);
    }

    private flushHighPriorityBatch(): void {
        if (this.highPriorityQueue.length === 0) {
            return;
        }

        const messages = this.highPriorityQueue.splice(0);
        this.sendBatch(messages, true);
    }

    private sendBatch(messages: WebSocketMessage[], isHighPriority = false): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not ready, re-queueing batch');
            // Re-queue messages
            if (isHighPriority) {
                this.highPriorityQueue.unshift(...messages);
            } else {
                this.batchQueue.unshift(...messages);
            }
            return;
        }

        const batch: BatchedMessage = {
            type: 'batch',
            messages,
            count: messages.length,
            timestamp: new Date().toISOString()
        };

        const batchStr = MessageCompressor.compress(batch);
        const isCompressed = MessageCompressor.shouldCompress(batchStr);

        if (isCompressed) {
            batch.compressed = true;
            this.compressionSaved += JSON.stringify(batch).length - batchStr.length;
        }

        this.ws.send(isCompressed ? batchStr : JSON.stringify(batch));

        this.messagesSent += messages.length;
        this.batchesSent++;
    }

    private clearBatchTimer(): void {
        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
            this.batchTimer = null;
        }
    }

    /**
     * Get batching statistics
     */
    getStats(): {
        messagesSent: number;
        batchesSent: number;
        averageBatchSize: number;
        compressionSaved: number;
        queuedMessages: number;
    } {
        return {
            messagesSent: this.messagesSent,
            batchesSent: this.batchesSent,
            averageBatchSize: this.batchesSent > 0 ? this.messagesSent / this.batchesSent : 0,
            compressionSaved: this.compressionSaved,
            queuedMessages: this.batchQueue.length + this.highPriorityQueue.length
        };
    }

    /**
     * Reset statistics
     */
    resetStats(): void {
        this.messagesSent = 0;
        this.batchesSent = 0;
        this.compressionSaved = 0;
    }

    /**
     * Cleanup resources
     */
    destroy(): void {
        this.clearBatchTimer();
        this.batchQueue = [];
        this.highPriorityQueue = [];
        this.ws = null;
    }
}
