<!-- API Monitor Widget Header -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Activity, AlertTriangle } from 'lucide-svelte';

  export let hasIssues = false;
  export let isExpanded = false;

  const dispatch = createEventDispatcher<{
    toggleExpanded: void;
  }>();

  function handleToggleExpanded() {
    dispatch('toggleExpanded');
  }
</script>

<div class="widget-header">
  <div class="widget-title">
    <Activity class="w-5 h-5" />
    <h3>API Monitor</h3>
    {#if hasIssues}
      <AlertTriangle class="w-4 h-4 text-red-500" />
    {/if}
  </div>
  <div class="widget-actions">
    <button
      type="button"
      on:click={handleToggleExpanded}
      class="btn btn-sm"
      title="Toggle detailed view"
    >
      {isExpanded ? 'Collapse' : 'Expand'}
    </button>
  </div>
</div>

<style>
  .widget-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-bottom: 1px solid #e5e7eb;
  }

  .widget-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #1f2937;
  }

  .widget-title h3 {
    margin: 0;
    font-size: 1rem;
  }

  .widget-actions {
    display: flex;
    gap: 8px;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    font-size: 0.875rem;
    font-weight: 500;
    border-radius: 6px;
    transition: all 0.15s ease;
    cursor: pointer;
    border: 1px solid #d1d5db;
    background: white;
    color: #374151;
  }

  .btn:hover {
    background: #f9fafb;
    border-color: #9ca3af;
  }

  .btn:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
  }

  .btn-sm {
    padding: 6px 10px;
    font-size: 0.8125rem;
  }
</style>
