<!--
  Confirm Dialog Component - Enhanced with Security & Accessibility
  Reusable confirmation dialog for destructive actions
-->
<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import Modal from './Modal.svelte';
  import Button from '../ui/atoms/Button.svelte';
  import Icon from '../Icon.svelte';
  import { sanitizeInput, generateCSRFToken, checkRateLimit } from '$lib/utils/validation';
  import { manageFocus, announceToScreenReader } from '$lib/utils/accessibility';

  // Props
  export let isOpen = false;
  export let title = 'Confirm Action';
  export let message = 'Are you sure you want to proceed?';
  export let confirmText = 'Confirm';
  export let cancelText = 'Cancel';
  export let variant: 'danger' | 'warning' | 'info' = 'warning';
  export let icon = '';
  export let isLoading = false;
  export let disabled = false;
  export let confirmButtonId = '';
  export let destructive = false;

  // Events
  const dispatch = createEventDispatcher<{
    confirm: void;
    cancel: void;
    close: void;
  }>();

  // Security & Accessibility
  let csrfToken = '';
  let attemptCount = 0;
  let lastAttemptTime = 0;
  let liveRegion: HTMLElement | undefined;
  let confirmButton: HTMLElement | undefined;
  let cancelButton: HTMLElement | undefined;

  // Rate limiting constants
  const MAX_ATTEMPTS = 5;
  const RATE_LIMIT_WINDOW = 60000; // 1 minute

  // Auto-select icon based on variant
  $: autoIcon = icon || getVariantIcon(variant);

  // Enhanced onMount
  onMount(async () => {
    // Generate CSRF token for security
    csrfToken = await generateCSRFToken();

    // Announce dialog opening
    if (isOpen) {
      const sanitizedTitle = sanitizeInput(title);
      const sanitizedMessage = sanitizeInput(message);
      announceToScreenReader(`Confirmation dialog opened: ${sanitizedTitle}. ${sanitizedMessage}`);

      // Focus management
      setTimeout(() => {
        if (destructive && confirmButton) {
          // For destructive actions, focus the cancel button by default
          cancelButton?.focus();
        } else if (confirmButton) {
          confirmButton.focus();
        }
      }, 100);
    }
  });

  onDestroy(() => {
    // Cleanup live region
    if (liveRegion && liveRegion.parentNode) {
      liveRegion.parentNode.removeChild(liveRegion);
    }
  });

  function getVariantIcon(v: typeof variant): string {
    switch (v) {
      case 'danger':
        return 'alert-triangle';
      case 'warning':
        return 'alert-circle';
      case 'info':
        return 'info';
      default:
        return 'help-circle';
    }
  }

  function getVariantColors(v: typeof variant) {
    switch (v) {
      case 'danger':
        return {
          icon: 'text-error-400',
          button: 'bg-error-600 hover:bg-error-700 focus:ring-error-500',
          border: 'border-error-500',
        };
      case 'warning':
        return {
          icon: 'text-warning-400',
          button: 'bg-warning-600 hover:bg-warning-700 focus:ring-warning-500',
          border: 'border-warning-500',
        };
      case 'info':
        return {
          icon: 'text-primary-400',
          button: 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500',
          border: 'border-primary-500',
        };
      default:
        return {
          icon: 'text-secondary-400',
          button: 'bg-secondary-600 hover:bg-secondary-700 focus:ring-secondary-500',
          border: 'border-secondary-500',
        };
    }
  }

  $: colors = getVariantColors(variant);

  // Enhanced confirm handler with security checks
  function handleConfirm() {
    if (disabled || isLoading) return;

    // Rate limiting check
    if (!checkRateLimit(attemptCount, lastAttemptTime, MAX_ATTEMPTS, RATE_LIMIT_WINDOW)) {
      announceToScreenReader('Too many attempts. Please wait before trying again.');
      return;
    }

    attemptCount++;
    lastAttemptTime = Date.now();

    // Announce action
    announceToScreenReader(`${sanitizeInput(confirmText)} action confirmed.`);

    dispatch('confirm');
  }

  // Enhanced cancel handler
  function handleCancel() {
    if (isLoading) return;

    announceToScreenReader('Action cancelled.');
    dispatch('cancel');
    dispatch('close');
  }

  // Enhanced close handler
  function handleClose() {
    if (isLoading) return;

    announceToScreenReader('Confirmation dialog closed.');
    dispatch('close');
  }

  // Handle escape key
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && !isLoading) {
      handleClose();
    } else if (event.key === 'Enter' && !disabled && !isLoading) {
      handleConfirm();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<Modal
  bind:open={isOpen}
  on:close={handleClose}
  size="sm"
  persistent={isLoading}
  closeOnEscape={!isLoading}
>
  <div class="px-6 py-4">
    <div class="flex items-start space-x-4">
      <!-- Icon -->
      <div class="flex-shrink-0">
        <div
          class="w-12 h-12 rounded-full border-2 {colors.border} bg-gray-800 flex items-center justify-center"
        >
          <Icon name={autoIcon} class="w-6 h-6 {colors.icon}" />
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <!-- Title -->
        <h3 class="text-lg font-semibold text-white mb-2">
          {title}
        </h3>

        <!-- Message -->
        <div class="text-gray-300 text-sm leading-relaxed">
          {#if typeof message === 'string'}
            <p>{message}</p>
          {:else}
            <slot name="message">
              <p>{message}</p>
            </slot>
          {/if}
        </div>

        <!-- Additional content slot -->
        <slot name="content" />
      </div>
    </div>
  </div>

  <div
    slot="footer"
    class="px-6 py-4 bg-gray-800 border-t border-gray-700 flex items-center justify-end space-x-3"
  >
    <!-- Cancel Button -->
    <Button variant="secondary" on:click={handleCancel} disabled={isLoading} class="min-w-20">
      {cancelText}
    </Button>

    <!-- Confirm Button -->
    <Button
      variant="primary"
      on:click={handleConfirm}
      disabled={disabled || isLoading}
      loading={isLoading}
      class="min-w-20 {colors.button}"
    >
      {confirmText}
    </Button>
  </div>
</Modal>

<!-- Enhanced version with slots for custom content -->
{#if $$slots.custom}
  <Modal
    bind:open={isOpen}
    on:close={handleClose}
    size="md"
    persistent={isLoading}
    closeOnEscape={!isLoading}
  >
    <div slot="header" class="flex items-center space-x-3">
      <div
        class="w-8 h-8 rounded-full border {colors.border} bg-gray-800 flex items-center justify-center"
      >
        <Icon name={autoIcon} class="w-4 h-4 {colors.icon}" />
      </div>
      <h3 class="text-lg font-semibold text-white">
        {title}
      </h3>
    </div>

    <div>
      <slot name="custom" />
    </div>

    <div slot="footer" class="flex items-center justify-end space-x-3">
      <Button variant="secondary" on:click={handleCancel} disabled={isLoading}>
        {cancelText}
      </Button>

      <Button
        variant="primary"
        on:click={handleConfirm}
        disabled={disabled || isLoading}
        loading={isLoading}
        class={colors.button}
      >
        {confirmText}
      </Button>
    </div>
  </Modal>
{/if}

<style>
  /* Custom button styles for variants */
  :global(.confirm-dialog-danger) {
    @apply bg-error-600 hover:bg-error-700 focus:ring-error-500;
  }

  :global(.confirm-dialog-warning) {
    @apply bg-warning-600 hover:bg-warning-700 focus:ring-warning-500;
  }

  :global(.confirm-dialog-info) {
    @apply bg-primary-600 hover:bg-primary-700 focus:ring-primary-500;
  }
</style>
