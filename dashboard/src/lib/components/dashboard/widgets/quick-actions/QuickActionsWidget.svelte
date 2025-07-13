<script lang="ts">
  import { Monitor, Play, Plus, RefreshCw, Settings, Square, Wrench } from 'lucide-svelte';
  import { createEventDispatcher } from 'svelte';
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
    openMaintenance: void;
  }>();

  const quickActions = [
    {
      id: 'deploy',
      label: 'Deploy Service',
      icon: Plus,
      color: 'bg-green-600 hover:bg-green-700',
      action: () => dispatch('deployService'),
    },
    {
      id: 'start-all',
      label: 'Start All',
      icon: Play,
      color: 'bg-blue-600 hover:bg-blue-700',
      disabled: !canStartAll,
      action: () => dispatch('startAll'),
    },
    {
      id: 'stop-all',
      label: 'Stop All',
      icon: Square,
      color: 'bg-red-600 hover:bg-red-700',
      disabled: !canStopAll,
      action: () => dispatch('stopAll'),
    },
    {
      id: 'refresh',
      label: 'Refresh All',
      icon: RefreshCw,
      color: 'bg-gray-600 hover:bg-gray-700',
      action: () => dispatch('refresh'),
    },
    {
      id: 'maintenance',
      label: 'Maintenance',
      icon: Wrench,
      color: 'bg-orange-600 hover:bg-orange-700',
      action: () => dispatch('openMaintenance'),
    },
    {
      id: 'monitoring',
      label: 'Monitoring',
      icon: Monitor,
      color: 'bg-purple-600 hover:bg-purple-700',
      action: () => dispatch('openMonitoring'),
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      color: 'bg-gray-600 hover:bg-gray-700',
      action: () => dispatch('openSettings'),
    },
  ];
</script>

<Widget title="Quick Actions" subtitle="Common management tasks" {loading} {error} size="small">
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
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .quick-action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    border-radius: 0.5rem;
    color: white;
    transition: all 0.2s ease;
    min-height: 80px;
    border: none;
    cursor: pointer;
  }

  .quick-action-btn:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5);
  }

  .quick-action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .action-label {
    font-size: 0.75rem;
    font-weight: 500;
    text-align: center;
    line-height: 1.25;
    margin-top: 0.5rem;
  }

  @media (max-width: 768px) {
    .quick-actions-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
