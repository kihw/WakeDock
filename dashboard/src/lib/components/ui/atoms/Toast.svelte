<!--
  Enhanced Toast Component - Atomic Design System
  Supports all variants, auto-dismiss, and animations with design tokens
-->
<script lang="ts">
  import { scale, fly, fade } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { createEventDispatcher, onMount } from 'svelte';
  import { variants, colors } from '$lib/design-system/tokens';

  // Props
  export let variant: 'success' | 'warning' | 'error' | 'info' | 'neutral' = 'info';
  export let title: string | undefined = undefined;
  export let message: string = '';
  export let dismissible = true;
  export let autoDismiss = true;
  export let duration = 5000;
  export let position:
    | 'top-left'
    | 'top-right'
    | 'bottom-left'
    | 'bottom-right'
    | 'top-center'
    | 'bottom-center' = 'top-right';
  export let icon: string | undefined = undefined;
  export let showIcon = true;
  export let actions: Array<{
    label: string;
    action: () => void;
    variant?: 'primary' | 'secondary';
  }> = [];
  export let testId: string | undefined = undefined;

  // Events
  const dispatch = createEventDispatcher<{
    dismiss: void;
    action: { label: string };
  }>();

  // State
  let isVisible = true;
  let progressWidth = 100;
  let autoDismissTimer: ReturnType<typeof setTimeout>;
  let progressTimer: ReturnType<typeof setInterval>;

  // Computed
  $: hasTitle = title || $$slots.title;
  $: hasMessage = message || $$slots.default;
  $: hasActions = actions.length > 0 || $$slots.actions;
  $: hasIcon = showIcon && (icon || $$slots.icon || getDefaultIcon(variant));

  // Icons for variants
  function getDefaultIcon(variant: string): string {
    const icons = {
      success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      warning:
        'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z',
      error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
      info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      neutral: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    };
    return icons[variant] || icons.info;
  }

  // Variant classes using design tokens
  const variantClasses = {
    success: {
      container: variants.toast.success,
      icon: 'text-success-400',
      title: 'text-white',
      message: 'text-success-100',
      button: 'text-white hover:bg-success-700',
      progress: 'bg-success-400',
    },
    warning: {
      container: variants.toast.warning,
      icon: 'text-warning-400',
      title: 'text-white',
      message: 'text-warning-100',
      button: 'text-white hover:bg-warning-700',
      progress: 'bg-warning-400',
    },
    error: {
      container: variants.toast.error,
      icon: 'text-error-400',
      title: 'text-white',
      message: 'text-error-100',
      button: 'text-white hover:bg-error-700',
      progress: 'bg-error-400',
    },
    info: {
      container: variants.toast.info,
      icon: 'text-primary-400',
      title: 'text-white',
      message: 'text-primary-100',
      button: 'text-white hover:bg-primary-700',
      progress: 'bg-primary-400',
    },
    neutral: {
      container: 'bg-neutral-600 text-white shadow-lg border border-neutral-700',
      icon: 'text-neutral-400',
      title: 'text-white',
      message: 'text-neutral-100',
      button: 'text-white hover:bg-neutral-700',
      progress: 'bg-neutral-400',
    },
  };

  // Position classes
  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
    'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2',
  };

  // Build classes
  $: classes = [
    'fixed z-50 max-w-sm w-full',
    'bg-white rounded-lg shadow-lg border',
    'pointer-events-auto',
    variantClasses[variant].container,
    positionClasses[position],
  ]
    .filter(Boolean)
    .join(' ');

  // Auto-dismiss logic
  onMount(() => {
    if (autoDismiss && duration > 0) {
      // Start progress bar animation
      progressTimer = setInterval(() => {
        progressWidth = Math.max(0, progressWidth - 100 / (duration / 100));
        if (progressWidth <= 0) {
          clearInterval(progressTimer);
        }
      }, 100);

      // Auto-dismiss timer
      autoDismissTimer = setTimeout(() => {
        handleDismiss();
      }, duration);
    }

    return () => {
      if (autoDismissTimer) clearTimeout(autoDismissTimer);
      if (progressTimer) clearInterval(progressTimer);
    };
  });

  // Event handlers
  function handleDismiss() {
    isVisible = false;
    dispatch('dismiss');
  }

  function handleAction(action: { label: string; action: () => void }) {
    action.action();
    dispatch('action', { label: action.label });
  }

  function handleMouseEnter() {
    if (autoDismissTimer) {
      clearTimeout(autoDismissTimer);
    }
    if (progressTimer) {
      clearInterval(progressTimer);
    }
  }

  function handleMouseLeave() {
    if (autoDismiss && duration > 0 && progressWidth > 0) {
      const remainingTime = (progressWidth / 100) * duration;

      progressTimer = setInterval(() => {
        progressWidth = Math.max(0, progressWidth - 100 / (remainingTime / 100));
        if (progressWidth <= 0) {
          clearInterval(progressTimer);
        }
      }, 100);

      autoDismissTimer = setTimeout(() => {
        handleDismiss();
      }, remainingTime);
    }
  }
</script>

{#if isVisible}
  <div
    class={classes}
    data-testid={testId}
    role="alert"
    aria-live="assertive"
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    in:fly={{
      x: position.includes('right') ? 300 : position.includes('left') ? -300 : 0,
      y: position.includes('top') ? -50 : position.includes('bottom') ? 50 : 0,
      duration: 300,
      easing: quintOut,
    }}
    out:fade={{ duration: 200 }}
  >
    <!-- Progress bar -->
    {#if autoDismiss && duration > 0}
      <div
        class="absolute bottom-0 left-0 right-0 h-1 bg-black bg-opacity-10 rounded-b-lg overflow-hidden"
      >
        <div
          class={`h-full ${variantClasses[variant].progress} transition-all duration-100 ease-linear`}
          style={`width: ${progressWidth}%`}
        />
      </div>
    {/if}

    <!-- Content -->
    <div class="p-4">
      <div class="flex items-start">
        <!-- Icon -->
        {#if hasIcon}
          <div class="flex-shrink-0">
            {#if icon}
              <i class={`${icon} w-5 h-5 ${variantClasses[variant].icon}`} aria-hidden="true"></i>
            {:else if $$slots.icon}
              <slot name="icon" />
            {:else}
              <svg
                class={`w-5 h-5 ${variantClasses[variant].icon}`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d={getDefaultIcon(variant)}
                />
              </svg>
            {/if}
          </div>
        {/if}

        <!-- Content -->
        <div class={`flex-1 ${hasIcon ? 'ml-3' : ''}`}>
          <!-- Title -->
          {#if hasTitle}
            <h3 class={`text-sm font-medium ${variantClasses[variant].title}`}>
              {#if title}
                {title}
              {:else}
                <slot name="title" />
              {/if}
            </h3>
          {/if}

          <!-- Message -->
          {#if hasMessage}
            <div class={`${hasTitle ? 'mt-1' : ''} text-sm ${variantClasses[variant].message}`}>
              {#if message}
                {message}
              {:else}
                <slot />
              {/if}
            </div>
          {/if}

          <!-- Actions -->
          {#if hasActions}
            <div class="mt-3 flex space-x-2">
              {#each actions as action}
                <button
                  type="button"
                  class={`text-sm font-medium ${variantClasses[variant].button} hover:underline focus:outline-none focus:underline`}
                  on:click={() => handleAction(action)}
                >
                  {action.label}
                </button>
              {/each}

              {#if $$slots.actions}
                <slot name="actions" />
              {/if}
            </div>
          {/if}
        </div>

        <!-- Dismiss button -->
        {#if dismissible}
          <div class="flex-shrink-0 ml-4">
            <button
              type="button"
              class={`inline-flex rounded-md p-1.5 ${variantClasses[variant].button} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white`}
              on:click={handleDismiss}
              aria-label="Dismiss"
            >
              <svg
                class="w-5 h-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  /* Ensure smooth transitions */
  :global(.transition-all) {
    transition-property: all;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 100ms;
  }

  /* Custom transform utilities */
  :global(.transform) {
    transform: translateX(var(--tw-translate-x, 0)) translateY(var(--tw-translate-y, 0))
      rotate(var(--tw-rotate, 0)) skewX(var(--tw-skew-x, 0)) skewY(var(--tw-skew-y, 0))
      scaleX(var(--tw-scale-x, 1)) scaleY(var(--tw-scale-y, 1));
  }

  :global(.-translate-x-1\/2) {
    --tw-translate-x: -50%;
  }
</style>
