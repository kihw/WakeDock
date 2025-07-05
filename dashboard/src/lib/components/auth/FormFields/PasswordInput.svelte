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
  export let autocomplete: string = 'new-password';
  export let minlength: number = 8;
  export let showStrengthIndicator: boolean = false;
  export let strengthData: any = null;

  const dispatch = createEventDispatcher<{
    input: { value: string };
    blur: { value: string };
    focus: void;
    toggleVisibility: void;
  }>();

  let showPassword = false;

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

  function togglePasswordVisibility() {
    showPassword = !showPassword;
    dispatch('toggleVisibility');
  }

  $: hasValue = value && value.length > 0;
  $: isValid = hasValue && !error && (!strengthData || strengthData.isValid);
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
      type={showPassword ? 'text' : 'password'}
      {required}
      {disabled}
      {placeholder}
      {autocomplete}
      {minlength}
      {value}
      on:input={handleInput}
      on:blur={handleBlur}
      on:focus={handleFocus}
      class="relative block w-full appearance-none rounded-md border px-3 py-2 pr-10 text-gray-900 placeholder-gray-500 focus:z-10 focus:outline-none focus:ring-2 sm:text-sm
        {error
          ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
          : isValid
            ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
            : 'border-gray-300 focus:border-green-500 focus:ring-green-500'}"
      aria-describedby={error 
        ? `${id}-error` 
        : showStrengthIndicator && strengthData 
          ? `${id}-strength ${id}-help` 
          : `${id}-help`}
      aria-invalid={error ? 'true' : 'false'}
    />
    
    <!-- Toggle visibility button -->
    <button
      type="button"
      class="absolute inset-y-0 right-0 flex items-center pr-3 hover:text-gray-600 focus:outline-none focus:text-gray-600"
      on:click={togglePasswordVisibility}
      aria-label={showPassword ? 'Masquer le mot de passe' : 'Montrer le mot de passe'}
      tabindex="0"
    >
      <svg
        class="h-5 w-5 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        {#if showPassword}
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"
          />
        {:else}
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
        {/if}
      </svg>
    </button>
  </div>

  <!-- Password Strength Indicator -->
  {#if showStrengthIndicator && strengthData && hasValue}
    <div class="mt-2" id="{id}-strength">
      <div class="flex items-center space-x-2">
        <div class="flex-1 bg-gray-200 rounded-full h-2">
          <div
            class="h-2 rounded-full transition-all duration-300 {strengthData.score <= 1
              ? 'bg-red-500'
              : strengthData.score <= 2
                ? 'bg-yellow-500'
                : strengthData.score <= 3
                  ? 'bg-blue-500'
                  : 'bg-green-500'}"
            style="width: {(strengthData.score / 4) * 100}%"
          ></div>
        </div>
        <span
          class="text-xs font-medium {strengthData.score <= 1
            ? 'text-red-600'
            : strengthData.score <= 2
              ? 'text-yellow-600'
              : strengthData.score <= 3
                ? 'text-blue-600'
                : 'text-green-600'}"
        >
          {strengthData.score <= 1
            ? 'Faible'
            : strengthData.score <= 2
              ? 'Moyen'
              : strengthData.score <= 3
                ? 'Bon'
                : 'Excellent'}
        </span>
      </div>
      {#if strengthData.feedback && strengthData.feedback.length > 0}
        <ul class="mt-1 text-xs text-gray-600 space-y-1">
          {#each strengthData.feedback as feedback}
            <li class="flex items-center">
              <svg
                class="h-3 w-3 mr-1 text-red-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
              {feedback}
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  {/if}

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