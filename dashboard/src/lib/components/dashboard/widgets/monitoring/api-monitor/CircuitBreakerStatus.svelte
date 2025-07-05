<!-- Circuit Breaker Status Display -->
<script lang="ts">
  import type { ApiMetrics } from '$lib/monitoring/api-monitor.js';

  export let metrics: ApiMetrics;

  function getCircuitBreakerEntries(metrics: ApiMetrics) {
    return Object.entries(metrics.circuitBreakerStatus).map(([endpoint, status]) => ({
      endpoint,
      status: status as any,
    }));
  }

  $: circuitBreakerEntries = getCircuitBreakerEntries(metrics);
  $: hasCircuitBreakers = circuitBreakerEntries.length > 0;
</script>

{#if hasCircuitBreakers}
  <div class="section">
    <h4 class="section-title">Circuit Breakers</h4>
    <div class="circuit-breakers">
      {#each circuitBreakerEntries as entry}
        <div class="circuit-breaker" class:open={entry.status.isOpen}>
          <span class="endpoint">{entry.endpoint}</span>
          <span class="status {entry.status.isOpen ? 'open' : 'closed'}">
            {entry.status.isOpen ? 'OPEN' : 'CLOSED'}
          </span>
          <span class="failures">{entry.status.failures} failures</span>
        </div>
      {/each}
    </div>
  </div>
{/if}

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

  .circuit-breakers {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .circuit-breaker {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    border-radius: 8px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    transition: all 0.2s ease;
  }

  .circuit-breaker.open {
    background: #fef2f2;
    border-color: #fca5a5;
  }

  .endpoint {
    font-family: monospace;
    font-size: 0.875rem;
    color: #374151;
    flex: 1;
  }

  .status {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
  }

  .status.open {
    background: #fca5a5;
    color: #991b1b;
  }

  .status.closed {
    background: #bbf7d0;
    color: #166534;
  }

  .failures {
    font-size: 0.75rem;
    color: #6b7280;
    margin-left: 8px;
  }
</style>
