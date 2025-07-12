<!--
  Base Button Component - Core functionality only
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let disabled = false;
  export let loading = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let testId: string | undefined = undefined;
  export let className = '';

  const dispatch = createEventDispatcher<{
    click: MouseEvent;
  }>();

  $: isDisabled = disabled || loading;
  $: isLink = href !== undefined;

  function handleClick(event: MouseEvent) {
    if (isDisabled) {
      event.preventDefault();
      return;
    }
    dispatch('click', event);
  }
</script>

{#if isLink}
  <a
    {href}
    {target}
    {rel}
    class={className}
    aria-label={ariaLabel}
    data-testid={testId}
    tabindex={isDisabled ? -1 : 0}
    role="button"
    on:click={handleClick}
  >
    <slot />
  </a>
{:else}
  <button
    {type}
    {disabled}
    class={className}
    aria-label={ariaLabel}
    data-testid={testId}
    on:click={handleClick}
  >
    <slot />
  </button>
{/if}