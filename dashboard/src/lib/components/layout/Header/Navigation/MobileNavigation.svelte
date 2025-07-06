<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { slide } from 'svelte/transition';

  export let currentPath: string = '';

  const dispatch = createEventDispatcher<{
    close: void;
  }>();

  interface NavItem {
    title: string;
    url: string;
    icon?: string;
    badge?: number;
  }

  const navItems: NavItem[] = [
    { title: 'Dashboard', url: '/', icon: '🏠' },
    { title: 'Services', url: '/services', icon: '🐳' },
    { title: 'Containers', url: '/containers', icon: '📦' },
    { title: 'Images', url: '/images', icon: '💿' },
    { title: 'Networks', url: '/networks', icon: '🌐' },
    { title: 'Volumes', url: '/volumes', icon: '💾' },
    { title: 'Monitoring', url: '/monitoring', icon: '📊' },
    { title: 'Security', url: '/security', icon: '🔒' },
    { title: 'Settings', url: '/settings', icon: '⚙️' },
  ];

  function isActive(url: string): boolean {
    if (url === '/') {
      return currentPath === '/';
    }
    return currentPath.startsWith(url);
  }

  function handleLinkClick() {
    dispatch('close');
  }
</script>

<div
  class="lg:hidden fixed inset-0 z-50 bg-gray-600 bg-opacity-75"
  transition:slide={{ duration: 300 }}
  on:click={() => dispatch('close')}
  on:keydown={(e) => e.key === 'Escape' && dispatch('close')}
>
  <div
    class="fixed inset-y-0 left-0 max-w-xs w-full bg-white dark:bg-gray-800 shadow-xl"
    on:click|stopPropagation
  >
    <!-- Header -->
    <div
      class="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700"
    >
      <div class="flex items-center">
        <img src="/logo.png" alt="WakeDock" class="h-8 w-8" />
        <span class="ml-2 text-lg font-semibold text-gray-900 dark:text-white">WakeDock</span>
      </div>
      <button
        type="button"
        class="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500"
        on:click={() => dispatch('close')}
        aria-label="Close navigation"
      >
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="mt-5 px-2" aria-label="Mobile navigation">
      <div class="space-y-1">
        {#each navItems as item}
          <a
            href={item.url}
            class="group flex items-center px-2 py-2 text-base font-medium rounded-md transition-colors duration-200
              {isActive(item.url)
              ? 'bg-green-100 text-green-900 dark:bg-green-900 dark:text-green-100'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'}"
            aria-current={isActive(item.url) ? 'page' : undefined}
            on:click={handleLinkClick}
          >
            {#if item.icon}
              <span class="mr-3 text-lg" aria-hidden="true">{item.icon}</span>
            {/if}
            {item.title}
            {#if item.badge}
              <span
                class="ml-auto inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
              >
                {item.badge}
              </span>
            {/if}
          </a>
        {/each}
      </div>
    </nav>
  </div>
</div>
