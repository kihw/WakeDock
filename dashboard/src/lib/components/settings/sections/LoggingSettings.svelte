<!-- Logging Settings Section -->
<script lang="ts">
  import { FileText, Archive, Settings, Info } from 'lucide-svelte';

  export let settings: {
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
    max_log_size: number;
    log_retention_days: number;
    structured_logging: boolean;
  };

  const logLevels = [
    {
      value: 'DEBUG',
      label: 'Debug',
      description: 'Detailed debugging information',
      color: 'text-slate-600',
    },
    {
      value: 'INFO',
      label: 'Info',
      description: 'General informational messages',
      color: 'text-blue-600',
    },
    {
      value: 'WARNING',
      label: 'Warning',
      description: 'Warning messages for potential issues',
      color: 'text-amber-600',
    },
    { value: 'ERROR', label: 'Error', description: 'Error messages only', color: 'text-red-600' },
  ];

  $: currentLevelInfo = logLevels.find((level) => level.value === settings.level);
</script>

<div class="settings-section">
  <div class="section-header">
    <h3 class="section-title">Logging Settings</h3>
    <p class="section-description">Configure application logging behavior and retention policies</p>
  </div>

  <div class="section-content">
    <!-- Log Level Configuration -->
    <div class="subsection">
      <div class="subsection-header">
        <Settings class="subsection-icon" />
        <h4 class="subsection-title">Log Level</h4>
      </div>

      <div class="log-level-selector">
        <div class="level-options">
          {#each logLevels as level}
            <label class="level-option" class:selected={settings.level === level.value}>
              <input
                type="radio"
                name="log-level"
                value={level.value}
                bind:group={settings.level}
                class="level-input"
              />
              <div class="level-content">
                <div class="level-header">
                  <span class="level-label {level.color}">{level.label}</span>
                  <span class="level-value">{level.value}</span>
                </div>
                <p class="level-description">{level.description}</p>
              </div>
            </label>
          {/each}
        </div>

        {#if currentLevelInfo}
          <div class="current-level-info">
            <Info class="info-icon" />
            <span class="info-text">
              Current level: <strong class={currentLevelInfo.color}>{currentLevelInfo.label}</strong
              >
              - {currentLevelInfo.description}
            </span>
          </div>
        {/if}
      </div>
    </div>

    <!-- Storage Configuration -->
    <div class="subsection">
      <div class="subsection-header">
        <Archive class="subsection-icon" />
        <h4 class="subsection-title">Storage & Retention</h4>
      </div>

      <div class="form-grid">
        <div class="form-group">
          <label for="max-log-size" class="form-label"> Maximum Log File Size (MB) </label>
          <input
            id="max-log-size"
            type="number"
            bind:value={settings.max_log_size}
            class="form-input"
            min="1"
            max="1000"
            placeholder="100"
          />
          <p class="form-help">Log files will be rotated when they exceed this size</p>
        </div>

        <div class="form-group">
          <label for="log-retention" class="form-label"> Log Retention (days) </label>
          <input
            id="log-retention"
            type="number"
            bind:value={settings.log_retention_days}
            class="form-input"
            min="1"
            max="365"
            placeholder="30"
          />
          <p class="form-help">Old log files will be automatically deleted after this period</p>
        </div>
      </div>
    </div>

    <!-- Format Configuration -->
    <div class="subsection">
      <div class="subsection-header">
        <FileText class="subsection-icon" />
        <h4 class="subsection-title">Log Format</h4>
      </div>

      <div class="format-section">
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              bind:checked={settings.structured_logging}
              class="checkbox-input"
            />
            <span class="checkbox-custom"></span>
            <span class="checkbox-text">Structured Logging (JSON)</span>
          </label>
          <p class="form-help">Output logs in JSON format for better parsing and analysis</p>
        </div>

        <!-- Format Preview -->
        <div class="format-preview">
          <h5 class="preview-title">Log Format Preview</h5>
          <div class="preview-content">
            {#if settings.structured_logging}
              <pre class="log-example json"><code
                  >{JSON.stringify(
                    {
                      timestamp: '2025-07-05T10:30:00.000Z',
                      level: settings.level,
                      message: "Service 'web-app' started successfully",
                      service: 'wakedock',
                      module: 'docker.manager',
                      container_id: 'a1b2c3d4e5f6',
                      user_id: 123,
                    },
                    null,
                    2
                  )}</code
                ></pre>
            {:else}
              <pre class="log-example text"><code
                  >2025-07-05 10:30:00.000 [{settings.level}] docker.manager - Service 'web-app' started successfully (container: a1b2c3d4e5f6, user: 123)</code
                ></pre>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- Storage Estimation -->
    <div class="storage-estimation">
      <div class="estimation-header">
        <Archive class="estimation-icon" />
        <span class="estimation-title">Storage Estimation</span>
      </div>
      <div class="estimation-content">
        <div class="estimation-item">
          <span class="estimation-label">Estimated daily logs:</span>
          <span class="estimation-value">~{Math.round(settings.max_log_size * 0.1)} MB</span>
        </div>
        <div class="estimation-item">
          <span class="estimation-label">Total retention storage:</span>
          <span class="estimation-value"
            >~{Math.round(settings.max_log_size * 0.1 * settings.log_retention_days)} MB</span
          >
        </div>
        <div class="estimation-item">
          <span class="estimation-label">Log rotation frequency:</span>
          <span class="estimation-value"
            >Every {Math.max(1, Math.round(settings.max_log_size / (settings.max_log_size * 0.1)))} days</span
          >
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .settings-section {
    @apply space-y-6;
  }

  .section-header {
    @apply border-b border-slate-200 dark:border-slate-700 pb-4;
  }

  .section-title {
    @apply text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1;
  }

  .section-description {
    @apply text-sm text-slate-600 dark:text-slate-400;
  }

  .section-content {
    @apply space-y-8 pt-2;
  }

  .subsection {
    @apply space-y-4;
  }

  .subsection-header {
    @apply flex items-center gap-2 mb-4;
  }

  .subsection-icon {
    @apply w-5 h-5 text-blue-600 dark:text-blue-400;
  }

  .subsection-title {
    @apply text-base font-medium text-slate-900 dark:text-slate-100;
  }

  .log-level-selector {
    @apply space-y-4;
  }

  .level-options {
    @apply grid grid-cols-1 md:grid-cols-2 gap-3;
  }

  .level-option {
    @apply relative block p-4 border border-slate-200 dark:border-slate-700 rounded-lg cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors duration-200;
  }

  .level-option.selected {
    @apply border-blue-500 bg-blue-50 dark:bg-blue-900/20;
  }

  .level-input {
    @apply sr-only;
  }

  .level-content {
    @apply space-y-2;
  }

  .level-header {
    @apply flex items-center justify-between;
  }

  .level-label {
    @apply font-medium;
  }

  .level-value {
    @apply text-xs font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-slate-600 dark:text-slate-400;
  }

  .level-description {
    @apply text-sm text-slate-600 dark:text-slate-400;
  }

  .current-level-info {
    @apply flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg;
  }

  .info-icon {
    @apply w-4 h-4 text-blue-600 dark:text-blue-400;
  }

  .info-text {
    @apply text-sm text-blue-800 dark:text-blue-200;
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

  .form-input {
    @apply w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200;
  }

  .form-help {
    @apply text-xs text-slate-500 dark:text-slate-400;
  }

  .format-section {
    @apply space-y-4;
  }

  .checkbox-group {
    @apply space-y-2;
  }

  .checkbox-label {
    @apply flex items-center gap-3 cursor-pointer;
  }

  .checkbox-input {
    @apply sr-only;
  }

  .checkbox-custom {
    @apply w-5 h-5 border-2 border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 transition-colors duration-200;
  }

  .checkbox-input:checked + .checkbox-custom {
    @apply bg-blue-600 border-blue-600;
  }

  .checkbox-custom:after {
    @apply content-[''] absolute w-2 h-3 border-white border-r-2 border-b-2 transform rotate-45 scale-0 transition-transform duration-200;
    left: 7px;
    top: 2px;
  }

  .checkbox-input:checked + .checkbox-custom:after {
    @apply scale-100;
  }

  .checkbox-text {
    @apply text-sm font-medium text-slate-700 dark:text-slate-300;
  }

  .format-preview {
    @apply space-y-3;
  }

  .preview-title {
    @apply text-sm font-medium text-slate-900 dark:text-slate-100;
  }

  .preview-content {
    @apply bg-slate-900 dark:bg-slate-950 rounded-lg p-4 overflow-x-auto;
  }

  .log-example {
    @apply text-sm font-mono;
  }

  .log-example.json {
    @apply text-green-400;
  }

  .log-example.text {
    @apply text-slate-300;
  }

  .storage-estimation {
    @apply p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700;
  }

  .estimation-header {
    @apply flex items-center gap-2 mb-3;
  }

  .estimation-icon {
    @apply w-5 h-5 text-slate-600 dark:text-slate-400;
  }

  .estimation-title {
    @apply text-sm font-medium text-slate-900 dark:text-slate-100;
  }

  .estimation-content {
    @apply space-y-2;
  }

  .estimation-item {
    @apply flex justify-between text-sm;
  }

  .estimation-label {
    @apply text-slate-600 dark:text-slate-400;
  }

  .estimation-value {
    @apply font-medium text-slate-900 dark:text-slate-100;
  }
</style>
