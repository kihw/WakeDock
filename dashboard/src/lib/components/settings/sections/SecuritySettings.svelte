<!-- Security Settings Section -->
<script lang="ts">
  import { Shield, Clock, Key, AlertTriangle } from 'lucide-svelte';

  export let settings: {
    session_timeout: number;
    max_login_attempts: number;
    password_min_length: number;
    require_strong_passwords: boolean;
    rate_limit_enabled: boolean;
    rate_limit_requests: number;
    rate_limit_window: number;
  };

  // Convert seconds to minutes for display
  $: sessionTimeoutMinutes = Math.floor(settings.session_timeout / 60);
  $: rateLimitWindowMinutes = Math.floor(settings.rate_limit_window / 60);

  function updateSessionTimeout(minutes: number) {
    settings.session_timeout = minutes * 60;
  }

  function updateRateLimitWindow(minutes: number) {
    settings.rate_limit_window = minutes * 60;
  }
</script>

<div class="settings-section">
  <div class="section-header">
    <h3 class="section-title">Security Settings</h3>
    <p class="section-description">
      Configure authentication, authorization, and security policies
    </p>
  </div>

  <div class="section-content">
    <!-- Authentication Settings -->
    <div class="subsection">
      <div class="subsection-header">
        <Key class="subsection-icon" />
        <h4 class="subsection-title">Authentication</h4>
      </div>

      <div class="form-grid">
        <div class="form-group">
          <label for="session-timeout" class="form-label"> Session Timeout (minutes) </label>
          <input
            id="session-timeout"
            type="number"
            value={sessionTimeoutMinutes}
            on:input={(e) => updateSessionTimeout(parseInt(e.target.value) || 60)}
            class="form-input"
            min="5"
            max="1440"
            placeholder="60"
          />
          <p class="form-help">Automatically log out users after this period of inactivity</p>
        </div>

        <div class="form-group">
          <label for="max-login-attempts" class="form-label"> Max Login Attempts </label>
          <input
            id="max-login-attempts"
            type="number"
            bind:value={settings.max_login_attempts}
            class="form-input"
            min="3"
            max="20"
            placeholder="5"
          />
          <p class="form-help">Lock account after this many failed login attempts</p>
        </div>
      </div>
    </div>

    <!-- Password Policy -->
    <div class="subsection">
      <div class="subsection-header">
        <Shield class="subsection-icon" />
        <h4 class="subsection-title">Password Policy</h4>
      </div>

      <div class="form-grid">
        <div class="form-group">
          <label for="password-min-length" class="form-label"> Minimum Password Length </label>
          <input
            id="password-min-length"
            type="number"
            bind:value={settings.password_min_length}
            class="form-input"
            min="6"
            max="128"
            placeholder="8"
          />
          <p class="form-help">Minimum number of characters required for passwords</p>
        </div>

        <div class="form-group">
          <div class="checkbox-group">
            <label class="checkbox-label">
              <input
                type="checkbox"
                bind:checked={settings.require_strong_passwords}
                class="checkbox-input"
              />
              <span class="checkbox-custom"></span>
              <span class="checkbox-text">Require Strong Passwords</span>
            </label>
            <p class="form-help">
              Enforce complex password requirements (uppercase, lowercase, numbers, symbols)
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Rate Limiting -->
    <div class="subsection">
      <div class="subsection-header">
        <Clock class="subsection-icon" />
        <h4 class="subsection-title">Rate Limiting</h4>
      </div>

      <div class="rate-limit-container">
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              bind:checked={settings.rate_limit_enabled}
              class="checkbox-input"
            />
            <span class="checkbox-custom"></span>
            <span class="checkbox-text">Enable Rate Limiting</span>
          </label>
          <p class="form-help">Protect against brute force attacks and API abuse</p>
        </div>

        {#if settings.rate_limit_enabled}
          <div class="form-grid">
            <div class="form-group">
              <label for="rate-limit-requests" class="form-label"> Requests per Window </label>
              <input
                id="rate-limit-requests"
                type="number"
                bind:value={settings.rate_limit_requests}
                class="form-input"
                min="10"
                max="1000"
                placeholder="100"
              />
              <p class="form-help">Maximum requests allowed per time window</p>
            </div>

            <div class="form-group">
              <label for="rate-limit-window" class="form-label"> Time Window (minutes) </label>
              <input
                id="rate-limit-window"
                type="number"
                value={rateLimitWindowMinutes}
                on:input={(e) => updateRateLimitWindow(parseInt(e.target.value) || 60)}
                class="form-input"
                min="1"
                max="1440"
                placeholder="60"
              />
              <p class="form-help">Time window for rate limit calculation</p>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Security Notice -->
    <div class="security-notice">
      <div class="notice-header">
        <AlertTriangle class="notice-icon" />
        <span class="notice-title">Security Recommendations</span>
      </div>
      <ul class="notice-list">
        <li>Enable strong password requirements for better security</li>
        <li>Set session timeout to 60 minutes or less for production</li>
        <li>Enable rate limiting to prevent abuse</li>
        <li>Regularly review and update security settings</li>
      </ul>
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

  .rate-limit-container {
    @apply space-y-4;
  }

  .security-notice {
    @apply p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg;
  }

  .notice-header {
    @apply flex items-center gap-2 mb-3;
  }

  .notice-icon {
    @apply w-5 h-5 text-amber-600 dark:text-amber-400;
  }

  .notice-title {
    @apply text-sm font-medium text-amber-800 dark:text-amber-200;
  }

  .notice-list {
    @apply space-y-1 text-sm text-amber-700 dark:text-amber-300;
  }

  .notice-list li {
    @apply relative pl-4;
  }

  .notice-list li:before {
    @apply content-['•'] absolute left-0 text-amber-600 dark:text-amber-400;
  }
</style>
