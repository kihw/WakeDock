<!-- Create New Service Page -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { services, ui, isAuthenticated } from '$lib/stores';
  import type { CreateServiceRequest } from '$lib/api';

  let isSubmitting = false;
  let formData: CreateServiceRequest = {
    name: '',
    image: '',
    ports: [],
    environment: {},
    volumes: [],
    restart_policy: 'unless-stopped',
    labels: {},
  };

  // Form fields for dynamic arrays
  let portsInput = '';
  let environmentInput = '';
  let volumesInput = '';
  let labelsInput = '';

  onMount(() => {
    // Redirect if not authenticated
    if (!$isAuthenticated) {
      goto('/login');
      return;
    }
  });

  const parsePortsInput = (input: string) => {
    if (!input.trim()) return [];

    return input
      .split(',')
      .map((port) => {
        const [host, container, protocol] = port.trim().split(':');
        return {
          host: parseInt(host),
          container: parseInt(container || host),
          protocol: (protocol as 'tcp' | 'udp') || 'tcp',
        };
      })
      .filter((p) => !isNaN(p.host) && !isNaN(p.container));
  };

  const parseKeyValueInput = (input: string): Record<string, string> => {
    if (!input.trim()) return {};

    const result: Record<string, string> = {};
    input.split(',').forEach((pair) => {
      const [key, value] = pair.trim().split('=');
      if (key && value) {
        result[key.trim()] = value.trim();
      }
    });
    return result;
  };

  const parseVolumesInput = (input: string) => {
    if (!input.trim()) return [];

    return input
      .split(',')
      .map((volume) => {
        const [host, container, mode] = volume.trim().split(':');
        return {
          host: host.trim(),
          container: container.trim(),
          mode: (mode as 'rw' | 'ro') || 'rw',
        };
      })
      .filter((v) => v.host && v.container);
  };

  const handleSubmit = async (event: Event) => {
    event.preventDefault();

    if (isSubmitting) return;

    // Validate required fields
    if (!formData.name.trim()) {
      ui.showError('Validation Error', 'Service name is required');
      return;
    }

    if (!formData.image.trim()) {
      ui.showError('Validation Error', 'Docker image is required');
      return;
    }

    isSubmitting = true;

    try {
      const serviceData: CreateServiceRequest = {
        ...formData,
        name: formData.name.trim(),
        image: formData.image.trim(),
        ports: parsePortsInput(portsInput),
        environment: parseKeyValueInput(environmentInput),
        volumes: parseVolumesInput(volumesInput),
        labels: parseKeyValueInput(labelsInput),
      };

      const newService = await services.create(serviceData);
      ui.showSuccess(
        'Service created',
        `Service "${newService.name}" has been created successfully.`
      );
      goto('/services');
    } catch (error) {
      ui.showError('Failed to create service', (error as any).message);
    } finally {
      isSubmitting = false;
    }
  };

  const handleCancel = () => {
    goto('/services');
  };
</script>

<svelte:head>
  <title>New Service - WakeDock</title>
</svelte:head>

<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
            <span class="ml-4 text-sm font-medium text-gray-500">New Service</span>
          </div>
        </li>
      </ol>
    </nav>

    <div class="mt-4">
      <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
        Create New Service
      </h1>
      <p class="mt-1 text-sm text-gray-500">
        Configure a new Docker service to be managed by WakeDock
      </p>
    </div>
  </div>

  <!-- Form -->
  <form on:submit={handleSubmit} class="space-y-8">
    <div class="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
      <div class="md:grid md:grid-cols-3 md:gap-6">
        <div class="md:col-span-1">
          <h3 class="text-lg font-medium leading-6 text-gray-900">Basic Information</h3>
          <p class="mt-1 text-sm text-gray-500">Basic configuration for your Docker service</p>
        </div>
        <div class="mt-5 md:mt-0 md:col-span-2">
          <div class="grid grid-cols-6 gap-6">
            <div class="col-span-6 sm:col-span-4">
              <label for="name" class="block text-sm font-medium text-gray-700">Service Name</label>
              <input
                type="text"
                name="name"
                id="name"
                required
                class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="my-service"
                bind:value={formData.name}
              />
              <p class="mt-2 text-sm text-gray-500">
                A unique name for your service. Used for container naming and identification.
              </p>
            </div>

            <div class="col-span-6">
              <label for="image" class="block text-sm font-medium text-gray-700">Docker Image</label
              >
              <input
                type="text"
                name="image"
                id="image"
                required
                class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="nginx:latest"
                bind:value={formData.image}
              />
              <p class="mt-2 text-sm text-gray-500">
                The Docker image to use for this service (e.g., nginx:latest, mysql:8.0).
              </p>
            </div>

            <div class="col-span-6 sm:col-span-3">
              <label for="restart_policy" class="block text-sm font-medium text-gray-700"
                >Restart Policy</label
              >
              <select
                id="restart_policy"
                name="restart_policy"
                class="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                bind:value={formData.restart_policy}
              >
                <option value="no">No</option>
                <option value="always">Always</option>
                <option value="on-failure">On Failure</option>
                <option value="unless-stopped">Unless Stopped</option>
              </select>
              <p class="mt-2 text-sm text-gray-500">
                When the container should be automatically restarted.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
      <div class="md:grid md:grid-cols-3 md:gap-6">
        <div class="md:col-span-1">
          <h3 class="text-lg font-medium leading-6 text-gray-900">Network & Storage</h3>
          <p class="mt-1 text-sm text-gray-500">Configure port mappings and volume mounts</p>
        </div>
        <div class="mt-5 md:mt-0 md:col-span-2">
          <div class="grid grid-cols-6 gap-6">
            <div class="col-span-6">
              <label for="ports" class="block text-sm font-medium text-gray-700"
                >Port Mappings</label
              >
              <input
                type="text"
                name="ports"
                id="ports"
                class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="8080:80,8443:443:tcp"
                bind:value={portsInput}
              />
              <p class="mt-2 text-sm text-gray-500">
                Comma-separated port mappings (host:container:protocol). Protocol is optional
                (default: tcp).
              </p>
            </div>

            <div class="col-span-6">
              <label for="volumes" class="block text-sm font-medium text-gray-700"
                >Volume Mounts</label
              >
              <input
                type="text"
                name="volumes"
                id="volumes"
                class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="/host/path:/container/path:rw,/another/path:/app/data:ro"
                bind:value={volumesInput}
              />
              <p class="mt-2 text-sm text-gray-500">
                Comma-separated volume mounts (host:container:mode). Mode is optional (default: rw).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
      <div class="md:grid md:grid-cols-3 md:gap-6">
        <div class="md:col-span-1">
          <h3 class="text-lg font-medium leading-6 text-gray-900">Environment & Labels</h3>
          <p class="mt-1 text-sm text-gray-500">Set environment variables and Docker labels</p>
        </div>
        <div class="mt-5 md:mt-0 md:col-span-2">
          <div class="grid grid-cols-6 gap-6">
            <div class="col-span-6">
              <label for="environment" class="block text-sm font-medium text-gray-700"
                >Environment Variables</label
              >
              <input
                type="text"
                name="environment"
                id="environment"
                class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="NODE_ENV=production,PORT=3000,DATABASE_URL=postgres://..."
                bind:value={environmentInput}
              />
              <p class="mt-2 text-sm text-gray-500">
                Comma-separated environment variables (KEY=value).
              </p>
            </div>

            <div class="col-span-6">
              <label for="labels" class="block text-sm font-medium text-gray-700"
                >Docker Labels</label
              >
              <input
                type="text"
                name="labels"
                id="labels"
                class="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                placeholder="traefik.enable=true,caddy.domain=example.com"
                bind:value={labelsInput}
              />
              <p class="mt-2 text-sm text-gray-500">Comma-separated Docker labels (key=value).</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex justify-end space-x-3">
      <button
        type="button"
        class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        on:click={handleCancel}
        disabled={isSubmitting}
      >
        Cancel
      </button>
      <button
        type="submit"
        class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={isSubmitting}
      >
        {#if isSubmitting}
          <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          Creating...
        {:else}
          Create Service
        {/if}
      </button>
    </div>
  </form>
</div>
