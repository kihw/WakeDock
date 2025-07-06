<!-- Service Detail Page -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { services, ui, isAuthenticated } from '$lib/stores';
  import { websocketClient as websocket } from '$lib/websocket';
  import { api } from '$lib/api';
  import type { Service, UpdateServiceRequest } from '$lib/api';

  let serviceId: string;
  let service: Service | null = null;
  let isLoading = true;
  let isEditing = false;
  let logs: string[] = [];
  let showLogs = false;
  let logLines = 100;
  let autoRefresh = true;
  let refreshInterval: NodeJS.Timeout | null = null;
  let logContainer: HTMLDivElement;

  // Edit form data
  let editForm: UpdateServiceRequest = {
    id: '',
    name: '',
    image: '',
    restart_policy: 'unless-stopped',
  };

  $: {
    serviceId = $page.params.id;
    if (serviceId) {
      loadService();
    }
  }

  onMount(() => {
    // Redirect if not authenticated
    if (!$isAuthenticated) {
      goto('/login');
      return;
    }

    // Setup WebSocket for real-time updates
    websocket.connect();
    websocket.subscribe('service_status', (data) => {
      if (data.serviceId === serviceId) {
        if (service) {
          service.status = data.status;
          service = { ...service }; // Trigger reactivity
        }
      }
    });

    websocket.subscribe('service_logs', (data) => {
      if (data.serviceId === serviceId) {
        logs = [...logs, data.log];
        // Auto-scroll to bottom
        setTimeout(() => {
          if (logContainer) {
            logContainer.scrollTop = logContainer.scrollHeight;
          }
        }, 100);
      }
    });

    // Setup auto-refresh
    if (autoRefresh) {
      startAutoRefresh();
    }
  });

  onDestroy(() => {
    stopAutoRefresh();
    websocket.disconnect();
  });

  const loadService = async () => {
    isLoading = true;
    try {
      service = await services.getService(serviceId);
      if (service) {
        editForm = {
          id: service.id,
          name: service.name,
          image: service.image,
          restart_policy: service.restart_policy,
        };
      }
    } catch (error) {
      ui.showError('Failed to load service', (error as any).message);
      goto('/services');
    } finally {
      isLoading = false;
    }
  };

  const startAutoRefresh = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    refreshInterval = setInterval(loadService, 5000);
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

  const handleServiceAction = async (action: 'start' | 'stop' | 'restart') => {
    if (!service) return;

    try {
      switch (action) {
        case 'start':
          await services.start(service.id);
          ui.showSuccess('Service started', 'Service is starting up...');
          break;
        case 'stop':
          await services.stop(service.id);
          ui.showSuccess('Service stopped', 'Service is shutting down...');
          break;
        case 'restart':
          await services.restart(service.id);
          ui.showSuccess('Service restarting', 'Service is restarting...');
          break;
      }

      // Refresh service status after a short delay
      setTimeout(loadService, 2000);
    } catch (error) {
      ui.showError(`Failed to ${action} service`, (error as any).message);
    }
  };

  const handleUpdate = async (event: Event) => {
    event.preventDefault();
    if (!service) return;

    try {
      const updatedService = await services.updateService(editForm);
      service = updatedService;
      isEditing = false;
      ui.showSuccess('Service updated', 'Service configuration has been updated.');
    } catch (error) {
      ui.showError('Failed to update service', (error as any).message);
    }
  };

  const handleDelete = async () => {
    if (!service) return;

    const confirmed = confirm(`Are you sure you want to delete service "${service.name}"?`);
    if (confirmed) {
      try {
        await services.delete(service.id);
        ui.showSuccess('Service deleted', `Service "${service.name}" has been deleted.`);
        goto('/services');
      } catch (error) {
        ui.showError('Failed to delete service', (error as any).message);
      }
    }
  };

  const loadLogs = async () => {
    if (!service) return;

    try {
      const response = await api.getServiceLogs(service.id, logLines);
      logs = response || [];
      showLogs = true;

      // Auto-scroll to bottom
      setTimeout(() => {
        if (logContainer) {
          logContainer.scrollTop = logContainer.scrollHeight;
        }
      }, 100);
    } catch (error) {
      ui.showError('Failed to load logs', (error as any).message);
    }
  };

  const toggleLogs = async () => {
    if (showLogs) {
      showLogs = false;
      // Stop real-time log streaming
      websocket.unsubscribe('service_logs');
    } else {
      await loadLogs();
      // Start real-time log streaming
      websocket.subscribe('service_logs', (data) => {
        if (data.serviceId === serviceId) {
          logs = [...logs, data.log];
          // Auto-scroll to bottom
          setTimeout(() => {
            if (logContainer) {
              logContainer.scrollTop = logContainer.scrollHeight;
            }
          }, 100);
        }
      });
    }
  };

  const clearLogs = () => {
    logs = [];
  };

  const downloadLogs = () => {
    const content = logs.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${service?.name}-logs.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
  <title>{service ? `${service.name} - ` : ''}Service Details - WakeDock</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  {#if isLoading}
    <div class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-sm text-gray-500">Loading service details...</p>
    </div>
  {:else if service}
    <!-- Header -->
    <div class="mb-8">
      <nav class="flex" aria-label="Breadcrumb">
        <ol class="flex items-center space-x-4">
          <li>
            <div>
              <a href="/services" class="text-gray-400 hover:text-gray-500">
                <svg class="flex-shrink-0 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M9.707 14.707a1 1 0 01-1.414 0L3.586 10l4.707-4.707a1 1 0 011.414 1.414L6.414 10l3.293 3.293a1 1 0 010 1.414z"
                    clip-rule="evenodd"
                  />
                </svg>
                <span class="sr-only">Back</span>
              </a>
            </div>
          </li>
          <li>
            <div class="flex items-center">
              <svg
                class="flex-shrink-0 h-5 w-5 text-gray-300"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
              <a href="/services" class="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700"
                >Services</a
              >
            </div>
          </li>
          <li>
            <div class="flex items-center">
              <svg
                class="flex-shrink-0 h-5 w-5 text-gray-300"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
              <span class="ml-4 text-sm font-medium text-gray-500">{service.name}</span>
            </div>
          </li>
        </ol>
      </nav>

      <div class="mt-4 md:flex md:items-center md:justify-between">
        <div class="flex-1 min-w-0">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              {service.name}
            </h1>
            <span
              class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(
                service.status
              )}"
            >
              {service.status}
            </span>
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
          <p class="mt-1 text-sm text-gray-500">
            {service.image}
          </p>
        </div>
        <div class="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          <button
            type="button"
            class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            on:click={toggleAutoRefresh}
          >
            {autoRefresh ? 'Stop Auto-refresh' : 'Auto-refresh'}
          </button>
          <button
            type="button"
            class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            on:click={loadService}
          >
            Refresh
          </button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Service Actions -->
      <div class="lg:col-span-1">
        <div class="bg-white shadow sm:rounded-lg mb-6">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Actions</h3>
            <div class="space-y-3">
              {#if service.status === 'running'}
                <button
                  type="button"
                  class="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-yellow-700 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
                  on:click={() => handleServiceAction('restart')}
                >
                  Restart Service
                </button>
                <button
                  type="button"
                  class="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  on:click={() => handleServiceAction('stop')}
                >
                  Stop Service
                </button>
              {:else if service.status === 'stopped'}
                <button
                  type="button"
                  class="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  on:click={() => handleServiceAction('start')}
                >
                  Start Service
                </button>
              {/if}

              <button
                type="button"
                class="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                on:click={loadLogs}
              >
                View Logs
              </button>

              <button
                type="button"
                class="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                on:click={() => (isEditing = !isEditing)}
              >
                {isEditing ? 'Cancel Edit' : 'Edit Service'}
              </button>

              <button
                type="button"
                class="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                on:click={handleDelete}
              >
                Delete Service
              </button>
            </div>
          </div>
        </div>

        <!-- Service Info -->
        <div class="bg-white shadow sm:rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Information</h3>
            <dl class="space-y-3">
              <div>
                <dt class="text-sm font-medium text-gray-500">Created</dt>
                <dd class="text-sm text-gray-900">
                  {formatDate(service.created_at)}
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Updated</dt>
                <dd class="text-sm text-gray-900">
                  {formatDate(service.updated_at)}
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Restart Policy</dt>
                <dd class="text-sm text-gray-900">
                  {service.restart_policy}
                </dd>
              </div>
              {#if service.ports.length > 0}
                <div>
                  <dt class="text-sm font-medium text-gray-500">Ports</dt>
                  <dd class="text-sm text-gray-900">
                    {#each service.ports as port}
                      <div>
                        {port.host}:{port.container}/{port.protocol}
                      </div>
                    {/each}
                  </dd>
                </div>
              {/if}
            </dl>
          </div>
        </div>
      </div>

      <!-- Service Configuration -->
      <div class="lg:col-span-2">
        {#if isEditing}
          <!-- Edit Form -->
          <form on:submit={handleUpdate} class="bg-white shadow sm:rounded-lg">
            <div class="px-4 py-5 sm:p-6">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Edit Service</h3>

              <div class="grid grid-cols-1 gap-6">
                <div>
                  <label for="edit-name" class="block text-sm font-medium text-gray-700"
                    >Service Name</label
                  >
                  <input
                    type="text"
                    id="edit-name"
                    required
                    class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    bind:value={editForm.name}
                  />
                </div>

                <div>
                  <label for="edit-image" class="block text-sm font-medium text-gray-700"
                    >Docker Image</label
                  >
                  <input
                    type="text"
                    id="edit-image"
                    required
                    class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    bind:value={editForm.image}
                  />
                </div>

                <div>
                  <label for="edit-restart-policy" class="block text-sm font-medium text-gray-700"
                    >Restart Policy</label
                  >
                  <select
                    id="edit-restart-policy"
                    class="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    bind:value={editForm.restart_policy}
                  >
                    <option value="no">No</option>
                    <option value="always">Always</option>
                    <option value="on-failure">On Failure</option>
                    <option value="unless-stopped">Unless Stopped</option>
                  </select>
                </div>
              </div>

              <div class="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  on:click={() => (isEditing = false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </form>
        {:else}
          <!-- Configuration Display -->
          <div class="bg-white shadow sm:rounded-lg">
            <div class="px-4 py-5 sm:p-6">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Configuration</h3>

              <div class="space-y-6">
                {#if Object.keys(service.environment).length > 0}
                  <div>
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Environment Variables</h4>
                    <div class="bg-gray-50 rounded-md p-3">
                      <dl class="space-y-2">
                        {#each Object.entries(service.environment) as [key, value]}
                          <div class="flex">
                            <dt class="text-sm font-medium text-gray-500 w-1/3">
                              {key}
                            </dt>
                            <dd class="text-sm text-gray-900 w-2/3 font-mono">
                              {value}
                            </dd>
                          </div>
                        {/each}
                      </dl>
                    </div>
                  </div>
                {/if}

                {#if service.volumes.length > 0}
                  <div>
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Volume Mounts</h4>
                    <div class="bg-gray-50 rounded-md p-3">
                      <div class="space-y-2">
                        {#each service.volumes as volume}
                          <div class="text-sm text-gray-900 font-mono">
                            {volume.host} → {volume.container}
                            ({volume.mode})
                          </div>
                        {/each}
                      </div>
                    </div>
                  </div>
                {/if}

                {#if Object.keys(service.labels).length > 0}
                  <div>
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Labels</h4>
                    <div class="bg-gray-50 rounded-md p-3">
                      <dl class="space-y-2">
                        {#each Object.entries(service.labels) as [key, value]}
                          <div class="flex">
                            <dt class="text-sm font-medium text-gray-500 w-1/3">
                              {key}
                            </dt>
                            <dd class="text-sm text-gray-900 w-2/3 font-mono">
                              {value}
                            </dd>
                          </div>
                        {/each}
                      </dl>
                    </div>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Logs Modal -->
    {#if showLogs}
      <div
        class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
        role="dialog"
        aria-modal="true"
        aria-labelledby="logs-modal-title"
        tabindex="-1"
        on:click={() => (showLogs = false)}
        on:keydown={(e) => e.key === 'Escape' && (showLogs = false)}
      >
        <div
          class="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white"
          role="document"
          tabindex="-1"
          on:click|stopPropagation
          on:keydown|stopPropagation
        >
          <div class="flex items-center justify-between mb-4">
            <h3 id="logs-modal-title" class="text-lg font-bold text-gray-900">Service Logs</h3>
            <div class="flex items-center space-x-2">
              <select
                class="text-sm border-gray-300 rounded-md"
                bind:value={logLines}
                on:change={loadLogs}
              >
                <option value={50}>50 lines</option>
                <option value={100}>100 lines</option>
                <option value={200}>200 lines</option>
                <option value={500}>500 lines</option>
              </select>
              <button
                type="button"
                class="text-gray-400 hover:text-gray-600"
                on:click={() => (showLogs = false)}
              >
                <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          <div
            class="bg-black text-green-400 p-4 rounded-md h-96 overflow-y-auto font-mono text-sm"
            bind:this={logContainer}
          >
            {#if logs.length > 0}
              {#each logs as line}
                <div class="whitespace-pre-wrap">{line}</div>
              {/each}
            {:else}
              <div class="text-gray-500">No logs available</div>
            {/if}
          </div>

          <div class="mt-4 flex justify-end">
            <button
              type="button"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              on:click={loadLogs}
            >
              Refresh Logs
            </button>
          </div>
        </div>
      </div>
    {/if}
  {:else}
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
      <p class="text-sm text-gray-500">Service not found</p>
      <button
        type="button"
        class="mt-4 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        on:click={() => goto('/services')}
      >
        Back to Services
      </button>
    </div>
  {/if}
</div>
