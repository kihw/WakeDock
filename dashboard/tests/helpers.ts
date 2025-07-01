/**
 * Test Helpers
 * Utility functions to assist with testing
 */

import { get } from 'svelte/store';
import { vi } from 'vitest';

/**
 * Wait for a store to meet a condition
 * @param store Svelte store to watch
 * @param predicate Function that returns true when the condition is met
 * @param timeout Maximum time to wait in milliseconds
 * @returns Promise that resolves when the condition is met or rejects on timeout
 */
export const waitForStoreUpdate = (store: any, predicate: (value: any) => boolean, timeout = 5000) => {
  return new Promise<void>((resolve, reject) => {
    const startTime = Date.now();
    const checkStore = () => {
      const currentValue = get(store);

      if (predicate(currentValue)) {
        resolve();
        return;
      }

      if (Date.now() - startTime > timeout) {
        reject(new Error(`Store did not update to expected value within ${timeout}ms`));
        return;
      }

      setTimeout(checkStore, 50);
    };

    checkStore();
  });
};

/**
 * Mock a fetch response
 * @param status HTTP status code
 * @param data Response data
 * @param headers Response headers
 * @returns Mocked fetch response
 */
export const mockFetchResponse = (status = 200, data: any = {}, headers = {}) => {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(headers),
    clone: () => mockFetchResponse(status, data, headers)
  };
};

/**
 * Mock API response for testing
 * @param endpoint Endpoint to mock
 * @param response Response data
 * @param status HTTP status code
 */
export const mockApiResponse = (endpoint: string, response: any, status = 200) => {
  global.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes(endpoint)) {
      return Promise.resolve(mockFetchResponse(status, response));
    }

    // Default fallback for unmatched URLs
    return Promise.resolve(mockFetchResponse(404, { error: 'Not Found' }));
  });
};

/**
 * Mock multiple API responses
 * @param mocks Array of endpoint/response pairs
 */
export const mockMultipleApiResponses = (mocks: Array<{ endpoint: string, response: any, status?: number }>) => {
  global.fetch = vi.fn().mockImplementation((url: string) => {
    for (const mock of mocks) {
      if (url.includes(mock.endpoint)) {
        return Promise.resolve(mockFetchResponse(mock.status || 200, mock.response));
      }
    }

    // Default fallback for unmatched URLs
    return Promise.resolve(mockFetchResponse(404, { error: 'Not Found' }));
  });
};

/**
 * Wait for DOM element to appear
 * @param selector CSS selector for the element
 * @param timeout Maximum time to wait in milliseconds
 * @returns Promise that resolves with the element or rejects on timeout
 */
export const waitForElement = (selector: string, timeout = 5000): Promise<Element> => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    const check = () => {
      const element = document.querySelector(selector);

      if (element) {
        resolve(element);
        return;
      }

      if (Date.now() - startTime > timeout) {
        reject(new Error(`Element ${selector} did not appear within ${timeout}ms`));
        return;
      }

      requestAnimationFrame(check);
    };

    check();
  });
};

/**
 * Create a simple mock WebSocket for testing
 * @returns Mock WebSocket object
 */
export const createMockWebSocket = () => {
  const mockWs = {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: 1, // WebSocket.OPEN
    dispatchEvent: (event: any) => {
      const listeners = mockWs.listeners[event.type] || [];
      listeners.forEach((listener: Function) => listener(event));
      return true;
    },
    listeners: {} as Record<string, Function[]>,
    triggerMessage: (data: any) => {
      const event = new MessageEvent('message', {
        data: typeof data === 'string' ? data : JSON.stringify(data)
      });
      mockWs.dispatchEvent(event);
    },
    triggerOpen: () => {
      mockWs.dispatchEvent(new Event('open'));
    },
    triggerClose: (code = 1000, reason = '') => {
      const event = new CloseEvent('close', { code, reason, wasClean: true });
      mockWs.dispatchEvent(event);
    },
    triggerError: () => {
      mockWs.dispatchEvent(new Event('error'));
    }
  };

  // Override addEventListener to store listeners
  mockWs.addEventListener.mockImplementation((type: string, listener: Function) => {
    if (!mockWs.listeners[type]) {
      mockWs.listeners[type] = [];
    }
    mockWs.listeners[type].push(listener);
  });

  // Override removeEventListener
  mockWs.removeEventListener.mockImplementation((type: string, listener: Function) => {
    if (!mockWs.listeners[type]) return;
    const index = mockWs.listeners[type].indexOf(listener);
    if (index !== -1) {
      mockWs.listeners[type].splice(index, 1);
    }
  });

  return mockWs;
};
