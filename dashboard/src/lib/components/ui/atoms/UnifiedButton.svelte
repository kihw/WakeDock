<!--
  Unified Button Component - TASK-UI-001
  Consolidates all button variants into a single, configurable component
  
  Replaces:
  - BaseButton.svelte
  - PrimaryButton.svelte 
  - SecondaryButton.svelte
  - IconButton.svelte
  - Button.svelte (wrapper)
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { variants } from '$lib/design-system/tokens';

  // Core props
  export let variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost' = 'primary';
  export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  export let disabled = false;
  export let loading = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';

  // Link behavior
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;

  // Icon support
  export let icon: string | undefined = undefined;
  export let iconPosition: 'left' | 'right' = 'left';
  export let iconOnly = false;

  // Layout
  export let fullWidth = false;
  export let outlined = false;

  // Accessibility
  export let ariaLabel: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  // Custom styling
  export let className = '';

  // Event dispatcher
  const dispatch = createEventDispatcher<{
    click: MouseEvent;
  }>();

  // Computed properties
  $: isDisabled = disabled || loading;
  $: isLink = href !== undefined;

  // Size classes mapping
  const sizeClasses = {
    xs: iconOnly ? 'p-1' : 'px-2 py-1 text-xs',
    sm: iconOnly ? 'p-1.5' : 'px-3 py-1.5 text-sm',
    md: iconOnly ? 'p-2' : 'px-4 py-2 text-sm',
    lg: iconOnly ? 'p-3' : 'px-6 py-3 text-base',
    xl: iconOnly ? 'p-4' : 'px-8 py-4 text-lg'
  };

  // Icon size classes
  const iconSizeClasses = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4', 
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
    xl: 'h-7 w-7'
  };

  // Base button classes
  const baseClasses = [
    'inline-flex items-center justify-center',
    'font-medium rounded-md',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'transition-all duration-200',
    'select-none'
  ].join(' ');

  // Variant classes from design tokens
  $: variantClasses = isDisabled
    ? variants.button[variant].disabled
    : variants.button[variant].base;

  // Outlined variant modification
  $: outlinedClasses = outlined && variant !== 'ghost'
    ? variantClasses.replace(/bg-\w+-\d+/, 'bg-transparent border-2').replace(/hover:bg-\w+-\d+/, 'hover:bg-opacity-10')
    : '';

  // Final computed classes
  $: computedClasses = [
    baseClasses,
    sizeClasses[size],
    outlined && variant !== 'ghost' ? outlinedClasses : variantClasses,
    fullWidth ? 'w-full' : '',
    isDisabled ? 'cursor-not-allowed' : 'cursor-pointer',
    className
  ].filter(Boolean).join(' ');

  // Event handlers
  function handleClick(event: MouseEvent) {
    if (isDisabled) {
      event.preventDefault();
      return;
    }
    dispatch('click', event);
  }

  // Loading spinner component
  function LoadingSpinner() {
    return `
      <svg class="animate-spin ${iconSizeClasses[size]} ${iconPosition === 'right' && !iconOnly ? 'ml-2' : !iconOnly ? 'mr-2' : ''}" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    `;
  }

  // Icon component helper
  function renderIcon(iconName: string, classes: string) {
    // This is a simplified icon renderer - in production you'd integrate with your icon system
    // For now, returning a generic icon placeholder
    return `<span class="${classes}" data-icon="${iconName}">⚡</span>`;
  }
</script>

{#if isLink}
  <a
    {href}
    {target}
    {rel}
    class={computedClasses}
    aria-label={ariaLabel}
    data-testid={testId}
    tabindex={isDisabled ? -1 : 0}
    role="button"
    aria-disabled={isDisabled}
    on:click={handleClick}
  >
    {#if loading}
      {@html LoadingSpinner()}
      {#if !iconOnly}
        <span class="sr-only">Loading...</span>
      {/if}
    {:else}
      {#if icon && iconPosition === 'left' && !iconOnly}
        {@html renderIcon(icon, `${iconSizeClasses[size]} mr-2`)}
      {/if}
      
      {#if iconOnly}
        {#if icon}
          {@html renderIcon(icon, iconSizeClasses[size])}
        {:else}
          <slot />
        {/if}
      {:else}
        <slot />
      {/if}
      
      {#if icon && iconPosition === 'right' && !iconOnly}
        {@html renderIcon(icon, `${iconSizeClasses[size]} ml-2`)}
      {/if}
    {/if}
  </a>
{:else}
  <button
    {type}
    {disabled}
    class={computedClasses}
    aria-label={ariaLabel}
    data-testid={testId}
    aria-disabled={isDisabled}
    on:click={handleClick}
  >
    {#if loading}
      {@html LoadingSpinner()}
      {#if !iconOnly}
        <span class="sr-only">Loading...</span>
      {/if}
    {:else}
      {#if icon && iconPosition === 'left' && !iconOnly}
        {@html renderIcon(icon, `${iconSizeClasses[size]} mr-2`)}
      {/if}
      
      {#if iconOnly}
        {#if icon}
          {@html renderIcon(icon, iconSizeClasses[size])}
        {:else}
          <slot />
        {/if}
      {:else}
        <slot />
      {/if}
      
      {#if icon && iconPosition === 'right' && !iconOnly}
        {@html renderIcon(icon, `${iconSizeClasses[size]} ml-2`)}
      {/if}
    {/if}
  </button>
{/if}

<style>
  /* Additional component-specific styles if needed */
  :global(.sr-only) {
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
</style>