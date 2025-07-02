/**
 * UI Store
 * Manages UI state like modals, notifications, theme, etc.
 */
import { writable } from 'svelte/store';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number; // in milliseconds, 0 for persistent
  timestamp: Date;
}

export interface Modal {
  id: string;
  type: string;
  data?: any;
  onConfirm?: () => void;
  onCancel?: () => void;
}

interface UIState {
  theme: 'light' | 'dark' | 'auto';
  sidebar: {
    collapsed: boolean;
    pinned: boolean;
  };
  notifications: Notification[];
  modals: Modal[];
  loading: {
    global: boolean;
    tasks: Set<string>; // For tracking specific loading tasks
  };
}

const initialState: UIState = {
  theme: 'auto',
  sidebar: {
    collapsed: false,
    pinned: true,
  },
  notifications: [],
  modals: [],
  loading: {
    global: false,
    tasks: new Set(),
  },
};

// Create the writable store
const { subscribe, set, update } = writable<UIState>(initialState);

// Auto-remove notifications
const scheduleNotificationRemoval = (id: string, duration: number) => {
  if (duration > 0) {
    setTimeout(() => {
      ui.removeNotification(id);
    }, duration);
  }
};

// UI store with methods
export const ui = {
  subscribe,

  // Theme management
  setTheme: (theme: 'light' | 'dark' | 'auto') => {
    update((state) => ({ ...state, theme }));

    // Persist theme preference
    if (typeof window !== 'undefined') {
      localStorage.setItem('wakedock_theme', theme);
    }
  },

  // Initialize theme from localStorage
  initTheme: () => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('wakedock_theme') as 'light' | 'dark' | 'auto';
      if (savedTheme) {
        ui.setTheme(savedTheme);
      }
    }
  },

  // Sidebar management
  toggleSidebar: () => {
    update((state) => ({
      ...state,
      sidebar: {
        ...state.sidebar,
        collapsed: !state.sidebar.collapsed,
      },
    }));
  },

  setSidebarCollapsed: (collapsed: boolean) => {
    update((state) => ({
      ...state,
      sidebar: {
        ...state.sidebar,
        collapsed,
      },
    }));
  },

  toggleSidebarPin: () => {
    update((state) => ({
      ...state,
      sidebar: {
        ...state.sidebar,
        pinned: !state.sidebar.pinned,
      },
    }));
  },

  // Notification management
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const duration = notification.duration ?? 5000; // Default 5 seconds

    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      duration,
    };

    update((state) => ({
      ...state,
      notifications: [...state.notifications, newNotification],
    }));

    scheduleNotificationRemoval(id, duration);
    return id;
  },

  removeNotification: (id: string) => {
    update((state) => ({
      ...state,
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearAllNotifications: () => {
    update((state) => ({ ...state, notifications: [] }));
  },

  // Convenience methods for different notification types
  showSuccess: (title: string, message?: string, duration?: number) => {
    return ui.addNotification({ type: 'success', title, message, duration });
  },

  showError: (title: string, message?: string, duration?: number) => {
    return ui.addNotification({ type: 'error', title, message, duration: duration || 0 }); // Errors persist by default
  },

  showWarning: (title: string, message?: string, duration?: number) => {
    return ui.addNotification({ type: 'warning', title, message, duration });
  },

  showInfo: (title: string, message?: string, duration?: number) => {
    return ui.addNotification({ type: 'info', title, message, duration });
  },

  // Modal management
  openModal: (modal: Omit<Modal, 'id'>) => {
    const id = `modal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newModal: Modal = { ...modal, id };

    update((state) => ({
      ...state,
      modals: [...state.modals, newModal],
    }));

    return id;
  },

  closeModal: (id?: string) => {
    update((state) => ({
      ...state,
      modals: id ? state.modals.filter((m) => m.id !== id) : state.modals.slice(0, -1),
    }));
  },

  closeAllModals: () => {
    update((state) => ({ ...state, modals: [] }));
  },

  // Loading state management
  setGlobalLoading: (loading: boolean) => {
    update((state) => ({
      ...state,
      loading: {
        ...state.loading,
        global: loading,
      },
    }));
  },

  addLoadingTask: (taskId: string) => {
    update((state) => ({
      ...state,
      loading: {
        ...state.loading,
        tasks: new Set([...state.loading.tasks, taskId]),
      },
    }));
  },

  removeLoadingTask: (taskId: string) => {
    update((state) => {
      const newTasks = new Set(state.loading.tasks);
      newTasks.delete(taskId);

      return {
        ...state,
        loading: {
          ...state.loading,
          tasks: newTasks,
        },
      };
    });
  },

  clearAllLoadingTasks: () => {
    update((state) => ({
      ...state,
      loading: {
        ...state.loading,
        tasks: new Set(),
      },
    }));
  },

  // Convenience method to wrap async operations with loading state
  withLoading: async <T>(taskId: string, asyncFn: () => Promise<T>): Promise<T> => {
    ui.addLoadingTask(taskId);
    try {
      return await asyncFn();
    } finally {
      ui.removeLoadingTask(taskId);
    }
  },
};
