<!-- Two-Factor Authentication Section -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Shield, Clock } from 'lucide-svelte';
  import { safeSanitizeInput } from '$lib/utils/errorHandling';

  export let twoFactorCode = '';
  export let twoFactorErrors: string[] = [];
  export let loading = false;

  const dispatch = createEventDispatcher<{
    validateField: { field: string; value: string };
  }>();

  let twoFactorTouched = false;

  function handleTwoFactorBlur() {
    twoFactorTouched = true;
    const sanitizedCode = safeSanitizeInput(twoFactorCode);
    twoFactorCode = sanitizedCode;
    dispatch('validateField', { field: 'twoFactorCode', value: sanitizedCode });
  }

  function handleTwoFactorInput(event: Event) {
    const target = event.target as HTMLInputElement;
    // Only allow numeric input and limit to 6 characters
    const numericValue = target.value.replace(/\D/g, '').slice(0, 6);
    twoFactorCode = numericValue;
    target.value = numericValue;
  }

  // Auto-submit when 6 digits are entered
  $: if (twoFactorCode.length === 6 && !twoFactorErrors.length) {
    dispatch('validateField', { field: 'twoFactorCode', value: twoFactorCode });
  }
</script>

<div class="two-factor-section">
  <div class="two-factor-header">
    <div class="header-icon">
      <Shield class="w-5 h-5 text-blue-600 dark:text-blue-400" />
    </div>
    <div class="header-content">
      <h3 class="header-title">Two-Factor Authentication</h3>
      <p class="header-description">Enter the 6-digit code from your authenticator app</p>
    </div>
  </div>

  <div class="form-group">
    <label for="twoFactorCode" class="form-label">
      <Clock class="label-icon" />
      Authentication Code
    </label>
    <div class="input-container">
      <input
        id="twoFactorCode"
        name="twoFactorCode"
        type="text"
        bind:value={twoFactorCode}
        on:blur={handleTwoFactorBlur}
        on:input={handleTwoFactorInput}
        placeholder="000000"
        class="form-input code-input"
        class:error={twoFactorErrors.length > 0 && twoFactorTouched}
        class:disabled={loading}
        disabled={loading}
        autocomplete="one-time-code"
        aria-describedby={twoFactorErrors.length > 0 ? 'twoFactorCode-error' : undefined}
        aria-invalid={twoFactorErrors.length > 0}
        maxlength="6"
        pattern="[0-9]{6}"
        inputmode="numeric"
        required
      />
      <div class="code-progress">
        <div class="progress-bar">
          <div class="progress-fill" style="width: {(twoFactorCode.length / 6) * 100}%"></div>
        </div>
        <span class="progress-text">
          {twoFactorCode.length}/6
        </span>
      </div>
    </div>
    {#if twoFactorErrors.length > 0 && twoFactorTouched}
      <div id="twoFactorCode-error" class="form-error" role="alert">
        {#each twoFactorErrors as error}
          <span class="error-message">{error}</span>
        {/each}
      </div>
    {/if}
  </div>

  <div class="two-factor-help">
    <p class="help-text">
      <strong>Don't have access to your authenticator app?</strong>
    </p>
    <div class="help-actions">
      <button type="button" class="help-link" disabled={loading}> Use backup code </button>
      <span class="help-divider">•</span>
      <button type="button" class="help-link" disabled={loading}> Contact support </button>
    </div>
  </div>
</div>

<style>
  .two-factor-section {
    @apply p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg space-y-4;
  }

  .two-factor-header {
    @apply flex items-start gap-3;
  }

  .header-icon {
    @apply flex-shrink-0 w-10 h-10 bg-blue-100 dark:bg-blue-800 rounded-lg flex items-center justify-center;
  }

  .header-content {
    @apply flex-1;
  }

  .header-title {
    @apply text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1;
  }

  .header-description {
    @apply text-sm text-slate-600 dark:text-slate-400;
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

  .input-container {
    @apply relative;
  }

  .form-input {
    @apply w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200;
  }

  .code-input {
    @apply text-center text-xl font-mono tracking-widest;
  }

  .form-input.error {
    @apply border-red-500 dark:border-red-400 focus:ring-red-500;
  }

  .form-input.disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .code-progress {
    @apply absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2;
  }

  .progress-bar {
    @apply w-12 h-2 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden;
  }

  .progress-fill {
    @apply h-full bg-blue-500 transition-all duration-300;
  }

  .progress-text {
    @apply text-xs text-slate-500 dark:text-slate-400 font-mono;
  }

  .form-error {
    @apply space-y-1;
  }

  .error-message {
    @apply block text-sm text-red-600 dark:text-red-400;
  }

  .two-factor-help {
    @apply pt-4 border-t border-blue-200 dark:border-blue-800;
  }

  .help-text {
    @apply text-sm text-slate-600 dark:text-slate-400 mb-2;
  }

  .help-actions {
    @apply flex items-center gap-2;
  }

  .help-link {
    @apply text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline bg-transparent border-none cursor-pointer transition-colors duration-200;
  }

  .help-link:disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .help-divider {
    @apply text-slate-400 dark:text-slate-500;
  }
</style>
