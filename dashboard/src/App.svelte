<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import Router, { link, push } from 'svelte-spa-router';
  import { wrap } from 'svelte-spa-router/wrap';

  // Stores
  import { authStore } from './lib/stores/auth';
  import { systemStore } from './lib/stores/system';
  import { toastStore } from './lib/stores/toastStore';
  import { uiLogger } from './lib/utils/logger';

  // Components
  import Navbar from './lib/components/Navbar.svelte';
  import Sidebar from './lib/components/Sidebar.svelte';
  import Toast from './lib/components/Toast.svelte';
  import LoadingSpinner from './lib/components/ui/atoms/LoadingSpinner.svelte';

  // Pages
  import Dashboard from './routes/+page.svelte';
  import Services from './routes/services/+page.svelte';
  import Monitoring from './routes/monitoring/+page.svelte';
  import Settings from './routes/settings/+page.svelte';
  import Login from './routes/login/+page.svelte';
  import NotFound from './routes/404/+page.svelte';

  // Routes configuration
  const routes = {
    '/': Dashboard,
    '/dashboard': Dashboard,
    '/services': Services,
    '/services/*': Services,
    '/monitoring': Monitoring,
    '/settings': Settings,
    '/settings/*': Settings,
    '/login': Login,
    '*': NotFound,
  };

  let sidebarOpen = writable(true);
  let loading = true;

  // Auth guard
  function authGuard(detail: any) {
    if (!$authStore.isAuthenticated && detail.location !== '/login') {
      push('/login');
      return false;
    }
    return true;
  }

  onMount(async () => {
    // Initialize app
    try {
      // Check if user is already authenticated
      const token = localStorage.getItem('auth_token');
      if (token) {
        await authStore.verifyToken();
      }

      // Load system info if authenticated
      if ($authStore.isAuthenticated) {
        await systemStore.loadSystemInfo();
      }
    } catch (error) {
      uiLogger.error('App', error, { context: 'initialization' });
      toastStore.add({
        type: 'error',
        message: 'Failed to initialize application',
      });
    } finally {
      loading = false;
    }
  });

  // Toggle sidebar
  function toggleSidebar() {
    sidebarOpen.update((value) => !value);
  }

  // Handle route changes
  function handleRouteChange(event: any) {
    const { location } = event.detail;

    // Close sidebar on mobile after navigation
    if (window.innerWidth < 768) {
      sidebarOpen.set(false);
    }

    // Update page title
    const pageTitles = {
      '/': 'Dashboard',
      '/dashboard': 'Dashboard',
      '/services': 'Services',
      '/monitoring': 'Monitoring',
      '/settings': 'Settings',
      '/login': 'Login',
    };

    const title = (pageTitles as any)[location] || 'WakeDock';
    document.title = `${title} - WakeDock`;
  }
</script>

<div class="app">
  {#if loading}
    <div class="loading-overlay">
      <LoadingSpinner size="large" />
      <p class="loading-text">Loading WakeDock...</p>
    </div>
  {:else}
    <!-- Main App Layout -->
    {#if $authStore.isAuthenticated}
      <!-- Authenticated Layout -->
      <div class="app-layout">
        <!-- Sidebar -->
        <Sidebar open={sidebarOpen} />

        <!-- Main Content Area -->
        <div class="main-content" class:shifted={$sidebarOpen}>
          <!-- Top Navigation -->
          <Navbar on:toggle-sidebar={toggleSidebar} />

          <!-- Page Content -->
          <main class="page-content">
            <Router {routes} on:routeLoaded={handleRouteChange} on:conditionsFailed={authGuard} />
          </main>
        </div>

        <!-- Mobile Sidebar Overlay -->
        {#if $sidebarOpen}
          <div
            class="sidebar-overlay"
            on:click={toggleSidebar}
            on:keydown={(e) => e.key === 'Escape' && toggleSidebar()}
          ></div>
        {/if}
      </div>
    {:else}
      <!-- Unauthenticated Layout -->
      <div class="auth-layout">
        <Router {routes} />
      </div>
    {/if}
  {/if}

  <!-- Toast Notifications -->
  <Toast />
</div>

<style>
  .app {
    min-height: 100vh;
    background-color: var(--color-background);
    color: var(--color-text);
  }

  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--color-background);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
  }

  .loading-text {
    margin-top: 1rem;
    font-size: 1.1rem;
    opacity: 0.7;
  }

  .app-layout {
    display: flex;
    min-height: 100vh;
    position: relative;
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    transition: margin-left 0.3s ease;
    margin-left: 0;
  }

  .main-content.shifted {
    margin-left: 250px;
  }

  .page-content {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
    background-color: var(--color-background-secondary);
  }

  .sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 40;
    display: none;
  }

  .auth-layout {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  }

  /* Responsive */
  @media (max-width: 768px) {
    .main-content.shifted {
      margin-left: 0;
    }

    .sidebar-overlay {
      display: block;
    }

    .page-content {
      padding: 1rem;
    }
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .app {
      background-color: var(--color-background-dark);
      color: var(--color-text-dark);
    }
  }
</style>
