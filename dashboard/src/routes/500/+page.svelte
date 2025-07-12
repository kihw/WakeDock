<script lang="ts">
  // 500 Internal Server Error Page
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Button from '$lib/components/ui/atoms/Button.svelte';

  let retryCount = 0;
  const maxRetries = 3;

  function handleRetry() {
    retryCount++;
    if (retryCount >= maxRetries) {
      goto('/');
    } else {
      // Attempt to reload the previous page or go home
      window.location.reload();
    }
  }

  function goHome() {
    goto('/');
  }

  onMount(() => {
    // Log error for monitoring
    console.error('500 Internal Server Error page loaded');
  });
</script>

<svelte:head>
  <title>Server Error - WakeDock</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
  <div class="max-w-md w-full space-y-8">
    <div class="text-center">
      <div class="mx-auto w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mb-8">
        <svg class="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      
      <h1 class="text-6xl font-bold text-gray-300 mb-4">500</h1>
      <h2 class="text-3xl font-extrabold text-gray-900 mb-2">Internal Server Error</h2>
      <p class="text-sm text-gray-600 mb-8">
        Something went wrong on our end. We're working to fix it.
      </p>

      <div class="space-y-4">
        <Button 
          variant="primary" 
          fullWidth 
          on:click={handleRetry}
          disabled={retryCount >= maxRetries}
        >
          {#if retryCount >= maxRetries}
            Redirecting to Dashboard...
          {:else}
            Try Again ({maxRetries - retryCount} attempts left)
          {/if}
        </Button>

        <Button variant="secondary" fullWidth on:click={goHome}>
          Return to Dashboard
        </Button>

        <div class="text-xs text-gray-400 mt-6">
          <p>Error ID: {Date.now().toString(36)}</p>
          <p>If this problem persists, please contact support.</p>
        </div>
      </div>
    </div>
  </div>
</div>