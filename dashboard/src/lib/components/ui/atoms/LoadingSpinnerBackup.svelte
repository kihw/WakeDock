<script lang="ts">
  import { getLoadingStore, cancelLoading } from '$lib/utils/loading';
  import type { LoadingState } from '$lib/utils/loading';
  import { variants } from '$lib/design-system/tokens';
  import { cssBridge } from '$lib/design-system/css-bridge';
  import { onMount } from 'svelte';

  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let color: string = 'var(--color-primary)';
  export let text: string = '';
  export let center: boolean = false;
  export let className: string = '';
  export let loadingKey: string = '';
  export let showProgress: boolean = false;
  export let showCancel: boolean = false;
  export let inline: boolean = false;
  export let variant: 'spinner' | 'pulse' | 'dots' = 'spinner';

  // Apply CSS bridge on component mount to ensure custom properties are available
  onMount(() => {
    cssBridge.applyToDocument();
  });

  // Enhanced loading state management
  $: loadingStore = loadingKey ? getLoadingStore(loadingKey) : null;
  $: loadingState = loadingStore ? ($loadingStore as LoadingState) : null;

  // Use loading state operation if available, fallback to text prop
  $: displayText = loadingState?.operation || text;
  $: showCancelButton = showCancel && loadingState?.canCancel;
  $: progress = loadingState?.progress;

  // Size mappings using design tokens
  const sizeClasses = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large',
  };

  const textSizes = {
    small: '0.8rem',
    medium: '0.9rem',
    large: '1.1rem',
  };

  // Variant classes for different loading animations
  $: variantClass = {
    spinner: '',
    pulse: 'pulse',
    dots: 'dots'
  }[variant];

  function handleCancel() {
    if (loadingKey && loadingState?.canCancel) {
      cancelLoading(loadingKey);
    }
  }

  // Calculate loading duration
  $: duration = loadingState?.startTime
    ? Math.floor((Date.now() - loadingState.startTime.getTime()) / 1000)
    : 0;
</script>

<div class="spinner-container {sizeClasses[size]} {variantClass} {className}" class:center class:inline>
  <div class="spinner-content">
    <div class="spinner" style="border-top-color: {color}">
      <div class="spinner-inner"></div>
    </div>

    <!-- Cancel button -->
    {#if showCancelButton}
      <button
        type="button"
        on:click={handleCancel}
        class="cancel-button"
        title="Cancel operation"
        aria-label="Cancel loading operation"
      >
        <svg class="cancel-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

  {#if displayText}
    <p class="spinner-text" style="font-size: {textSizes[size]}">
      {displayText}
      {#if duration > 3}
        <span class="duration">({duration}s)</span>
      {/if}
    </p>
  {/if}

  <!-- Progress bar -->
  {#if showProgress && typeof progress === 'number'}
    <div class="progress-container">
      <div class="progress-bar" style="width: {progress}%" />
    </div>
    <div class="progress-text" style="font-size: {textSizes[size]}">
      {Math.round(progress)}%
    </div>
  {/if}
</div>

<style>
  .spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .spinner-container.center {
    justify-content: center;
    min-height: 200px;
  }

  .spinner-container.inline {
    flex-direction: row;
    min-height: auto;
    gap: 0.75rem;
  }

  .spinner-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    position: relative;
  }

  .spinner {
    position: relative;
    border: 2px solid var(--color-border);
    border-top: 2px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .cancel-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    color: var(--color-text-secondary);
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .cancel-button:hover {
    color: var(--color-error);
    background-color: var(--color-error-bg);
  }

  .cancel-button:focus {
    outline: 2px solid var(--color-focus);
    outline-offset: 2px;
  }

  .cancel-icon {
    width: 1rem;
    height: 1rem;
  }

  .duration {
    color: var(--color-text-secondary);
    font-size: 0.85em;
    margin-left: 0.25rem;
  }

  .progress-container {
    width: 100%;
    max-width: 200px;
    height: 4px;
    background-color: var(--color-border);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background-color: var(--color-primary);
    transition: width 0.3s ease;
    border-radius: 2px;
  }

  .progress-text {
    color: var(--color-text-secondary);
    font-weight: 500;
    text-align: center;
  }

  .spinner-inner {
    position: absolute;
    top: 2px;
    left: 2px;
    right: 2px;
    bottom: 2px;
    border: 1px solid transparent;
    border-top: 1px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite reverse;
    opacity: 0.6;
  }

  .spinner-small .spinner {
    width: 16px;
    height: 16px;
    border-width: 1px;
  }

  .spinner-small .spinner-inner {
    border-width: 0.5px;
    top: 1px;
    left: 1px;
    right: 1px;
    bottom: 1px;
  }

  .spinner-medium .spinner {
    width: 24px;
    height: 24px;
  }

  .spinner-large .spinner {
    width: 40px;
    height: 40px;
    border-width: 3px;
  }

  .spinner-large .spinner-inner {
    border-width: 1.5px;
    top: 3px;
    left: 3px;
    right: 3px;
    bottom: 3px;
  }

  .spinner-text {
    margin: 0;
    color: var(--color-text-secondary);
    font-weight: 500;
    text-align: center;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  /* Pulse variant for different loading states */
  .spinner-container.pulse .spinner {
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  /* Dots variant */
  .spinner-container.dots .spinner {
    display: none;
  }

  .spinner-container.dots::after {
    content: '';
    display: inline-block;
    width: 40px;
    height: 10px;
    background: linear-gradient(
      90deg,
      var(--color-primary) 0%,
      var(--color-primary) 25%,
      transparent 25%,
      transparent 75%,
      var(--color-primary) 75%
    );
    background-size: 10px 10px;
    animation: dots 1.2s infinite linear;
  }

  @keyframes dots {
    0% {
      background-position: 0 0;
    }
    100% {
      background-position: 40px 0;
    }
  }
</style>
