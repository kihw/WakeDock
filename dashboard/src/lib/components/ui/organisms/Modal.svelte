<!-- Base Modal Component -->
<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy, tick } from 'svelte';
  import { manageFocus, announceToScreenReader, trapFocus } from '$lib/utils/accessibility';
  import { colors } from '$lib/design-system/tokens';

  export let open: boolean = false;
  export let size: 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'md';
  export let persistent: boolean = false; // Prevent closing on backdrop click
  export let showCloseButton: boolean = true;
  export let title: string = '';
  export let closeOnEscape: boolean = true;
  export let ariaLabel: string = '';
  export let ariaDescribedBy: string = '';
  export let role: 'dialog' | 'alertdialog' = 'dialog';

  const dispatch = createEventDispatcher<{
    close: void;
    open: void;
  }>();

  // Size classes
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4',
  };

  let modalElement: HTMLDivElement;
  let previouslyFocusedElement: HTMLElement | null = null;
  let focusTrap: { destroy: () => void } | null = null;

  // Generate unique IDs for accessibility
  const titleId = `modal-title-${Math.random().toString(36).substr(2, 9)}`;
  const descriptionId = `modal-description-${Math.random().toString(36).substr(2, 9)}`;

  onMount(() => {
    // Only run in browser (not during SSR)
    if (typeof window !== 'undefined' && typeof document !== 'undefined') {
      // Global escape key handling
      const handleKeydown = (event: KeyboardEvent) => {
        if (open && closeOnEscape && event.key === 'Escape') {
          handleClose();
        }
      };

      document.addEventListener('keydown', handleKeydown);

      return () => {
        document.removeEventListener('keydown', handleKeydown);
      };
    }
  });

  onDestroy(() => {
    // Restore focus when component is destroyed
    if (previouslyFocusedElement) {
      manageFocus(previouslyFocusedElement);
    }

    // Clean up focus trap
    if (focusTrap) {
      focusTrap.destroy();
    }
  });

  // Watch for modal open/close changes
  $: if (open) {
    handleOpen();
  } else {
    handleCloseCleanup();
  }

  async function handleOpen() {
    await tick();

    // Store previously focused element
    previouslyFocusedElement = document.activeElement as HTMLElement;

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    // Set up focus trap
    if (modalElement) {
      focusTrap = trapFocus(modalElement);

      // Focus the first focusable element or the modal itself
      const firstFocusable = modalElement.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (firstFocusable) {
        manageFocus(firstFocusable as HTMLElement);
      } else {
        manageFocus(modalElement);
      }
    }

    // Announce modal opening to screen readers
    announceToScreenReader(
      `${role === 'alertdialog' ? 'Alert dialog' : 'Dialog'} opened: ${title || 'Modal dialog'}`
    );

    dispatch('open');
  }

  function handleCloseCleanup() {
    // Restore body scroll
    document.body.style.overflow = '';

    // Clean up focus trap
    if (focusTrap) {
      focusTrap.destroy();
      focusTrap = null;
    }

    // Restore focus to previously focused element
    if (previouslyFocusedElement) {
      manageFocus(previouslyFocusedElement);
      previouslyFocusedElement = null;
    }
  }

  const handleBackdropClick = (event: MouseEvent) => {
    if (!persistent && event.target === event.currentTarget) {
      handleClose();
    }
  };

  const handleBackdropKeydown = (event: KeyboardEvent) => {
    if (!persistent && event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      handleClose();
    }
  };

  const handleClose = () => {
    if (open) {
      open = false;
      dispatch('close');
    }
  };
</script>

{#if open}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-secondary-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4"
    on:click={handleBackdropClick}
    on:keydown={handleBackdropKeydown}
    bind:this={modalElement}
    {role}
    aria-modal="true"
    aria-labelledby={title ? titleId : ariaLabel ? undefined : 'modal-title'}
    aria-describedby={ariaDescribedBy || descriptionId}
    aria-label={ariaLabel}
    tabindex="-1"
  >
    <!-- Modal Content -->
    <div
      class="relative bg-white rounded-lg shadow-xl {sizeClasses[
        size
      ]} w-full max-h-full overflow-hidden"
      role="document"
      on:click|stopPropagation
    >
      <!-- Header -->
      {#if title || showCloseButton || $$slots.header}
        <div class="flex items-center justify-between p-6 border-b border-secondary-200">
          <div class="flex items-center">
            {#if $$slots.header}
              <slot name="header" />
            {:else if title}
              <h3 class="text-lg font-medium text-secondary-900">
                {title}
              </h3>
            {/if}
          </div>

          {#if showCloseButton}
            <button
              type="button"
              class="text-secondary-400 hover:text-secondary-600 focus:outline-none focus:text-secondary-600 transition ease-in-out duration-150"
              on:click={handleClose}
              aria-label="Close modal"
            >
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          {/if}
        </div>
      {/if}

      <!-- Body -->
      <div class="p-6 overflow-y-auto max-h-96">
        <slot />
      </div>

      <!-- Footer -->
      {#if $$slots.footer}
        <div class="flex items-center justify-end px-6 py-4 bg-secondary-50 border-t border-secondary-200">
          <slot name="footer" />
        </div>
      {/if}
    </div>
  </div>
{/if}
