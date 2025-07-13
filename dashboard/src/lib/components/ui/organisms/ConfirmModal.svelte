<!-- Confirmation Modal Component -->
<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import Modal from './Modal.svelte';
  import Button from '../atoms/Button.svelte';
  import { sanitizeInput, generateCSRFToken, checkRateLimit } from '../../../utils/validation';
  import { announceToScreenReader, manageFocus } from '../../../utils/accessibility';
  import { colors } from '$lib/design-system/tokens';

  export let open: boolean = false;
  export let title: string = 'Confirm Action';
  export let message: string = 'Are you sure you want to perform this action?';
  export let confirmText: string = 'Confirm';
  export let cancelText: string = 'Cancel';
  export let confirmVariant: 'primary' | 'danger' | 'success' | 'warning' = 'primary';
  export let loading: boolean = false;
  export let persistent: boolean = false;
  export let ariaLabel: string = '';
  export let ariaDescribedBy: string = '';

  const dispatch = createEventDispatcher<{
    confirm: { csrfToken: string };
    cancel: void;
    close: void;
  }>();

  let csrfToken = '';
  let modalElement: HTMLElement;

  // Initialize security
  onMount(async () => {
    csrfToken = await generateCSRFToken();
  });

  // Enhanced confirm handler with security checks
  const handleConfirm = async () => {
    // Rate limiting check
    if (!checkRateLimit('confirm-modal', 3, 60000)) {
      announceToScreenReader(
        'Action blocked due to rate limiting. Please wait before trying again.'
      );
      return;
    }

    try {
      announceToScreenReader('Confirming action...');
      dispatch('confirm', { csrfToken });
    } catch (error) {
      console.error('Confirm error:', error);
      announceToScreenReader('Error confirming action. Please try again.');
    }
  };

  const handleCancel = () => {
    open = false;
    announceToScreenReader('Action cancelled');
    dispatch('cancel');
  };

  const handleClose = () => {
    if (!loading) {
      open = false;
      announceToScreenReader('Modal closed');
      dispatch('close');
    }
  };

  // Announce modal state changes
  $: if (open) {
    announceToScreenReader(`Confirmation dialog opened: ${sanitizeInput(title)}`);
  }
</script>

<Modal
  bind:open
  size="sm"
  {persistent}
  showCloseButton={!loading}
  closeOnEscape={!loading}
  on:close={handleClose}
  role="alertdialog"
  ariaLabel={ariaLabel || `${sanitizeInput(title)} confirmation dialog`}
  ariaDescribedBy={ariaDescribedBy || 'confirm-message confirm-description'}
>
  <header slot="header" class="flex items-center">
    {#if confirmVariant === 'danger'}
      <div
        class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-error-100 mr-3"
        role="img"
        aria-label="Warning icon for dangerous action"
      >
        <svg
          class="h-6 w-6 text-error-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
    {:else if confirmVariant === 'warning'}
      <div
        class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-warning-100 mr-3"
        role="img"
        aria-label="Warning icon"
      >
        <svg
          class="h-6 w-6 text-warning-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
    {:else if confirmVariant === 'success'}
      <div
        class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-success-100 mr-3"
        role="img"
        aria-label="Success icon"
      >
        <svg
          class="h-6 w-6 text-success-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
    {:else}
      <div
        class="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-primary-100 mr-3"
        role="img"
        aria-label="Information icon"
      >
        <svg
          class="h-6 w-6 text-primary-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
    {/if}
    <h1 class="text-lg font-medium text-secondary-900" id="confirm-title">
      {sanitizeInput(title)}
    </h1>
  </header>

  <div class="text-sm text-secondary-500" id="confirm-message" aria-live="polite">
    {sanitizeInput(message)}
  </div>

  <div id="confirm-description" class="sr-only" aria-live="polite">
    {confirmVariant === 'danger'
      ? 'This is a destructive action that cannot be undone.'
      : confirmVariant === 'warning'
        ? 'Please review this action carefully before proceeding.'
        : 'Please confirm you want to proceed with this action.'}
  </div>

  <footer slot="footer" class="flex space-x-3" role="group" aria-label="Confirmation actions">
    <Button
      variant="secondary"
      on:click={handleCancel}
      disabled={loading}
      ariaLabel="Cancel action and close dialog"
    >
      {sanitizeInput(cancelText)}
    </Button>

    <Button
      variant={confirmVariant}
      on:click={handleConfirm}
      {loading}
      disabled={loading}
      ariaLabel="Confirm action: {sanitizeInput(confirmText)}"
      ariaDescribedBy="confirm-description"
    >
      {sanitizeInput(confirmText)}
    </Button>
  </footer>
</Modal>

<style>
  /* Accessibility Enhancements */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  /* Focus Management */
  :global(.modal-content:focus-within) {
    outline: 2px solid var(--color-focus);
    outline-offset: 2px;
  }

  /* High Contrast Support */
  @media (prefers-contrast: high) {
    .flex-shrink-0 {
      border: 2px solid currentColor;
    }

    h1 {
      font-weight: bold;
    }
  }
</style>
