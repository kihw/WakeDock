<script lang="ts">
  // Login Page
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { auth } from '$lib/stores/auth';
  import Button from '$lib/components/ui/atoms/Button.svelte';
  import Input from '$lib/components/forms/Input.svelte';
  import { generateCSRFToken } from '$lib/utils/validation';

  let username = '';
  let password = '';
  let loading = false;
  let error = '';
  let csrfToken = '';

  onMount(() => {
    // Redirect if already authenticated
    if ($auth.isAuthenticated) {
      push('/');
      return;
    }

    // Generate CSRF token
    csrfToken = generateCSRFToken();
  });

  async function handleLogin(event: Event) {
    event.preventDefault();

    if (!username || !password) {
      error = 'Please enter both username and password';
      return;
    }

    loading = true;
    error = '';

    try {
      await auth.login(username, password);
      push('/');
    } catch (err: any) {
      error = err.message || 'Login failed';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Login - WakeDock</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
  <div class="max-w-md w-full space-y-8">
    <div>
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Sign in to WakeDock</h2>
      <p class="mt-2 text-center text-sm text-gray-600">Manage your services and containers</p>
    </div>

    <form class="mt-8 space-y-6" on:submit={handleLogin}>
      <input type="hidden" name="csrf_token" value={csrfToken} />

      <div class="space-y-4">
        <Input
          label="Username"
          id="username"
          type="text"
          required
          bind:value={username}
          autocomplete="username"
          placeholder="Enter your username"
        />

        <Input
          label="Password"
          id="password"
          type="password"
          required
          bind:value={password}
          autocomplete="current-password"
          placeholder="Enter your password"
        />
      </div>

      {#if error}
        <div class="rounded-md bg-red-50 p-4">
          <div class="text-sm text-red-700">{error}</div>
        </div>
      {/if}

      <div>
        <Button type="submit" variant="primary" {loading} className="w-full flex justify-center">
          {loading ? 'Signing in...' : 'Sign in'}
        </Button>
      </div>
    </form>
  </div>
</div>
