<!--
  Secondary Button - Secondary action variant
-->
<script lang="ts">
  import BaseButton from './BaseButton.svelte';

  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let fullWidth = false;
  export let disabled = false;
  export let loading = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  $: classes = [
    'inline-flex items-center justify-center',
    'font-medium rounded-md',
    'bg-gray-100 text-gray-900',
    'hover:bg-gray-200 focus:ring-gray-500',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed',
    'transition-all duration-200',
    sizeClasses[size],
    fullWidth ? 'w-full' : ''
  ].filter(Boolean).join(' ');
</script>

<BaseButton
  {disabled}
  {loading}
  {type}
  {href}
  {target}
  {rel}
  {ariaLabel}
  {testId}
  className={classes}
  on:click
>
  {#if loading}
    <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    Loading...
  {:else}
    <slot />
  {/if}
</BaseButton>