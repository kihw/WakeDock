<!-- Dashboard Page Refactorisée -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth.js';
  import { api, type Service, type SystemOverview } from '$lib/api';
  import { websocketClient } from '$lib/websocket.js';
  import Dashboard from '$lib/components/dashboard/Dashboard.svelte';
  import { Button } from '$lib/components/ui/atoms';

  interface DashboardData {
    system: {
      cpu_usage: number;
      memory_usage: number;
      disk_usage: number;
      uptime: number;
    };
    services: {
      total: number;
      running: number;
      stopped: number;
      error: number;
    };
    servicesList: Service[];
  }

  let dashboardData: DashboardData | null = null;
  let loading = true;
  let error = '';
  let services: Service[] = [];
  let systemOverview: SystemOverview | null = null;

  // WebSocket subscriptions
  let wsUnsubscribers: (() => void)[] = [];

  onMount(async () => {
    // Check authentication
    if (!$auth.user) {
      goto('/login');
      return;
    }

    await initializeDashboard();
    setupWebSocketSubscriptions();
  });

  onDestroy(() => {
    // Clean up WebSocket subscriptions
    wsUnsubscribers.forEach((unsubscribe) => unsubscribe());
  });

  async function initializeDashboard() {
    loading = true;
    error = '';

    try {
      await Promise.all([loadServices(), loadSystemOverview()]);

      updateDashboardData();
    } catch (e) {
      console.error('Failed to initialize dashboard:', e);
      error = 'Failed to load dashboard data';
    } finally {
      loading = false;
    }
  }

  async function loadServices() {
    try {
      if (typeof window !== 'undefined' && api.isAuthenticated()) {
        services = await api.services.getAll();
      } else {
        services = [];
      }
    } catch (apiError) {
      console.warn('API not available:', apiError);
      services = [];
    }
  }

  async function loadSystemOverview() {
    try {
      if (typeof window !== 'undefined' && api.isAuthenticated()) {
        systemOverview = await api.getSystemOverview();
      }
    } catch (error) {
      console.warn('Failed to load system overview:', error);
    }
  }

  function updateDashboardData() {
    // Calculate service stats
    const serviceStats = services.reduce(
      (acc, service) => {
        acc.total++;
        switch (service.status) {
          case 'running':
            acc.running++;
            break;
          case 'stopped':
            acc.stopped++;
            break;
          case 'error':
            acc.error++;
            break;
        }
        return acc;
      },
      { total: 0, running: 0, stopped: 0, error: 0 }
    );

    dashboardData = {
      system: systemOverview?.system || {
        cpu_usage: 0,
        memory_usage: 0,
        disk_usage: 0,
        uptime: 0,
      },
      services: serviceStats,
      servicesList: services,
    };
  }

  function setupWebSocketSubscriptions() {
    // Subscribe to service updates
    const serviceUnsubscribe = websocketClient.serviceUpdates.subscribe((updates) => {
      if (updates.length > 0) {
        // Update services with real-time data
        services = services.map((service) => {
          const update = updates.find((u) => u.id === service.id);
          if (update) {
            return {
              ...service,
              status: update.status,
              health_status: update.health_status,
              resource_usage: update.stats
                ? {
                    cpu_usage: update.stats.cpu_usage,
                    memory_usage: update.stats.memory_usage,
                    network_io: update.stats.network_io,
                  }
                : service.resource_usage,
            };
          }
          return service;
        });
        updateDashboardData();
      }
    });

    // Subscribe to system updates
    const systemUnsubscribe = websocketClient.systemUpdates.subscribe((update) => {
      if (update) {
        systemOverview = {
          services: update.services_count,
          system: {
            cpu_usage: update.cpu_usage,
            memory_usage: update.memory_usage,
            disk_usage: update.disk_usage,
            uptime: update.uptime,
          },
          docker: {
            version: '20.10.0',
            api_version: '1.41',
            status: 'healthy',
          },
          caddy: {
            version: '2.6.0',
            status: 'healthy',
            active_routes: 0,
          },
        };
        updateDashboardData();
      }
    });

    wsUnsubscribers.push(serviceUnsubscribe, systemUnsubscribe);
  }

  // Dashboard event handlers
  async function handleRefresh() {
    await initializeDashboard();
  }

  async function handleStartAll() {
    try {
      // Optimistically update all stopped services to starting
      services = services.map((s) => (s.status === 'stopped' ? { ...s, status: 'starting' } : s));
      updateDashboardData();

      // Start all stopped services
      if (api.isAuthenticated()) {
        const stoppedServices = services.filter((s) => s.status === 'starting');
        await Promise.all(stoppedServices.map((service) => api.startService(service.id)));
        // The WebSocket will update the actual statuses when they change
      } else {
        throw new Error('Not authenticated');
      }
    } catch (e) {
      console.error('Failed to start all services:', e);
      // Revert optimistic update
      await loadServices();
      updateDashboardData();
    }
  }

  async function handleStopAll() {
    try {
      // Optimistically update all running services to stopping
      services = services.map((s) => (s.status === 'running' ? { ...s, status: 'stopping' } : s));
      updateDashboardData();

      // Stop all running services
      if (api.isAuthenticated()) {
        const runningServices = services.filter((s) => s.status === 'stopping');
        await Promise.all(runningServices.map((service) => api.stopService(service.id)));
        // The WebSocket will update the actual statuses when they change
      } else {
        throw new Error('Not authenticated');
      }
    } catch (e) {
      console.error('Failed to stop all services:', e);
      // Revert optimistic update
      await loadServices();
      updateDashboardData();
    }
  }

  function handleDeployService() {
    goto('/services/new');
  }
</script>

<svelte:head>
  <title>Dashboard - WakeDock</title>
  <meta name="description" content="WakeDock dashboard - Monitor and manage your Docker services" />
</svelte:head>

{#if error}
  <div class="error-container">
    <div class="error-content">
      <h1 class="error-title">Dashboard Error</h1>
      <p class="error-message">{error}</p>
      <Button variant="success" on:click={handleRefresh}>Try Again</Button>
    </div>
  </div>
{:else}
  <Dashboard
    {dashboardData}
    {loading}
    on:refresh={handleRefresh}
    on:startAll={handleStartAll}
    on:stopAll={handleStopAll}
    on:deployService={handleDeployService}
  />
{/if}

<style>
  .error-container {
    @apply min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center;
  }

  .error-content {
    @apply text-center;
  }

  .error-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-4;
  }

  .error-message {
    @apply text-gray-600 dark:text-gray-400 mb-6;
  }
</style>
