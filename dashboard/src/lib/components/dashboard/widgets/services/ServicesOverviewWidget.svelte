<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Container, Play, Square, AlertTriangle, Plus } from 'lucide-svelte';
  import Widget from '../base/Widget.svelte';
  
  export let data: {
    total: number;
    running: number;
    stopped: number;
    error: number;
  } | null = null;
  export let loading: boolean = false;
  export let error: string = '';

  const dispatch = createEventDispatcher<{
    refresh: void;
    viewAll: void;
    deployNew: void;
  }>();

  $: healthPercentage = data ? Math.round((data.running / data.total) * 100) || 0 : 0;
</script>

<Widget
  title="Services Overview"
  subtitle="{data?.total || 0} services configured"
  {loading}
  {error}
  refreshable={true}
  size="medium"
  on:refresh={() => dispatch('refresh')}
>
  {#if data}
    <div class="services-overview">
      <!-- Health Ring -->
      <div class="health-ring-container">
        <div class="health-ring">
          <svg class="health-ring-svg" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="currentColor"
              stroke-width="8"
              class="health-ring-bg"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="currentColor"
              stroke-width="8"
              stroke-linecap="round"
              class="health-ring-progress"
              style="stroke-dasharray: {(healthPercentage / 100) * 251.3} 251.3"
            />
          </svg>
          <div class="health-ring-content">
            <div class="health-percentage">{healthPercentage}%</div>
            <div class="health-label">Healthy</div>
          </div>
        </div>
      </div>

      <!-- Service Stats -->
      <div class="service-stats">
        <div class="stat-item running">
          <div class="stat-icon">
            <Play class="h-4 w-4" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{data.running}</div>
            <div class="stat-label">Running</div>
          </div>
        </div>

        <div class="stat-item stopped">
          <div class="stat-icon">
            <Square class="h-4 w-4" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{data.stopped}</div>
            <div class="stat-label">Stopped</div>
          </div>
        </div>

        {#if data.error > 0}
          <div class="stat-item error">
            <div class="stat-icon">
              <AlertTriangle class="h-4 w-4" />
            </div>
            <div class="stat-content">
              <div class="stat-value">{data.error}</div>
              <div class="stat-label">Error</div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Quick Actions -->
      <div class="quick-actions">
        <button
          type="button"
          class="action-btn primary"
          on:click={() => dispatch('deployNew')}
        >
          <Plus class="h-4 w-4" />
          Deploy Service
        </button>
        
        <button
          type="button"
          class="action-btn secondary"
          on:click={() => dispatch('viewAll')}
        >
          <Container class="h-4 w-4" />
          View All
        </button>
      </div>
    </div>
  {/if}
</Widget>

<style>
  .services-overview {
    @apply space-y-6;
  }

  .health-ring-container {
    @apply flex justify-center;
  }

  .health-ring {
    @apply relative w-24 h-24;
  }

  .health-ring-svg {
    @apply w-full h-full transform -rotate-90;
  }

  .health-ring-bg {
    @apply text-gray-200 dark:text-gray-600;
  }

  .health-ring-progress {
    @apply text-green-500 transition-all duration-300;
    transform-origin: center;
  }

  .health-ring-content {
    @apply absolute inset-0 flex flex-col items-center justify-center;
  }

  .health-percentage {
    @apply text-lg font-bold text-gray-900 dark:text-white;
  }

  .health-label {
    @apply text-xs text-gray-500 dark:text-gray-400;
  }

  .service-stats {
    @apply grid grid-cols-2 gap-4;
  }

  .stat-item {
    @apply flex items-center space-x-3 p-3 rounded-lg;
  }

  .stat-item.running {
    @apply bg-green-50 dark:bg-green-900/20;
  }

  .stat-item.stopped {
    @apply bg-gray-50 dark:bg-gray-700;
  }

  .stat-item.error {
    @apply bg-red-50 dark:bg-red-900/20;
  }

  .stat-icon {
    @apply w-8 h-8 rounded-lg flex items-center justify-center text-white;
  }

  .stat-item.running .stat-icon {
    @apply bg-green-500;
  }

  .stat-item.stopped .stat-icon {
    @apply bg-gray-500;
  }

  .stat-item.error .stat-icon {
    @apply bg-red-500;
  }

  .stat-content {
    @apply flex-1 min-w-0;
  }

  .stat-value {
    @apply text-lg font-semibold text-gray-900 dark:text-white;
  }

  .stat-label {
    @apply text-sm text-gray-500 dark:text-gray-400;
  }

  .quick-actions {
    @apply grid grid-cols-2 gap-2;
  }

  .action-btn {
    @apply flex items-center justify-center space-x-2 px-3 py-2 rounded-md text-sm font-medium;
    @apply transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2;
  }

  .action-btn.primary {
    @apply bg-green-600 text-white hover:bg-green-700 focus:ring-green-500;
  }

  .action-btn.secondary {
    @apply bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500;
    @apply dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600;
  }
</style>