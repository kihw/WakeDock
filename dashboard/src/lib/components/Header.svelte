<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { Menu } from 'lucide-svelte';
  import type { Writable } from 'svelte/store';
  import { generateCSRFToken } from '$lib/utils/validation';
  import { announceToScreenReader } from '$lib/utils/accessibility';

  import MainNavigation from './layout/Header/Navigation/MainNavigation.svelte';
  import MobileNavigation from './layout/Header/Navigation/MobileNavigation.svelte';
  import GlobalSearch from './layout/Header/Search/GlobalSearch.svelte';
  import UserMenu from './layout/Header/UserMenu/UserMenu.svelte';

  interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
    avatar?: string;
    role: string;
  }

  export let variant: 'default' | 'compact' | 'minimal' = 'default';
  export let sidebarOpen: Writable<boolean>;
  export let toggleMobileMenu: (() => void) | undefined = undefined;
  export let user: User | null = null;
  export let unreadNotifications: number = 0;

  let isMobileMenuOpen = false;
  let isSearchOpen = false;
  let globalSearch: GlobalSearch;
  let csrfToken = '';
  let keyboardNavigation = false;

  $: currentPath = $page.url.pathname;

  onMount(() => {
    csrfToken = generateCSRFToken();

    // Global keyboard shortcuts
    const handleKeydown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        switch (e.key.toLowerCase()) {
          case 'k':
            e.preventDefault();
            globalSearch?.openSearch();
            break;
          case 'b':
            e.preventDefault();
            toggleSidebar();
            break;
        }
      }

      // Escape key handling
      if (e.key === 'Escape') {
        if (isMobileMenuOpen) {
          isMobileMenuOpen = false;
        }
      }

      // Tab navigation detection
      if (e.key === 'Tab') {
        keyboardNavigation = true;
        document.body.classList.add('keyboard-navigation');
      }
    };

    const handleMouseDown = () => {
      keyboardNavigation = false;
      document.body.classList.remove('keyboard-navigation');
    };

    document.addEventListener('keydown', handleKeydown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeydown);
      document.removeEventListener('mousedown', handleMouseDown);
      csrfToken = '';
    };
  });

  function toggleSidebar() {
    sidebarOpen.update((open) => !open);
    announceToScreenReader($sidebarOpen ? 'Sidebar opened' : 'Sidebar closed');
  }

  function handleThemeToggle() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('wakedock_theme', newTheme);

    announceToScreenReader(`Theme changed to ${newTheme} mode`);
  }

  function handleLogout() {
    // Implement logout logic
    announceToScreenReader('Signing out...');
    // Redirect to logout endpoint or clear auth state
  }
</script>

<header
  class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40"
  class:compact={variant === 'compact'}
>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between items-center h-16">
      <!-- Left Section: Logo + Navigation -->
      <div class="flex items-center space-x-8">
        <!-- Logo -->
        <div class="flex items-center space-x-4">
          <!-- Sidebar Toggle (when sidebar exists) -->
          <button
            type="button"
            class="p-2 rounded-md text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500 lg:hidden"
            on:click={toggleSidebar}
            aria-label="Toggle sidebar"
          >
            <Menu class="h-5 w-5" />
          </button>

          <!-- Brand -->
          <a href="/" class="flex items-center space-x-2">
            <img src="/logo.png" alt="WakeDock" class="h-8 w-8" />
            <span class="text-xl font-bold text-gray-900 dark:text-white">WakeDock</span>
          </a>
        </div>

        <!-- Desktop Navigation -->
        {#if variant !== 'minimal'}
          <MainNavigation {currentPath} />
        {/if}
      </div>

      <!-- Center Section: Search -->
      {#if variant === 'default'}
        <div class="flex-1 max-w-lg mx-8">
          <GlobalSearch bind:this={globalSearch} bind:isOpen={isSearchOpen} />
        </div>
      {/if}

      <!-- Right Section: User Actions -->
      <div class="flex items-center space-x-4">
        <!-- User Menu -->
        <UserMenu
          {user}
          {unreadNotifications}
          on:themeToggle={handleThemeToggle}
          on:logout={handleLogout}
        />

        <!-- Mobile Menu Toggle -->
        <button
          type="button"
          class="p-2 rounded-md text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500 lg:hidden mobile-haptic-feedback"
          on:click={toggleMobileMenu || (() => (isMobileMenuOpen = !isMobileMenuOpen))}
          aria-label="Toggle mobile menu"
          aria-expanded={isMobileMenuOpen}
        >
          <Menu class="h-5 w-5" />
        </button>
      </div>
    </div>
  </div>

  <!-- Mobile Navigation -->
  {#if isMobileMenuOpen}
    <MobileNavigation {currentPath} on:close={() => (isMobileMenuOpen = false)} />
  {/if}
</header>

<style>
  .compact {
    @apply h-12;
  }

  .compact .h-16 {
    @apply h-12;
  }

  :global(.keyboard-navigation) :global(*:focus) {
    @apply outline-none ring-2 ring-green-500 ring-offset-2;
  }
</style>
