<!-- General Settings Section -->
<script lang="ts">
  export let settings: {
    app_name: string;
    app_description: string;
    default_domain: string;
    admin_email: string;
  };
</script>

<div class="settings-section">
  <div class="section-header">
    <h3 class="section-title">General Settings</h3>
    <p class="section-description">Configure basic application settings and information</p>
  </div>

  <div class="section-content">
    <div class="form-grid">
      <div class="form-group">
        <label for="app-name" class="form-label"> Application Name </label>
        <input
          id="app-name"
          type="text"
          bind:value={settings.app_name}
          class="form-input"
          placeholder="WakeDock"
        />
        <p class="form-help">The name displayed in the application header and title</p>
      </div>

      <div class="form-group">
        <label for="default-domain" class="form-label"> Default Domain </label>
        <input
          id="default-domain"
          type="text"
          bind:value={settings.default_domain}
          class="form-input"
          placeholder="localhost"
        />
        <p class="form-help">Default domain used for service proxying</p>
      </div>

      <div class="form-group col-span-full">
        <label for="app-description" class="form-label"> Application Description </label>
        <textarea
          id="app-description"
          bind:value={settings.app_description}
          rows="3"
          class="form-input"
          placeholder="Docker service wake-up and management system"
        ></textarea>
        <p class="form-help">Brief description of this WakeDock instance</p>
      </div>

      <div class="form-group">
        <label for="admin-email" class="form-label"> Administrator Email </label>
        <input
          id="admin-email"
          type="email"
          bind:value={settings.admin_email}
          class="form-input"
          placeholder="admin@example.com"
        />
        <p class="form-help">Email address for system notifications and alerts</p>
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
    @apply pt-2;
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
    @apply w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200;
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
</style>
