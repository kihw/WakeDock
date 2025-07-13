<script lang="ts">
  import { goto } from '$app/navigation';
  import { RefreshCw, Settings } from 'lucide-svelte';
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';

  import DashboardCustomizeModal from './DashboardCustomizeModal.svelte';
  import GridLayout from './layouts/GridLayout.svelte';
  import QuickActionsWidget from './widgets/quick-actions/QuickActionsWidget.svelte';
  import RunningServicesWidget from './widgets/services/RunningServicesWidget.svelte';
  import ServicesOverviewWidget from './widgets/services/ServicesOverviewWidget.svelte';
  import SystemOverviewWidget from './widgets/system/SystemOverviewWidget.svelte';

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
    servicesList: any[];
  }

  interface WidgetConfig {
    id: string;
    component: any;
    size: 'small' | 'medium' | 'large';
    position: { x: number; y: number };
    props?: any;
  }

  export let dashboardData: DashboardData | null = null;
  export let loading: boolean = false;
  export let userPreferences: any = null;

  let showCustomizeModal = false;

  const dispatch = createEventDispatcher<{
    refresh: void;
    startAll: void;
    stopAll: void;
    deployService: void;
  }>();

  // Default widget layout
  const defaultLayout: WidgetConfig[] = [
    {
      id: 'system-overview',
      component: SystemOverviewWidget,
      size: 'large',
      position: { x: 0, y: 0 },
      props: {},
    },
    {
      id: 'services-overview',
      component: ServicesOverviewWidget,
      size: 'medium',
      position: { x: 3, y: 0 },
      props: {},
    },
    {
      id: 'running-services',
      component: RunningServicesWidget,
      size: 'medium',
      position: { x: 0, y: 2 },
      props: {},
    },
    {
      id: 'quick-actions',
      component: QuickActionsWidget,
      size: 'small',
      position: { x: 2, y: 2 },
      props: {},
    },
  ];

  $: widgetConfig = userPreferences?.dashboardLayout || defaultLayout;
  $: isLoading = loading;
  $: canStartAll = dashboardData ? dashboardData.services.stopped > 0 : false;
  $: canStopAll = dashboardData ? dashboardData.services.running > 0 : false;

  // Auto-refresh interval
  let refreshInterval: ReturnType<typeof setInterval> | null = null;

  onMount(() => {
    // Auto-refresh every 30 seconds
    refreshInterval = setInterval(() => {
      dispatch('refresh');
    }, 30000);
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  function handleRefresh() {
    dispatch('refresh');
  }

  function handleDeployService() {
    dispatch('deployService');
    goto('/services/new');
  }

  function handleStartAll() {
    dispatch('startAll');
  }

  function handleStopAll() {
    dispatch('stopAll');
  }

  function handleOpenSettings() {
    goto('/settings');
  }

  function handleOpenMonitoring() {
    goto('/monitoring');
  }

  function handleOpenMaintenance() {
    goto('/maintenance');
  }

  function openCustomizeModal() {
    showCustomizeModal = true;
  }

  // Transform data for widgets
  $: transformedWidgets = widgetConfig.map((widget) => ({
    ...widget,
    props: {
      ...widget.props,
      // Pass relevant data to each widget
      ...(widget.id === 'system-overview' && dashboardData
        ? {
            data: dashboardData.system,
            loading: isLoading,
          }
        : {}),
      ...(widget.id === 'services-overview' && dashboardData
        ? {
            data: dashboardData.services,
            loading: isLoading,
          }
        : {}),
      ...(widget.id === 'running-services' && dashboardData
        ? {
            services: dashboardData.servicesList || [],
            loading: isLoading,
          }
        : {}),
      ...(widget.id === 'quick-actions'
        ? {
            loading: isLoading,
            canStartAll,
            canStopAll,
          }
        : {}),
    },
  }));
</script>

<div class="dashboard">
  <!-- Dashboard Header -->
  <div class="dashboard-header">
    <div class="header-content">
      <div class="title-section">
        <h1 class="dashboard-title">Dashboard</h1>
        <p class="dashboard-subtitle">System overview and service management</p>
      </div>

      <div class="header-actions">
        <button
          type="button"
          class="action-btn secondary"
          on:click={handleRefresh}
          disabled={isLoading}
          aria-label="Refresh dashboard"
        >
          <RefreshCw class="h-4 w-4 {isLoading ? 'animate-spin' : ''}" />
          Refresh
        </button>

        <button
          type="button"
          class="action-btn primary"
          on:click={openCustomizeModal}
          aria-label="Customize dashboard"
        >
          <Settings class="h-4 w-4" />
          Customize
        </button>
      </div>
    </div>
  </div>

  <!-- Dashboard Content -->
  <div class="dashboard-content">
    {#if isLoading && !dashboardData}
      <div class="dashboard-skeleton">
        <!-- Loading skeleton -->
        {#each Array(4) as _}
          <div class="widget-skeleton"></div>
        {/each}
      </div>
    {:else}
      <GridLayout
        widgets={transformedWidgets}
        {dashboardData}
        on:refresh={handleRefresh}
        on:widgetMoved
        on:widgetResized
      />
    {/if}
  </div>

  <!-- Dashboard Customization Modal -->
  {#if showCustomizeModal}
    <DashboardCustomizeModal
      bind:show={showCustomizeModal}
      currentLayout={widgetConfig}
      on:save={(event) => {
        // Update user preferences with new layout
        userPreferences = {
          ...userPreferences,
          dashboardLayout: event.detail.layout,
        };
        showCustomizeModal = false;
        dispatch('preferencesUpdated', userPreferences);
      }}
    />
  {/if}
</div>

<!-- Event handlers for widget actions -->
<svelte:window
  on:deployService={handleDeployService}
  on:startAll={handleStartAll}
  on:stopAll={handleStopAll}
  on:openSettings={handleOpenSettings}
  on:openMonitoring={handleOpenMonitoring}
  on:openMaintenance={handleOpenMaintenance}
/>

<style>
  .dashboard {
    @apply min-h-screen bg-gray-50 dark:bg-gray-900;
  }

  .dashboard-header {
    @apply bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700;
  }

  .header-content {
    @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6;
    @apply flex items-center justify-between;
  }

  .title-section {
    @apply flex-1 min-w-0;
  }

  .dashboard-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white;
  }

  .dashboard-subtitle {
    @apply mt-1 text-sm text-gray-500 dark:text-gray-400;
  }

  .header-actions {
    @apply flex items-center space-x-3;
  }

  .action-btn {
    @apply inline-flex items-center px-4 py-2 border rounded-md text-sm font-medium;
    @apply focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500;
    @apply transition-colors duration-200;
  }

  .action-btn.primary {
    @apply border-transparent bg-green-600 text-white hover:bg-green-700;
  }

  .action-btn.secondary {
    @apply border-gray-300 bg-white text-gray-700 hover:bg-gray-50;
    @apply dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600;
  }

  .action-btn:disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .action-btn .h-4 {
    @apply mr-2;
  }

  .dashboard-content {
    @apply flex-1;
  }

  .dashboard-skeleton {
    @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4;
  }

  .widget-skeleton {
    @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700;
    @apply h-48 animate-pulse;
  }
</style>
