<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let id: string;
  export let name: string;
  export let label: string;
  export let value: string = '';
  export let placeholder: string = '';
  export let required: boolean = false;
  export let disabled: boolean = false;
  export let error: string | null = null;
  export let helpText: string = '';
  export let autocomplete: string = 'email';
  export let showValidationIcon: boolean = true;

  const dispatch = createEventDispatcher<{
    input: { value: string };
    blur: { value: string };
    focus: void;
  }>();

  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    value = target.value;
    dispatch('input', { value });
  }

  function handleBlur(event: Event) {
    const target = event.target as HTMLInputElement;
    dispatch('blur', { value: target.value });
  }

  function handleFocus() {
    dispatch('focus');
  }

  $: hasValue = value && value.length > 0;
  $: isValid = hasValue && !error;
</script>

<div>
  <label for={id} class="block text-sm font-medium text-gray-700 mb-1">
    {label}
    {#if required}
      <span class="text-red-500" aria-label="required">*</span>
    {/if}
  </label>
  
  <div class="relative">
    <input
      {id}
      {name}
      type="email"
      {required}
      {disabled}
      {placeholder}
      {autocomplete}
      {value}
      on:input={handleInput}
      on:blur={handleBlur}
      on:focus={handleFocus}
      class="relative block w-full appearance-none rounded-md border px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none focus:ring-2 sm:text-sm
        {error
          ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
          : isValid
            ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
            : 'border-gray-300 focus:border-green-500 focus:ring-green-500'}
        {showValidationIcon && hasValue ? 'pr-10' : ''}"
      aria-describedby={error ? `${id}-error` : helpText ? `${id}-help` : undefined}
      aria-invalid={error ? 'true' : 'false'}
    />
    
    <!-- Validation icon -->
    {#if showValidationIcon && hasValue}
      <div class="absolute inset-y-0 right-0 flex items-center pr-3">
        {#if error}
          <svg
            class="h-5 w-5 text-red-500"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
        {:else}
          <svg
            class="h-5 w-5 text-green-500"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Help text -->
  {#if !error && helpText}
    <p id="{id}-help" class="mt-1 text-sm text-gray-500">
      {helpText}
    </p>
  {/if}

  <!-- Error message -->
  {#if error}
    <p id="{id}-error" class="mt-1 text-sm text-red-600" role="alert">
      <span class="sr-only">Erreur:</span>
      {error}
    </p>
  {/if}
</div>