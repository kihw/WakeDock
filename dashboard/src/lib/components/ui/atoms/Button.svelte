<!--
  Enhanced Button Component - Atomic Design System
  Supports all variants, sizes, states, and accessibility features
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { scale, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';

  // Props
  export let variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost' =
    'primary';
  export let size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
  export let disabled = false;
  export let loading = false;
  export let fullWidth = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;
  export let download: string | boolean | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let ariaDescribedBy: string | undefined = undefined;
  export let testId: string | undefined = undefined;
  export let leftIcon: string | undefined = undefined;
  export let rightIcon: string | undefined = undefined;
  export let iconOnly = false;
  export let rounded = false;
  export let elevated = false;
  export let outline = false;
  export let animatePress = true;
  export let pulse = false;
  export let loadingText = 'Loading...';

  // Events
  const dispatch = createEventDispatcher<{
    click: MouseEvent;
    focus: FocusEvent;
    blur: FocusEvent;
    mouseenter: MouseEvent;
    mouseleave: MouseEvent;
    keydown: KeyboardEvent;
    keyup: KeyboardEvent;
  }>();

  // State
  let isPressed = false;
  let isFocused = false;
  let isHovered = false;

  // Computed styles
  $: isDisabled = disabled || loading;
  $: isLink = href !== undefined;
  $: hasSlot = $$slots.default;
  $: hasLeftIcon = leftIcon || $$slots.leftIcon;
  $: hasRightIcon = rightIcon || $$slots.rightIcon;
  $: hasIcons = hasLeftIcon || hasRightIcon;

  // Base classes
  const baseClasses = [
    'inline-flex items-center justify-center',
    'font-medium',
    'transition-all duration-200 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:cursor-not-allowed',
    'select-none',
    'relative',
    'overflow-hidden',
  ];

  // Variant classes
  const variantClasses = {
    primary: {
      base: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 shadow-sm',
      disabled: 'bg-blue-300 text-blue-100',
      outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50 focus:ring-blue-500',
    },
    secondary: {
      base: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500 shadow-sm',
      disabled: 'bg-gray-50 text-gray-400',
      outline: 'border-2 border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500',
    },
    success: {
      base: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500 shadow-sm',
      disabled: 'bg-green-300 text-green-100',
      outline: 'border-2 border-green-600 text-green-600 hover:bg-green-50 focus:ring-green-500',
    },
    warning: {
      base: 'bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500 shadow-sm',
      disabled: 'bg-yellow-300 text-yellow-100',
      outline:
        'border-2 border-yellow-600 text-yellow-600 hover:bg-yellow-50 focus:ring-yellow-500',
    },
    error: {
      base: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-sm',
      disabled: 'bg-red-300 text-red-100',
      outline: 'border-2 border-red-600 text-red-600 hover:bg-red-50 focus:ring-red-500',
    },
    ghost: {
      base: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
      disabled: 'text-gray-400',
      outline: 'border-2 border-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
    },
  };

  // Size classes
  const sizeClasses = {
    sm: {
      base: 'px-3 py-1.5 text-sm',
      icon: 'p-1.5',
      gap: 'gap-1.5',
    },
    md: {
      base: 'px-4 py-2 text-sm',
      icon: 'p-2',
      gap: 'gap-2',
    },
    lg: {
      base: 'px-6 py-3 text-base',
      icon: 'p-3',
      gap: 'gap-2.5',
    },
    xl: {
      base: 'px-8 py-4 text-lg',
      icon: 'p-4',
      gap: 'gap-3',
    },
  };

  // Build final classes
  $: classes = [
    ...baseClasses,
    isDisabled
      ? variantClasses[variant].disabled
      : outline
        ? variantClasses[variant].outline
        : variantClasses[variant].base,
    iconOnly ? sizeClasses[size].icon : sizeClasses[size].base,
    hasIcons && !iconOnly ? sizeClasses[size].gap : '',
    fullWidth ? 'w-full' : '',
    rounded ? 'rounded-full' : 'rounded-md',
    elevated ? 'shadow-lg hover:shadow-xl' : '',
    pulse ? 'animate-pulse' : '',
    isPressed && animatePress ? 'scale-95' : '',
    isHovered && !isDisabled ? 'transform hover:scale-105' : '',
  ]
    .filter(Boolean)
    .join(' ');

  // Event handlers
  function handleClick(event: MouseEvent) {
    if (isDisabled) {
      event.preventDefault();
      return;
    }
    dispatch('click', event);
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (isDisabled) return;

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      isPressed = true;
    }

    dispatch('keydown', event);
  }

  function handleKeyUp(event: KeyboardEvent) {
    if (isDisabled) return;

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      isPressed = false;
      // Trigger click on Enter/Space
      if (event.currentTarget instanceof HTMLElement) {
        event.currentTarget.click();
      }
    }

    dispatch('keyup', event);
  }

  function handleFocus(event: FocusEvent) {
    if (isDisabled) return;
    isFocused = true;
    dispatch('focus', event);
  }

  function handleBlur(event: FocusEvent) {
    if (isDisabled) return;
    isFocused = false;
    isPressed = false;
    dispatch('blur', event);
  }

  function handleMouseEnter(event: MouseEvent) {
    if (isDisabled) return;
    isHovered = true;
    dispatch('mouseenter', event);
  }

  function handleMouseLeave(event: MouseEvent) {
    if (isDisabled) return;
    isHovered = false;
    isPressed = false;
    dispatch('mouseleave', event);
  }

  function handleMouseDown() {
    if (isDisabled) return;
    isPressed = true;
  }

  function handleMouseUp() {
    if (isDisabled) return;
    isPressed = false;
  }
</script>

{#if isLink}
  <a
    {href}
    {target}
    {rel}
    {download}
    class={classes}
    aria-label={ariaLabel}
    aria-describedby={ariaDescribedBy}
    data-testid={testId}
    tabindex={isDisabled ? -1 : 0}
    role="button"
    on:click={handleClick}
    on:keydown={handleKeyDown}
    on:keyup={handleKeyUp}
    on:focus={handleFocus}
    on:blur={handleBlur}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    on:mousedown={handleMouseDown}
    on:mouseup={handleMouseUp}
  >
    {#if loading}
      <div class="flex items-center justify-center">
        <svg
          class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        {#if !iconOnly}
          <span>{loadingText}</span>
        {/if}
      </div>
    {:else}
      {#if hasLeftIcon}
        <span class="flex-shrink-0">
          {#if leftIcon}
            <i class={leftIcon} aria-hidden="true"></i>
          {:else}
            <slot name="leftIcon" />
          {/if}
        </span>
      {/if}

      {#if hasSlot && !iconOnly}
        <span class="flex-1 truncate">
          <slot />
        </span>
      {/if}

      {#if hasRightIcon}
        <span class="flex-shrink-0">
          {#if rightIcon}
            <i class={rightIcon} aria-hidden="true"></i>
          {:else}
            <slot name="rightIcon" />
          {/if}
        </span>
      {/if}
    {/if}

    <!-- Ripple effect -->
    {#if isPressed && animatePress}
      <div
        class="absolute inset-0 bg-white bg-opacity-20 rounded-md pointer-events-none"
        in:scale={{ duration: 150, easing: quintOut }}
        out:scale={{ duration: 150, easing: quintOut }}
      ></div>
    {/if}
  </a>
{:else}
  <button
    {type}
    {disabled}
    class={classes}
    aria-label={ariaLabel}
    aria-describedby={ariaDescribedBy}
    data-testid={testId}
    on:click={handleClick}
    on:keydown={handleKeyDown}
    on:keyup={handleKeyUp}
    on:focus={handleFocus}
    on:blur={handleBlur}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    on:mousedown={handleMouseDown}
    on:mouseup={handleMouseUp}
  >
    {#if loading}
      <div class="flex items-center justify-center">
        <svg
          class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        {#if !iconOnly}
          <span>{loadingText}</span>
        {/if}
      </div>
    {:else}
      {#if hasLeftIcon}
        <span class="flex-shrink-0">
          {#if leftIcon}
            <i class={leftIcon} aria-hidden="true"></i>
          {:else}
            <slot name="leftIcon" />
          {/if}
        </span>
      {/if}

      {#if hasSlot && !iconOnly}
        <span class="flex-1 truncate">
          <slot />
        </span>
      {/if}

      {#if hasRightIcon}
        <span class="flex-shrink-0">
          {#if rightIcon}
            <i class={rightIcon} aria-hidden="true"></i>
          {:else}
            <slot name="rightIcon" />
          {/if}
        </span>
      {/if}
    {/if}

    <!-- Ripple effect -->
    {#if isPressed && animatePress}
      <div
        class="absolute inset-0 bg-white bg-opacity-20 rounded-md pointer-events-none"
        in:scale={{ duration: 150, easing: quintOut }}
        out:scale={{ duration: 150, easing: quintOut }}
      ></div>
    {/if}
  </button>
{/if}

<style>
  /* Custom focus styles for better accessibility */
  :global(.focus-visible) {
    outline: 2px solid currentColor;
    outline-offset: 2px;
  }

  /* Ensure smooth transitions */
  :global(.transition-all) {
    transition-property: all;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 150ms;
  }
</style>
