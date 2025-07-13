<!-- Login Form Component -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { LoginCredentials, LoginResult } from '$lib/types/auth';
  import LoginHeader from './LoginHeader.svelte';
  import LoginFields from './LoginFields.svelte';
  import TwoFactorSection from './TwoFactorSection.svelte';
  import LoginActions from './LoginActions.svelte';
  import LoginFooter from './LoginFooter.svelte';

  export let loading = false;
  export let error = '';
  export let requiresTwoFactor = false;
  export let showTwoFactorInput = false;
  export let csrfToken = '';
  export let rateLimited = false;
  export let attemptCount = 0;

  const dispatch = createEventDispatcher<{
    submit: LoginCredentials;
    validateField: { field: string; value: string };
    rateLimit: { attempts: number };
  }>();

  let usernameOrEmail = '';
  let password = '';
  let twoFactorCode = '';
  let rememberMe = false;
  let formRef: HTMLFormElement;

  // Field validation state
  let usernameOrEmailErrors: string[] = [];
  let passwordErrors: string[] = [];
  let twoFactorErrors: string[] = [];

  function handleSubmit() {
    dispatch('submit', {
      usernameOrEmail,
      password,
      twoFactorCode: requiresTwoFactor ? twoFactorCode : undefined,
      rememberMe,
      csrfToken,
    });
  }

  function handleFieldValidation(field: string, value: string) {
    dispatch('validateField', { field, value });
  }

  // Clear sensitive data when needed
  export function clearSensitiveData() {
    password = '';
    twoFactorCode = '';
  }

  // Focus on two-factor input when enabled
  export function focusTwoFactor() {
    if (showTwoFactorInput) {
      setTimeout(() => {
        const twoFactorInput = document.getElementById('twoFactorCode');
        if (twoFactorInput) {
          twoFactorInput.focus();
        }
      }, 100);
    }
  }

  // Reactive updates for two-factor
  $: if (requiresTwoFactor && !showTwoFactorInput) {
    showTwoFactorInput = true;
    focusTwoFactor();
  }
</script>

<div class="login-container">
  <div class="login-card">
    <LoginHeader />

    <form bind:this={formRef} on:submit|preventDefault={handleSubmit} class="login-form" novalidate>
      <input type="hidden" name="csrfToken" value={csrfToken} />

      <LoginFields
        bind:usernameOrEmail
        bind:password
        bind:rememberMe
        {usernameOrEmailErrors}
        {passwordErrors}
        {loading}
        {rateLimited}
        on:validateField={(e) => handleFieldValidation(e.detail.field, e.detail.value)}
      />

      {#if showTwoFactorInput}
        <TwoFactorSection
          bind:twoFactorCode
          {twoFactorErrors}
          {loading}
          on:validateField={(e) => handleFieldValidation(e.detail.field, e.detail.value)}
        />
      {/if}

      <LoginActions {loading} {error} {rateLimited} {attemptCount} on:submit={handleSubmit} />
    </form>

    <LoginFooter />
  </div>
</div>

<style>
  .login-container {
    @apply min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 px-4 py-8;
  }

  .login-card {
    @apply w-full max-w-md bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 p-8;
  }

  .login-form {
    @apply space-y-6;
  }
</style>
