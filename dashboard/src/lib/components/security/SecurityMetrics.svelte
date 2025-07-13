<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Card } from '$lib/components/ui/atoms';
  import Button from '$lib/components/ui/atoms/Button.svelte';

  export let metrics: SecurityMetrics;
  export let loading = false;
  export let autoRefresh = true;

  const dispatch = createEventDispatcher<{
    refresh: void;
    toggleAutoRefresh: { enabled: boolean };
  }>();

  interface SecurityMetrics {
    totalSessions: number;
    activeSessions: number;
    failedLogins: number;
    lastActivity: string;
  }

  function handleRefresh() {
    dispatch('refresh');
  }

  function handleAutoRefreshToggle() {
    dispatch('toggleAutoRefresh', { enabled: !autoRefresh });
  }
</script>

<Card>
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Security Metrics</h2>
    <div class="flex items-center gap-2">
      <Button variant="outline" size="sm" on:click={handleRefresh} disabled={loading}>
        {loading ? 'Refreshing...' : 'Refresh'}
      </Button>
      <Button
        variant={autoRefresh ? 'primary' : 'outline'}
        size="sm"
        on:click={handleAutoRefreshToggle}
      >
        Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
      </Button>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <!-- Total Sessions -->
    <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
      <div class="flex items-center">
        <div class="p-2 bg-blue-100 dark:bg-blue-800 rounded-lg">
          <svg
            class="w-6 h-6 text-blue-600 dark:text-blue-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM9 9a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
        </div>
        <div class="ml-4">
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Sessions</p>
          <p class="text-2xl font-semibold text-gray-900 dark:text-white">
            {loading ? '...' : metrics.totalSessions.toLocaleString()}
          </p>
        </div>
      </div>
    </div>

    <!-- Active Sessions -->
    <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
      <div class="flex items-center">
        <div class="p-2 bg-green-100 dark:bg-green-800 rounded-lg">
          <svg
            class="w-6 h-6 text-green-600 dark:text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div class="ml-4">
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Active Sessions</p>
          <p class="text-2xl font-semibold text-gray-900 dark:text-white">
            {loading ? '...' : metrics.activeSessions.toLocaleString()}
          </p>
        </div>
      </div>
    </div>

    <!-- Failed Logins -->
    <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
      <div class="flex items-center">
        <div class="p-2 bg-red-100 dark:bg-red-800 rounded-lg">
          <svg
            class="w-6 h-6 text-red-600 dark:text-red-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.08 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>
        <div class="ml-4">
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Failed Logins</p>
          <p class="text-2xl font-semibold text-gray-900 dark:text-white">
            {loading ? '...' : metrics.failedLogins.toLocaleString()}
          </p>
        </div>
      </div>
    </div>

    <!-- Last Activity -->
    <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
      <div class="flex items-center">
        <div class="p-2 bg-purple-100 dark:bg-purple-800 rounded-lg">
          <svg
            class="w-6 h-6 text-purple-600 dark:text-purple-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div class="ml-4">
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Last Activity</p>
          <p class="text-sm font-semibold text-gray-900 dark:text-white">
            {loading ? '...' : metrics.lastActivity || 'No recent activity'}
          </p>
        </div>
      </div>
    </div>
  </div>
</Card>
