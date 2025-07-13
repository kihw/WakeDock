<!--
  Icon Button - Icon-only variant with design tokens
-->
<script lang="ts">
  import BaseButton from './BaseButton.svelte';
  import { variants } from '$lib/design-system/tokens';

  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let variant: 'primary' | 'secondary' | 'ghost' = 'ghost';
  export let disabled = false;
  export let loading = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  const sizeClasses = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3'
  };

  // Use design tokens for consistent styling
  const variantClasses = {
    primary: variants.button.primary.base,
    secondary: variants.button.secondary.base,
    ghost: variants.button.ghost.base
  };

  $: classes = [
    'inline-flex items-center justify-center',
    'rounded-md',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'transition-all duration-200',
    sizeClasses[size],
    disabled ? 'cursor-not-allowed opacity-50' : variantClasses[variant]
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
    <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  {:else}
    <slot />
  {/if}
</BaseButton>