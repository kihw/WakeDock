<!-- Login Form Fields -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Eye, EyeOff, User, Lock } from 'lucide-svelte';
  import { safeSanitizeInput } from '$lib/utils/errorHandling';
  import { validateEmail } from '$lib/utils/validation';

  export let usernameOrEmail = '';
  export let password = '';
  export let rememberMe = false;
  export let usernameOrEmailErrors: string[] = [];
  export let passwordErrors: string[] = [];
  export let loading = false;
  export let rateLimited = false;

  const dispatch = createEventDispatcher<{
    validateField: { field: string; value: string };
  }>();

  let showPassword = false;
  let usernameOrEmailTouched = false;
  let passwordTouched = false;

  function handleUsernameOrEmailBlur() {
    usernameOrEmailTouched = true;
    const sanitizedInput = safeSanitizeInput(usernameOrEmail);
    usernameOrEmail = sanitizedInput;
    dispatch('validateField', { field: 'usernameOrEmail', value: sanitizedInput });
  }

  function handlePasswordBlur() {
    passwordTouched = true;
    dispatch('validateField', { field: 'password', value: password });
  }

  function togglePasswordVisibility() {
    showPassword = !showPassword;
  }

  // Determine field type for username/email
  $: fieldType = usernameOrEmail.includes('@') ? 'email' : 'text';
  $: fieldPlaceholder = usernameOrEmail.includes('@') ? 'Enter your email' : 'Enter your username';
  $: fieldLabel = usernameOrEmail.includes('@') ? 'Email' : 'Username';
</script>

<div class="form-fields">
  <!-- Username/Email Field -->
  <div class="form-group">
    <label for="usernameOrEmail" class="form-label">
      <User class="label-icon" />
      {fieldLabel}
    </label>
    <div class="input-container">
      <input
        id="usernameOrEmail"
        name="usernameOrEmail"
        type="text"
        bind:value={usernameOrEmail}
        on:blur={handleUsernameOrEmailBlur}
        placeholder={fieldPlaceholder}
        class="form-input"
        class:error={usernameOrEmailErrors.length > 0 && usernameOrEmailTouched}
        class:disabled={loading || rateLimited}
        disabled={loading || rateLimited}
        autocomplete="username"
        aria-describedby={usernameOrEmailErrors.length > 0 ? 'usernameOrEmail-error' : undefined}
        aria-invalid={usernameOrEmailErrors.length > 0}
        required
      />
    </div>
    {#if usernameOrEmailErrors.length > 0 && usernameOrEmailTouched}
      <div id="usernameOrEmail-error" class="form-error" role="alert">
        {#each usernameOrEmailErrors as error}
          <span class="error-message">{error}</span>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Password Field -->
  <div class="form-group">
    <label for="password" class="form-label">
      <Lock class="label-icon" />
      Password
    </label>
    <div class="input-container">
      {#if showPassword}
        <input
          id="password"
          name="password"
          type="text"
          bind:value={password}
          on:blur={handlePasswordBlur}
          placeholder="Enter your password"
          class="form-input pr-12"
          class:error={passwordErrors.length > 0 && passwordTouched}
          class:disabled={loading || rateLimited}
          disabled={loading || rateLimited}
          required
          minlength="8"
          aria-describedby="password-error"
          autocomplete="current-password"
        />
      {:else}
        <input
          id="password"
          name="password"
          type="password"
          bind:value={password}
          on:blur={handlePasswordBlur}
          placeholder="Enter your password"
          class="form-input pr-12"
          class:error={passwordErrors.length > 0 && passwordTouched}
          class:disabled={loading || rateLimited}
          disabled={loading || rateLimited}
          required
          minlength="8"
          aria-describedby="password-error"
          autocomplete="current-password"
        />
      {/if}
      <button
        type="button"
        on:click={togglePasswordVisibility}
        class="password-toggle"
        aria-label={showPassword ? 'Hide password' : 'Show password'}
        disabled={loading || rateLimited}
      >
        {#if showPassword}
          <EyeOff class="toggle-icon" />
        {:else}
          <Eye class="toggle-icon" />
        {/if}
      </button>
    </div>
    {#if passwordErrors.length > 0 && passwordTouched}
      <div id="password-error" class="form-error" role="alert">
        {#each passwordErrors as error}
          <span class="error-message">{error}</span>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Remember Me -->
  <div class="form-group">
    <div class="checkbox-container">
      <input
        id="rememberMe"
        name="rememberMe"
        type="checkbox"
        bind:checked={rememberMe}
        class="form-checkbox"
        disabled={loading || rateLimited}
      />
      <label for="rememberMe" class="checkbox-label"> Remember me for 30 days </label>
    </div>
  </div>
</div>

<style>
  .form-fields {
    @apply space-y-4;
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

  .form-input.error {
    @apply border-red-500 dark:border-red-400 focus:ring-red-500;
  }

  .form-input.disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .password-toggle {
    @apply absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 transition-colors duration-200 bg-transparent border-none cursor-pointer p-1;
  }

  .password-toggle:disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .toggle-icon {
    @apply w-5 h-5;
  }

  .form-error {
    @apply space-y-1;
  }

  .error-message {
    @apply block text-sm text-red-600 dark:text-red-400;
  }

  .checkbox-container {
    @apply flex items-center gap-3;
  }

  .form-checkbox {
    @apply w-4 h-4 text-blue-600 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded focus:ring-blue-500 dark:focus:ring-blue-400 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .checkbox-label {
    @apply text-sm text-slate-700 dark:text-slate-300 cursor-pointer;
  }
</style>
