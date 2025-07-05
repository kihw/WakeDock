<!-- API Monitor Actions -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher<{
    downloadReport: void;
    clearMetrics: void;
  }>();

  function handleDownloadReport() {
    dispatch('downloadReport');
  }

  function handleClearMetrics() {
    dispatch('clearMetrics');
  }
</script>

<div class="section">
  <h4 class="section-title">Actions</h4>
  <div class="actions">
    <button type="button" on:click={handleDownloadReport} class="btn btn-sm btn-outline">
      Download Report
    </button>
    <button type="button" on:click={handleClearMetrics} class="btn btn-sm btn-outline">
      Clear Metrics
    </button>
  </div>
</div>

<style>
  .section {
    margin-bottom: 24px;
  }

  .section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 12px;
  }

  .actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
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
    border: none;
    text-decoration: none;
  }

  .btn:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
  }

  .btn-sm {
    padding: 6px 10px;
    font-size: 0.8125rem;
  }

  .btn-outline {
    background: white;
    border: 1px solid #d1d5db;
    color: #374151;
  }

  .btn-outline:hover {
    background: #f9fafb;
    border-color: #9ca3af;
  }

  .btn-outline:active {
    background: #f3f4f6;
  }
</style>
