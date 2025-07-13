<!-- Select Field Component -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { sanitizeInput } from '$lib/utils/validation';
  import { announceToScreenReader } from '$lib/utils/accessibility';
  import { variants } from '$lib/design-system/tokens';

  export let label: string;
  export let id: string = '';
  export let value: string | number | string[] = '';
  export let options: Array<{
    value: string | number;
    label: string;
    disabled?: boolean;
  }> = [];
  export let required: boolean = false;
  export let disabled: boolean = false;
  export let error: string = '';
  export let help: string = '';
  export let placeholder: string = '';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let multiple: boolean = false;
  export let autocomplete: string = '';
  export let ariaLabel: string = '';

  // Class prop support
  let cssClass = '';
  export { cssClass as class };

  const dispatch = createEventDispatcher<{
    change: { value: string | number | string[] };
    focus: void;
    blur: void;
  }>();

  // Select sizing classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  // Generate unique IDs for accessibility
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
  const helpId = `${selectId}-help`;
  const errorId = `${selectId}-error`;

  // Handle change event with security and accessibility
  const handleChange = (event: Event) => {
    const target = event.target as HTMLSelectElement;
    let newValue: string | number | string[];

    if (multiple) {
      const selectedValues: string[] = [];
      for (const option of target.selectedOptions) {
        // Sanitize each selected value
        const sanitizedValue = sanitizeInput(option.value);
        selectedValues.push(sanitizedValue);
      }
      newValue = selectedValues;
    } else {
      // Sanitize single value
      newValue = sanitizeInput(target.value);
    }

    value = newValue;

    // Dispatch change event
    dispatch('change', { value: newValue });

    // Announce selection to screen readers
    const selectedLabel = multiple
      ? `${(newValue as string[]).length} options selected`
      : options.find((opt) => opt.value.toString() === newValue.toString())?.label || newValue;

    announceToScreenReader(`Selected: ${selectedLabel}`);
  };

  const handleFocus = () => {
    dispatch('focus');
  };

  const handleBlur = () => {
    dispatch('blur');
  };
</script>

<div class="form-field">
  <label for={selectId} class="block text-sm font-medium text-secondary-700 mb-1">
    {label}
    {#if required}
      <span class="text-error-500 ml-1">*</span>
    {/if}
  </label>

  <div class="relative">
    <select
      id={selectId}
      {required}
      {disabled}
      {multiple}
      {autocomplete}
      aria-label={ariaLabel}
      class="block w-full {sizeClasses[
        size
      ]} border rounded-md shadow-sm focus:ring-2 focus:ring-offset-0 disabled:bg-secondary-100 disabled:cursor-not-allowed transition-colors duration-200
      {error
        ? variants.input.error
        : variants.input.base} {cssClass}"
      class:pr-10={error && !multiple}
      {value}
      on:change={handleChange}
      on:blur={handleBlur}
      on:focus={handleFocus}
      aria-describedby={error ? errorId : help ? helpId : undefined}
      aria-invalid={error ? 'true' : 'false'}
      aria-required={required}
    >
      {#if placeholder && !multiple}
        <option value="" disabled={required} hidden>
          {placeholder}
        </option>
      {/if}

      {#each options as option}
        <option value={option.value} disabled={option.disabled}>
          {option.label}
        </option>
      {/each}
    </select>

    {#if error && !multiple}
      <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
        <svg class="h-5 w-5 text-error-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fill-rule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
            clip-rule="evenodd"
          />
        </svg>
      </div>
    {/if}
  </div>

  {#if error}
    <p id={errorId} class="mt-1 text-sm text-error-600" role="alert">
      <span class="sr-only">Error:</span>
      {error}
    </p>
  {:else if help}
    <p id={helpId} class="mt-1 text-sm text-secondary-500">
      {help}
    </p>
  {/if}
</div>

<style>
  .form-field {
    margin-bottom: 1rem;
  }
</style>
