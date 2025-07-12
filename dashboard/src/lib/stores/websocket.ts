/**
 * WebSocket Store - Manages WebSocket connections and state
 */
import { writable, derived } from 'svelte/store';

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastMessage: any;
  connectionAttempts: number;
}

// WebSocket state store
function createWebSocketStore() {
  const { subscribe, set, update } = writable<WebSocketState>({
    connected: false,
    connecting: false,
    error: null,
    lastMessage: null,
    connectionAttempts: 0
  });

  let websocketClient: any = null;

  // Initialize WebSocket client
  const initializeWebSocket = async () => {
    if (typeof window !== 'undefined') {
      try {
        const module = await import('../websocket.js');
        websocketClient = module.websocketClient;
        
        // Subscribe to WebSocket events
        websocketClient.subscribe('connect', () => {
          update(state => ({ ...state, connected: true, connecting: false, error: null }));
        });

        websocketClient.subscribe('disconnect', () => {
          update(state => ({ ...state, connected: false, connecting: false }));
        });

        websocketClient.subscribe('error', (error: any) => {
          update(state => ({ ...state, error: error.message, connecting: false }));
        });

        websocketClient.subscribe('message', (message: any) => {
          update(state => ({ ...state, lastMessage: message }));
        });

      } catch (error) {
        console.warn('Failed to initialize WebSocket:', error);
        update(state => ({ ...state, error: 'Failed to initialize WebSocket' }));
      }
    }
  };

  return {
    subscribe,
    
    // Initialize WebSocket
    initialize: initializeWebSocket,
    
    // Connect to WebSocket
    connect: () => {
      if (websocketClient) {
        update(state => ({ ...state, connecting: true, connectionAttempts: state.connectionAttempts + 1 }));
        websocketClient.connect();
      }
    },
    
    // Disconnect from WebSocket
    disconnect: () => {
      if (websocketClient) {
        websocketClient.disconnect();
        update(state => ({ ...state, connected: false, connecting: false }));
      }
    },
    
    // Send message through WebSocket
    send: (message: any) => {
      if (websocketClient && websocketClient.connected) {
        websocketClient.send(message);
      }
    },
    
    // Subscribe to specific WebSocket events
    subscribeToEvent: (event: string, callback: (data: any) => void) => {
      if (websocketClient) {
        websocketClient.subscribe(event, callback);
      }
    },
    
    // Get WebSocket client instance
    getClient: () => websocketClient
  };
}

export const websocketStore = createWebSocketStore();

// Derived store for connection status
export const isWebSocketConnected = derived(
  websocketStore,
  $ws => $ws.connected
);

// Derived store for WebSocket errors
export const websocketError = derived(
  websocketStore,
  $ws => $ws.error
);