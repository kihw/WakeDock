<!-- Login Form Header -->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { debugConfig } from '$lib/config/environment';

  // Debug configuration display
  $: isDevelopment = debugConfig.environment === 'development';
</script>

<div class="login-header">
  <div class="brand-container">
    <button on:click={() => goto('/')} class="brand-link" aria-label="Go to home page">
      <img src="/logo.png" alt="WakeDock" class="brand-logo" />
      <span class="brand-text">WakeDock</span>
    </button>
  </div>

  <div class="login-title">
    <h1>Welcome back</h1>
    <p>Sign in to your account to continue</p>
  </div>

  {#if isDevelopment}
    <div class="development-notice">
      <span class="development-badge">DEV</span>
      <span class="development-text">Development Mode</span>
    </div>
  {/if}
</div>

<style>
  .login-header {
    @apply text-center mb-8;
  }

  .brand-container {
    @apply mb-6;
  }

  .brand-link {
    @apply inline-flex items-center gap-3 text-slate-900 dark:text-slate-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200 bg-transparent border-none cursor-pointer;
  }

  .brand-logo {
    @apply w-12 h-12;
  }

  .brand-text {
    @apply text-2xl font-bold;
  }

  .login-title h1 {
    @apply text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2;
  }

  .login-title p {
    @apply text-slate-600 dark:text-slate-400;
  }

  .development-notice {
    @apply mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg;
  }

  .development-badge {
    @apply inline-block bg-amber-100 dark:bg-amber-800 text-amber-800 dark:text-amber-100 px-2 py-1 rounded text-xs font-semibold mr-2;
  }

  .development-text {
    @apply text-amber-700 dark:text-amber-300 text-sm;
  }
</style>
