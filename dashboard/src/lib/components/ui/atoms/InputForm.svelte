<script lang="ts">
  import { sanitizeInput } from '$lib/utils/validation';
  import { manageFocus, announceToScreenReader } from '$lib/utils/accessibility';
  import { variants } from '$lib/design-system/tokens';

  export let label: string;
  export let id: string;
  export let type: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' = 'text';
  export let value: string | number = '';
  export let placeholder: string = '';
  export let required: boolean = false;
  export let disabled: boolean = false;
  export let readonly: boolean = false;
  export let error: string = '';
  export let help: string = '';
  export let autocomplete: string = '';
  export let maxlength: number | undefined = undefined;
  export let minlength: number | undefined = undefined;
  export let min: number | undefined = undefined;
  export let max: number | undefined = undefined;
  export let step: number | undefined = undefined;
  export let pattern: string = '';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let showValidation: boolean = true;
  export let sanitize: boolean = true;
  export let ariaLabel: string = '';
  export let ariaDescribedBy: string = '';

  // Allow `class` prop as well (standard HTML attribute)
  let cssClass = '';
  export { cssClass as class };

  // Input sizing classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  // Generate unique ID if not provided
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const errorId = `${inputId}-error`;
  const helpId = `${inputId}-help`;

  // Determine aria-describedby value
  $: describedBy = [ariaDescribedBy, error ? errorId : null, help && !error ? helpId : null]
    .filter(Boolean)
    .join(' ');

  // Handle input event with security and accessibility
  const handleInput = (event: Event) => {
    const target = event.target as HTMLInputElement;
    let newValue: string | number;

    if (type === 'number') {
      newValue = target.valueAsNumber || 0;
    } else {
      newValue = target.value;
      // Sanitize input if enabled
      if (sanitize && typeof newValue === 'string') {
        newValue = sanitizeInput(newValue);
      }
    }

    value = newValue;
  };

  // Handle blur event for validation feedback
  const handleBlur = (event: Event) => {
    if (error) {
      announceToScreenReader(`Field ${label} has an error: ${error}`);
    }
  };

  // Focus management
  export const focus = () => {
    const input = document.getElementById(inputId);
    if (input) {
      manageFocus(input as HTMLInputElement);
    }
  };
</script>

<div class="form-field">
  <label for={inputId} class="block text-sm font-medium text-secondary-700 mb-1">
    {label}
    {#if required}
      <span class="text-error-500 ml-1" aria-label="required">*</span>
    {/if}
  </label>

  <div class="relative">
    <input
      id={inputId}
      {type}
      {placeholder}
      {required}
      {disabled}
      {readonly}
      {autocomplete}
      {maxlength}
      {minlength}
      {min}
      {max}
      {step}
      {pattern}
      class="block w-full {sizeClasses[
        size
      ]} {variants.input.base} disabled:bg-secondary-100 disabled:cursor-not-allowed transition-colors duration-200"
      class:border-error-300={error}
      class:focus:border-error-500={error}
      class:focus:ring-error-500={error}
      class:border-success-300={showValidation && value && !error}
      class:focus:border-success-500={showValidation && value && !error}
      class:focus:ring-success-500={showValidation && value && !error}
      class:pr-10={error || (showValidation && value && !error)}
      value={type === 'number' ? value : value}
      aria-label={ariaLabel || label}
      aria-describedby={describedBy || undefined}
      aria-invalid={error ? 'true' : 'false'}
      aria-required={required ? 'true' : 'false'}
      on:input={handleInput}
      on:blur={handleBlur}
      on:focus
      on:change
      on:keydown
      on:keyup
      on:keypress
    />

    <!-- Validation icons -->
    {#if showValidation && (error || (value && !error))}
      <div class="absolute inset-y-0 right-0 flex items-center pr-3">
        {#if error}
          <svg
            class="h-5 w-5 text-error-500"
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
            class="h-5 w-5 text-success-500"
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

  {#if error}
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

  <!-- Help text -->
  {#if help && !error}
    <p id={helpId} class="mt-1 text-sm text-secondary-500">
      {help}
    </p>
  {/if}

  <!-- Error message -->
  {#if error}
    <p id={errorId} class="mt-1 text-sm text-error-600" role="alert">
      <span class="sr-only">Error:</span>
      {error}
    </p>
  {/if}
</div>

<style>
  .form-field {
    margin-bottom: 1rem;
  }
</style>
