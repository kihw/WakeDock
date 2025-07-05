<!-- Docker Settings Section -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { TestTube, CheckCircle, AlertCircle } from 'lucide-svelte';

  export let settings: {
    socket_path: string;
    network_name: string;
    default_restart_policy: string;
    image_pull_policy: 'always' | 'if-not-present' | 'never';
  };

  const dispatch = createEventDispatcher<{
    testConnection: { type: 'docker' };
  }>();

  function handleTestConnection() {
    dispatch('testConnection', { type: 'docker' });
  }

  const restartPolicies = [
    { value: 'no', label: 'No', description: 'Do not restart containers' },
    { value: 'always', label: 'Always', description: 'Always restart containers' },
    { value: 'on-failure', label: 'On Failure', description: 'Restart only on failure' },
    {
      value: 'unless-stopped',
      label: 'Unless Stopped',
      description: 'Restart unless manually stopped',
    },
  ];

  const pullPolicies = [
    { value: 'always', label: 'Always', description: 'Always pull the latest image' },
    {
      value: 'if-not-present',
      label: 'If Not Present',
      description: 'Pull only if image not present locally',
    },
    { value: 'never', label: 'Never', description: 'Never pull images, use local only' },
  ];
</script>

<div class="settings-section">
  <div class="section-header">
    <div class="header-content">
      <h3 class="section-title">Docker Settings</h3>
      <p class="section-description">Configure Docker daemon connection and container defaults</p>
    </div>
    <button type="button" on:click={handleTestConnection} class="test-button">
      <TestTube class="test-icon" />
      Test Connection
    </button>
  </div>

  <div class="section-content">
    <div class="form-grid">
      <div class="form-group">
        <label for="socket-path" class="form-label"> Docker Socket Path </label>
        <input
          id="socket-path"
          type="text"
          bind:value={settings.socket_path}
          class="form-input"
          placeholder="/var/run/docker.sock"
        />
        <p class="form-help">Path to the Docker daemon socket</p>
      </div>

      <div class="form-group">
        <label for="network-name" class="form-label"> Default Network Name </label>
        <input
          id="network-name"
          type="text"
          bind:value={settings.network_name}
          class="form-input"
          placeholder="wakedock"
        />
        <p class="form-help">Network used for container communication</p>
      </div>

      <div class="form-group">
        <label for="restart-policy" class="form-label"> Default Restart Policy </label>
        <select
          id="restart-policy"
          bind:value={settings.default_restart_policy}
          class="form-select"
        >
          {#each restartPolicies as policy}
            <option value={policy.value}>
              {policy.label}
            </option>
          {/each}
        </select>
        <p class="form-help">
          {restartPolicies.find((p) => p.value === settings.default_restart_policy)?.description ||
            'Default container restart behavior'}
        </p>
      </div>

      <div class="form-group">
        <label for="pull-policy" class="form-label"> Image Pull Policy </label>
        <select id="pull-policy" bind:value={settings.image_pull_policy} class="form-select">
          {#each pullPolicies as policy}
            <option value={policy.value}>
              {policy.label}
            </option>
          {/each}
        </select>
        <p class="form-help">
          {pullPolicies.find((p) => p.value === settings.image_pull_policy)?.description ||
            'When to pull Docker images'}
        </p>
      </div>
    </div>

    <!-- Docker Connection Status Info -->
    <div class="connection-info">
      <div class="info-card">
        <div class="info-header">
          <CheckCircle class="info-icon success" />
          <span class="info-title">Connection Status</span>
        </div>
        <p class="info-description">Click "Test Connection" to verify Docker daemon connectivity</p>
      </div>

      <div class="info-card">
        <div class="info-header">
          <AlertCircle class="info-icon warning" />
          <span class="info-title">Security Note</span>
        </div>
        <p class="info-description">
          Ensure WakeDock has appropriate permissions to access the Docker socket
        </p>
      </div>
    </div>
  </div>
</div>

<style>
  .settings-section {
    @apply space-y-6;
  }

  .section-header {
    @apply flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 border-b border-slate-200 dark:border-slate-700 pb-4;
  }

  .header-content {
    @apply flex-1;
  }

  .section-title {
    @apply text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1;
  }

  .section-description {
    @apply text-sm text-slate-600 dark:text-slate-400;
  }

  .test-button {
    @apply flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2;
  }

  .test-icon {
    @apply w-4 h-4;
  }

  .section-content {
    @apply space-y-6 pt-2;
  }

  .form-grid {
    @apply grid grid-cols-1 md:grid-cols-2 gap-6;
  }

  .form-group {
    @apply space-y-2;
  }

  .form-label {
    @apply block text-sm font-medium text-slate-700 dark:text-slate-300;
  }

  .form-input,
  .form-select {
    @apply w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200;
  }

  .form-help {
    @apply text-xs text-slate-500 dark:text-slate-400;
  }

  .connection-info {
    @apply grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-200 dark:border-slate-700;
  }

  .info-card {
    @apply p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700;
  }

  .info-header {
    @apply flex items-center gap-2 mb-2;
  }

  .info-icon {
    @apply w-5 h-5;
  }

  .info-icon.success {
    @apply text-green-600 dark:text-green-400;
  }

  .info-icon.warning {
    @apply text-amber-600 dark:text-amber-400;
  }

  .info-title {
    @apply text-sm font-medium text-slate-900 dark:text-slate-100;
  }

  .info-description {
    @apply text-xs text-slate-600 dark:text-slate-400;
  }
</style>
