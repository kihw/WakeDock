<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let id: string;
  export let name: string;
  export let label: string;
  export let checked: boolean = false;
  export let required: boolean = false;
  export let disabled: boolean = false;
  export let error: string | null = null;
  export let helpText: string = '';

  const dispatch = createEventDispatcher<{
    change: { checked: boolean };
  }>();

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement;
    checked = target.checked;
    dispatch('change', { checked });
  }
</script>

<div class="flex items-start">
  <input
    {id}
    {name}
    type="checkbox"
    {required}
    {disabled}
    {checked}
    on:change={handleChange}
    class="mt-1 h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500 focus:ring-2 focus:outline-none
      {error ? 'border-red-500' : ''}"
    aria-describedby={error ? `${id}-error` : helpText ? `${id}-help` : undefined}
    aria-invalid={error ? 'true' : 'false'}
  />
  <div class="ml-2 flex-1">
    <label for={id} class="block text-sm text-gray-900">
      {@html label}
      {#if required}
        <span class="text-red-500" aria-label="required">*</span>
      {/if}
    </label>
    
    <!-- Help text -->
    {#if !error && helpText}
      <p id="{id}-help" class="text-sm text-gray-500 mt-1">
        {helpText}
      </p>
    {/if}

    <!-- Error message -->
    {#if error}
      <p id="{id}-error" class="text-sm text-red-600 mt-1" role="alert">
        <span class="sr-only">Erreur:</span>
        {error}
      </p>
    {/if}
  </div>
</div>