<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Cpu, HardDrive, MemoryStick, Clock } from 'lucide-svelte';
  import Widget from '../base/Widget.svelte';

  export let data: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    uptime: number;
  } | null = null;
  export let loading: boolean = false;
  export let error: string = '';

  const dispatch = createEventDispatcher<{
    refresh: void;
  }>();

  function formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }

  function getUsageColor(usage: number): string {
    if (usage < 50) return 'text-green-600';
    if (usage < 80) return 'text-yellow-600';
    return 'text-red-600';
  }

  function getUsageBarColor(usage: number): string {
    if (usage < 50) return 'bg-green-500';
    if (usage < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  }
</script>

<Widget
  title="System Overview"
  subtitle="Resource usage and system status"
  {loading}
  {error}
  refreshable={true}
  size="large"
  on:refresh={() => dispatch('refresh')}
>
  {#if data}
    <div class="grid grid-cols-2 gap-6">
      <!-- CPU Usage -->
      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon cpu">
            <Cpu class="h-5 w-5" />
          </div>
          <div class="metric-info">
            <h4 class="metric-title">CPU Usage</h4>
            <p class="metric-value {getUsageColor(data.cpu_usage)}">
              {(typeof data.cpu_usage === 'number' ? data.cpu_usage : 0).toFixed(1)}%
            </p>
          </div>
        </div>
        <div class="metric-bar">
          <div class="metric-bar-bg">
            <div
              class="metric-bar-fill {getUsageBarColor(data.cpu_usage)}"
              style="width: {Math.min(data.cpu_usage, 100)}%"
            ></div>
          </div>
        </div>
      </div>

      <!-- Memory Usage -->
      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon memory">
            <MemoryStick class="h-5 w-5" />
          </div>
          <div class="metric-info">
            <h4 class="metric-title">Memory Usage</h4>
            <p class="metric-value {getUsageColor(data.memory_usage)}">
              {(typeof data.memory_usage === 'number' ? data.memory_usage : 0).toFixed(1)}%
            </p>
          </div>
        </div>
        <div class="metric-bar">
          <div class="metric-bar-bg">
            <div
              class="metric-bar-fill {getUsageBarColor(data.memory_usage)}"
              style="width: {Math.min(data.memory_usage, 100)}%"
            ></div>
          </div>
        </div>
      </div>

      <!-- Disk Usage -->
      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon disk">
            <HardDrive class="h-5 w-5" />
          </div>
          <div class="metric-info">
            <h4 class="metric-title">Disk Usage</h4>
            <p class="metric-value {getUsageColor(data.disk_usage)}">
              {(typeof data.disk_usage === 'number' ? data.disk_usage : 0).toFixed(1)}%
            </p>
          </div>
        </div>
        <div class="metric-bar">
          <div class="metric-bar-bg">
            <div
              class="metric-bar-fill {getUsageBarColor(data.disk_usage)}"
              style="width: {Math.min(data.disk_usage, 100)}%"
            ></div>
          </div>
        </div>
      </div>

      <!-- System Uptime -->
      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon uptime">
            <Clock class="h-5 w-5" />
          </div>
          <div class="metric-info">
            <h4 class="metric-title">System Uptime</h4>
            <p class="metric-value text-blue-600">
              {formatUptime(data.uptime)}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- System Health Status -->
    <div class="system-status mt-6">
      <div class="status-indicator">
        <div
          class="status-dot {data.cpu_usage < 80 && data.memory_usage < 80 && data.disk_usage < 90
            ? 'healthy'
            : 'warning'}"
        ></div>
        <span class="status-text">
          {data.cpu_usage < 80 && data.memory_usage < 80 && data.disk_usage < 90
            ? 'System Healthy'
            : 'System Under Load'}
        </span>
      </div>
    </div>
  {/if}
</Widget>

<style>
  .metric-card {
    @apply bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-3;
  }

  .metric-header {
    @apply flex items-center space-x-3;
  }

  .metric-icon {
    @apply w-10 h-10 rounded-lg flex items-center justify-center text-white;
  }

  .metric-icon.cpu {
    @apply bg-blue-500;
  }

  .metric-icon.memory {
    @apply bg-green-500;
  }

  .metric-icon.disk {
    @apply bg-purple-500;
  }

  .metric-icon.uptime {
    @apply bg-orange-500;
  }

  .metric-info {
    @apply flex-1 min-w-0;
  }

  .metric-title {
    @apply text-sm font-medium text-gray-700 dark:text-gray-300;
  }

  .metric-value {
    @apply text-lg font-semibold;
  }

  .metric-bar {
    @apply w-full;
  }

  .metric-bar-bg {
    @apply w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden;
  }

  .metric-bar-fill {
    @apply h-full transition-all duration-300 ease-in-out;
  }

  .system-status {
    @apply flex items-center justify-center pt-4 border-t border-gray-200 dark:border-gray-600;
  }

  .status-indicator {
    @apply flex items-center space-x-2;
  }

  .status-dot {
    @apply w-3 h-3 rounded-full;
  }

  .status-dot.healthy {
    @apply bg-green-500;
  }

  .status-dot.warning {
    @apply bg-yellow-500;
  }

  .status-text {
    @apply text-sm font-medium text-gray-700 dark:text-gray-300;
  }
</style>
