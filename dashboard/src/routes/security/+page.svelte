<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { isAuthenticated } from '$lib/stores';

  // Simple state management
  let loading = true;
  let activeTab = 'monitoring';
  
  let securityMetrics = {
    totalSessions: 0,
    activeSessions: 0,
    failedLogins: 0,
    lastActivity: ''
  };

  onMount(async () => {
    // Redirect if not authenticated
    if (!$isAuthenticated) {
      goto('/login');
      return;
    }
    
    // Load basic security data
    try {
      // Simulated loading
      setTimeout(() => {
        loading = false;
      }, 1000);
    } catch (error) {
      console.error('Failed to load security data:', error);
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Security - WakeDock</title>
  <meta name="description" content="Security monitoring and audit logs for WakeDock" />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Security Center</h1>
    <p class="mt-2 text-gray-600 dark:text-gray-400">
      Monitor security events and review audit logs for your WakeDock instance.
    </p>
  </div>

  <!-- Tab Navigation -->
  <div class="mb-6 border-b">
    <nav class="-mb-px flex" aria-label="Tabs">
      <button
        class="py-3 px-4 border-b-2 font-medium text-sm {activeTab === 'monitoring'
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        on:click={() => (activeTab = 'monitoring')}
        aria-selected={activeTab === 'monitoring'}
        role="tab"
      >
        Security Monitoring
      </button>
      <button
        class="ml-8 py-3 px-4 border-b-2 font-medium text-sm {activeTab === 'audit'
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        on:click={() => (activeTab = 'audit')}
        aria-selected={activeTab === 'audit'}
        role="tab"
      >
        Audit Logs
      </button>
    </nav>
  </div>

  <!-- Tab Content -->
  {#if activeTab === 'monitoring'}
    <div class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Security Metrics Cards -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Total Sessions</dt>
                <dd class="text-lg font-medium text-gray-900">{securityMetrics.totalSessions}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Active Sessions</dt>
                <dd class="text-lg font-medium text-gray-900">{securityMetrics.activeSessions}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Failed Logins</dt>
                <dd class="text-lg font-medium text-gray-900">{securityMetrics.failedLogins}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <svg class="h-8 w-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Last Activity</dt>
                <dd class="text-sm font-medium text-gray-900">
                  {securityMetrics.lastActivity || 'Never'}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Security Events -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Security Events</h3>
          {#if loading}
            <div class="text-center py-8">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              <p class="mt-2 text-gray-600">Loading security events...</p>
            </div>
          {:else}
            <div class="text-center py-8">
              <p class="text-gray-600">No security events found.</p>
              <p class="text-sm text-gray-500 mt-2">This is a simplified version for build compatibility.</p>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {:else if activeTab === 'audit'}
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Audit Logs</h3>
        {#if loading}
          <div class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            <p class="mt-2 text-gray-600">Loading audit logs...</p>
          </div>
        {:else}
          <div class="text-center py-8">
            <p class="text-gray-600">Audit logs functionality will be implemented here.</p>
            <p class="text-sm text-gray-500 mt-2">This is a simplified version for build compatibility.</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
