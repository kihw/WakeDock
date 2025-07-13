<!-- API Monitor Metrics Grid -->
<script lang="ts">
  import { Wifi, WifiOff, TrendingUp, AlertTriangle, Clock } from 'lucide-svelte';
  import type { ApiMetrics } from '$lib/monitoring/api-monitor.js';

  export let metrics: ApiMetrics;

  $: errorRate = metrics.requestCount > 0 ? (metrics.errorCount / metrics.requestCount) * 100 : 0;
</script>

<div class="metrics-grid">
  <!-- Network Status -->
  <div class="metric network-status" class:offline={!metrics.networkStatus.isOnline}>
    {#if metrics.networkStatus.isOnline}
      <Wifi class="w-5 h-5 text-green-500" />
      <span class="metric-label">Online</span>
    {:else}
      <WifiOff class="w-5 h-5 text-red-500" />
      <span class="metric-label">Offline</span>
    {/if}
  </div>

  <!-- Request Count -->
  <div class="metric">
    <TrendingUp class="w-4 h-4 text-blue-500" />
    <div class="metric-content">
      <span class="metric-value">{metrics.requestCount}</span>
      <span class="metric-label">Requests</span>
    </div>
  </div>

  <!-- Error Rate -->
  <div class="metric" class:error={errorRate > 5}>
    <AlertTriangle class="w-4 h-4 {errorRate > 5 ? 'text-red-500' : 'text-gray-400'}" />
    <div class="metric-content">
      <span class="metric-value">{(typeof errorRate === 'number' ? errorRate : 0).toFixed(1)}%</span
      >
      <span class="metric-label">Error Rate</span>
    </div>
  </div>

  <!-- Response Time -->
  <div class="metric" class:slow={metrics.averageResponseTime > 2000}>
    <Clock
      class="w-4 h-4 {metrics.averageResponseTime > 2000 ? 'text-yellow-500' : 'text-gray-400'}"
    />
    <div class="metric-content">
      <span class="metric-value"
        >{(typeof metrics.averageResponseTime === 'number'
          ? metrics.averageResponseTime
          : 0
        ).toFixed(0)}ms</span
      >
      <span class="metric-label">Avg Response</span>
    </div>
  </div>
</div>

<style>
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
    gap: 2px;
  }

  .metric-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
  }

  .metric-label {
    font-size: 0.875rem;
    color: #6b7280;
  }
</style>
