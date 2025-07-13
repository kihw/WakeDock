<!--
  Enhanced Loading Spinner Component - Atomic Design System
  Multiple spinner types, sizes, and variants with design tokens
-->
<script lang="ts">
  import { scale, fade } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { variants } from '$lib/design-system/tokens';

  // Props
  export let type: 'spin' | 'pulse' | 'bounce' | 'dots' | 'bars' | 'ring' = 'spin';
  export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  export let variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'white' =
    'primary';
  export let fullScreen = false;
  export let overlay = false;
  export let label: string | undefined = undefined;
  export let showLabel = false;
  export let duration: number | undefined = undefined;
  export let testId: string | undefined = undefined;

  // Computed
  $: hasLabel = label || showLabel;
  $: accessibleLabel = label || 'Loading...';

  // Size classes
  const sizeClasses = {
    xs: {
      spinner: 'w-4 h-4',
      dot: 'w-2 h-2',
      bar: 'w-1 h-4',
      text: 'text-xs',
    },
    sm: {
      spinner: 'w-5 h-5',
      dot: 'w-2.5 h-2.5',
      bar: 'w-1.5 h-5',
      text: 'text-sm',
    },
    md: {
      spinner: 'w-6 h-6',
      dot: 'w-3 h-3',
      bar: 'w-2 h-6',
      text: 'text-base',
    },
    lg: {
      spinner: 'w-8 h-8',
      dot: 'w-4 h-4',
      bar: 'w-3 h-8',
      text: 'text-lg',
    },
    xl: {
      spinner: 'w-12 h-12',
      dot: 'w-6 h-6',
      bar: 'w-4 h-12',
      text: 'text-xl',
    },
  };

  // Variant classes using design tokens
  const variantClasses = {
    primary: 'text-primary-600',
    secondary: 'text-secondary-600', 
    success: 'text-success-600',
    warning: 'text-warning-600',
    error: 'text-error-600',
    white: 'text-white',
  };

  // Container classes
  $: containerClasses = [
    'flex items-center justify-center',
    fullScreen ? 'fixed inset-0 z-50' : '',
    overlay ? 'bg-black bg-opacity-50' : '',
    hasLabel ? 'flex-col space-y-2' : '',
  ]
    .filter(Boolean)
    .join(' ');

  // Spinner classes using design tokens for more sophisticated styling
  $: spinnerClasses = [
    variantClasses[variant], 
    'animate-spin',
    type === 'ring' ? variants.spinner[variant] || variants.spinner.primary : ''
  ].filter(Boolean).join(' ');

  // Animation styles
  $: animationStyle = duration ? `animation-duration: ${duration}ms` : '';
</script>

<div
  class={containerClasses}
  role="status"
  aria-live="polite"
  aria-label={accessibleLabel}
  data-testid={testId}
  style={animationStyle}
>
  {#if type === 'spin'}
    <!-- Spinning circle -->
    <svg
      class={`${sizeClasses[size].spinner} ${spinnerClasses}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  {:else if type === 'ring'}
    <!-- Ring spinner -->
    <div class={`${sizeClasses[size].spinner} ${variantClasses[variant]} animate-spin`}>
      <div class="absolute inset-0 border-4 border-current border-opacity-25 rounded-full"></div>
      <div
        class="absolute inset-0 border-4 border-transparent border-t-current rounded-full animate-spin"
      ></div>
    </div>
  {:else if type === 'pulse'}
    <!-- Pulsing circle -->
    <div class={`${sizeClasses[size].spinner} ${variantClasses[variant]} animate-pulse`}>
      <div class="w-full h-full bg-current rounded-full"></div>
    </div>
  {:else if type === 'bounce'}
    <!-- Bouncing circle -->
    <div class={`${sizeClasses[size].spinner} ${variantClasses[variant]} animate-bounce`}>
      <div class="w-full h-full bg-current rounded-full"></div>
    </div>
  {:else if type === 'dots'}
    <!-- Three dots -->
    <div class="flex space-x-1">
      {#each Array(3) as _, i}
        <div
          class={`${sizeClasses[size].dot} ${variantClasses[variant]} bg-current rounded-full animate-bounce`}
          style={`animation-delay: ${i * 0.15}s`}
        />
      {/each}
    </div>
  {:else if type === 'bars'}
    <!-- Animated bars -->
    <div class="flex space-x-1">
      {#each Array(3) as _, i}
        <div
          class={`${sizeClasses[size].bar} ${variantClasses[variant]} bg-current animate-pulse`}
          style={`animation-delay: ${i * 0.15}s`}
        />
      {/each}
    </div>
  {/if}

  {#if hasLabel}
    <div class={`${sizeClasses[size].text} ${variantClasses[variant]} font-medium`}>
      {#if label}
        {label}
      {:else}
        Loading...
      {/if}
    </div>
  {/if}

  <!-- Screen reader only text -->
  <span class="sr-only">{accessibleLabel}</span>
</div>

<style>
  /* Custom animation keyframes */
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
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

  @keyframes bounce {
    0%,
    100% {
      transform: translateY(0);
      animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
    }
    50% {
      transform: translateY(-25%);
      animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
    }
  }

  /* Apply animations */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  :global(.animate-pulse) {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  :global(.animate-bounce) {
    animation: bounce 1s infinite;
  }

  /* Screen reader only utility */
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
</style>
