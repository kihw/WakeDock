import { writable } from 'svelte/store';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  dismissible?: boolean;
}

interface ToastState {
  toasts: Toast[];
}

const initialState: ToastState = {
  toasts: [],
};

function createToastStore() {
  const { subscribe, update } = writable<ToastState>(initialState);

  let toastId = 0;

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = `toast-${++toastId}`;
    const newToast: Toast = {
      id,
      duration: 5000,
      dismissible: true,
      ...toast,
    };

    update((state) => ({
      ...state,
      toasts: [...state.toasts, newToast],
    }));

    // Auto dismiss if duration is set
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }

    return id;
  };

  const removeToast = (id: string) => {
    update((state) => ({
      ...state,
      toasts: state.toasts.filter((toast) => toast.id !== id),
    }));
  };

  const clearAll = () => {
    update((state) => ({
      ...state,
      toasts: [],
    }));
  };

  return {
    subscribe,
    success: (message: string, options?: Partial<Toast>) =>
      addToast({ message, type: 'success', ...options }),
    error: (message: string, options?: Partial<Toast>) =>
      addToast({ message, type: 'error', duration: 8000, ...options }),
    warning: (message: string, options?: Partial<Toast>) =>
      addToast({ message, type: 'warning', ...options }),
    info: (message: string, options?: Partial<Toast>) =>
      addToast({ message, type: 'info', ...options }),
    add: addToast,
    remove: removeToast,
    clear: clearAll,
  };
}

export const toastStore = createToastStore();
export const toast = toastStore; // Alias pour compatibilité
