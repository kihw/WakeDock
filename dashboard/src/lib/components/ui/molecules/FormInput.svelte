<!--
  FormInput Component - TASK-UI-002  
  Molecular component that adds validation, labels, and help text to BaseInput
  
  Responsibilities:
  - Wrap BaseInput with label and help text
  - Handle validation logic and error display
  - Provide form integration
  - Manage input state (dirty, touched, valid)
  
  Does NOT handle:
  - Icons or decorative elements (use FieldInput)
  - Complex loading states (use FieldInput)
  - Password toggle or clear buttons (use FieldInput)
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import BaseInput from '../atoms/BaseInput.svelte';
  import type { 
    FormInputProps, 
    ValidationRule, 
    ValidationResult,
    InputEvents,
    InputState
  } from '../atoms/BaseInput.types';

  // Extend BaseInput props with form-specific features
  export let label: string | undefined = undefined;
  export let helperText: string | undefined = undefined;
  export let error: string | undefined = undefined;
  export let success: string | undefined = undefined;
  export let required = false;

  // Validation configuration
  export let validationRules: ValidationRule[] = [];
  export let validateOnBlur = true;
  export let validateOnInput = false;

  // Form integration
  export let formName: string | undefined = undefined;
  export let fieldName: string | undefined = undefined;

  // All BaseInput props (pass-through)
  export let type: FormInputProps['type'] = 'text';
  export let value: FormInputProps['value'] = '';
  export let placeholder: FormInputProps['placeholder'] = '';
  export let disabled: FormInputProps['disabled'] = false;
  export let readonly: FormInputProps['readonly'] = false;
  export let size: FormInputProps['size'] = 'md';
  export let variant: FormInputProps['variant'] = 'default';
  export let fullWidth: FormInputProps['fullWidth'] = false;
  export let id: FormInputProps['id'] = undefined;
  export let name: FormInputProps['name'] = undefined;
  export let autocomplete: FormInputProps['autocomplete'] = undefined;
  export let autofocus: FormInputProps['autofocus'] = false;
  export let minLength: FormInputProps['minLength'] = undefined;
  export let maxLength: FormInputProps['maxLength'] = undefined;
  export let min: FormInputProps['min'] = undefined;
  export let max: FormInputProps['max'] = undefined;
  export let step: FormInputProps['step'] = undefined;
  export let pattern: FormInputProps['pattern'] = undefined;
  export let ariaLabel: FormInputProps['ariaLabel'] = undefined;
  export let testId: FormInputProps['testId'] = undefined;
  export let className: FormInputProps['className'] = '';

  // Enhanced event dispatcher
  const dispatch = createEventDispatcher<InputEvents & {
    validate: ValidationResult;
    stateChange: InputState;
  }>();

  // Component state
  let inputState: InputState = {
    value: value,
    isFocused: false,
    isValid: true,
    errors: [],
    isDirty: false,
    isTouched: false
  };

  // Reactive computations
  $: inputState.value = value;
  $: inputState.isValid = inputState.errors.length === 0;

  // Generate unique IDs for accessibility
  const uniqueId = id || `form-input-${Math.random().toString(36).substr(2, 9)}`;
  const labelId = `${uniqueId}-label`;
  const errorId = `${uniqueId}-error`;
  const helperId = `${uniqueId}-helper`;

  // Computed ARIA describedby
  $: ariaDescribedBy = [
    helperText ? helperId : null,
    (error || inputState.errors.length > 0) ? errorId : null
  ].filter(Boolean).join(' ') || undefined;

  // Computed variant based on validation state
  $: computedVariant = error || inputState.errors.length > 0 
    ? 'error' 
    : success 
    ? 'success' 
    : variant;

  // Validation functions
  function validateValue(val: string | number): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // External error takes precedence
    if (error) {
      errors.push(error);
    }

    // Run validation rules
    for (const rule of validationRules) {
      const result = validateRule(val, rule);
      if (result !== true) {
        errors.push(typeof result === 'string' ? result : rule.message || 'Invalid input');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  function validateRule(val: string | number, rule: ValidationRule): boolean | string {
    const stringVal = String(val);
    
    switch (rule.type) {
      case 'required':
        return stringVal.trim().length > 0 || 'This field is required';
      
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(stringVal) || 'Please enter a valid email address';
      
      case 'minLength':
        return stringVal.length >= (rule.value as number) || 
               `Must be at least ${rule.value} characters`;
      
      case 'maxLength':
        return stringVal.length <= (rule.value as number) || 
               `Must be no more than ${rule.value} characters`;
      
      case 'pattern':
        const regex = rule.value as RegExp;
        return regex.test(stringVal) || rule.message || 'Invalid format';
      
      case 'custom':
        if (rule.validator) {
          return rule.validator(val);
        }
        return true;
      
      default:
        return true;
    }
  }

  function runValidation() {
    const result = validateValue(value);
    inputState.errors = result.errors;
    inputState.isValid = result.isValid;
    
    dispatch('validate', result);
    dispatch('stateChange', inputState);
    
    return result;
  }

  // Event handlers
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    value = type === 'number' ? +target.value : target.value;
    inputState.isDirty = true;
    
    if (validateOnInput) {
      runValidation();
    }
    
    dispatch('input', event);
  }

  function handleChange(event: Event) {
    dispatch('change', event);
  }

  function handleFocus(event: FocusEvent) {
    inputState.isFocused = true;
    dispatch('focus', event);
    dispatch('stateChange', inputState);
  }

  function handleBlur(event: FocusEvent) {
    inputState.isFocused = false;
    inputState.isTouched = true;
    
    if (validateOnBlur) {
      runValidation();
    }
    
    dispatch('blur', event);
    dispatch('stateChange', inputState);
  }

  function handleKeydown(event: KeyboardEvent) {
    dispatch('keydown', event);
  }

  function handleKeyup(event: KeyboardEvent) {
    dispatch('keyup', event);
  }

  // Public API for external validation
  export function validate(): ValidationResult {
    return runValidation();
  }

  export function reset() {
    value = '';
    inputState = {
      value: '',
      isFocused: false,
      isValid: true,
      errors: [],
      isDirty: false,
      isTouched: false
    };
    dispatch('stateChange', inputState);
  }

  export function getState(): InputState {
    return { ...inputState };
  }

  // Add required validation rule if required prop is set
  $: if (required && !validationRules.some(rule => rule.type === 'required')) {
    validationRules = [{ type: 'required' }, ...validationRules];
  }
</script>

<div class="form-input-wrapper {className}" class:has-error={error || inputState.errors.length > 0}>
  <!-- Label -->
  {#if label}
    <label 
      for={uniqueId}
      id={labelId}
      class="form-input-label"
      class:required
    >
      {label}
      {#if required}
        <span class="required-indicator" aria-label="required">*</span>
      {/if}
    </label>
  {/if}

  <!-- BaseInput -->
  <BaseInput
    {id}
    {name}
    {type}
    {value}
    {placeholder}
    {disabled}
    {readonly}
    required={required}
    {size}
    variant={computedVariant}
    {fullWidth}
    {autocomplete}
    {autofocus}
    {minLength}
    {maxLength}
    {min}
    {max}
    {step}
    {pattern}
    {ariaLabel}
    {ariaDescribedBy}
    {testId}
    on:input={handleInput}
    on:change={handleChange}
    on:focus={handleFocus}
    on:blur={handleBlur}
    on:keydown={handleKeydown}
    on:keyup={handleKeyup}
  />

  <!-- Helper Text -->
  {#if helperText && !error && inputState.errors.length === 0}
    <div id={helperId} class="form-input-helper">
      {helperText}
    </div>
  {/if}

  <!-- Error Messages -->
  {#if error || inputState.errors.length > 0}
    <div id={errorId} class="form-input-error" role="alert" aria-live="polite">
      {#if error}
        <div class="error-message">{error}</div>
      {:else}
        {#each inputState.errors as errorMsg}
          <div class="error-message">{errorMsg}</div>
        {/each}
      {/if}
    </div>
  {/if}

  <!-- Success Message -->
  {#if success && !error && inputState.errors.length === 0}
    <div class="form-input-success" role="status">
      {success}
    </div>
  {/if}
</div>

<style>
  .form-input-wrapper {
    @apply w-full;
  }

  .form-input-label {
    @apply block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1;
  }

  .form-input-label.required {
    @apply after:content-['*'] after:ml-1 after:text-red-500;
  }

  .required-indicator {
    @apply text-red-500 ml-1;
  }

  .form-input-helper {
    @apply mt-1 text-xs text-gray-500 dark:text-gray-400;
  }

  .form-input-error {
    @apply mt-1 text-xs text-red-600 dark:text-red-400;
  }

  .error-message {
    @apply flex items-center;
  }

  .error-message:before {
    content: '⚠️';
    @apply mr-1;
  }

  .form-input-success {
    @apply mt-1 text-xs text-green-600 dark:text-green-400;
  }

  .form-input-success:before {
    content: '✅';
    @apply mr-1;
  }

  .has-error :global(.input-base) {
    @apply border-red-500 focus:border-red-500 focus:ring-red-500;
  }
</style>