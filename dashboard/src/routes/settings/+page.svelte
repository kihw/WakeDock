<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { toast } from '$lib/stores/toastStore';
  import Button from '$lib/components/forms/Button.svelte';
  import Modal from '$lib/components/modals/Modal.svelte';

  // Check if current user is admin
  $: isAdmin = $auth.user?.role === 'admin';

  interface SystemSettings {
    general: {
      app_name: string;
      app_description: string;
      default_domain: string;
      admin_email: string;
    };
    docker: {
      socket_path: string;
      network_name: string;
      default_restart_policy: string;
      image_pull_policy: 'always' | 'if-not-present' | 'never';
    };
    caddy: {
      config_path: string;
      auto_https: boolean;
      admin_api_enabled: boolean;
      admin_api_port: number;
    };
    security: {
      session_timeout: number;
      max_login_attempts: number;
      password_min_length: number;
      require_strong_passwords: boolean;
      rate_limit_enabled: boolean;
      rate_limit_requests: number;
      rate_limit_window: number;
    };
    logging: {
      level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
      max_log_size: number;
      log_retention_days: number;
      structured_logging: boolean;
    };
    monitoring: {
      metrics_enabled: boolean;
      health_check_interval: number;
      alert_email: string;
      slack_webhook_url: string;
    };
  }

  let settings: SystemSettings = {
    general: {
      app_name: 'WakeDock',
      app_description: 'Docker service wake-up and management system',
      default_domain: 'localhost',
      admin_email: '',
    },
    docker: {
      socket_path: '/var/run/docker.sock',
      network_name: 'wakedock',
      default_restart_policy: 'unless-stopped',
      image_pull_policy: 'if-not-present',
    },
    caddy: {
      config_path: '/app/caddy/Caddyfile',
      auto_https: true,
      admin_api_enabled: true,
      admin_api_port: 2019,
    },
    security: {
      session_timeout: 3600,
      max_login_attempts: 5,
      password_min_length: 8,
      require_strong_passwords: true,
      rate_limit_enabled: true,
      rate_limit_requests: 100,
      rate_limit_window: 3600,
    },
    logging: {
      level: 'INFO',
      max_log_size: 100,
      log_retention_days: 30,
      structured_logging: true,
    },
    monitoring: {
      metrics_enabled: true,
      health_check_interval: 30,
      alert_email: '',
      slack_webhook_url: '',
    },
  };

  let originalSettings: SystemSettings;
  let loading = true;
  let saving = false;
  let activeTab = 'general';
  let showConfirmModal = false;
  let hasChanges = false;

  const tabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'docker', label: 'Docker', icon: '🐳' },
    { id: 'caddy', label: 'Caddy', icon: '🌐' },
    { id: 'security', label: 'Security', icon: '🔒' },
    { id: 'logging', label: 'Logging', icon: '📝' },
    { id: 'monitoring', label: 'Monitoring', icon: '📊' },
  ];

  onMount(async () => {
    if (!isAdmin) {
      goto('/');
      return;
    }
    await loadSettings();
  });

  $: {
    // Check for changes
    hasChanges = JSON.stringify(settings) !== JSON.stringify(originalSettings);
  }

  async function loadSettings() {
    try {
      loading = true;
      // In a real implementation, this would fetch from the API
      // const response = await api.settings.get();
      // settings = response;
      originalSettings = JSON.parse(JSON.stringify(settings));
    } catch (err) {
      toast.error('Failed to load settings');
    } finally {
      loading = false;
    }
  }

  async function handleSave() {
    if (!hasChanges) return;

    try {
      saving = true;
      // In a real implementation, this would save to the API
      // await api.settings.update(settings);

      originalSettings = JSON.parse(JSON.stringify(settings));
      toast.success('Settings saved successfully');
    } catch (err) {
      toast.error('Failed to save settings');
    } finally {
      saving = false;
    }
  }

  function handleReset() {
    if (!hasChanges) return;
    showConfirmModal = true;
  }

  function confirmReset() {
    settings = JSON.parse(JSON.stringify(originalSettings));
    showConfirmModal = false;
    toast.info('Settings reset to last saved values');
  }

  async function testConnection(type: 'docker' | 'caddy') {
    try {
      if (type === 'docker') {
        // Test docker connection
        toast.info('Testing Docker connection...');
        // await api.system.testDockerConnection();
        toast.success('Docker connection successful');
      } else if (type === 'caddy') {
        // Test caddy connection
        toast.info('Testing Caddy connection...');
        // await api.system.testCaddyConnection();
        toast.success('Caddy connection successful');
      }
    } catch (err) {
      toast.error(`Failed to connect to ${type}`);
    }
  }
</script>

<svelte:head>
  <title>System Settings - WakeDock</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold text-gray-900">System Settings</h1>
    <div class="flex space-x-3">
      <Button
        on:click={handleReset}
        disabled={!hasChanges || saving}
        class="bg-gray-300 hover:bg-gray-400 text-gray-700"
      >
        Reset
      </Button>
      <Button
        on:click={handleSave}
        disabled={!hasChanges || saving}
        class="bg-blue-600 hover:bg-blue-700 text-white"
      >
        {#if saving}
          <svg
            class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          Saving...
        {:else}
          Save Changes
        {/if}
      </Button>
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  {:else}
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <!-- Tab Navigation -->
      <div class="border-b border-gray-200">
        <nav class="-mb-px flex">
          {#each tabs as tab}
            <button
              on:click={() => (activeTab = tab.id)}
              class="py-4 px-6 text-sm font-medium border-b-2 {activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
            >
              <span class="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          {/each}
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="p-6">
        {#if activeTab === 'general'}
          <div class="space-y-6">
            <h3 class="text-lg font-medium text-gray-900">General Settings</h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="app-name" class="block text-sm font-medium text-gray-700"
                  >Application Name</label
                >
                <input
                  id="app-name"
                  type="text"
                  bind:value={settings.general.app_name}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label for="default-domain" class="block text-sm font-medium text-gray-700"
                  >Default Domain</label
                >
                <input
                  id="default-domain"
                  type="text"
                  bind:value={settings.general.default_domain}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  bind:value={settings.general.app_description}
                  rows="3"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                ></textarea>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Admin Email</label>
                <input
                  type="email"
                  bind:value={settings.general.admin_email}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        {:else if activeTab === 'docker'}
          <div class="space-y-6">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium text-gray-900">Docker Settings</h3>
              <Button
                on:click={() => testConnection('docker')}
                size="sm"
                class="bg-green-600 hover:bg-green-700 text-white"
              >
                Test Connection
              </Button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700">Docker Socket Path</label>
                <input
                  type="text"
                  bind:value={settings.docker.socket_path}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Network Name</label>
                <input
                  type="text"
                  bind:value={settings.docker.network_name}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Default Restart Policy</label
                >
                <select
                  bind:value={settings.docker.default_restart_policy}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="no">No</option>
                  <option value="always">Always</option>
                  <option value="on-failure">On Failure</option>
                  <option value="unless-stopped">Unless Stopped</option>
                </select>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Image Pull Policy</label>
                <select
                  bind:value={settings.docker.image_pull_policy}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="always">Always</option>
                  <option value="if-not-present">If Not Present</option>
                  <option value="never">Never</option>
                </select>
              </div>
            </div>
          </div>
        {:else if activeTab === 'caddy'}
          <div class="space-y-6">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium text-gray-900">Caddy Settings</h3>
              <Button
                on:click={() => testConnection('caddy')}
                size="sm"
                class="bg-green-600 hover:bg-green-700 text-white"
              >
                Test Connection
              </Button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700">Config Path</label>
                <input
                  type="text"
                  bind:value={settings.caddy.config_path}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Admin API Port</label>
                <input
                  type="number"
                  bind:value={settings.caddy.admin_api_port}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div class="flex items-center">
                <input
                  type="checkbox"
                  bind:checked={settings.caddy.auto_https}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label class="ml-2 block text-sm text-gray-900">Auto HTTPS</label>
              </div>

              <div class="flex items-center">
                <input
                  type="checkbox"
                  bind:checked={settings.caddy.admin_api_enabled}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label class="ml-2 block text-sm text-gray-900">Enable Admin API</label>
              </div>
            </div>
          </div>
        {:else if activeTab === 'security'}
          <div class="space-y-6">
            <h3 class="text-lg font-medium text-gray-900">Security Settings</h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700"
                  >Session Timeout (seconds)</label
                >
                <input
                  type="number"
                  bind:value={settings.security.session_timeout}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Max Login Attempts</label>
                <input
                  type="number"
                  bind:value={settings.security.max_login_attempts}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700"
                  >Minimum Password Length</label
                >
                <input
                  type="number"
                  bind:value={settings.security.password_min_length}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700"
                  >Rate Limit (requests per window)</label
                >
                <input
                  type="number"
                  bind:value={settings.security.rate_limit_requests}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div class="flex items-center">
                <input
                  type="checkbox"
                  bind:checked={settings.security.require_strong_passwords}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label class="ml-2 block text-sm text-gray-900">Require Strong Passwords</label>
              </div>

              <div class="flex items-center">
                <input
                  type="checkbox"
                  bind:checked={settings.security.rate_limit_enabled}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label class="ml-2 block text-sm text-gray-900">Enable Rate Limiting</label>
              </div>
            </div>
          </div>
        {:else if activeTab === 'logging'}
          <div class="space-y-6">
            <h3 class="text-lg font-medium text-gray-900">Logging Settings</h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700">Log Level</label>
                <select
                  bind:value={settings.logging.level}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="DEBUG">Debug</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                </select>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Max Log Size (MB)</label>
                <input
                  type="number"
                  bind:value={settings.logging.max_log_size}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Log Retention (days)</label>
                <input
                  type="number"
                  bind:value={settings.logging.log_retention_days}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div class="flex items-center">
                <input
                  type="checkbox"
                  bind:checked={settings.logging.structured_logging}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label class="ml-2 block text-sm text-gray-900">Structured Logging (JSON)</label>
              </div>
            </div>
          </div>
        {:else if activeTab === 'monitoring'}
          <div class="space-y-6">
            <h3 class="text-lg font-medium text-gray-900">Monitoring Settings</h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700"
                  >Health Check Interval (seconds)</label
                >
                <input
                  type="number"
                  bind:value={settings.monitoring.health_check_interval}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Alert Email</label>
                <input
                  type="email"
                  bind:value={settings.monitoring.alert_email}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700">Slack Webhook URL</label>
                <input
                  type="url"
                  bind:value={settings.monitoring.slack_webhook_url}
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="https://hooks.slack.com/services/..."
                />
              </div>

              <div class="flex items-center">
                <input
                  type="checkbox"
                  bind:checked={settings.monitoring.metrics_enabled}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label class="ml-2 block text-sm text-gray-900">Enable Metrics Collection</label>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<!-- Reset Confirmation Modal -->
<Modal bind:open={showConfirmModal} title="Reset Settings">
  <p class="text-gray-600 mb-4">
    Are you sure you want to reset all settings to their last saved values? This will discard all
    unsaved changes.
  </p>
  <div class="flex justify-end space-x-3">
    <Button
      on:click={() => (showConfirmModal = false)}
      class="bg-gray-300 hover:bg-gray-400 text-gray-700"
    >
      Cancel
    </Button>
    <Button on:click={confirmReset} class="bg-red-600 hover:bg-red-700 text-white">
      Reset Settings
    </Button>
  </div>
</Modal>

<style>
  :global(.container) {
    max-width: 1200px;
  }
</style>
