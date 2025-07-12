<!-- Settings Page Header -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Save, RotateCcw } from 'lucide-svelte';
  import LoadingSpinner from '$lib/components/ui/atoms/LoadingSpinner.svelte';

  export let hasChanges = false;
  export let saving = false;

  const dispatch = createEventDispatcher<{
    save: void;
    reset: void;
  }>();

  function handleSave() {
    dispatch('save');
  }

  function handleReset() {
    dispatch('reset');
  }
</script>

<div class="settings-header">
  <div class="header-content">
    <h1 class="page-title">System Settings</h1>
    <p class="page-description">Configure WakeDock system settings and preferences</p>
  </div>

  <div class="header-actions">
    <button
      type="button"
      on:click={handleReset}
      disabled={!hasChanges || saving}
      class="btn btn-secondary"
      title="Reset to last saved values"
    >
      <RotateCcw class="btn-icon" />
      Reset
    </button>

    <button
      type="button"
      on:click={handleSave}
      disabled={!hasChanges || saving}
      class="btn btn-primary"
      title="Save all changes"
    >
      {#if saving}
        <LoadingSpinner size="sm" />
        <span>Saving...</span>
      {:else}
        <Save class="btn-icon" />
        <span>Save Changes</span>
      {/if}
    </button>
  </div>
</div>

{#if hasChanges}
  <div class="changes-indicator">
    <div class="indicator-content">
      <div class="indicator-icon">
        <div class="change-dot"></div>
      </div>
      <span class="indicator-text"> You have unsaved changes </span>
    </div>
  </div>
{/if}

<style>
  .settings-header {
    @apply flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-6;
  }

  .header-content {
    @apply flex-1;
  }

  .page-title {
    @apply text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2;
  }

  .page-description {
    @apply text-slate-600 dark:text-slate-400;
  }

  .header-actions {
    @apply flex items-center gap-3;
  }

  .btn {
    @apply flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2;
  }

  .btn-secondary {
    @apply bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600 focus:ring-slate-500;
  }

  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500;
  }

  .btn:disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .btn-icon {
    @apply w-4 h-4;
  }

  .changes-indicator {
    @apply mb-6 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg;
  }

  .indicator-content {
    @apply flex items-center gap-2;
  }

  .indicator-icon {
    @apply flex items-center justify-center;
  }

  .change-dot {
    @apply w-2 h-2 bg-amber-500 rounded-full animate-pulse;
  }

  .indicator-text {
    @apply text-sm text-amber-800 dark:text-amber-200 font-medium;
  }
</style>
