<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Plus, Play, Square, RefreshCw, Settings, Monitor } from 'lucide-svelte';
  import Widget from '../base/Widget.svelte';
  
  export let loading: boolean = false;
  export let error: string = '';
  export let canStartAll: boolean = false;
  export let canStopAll: boolean = false;

  const dispatch = createEventDispatcher<{
    deployService: void;
    startAll: void;
    stopAll: void;
    refresh: void;
    openSettings: void;
    openMonitoring: void;
  }>();

  const quickActions = [
    {
      id: 'deploy',
      label: 'Deploy Service',
      icon: Plus,
      color: 'bg-green-600 hover:bg-green-700',
      action: () => dispatch('deployService')
    },
    {
      id: 'start-all',
      label: 'Start All',
      icon: Play,
      color: 'bg-blue-600 hover:bg-blue-700',
      disabled: !canStartAll,
      action: () => dispatch('startAll')
    },
    {
      id: 'stop-all',
      label: 'Stop All',
      icon: Square,
      color: 'bg-red-600 hover:bg-red-700',
      disabled: !canStopAll,
      action: () => dispatch('stopAll')
    },
    {
      id: 'refresh',
      label: 'Refresh All',
      icon: RefreshCw,
      color: 'bg-gray-600 hover:bg-gray-700',
      action: () => dispatch('refresh')
    },
    {
      id: 'monitoring',
      label: 'Monitoring',
      icon: Monitor,
      color: 'bg-purple-600 hover:bg-purple-700',
      action: () => dispatch('openMonitoring')
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      color: 'bg-gray-600 hover:bg-gray-700',
      action: () => dispatch('openSettings')
    }
  ];
</script>

<Widget
  title="Quick Actions"
  subtitle="Common management tasks"
  {loading}
  {error}
  size="small"
>
  <div class="quick-actions-grid">
    {#each quickActions as action}
      <button
        type="button"
        class="quick-action-btn {action.color}"
        disabled={action.disabled || loading}
        on:click={action.action}
        title={action.label}
      >
        <svelte:component this={action.icon} class="h-5 w-5" />
        <span class="action-label">{action.label}</span>
      </button>
    {/each}
  </div>
</Widget>

<style>
  .quick-actions-grid {
    @apply grid grid-cols-2 gap-3;
  }

  .quick-action-btn {
    @apply flex flex-col items-center justify-center p-4 rounded-lg text-white;
    @apply transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2;
    @apply min-h-[80px] space-y-2;
  }

  .quick-action-btn:focus {
    @apply ring-white ring-opacity-50;
  }

  .quick-action-btn:disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .action-label {
    @apply text-xs font-medium text-center leading-tight;
  }

  @media (max-width: 768px) {
    .quick-actions-grid {
      @apply grid-cols-1;
    }
  }
</style>