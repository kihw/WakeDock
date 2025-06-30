<script lang="ts">
  import {
    Menu,
    X,
    Container,
    BarChart3,
    Settings,
    Users,
    Shield,
    Home,
    Activity,
    Layers,
    Zap,
  } from 'lucide-svelte';
  import { onMount, onDestroy } from 'svelte';
  import type { Writable } from 'svelte/store';
  import { page } from '$app/stores';
  import {
    manageFocus,
    announceToScreenReader,
    trapFocus,
    restoreFocus,
  } from '$lib/utils/accessibility';
  import { sanitizeInput } from '$lib/utils/validation';

  export let open: Writable<boolean>;

  let sidebarElement: HTMLElement;
  let navElement: HTMLElement;
  let focusedItemIndex = -1;
  let previousFocus: HTMLElement;
  let keyboardNavigation = false;

  // Enhanced navigation items with accessibility metadata
  const navItems = [
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

  function isActive(href: string): boolean {
    if (href === '/') {
      return currentPath === '/';
    }
    return currentPath.startsWith(href);
  }

  // Enhanced keyboard navigation
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

    // Number shortcuts for navigation
    const num = parseInt(event.key);
    if (num >= 1 && num <= navItems.length) {
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
    if (index >= 0 && index < navItems.length) {
      const item = navItems[index];
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
    announceToScreenReader(`Navigating to ${item.label} - ${item.description}`);

    // Close sidebar on mobile after navigation
    if (window.innerWidth <= 768) {
      open.set(false);
    }
  }

  // Watch for sidebar open/close with accessibility
  $: {
    if ($open) {
      previousFocus = document.activeElement as HTMLElement;

      // Focus first nav item when opening
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
        `Sidebar opened. Use arrow keys to navigate. Press Enter to select. ${navItems.length} navigation items available.`
      );
    }
  }

  onMount(() => {
    // Keyboard event listeners
    const handleGlobalKeydown = (e: KeyboardEvent) => {
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

    document.addEventListener('keydown', handleGlobalKeydown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleGlobalKeydown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  });

  // System stats for sidebar footer (sanitized)
  let systemStats = {
    cpu: 24,
    memory: 68,
    uptime: sanitizeInput('14h 32m'),
  };
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
  <!-- Logo Section -->
  <div class="sidebar-header">
    <div class="logo">
      <div class="logo-icon" role="img" aria-label="WakeDock logo">
        <Container size={28} />
      </div>
      <div class="logo-text">
        <span class="logo-name">WakeDock</span>
        <span class="logo-tagline">Docker Manager</span>
      </div>
    </div>
    <button
      class="close-btn"
      on:click={closeSidebar}
      aria-label="Close sidebar navigation"
      type="button"
    >
      <X size={20} />
    </button>
  </div>

  <!-- Quick Actions -->
  <div class="quick-actions" role="group" aria-label="Quick actions">
    <button
      class="quick-action primary"
      aria-label="Deploy new service quickly"
      title="Deploy new service"
      type="button"
    >
      <Zap size={16} aria-hidden="true" />
      <span>Quick Deploy</span>
    </button>
  </div>

  <!-- Navigation -->
  <nav bind:this={navElement} class="sidebar-nav" aria-label="Main navigation menu">
    <div class="nav-section" role="group" aria-labelledby="main-nav-title">
      <h2 id="main-nav-title" class="nav-section-title">Main</h2>
      {#each navItems.slice(0, 4) as item, index}
        <a
          href={item.href}
          class="nav-item"
          class:active={isActive(item.href)}
          on:click={() => handleNavClick(item)}
          role="menuitem"
          tabindex="0"
          aria-label="{item.label} - {item.description}"
          aria-describedby="nav-{index}-desc"
          aria-current={isActive(item.href) ? 'page' : undefined}
          data-shortcut={item.shortcut}
        >
          <div class="nav-item-icon" aria-hidden="true">
            <svelte:component this={item.icon} size={20} />
          </div>
          <div class="nav-item-content">
            <span class="nav-item-label">{item.label}</span>
            <span
              id="nav-{index}-desc"
              class="nav-item-description"
              aria-label="Description: {item.description}"
            >
              {item.description}
            </span>
          </div>
          <kbd class="nav-shortcut" aria-label="Keyboard shortcut {item.shortcut}">
            {item.shortcut}
          </kbd>
          {#if isActive(item.href)}
            <div class="nav-item-indicator" aria-hidden="true"></div>
          {/if}
        </a>
      {/each}
    </div>

    <div class="nav-section" role="group" aria-labelledby="admin-nav-title">
      <h2 id="admin-nav-title" class="nav-section-title">Administration</h2>
      {#each navItems.slice(4) as item, index}
        <a
          href={item.href}
          class="nav-item"
          class:active={isActive(item.href)}
          on:click={() => handleNavClick(item)}
          role="menuitem"
          tabindex="0"
          aria-label="{item.label} - {item.description}"
          aria-describedby="nav-admin-{index}-desc"
          aria-current={isActive(item.href) ? 'page' : undefined}
          data-shortcut={item.shortcut}
        >
          <div class="nav-item-icon" aria-hidden="true">
            <svelte:component this={item.icon} size={20} />
          </div>
          <div class="nav-item-content">
            <span class="nav-item-label">{item.label}</span>
            <span
              id="nav-admin-{index}-desc"
              class="nav-item-description"
              aria-label="Description: {item.description}"
            >
              {item.description}
            </span>
          </div>
          <kbd class="nav-shortcut" aria-label="Keyboard shortcut {item.shortcut}">
            {item.shortcut}
          </kbd>
          {#if isActive(item.href)}
            <div class="nav-item-indicator" aria-hidden="true"></div>
          {/if}
        </a>
      {/each}
    </div>
  </nav>

  <!-- System Status -->
  <div class="sidebar-status" role="complementary" aria-labelledby="system-status-title">
    <div class="status-header">
      <h3 id="system-status-title" class="status-title">System Status</h3>
      <div class="status-indicator online" aria-label="System is online">
        <span class="status-dot" aria-hidden="true"></span>
        <span class="status-text">Online</span>
      </div>
    </div>

    <div class="status-metrics" role="group" aria-label="System metrics">
      <div class="metric">
        <div class="metric-header">
          <span class="metric-label">CPU</span>
          <span class="metric-value" aria-label="CPU usage {systemStats.cpu} percent">
            {systemStats.cpu}%
          </span>
        </div>
        <div
          class="metric-bar"
          role="progressbar"
          aria-valuenow={systemStats.cpu}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div class="metric-fill" style="width: {systemStats.cpu}%" aria-hidden="true"></div>
        </div>
      </div>

      <div class="metric">
        <div class="metric-header">
          <span class="metric-label">Memory</span>
          <span class="metric-value" aria-label="Memory usage {systemStats.memory} percent">
            {systemStats.memory}%
          </span>
        </div>
        <div
          class="metric-bar"
          role="progressbar"
          aria-valuenow={systemStats.memory}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div
            class="metric-fill high"
            style="width: {systemStats.memory}%"
            aria-hidden="true"
          ></div>
        </div>
      </div>

      <div class="uptime">
        <span class="uptime-label">Uptime</span>
        <span class="uptime-value" aria-label="System uptime {systemStats.uptime}">
          {systemStats.uptime}
        </span>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="sidebar-footer" role="contentinfo">
    <div class="version">
      <p class="version-text" aria-label="WakeDock version 1.0.0">WakeDock v1.0.0</p>
      <p class="build-info" aria-label="Build version 2024.1.1">Build 2024.1.1</p>
    </div>
  </div>
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

  /* Header Section */
  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-light);
    background: rgba(255, 255, 255, 0.05);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .logo-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-lg);
    background: var(--gradient-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: var(--shadow-md);
  }

  .logo-text {
    display: flex;
    flex-direction: column;
  }

  .logo-name {
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--color-text);
    line-height: 1.2;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .logo-tagline {
    font-size: 0.75rem;
    color: var(--color-text-muted);
    line-height: 1.2;
  }

  .close-btn {
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    padding: var(--spacing-xs);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-normal);
  }

  .close-btn:hover {
    background: var(--color-surface-hover);
    color: var(--color-text);
    transform: scale(1.1);
  }

  /* Quick Actions */
  .quick-actions {
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-light);
  }

  .quick-action {
    width: 100%;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    border-radius: var(--radius);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-normal);
    background: var(--gradient-primary);
    color: white;
    box-shadow: var(--shadow-sm);
  }

  .quick-action:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  /* Navigation */
  .sidebar-nav {
    flex: 1;
    padding: var(--spacing-lg);
    overflow-y: auto;
  }

  .nav-section {
    margin-bottom: var(--spacing-xl);
  }

  .nav-section:last-child {
    margin-bottom: 0;
  }

  .nav-section-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-text-muted);
    margin-bottom: var(--spacing-md);
    padding: 0 var(--spacing-sm);
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md) var(--spacing-sm);
    border-radius: var(--radius-lg);
    color: var(--color-text-secondary);
    text-decoration: none;
    margin-bottom: var(--spacing-xs);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
  }

  .nav-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity var(--transition-normal);
    z-index: -1;
  }

  .nav-item:hover {
    color: var(--color-text);
    transform: translateX(4px);
    background: rgba(255, 255, 255, 0.05);
  }

  .nav-item.active {
    color: white;
    background: var(--gradient-primary);
    box-shadow: var(--shadow-md);
  }

  .nav-item.active::before {
    opacity: 1;
  }

  .nav-item-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius);
    background: rgba(255, 255, 255, 0.1);
    transition: all var(--transition-normal);
    flex-shrink: 0;
  }

  .nav-item:hover .nav-item-icon {
    background: rgba(255, 255, 255, 0.15);
    transform: scale(1.05);
  }

  .nav-item.active .nav-item-icon {
    background: rgba(255, 255, 255, 0.2);
  }

  .nav-item-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    min-width: 0;
  }

  .nav-item-label {
    font-weight: 500;
    font-size: 0.9rem;
    line-height: 1.2;
  }

  .nav-item-description {
    font-size: 0.75rem;
    opacity: 0.8;
    line-height: 1.2;
  }

  .nav-item-indicator {
    position: absolute;
    right: var(--spacing-sm);
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    animation: pulse 2s infinite;
  }

  /* Navigation Shortcuts */
  .nav-shortcut {
    position: absolute;
    right: var(--spacing-md);
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--spacing-xs);
    padding: 2px 6px;
    font-size: 0.7rem;
    font-family: monospace;
    color: var(--color-text-muted);
    opacity: 0;
    transition: opacity var(--transition-normal);
  }

  .nav-item:hover .nav-shortcut,
  .nav-item:focus .nav-shortcut {
    opacity: 1;
  }

  /* Accessibility Enhancements */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  /* Keyboard navigation focus styles */
  :global(.keyboard-navigation) .nav-item:focus,
  :global(.keyboard-navigation) .close-btn:focus,
  :global(.keyboard-navigation) .quick-action:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }

  /* Enhanced focus for navigation items */
  .nav-item:focus {
    background: var(--color-primary);
    color: white;
    outline: 2px solid rgba(255, 255, 255, 0.5);
    outline-offset: -2px;
  }

  .nav-item:focus .nav-item-description {
    opacity: 1;
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .sidebar {
      border: 2px solid;
    }

    .nav-item,
    .quick-action,
    .close-btn {
      border: 1px solid;
    }

    .metric-bar {
      border: 1px solid;
    }
  }

  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }

    .nav-item-indicator {
      animation: none;
    }

    .status-dot {
      animation: none;
    }
  }

  /* Focus trap styles */
  .sidebar[tabindex='-1']:focus {
    outline: none;
  }

  /* Section titles as proper headings */
  .nav-section-title,
  .status-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-text-muted);
    margin: 0 0 var(--spacing-md) 0;
    padding: 0 var(--spacing-sm);
  }

  /* Progress bar accessibility */
  .metric-bar {
    position: relative;
  }

  .metric-bar:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }

  /* Overlay accessibility */
  .overlay:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: -2px;
  }
</style>
