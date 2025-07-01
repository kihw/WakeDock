<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  // Props interface
  export interface ButtonProps {
    type?: 'button' | 'submit' | 'reset';
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'ghost';
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
    disabled?: boolean;
    loading?: boolean;
    href?: string;
    target?: string;
    ariaLabel?: string;
    ariaDescribedBy?: string;
    className?: string;
    class?: string;
    'aria-label'?: string;
    'aria-describedby'?: string;
    focus?: () => void;
  }

  // Props
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let variant: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'ghost' =
    'primary';
  export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  export let disabled = false;
  export let loading = false;
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let ariaDescribedBy: string | undefined = undefined;
  export let className = '';

  // Allow `class` prop as well (standard HTML attribute)
  let cssClass = '';
  export { cssClass as class };

  // Allow aria-label prop as well
  let ariaLabelProp = '';
  export { ariaLabelProp as 'aria-label' };

  // Allow aria-describedby prop as well
  let ariaDescribedByProp = '';
  export { ariaDescribedByProp as 'aria-describedby' };

  const dispatch = createEventDispatcher();

  function handleClick(event: MouseEvent) {
    if (disabled || loading) {
      event.preventDefault();
      return;
    }
    dispatch('click', event);
  }

  // Style mappings
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white border-blue-600 hover:border-blue-700',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white border-gray-600 hover:border-gray-700',
    success: 'bg-green-600 hover:bg-green-700 text-white border-green-600 hover:border-green-700',
    warning:
      'bg-yellow-600 hover:bg-yellow-700 text-white border-yellow-600 hover:border-yellow-700',
    danger: 'bg-red-600 hover:bg-red-700 text-white border-red-600 hover:border-red-700',
    ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 border-gray-300 hover:border-gray-400',
  };

  const sizes = {
    xs: 'px-2 py-1 text-xs',
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
    xl: 'px-8 py-4 text-xl',
  };

  $: classes = [
    'inline-flex items-center justify-center font-medium border rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2',
    variants[variant],
    sizes[size],
    disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
    className,
    cssClass,
  ]
    .filter(Boolean)
    .join(' ');
</script>

<!-- Render as link if href is provided -->
{#if href}
  <a
    {href}
    {target}
    class={classes}
    aria-label={ariaLabel || ariaLabelProp || undefined}
    aria-describedby={ariaDescribedBy || ariaDescribedByProp || undefined}
    on:click={handleClick}
    tabindex={disabled ? -1 : 0}
  >
    {#if loading}
      <svg
        class="animate-spin -ml-1 mr-2 h-4 w-4"
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
    {/if}
    <slot />
  </a>
  <!-- Render as button otherwise -->
{:else}
  <button
    {type}
    {disabled}
    class={classes}
    aria-label={ariaLabel || ariaLabelProp || undefined}
    aria-describedby={ariaDescribedBy || ariaDescribedByProp || undefined}
    on:click={handleClick}
  >
    {#if loading}
      <svg
        class="animate-spin -ml-1 mr-2 h-4 w-4"
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
    {/if}
    <slot />
  </button>
{/if}

<style>
  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
