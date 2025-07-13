<!--
  BaseInput Component - TASK-UI-002
  Atomic input component with minimal responsibilities (<150 lines)
  
  Responsibilities:
  - Render basic input element
  - Apply design tokens consistently  
  - Handle basic input types
  - Provide accessibility attributes
  - Dispatch input events
  
  Does NOT handle:
  - Labels, help text, or error messages
  - Icons or decorative elements
  - Complex validation logic
  - Loading states
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { variants } from '$lib/design-system/tokens';

  // Input types supported
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
    | 'color'
    | 'file'
    | 'range' = 'text';

  // Core props
  export let value: string | number = '';
  export let placeholder = '';
  export let disabled = false;
  export let readonly = false;
  export let required = false;

  // Sizing and variants
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let variant: 'default' | 'success' | 'warning' | 'error' = 'default';
  export let fullWidth = false;

  // HTML attributes
  export let id: string | undefined = undefined;
  export let name: string | undefined = undefined;
  export let autocomplete: string | undefined = undefined;
  // ACCESSIBILITY: Removed autofocus prop - violates WCAG 2.4.3 Focus Order  
  // Use focus() method programmatically instead when needed
  export let minLength: number | undefined = undefined;
  export let maxLength: number | undefined = undefined;
  export let min: number | string | undefined = undefined;
  export let max: number | string | undefined = undefined;
  export let step: number | string | undefined = undefined;
  export let pattern: string | undefined = undefined;

  // Accessibility
  export let ariaLabel: string | undefined = undefined;
  export let ariaDescribedBy: string | undefined = undefined;
  export let testId: string | undefined = undefined;

  // Custom styling
  export let className = '';

  // Event dispatcher
  const dispatch = createEventDispatcher<{
    input: Event;
    change: Event;
    focus: FocusEvent;
    blur: FocusEvent;
    keydown: KeyboardEvent;
    keyup: KeyboardEvent;
  }>();

  // Size classes using design tokens
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm', 
    lg: 'px-6 py-3 text-base'
  };

  // Base classes using design tokens
  const baseClasses = [
    'border rounded-md',
    'transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'placeholder:text-gray-400',
    'w-full' // Always full width of container
  ].join(' ');

  // Variant classes from design tokens
  $: variantClasses = variants.input[variant === 'default' ? 'base' : variant];

  // Computed classes
  $: computedClasses = [
    baseClasses,
    sizeClasses[size],
    variantClasses,
    fullWidth ? 'w-full' : '',
    className
  ].filter(Boolean).join(' ');

  // Event handlers
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    value = type === 'number' ? +target.value : target.value;
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
    dispatch('keydown', event);
  }

  function handleKeyup(event: KeyboardEvent) {
    dispatch('keyup', event);
  }
</script>

<input
  {id}
  {name}
  {type}
  {value}
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
  class={computedClasses}
  aria-label={ariaLabel}
  aria-describedby={ariaDescribedBy}
  data-testid={testId}
  on:input={handleInput}
  on:change={handleChange}
  on:focus={handleFocus}
  on:blur={handleBlur}
  on:keydown={handleKeydown}
  on:keyup={handleKeyup}
/>