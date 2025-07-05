<!-- Caddy Settings Section -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { TestTube, Globe, Shield, Settings } from 'lucide-svelte';

  export let settings: {
    config_path: string;
    auto_https: boolean;
    admin_api_enabled: boolean;
    admin_api_port: number;
  };

  const dispatch = createEventDispatcher<{
    testConnection: { type: 'caddy' };
  }>();

  function handleTestConnection() {
    dispatch('testConnection', { type: 'caddy' });
  }
</script>

<div class="settings-section">
  <div class="section-header">
    <div class="header-content">
      <h3 class="section-title">Caddy Settings</h3>
      <p class="section-description">Configure Caddy reverse proxy and HTTPS settings</p>
    </div>
    <button type="button" on:click={handleTestConnection} class="test-button">
      <TestTube class="test-icon" />
      Test Connection
    </button>
  </div>

  <div class="section-content">
    <div class="form-grid">
      <div class="form-group col-span-full">
        <label for="config-path" class="form-label">
          <Settings class="label-icon" />
          Configuration File Path
        </label>
        <input
          id="config-path"
          type="text"
          bind:value={settings.config_path}
          class="form-input"
          placeholder="/app/caddy/Caddyfile"
        />
        <p class="form-help">Path to the Caddy configuration file (Caddyfile)</p>
      </div>

      <div class="form-group">
        <label for="admin-api-port" class="form-label"> Admin API Port </label>
        <input
          id="admin-api-port"
          type="number"
          bind:value={settings.admin_api_port}
          class="form-input"
          min="1024"
          max="65535"
          placeholder="2019"
        />
        <p class="form-help">Port for Caddy's administrative API</p>
      </div>
    </div>

    <!-- Feature Toggles -->
    <div class="feature-section">
      <h4 class="feature-title">Features</h4>
      <div class="feature-grid">
        <div class="feature-item">
          <div class="feature-header">
            <div class="feature-info">
              <div class="feature-icon-wrapper">
                <Shield class="feature-icon" />
              </div>
              <div class="feature-content">
                <h5 class="feature-name">Automatic HTTPS</h5>
                <p class="feature-description">Automatically obtain and renew SSL certificates</p>
              </div>
            </div>
            <label class="toggle">
              <input type="checkbox" bind:checked={settings.auto_https} class="toggle-input" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div class="feature-item">
          <div class="feature-header">
            <div class="feature-info">
              <div class="feature-icon-wrapper">
                <Globe class="feature-icon" />
              </div>
              <div class="feature-content">
                <h5 class="feature-name">Admin API</h5>
                <p class="feature-description">Enable Caddy's administrative API interface</p>
              </div>
            </div>
            <label class="toggle">
              <input
                type="checkbox"
                bind:checked={settings.admin_api_enabled}
                class="toggle-input"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Configuration Preview -->
    <div class="config-preview">
      <h4 class="preview-title">Configuration Preview</h4>
      <div class="preview-content">
        <pre class="config-code"><code
            >{`{
  "apps": {
    "http": {
      "servers": {
        "wakedock": {
          "listen": [":80", ":443"],
          "automatic_https": {
            "disable": ${!settings.auto_https}
          }
        }
      }
    }
  },
  "admin": {
    "disabled": ${!settings.admin_api_enabled},
    "listen": "${settings.admin_api_enabled ? `localhost:${settings.admin_api_port}` : 'disabled'}"
  }
}`}</code
          ></pre>
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
    @apply flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300;
  }

  .label-icon {
    @apply w-4 h-4 text-slate-500 dark:text-slate-400;
  }

  .form-input {
    @apply w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200;
  }

  .form-help {
    @apply text-xs text-slate-500 dark:text-slate-400;
  }

  .col-span-full {
    grid-column: span 1;
  }

  @media (min-width: 768px) {
    .col-span-full {
      grid-column: span 2;
    }
  }

  .feature-section {
    @apply space-y-4 pt-4 border-t border-slate-200 dark:border-slate-700;
  }

  .feature-title {
    @apply text-base font-medium text-slate-900 dark:text-slate-100;
  }

  .feature-grid {
    @apply space-y-4;
  }

  .feature-item {
    @apply p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700;
  }

  .feature-header {
    @apply flex items-center justify-between;
  }

  .feature-info {
    @apply flex items-center gap-3;
  }

  .feature-icon-wrapper {
    @apply w-10 h-10 bg-blue-100 dark:bg-blue-900/50 rounded-lg flex items-center justify-center;
  }

  .feature-icon {
    @apply w-5 h-5 text-blue-600 dark:text-blue-400;
  }

  .feature-content {
    @apply flex-1;
  }

  .feature-name {
    @apply text-sm font-medium text-slate-900 dark:text-slate-100 mb-1;
  }

  .feature-description {
    @apply text-xs text-slate-600 dark:text-slate-400;
  }

  .toggle {
    @apply relative inline-flex items-center cursor-pointer;
  }

  .toggle-input {
    @apply sr-only;
  }

  .toggle-slider {
    @apply w-11 h-6 bg-slate-300 dark:bg-slate-600 rounded-full transition-colors duration-200;
  }

  .toggle-input:checked + .toggle-slider {
    @apply bg-blue-600;
  }

  .toggle-slider:before {
    @apply content-[''] absolute top-[2px] left-[2px] bg-white rounded-full h-5 w-5 transition-transform duration-200;
  }

  .toggle-input:checked + .toggle-slider:before {
    @apply translate-x-5;
  }

  .config-preview {
    @apply space-y-3 pt-4 border-t border-slate-200 dark:border-slate-700;
  }

  .preview-title {
    @apply text-base font-medium text-slate-900 dark:text-slate-100;
  }

  .preview-content {
    @apply bg-slate-900 dark:bg-slate-950 rounded-lg p-4 overflow-x-auto;
  }

  .config-code {
    @apply text-sm text-slate-300 font-mono;
  }
</style>
