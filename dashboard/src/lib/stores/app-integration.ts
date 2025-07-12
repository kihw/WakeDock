/**
 * App Integration Store - Coordinates auth and websocket interactions
 */
import { auth } from './auth.js';
import { websocketStore } from './websocket.js';

// Subscribe to auth changes and manage WebSocket connection accordingly
auth.subscribe(authState => {
  if (authState.isAuthenticated && !authState.isLoading) {
    // Start WebSocket connection when user logs in
    websocketStore.connect();
  } else if (!authState.isAuthenticated) {
    // Disconnect WebSocket when user logs out
    websocketStore.disconnect();
  }
});

// Initialize WebSocket on app start
if (typeof window !== 'undefined') {
  websocketStore.initialize();
}

export const appIntegration = {
  // Initialize the app integration
  initialize: () => {
    console.log('🔗 App integration initialized');
  }
};