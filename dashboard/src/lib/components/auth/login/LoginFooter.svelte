<!-- Login Footer -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { Globe, Shield, Clock } from 'lucide-svelte';

  let currentYear = new Date().getFullYear();
  let buildVersion = 'v1.0.0';
  let lastUpdate = '';

  onMount(() => {
    // Get build info from environment if available
    try {
      buildVersion = process.env.PUBLIC_BUILD_VERSION || 'v1.0.0';
      lastUpdate = process.env.PUBLIC_BUILD_DATE || new Date().toISOString().split('T')[0];
    } catch (e) {
      // Fallback for client-side
      lastUpdate = new Date().toISOString().split('T')[0];
    }
  });
</script>

<div class="login-footer">
  <div class="footer-content">
    <div class="footer-links">
      <a href="https://github.com/wakedock/wakedock/blob/main/PRIVACY.md" target="_blank" class="footer-link"> Privacy Policy </a>
      <span class="footer-divider">•</span>
      <a href="https://github.com/wakedock/wakedock/blob/main/TERMS.md" target="_blank" class="footer-link"> Terms of Service </a>
      <span class="footer-divider">•</span>
      <a href="https://github.com/wakedock/wakedock/issues" target="_blank" class="footer-link"> Support </a>
    </div>

    <div class="footer-info">
      <div class="info-item">
        <Globe class="info-icon" />
        <span class="info-text">
          <a href="https://github.com/wakedock/wakedock/blob/main/README.md" target="_blank" class="info-link">Documentation</a>
        </span>
      </div>
      <div class="info-item">
        <Shield class="info-icon" />
        <span class="info-text">Secure Login</span>
      </div>
      <div class="info-item">
        <Clock class="info-icon" />
        <span class="info-text">Updated {lastUpdate}</span>
      </div>
    </div>

    <div class="footer-bottom">
      <p class="copyright">
        © {currentYear} WakeDock. All rights reserved.
      </p>
      <p class="version">
        {buildVersion}
      </p>
    </div>
  </div>
</div>

<style>
  .login-footer {
    @apply mt-8 pt-6 border-t border-slate-200 dark:border-slate-700;
  }

  .footer-content {
    @apply space-y-4;
  }

  .footer-links {
    @apply flex items-center justify-center gap-2 text-sm;
  }

  .footer-link {
    @apply text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors duration-200;
  }

  .footer-divider {
    @apply text-slate-400 dark:text-slate-500;
  }

  .footer-info {
    @apply flex items-center justify-center gap-6 text-xs;
  }

  .info-item {
    @apply flex items-center gap-2;
  }

  .info-icon {
    @apply w-3 h-3 text-slate-500 dark:text-slate-400;
  }

  .info-text {
    @apply text-slate-600 dark:text-slate-400;
  }

  .info-link {
    @apply text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors duration-200;
  }

  .footer-bottom {
    @apply flex items-center justify-between text-xs text-slate-500 dark:text-slate-400;
  }

  .copyright {
    @apply text-center flex-1;
  }

  .version {
    @apply absolute right-0 text-slate-400 dark:text-slate-500;
  }

  @media (max-width: 640px) {
    .footer-info {
      @apply flex-col gap-2;
    }

    .footer-bottom {
      @apply flex-col gap-2;
    }

    .version {
      @apply relative right-auto;
    }
  }
</style>
