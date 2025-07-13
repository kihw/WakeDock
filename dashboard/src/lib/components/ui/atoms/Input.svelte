<!--
  Enhanced Input Component - Atomic Design System
  Supports all input types, validation states, and accessibility features with design tokens
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { scale, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { variants, accessibleColors, accessibilityTokens } from '$lib/design-system/tokens';
  import { accessibilityUtils } from '$lib/design-system/accessibility';

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
    | 'week' = 'text';
  export let value: string | number = '';
  export let placeholder = '';
  export let disabled = false;
  export let readonly = false;
  export let required = false;
  export let autocomplete: string | undefined = undefined;
  // ACCESSIBILITY: Removed autofocus prop - violates WCAG 2.4.3 Focus Order
  // Use focus() method programmatically instead when needed
  export let id: string | undefined = undefined;
  export let name: string | undefined = undefined;
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let variant: 'default' | 'success' | 'warning' | 'error' = 'default';
  export let fullWidth = false;
  export let rounded = false;
  export let label: string | undefined = undefined;
  export let helperText: string | undefined = undefined;
  export let errorText: string | undefined = undefined;
  export let successText: string | undefined = undefined;
  export let leftIcon: string | undefined = undefined;
  export let rightIcon: string | undefined = undefined;
  export let clearable = false;
  export let showPasswordToggle = false;
  export let loading = false;
  export let debounceMs = 0;
  export let minLength: number | undefined = undefined;
  export let maxLength: number | undefined = undefined;
  export let min: number | string | undefined = undefined;
  export let max: number | string | undefined = undefined;
  export let step: number | string | undefined = undefined;
  export let pattern: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let ariaDescribedBy: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  // Events
  const dispatch = createEventDispatcher<{
    input: { value: string | number; event: Event };
    change: { value: string | number; event: Event };
    focus: FocusEvent;
    blur: FocusEvent;
    keydown: KeyboardEvent;
    keyup: KeyboardEvent;
    clear: void;
    togglePassword: boolean;
  }>();

  // State
  let isFocused = false;
  let isPasswordVisible = false;
  let inputElement: HTMLInputElement;
  let debounceTimer: ReturnType<typeof setTimeout>;

  // Computed
  $: hasError = variant === 'error' || !!errorText;
  $: hasSuccess = variant === 'success' || !!successText;
  $: hasWarning = variant === 'warning';
  $: hasLeftIcon = leftIcon || $$slots.leftIcon;
  $: hasRightIcon =
    rightIcon ||
    $$slots.rightIcon ||
    clearable ||
    (type === 'password' && showPasswordToggle) ||
    loading;
  // ACCESSIBILITY: Generate unique IDs if not provided
  $: componentId = id || accessibilityUtils.generateId('input');
  $: helperId = `${componentId}-helper`;
  $: errorId = `${componentId}-error`;
  $: successId = `${componentId}-success`;
  $: describedBy = accessibilityUtils.buildDescribedBy([
    ariaDescribedBy,
    helperText ? helperId : undefined,
    hasError && errorText ? errorId : undefined,
    hasSuccess && successText ? successId : undefined,
  ]);

  // Base classes using design tokens (Updated for WCAG compliance)
  const baseClasses = [
    'block w-full',
    'border',
    'transition-all duration-200 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:cursor-not-allowed disabled:bg-secondary-50 disabled:text-secondary-600',
    'placeholder-secondary-500', // Changed from 400 to 500 for better contrast (4.76:1)
    'text-secondary-800', // Excellent contrast (14.63:1)
  ];

  // Variant classes using design tokens
  const variantClasses = {
    default: {
      base: variants.input.base,
      bg: 'bg-white',
    },
    success: {
      base: variants.input.success,
      bg: 'bg-success-50',
    },
    warning: {
      base: variants.input.warning,
      bg: 'bg-warning-50',
    },
    error: {
      base: variants.input.error,
      bg: 'bg-error-50',
    },
  };

  // Size classes
  const sizeClasses = {
    sm: {
      input: 'px-3 py-1.5 text-sm',
      icon: 'w-4 h-4',
      button: 'p-1',
    },
    md: {
      input: 'px-4 py-2 text-sm',
      icon: 'w-5 h-5',
      button: 'p-1.5',
    },
    lg: {
      input: 'px-4 py-3 text-base',
      icon: 'w-6 h-6',
      button: 'p-2',
    },
  };

  // Build classes
  $: containerClasses = ['relative', fullWidth ? 'w-full' : ''].filter(Boolean).join(' ');

  $: inputClasses = [
    ...baseClasses,
    variantClasses[variant].base,
    disabled ? 'bg-secondary-50' : variantClasses[variant].bg,
    sizeClasses[size].input,
    rounded ? 'rounded-full' : 'rounded-md',
    hasLeftIcon ? 'pl-10' : '',
    hasRightIcon ? 'pr-10' : '',
  ]
    .filter(Boolean)
    .join(' ');

  $: labelClasses = [
    'block text-sm font-medium',
    hasError ? 'text-error-700' : hasSuccess ? 'text-success-700' : 'text-secondary-700',
    'mb-1',
  ]
    .filter(Boolean)
    .join(' ');

  // Event handlers
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    const newValue = type === 'number' ? Number(target.value) : target.value;

    // Clear previous debounce
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Set value immediately for reactive updates
    value = newValue;

    // Debounce dispatch if specified
    if (debounceMs > 0) {
      debounceTimer = setTimeout(() => {
        dispatch('input', { value: newValue, event });
      }, debounceMs);
    } else {
      dispatch('input', { value: newValue, event });
    }
  }

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const newValue = type === 'number' ? Number(target.value) : target.value;
    value = newValue;
    dispatch('change', { value: newValue, event });
  }

  function handleFocus(event: FocusEvent) {
    isFocused = true;
    dispatch('focus', event);
  }

  function handleBlur(event: FocusEvent) {
    isFocused = false;
    dispatch('blur', event);
  }

  function handleKeyDown(event: KeyboardEvent) {
    dispatch('keydown', event);
  }

  function handleKeyUp(event: KeyboardEvent) {
    dispatch('keyup', event);
  }

  function handleClear() {
    value = '';
    dispatch('clear');
    dispatch('input', { value: '', event: new Event('input') });
    inputElement?.focus();
  }

  function handleTogglePassword() {
    isPasswordVisible = !isPasswordVisible;
    dispatch('togglePassword', isPasswordVisible);
  }

  // Public methods
  export function focus() {
    inputElement?.focus();
  }

  export function blur() {
    inputElement?.blur();
  }

  export function select() {
    inputElement?.select();
  }

  export function setSelectionRange(start: number, end: number) {
    inputElement?.setSelectionRange(start, end);
  }
</script>

<div class={containerClasses}>
  {#if label}
    <label for={componentId} class={labelClasses}>
      {label}
      {#if required}
        <span class="text-error-500 ml-1">*</span>
      {/if}
    </label>
  {/if}

  <div class="relative">
    <!-- Left Icon -->
    {#if hasLeftIcon}
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        {#if leftIcon}
          <i class={`${leftIcon} ${sizeClasses[size].icon} text-secondary-400`} aria-hidden="true"></i>
        {:else}
          <slot name="leftIcon" />
        {/if}
      </div>
    {/if}

    <!-- Input -->
    {#if type === 'password'}
      {#if isPasswordVisible}
        <input
          bind:this={inputElement}
          bind:value
          type="text"
          id={componentId}
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
          class={inputClasses}
          aria-label={ariaLabel}
          aria-describedby={describedBy}
          aria-invalid={hasError}
          data-testid={testId}
          on:input={handleInput}
          on:change={handleChange}
          on:focus={handleFocus}
          on:blur={handleBlur}
          on:keydown={handleKeyDown}
          on:keyup={handleKeyUp}
        />
      {:else}
        <input
          bind:this={inputElement}
          bind:value
          type="password"
          id={componentId}
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
          class={inputClasses}
          aria-label={ariaLabel}
          aria-describedby={describedBy}
          aria-invalid={hasError}
          data-testid={testId}
          on:input={handleInput}
          on:change={handleChange}
          on:focus={handleFocus}
          on:blur={handleBlur}
          on:keydown={handleKeyDown}
          on:keyup={handleKeyUp}
        />
      {/if}
    {:else if type === 'text'}
      <input
        bind:this={inputElement}
        bind:value
        type="text"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {:else if type === 'email'}
      <input
        bind:this={inputElement}
        bind:value
        type="email"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {:else if type === 'number'}
      <input
        bind:this={inputElement}
        bind:value
        type="number"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {:else if type === 'tel'}
      <input
        bind:this={inputElement}
        bind:value
        type="tel"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {:else if type === 'url'}
      <input
        bind:this={inputElement}
        bind:value
        type="url"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {:else if type === 'search'}
      <input
        bind:this={inputElement}
        bind:value
        type="search"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {:else if type === 'date'}
      <input
        bind:this={inputElement}
        bind:value
        type="date"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {:else if type === 'time'}
      <input
        bind:this={inputElement}
        bind:value
        type="time"
        {id}
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
        class={inputClasses}
        aria-label={ariaLabel}
        aria-describedby={describedBy}
        data-testid={testId}
        on:input={handleInput}
        on:change={handleChange}
        on:focus={handleFocus}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        on:keyup={handleKeyUp}
      />
    {/if}

    <!-- Right Icons/Buttons -->
    {#if hasRightIcon}
      <div class="absolute inset-y-0 right-0 pr-3 flex items-center space-x-1">
        {#if loading}
          <div class="animate-spin">
            <svg
              class={`${sizeClasses[size].icon} text-secondary-400`}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          </div>
        {/if}

        {#if type === 'password' && showPasswordToggle}
          <button
            type="button"
            class={`${sizeClasses[size].button} text-secondary-400 hover:text-secondary-600 focus:outline-none focus:text-secondary-600`}
            on:click={handleTogglePassword}
            aria-label={isPasswordVisible ? 'Hide password' : 'Show password'}
          >
            {#if isPasswordVisible}
              <svg
                class={sizeClasses[size].icon}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"
                />
              </svg>
            {:else}
              <svg
                class={sizeClasses[size].icon}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
            {/if}
          </button>
        {/if}

        {#if clearable && value !== ''}
          <button
            type="button"
            class={`${sizeClasses[size].button} text-secondary-400 hover:text-secondary-600 focus:outline-none focus:text-secondary-600`}
            on:click={handleClear}
            aria-label="Clear input"
          >
            <svg
              class={sizeClasses[size].icon}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        {/if}

        {#if rightIcon}
          <i class={`${rightIcon} ${sizeClasses[size].icon} text-secondary-400`} aria-hidden="true"></i>
        {:else if $$slots.rightIcon}
          <slot name="rightIcon" />
        {/if}
      </div>
    {/if}
  </div>

  <!-- Helper/Error/Success Text -->
  {#if helperText || errorText || successText}
    <div class="mt-1 text-sm">
      {#if hasError && errorText}
        <p class="text-error-600" id={errorId}>
          {errorText}
        </p>
      {:else if hasSuccess && successText}
        <p class="text-success-600" id={successId}>
          {successText}
        </p>
      {:else if helperText}
        <p class="text-secondary-600" id={helperId}>
          {helperText}
        </p>
      {/if}
    </div>
  {/if}
</div>

<style>
  /* Custom focus styles */
  input:focus {
    box-shadow: 0 0 0 1px currentColor;
  }

  /* Remove default browser styles */
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  input[type='number'] {
    -moz-appearance: textfield;
  }

  input::-webkit-search-decoration,
  input::-webkit-search-cancel-button,
  input::-webkit-search-results-button,
  input::-webkit-search-results-decoration {
    -webkit-appearance: none;
  }
</style>
