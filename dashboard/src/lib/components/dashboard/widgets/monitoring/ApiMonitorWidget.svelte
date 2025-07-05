<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { apiMonitor, type ApiMetrics } from '$lib/monitoring/api-monitor.js';
  import { Activity } from 'lucide-svelte';
  import ApiMonitorHeader from './api-monitor/ApiMonitorHeader.svelte';
  import ApiMetricsGrid from './api-monitor/ApiMetricsGrid.svelte';
  import CircuitBreakerStatus from './api-monitor/CircuitBreakerStatus.svelte';
  import ApiMonitorActions from './api-monitor/ApiMonitorActions.svelte';

  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let refreshInterval: number = 5000; // 5 seconds

  let metrics: ApiMetrics | null = null;
  let isExpanded = false;
  let refreshTimer: ReturnType<typeof setInterval> | null = null;

  const sizeClasses = {
    small: 'col-span-1 row-span-1',
    medium: 'col-span-2 row-span-1',
    large: 'col-span-3 row-span-2',
  };

  onMount(() => {
    updateMetrics();
    refreshTimer = setInterval(updateMetrics, refreshInterval);
  });

  onDestroy(() => {
    if (refreshTimer) {
      clearInterval(refreshTimer);
    }
  });

  function updateMetrics() {
    metrics = apiMonitor.getOverallMetrics();
  }

  function toggleExpanded() {
    isExpanded = !isExpanded;
  }

  function downloadReport() {
    const report = apiMonitor.generateReport();
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api-report-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function clearMetrics() {
    apiMonitor.clear();
    updateMetrics();
  }

  function getCircuitBreakerEntries(metrics: ApiMetrics) {
    return Object.entries(metrics.circuitBreakerStatus).map(([endpoint, status]) => ({
      endpoint,
      status: status as any,
    }));
  }

  $: errorRate =
    metrics && metrics.requestCount > 0 ? (metrics.errorCount / metrics.requestCount) * 100 : 0;
  $: circuitBreakerEntries = metrics ? getCircuitBreakerEntries(metrics) : [];
  $: circuitBreakerIssues = circuitBreakerEntries.filter((entry) => entry.status.isOpen);
  $: hasIssues =
    errorRate > 5 || circuitBreakerIssues.length > 0 || !metrics?.networkStatus.isOnline;
</script>

<div class="widget api-monitor-widget {sizeClasses[size]} {hasIssues ? 'has-issues' : ''}">
  <ApiMonitorHeader {hasIssues} {isExpanded} on:toggleExpanded={toggleExpanded} />

  <div class="widget-content">
    {#if metrics}
      <ApiMetricsGrid {metrics} />

      {#if isExpanded}
        <div class="expanded-content">
          <CircuitBreakerStatus {metrics} />
          <ApiMonitorActions on:downloadReport={downloadReport} on:clearMetrics={clearMetrics} />
        </div>
      {/if}
    {:else}
      <div class="no-data">
        <Activity class="w-8 h-8 text-gray-400" />
        <p>No API metrics available</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .api-monitor-widget {
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
    transition: all 0.2s ease;
  }

  .api-monitor-widget.has-issues {
    border-color: #fca5a5;
  }

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

  .widget-actions {
    display: flex;
    gap: 8px;
  }

  .widget-content {
    padding: 16px;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .metric {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-radius: 8px;
    background: #f9fafb;
    transition: background-color 0.2s ease;
  }

  .metric.error {
    background: #fef2f2;
  }

  .metric.slow {
    background: #fffbeb;
  }

  .metric.network-status {
    grid-column: span 2;
    justify-content: center;
  }

  .metric.network-status.offline {
    background: #fef2f2;
  }

  .metric-content {
    display: flex;
    flex-direction: column;
  }

  .metric-value {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
  }

  .metric-label {
    font-size: 14px;
    color: #6b7280;
  }

  .expanded-content {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .circuit-breakers {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .circuit-breaker {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px;
    border-radius: 4px;
    background: #f9fafb;
    font-size: 14px;
  }

  .circuit-breaker.open {
    background: #fef2f2;
  }

  .endpoint {
    font-family: monospace;
    color: #374151;
  }

  .status {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
  }

  .status.open {
    background: #fee2e2;
    color: #dc2626;
  }

  .status.closed {
    background: #d1fae5;
    color: #059669;
  }

  .failures {
    color: #6b7280;
  }

  .actions {
    display: flex;
    gap: 8px;
  }

  .btn {
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s ease;
    cursor: pointer;
  }

  .btn-sm {
    padding: 4px 8px;
    font-size: 12px;
  }

  .btn-outline {
    border: 1px solid #d1d5db;
    color: #374151;
    background: white;
  }

  .btn-outline:hover {
    background: #f9fafb;
  }

  .no-data {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 0;
    color: #9ca3af;
  }

  .no-data p {
    margin-top: 8px;
    font-size: 14px;
  }

  /* Dark mode styles */
  :global(.dark) .api-monitor-widget {
    background: #1f2937;
    border-color: #374151;
  }

  :global(.dark) .api-monitor-widget.has-issues {
    border-color: #dc2626;
  }

  :global(.dark) .widget-header {
    border-bottom-color: #374151;
  }

  :global(.dark) .widget-title {
    color: white;
  }

  :global(.dark) .metric {
    background: #374151;
  }

  :global(.dark) .metric.error {
    background: rgba(220, 38, 38, 0.2);
  }

  :global(.dark) .metric.slow {
    background: rgba(245, 158, 11, 0.2);
  }

  :global(.dark) .metric.network-status.offline {
    background: rgba(220, 38, 38, 0.2);
  }

  :global(.dark) .metric-value {
    color: white;
  }

  :global(.dark) .metric-label {
    color: #9ca3af;
  }

  :global(.dark) .circuit-breaker {
    background: #374151;
  }

  :global(.dark) .circuit-breaker.open {
    background: rgba(220, 38, 38, 0.2);
  }

  :global(.dark) .endpoint {
    color: #d1d5db;
  }

  :global(.dark) .status.open {
    background: rgba(220, 38, 38, 0.3);
    color: #fca5a5;
  }

  :global(.dark) .status.closed {
    background: rgba(5, 150, 105, 0.3);
    color: #6ee7b7;
  }

  :global(.dark) .failures {
    color: #9ca3af;
  }

  :global(.dark) .btn-outline {
    border-color: #6b7280;
    color: #d1d5db;
    background: #374151;
  }

  :global(.dark) .btn-outline:hover {
    background: #4b5563;
  }

  :global(.dark) .no-data {
    color: #6b7280;
  }
</style>
