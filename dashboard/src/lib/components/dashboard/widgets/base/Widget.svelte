<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Settings, Maximize2, RefreshCw } from 'lucide-svelte';

  export let title: string;
  export let subtitle: string = '';
  export let loading: boolean = false;
  export let error: string = '';
  export let refreshable: boolean = false;
  export let configurable: boolean = false;
  export let expandable: boolean = false;
  export let size: 'small' | 'medium' | 'large' = 'medium';

  const dispatch = createEventDispatcher<{
    refresh: void;
    configure: void;
    expand: void;
  }>();

  $: sizeClasses = {
    small: 'col-span-1 row-span-1',
    medium: 'col-span-2 row-span-1', 
    large: 'col-span-3 row-span-2'
  };
</script>

<div class="widget {sizeClasses[size]}">
  <!-- Widget Header -->
  <div class="widget-header">
    <div class="widget-title-section">
      <h3 class="widget-title">{title}</h3>
      {#if subtitle}
        <p class="widget-subtitle">{subtitle}</p>
      {/if}
    </div>
    
    <div class="widget-actions">
      {#if refreshable}
        <button
          type="button"
          class="widget-action-btn"
          on:click={() => dispatch('refresh')}
          disabled={loading}
          aria-label="Refresh widget"
        >
          <RefreshCw class="h-4 w-4 {loading ? 'animate-spin' : ''}" />
        </button>
      {/if}
      
      {#if expandable}
        <button
          type="button"
          class="widget-action-btn"
          on:click={() => dispatch('expand')}
          aria-label="Expand widget"
        >
          <Maximize2 class="h-4 w-4" />
        </button>
      {/if}
      
      {#if configurable}
        <button
          type="button"
          class="widget-action-btn"
          on:click={() => dispatch('configure')}
          aria-label="Configure widget"
        >
          <Settings class="h-4 w-4" />
        </button>
      {/if}
    </div>
  </div>

  <!-- Widget Content -->
  <div class="widget-content">
    {#if loading}
      <div class="widget-loading">
        <div class="loading-spinner">
          <RefreshCw class="h-6 w-6 animate-spin text-gray-400" />
        </div>
        <p class="loading-text">Loading...</p>
      </div>
    {:else if error}
      <div class="widget-error">
        <div class="error-icon">⚠️</div>
        <p class="error-message">{error}</p>
        {#if refreshable}
          <button
            type="button"
            class="error-retry-btn"
            on:click={() => dispatch('refresh')}
          >
            Retry
          </button>
        {/if}
      </div>
    {:else}
      <slot />
    {/if}
  </div>
</div>

<style>
  .widget {
    @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden;
    @apply flex flex-col;
    min-height: 200px;
  }

  .widget-header {
    @apply flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800;
  }

  .widget-title-section {
    @apply flex-1 min-w-0;
  }

  .widget-title {
    @apply text-sm font-medium text-gray-900 dark:text-white truncate;
  }

  .widget-subtitle {
    @apply text-xs text-gray-500 dark:text-gray-400 mt-0.5;
  }

  .widget-actions {
    @apply flex items-center space-x-1;
  }

  .widget-action-btn {
    @apply p-1.5 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300;
    @apply hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-200;
    @apply focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2;
  }

  .widget-action-btn:disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .widget-content {
    @apply flex-1 p-4 overflow-auto;
  }

  .widget-loading {
    @apply flex flex-col items-center justify-center h-full text-center py-8;
  }

  .loading-spinner {
    @apply mb-3;
  }

  .loading-text {
    @apply text-sm text-gray-500 dark:text-gray-400;
  }

  .widget-error {
    @apply flex flex-col items-center justify-center h-full text-center py-8;
  }

  .error-icon {
    @apply text-2xl mb-2;
  }

  .error-message {
    @apply text-sm text-red-600 dark:text-red-400 mb-4;
  }

  .error-retry-btn {
    @apply px-3 py-1.5 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200;
    @apply focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2;
    @apply transition-colors duration-200;
  }
</style>