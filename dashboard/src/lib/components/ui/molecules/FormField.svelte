<!--
  FormField Molecule - Complete form field with label, input, validation, and help text
  Combines Input with proper form structure and validation display
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Input from '../atoms/Input.svelte';
  import Badge from '../atoms/Badge.svelte';

  // Props
  export let type:
    | 'text'
    | 'email'
    | 'password'
    | 'number'
    | 'tel'
    | 'url'
    | 'search'
    | 'date'
    | 'time'
    | 'datetime-local'
    | 'month'
    | 'week'
    | 'textarea'
    | 'select' = 'text';
  export let name: string;
  export let value: string | number = '';
  export let label: string;
  export let placeholder: string = '';
  export let required = false;
  export let disabled = false;
  export let readonly = false;
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let variant: 'default' | 'success' | 'warning' | 'error' = 'default';
  export let fullWidth = true;
  export let helpText: string | undefined = undefined;
  export let errorText: string | undefined = undefined;
  export let successText: string | undefined = undefined;
  export let validationRules: Array<{
    rule: (value: any) => boolean;
    message: string;
  }> = [];
  export let validateOnBlur = true;
  export let validateOnInput = false;
  export let showValidationIcon = true;
  export let leftIcon: string | undefined = undefined;
  export let rightIcon: string | undefined = undefined;
  export let clearable = false;
  export let showPasswordToggle = false;
  export let autocomplete: string | undefined = undefined;
  export let minLength: number | undefined = undefined;
  export let maxLength: number | undefined = undefined;
  export let min: number | string | undefined = undefined;
  export let max: number | string | undefined = undefined;
  export let step: number | string | undefined = undefined;
  export let pattern: string | undefined = undefined;
  export let options: Array<{ value: string | number; label: string; disabled?: boolean }> = [];
  export let rows = 3;
  export let testId: string | undefined = undefined;

  // Events
  const dispatch = createEventDispatcher<{
    input: { value: string | number; event: Event };
    change: { value: string | number; event: Event };
    focus: FocusEvent;
    blur: FocusEvent;
    validate: { valid: boolean; errors: string[] };
    clear: void;
    togglePassword: boolean;
  }>();

  // State
  let touched = false;
  let focused = false;
  let validationErrors: string[] = [];
  let isValid = true;
  let inputElement: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;

  // Computed
  $: hasError = variant === 'error' || errorText || validationErrors.length > 0;
  $: hasSuccess = variant === 'success' || successText;
  $: hasWarning = variant === 'warning';
  $: currentVariant = hasError
    ? 'error'
    : hasSuccess
      ? 'success'
      : hasWarning
        ? 'warning'
        : 'default';
  $: displayErrorText = errorText || validationErrors[0];
  $: displaySuccessText = successText;
  $: displayHelpText = helpText;
  $: fieldId = `field-${name}`;
  $: helperId = `${fieldId}-helper`;
  $: errorId = `${fieldId}-error`;
  $: successId = `${fieldId}-success`;

  // Label classes
  $: labelClasses = [
    'block text-sm font-medium mb-1',
    hasError ? 'text-red-700' : hasSuccess ? 'text-green-700' : 'text-gray-700',
  ]
    .filter(Boolean)
    .join(' ');

  // Validation
  function validateField(val: string | number): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Required validation
    if (required && (!val || val.toString().trim() === '')) {
      errors.push(`${label} is required`);
    }

    // Length validation
    if (val && typeof val === 'string') {
      if (minLength && val.length < minLength) {
        errors.push(`${label} must be at least ${minLength} characters`);
      }
      if (maxLength && val.length > maxLength) {
        errors.push(`${label} must be no more than ${maxLength} characters`);
      }
    }

    // Number validation
    if (val && type === 'number') {
      const numVal = Number(val);
      if (min !== undefined && numVal < Number(min)) {
        errors.push(`${label} must be at least ${min}`);
      }
      if (max !== undefined && numVal > Number(max)) {
        errors.push(`${label} must be no more than ${max}`);
      }
    }

    // Pattern validation
    if (val && pattern && typeof val === 'string') {
      const regex = new RegExp(pattern);
      if (!regex.test(val)) {
        errors.push(`${label} format is invalid`);
      }
    }

    // Custom validation rules
    if (val) {
      validationRules.forEach((rule) => {
        if (!rule.rule(val)) {
          errors.push(rule.message);
        }
      });
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  // Event handlers
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
    const newValue = type === 'number' ? Number(target.value) : target.value;
    value = newValue;

    // Validate on input if enabled
    if (validateOnInput || touched) {
      const validation = validateField(newValue);
      validationErrors = validation.errors;
      isValid = validation.valid;
      dispatch('validate', { valid: isValid, errors: validationErrors });
    }

    dispatch('input', { value: newValue, event });
  }

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
    const newValue = type === 'number' ? Number(target.value) : target.value;
    value = newValue;

    dispatch('change', { value: newValue, event });
  }

  function handleFocus(event: FocusEvent) {
    focused = true;
    dispatch('focus', event);
  }

  function handleBlur(event: FocusEvent) {
    focused = false;
    touched = true;

    // Validate on blur if enabled
    if (validateOnBlur) {
      const validation = validateField(value);
      validationErrors = validation.errors;
      isValid = validation.valid;
      dispatch('validate', { valid: isValid, errors: validationErrors });
    }

    dispatch('blur', event);
  }

  function handleClear() {
    value = '';
    validationErrors = [];
    isValid = true;
    dispatch('clear');
    dispatch('input', { value: '', event: new Event('input') });
  }

  function handleTogglePassword(event: CustomEvent<boolean>) {
    dispatch('togglePassword', event.detail);
  }

  // Public methods
  export function focus() {
    if (inputElement) {
      inputElement.focus();
    }
  }

  export function blur() {
    if (inputElement) {
      inputElement.blur();
    }
  }

  export function validate() {
    const validation = validateField(value);
    validationErrors = validation.errors;
    isValid = validation.valid;
    touched = true;
    dispatch('validate', { valid: isValid, errors: validationErrors });
    return validation;
  }

  export function reset() {
    value = '';
    validationErrors = [];
    isValid = true;
    touched = false;
    focused = false;
  }
</script>

<div class="form-field {fullWidth ? 'w-full' : ''}" data-testid={testId}>
  <!-- Label -->
  <label for={fieldId} class={labelClasses}>
    {label}
    {#if required}
      <span class="text-red-500 ml-1">*</span>
    {/if}
    {#if maxLength && type !== 'number'}
      <span class="text-xs text-gray-500 ml-2">
        {typeof value === 'string' ? value.length : 0}/{maxLength}
      </span>
    {/if}
  </label>

  <!-- Input Field -->
  <div class="mt-1">
    {#if type === 'textarea'}
      <textarea
        bind:this={inputElement}
        bind:value
        id={fieldId}
        {name}
        {placeholder}
        {disabled}
        {readonly}
        {required}
        {autocomplete}
        {minLength}
        {maxLength}
        {rows}
        class={`
          block w-full border rounded-md shadow-sm
          transition-all duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-offset-1
          disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500
          placeholder-gray-400 text-gray-900
          ${size === 'sm' ? 'px-3 py-1.5 text-sm' : size === 'lg' ? 'px-4 py-3 text-base' : 'px-4 py-2 text-sm'}
          ${
            currentVariant === 'error'
              ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
              : currentVariant === 'success'
                ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                : currentVariant === 'warning'
                  ? 'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }
          ${disabled ? 'bg-gray-50' : 'bg-white'}
        `}
        aria-describedby={[
          displayHelpText ? helperId : '',
          displayErrorText ? errorId : '',
          displaySuccessText ? successId : '',
        ]
          .filter(Boolean)
          .join(' ') || undefined}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
      />
    {:else if type === 'select'}
      <select
        bind:this={inputElement}
        bind:value
        id={fieldId}
        {name}
        {disabled}
        {required}
        class={`
          block w-full border rounded-md shadow-sm
          transition-all duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-offset-1
          disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500
          text-gray-900
          ${size === 'sm' ? 'px-3 py-1.5 text-sm' : size === 'lg' ? 'px-4 py-3 text-base' : 'px-4 py-2 text-sm'}
          ${
            currentVariant === 'error'
              ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
              : currentVariant === 'success'
                ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                : currentVariant === 'warning'
                  ? 'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }
          ${disabled ? 'bg-gray-50' : 'bg-white'}
        `}
        aria-describedby={[
          displayHelpText ? helperId : '',
          displayErrorText ? errorId : '',
          displaySuccessText ? successId : '',
        ]
          .filter(Boolean)
          .join(' ') || undefined}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
      >
        {#if placeholder}
          <option value="" disabled>{placeholder}</option>
        {/if}
        {#each options as option}
          <option value={option.value} disabled={option.disabled}>
            {option.label}
          </option>
        {/each}
      </select>
    {:else}
      <Input
        bind:this={inputElement}
        bind:value
        {type}
        id={fieldId}
        {name}
        {placeholder}
        {disabled}
        {readonly}
        {required}
        {autocomplete}
        {minLength}
        {maxLength}
        {min}
        {max}
        {step}
        {pattern}
        {size}
        variant={currentVariant}
        {fullWidth}
        {leftIcon}
        {rightIcon}
        {clearable}
        {showPasswordToggle}
        ariaDescribedBy={[
          displayHelpText ? helperId : '',
          displayErrorText ? errorId : '',
          displaySuccessText ? successId : '',
        ]
          .filter(Boolean)
          .join(' ') || undefined}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:clear={handleClear}
        on:togglePassword={handleTogglePassword}
      />
    {/if}
  </div>

  <!-- Help/Error/Success Text -->
  <div class="mt-1 min-h-[1.25rem]">
    {#if displayErrorText}
      <div class="flex items-center space-x-1">
        {#if showValidationIcon}
          <svg
            class="w-4 h-4 text-red-500 flex-shrink-0"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        {/if}
        <p class="text-sm text-red-600" id={errorId}>
          {displayErrorText}
        </p>
      </div>
    {:else if displaySuccessText}
      <div class="flex items-center space-x-1">
        {#if showValidationIcon}
          <svg
            class="w-4 h-4 text-green-500 flex-shrink-0"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        {/if}
        <p class="text-sm text-green-600" id={successId}>
          {displaySuccessText}
        </p>
      </div>
    {:else if displayHelpText}
      <p class="text-sm text-gray-600" id={helperId}>
        {displayHelpText}
      </p>
    {/if}
  </div>

  <!-- Additional validation badges -->
  {#if validationErrors.length > 1}
    <div class="mt-2 flex flex-wrap gap-1">
      {#each validationErrors.slice(1) as error}
        <Badge variant="error" size="sm">
          {error}
        </Badge>
      {/each}
    </div>
  {/if}
</div>

<style>
  /* Custom styles for better form field appearance */
  .form-field {
    position: relative;
  }

  /* Focus styles */
  .form-field:focus-within .form-field-label {
    color: #2563eb;
  }

  /* Textarea resize handle */
  textarea {
    resize: vertical;
  }

  /* Select dropdown arrow */
  select {
    background-image: url("data:image/svg+xml;charset=UTF-8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 9l6 6 6-6'/></svg>");
    background-repeat: no-repeat;
    background-position: right 0.5rem center;
    background-size: 1.5em 1.5em;
    padding-right: 2.5rem;
    appearance: none;
  }

  /* Disable select arrow for disabled state */
  select:disabled {
    background-image: none;
  }
</style>
