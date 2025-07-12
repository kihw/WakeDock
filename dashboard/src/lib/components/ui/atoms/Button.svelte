<!--
  Button Component - Simplified unified button with variant selection
  Backward compatible with the original complex Button component
-->
<script lang="ts">
  import PrimaryButton from './PrimaryButton.svelte';
  import SecondaryButton from './SecondaryButton.svelte';
  import IconButton from './IconButton.svelte';

  export let variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost' = 'primary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let disabled = false;
  export let loading = false;
  export let fullWidth = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let testId: string | undefined = undefined;
  export let iconOnly = false;

  // Map legacy variants to simplified variants
  $: mappedVariant = variant === 'success' || variant === 'warning' || variant === 'error' ? 'primary' : variant;
  $: mappedIconVariant = variant === 'ghost' ? 'ghost' : variant === 'secondary' ? 'secondary' : 'primary';
</script>

{#if iconOnly}
  <IconButton
    {size}
    variant={mappedIconVariant}
    {disabled}
    {loading}
    {type}
    {href}
    {target}
    {rel}
    {ariaLabel}
    {testId}
    on:click
  >
    <slot />
  </IconButton>
{:else if variant === 'secondary' || variant === 'ghost'}
  <SecondaryButton
    {size}
    {fullWidth}
    {disabled}
    {loading}
    {type}
    {href}
    {target}
    {rel}
    {ariaLabel}
    {testId}
    on:click
  >
    <slot />
  </SecondaryButton>
{:else}
  <PrimaryButton
    {size}
    {fullWidth}
    {disabled}
    {loading}
    {type}
    {href}
    {target}
    {rel}
    {ariaLabel}
    {testId}
    on:click
  >
    <slot />
  </PrimaryButton>
{/if}
