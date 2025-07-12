<script lang="ts">
  // 503 Service Unavailable Page
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Button from '$lib/components/ui/atoms/Button.svelte';
  import LoadingSpinner from '$lib/components/ui/atoms/LoadingSpinner.svelte';

  let isChecking = false;
  let lastCheckTime = Date.now();
  let autoRetryEnabled = true;
  let retryInterval: number;

  async function checkServiceStatus(): Promise<boolean> {
    try {
      const response = await fetch('/health', { method: 'GET' });
      return response.ok;
    } catch {
      return false;
    }
  }

  async function handleRetry() {
    isChecking = true;
    const isAvailable = await checkServiceStatus();
    
    if (isAvailable) {
      goto('/');
    } else {
      isChecking = false;
      lastCheckTime = Date.now();
    }
  }

  function toggleAutoRetry() {
    autoRetryEnabled = !autoRetryEnabled;
    
    if (autoRetryEnabled) {
      startAutoRetry();
    } else {
      clearInterval(retryInterval);
    }
  }

  function startAutoRetry() {
    retryInterval = window.setInterval(async () => {
      if (!isChecking) {
        const isAvailable = await checkServiceStatus();
        if (isAvailable) {
          goto('/');
        }
        lastCheckTime = Date.now();
      }
    }, 10000); // Check every 10 seconds
  }

  onMount(() => {
    if (autoRetryEnabled) {
      startAutoRetry();
    }

    return () => {
      if (retryInterval) {
        clearInterval(retryInterval);
      }
    };
  });
</script>

<svelte:head>
  <title>Service Unavailable - WakeDock</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
  <div class="max-w-md w-full space-y-8">
    <div class="text-center">
      <div class="mx-auto w-24 h-24 bg-yellow-100 rounded-full flex items-center justify-center mb-8">
        <svg class="w-12 h-12 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      
      <h1 class="text-6xl font-bold text-gray-300 mb-4">503</h1>
      <h2 class="text-3xl font-extrabold text-gray-900 mb-2">Service Unavailable</h2>
      <p class="text-sm text-gray-600 mb-8">
        WakeDock is temporarily unavailable for maintenance or due to high load.
      </p>

      <div class="space-y-4">
        <Button 
          variant="primary" 
          fullWidth 
          on:click={handleRetry}
          disabled={isChecking}
        >
          {#if isChecking}
            <LoadingSpinner size="sm" class="mr-2" />
            Checking Status...
          {:else}
            Check Status
          {/if}
        </Button>

        <div class="flex items-center justify-center space-x-2">
          <input 
            type="checkbox" 
            id="autoRetry" 
            bind:checked={autoRetryEnabled}
            on:change={toggleAutoRetry}
            class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
          >
          <label for="autoRetry" class="text-sm text-gray-600">
            Auto-retry every 10 seconds
          </label>
        </div>

        <div class="text-xs text-gray-400 mt-6">
          <p>Last checked: {new Date(lastCheckTime).toLocaleTimeString()}</p>
          <p>The service should be back shortly. Thank you for your patience.</p>
        </div>
      </div>
    </div>
  </div>
</div>