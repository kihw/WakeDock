/**
 * Layout Store - Manages sidebar and layout state
 */
import { writable } from 'svelte/store';

export const sidebarOpen = writable(false);
export const mounted = writable(false);

// Layout utilities
export function closeSidebarOnMobile() {
  if (typeof window !== 'undefined' && window.innerWidth <= 768) {
    sidebarOpen.set(false);
  }
}

export function toggleSidebar() {
  sidebarOpen.update(open => !open);
}

export function handleEscapeKey(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    sidebarOpen.set(false);
  }
}

export function handleResize() {
  if (typeof window !== 'undefined' && window.innerWidth > 768) {
    sidebarOpen.set(false);
  }
}