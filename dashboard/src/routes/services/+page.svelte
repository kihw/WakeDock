<!-- Services List Page -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { services, serviceStats, ui, isAuthenticated } from '$lib/stores';
  import { websocketClient as websocket } from '$lib/websocket';
  import type { Service } from '$lib/api';

  let searchTerm = '';
  let statusFilter = 'all';
  let filteredServices: Service[] = [];
  let autoRefresh = true;
  let refreshInterval: NodeJS.Timeout | null = null;

  // Optimize filtering with separate reactive statements to avoid unnecessary re-computations
  $: lowerSearchTerm = searchTerm.toLowerCase();
  $: filteredServices = $services.services?.filter((service) => {
    const matchesSearch = !searchTerm || 
      service.name.toLowerCase().includes(lowerSearchTerm) ||
      service.image.toLowerCase().includes(lowerSearchTerm);
    const matchesStatus = statusFilter === 'all' || service.status === statusFilter;
    return matchesSearch && matchesStatus;
  }) || [];

  onMount(() => {
    // Redirect if not authenticated
    if (!$isAuthenticated) {
      goto('/login');
      return;
    }

    // Load services and stats
    services.load();

    // Setup WebSocket for real-time updates
    websocket.connect();
    websocket.subscribe('service_status', (data) => {
      services.updateServiceStatus(data.serviceId, data.status);
    });

    // Setup auto-refresh
    startAutoRefresh();
  });

  onDestroy(() => {
    stopAutoRefresh();
    websocket.disconnect();
  });

  const startAutoRefresh = () => {
    if (autoRefresh && !refreshInterval) {
      refreshInterval = setInterval(() => {
        // Only refresh if page is visible to reduce unnecessary API calls
        if (!document.hidden) {
          services.load();
        }
      }, 30000); // Refresh every 30 seconds
    }
  };

  const stopAutoRefresh = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  };

  const toggleAutoRefresh = () => {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  };

  const handleServiceAction = async (serviceId: string, action: 'start' | 'stop' | 'restart') => {
    try {
      switch (action) {
        case 'start':
          await services.start(serviceId);
          ui.showSuccess('Service started', 'Service is starting up...');
          break;
        case 'stop':
          await services.stop(serviceId);
          ui.showSuccess('Service stopped', 'Service is shutting down...');
          break;
        case 'restart':
          await services.restart(serviceId);
          ui.showSuccess('Service restarting', 'Service is restarting...');
          break;
      }
    } catch (error) {
      ui.showError(`Failed to ${action} service`, (error as any).message);
    }
  };

  const handleDeleteService = async (serviceId: string, serviceName: string) => {
    const confirmed = confirm(`Are you sure you want to delete service "${serviceName}"?`);
    if (confirmed) {
      try {
        await services.delete(serviceId);
        ui.showSuccess('Service deleted', `Service "${serviceName}" has been deleted.`);
      } catch (error) {
        ui.showError('Failed to delete service', (error as any).message);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-600 bg-green-100';
      case 'stopped':
        return 'text-gray-600 bg-gray-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'starting':
        return 'text-blue-600 bg-blue-100';
      case 'stopping':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };
</script>

<svelte:head>
  <title>Services - WakeDock</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <!-- Header -->
  <div class="md:flex md:items-center md:justify-between mb-8">
    <div class="flex-1 min-w-0">
      <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">Services</h1>
      <p class="mt-1 text-sm text-gray-500">Manage your Docker services and containers</p>
    </div>
    <div class="mt-4 flex md:mt-0 md:ml-4 space-x-3">
      <!-- Auto-refresh toggle -->
      <button
        type="button"
        class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        class:bg-blue-50={autoRefresh}
        class:text-blue-700={autoRefresh}
        on:click={toggleAutoRefresh}
      >
        <svg class="-ml-0.5 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        Auto-refresh
      </button>

      <!-- Refresh button -->
      <button
        type="button"
        class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        on:click={() => services.load()}
        disabled={$services.isLoading}
      >
        <svg
          class="-ml-0.5 mr-2 h-4 w-4"
          class:animate-spin={$services.isLoading}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        Refresh
      </button>

      <!-- New service button -->
      <button
        type="button"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        on:click={() => goto('/services/new')}
      >
        <svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        New Service
      </button>
    </div>
  </div>

  <!-- Stats Cards -->
  {#if $serviceStats}
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6">
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-blue-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Total Services</dt>
                <dd class="text-lg font-medium text-gray-900">
                  {$serviceStats?.total || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-green-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Running</dt>
                <dd class="text-lg font-medium text-gray-900">
                  {$serviceStats?.running || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-gray-100 rounded-md flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-gray-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Stopped</dt>
                <dd class="text-lg font-medium text-gray-900">
                  {$serviceStats?.stopped || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-red-100 rounded-md flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-red-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Errors</dt>
                <dd class="text-lg font-medium text-gray-900">
                  {$serviceStats?.error || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Filters -->
  <div class="bg-white shadow rounded-lg mb-6">
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div class="flex-1 min-w-0">
          <div class="max-w-lg">
            <label for="search" class="sr-only">Search services</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg
                  class="h-5 w-5 text-gray-400"
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
              </div>
              <input
                id="search"
                type="search"
                placeholder="Search services..."
                class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                bind:value={searchTerm}
              />
            </div>
          </div>
        </div>
        <div class="mt-4 sm:mt-0 sm:ml-4">
          <select
            class="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            bind:value={statusFilter}
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="error">Error</option>
            <option value="starting">Starting</option>
            <option value="stopping">Stopping</option>
          </select>
        </div>
      </div>
    </div>
  </div>

  <!-- Services List -->
  <div class="bg-white shadow overflow-hidden sm:rounded-md">
    {#if $services.isLoading}
      <div class="text-center py-12">
        <div
          class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
        ></div>
        <p class="mt-2 text-sm text-gray-500">Loading services...</p>
      </div>
    {:else if $services.error}
      <div class="text-center py-12">
        <div class="text-red-600 mb-2">
          <svg class="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <p class="text-sm text-gray-500">{$services.error}</p>
        <button
          type="button"
          class="mt-4 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          on:click={() => services.load()}
        >
          Try Again
        </button>
      </div>
    {:else if filteredServices.length === 0}
      <div class="text-center py-12">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No services found</h3>
        <p class="mt-1 text-sm text-gray-500">
          {searchTerm || statusFilter !== 'all'
            ? 'Try adjusting your filters.'
            : 'Get started by creating a new service.'}
        </p>
        {#if !searchTerm && statusFilter === 'all'}
          <div class="mt-6">
            <button
              type="button"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              on:click={() => goto('/services/new')}
            >
              <svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Service
            </button>
          </div>
        {/if}
      </div>
    {:else}
      <ul class="divide-y divide-gray-200">
        {#each filteredServices as service (service.id)}
          <li class="px-6 py-4 hover:bg-gray-50">
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center">
                  <div class="flex-shrink-0">
                    <span
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(
                        service.status
                      )}"
                    >
                      {service.status}
                    </span>
                  </div>
                  <div class="ml-4 flex-1 min-w-0">
                    <div class="flex items-center">
                      <p class="text-sm font-medium text-gray-900 truncate">
                        {service.name}
                      </p>
                      {#if service.health_status}
                        <span
                          class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {service.health_status ===
                          'healthy'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'}"
                        >
                          {service.health_status}
                        </span>
                      {/if}
                    </div>
                    <p class="text-sm text-gray-500 truncate">
                      {service.image}
                    </p>
                    <div class="mt-1 flex items-center text-xs text-gray-500">
                      <span>Created {formatDate(service.created_at)}</span>
                      {#if service.ports.length > 0}
                        <span class="ml-4">
                          Ports: {service.ports.map((p) => `${p.host}:${p.container}`).join(', ')}
                        </span>
                      {/if}
                    </div>
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <!-- Action buttons -->
                {#if service.status === 'running'}
                  <button
                    type="button"
                    class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-yellow-700 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
                    on:click={() => handleServiceAction(service.id, 'restart')}
                  >
                    Restart
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    on:click={() => handleServiceAction(service.id, 'stop')}
                  >
                    Stop
                  </button>
                {:else if service.status === 'stopped'}
                  <button
                    type="button"
                    class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    on:click={() => handleServiceAction(service.id, 'start')}
                  >
                    Start
                  </button>
                {/if}

                <button
                  type="button"
                  class="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  on:click={() => goto(`/services/${service.id}`)}
                >
                  Details
                </button>

                <button
                  type="button"
                  class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  on:click={() => handleDeleteService(service.id, service.name)}
                >
                  Delete
                </button>
              </div>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>
