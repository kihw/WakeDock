<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Play, Square, ExternalLink, MoreVertical } from 'lucide-svelte';
  import Widget from '../base/Widget.svelte';

  interface Service {
    id: string;
    name: string;
    status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
    subdomain: string;
    resource_usage?: {
      cpu_usage: number;
      memory_usage: number;
    };
  }

  export let services: Service[] = [];
  export let loading: boolean = false;
  export let error: string = '';

  const dispatch = createEventDispatcher<{
    refresh: void;
    start: { serviceId: string };
    stop: { serviceId: string };
    viewDetails: { serviceId: string };
  }>();

  $: runningServices = services.filter((s) => s.status === 'running').slice(0, 5);

  function getStatusColor(status: string): string {
    switch (status) {
      case 'running':
        return 'text-green-600';
      case 'stopped':
        return 'text-gray-600';
      case 'error':
        return 'text-red-600';
      case 'starting':
        return 'text-blue-600';
      case 'stopping':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  }

  function getStatusDotColor(status: string): string {
    switch (status) {
      case 'running':
        return 'bg-green-500';
      case 'stopped':
        return 'bg-gray-500';
      case 'error':
        return 'bg-red-500';
      case 'starting':
        return 'bg-blue-500';
      case 'stopping':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  }
</script>

<Widget
  title="Running Services"
  subtitle="{runningServices.length} active services"
  {loading}
  {error}
  refreshable={true}
  size="medium"
  on:refresh={() => dispatch('refresh')}
>
  {#if runningServices.length > 0}
    <div class="services-list">
      {#each runningServices as service (service.id)}
        <div class="service-item">
          <div class="service-info">
            <div class="service-header">
              <div class="service-status">
                <div class="status-dot {getStatusDotColor(service.status)}"></div>
                <span class="service-name">{service.name}</span>
              </div>
              <div class="service-actions">
                <a
                  href="https://{service.subdomain}"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="action-link"
                  title="Open service"
                >
                  <ExternalLink class="h-4 w-4" />
                </a>
                <button
                  type="button"
                  class="action-btn"
                  on:click={() => dispatch('viewDetails', { serviceId: service.id })}
                  title="More options"
                >
                  <MoreVertical class="h-4 w-4" />
                </button>
              </div>
            </div>

            <div class="service-details">
              <div class="service-url">{service.subdomain}</div>
              {#if service.resource_usage}
                <div class="resource-usage">
                  <span class="usage-item">
                    CPU: {(typeof service.resource_usage.cpu_usage === 'number'
                      ? service.resource_usage.cpu_usage
                      : 0
                    ).toFixed(1)}%
                  </span>
                  <span class="usage-item">
                    RAM: {(typeof service.resource_usage.memory_usage === 'number'
                      ? service.resource_usage.memory_usage
                      : 0
                    ).toFixed(1)}%
                  </span>
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>

    <!-- View All Link -->
    <div class="view-all">
      <a href="/services" class="view-all-link"> View all services → </a>
    </div>
  {:else}
    <div class="empty-state">
      <div class="empty-icon">
        <Play class="h-8 w-8 text-gray-400" />
      </div>
      <p class="empty-message">No running services</p>
      <a href="/services/new" class="empty-action"> Deploy your first service </a>
    </div>
  {/if}
</Widget>

<style>
  .services-list {
    @apply space-y-3;
  }

  .service-item {
    @apply border border-gray-200 dark:border-gray-600 rounded-lg p-3;
    @apply hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200;
  }

  .service-info {
    @apply space-y-2;
  }

  .service-header {
    @apply flex items-center justify-between;
  }

  .service-status {
    @apply flex items-center space-x-2;
  }

  .status-dot {
    @apply w-2 h-2 rounded-full;
  }

  .service-name {
    @apply text-sm font-medium text-gray-900 dark:text-white;
  }

  .service-actions {
    @apply flex items-center space-x-1;
  }

  .action-link,
  .action-btn {
    @apply p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300;
    @apply hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-200;
    @apply focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2;
  }

  .service-details {
    @apply text-xs text-gray-500 dark:text-gray-400 space-y-1;
  }

  .service-url {
    @apply font-mono;
  }

  .resource-usage {
    @apply flex items-center space-x-3;
  }

  .usage-item {
    @apply inline-flex;
  }

  .view-all {
    @apply mt-4 pt-3 border-t border-gray-200 dark:border-gray-600;
  }

  .view-all-link {
    @apply text-sm text-green-600 hover:text-green-700 font-medium;
  }

  .empty-state {
    @apply text-center py-8;
  }

  .empty-icon {
    @apply flex justify-center mb-3;
  }

  .empty-message {
    @apply text-sm text-gray-500 dark:text-gray-400 mb-4;
  }

  .empty-action {
    @apply inline-flex items-center px-3 py-2 text-sm font-medium;
    @apply text-green-600 bg-green-50 rounded-md hover:bg-green-100;
    @apply focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2;
    @apply transition-colors duration-200;
  }
</style>
