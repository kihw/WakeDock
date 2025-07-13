<!--
  Enhanced Avatar Component - Atomic Design System
  Supports images, initials, icons, and status indicators with design tokens
-->
<script lang="ts">
  import { scale, fade } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';
  import { variants } from '$lib/design-system/tokens';

  // Props
  export let src: string | undefined = undefined;
  export let alt: string = '';
  export let name: string | undefined = undefined;
  export let initials: string | undefined = undefined;
  export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' = 'md';
  export let variant: 'circle' | 'square' | 'rounded' = 'circle';
  export let colorVariant: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'neutral' = 'neutral';
  export let status: 'online' | 'offline' | 'away' | 'busy' | undefined = undefined;
  export let statusPosition: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' =
    'bottom-right';
  export let border = false;
  export let borderColor = 'border-gray-300';
  export let fallbackIcon: string | undefined = undefined;
  export let backgroundColor: string | undefined = undefined;
  export let textColor: string | undefined = undefined;
  export let clickable = false;
  export let loading = false;
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  // Events
  const dispatch = createEventDispatcher<{
    click: MouseEvent;
    error: Event;
    load: Event;
  }>();

  // State
  let imageError = false;
  let imageLoaded = false;
  let isHovered = false;

  // Computed
  $: displayInitials = initials || getInitials(name);
  $: hasImage = src && !imageError;
  $: hasInitials = displayInitials && !hasImage;
  $: hasFallbackIcon = fallbackIcon || $$slots.fallbackIcon;
  $: isInteractive = clickable || href;
  $: isLink = href !== undefined;
  
  // Use design tokens for colors, with fallback to props
  $: avatarColors = variants.avatar[colorVariant] || variants.avatar.neutral;
  $: finalBackgroundColor = backgroundColor || avatarColors;
  $: finalTextColor = textColor || (colorVariant === 'neutral' ? 'text-neutral-800' : `text-${colorVariant}-800`);

  // Size classes
  const sizeClasses = {
    xs: {
      container: 'w-6 h-6',
      text: 'text-xs',
      icon: 'w-3 h-3',
      status: 'w-2 h-2',
    },
    sm: {
      container: 'w-8 h-8',
      text: 'text-sm',
      icon: 'w-4 h-4',
      status: 'w-2.5 h-2.5',
    },
    md: {
      container: 'w-10 h-10',
      text: 'text-base',
      icon: 'w-5 h-5',
      status: 'w-3 h-3',
    },
    lg: {
      container: 'w-12 h-12',
      text: 'text-lg',
      icon: 'w-6 h-6',
      status: 'w-3.5 h-3.5',
    },
    xl: {
      container: 'w-16 h-16',
      text: 'text-xl',
      icon: 'w-8 h-8',
      status: 'w-4 h-4',
    },
    '2xl': {
      container: 'w-20 h-20',
      text: 'text-2xl',
      icon: 'w-10 h-10',
      status: 'w-5 h-5',
    },
  };

  // Variant classes
  const variantClasses = {
    circle: 'rounded-full',
    square: 'rounded-none',
    rounded: 'rounded-md',
  };

  // Status classes
  const statusClasses = {
    online: 'bg-green-400 border-green-500',
    offline: 'bg-gray-400 border-gray-500',
    away: 'bg-yellow-400 border-yellow-500',
    busy: 'bg-red-400 border-red-500',
  };

  // Status position classes
  const statusPositionClasses = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0',
  };

  // Build classes
  $: classes = [
    'relative inline-flex items-center justify-center',
    'flex-shrink-0',
    'overflow-hidden',
    sizeClasses[size].container,
    variantClasses[variant],
    border ? `border-2 ${borderColor}` : '',
    isInteractive ? 'cursor-pointer transition-all duration-200 hover:opacity-80' : '',
    loading ? 'animate-pulse' : '',
  ]
    .filter(Boolean)
    .join(' ');

  // Utility functions
  function getInitials(name: string | undefined): string {
    if (!name) return '';

    const names = name.trim().split(' ');
    if (names.length === 1) {
      return names[0].substring(0, 2).toUpperCase();
    }

    return names
      .slice(0, 2)
      .map((n) => n.charAt(0).toUpperCase())
      .join('');
  }

  // Event handlers
  function handleClick(event: MouseEvent) {
    if (!isInteractive) return;
    dispatch('click', event);
  }

  function handleImageError(event: Event) {
    imageError = true;
    imageLoaded = false;
    dispatch('error', event);
  }

  function handleImageLoad(event: Event) {
    imageError = false;
    imageLoaded = true;
    dispatch('load', event);
  }

  function handleMouseEnter() {
    isHovered = true;
  }

  function handleMouseLeave() {
    isHovered = false;
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (!isInteractive) return;

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (event.currentTarget instanceof HTMLElement) {
        event.currentTarget.click();
      }
    }
  }
</script>

{#if isLink}
  <a
    {href}
    {target}
    class={classes}
    {alt}
    data-testid={testId}
    on:click={handleClick}
    on:keydown={handleKeyDown}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
  >
    <!-- Image -->
    {#if hasImage}
      <img
        {src}
        {alt}
        class="w-full h-full object-cover"
        on:error={handleImageError}
        on:load={handleImageLoad}
        in:fade={{ duration: 200 }}
      />
    {:else if hasInitials}
      <!-- Initials -->
      <div class={`w-full h-full flex items-center justify-center ${finalBackgroundColor}`}>
        <span class={`font-medium ${finalTextColor} ${sizeClasses[size].text}`}>
          {displayInitials}
        </span>
      </div>
    {:else if hasFallbackIcon}
      <!-- Fallback icon -->
      <div class={`w-full h-full flex items-center justify-center ${finalBackgroundColor}`}>
        {#if fallbackIcon}
          <i class={`${fallbackIcon} ${sizeClasses[size].icon} ${finalTextColor}`} aria-hidden="true"
          ></i>
        {:else}
          <slot name="fallbackIcon" />
        {/if}
      </div>
    {:else}
      <!-- Default user icon -->
      <div class={`w-full h-full flex items-center justify-center ${finalBackgroundColor}`}>
        <svg
          class={`${sizeClasses[size].icon} ${finalTextColor}`}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          />
        </svg>
      </div>
    {/if}

    <!-- Status indicator -->
    {#if status}
      <div
        class={`absolute ${statusPositionClasses[statusPosition]} transform translate-x-1/2 -translate-y-1/2`}
      >
        <div
          class={`${sizeClasses[size].status} ${statusClasses[status]} rounded-full border-2 border-white`}
        ></div>
      </div>
    {/if}

    <!-- Loading overlay -->
    {#if loading}
      <div class="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center">
        <div class="animate-spin rounded-full h-1/2 w-1/2 border-b-2 border-white"></div>
      </div>
    {/if}
  </a>
{:else}
  <div
    class={classes}
    data-testid={testId}
    tabindex={isInteractive ? 0 : -1}
    role={isInteractive ? 'button' : 'img'}
    aria-label={alt || name}
    on:click={handleClick}
    on:keydown={handleKeyDown}
    on:mouseenter={handleMouseEnter}
    on:mouseleave={handleMouseLeave}
  >
    <!-- Image -->
    {#if hasImage}
      <img
        {src}
        {alt}
        class="w-full h-full object-cover"
        on:error={handleImageError}
        on:load={handleImageLoad}
        in:fade={{ duration: 200 }}
      />
    {:else if hasInitials}
      <!-- Initials -->
      <div class={`w-full h-full flex items-center justify-center ${finalBackgroundColor}`}>
        <span class={`font-medium ${finalTextColor} ${sizeClasses[size].text}`}>
          {displayInitials}
        </span>
      </div>
    {:else if hasFallbackIcon}
      <!-- Fallback icon -->
      <div class={`w-full h-full flex items-center justify-center ${finalBackgroundColor}`}>
        {#if fallbackIcon}
          <i class={`${fallbackIcon} ${sizeClasses[size].icon} ${finalTextColor}`} aria-hidden="true"
          ></i>
        {:else}
          <slot name="fallbackIcon" />
        {/if}
      </div>
    {:else}
      <!-- Default user icon -->
      <div class={`w-full h-full flex items-center justify-center ${finalBackgroundColor}`}>
        <svg
          class={`${sizeClasses[size].icon} ${finalTextColor}`}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          />
        </svg>
      </div>
    {/if}

    <!-- Status indicator -->
    {#if status}
      <div
        class={`absolute ${statusPositionClasses[statusPosition]} transform translate-x-1/2 -translate-y-1/2`}
      >
        <div
          class={`${sizeClasses[size].status} ${statusClasses[status]} rounded-full border-2 border-white`}
        ></div>
      </div>
    {/if}

    <!-- Loading overlay -->
    {#if loading}
      <div class="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center">
        <div class="animate-spin rounded-full h-1/2 w-1/2 border-b-2 border-white"></div>
      </div>
    {/if}
  </div>
{/if}

<style>
  /* Ensure smooth transitions */
  :global(.transition-all) {
    transition-property: all;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 200ms;
  }

  /* Custom transform utilities */
  :global(.transform) {
    transform: translateX(var(--tw-translate-x, 0)) translateY(var(--tw-translate-y, 0));
  }

  :global(.translate-x-1\/2) {
    --tw-translate-x: 50%;
  }

  :global(.-translate-y-1\/2) {
    --tw-translate-y: -50%;
  }
</style>
