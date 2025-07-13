// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
  namespace App {
    interface Error {
      message: string;
      code?: string;
      details?: Record<string, unknown>;
      timestamp?: string;
      requestId?: string;
    }

    interface Locals {
      user: import('./lib/types/user').User | null;
      isAuthenticated: boolean;
      errorContext?: {
        request: Request;
        userAgent?: string;
        timestamp: string;
        userId?: number;
      };
    }

    interface PageData {
      user?: import('./lib/types/user').User;
      flash?: {
        type: 'success' | 'error' | 'warning' | 'info';
        message: string;
      };
    }

    interface PageState {
      selected?: string;
      scrollY?: number;
      filters?: Record<string, unknown>;
    }

    interface Platform {
      env?: {
        VITE_API_URL?: string;
        VITE_WS_URL?: string;
        VITE_APP_ENV?: string;
        VITE_APP_VERSION?: string;
      };
    }
  }

  // Global type declarations
  interface Window {
    __WAKEDOCK_CONFIG__?: {
      apiUrl: string;
      wsUrl: string;
      version: string;
      environment: string;
    };
  }

  // Service Worker types
  interface ServiceWorkerGlobalScope {
    clients: Clients;
    registration: ServiceWorkerRegistration;
    skipWaiting(): Promise<void>;
  }

  // Notification types for PWA
  interface CustomNotificationOptions {
    body?: string;
    icon?: string;
    badge?: string;
    image?: string;
    data?: Record<string, unknown>;
    actions?: Array<{
      action: string;
      title: string;
      icon?: string;
    }>;
    tag?: string;
    renotify?: boolean;
    silent?: boolean | null;
    requireInteraction?: boolean;
    timestamp?: number;
  }
}

// Module declarations for assets
declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}

declare module '*.ico' {
  const content: string;
  export default content;
}

// Environment variables
declare module '$env/static/private' {
  export const NODE_ENV: string;
  export const VITE_API_URL: string;
  export const VITE_WS_URL: string;
}

declare module '$env/static/public' {
  export const PUBLIC_API_URL: string;
  export const PUBLIC_WS_URL: string;
  export const PUBLIC_APP_VERSION: string;
}

declare module '$env/dynamic/private' {
  export const env: Record<string, string>;
}

declare module '$env/dynamic/public' {
  export const env: Record<string, string>;
}

export {};
