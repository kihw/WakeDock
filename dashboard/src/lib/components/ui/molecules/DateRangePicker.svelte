<script lang="ts">
  export let label: string = '';
  export let startDate: string = '';
  export let endDate: string = '';
  export let disabled: boolean = false;
  export let className: string = '';

  // Allow `class` prop as well
  let cssClass = '';
  export { cssClass as class };

  import { createEventDispatcher } from 'svelte';
  import { variants } from '$lib/design-system/tokens';
  const dispatch = createEventDispatcher();

  // Generate unique IDs for accessibility
  const startDateId = `start-date-${Math.random().toString(36).substr(2, 9)}`;
  const endDateId = `end-date-${Math.random().toString(36).substr(2, 9)}`;
  const groupId = `date-range-${Math.random().toString(36).substr(2, 9)}`;

  function handleChange() {
    dispatch('change', { startDate, endDate });
  }
</script>

<div class="date-range-picker {className} {cssClass}">
  {#if label}
    <fieldset class="border-0 p-0 m-0">
      <legend class="block text-sm font-medium text-secondary-700 mb-2">{label}</legend>
      <div class="flex items-center space-x-2" role="group" aria-labelledby={groupId}>
        <input
          id={startDateId}
          type="date"
          bind:value={startDate}
          on:change={handleChange}
          {disabled}
          aria-label="Start date"
          class="{variants.input.base} px-3 py-2 focus:outline-none focus:ring-2"
        />
        <span class="text-secondary-500" aria-hidden="true">to</span>
        <input
          id={endDateId}
          type="date"
          bind:value={endDate}
          on:change={handleChange}
          {disabled}
          aria-label="End date"
          class="{variants.input.base} px-3 py-2 focus:outline-none focus:ring-2"
        />
      </div>
    </fieldset>
  {:else}
    <div class="flex items-center space-x-2" role="group" aria-label="Date range picker">
      <input
        id={startDateId}
        type="date"
        bind:value={startDate}
        on:change={handleChange}
        {disabled}
        aria-label="Start date"
        class="{variants.input.base} px-3 py-2 focus:outline-none focus:ring-2"
      />
      <span class="text-secondary-500" aria-hidden="true">to</span>
      <input
        id={endDateId}
        type="date"
        bind:value={endDate}
        on:change={handleChange}
        {disabled}
        aria-label="End date"
        class="{variants.input.base} px-3 py-2 focus:outline-none focus:ring-2"
      />
    </div>
  {/if}
</div>
