<!--
  FieldInput Component - TASK-UI-002
  Full-featured input component with icons, clear button, password toggle
  
  Responsibilities:
  - All FormInput functionality
  - Icon support (left/right positioning)
  - Clear button functionality
  - Password visibility toggle
  - Loading states with spinner
  - Copy/paste actions
  - Debounced input events
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import FormInput from './FormInput.svelte';
  import { colors } from '$lib/design-system/tokens';
  import type { 
    FieldInputProps, 
    EnhancedInputEvents,
    IconPosition,
    ValidationRule,
    ValidationResult,
    InputState
  } from '../atoms/BaseInput.types';

  // FormInput props (pass-through)
  export let label: FieldInputProps['label'] = undefined;
  export let helperText: FieldInputProps['helperText'] = undefined;
  export let error: FieldInputProps['error'] = undefined;
  export let success: FieldInputProps['success'] = undefined;
  export let validationRules: ValidationRule[] = [];
  export let validateOnBlur = true;
  export let validateOnInput = false;
  export let formName: FieldInputProps['formName'] = undefined;
  export let fieldName: FieldInputProps['fieldName'] = undefined;

  // BaseInput props (pass-through)
  export let type: FieldInputProps['type'] = 'text';
  export let value: FieldInputProps['value'] = '';
  export let placeholder: FieldInputProps['placeholder'] = '';
  export let disabled: FieldInputProps['disabled'] = false;
  export let readonly: FieldInputProps['readonly'] = false;
  export let required: FieldInputProps['required'] = false;
  export let size: FieldInputProps['size'] = 'md';
  export let variant: FieldInputProps['variant'] = 'default';
  export let fullWidth: FieldInputProps['fullWidth'] = false;
  export let id: FieldInputProps['id'] = undefined;
  export let name: FieldInputProps['name'] = undefined;
  export let autocomplete: FieldInputProps['autocomplete'] = undefined;
  // ACCESSIBILITY: Removed autofocus prop - violates WCAG 2.4.3 Focus Order  
  // Use focus() method programmatically instead when needed
  export let minLength: FieldInputProps['minLength'] = undefined;
  export let maxLength: FieldInputProps['maxLength'] = undefined;
  export let min: FieldInputProps['min'] = undefined;
  export let max: FieldInputProps['max'] = undefined;
  export let step: FieldInputProps['step'] = undefined;
  export let pattern: FieldInputProps['pattern'] = undefined;
  export let ariaLabel: FieldInputProps['ariaLabel'] = undefined;
  export let testId: FieldInputProps['testId'] = undefined;
  export let className: FieldInputProps['className'] = '';

  // Enhanced FieldInput features
  export let leftIcon: string | undefined = undefined;
  export let rightIcon: string | undefined = undefined;
  export let iconPosition: IconPosition = 'left';
  export let clearable = false;
  export let showPasswordToggle = false;
  export let loading = false;
  export let debounceMs = 0;
  export let copyable = false;
  export let pasteAction: (() => void) | undefined = undefined;

  // Enhanced event dispatcher
  const dispatch = createEventDispatcher<EnhancedInputEvents>();

  // Internal state
  let isPasswordVisible = false;
  let debounceTimeout: NodeJS.Timeout;
  let formInputRef: FormInput;

  // Computed properties
  $: actualType = type === 'password' && isPasswordVisible ? 'text' : type;
  $: shouldShowPasswordToggle = showPasswordToggle && type === 'password';
  $: shouldShowClearButton = clearable && value && !disabled && !readonly;
  $: hasLeftIcon = leftIcon && iconPosition === 'left';
  $: hasRightIcon = rightIcon && iconPosition === 'right';
  $: hasAnyRightElement = hasRightIcon || shouldShowPasswordToggle || shouldShowClearButton || loading || copyable;

  // Icon size mapping based on input size
  const iconSizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5', 
    lg: 'h-6 w-6'
  };

  // Utility functions
  function debounce(func: Function, delay: number) {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(func, delay);
  }

  function renderIcon(iconName: string, classes: string = '') {
    // Simplified icon renderer - integrate with your icon system
    const iconMap: Record<string, string> = {
      search: '🔍',
      email: '📧',
      password: '🔒',
      user: '👤',
      phone: '📞',
      url: '🌐',
      calendar: '📅',
      time: '⏰',
      clear: '❌',
      copy: '📋',
      paste: '📥',
      show: '👁️',
      hide: '🙈'
    };
    
    return iconMap[iconName] || '⚡';
  }

  // Event handlers
  function handleInput(event: Event) {
    if (debounceMs > 0) {
      debounce(() => {
        dispatch('debounceInput', { value });
      }, debounceMs);
    }
    
    dispatch('input', event);
  }

  function handleChange(event: Event) {
    dispatch('change', event);
  }

  function handleFocus(event: FocusEvent) {
    dispatch('focus', event);
  }

  function handleBlur(event: FocusEvent) {
    dispatch('blur', event);
  }

  function handleKeydown(event: KeyboardEvent) {
    // Handle keyboard shortcuts
    if (event.key === 'Escape' && shouldShowClearButton) {
      handleClear();
    }
    
    dispatch('keydown', event);
  }

  function handleKeyup(event: KeyboardEvent) {
    dispatch('keyup', event);
  }

  function handleValidate(event: CustomEvent<ValidationResult>) {
    dispatch('validate', event.detail);
  }

  function handleStateChange(event: CustomEvent<InputState>) {
    // Forward state changes from FormInput
  }

  // Enhanced action handlers
  function handleClear() {
    value = '';
    dispatch('clear', new Event('clear'));
    
    // Focus input after clearing
    const inputElement = document.getElementById(id || '');
    if (inputElement) {
      inputElement.focus();
    }
  }

  function handlePasswordToggle() {
    isPasswordVisible = !isPasswordVisible;
    dispatch('togglePassword', new Event('togglePassword'));
  }

  function handleIconClick(position: IconPosition, event: MouseEvent) {
    dispatch('iconClick', { position, event });
  }

  function handleCopy() {
    if (copyable && value) {
      navigator.clipboard.writeText(String(value)).then(() => {
        dispatch('copy', { value: String(value) });
      });
    }
  }

  function handlePaste() {
    if (pasteAction) {
      pasteAction();
    } else {
      navigator.clipboard.readText().then((text) => {
        value = text;
        dispatch('paste', { value: text });
      });
    }
  }

  // Public API
  export function validate() {
    return formInputRef?.validate();
  }

  export function reset() {
    formInputRef?.reset();
    isPasswordVisible = false;
  }

  export function getState() {
    return formInputRef?.getState();
  }

  export function focus() {
    const inputElement = document.getElementById(id || '');
    if (inputElement) {
      inputElement.focus();
    }
  }

  export function clear() {
    handleClear();
  }
</script>

<div class="field-input-wrapper {className}">
  <div class="field-input-container" class:has-left-icon={hasLeftIcon} class:has-right-elements={hasAnyRightElement}>
    
    <!-- Left Icon -->
    {#if hasLeftIcon}
      <div 
        class="field-input-icon field-input-icon-left {iconSizeClasses[size]}"
        on:click={(e) => handleIconClick('left', e)}
        on:keydown={(e) => e.key === 'Enter' && handleIconClick('left', e)}
        role="button"
        tabindex="0"
        aria-label="Left icon"
      >
        <span class="icon-content">
          {renderIcon(leftIcon, iconSizeClasses[size])}
        </span>
      </div>
    {/if}

    <!-- FormInput (core functionality) -->
    <FormInput
      bind:this={formInputRef}
      {label}
      {helperText}
      {error}
      {success}
      {validationRules}
      {validateOnBlur}
      {validateOnInput}
      {formName}
      {fieldName}
      type={actualType}
      {value}
      {placeholder}
      {disabled}
      {readonly}
      {required}
      {size}
      {variant}
      {fullWidth}
      {id}
      {name}
      {autocomplete}
      {minLength}
      {maxLength}
      {min}
      {max}
      {step}
      {pattern}
      {ariaLabel}
      {testId}
      className="field-input-base"
      on:input={handleInput}
      on:change={handleChange}
      on:focus={handleFocus}
      on:blur={handleBlur}
      on:keydown={handleKeydown}
      on:keyup={handleKeyup}
      on:validate={handleValidate}
      on:stateChange={handleStateChange}
    />

    <!-- Right Elements Container -->
    {#if hasAnyRightElement}
      <div class="field-input-right-elements">
        
        <!-- Loading Spinner -->
        {#if loading}
          <div class="field-input-spinner {iconSizeClasses[size]}" aria-label="Loading">
            <svg class="animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        {/if}

        <!-- Copy Button -->
        {#if copyable && value && !loading}
          <button
            type="button"
            class="field-input-action {iconSizeClasses[size]}"
            on:click={handleCopy}
            aria-label="Copy value"
            disabled={disabled}
          >
            {renderIcon('copy', iconSizeClasses[size])}
          </button>
        {/if}

        <!-- Paste Button -->
        {#if pasteAction && !loading && !readonly}
          <button
            type="button"
            class="field-input-action {iconSizeClasses[size]}"
            on:click={handlePaste}
            aria-label="Paste value"
            disabled={disabled}
          >
            {renderIcon('paste', iconSizeClasses[size])}
          </button>
        {/if}

        <!-- Clear Button -->
        {#if shouldShowClearButton && !loading}
          <button
            type="button"
            class="field-input-action {iconSizeClasses[size]}"
            on:click={handleClear}
            aria-label="Clear input"
          >
            {renderIcon('clear', iconSizeClasses[size])}
          </button>
        {/if}

        <!-- Password Toggle -->
        {#if shouldShowPasswordToggle && !loading}
          <button
            type="button"
            class="field-input-action {iconSizeClasses[size]}"
            on:click={handlePasswordToggle}
            aria-label={isPasswordVisible ? 'Hide password' : 'Show password'}
          >
            {renderIcon(isPasswordVisible ? 'hide' : 'show', iconSizeClasses[size])}
          </button>
        {/if}

        <!-- Right Icon -->
        {#if hasRightIcon && !loading}
          <div 
            class="field-input-icon field-input-icon-right {iconSizeClasses[size]}"
            on:click={(e) => handleIconClick('right', e)}
            on:keydown={(e) => e.key === 'Enter' && handleIconClick('right', e)}
            role="button"
            tabindex="0"
            aria-label="Right icon"
          >
            <span class="icon-content">
              {renderIcon(rightIcon, iconSizeClasses[size])}
            </span>
          </div>
        {/if}

      </div>
    {/if}

  </div>
</div>

<style>
  .field-input-wrapper {
    @apply relative w-full;
  }

  .field-input-container {
    @apply relative;
  }

  .field-input-container.has-left-icon :global(.field-input-base input) {
    @apply pl-10;
  }

  .field-input-container.has-right-elements :global(.field-input-base input) {
    @apply pr-12;
  }

  .field-input-icon {
    @apply absolute top-1/2 transform -translate-y-1/2 cursor-pointer;
    @apply transition-colors;
    @apply flex items-center justify-center;
    color: theme('colors.secondary.400');
  }
  
  .field-input-icon:hover,
  .field-input-icon:focus {
    color: theme('colors.secondary.600');
  }

  .field-input-icon-left {
    @apply left-3;
  }

  .field-input-icon-right {
    @apply right-3;
  }

  .field-input-right-elements {
    @apply absolute right-2 top-1/2 transform -translate-y-1/2;
    @apply flex items-center space-x-1;
  }

  .field-input-action {
    @apply p-1 rounded transition-colors;
    @apply focus:outline-none focus:ring-2 focus:ring-opacity-50;
    @apply disabled:opacity-50 disabled:cursor-not-allowed;
    color: theme('colors.secondary.400');
  }
  
  .field-input-action:hover {
    color: theme('colors.secondary.600');
  }
  
  .field-input-action:focus {
    --tw-ring-color: theme('colors.primary.500');
  }

  .field-input-spinner {
    color: theme('colors.secondary.400');
  }

  .icon-content {
    @apply text-lg leading-none;
  }

  /* Adjust input padding when multiple right elements present */
  .field-input-container.has-right-elements :global(.field-input-base input) {
    @apply pr-16;
  }

  /* Focus states for icon buttons */
  .field-input-icon:focus {
    @apply outline-none ring-2 ring-opacity-50 rounded;
    --tw-ring-color: theme('colors.primary.500');
  }

  /* Loading state adjustments */
  .field-input-container:has(.field-input-spinner) :global(.field-input-base input) {
    @apply pr-12;
  }
</style>