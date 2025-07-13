<!--
  Enhanced Badge Component - Atomic Design System
  Supports all variants, sizes, and states with design tokens
-->
<script lang="ts">
  import { scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { variants } from '$lib/design-system/tokens';

  // Props
  export let variant:
    | 'primary'
    | 'secondary'
    | 'success'
    | 'warning'
    | 'error'
    | 'info'
    | 'neutral' = 'primary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let rounded = false;
  export let outlined = false;
  export let dot = false;
  export let removable = false;
  export let icon: string | undefined = undefined;
  export let pulse = false;
  export let clickable = false;
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  // Events
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher<{
    click: MouseEvent;
    remove: void;
    keydown: KeyboardEvent;
  }>();

  // State
  let isHovered = false;
  let isPressed = false;

  // Computed
  $: hasSlot = $$slots.default;
  $: hasIcon = icon || $$slots.icon;
  $: isInteractive = clickable || href || removable;
  $: isLink = href !== undefined;

  // Base classes
  const baseClasses = [
    'inline-flex items-center justify-center',
    'font-medium',
    'whitespace-nowrap',
    'select-none',
  ];

  // Variant classes using design tokens
  const variantClasses = {
    primary: {
      filled: variants.badge.primary,
      outlined: 'border-primary-500 text-primary-700 bg-transparent',
      dot: 'bg-primary-500',
    },
    secondary: {
      filled: variants.badge.secondary,
      outlined: 'border-secondary-500 text-secondary-700 bg-transparent',
      dot: 'bg-secondary-500',
    },
    success: {
      filled: variants.badge.success,
      outlined: 'border-success-500 text-success-700 bg-transparent',
      dot: 'bg-success-500',
    },
    warning: {
      filled: variants.badge.warning,
      outlined: 'border-warning-500 text-warning-700 bg-transparent',
      dot: 'bg-warning-500',
    },
    error: {
      filled: variants.badge.error,
      outlined: 'border-error-500 text-error-700 bg-transparent',
      dot: 'bg-error-500',
    },
    info: {
      filled: variants.badge.info,
      outlined: 'border-primary-500 text-primary-700 bg-transparent',
      dot: 'bg-primary-500',
    },
    neutral: {
      filled: variants.badge.neutral,
      outlined: 'border-neutral-500 text-neutral-700 bg-transparent',
      dot: 'bg-neutral-500',
    },
  };

  // Size classes
  const sizeClasses = {
    sm: {
      badge: 'px-2 py-0.5 text-xs',
      gap: 'gap-1',
      icon: 'w-3 h-3',
      dot: 'w-2 h-2',
      removeButton: 'ml-1 -mr-0.5 w-4 h-4',
    },
    md: {
      badge: 'px-2.5 py-1 text-sm',
      gap: 'gap-1.5',
      icon: 'w-4 h-4',
      dot: 'w-2.5 h-2.5',
      removeButton: 'ml-1.5 -mr-0.5 w-5 h-5',
    },
    lg: {
      badge: 'px-3 py-1.5 text-base',
      gap: 'gap-2',
      icon: 'w-5 h-5',
      dot: 'w-3 h-3',
      removeButton: 'ml-2 -mr-1 w-6 h-6',
    },
  };

  // Build classes
  $: classes = [
    ...baseClasses,
    outlined ? variantClasses[variant].outlined : variantClasses[variant].filled,
    outlined ? 'border-2' : 'border',
    sizeClasses[size].badge,
    hasIcon || hasSlot ? sizeClasses[size].gap : '',
    rounded ? 'rounded-full' : 'rounded-md',
    pulse ? 'animate-pulse' : '',
    isInteractive ? 'cursor-pointer hover:opacity-80 transition-opacity duration-200' : '',
    isPressed ? 'scale-95 transition-transform duration-100' : '',
  ]
    .filter(Boolean)
    .join(' ');

  // Event handlers
  function handleClick(event: MouseEvent) {
    if (!isInteractive) return;
    dispatch('click', event);
  }

  function handleRemove(event: MouseEvent) {
    event.stopPropagation();
    dispatch('remove');
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (!isInteractive) return;

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      isPressed = true;
      if (event.currentTarget instanceof HTMLElement) {
        event.currentTarget.click();
      }
    }

    dispatch('keydown', event);
  }

  function handleKeyUp(event: KeyboardEvent) {
    if (!isInteractive) return;

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      isPressed = false;
    }
  }

  function handleMouseEnter() {
    if (!isInteractive) return;
    isHovered = true;
  }

  function handleMouseLeave() {
    if (!isInteractive) return;
    isHovered = false;
    isPressed = false;
  }

  function handleMouseDown() {
    if (!isInteractive) return;
    isPressed = true;
  }

  function handleMouseUp() {
    if (!isInteractive) return;
    isPressed = false;
  }
</script>

{#if dot}
  <!-- Dot variant -->
  <span
    class={`inline-block ${sizeClasses[size].dot} ${variantClasses[variant].dot} rounded-full ${pulse ? 'animate-pulse' : ''}`}
    aria-label={ariaLabel}
    data-testid={testId}
    role={isInteractive ? 'button' : null}
    tabindex={isInteractive ? 0 : null}
    on:click={handleClick}
    on:keydown={handleKeyDown}
    on:keyup={handleKeyUp}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    on:mousedown={handleMouseDown}
    on:mouseup={handleMouseUp}
  ></span>
{:else if isLink}
  <!-- Link variant -->
  <a
    {href}
    {target}
    class={classes}
    aria-label={ariaLabel}
    data-testid={testId}
    on:click={handleClick}
    on:keydown={handleKeyDown}
    on:keyup={handleKeyUp}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    on:mousedown={handleMouseDown}
    on:mouseup={handleMouseUp}
  >
    {#if hasIcon}
      <span class="flex-shrink-0">
        {#if icon}
          <i class={`${icon} ${sizeClasses[size].icon}`} aria-hidden="true"></i>
        {:else}
          <slot name="icon" />
        {/if}
      </span>
    {/if}

    {#if hasSlot}
      <span class="flex-1 truncate">
        <slot />
      </span>
    {/if}

    {#if removable}
      <button
        type="button"
        class={`${sizeClasses[size].removeButton} flex-shrink-0 rounded-full hover:bg-black hover:bg-opacity-10 focus:outline-none focus:bg-black focus:bg-opacity-10 transition-colors duration-200`}
        on:click={handleRemove}
        aria-label="Remove"
      >
        <svg
          class="w-full h-full"
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
    {/if}
  </a>
{:else}
  <!-- Regular badge -->
  <span
    class={classes}
    aria-label={ariaLabel}
    data-testid={testId}
    role={isInteractive ? 'button' : null}
    tabindex={isInteractive ? 0 : null}
    on:click={handleClick}
    on:keydown={handleKeyDown}
    on:keyup={handleKeyUp}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    on:mousedown={handleMouseDown}
    on:mouseup={handleMouseUp}
  >
    {#if hasIcon}
      <span class="flex-shrink-0">
        {#if icon}
          <i class={`${icon} ${sizeClasses[size].icon}`} aria-hidden="true"></i>
        {:else}
          <slot name="icon" />
        {/if}
      </span>
    {/if}

    {#if hasSlot}
      <span class="flex-1 truncate">
        <slot />
      </span>
    {/if}

    {#if removable}
      <button
        type="button"
        class={`${sizeClasses[size].removeButton} flex-shrink-0 rounded-full hover:bg-black hover:bg-opacity-10 focus:outline-none focus:bg-black focus:bg-opacity-10 transition-colors duration-200`}
        on:click={handleRemove}
        aria-label="Remove"
      >
        <svg
          class="w-full h-full"
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
    {/if}
  </span>
{/if}

<style>
  /* Ensure smooth transitions */
  :global(.transition-opacity) {
    transition-property: opacity;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 200ms;
  }

  :global(.transition-transform) {
    transition-property: transform;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 100ms;
  }

  :global(.transition-colors) {
    transition-property: background-color, border-color, color, fill, stroke;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 200ms;
  }
</style>
