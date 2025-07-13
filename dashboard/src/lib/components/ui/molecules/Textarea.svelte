<!-- Textarea Field Component -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { sanitizeInput } from '$lib/utils/validation';
  import { announceToScreenReader } from '$lib/utils/accessibility';
  import { variants } from '$lib/design-system/tokens';

  export let label: string;
  export let id: string = '';
  export let value: string = '';
  export let placeholder: string = '';
  export let required: boolean = false;
  export let disabled: boolean = false;
  export let readonly: boolean = false;
  export let error: string = '';
  export let help: string = '';
  export let rows: number = 4;
  export let maxlength: number | undefined = undefined;
  export let minlength: number | undefined = undefined;
  export let resize: 'none' | 'vertical' | 'horizontal' | 'both' = 'vertical';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let autocomplete: string = '';
  export let spellcheck: boolean = true;
  export let autoSanitize: boolean = true;

  const dispatch = createEventDispatcher<{
    input: { value: string };
    change: { value: string };
    focus: void;
    blur: void;
  }>();

  // Textarea sizing classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  // Resize classes
  const resizeClasses = {
    none: 'resize-none',
    vertical: 'resize-y',
    horizontal: 'resize-x',
    both: 'resize',
  };

  // Generate unique IDs for accessibility
  const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
  const helpId = `${textareaId}-help`;
  const errorId = `${textareaId}-error`;
  const counterId = `${textareaId}-counter`;

  // Character count for accessibility
  $: characterCount = value.length;
  $: characterLimit = maxlength;
  $: remainingChars = characterLimit ? characterLimit - characterCount : null;

  // Handle input event with security and accessibility
  const handleInput = (event: Event) => {
    const target = event.target as HTMLTextAreaElement;
    let newValue = target.value;

    // Auto-sanitize if enabled
    if (autoSanitize) {
      newValue = sanitizeInput(newValue);
    }

    value = newValue;

    // Dispatch input event
    dispatch('input', { value: newValue });

    // Announce character count changes for screen readers (but not too frequently)
    if (characterLimit && remainingChars !== null) {
      if (remainingChars === 0) {
        announceToScreenReader('Character limit reached');
      } else if (remainingChars < 10) {
        announceToScreenReader(`${remainingChars} characters remaining`);
      }
    }
  };

  const handleChange = (event: Event) => {
    const target = event.target as HTMLTextAreaElement;
    dispatch('change', { value: target.value });
  };

  const handleFocus = () => {
    dispatch('focus');
  };

  const handleBlur = () => {
    dispatch('blur');
  };
</script>

<div class="form-field">
  <label for={textareaId} class="block text-sm font-medium text-secondary-700 mb-1">
    {label}
    {#if required}
      <span class="text-error-500 ml-1">*</span>
    {/if}
  </label>

  <div class="relative">
    <textarea
      id={textareaId}
      {placeholder}
      {required}
      {disabled}
      {readonly}
      {rows}
      {maxlength}
      {minlength}
      {autocomplete}
      {spellcheck}
      class="block w-full {sizeClasses[size]} {resizeClasses[
        resize
      ]} border rounded-md shadow-sm focus:ring-2 focus:ring-offset-0 disabled:bg-secondary-100 disabled:cursor-not-allowed readonly:bg-secondary-50 transition-colors duration-200
      {error
        ? variants.input.error
        : variants.input.base}"
      bind:value
      on:input={handleInput}
      on:blur={handleBlur}
      on:focus={handleFocus}
      on:change={handleChange}
      on:keydown
      on:keyup
      on:keypress
      aria-describedby={[
        error ? errorId : null,
        help ? helpId : null,
        characterLimit ? counterId : null,
      ]
        .filter(Boolean)
        .join(' ') || undefined}
      aria-invalid={error ? 'true' : 'false'}
      aria-required={required}
    ></textarea>

    {#if error}
      <div class="absolute top-2 right-2 pointer-events-none">
        <svg
          class="h-5 w-5 text-error-500"
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path
            fill-rule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
            clip-rule="evenodd"
          />
        </svg>
      </div>
    {/if}
  </div>

  <!-- Character counter -->
  {#if characterLimit}
    <div id={counterId} class="mt-1 flex justify-between text-sm">
      <div></div>
      <div class="text-secondary-500" class:text-error-500={remainingChars !== null && remainingChars < 0}>
        {characterCount}
        {#if characterLimit}
          / {characterLimit}
        {/if}
        <span class="sr-only">characters used</span>
      </div>
    </div>
  {/if}

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
