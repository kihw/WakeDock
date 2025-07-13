<!--
  Enhanced Card Component - Atomic Design System
  Supports all variants, interactions, and accessibility features
-->
<script lang="ts">
  import { scale, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { createEventDispatcher } from 'svelte';
  import { variants } from '$lib/design-system/tokens';

  // Props
  export let variant: 'default' | 'elevated' | 'outlined' | 'filled' | 'ghost' = 'default';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let rounded = false;
  export let interactive = false;
  export let loading = false;
  export let disabled = false;
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let padding: 'none' | 'sm' | 'md' | 'lg' | boolean = 'md';
  export let header: string | undefined = undefined;
  export let footer: string | undefined = undefined;
  export let divider = false;
  export let hoverable = false;
  export let focusable = false;
  export let fullWidth = false;
  export let fullHeight = false;
  export let overflow: 'visible' | 'hidden' | 'scroll' | 'auto' = 'visible';
  export let ariaLabel: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  // Legacy compatibility props for migration from simple Card component
  export let title: string | undefined = undefined;
  export let subtitle: string | undefined = undefined;
  export let className: string = '';

  // Allow `class` prop as well for compatibility
  let cssClass = '';
  export { cssClass as class };

  // Events
  const dispatch = createEventDispatcher<{
    click: MouseEvent;
    focus: FocusEvent;
    blur: FocusEvent;
    keydown: KeyboardEvent;
    mouseenter: MouseEvent;
    mouseleave: MouseEvent;
  }>();

  // State
  let isHovered = false;
  let isFocused = false;
  let isPressed = false;

  // Computed
  $: effectiveHeader = title || header;
  $: effectiveFooter = subtitle || footer;
  $: hasHeader = effectiveHeader || $$slots.header;
  $: hasFooter = effectiveFooter || $$slots.footer;
  $: hasContent = $$slots.default;
  $: isInteractive = interactive || href || focusable;
  $: isLink = href !== undefined;
  $: isDisabled = disabled || loading;

  // Handle legacy boolean padding
  $: effectivePadding = typeof padding === 'boolean' 
    ? (padding ? 'md' : 'none') 
    : padding;

  // Base classes
  const baseClasses = ['block', 'transition-all duration-200 ease-in-out', 'relative'];

  // Variant classes from design tokens
  const variantClasses = {
    default: {
      base: variants.card.base,
      hover: 'hover:shadow-md',
      focus: 'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
    },
    elevated: {
      base: variants.card.elevated,
      hover: 'hover:shadow-xl',
      focus: 'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
    },
    outlined: {
      base: variants.card.outlined,
      hover: 'hover:border-secondary-400',
      focus: 'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:border-primary-500',
    },
    filled: {
      base: variants.card.filled,
      hover: 'hover:bg-secondary-100',
      focus: 'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
    },
    ghost: {
      base: 'bg-transparent border border-transparent',
      hover: 'hover:bg-secondary-50',
      focus: 'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
    },
  };

  // Size classes
  const sizeClasses = {
    sm: {
      base: 'text-sm',
      rounded: 'rounded-md',
    },
    md: {
      base: 'text-base',
      rounded: 'rounded-lg',
    },
    lg: {
      base: 'text-lg',
      rounded: 'rounded-xl',
    },
  };

  // Padding classes
  const paddingClasses = {
    none: 'p-0',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  // Build classes
  $: classes = [
    ...baseClasses,
    variantClasses[variant].base,
    sizeClasses[size].base,
    rounded ? 'rounded-2xl' : sizeClasses[size].rounded,
    fullWidth ? 'w-full' : '',
    fullHeight ? 'h-full' : '',
    overflow !== 'visible' ? `overflow-${overflow}` : '',
    isInteractive && !isDisabled ? 'cursor-pointer' : '',
    isInteractive && !isDisabled && hoverable ? variantClasses[variant].hover : '',
    isInteractive && !isDisabled && focusable ? variantClasses[variant].focus : '',
    isInteractive && !isDisabled && focusable ? 'focus:outline-none' : '',
    isPressed && isInteractive ? 'scale-[0.98] transition-transform duration-100' : '',
    isDisabled ? 'opacity-50 cursor-not-allowed' : '',
    className, // Legacy className support
    cssClass, // Legacy class support
  ]
    .filter(Boolean)
    .join(' ');

  $: containerClasses = [hasHeader || hasFooter ? 'flex flex-col' : '', fullHeight ? 'h-full' : '']
    .filter(Boolean)
    .join(' ');

  $: headerClasses = [
    'px-4 py-3',
    'border-b border-gray-200',
    'font-semibold text-gray-900',
    divider ? 'border-gray-300' : '',
  ]
    .filter(Boolean)
    .join(' ');

  $: contentClasses = [
    paddingClasses[effectivePadding],
    hasHeader && hasFooter ? 'flex-1' : '',
    overflow !== 'visible' ? `overflow-${overflow}` : '',
  ]
    .filter(Boolean)
    .join(' ');

  $: footerClasses = [
    'px-4 py-3',
    'border-t border-gray-200',
    'text-sm text-gray-600',
    divider ? 'border-gray-300' : '',
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

  function handleKeyDown(event: KeyboardEvent) {
    if (isDisabled) return;

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
    if (isDisabled) return;

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      isPressed = false;
    }
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
    class={classes}
    aria-label={ariaLabel}
    data-testid={testId}
    tabindex={isDisabled ? -1 : 0}
    role="button"
    on:click={handleClick}
    on:focus={handleFocus}
    on:blur={handleBlur}
    on:keydown={handleKeyDown}
    on:keyup={handleKeyUp}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    on:mousedown={handleMouseDown}
    on:mouseup={handleMouseUp}
  >
    <div class={containerClasses}>
      {#if hasHeader}
        <div class={headerClasses}>
          {#if effectiveHeader}
            {effectiveHeader}
          {:else}
            <slot name="header" />
          {/if}
        </div>
      {/if}

      {#if hasContent}
        <div class={contentClasses}>
          {#if loading}
            <div class="flex items-center justify-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          {:else}
            <slot />
          {/if}
        </div>
      {/if}

      {#if hasFooter}
        <div class={footerClasses}>
          {#if effectiveFooter}
            {effectiveFooter}
          {:else}
            <slot name="footer" />
          {/if}
        </div>
      {/if}
    </div>
  </a>
{:else}
  <div
    class={classes}
    aria-label={ariaLabel}
    data-testid={testId}
    tabindex={isInteractive && !isDisabled ? 0 : -1}
    role={isInteractive ? 'button' : undefined}
    on:click={handleClick}
    on:focus={handleFocus}
    on:blur={handleBlur}
    on:keydown={handleKeyDown}
    on:keyup={handleKeyUp}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
    on:mousedown={handleMouseDown}
    on:mouseup={handleMouseUp}
  >
    <div class={containerClasses}>
      {#if hasHeader}
        <div class={headerClasses}>
          {#if effectiveHeader}
            {effectiveHeader}
          {:else}
            <slot name="header" />
          {/if}
        </div>
      {/if}

      {#if hasContent}
        <div class={contentClasses}>
          {#if loading}
            <div class="flex items-center justify-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          {:else}
            <slot />
          {/if}
        </div>
      {/if}

      {#if hasFooter}
        <div class={footerClasses}>
          {#if effectiveFooter}
            {effectiveFooter}
          {:else}
            <slot name="footer" />
          {/if}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  /* Ensure smooth transitions */
  :global(.transition-all) {
    transition-property: all;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 200ms;
  }

  :global(.transition-transform) {
    transition-property: transform;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 100ms;
  }

  /* Focus styles */
  :global(.focus-visible) {
    outline: 2px solid transparent;
    outline-offset: 2px;
  }
</style>
