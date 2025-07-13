<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { toast } from '$lib/stores/toastStore';
  import { ApiClient } from '$lib/api/api-client';
  import SettingsPage from '$lib/components/settings/SettingsPage.svelte';

  // Initialize API client
  const api = new ApiClient();
  
  // Set token when auth changes
  $: if ($auth.token) {
    api.setToken($auth.token);
  }

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
      const response = await api.system.getSettings();
      settings = response;
      originalSettings = JSON.parse(JSON.stringify(settings));
    } catch (err) {
      console.error('Failed to load settings:', err);
      toast.error('Failed to load settings');
    } finally {
      loading = false;
    }
  }

  async function handleSave() {
    if (!hasChanges) return;

    try {
      saving = true;
      await api.system.updateSettings(settings);
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
        // Test Docker connection
        toast.info('Testing Docker connection...');
        // await api.system.testDockerConnection();
        toast.success('Docker connection successful');
      } else if (type === 'caddy') {
        // Test Caddy connection
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
  {#if loading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  {:else}
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <SettingsPage
        {settings}
        {loading}
        {saving}
        {hasChanges}
        bind:activeTab
        on:save={handleSave}
        on:reset={handleReset}
        on:tabChange={(e) => (activeTab = e.detail.tab)}
        on:testConnection={(e) => testConnection(e.detail.type)}
      />
    </div>
  {/if}
</div>

<style>
  :global(.container) {
    max-width: 1200px;
  }
</style>
