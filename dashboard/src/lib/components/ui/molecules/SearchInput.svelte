<!--
  SearchInput Molecule - Combines Input with search functionality
  Includes debouncing, clear button, and search suggestions with design tokens
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { fly, fade } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import Input from '../atoms/Input.svelte';
  import Button from '../atoms/Button.svelte';
  import LoadingSpinner from '../atoms/LoadingSpinner.svelte';
  import { colors } from '$lib/design-system/tokens';

  // Props
  export let value = '';
  export let placeholder = 'Search...';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let disabled = false;
  export let loading = false;
  export let debounceMs = 300;
  export let suggestions: string[] = [];
  export let showSuggestions = false;
  export let maxSuggestions = 5;
  export let clearable = true;
  export let searchOnEnter = false;
  // ACCESSIBILITY: Removed autoFocus prop - violates WCAG 2.4.3 Focus Order  
  // Use focus() method programmatically instead when needed
  export let fullWidth = false;
  export let variant: 'default' | 'success' | 'warning' | 'error' = 'default';
  export let testId: string | undefined = undefined;

  // Events
  const dispatch = createEventDispatcher<{
    search: { query: string };
    clear: void;
    select: { suggestion: string };
    input: { value: string };
    focus: FocusEvent;
    blur: FocusEvent;
  }>();

  // State
  let inputElement: HTMLInputElement;
  let showSuggestionsDropdown = false;
  let selectedSuggestionIndex = -1;
  let debounceTimer: ReturnType<typeof setTimeout>;
  let isFocused = false;

  // Optimized computed - cache lowercase value to avoid repeated computation
  $: lowerValue = value.toLowerCase();
  $: filteredSuggestions = lowerValue 
    ? suggestions
        .filter((s) => s.toLowerCase().includes(lowerValue))
        .slice(0, maxSuggestions)
    : [];
  $: shouldShowSuggestions =
    showSuggestions &&
    showSuggestionsDropdown &&
    filteredSuggestions.length > 0 &&
    value.length > 0;

  // Event handlers
  function handleInput(event: CustomEvent<{ value: string }>) {
    value = event.detail.value;
    dispatch('input', { value });

    // Reset suggestion selection
    selectedSuggestionIndex = -1;

    // Show suggestions if enabled
    if (showSuggestions && value.length > 0) {
      showSuggestionsDropdown = true;
    } else {
      showSuggestionsDropdown = false;
    }

    // Debounced search
    if (!searchOnEnter) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        if (value.trim()) {
          dispatch('search', { query: value.trim() });
        }
      }, debounceMs);
    }
  }

  function handleKeyDown(event: CustomEvent<KeyboardEvent>) {
    const key = event.detail.key;

    if (key === 'Enter') {
      event.detail.preventDefault();

      if (selectedSuggestionIndex >= 0 && filteredSuggestions[selectedSuggestionIndex]) {
        // Select suggestion
        selectSuggestion(filteredSuggestions[selectedSuggestionIndex]);
      } else if (value.trim()) {
        // Perform search
        dispatch('search', { query: value.trim() });
        showSuggestionsDropdown = false;
      }
    } else if (key === 'Escape') {
      showSuggestionsDropdown = false;
      selectedSuggestionIndex = -1;
      inputElement?.blur();
    } else if (key === 'ArrowDown') {
      event.detail.preventDefault();
      if (shouldShowSuggestions) {
        selectedSuggestionIndex = Math.min(
          selectedSuggestionIndex + 1,
          filteredSuggestions.length - 1
        );
      }
    } else if (key === 'ArrowUp') {
      event.detail.preventDefault();
      if (shouldShowSuggestions) {
        selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
      }
    }
  }

  function handleFocus(event: CustomEvent<FocusEvent>) {
    isFocused = true;

    // Show suggestions if there are any and value is not empty
    if (showSuggestions && value.length > 0 && filteredSuggestions.length > 0) {
      showSuggestionsDropdown = true;
    }

    dispatch('focus', event.detail);
  }

  function handleBlur(event: CustomEvent<FocusEvent>) {
    isFocused = false;

    // Delay hiding suggestions to allow for clicks
    setTimeout(() => {
      showSuggestionsDropdown = false;
      selectedSuggestionIndex = -1;
    }, 150);

    dispatch('blur', event.detail);
  }

  function handleClear() {
    value = '';
    showSuggestionsDropdown = false;
    selectedSuggestionIndex = -1;
    clearTimeout(debounceTimer);
    dispatch('clear');
    dispatch('input', { value: '' });
    inputElement?.focus();
  }

  function selectSuggestion(suggestion: string) {
    value = suggestion;
    showSuggestionsDropdown = false;
    selectedSuggestionIndex = -1;
    dispatch('select', { suggestion });
    dispatch('search', { query: suggestion });
  }

  function handleSuggestionClick(suggestion: string) {
    selectSuggestion(suggestion);
  }

  // Public methods
  export function focus() {
    inputElement?.focus();
  }

  export function blur() {
    inputElement?.blur();
  }

  export function clear() {
    handleClear();
  }
</script>

<div class="relative {fullWidth ? 'w-full' : ''}">
  <Input
    bind:this={inputElement}
    bind:value
    type="search"
    {placeholder}
    {size}
    {disabled}
    {variant}
    {fullWidth}
    {testId}
    leftIcon="fas fa-search"
    on:input={handleInput}
    on:keydown={handleKeyDown}
    on:focus={handleFocus}
    on:blur={handleBlur}
    on:clear={handleClear}
  >
    <svelte:fragment slot="rightIcon">
      {#if loading}
        <LoadingSpinner size="sm" type="spin" />
      {:else if clearable && value}
        <button
          type="button"
          class="p-1 text-secondary-400 hover:text-secondary-600 focus:outline-none focus:text-secondary-600"
          on:click={handleClear}
          aria-label="Clear search"
        >
          <svg
            class="w-4 h-4"
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
    </svelte:fragment>
  </Input>

  <!-- Suggestions dropdown -->
  {#if shouldShowSuggestions}
    <div
      class="absolute z-10 w-full mt-1 bg-white border border-secondary-300 rounded-md shadow-lg max-h-60 overflow-y-auto"
      in:fly={{ y: -5, duration: 150, easing: quintOut }}
      out:fade={{ duration: 100 }}
    >
      <ul class="py-1">
        {#each filteredSuggestions as suggestion, index}
          <li>
            <button
              type="button"
              class={`w-full text-left px-4 py-2 text-sm hover:bg-secondary-100 focus:bg-secondary-100 focus:outline-none ${
                index === selectedSuggestionIndex ? 'bg-primary-50 text-primary-600' : 'text-secondary-900'
              }`}
              on:click={() => handleSuggestionClick(suggestion)}
              on:mouseenter={() => (selectedSuggestionIndex = index)}
            >
              <div class="flex items-center">
                <svg
                  class="w-4 h-4 mr-2 text-secondary-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <span class="truncate">{suggestion}</span>
              </div>
            </button>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>

<style>
  /* Ensure suggestions dropdown appears above other content */
  :global(.z-10) {
    z-index: 10;
  }
</style>
