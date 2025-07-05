<!-- Monitoring Settings Section -->
<script lang="ts">
  export let settings: {
    metrics_enabled: boolean;
    health_check_interval: number;
    alert_email: string;
    slack_webhook_url: string;
  };
</script>

<div class="settings-section">
  <div class="section-header">
    <h3 class="section-title">Monitoring Settings</h3>
    <p class="section-description">Configure monitoring, health checks, and alerting</p>
  </div>

  <div class="section-content">
    <div class="form-grid">
      <div class="form-group">
        <label for="health-check-interval" class="form-label">
          Health Check Interval (seconds)
        </label>
        <input
          id="health-check-interval"
          type="number"
          bind:value={settings.health_check_interval}
          class="form-input"
          placeholder="30"
          min="10"
          max="3600"
        />
        <p class="form-help">How often to check system health (minimum 10 seconds)</p>
      </div>

      <div class="form-group">
        <label for="alert-email" class="form-label"> Alert Email </label>
        <input
          id="alert-email"
          type="email"
          bind:value={settings.alert_email}
          class="form-input"
          placeholder="admin@example.com"
        />
        <p class="form-help">Email address for system alerts and notifications</p>
      </div>

      <div class="form-group col-span-2">
        <label for="slack-webhook" class="form-label"> Slack Webhook URL </label>
        <input
          id="slack-webhook"
          type="url"
          bind:value={settings.slack_webhook_url}
          class="form-input"
          placeholder="https://hooks.slack.com/services/..."
        />
        <p class="form-help">Optional Slack webhook for notifications</p>
      </div>

      <div class="form-group col-span-2">
        <div class="checkbox-group">
          <input
            id="metrics-enabled"
            type="checkbox"
            bind:checked={settings.metrics_enabled}
            class="form-checkbox"
          />
          <div class="checkbox-content">
            <label for="metrics-enabled" class="checkbox-label"> Enable Metrics Collection </label>
            <p class="checkbox-description">Collect system metrics for monitoring and analytics</p>
          </div>
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
    @apply pb-4 border-b border-gray-200;
  }

  .section-title {
    @apply text-lg font-semibold text-gray-900;
  }

  .section-description {
    @apply text-sm text-gray-600 mt-1;
  }

  .section-content {
    @apply pt-4;
  }

  .form-grid {
    @apply grid grid-cols-1 md:grid-cols-2 gap-6;
  }

  .form-group {
    @apply space-y-2;
  }

  .form-label {
    @apply block text-sm font-medium text-gray-700;
  }

  .form-input {
    @apply w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm;
  }

  .form-help {
    @apply text-xs text-gray-500;
  }

  .checkbox-group {
    @apply flex items-start space-x-3;
  }

  .form-checkbox {
    @apply h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1;
  }

  .checkbox-content {
    @apply flex-1;
  }

  .checkbox-label {
    @apply text-sm font-medium text-gray-900 cursor-pointer;
  }

  .checkbox-description {
    @apply text-xs text-gray-500 mt-1;
  }

  .col-span-2 {
    grid-column: span 1;
  }

  @media (min-width: 768px) {
    .col-span-2 {
      grid-column: span 2;
    }
  }
</style>
