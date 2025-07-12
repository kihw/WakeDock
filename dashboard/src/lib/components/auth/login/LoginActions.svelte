<!-- Login Actions and Submit Button -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { LogIn, AlertCircle, Shield, Clock } from 'lucide-svelte';
  import LoadingSpinner from '$lib/components/ui/atoms/LoadingSpinner.svelte';

  export let loading = false;
  export let error = '';
  export let rateLimited = false;
  export let attemptCount = 0;

  const dispatch = createEventDispatcher<{
    submit: void;
  }>();

  function handleSubmit() {
    dispatch('submit');
  }

  // Calculate remaining attempts for rate limiting
  $: remainingAttempts = Math.max(0, 10 - attemptCount);
  $: showRateWarning = attemptCount >= 7 && !rateLimited;
</script>

<div class="login-actions">
  <!-- Error Display -->
  {#if error}
    <div class="error-container" role="alert">
      <div class="error-icon">
        <AlertCircle class="w-5 h-5 text-red-500" />
      </div>
      <div class="error-content">
        <p class="error-message">{error}</p>
        {#if showRateWarning}
          <p class="error-warning">
            {remainingAttempts} attempts remaining before temporary lockout
          </p>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Rate Limit Warning -->
  {#if showRateWarning && !error}
    <div class="warning-container">
      <div class="warning-icon">
        <Shield class="w-5 h-5 text-amber-500" />
      </div>
      <div class="warning-content">
        <p class="warning-message">
          Security Warning: {remainingAttempts} attempts remaining
        </p>
        <p class="warning-description">
          Account will be temporarily locked after {remainingAttempts} more failed attempts
        </p>
      </div>
    </div>
  {/if}

  <!-- Rate Limited State -->
  {#if rateLimited}
    <div class="rate-limit-container">
      <div class="rate-limit-icon">
        <Clock class="w-5 h-5 text-red-500" />
      </div>
      <div class="rate-limit-content">
        <p class="rate-limit-message">Account Temporarily Locked</p>
        <p class="rate-limit-description">
          Too many failed attempts. Please try again in 5 minutes.
        </p>
      </div>
    </div>
  {/if}

  <!-- Submit Button -->
  <button
    type="submit"
    on:click={handleSubmit}
    class="submit-button"
    class:loading
    class:disabled={loading || rateLimited}
    disabled={loading || rateLimited}
  >
    {#if loading}
      <LoadingSpinner size="sm" />
      <span>Signing in...</span>
    {:else}
      <LogIn class="button-icon" />
      <span>Sign in</span>
    {/if}
  </button>

  <!-- Additional Actions -->
  <div class="additional-actions">
    <a href="/auth/forgot-password" class="action-link" class:disabled={loading || rateLimited}>
      Forgot your password?
    </a>
    <span class="action-divider">•</span>
    <a href="/auth/register" class="action-link" class:disabled={loading || rateLimited}>
      Create an account
    </a>
  </div>
</div>

<style>
  .login-actions {
    @apply space-y-4;
  }

  .error-container {
    @apply p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3;
  }

  .error-icon {
    @apply flex-shrink-0 w-8 h-8 bg-red-100 dark:bg-red-800 rounded-lg flex items-center justify-center;
  }

  .error-content {
    @apply flex-1 space-y-1;
  }

  .error-message {
    @apply text-sm font-medium text-red-800 dark:text-red-200;
  }

  .error-warning {
    @apply text-xs text-red-600 dark:text-red-300;
  }

  .warning-container {
    @apply p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg flex items-start gap-3;
  }

  .warning-icon {
    @apply flex-shrink-0 w-8 h-8 bg-amber-100 dark:bg-amber-800 rounded-lg flex items-center justify-center;
  }

  .warning-content {
    @apply flex-1 space-y-1;
  }

  .warning-message {
    @apply text-sm font-medium text-amber-800 dark:text-amber-200;
  }

  .warning-description {
    @apply text-xs text-amber-600 dark:text-amber-300;
  }

  .rate-limit-container {
    @apply p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3;
  }

  .rate-limit-icon {
    @apply flex-shrink-0 w-8 h-8 bg-red-100 dark:bg-red-800 rounded-lg flex items-center justify-center;
  }

  .rate-limit-content {
    @apply flex-1 space-y-1;
  }

  .rate-limit-message {
    @apply text-sm font-medium text-red-800 dark:text-red-200;
  }

  .rate-limit-description {
    @apply text-xs text-red-600 dark:text-red-300;
  }

  .submit-button {
    @apply w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-slate-800;
  }

  .submit-button.loading {
    @apply bg-blue-500 cursor-not-allowed;
  }

  .submit-button.disabled {
    @apply bg-slate-400 dark:bg-slate-600 cursor-not-allowed;
  }

  .button-icon {
    @apply w-5 h-5;
  }

  .additional-actions {
    @apply flex items-center justify-center gap-2 text-sm;
  }

  .action-link {
    @apply text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline transition-colors duration-200;
  }

  .action-link.disabled {
    @apply opacity-50 cursor-not-allowed pointer-events-none;
  }

  .action-divider {
    @apply text-slate-400 dark:text-slate-500;
  }
</style>
