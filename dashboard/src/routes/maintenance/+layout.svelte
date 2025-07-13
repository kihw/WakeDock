<!-- Maintenance Layout -->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  // Check authentication
  onMount(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      goto('/login');
      return;
    }
  });
</script>

<div class="min-h-screen bg-gray-50">
  <!-- Navigation breadcrumb -->
  <nav class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center space-x-4">
          <a href="/" class="text-blue-600 hover:text-blue-800 font-medium"> ← Dashboard </a>
          <span class="text-gray-300">/</span>
          <span class="text-gray-900 font-medium">Maintenance</span>
        </div>

        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-500">WakeDock System Maintenance</span>
        </div>
      </div>
    </div>
  </nav>

  <!-- Main content -->
  <main>
    <slot />
  </main>
</div>
