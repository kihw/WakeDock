<script lang="ts">
  // 404 Not Found Page
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';

  let countdown = 5;
  let intervalId: number;

  onMount(() => {
    intervalId = window.setInterval(() => {
      countdown--;
      if (countdown <= 0) {
        clearInterval(intervalId);
        push('/');
      }
    }, 1000) as unknown as number;

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  });
</script>

<svelte:head>
  <title>Page Not Found - WakeDock</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
  <div class="max-w-md w-full space-y-8">
    <div class="text-center">
      <h1 class="text-9xl font-bold text-gray-300">404</h1>
      <h2 class="mt-6 text-3xl font-extrabold text-gray-900">Page not found</h2>
      <p class="mt-2 text-sm text-gray-600">Sorry, we couldn't find the page you're looking for.</p>
      <div class="mt-6 flex flex-col space-y-4">
        <button
          type="button"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          on:click={() => push('/')}
        >
          Go back to dashboard
        </button>
        <p class="text-sm text-gray-500">
          Redirecting automatically in {countdown} seconds...
        </p>
      </div>
    </div>
  </div>
</div>
