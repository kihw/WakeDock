/// <reference lib="webworker" />

// Additional event types for service worker
interface SyncEvent extends Event {
  tag: string;
  waitUntil(promise: Promise<any>): void;
}

interface PendingAction {
  id: string;
  url: string;
  options: RequestInit;
}

// Export empty module to make this a module file
export {};
