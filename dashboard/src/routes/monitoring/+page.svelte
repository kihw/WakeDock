<script lang="ts">
  // Monitoring Dashboard Page
  import { onMount, onDestroy } from 'svelte';
  import { websocketClient as websocket } from '$lib/websocket';
  import { uiLogger } from '$lib/utils/logger';
  import { Card } from '$lib/components/ui/atoms';
  import Button from '$lib/components/ui/atoms/Button.svelte';
  import ResourceChart from '$lib/components/ui/organisms/charts/ResourceChart.svelte';

  let systemMetrics = {
    cpu: 0,
    memory: 0,
    disk: 0,
    network: { rx: 0, tx: 0 },
  };

  let services: any[] = [];
  let alerts: any[] = [];

  onMount(() => {
    // Connect to websocket for real-time updates
    websocket.connect();

    // Subscribe to system metrics
    websocket.subscribe('system_metrics', (data: any) => {
      systemMetrics = data;
    });

    // Load initial data
    loadMonitoringData();
  });

  onDestroy(() => {
    websocket.disconnect();
  });

  async function loadMonitoringData() {
    try {
      // Load system metrics and alerts
      uiLogger.info('Monitoring', 'Loading monitoring data');
    } catch (error) {
      uiLogger.error('Monitoring', error, { context: 'loadMonitoringData' });
    }
  }

  function refreshData() {
    loadMonitoringData();
  }
</script>

<svelte:head>
  <title>Monitoring - WakeDock</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold text-gray-900">System Monitoring</h1>
    <Button on:click={refreshData} variant="primary">Refresh Data</Button>
  </div>

  <!-- System Metrics -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <Card title="CPU Usage">
      <div class="text-3xl font-bold text-blue-600">
        {(typeof systemMetrics.cpu === 'number' ? systemMetrics.cpu : 0).toFixed(1)}%
      </div>
    </Card>

    <Card title="Memory Usage">
      <div class="text-3xl font-bold text-green-600">
        {(typeof systemMetrics.memory === 'number' ? systemMetrics.memory : 0).toFixed(1)}%
      </div>
    </Card>

    <Card title="Disk Usage">
      <div class="text-3xl font-bold text-yellow-600">
        {(typeof systemMetrics.disk === 'number' ? systemMetrics.disk : 0).toFixed(1)}%
      </div>
    </Card>

    <Card title="Network">
      <div class="text-sm text-gray-600">
        <div>↓ {((systemMetrics.network?.rx || 0) / 1024 / 1024).toFixed(2)} MB/s</div>
        <div>↑ {((systemMetrics.network?.tx || 0) / 1024 / 1024).toFixed(2)} MB/s</div>
      </div>
    </Card>
  </div>

  <!-- Resource Charts -->
  <Card title="Resource Usage Over Time">
    <ResourceChart data={[]} title="System Resources" showLegend={true} autoRefresh={true} />
  </Card>

  <!-- Service Status -->
  <Card title="Service Status">
    {#if services.length > 0}
      <div class="space-y-2">
        {#each services as service}
          <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span class="font-medium">{service.name}</span>
            <span
              class="px-2 py-1 text-xs rounded-full {service.status === 'running'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'}"
            >
              {service.status}
            </span>
          </div>
        {/each}
      </div>
    {:else}
      <p class="text-gray-500">No services to display</p>
    {/if}
  </Card>

  <!-- Alerts -->
  {#if alerts.length > 0}
    <Card title="Recent Alerts">
      <div class="space-y-2">
        {#each alerts as alert}
          <div class="p-3 bg-yellow-50 border-l-4 border-yellow-400">
            <div class="text-sm font-medium text-yellow-800">{alert.title}</div>
            <div class="text-sm text-yellow-700">{alert.message}</div>
          </div>
        {/each}
      </div>
    </Card>
  {/if}
</div>
