<!-- Refactored Modular Sidebar Component -->
<script lang="ts">
  import { onMount } from 'svelte';
  import type { Writable } from 'svelte/store';
  import { page } from '$app/stores';
  import { Home, Container, Activity, BarChart3, Users, Shield, Settings } from 'lucide-svelte';
  import { manageFocus, announceToScreenReader, trapFocus } from '$lib/utils/accessibility';
  import { sanitizeInput } from '$lib/utils/validation';

  // Import modular components
  import SidebarHeader from './sidebar/SidebarHeader.svelte';
  import QuickActions from './sidebar/QuickActions.svelte';
  import NavigationSection from './sidebar/NavigationSection.svelte';
  import SystemStatus from './sidebar/SystemStatus.svelte';
  import SidebarFooter from './sidebar/SidebarFooter.svelte';

  export let open: Writable<boolean>;

  let sidebarElement: HTMLElement;
  let navElement: HTMLElement;
  let focusedItemIndex = -1;
  let previousFocus: HTMLElement;
  let keyboardNavigation = false;

  // Navigation configuration
  const mainNavItems = [
    {
      label: 'Dashboard',
      href: '/',
      icon: Home,
      description: 'Overview and metrics',
      shortcut: '1',
    },
    {
      label: 'Services',
      href: '/services',
      icon: Container,
      description: 'Manage containers',
      shortcut: '2',
    },
    {
      label: 'Monitoring',
      href: '/monitoring',
      icon: Activity,
      description: 'System health',
      shortcut: '3',
    },
    {
      label: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
      description: 'Usage insights',
      shortcut: '4',
    },
  ];

  const adminNavItems = [
    {
      label: 'Users',
      href: '/users',
      icon: Users,
      description: 'User management',
      shortcut: '5',
    },
    {
      label: 'Security',
      href: '/security',
      icon: Shield,
      description: 'Access control',
      shortcut: '6',
    },
    {
      label: 'Settings',
      href: '/settings',
      icon: Settings,
      description: 'System configuration',
      shortcut: '7',
    },
  ];

  $: currentPath = $page.url.pathname;

  // System stats
  let systemStats = {
    cpu: 24,
    memory: 68,
    uptime: sanitizeInput('14h 32m'),
  };

  // Event handlers
  function handleKeydown(event: KeyboardEvent) {
    if (!$open) return;

    switch (event.key) {
      case 'Escape':
        closeSidebar();
        break;
      case 'ArrowDown':
        event.preventDefault();
        focusNextItem();
        break;
      case 'ArrowUp':
        event.preventDefault();
        focusPreviousItem();
        break;
      case 'Home':
        event.preventDefault();
        focusFirstItem();
        break;
      case 'End':
        event.preventDefault();
        focusLastItem();
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        activateFocusedItem();
        break;
    }

    // Number shortcuts
    const num = parseInt(event.key);
    if (num >= 1 && num <= 7) {
      event.preventDefault();
      navigateToItem(num - 1);
    }
  }

  function focusNextItem() {
    const items = navElement.querySelectorAll('.nav-item');
    focusedItemIndex = Math.min(focusedItemIndex + 1, items.length - 1);
    (items[focusedItemIndex] as HTMLElement).focus();
  }

  function focusPreviousItem() {
    const items = navElement.querySelectorAll('.nav-item');
    focusedItemIndex = Math.max(focusedItemIndex - 1, 0);
    (items[focusedItemIndex] as HTMLElement).focus();
  }

  function focusFirstItem() {
    const items = navElement.querySelectorAll('.nav-item');
    focusedItemIndex = 0;
    (items[0] as HTMLElement).focus();
  }

  function focusLastItem() {
    const items = navElement.querySelectorAll('.nav-item');
    focusedItemIndex = items.length - 1;
    (items[focusedItemIndex] as HTMLElement).focus();
  }

  function activateFocusedItem() {
    const items = navElement.querySelectorAll('.nav-item');
    const focusedItem = items[focusedItemIndex] as HTMLAnchorElement;
    if (focusedItem) {
      focusedItem.click();
    }
  }

  function navigateToItem(index: number) {
    const allItems = [...mainNavItems, ...adminNavItems];
    if (index >= 0 && index < allItems.length) {
      const item = allItems[index];
      announceToScreenReader(`Navigating to ${item.label}`);
      window.location.href = item.href;
    }
  }

  function closeSidebar() {
    open.set(false);
    if (previousFocus) {
      manageFocus(previousFocus);
    }
    announceToScreenReader('Sidebar closed');
  }

  function handleNavClick(item: any) {
    // Close sidebar on mobile after navigation
    if (window.innerWidth <= 768) {
      open.set(false);
    }
  }

  function handleQuickDeploy() {
    // Quick deploy functionality
    announceToScreenReader('Quick deploy initiated');
    // Add your quick deploy logic here
  }

  // Watch for sidebar open/close
  $: {
    if ($open) {
      previousFocus = document.activeElement as HTMLElement;

      // Focus management
      setTimeout(() => {
        if (sidebarElement) {
          trapFocus(sidebarElement);
          const firstNavItem = sidebarElement.querySelector('.nav-item') as HTMLElement;
          if (firstNavItem) {
            manageFocus(firstNavItem);
            focusedItemIndex = 0;
          }
        }
      }, 100);

      announceToScreenReader(
        `Sidebar opened. Use arrow keys to navigate. Press Enter to select. ${mainNavItems.length + adminNavItems.length} navigation items available.`
      );
    }
  }

  onMount(() => {
    // Keyboard navigation detection
    const handleGlobalKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        keyboardNavigation = true;
        document.body.classList.add('keyboard-navigation');
      }
    };

    const handleMouseDown = () => {
      keyboardNavigation = false;
      document.body.classList.remove('keyboard-navigation');
    };

    document.addEventListener('keydown', handleGlobalKeydown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleGlobalKeydown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  });
</script>

<aside
  bind:this={sidebarElement}
  class="sidebar"
  class:open={$open}
  role="navigation"
  aria-label="Main navigation"
  aria-hidden={!$open}
  on:keydown={handleKeydown}
  tabindex="-1"
  id="sidebar"
>
  <!-- Header Section -->
  <SidebarHeader onClose={closeSidebar} />

  <!-- Quick Actions -->
  <QuickActions onQuickDeploy={handleQuickDeploy} />

  <!-- Navigation -->
  <nav bind:this={navElement} class="sidebar-nav" aria-label="Main navigation menu">
    <NavigationSection
      title="Main"
      titleId="main-nav-title"
      items={mainNavItems}
      {currentPath}
      sectionType="main"
      onNavigate={handleNavClick}
    />

    <NavigationSection
      title="Administration"
      titleId="admin-nav-title"
      items={adminNavItems}
      {currentPath}
      sectionType="admin"
      onNavigate={handleNavClick}
    />
  </nav>

  <!-- System Status -->
  <SystemStatus {systemStats} />

  <!-- Footer -->
  <SidebarFooter />
</aside>

{#if $open}
  <div
    class="overlay"
    on:click={closeSidebar}
    on:keydown={(e) => e.key === 'Escape' && closeSidebar()}
    aria-label="Close sidebar"
    role="button"
    tabindex="0"
  ></div>
{/if}

<style>
  .sidebar {
    position: fixed;
    top: 0;
    left: -320px;
    width: 320px;
    height: 100vh;
    background: var(--gradient-surface);
    border-right: 1px solid var(--color-border);
    z-index: 50;
    transition: left var(--transition-normal);
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: var(--shadow-xl);
  }

  .sidebar.open {
    left: 0;
  }

  .sidebar-nav {
    flex: 1;
    padding: var(--spacing-lg);
    overflow-y: auto;
  }

  .overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 40;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
  }

  .overlay:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: -2px;
  }

  .sidebar[tabindex='-1']:focus {
    outline: none;
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .sidebar {
      border: 2px solid;
    }
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .sidebar {
      width: 100%;
      left: -100%;
    }
  }
</style>
