<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { toastStore } from '../stores/toastStore';
  import Icon from './Icon.svelte';

  export let type: 'success' | 'error' | 'warning' | 'info' = 'info';
  export let message: string = '';
  export let duration: number = 5000;
  export let dismissible: boolean = true;
  export let id: string = '';

  let visible = true;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  onMount(() => {
    if (duration > 0) {
      timeoutId = setTimeout(() => {
        dismiss();
      }, duration);
    }
  });

  function dismiss() {
    visible = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    if (id) {
      toastStore.remove(id);
    }
  }

  function getIcon() {
    switch (type) {
      case 'success':
        return 'check-circle';
      case 'error':
        return 'x-circle';
      case 'warning':
        return 'alert-triangle';
      case 'info':
      default:
        return 'info';
    }
  }

  function getColorClass() {
    switch (type) {
      case 'success':
        return 'toast-success';
      case 'error':
        return 'toast-error';
      case 'warning':
        return 'toast-warning';
      case 'info':
      default:
        return 'toast-info';
    }
  }
</script>

{#if visible}
  <div
    class="toast {getColorClass()}"
    transition:fly={{ x: 300, duration: 300 }}
    role="alert"
    aria-live="polite"
  >
    <div class="toast-content">
      <Icon name={getIcon()} class="toast-icon" />
      <span class="toast-message">{message}</span>
    </div>

    {#if dismissible}
      <button
        type="button"
        class="toast-dismiss"
        on:click={dismiss}
        aria-label="Dismiss notification"
      >
        <Icon name="x" class="w-4 h-4" />
      </button>
    {/if}
  </div>
{/if}

<style>
  .toast {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(8px);
    max-width: 400px;
    min-width: 300px;
  }

  .toast-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
  }

  .toast-message {
    font-size: 0.875rem;
    line-height: 1.25rem;
  }

  .toast-dismiss {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    transition: background-color 0.15s ease;
    margin-left: 0.75rem;
  }

  .toast-dismiss:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  .toast-success {
    background-color: rgba(34, 197, 94, 0.9);
    color: white;
  }

  .toast-error {
    background-color: rgba(239, 68, 68, 0.9);
    color: white;
  }

  .toast-warning {
    background-color: rgba(245, 158, 11, 0.9);
    color: white;
  }

  .toast-info {
    background-color: rgba(59, 130, 246, 0.9);
    color: white;
  }

  :global(.toast-icon) {
    width: 1.25rem;
    height: 1.25rem;
    flex-shrink: 0;
  }
</style>
