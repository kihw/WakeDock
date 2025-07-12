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
  const dispatch = createEventDispatcher();

  function handleChange() {
    dispatch('change', { startDate, endDate });
  }
</script>

<div class="date-range-picker {className} {cssClass}">
  {#if label}
    <label class="block text-sm font-medium text-gray-700 mb-2">{label}</label>
  {/if}
  <div class="flex items-center space-x-2">
    <input
      type="date"
      bind:value={startDate}
      on:change={handleChange}
      {disabled}
      class="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    />
    <span class="text-gray-500">to</span>
    <input
      type="date"
      bind:value={endDate}
      on:change={handleChange}
      {disabled}
      class="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    />
  </div>
</div>
