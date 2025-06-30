<script lang="ts">
  import { Menu, Bell, User, Sun, Moon, Settings } from 'lucide-svelte';
  import { writable } from 'svelte/store';
  import { onMount, onDestroy } from 'svelte';
  import type { Writable } from 'svelte/store';
  import { sanitizeInput, generateCSRFToken, checkRateLimit } from '$lib/utils/validation';
  import {
    manageFocus,
    announceToScreenReader,
    trapFocus,
    restoreFocus,
  } from '$lib/utils/accessibility';

  export let sidebarOpen: Writable<boolean>;

  const darkMode = writable(false);
  let searchQuery = '';
  let showNotifications = false;
  let showUserMenu = false;
  let searchInput: HTMLInputElement;
  let notificationDropdown: HTMLElement;
  let userDropdown: HTMLElement;
  let headerElement: HTMLElement;
  let previousFocus: HTMLElement;

  // Security state
  let csrfToken = '';
  let searchAttempts = 0;
  let isSearchRateLimited = false;

  // Accessibility state
  let keyboardNavigation = false;
  let searchExpanded = false;

  function toggleDarkMode() {
    darkMode.update((dark) => {
      const newMode = !dark;
      document.documentElement.setAttribute('data-theme', newMode ? 'dark' : 'light');
      localStorage.setItem('wakedock_theme', newMode ? 'dark' : 'light');

      // Announce theme change to screen readers
      announceToScreenReader(`Theme changed to ${newMode ? 'dark' : 'light'} mode`);

      return newMode;
    });
  }

  // Initialize theme from localStorage with accessibility
  onMount(() => {
    // Initialize CSRF token
    csrfToken = generateCSRFToken();

    // Theme initialization
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('wakedock_theme');
      if (savedTheme) {
        darkMode.set(savedTheme === 'dark');
        document.documentElement.setAttribute('data-theme', savedTheme);
      }
    }

    // Keyboard event handlers for accessibility
    const handleKeydown = (e: KeyboardEvent) => {
      // Global keyboard shortcuts
      if (e.metaKey || e.ctrlKey) {
        switch (e.key.toLowerCase()) {
          case 'k':
            e.preventDefault();
            openSearch();
            break;
          case 'b':
            e.preventDefault();
            toggleSidebar();
            break;
        }
      }

      // Escape key handling
      if (e.key === 'Escape') {
        if (showNotifications) {
          closeNotifications();
        } else if (showUserMenu) {
          closeUserMenu();
        } else if (searchExpanded) {
          closeSearch();
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
    };
  });

  onDestroy(() => {
    // Clear sensitive data
    csrfToken = '';
    searchQuery = '';
  });

  function toggleSidebar() {
    sidebarOpen.update((open) => !open);
    announceToScreenReader($sidebarOpen ? 'Sidebar opened' : 'Sidebar closed');
  }

  // Enhanced search functionality with security
  function openSearch() {
    searchExpanded = true;
    if (searchInput) {
      manageFocus(searchInput);
      announceToScreenReader('Search opened. Type to search for services and content.');
    }
  }

  function closeSearch() {
    searchExpanded = false;
    searchQuery = '';
    if (previousFocus) {
      manageFocus(previousFocus);
    }
  }

  function handleSearch(e: Event) {
    const target = e.target as HTMLInputElement;
    const query = sanitizeInput(target.value);

    // Rate limiting for search
    const rateLimitResult = checkRateLimit('search', searchAttempts, 20, 60000); // 20 searches per minute
    if (!rateLimitResult.allowed) {
      isSearchRateLimited = true;
      announceToScreenReader('Search rate limit exceeded. Please wait before searching again.');
      return;
    }

    searchQuery = query;
    searchAttempts++;

    // Perform search logic here
    if (query.length > 2) {
      announceToScreenReader(`Searching for "${query}"`);
      // TODO: Implement actual search functionality
    }
  }

  // Enhanced notification handling with accessibility
  function toggleNotifications(e: MouseEvent) {
    e.stopPropagation();

    if (showNotifications) {
      closeNotifications();
    } else {
      openNotifications();
    }
  }

  function openNotifications() {
    previousFocus = document.activeElement as HTMLElement;
    showUserMenu = false;
    showNotifications = true;

    setTimeout(() => {
      if (notificationDropdown) {
        trapFocus(notificationDropdown);
        const firstItem = notificationDropdown.querySelector('[role="menuitem"]') as HTMLElement;
        if (firstItem) {
          manageFocus(firstItem);
        }
      }
    }, 100);

    announceToScreenReader(
      `Notifications menu opened. ${notifications.length} notifications available.`
    );
  }

  function closeNotifications() {
    showNotifications = false;
    if (previousFocus) {
      manageFocus(previousFocus);
    }
    announceToScreenReader('Notifications menu closed');
  }

  // Enhanced user menu handling with accessibility
  function toggleUserMenu(e: MouseEvent) {
    e.stopPropagation();

    if (showUserMenu) {
      closeUserMenu();
    } else {
      openUserMenu();
    }
  }

  function openUserMenu() {
    previousFocus = document.activeElement as HTMLElement;
    showNotifications = false;
    showUserMenu = true;

    setTimeout(() => {
      if (userDropdown) {
        trapFocus(userDropdown);
        const firstItem = userDropdown.querySelector('[role="menuitem"]') as HTMLElement;
        if (firstItem) {
          manageFocus(firstItem);
        }
      }
    }, 100);

    announceToScreenReader('User menu opened. Navigate with arrow keys.');
  }

  function closeUserMenu() {
    showUserMenu = false;
    if (previousFocus) {
      manageFocus(previousFocus);
    }
    announceToScreenReader('User menu closed');
  }

  // Mock notifications with security
  const notifications = [
    {
      id: 1,
      title: 'Service Started',
      message: 'nginx-proxy is now running',
      time: '2 min ago',
      type: 'success',
    },
    {
      id: 2,
      title: 'Memory Alert',
      message: 'High memory usage detected',
      time: '5 min ago',
      type: 'warning',
    },
    {
      id: 3,
      title: 'Backup Complete',
      message: 'Database backup finished',
      time: '1 hour ago',
      type: 'info',
    },
  ];

  function getNotificationIcon(type: string) {
    switch (type) {
      case 'success':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return 'ℹ️';
    }
  }

  // Handle click outside dropdowns
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as Element;

    if (showNotifications && !notificationDropdown?.contains(target)) {
      closeNotifications();
    }

    if (showUserMenu && !userDropdown?.contains(target)) {
      closeUserMenu();
    }
  }

  // Enhanced logout with security
  function handleLogout() {
    // Clear session data
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');

    // Clear CSRF token
    csrfToken = '';

    announceToScreenReader('Logging out...');

    // TODO: Call actual logout API
    // window.location.href = '/login';
  }
</script>

<!-- CSRF Token (hidden) -->
<input type="hidden" name="_csrf" value={csrfToken} />

<header
  bind:this={headerElement}
  class="header"
  aria-label="Site header with navigation and user controls"
>
  <div class="header-left">
    <button
      class="menu-btn"
      on:click={toggleSidebar}
      aria-label="Toggle sidebar navigation"
      aria-expanded={$sidebarOpen}
      aria-controls="sidebar"
      type="button"
    >
      <Menu size={20} />
    </button>

    <div class="breadcrumb" role="navigation" aria-label="Breadcrumb">
      <h1 class="page-title">Dashboard</h1>
      <span class="page-subtitle">Welcome back, Admin</span>
    </div>
  </div>

  <div class="header-right">
    <!-- Enhanced Search Bar with Accessibility -->
    <div class="search-container" role="search">
      <div class="search-input-wrapper" class:expanded={searchExpanded}>
        <svg
          class="search-icon"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          bind:this={searchInput}
          bind:value={searchQuery}
          type="search"
          placeholder="Search services, containers..."
          class="search-input"
          disabled={isSearchRateLimited}
          on:input={handleSearch}
          on:focus={openSearch}
          aria-label="Search services and containers"
          aria-describedby="search-help"
          autocomplete="off"
          spellcheck="false"
        />
        <kbd class="search-kbd" aria-label="Keyboard shortcut Control K">⌘K</kbd>

        {#if isSearchRateLimited}
          <div class="search-error" role="alert">Search temporarily limited. Please wait.</div>
        {/if}
      </div>
      <div id="search-help" class="sr-only">
        Use Control+K to quickly access search. Type to find services, containers, and other
        content.
      </div>
    </div>

    <!-- Theme Toggle with Accessibility -->
    <button
      class="icon-btn theme-toggle"
      on:click={toggleDarkMode}
      aria-label={$darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      title={$darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      type="button"
    >
      {#if $darkMode}
        <Sun size={18} />
      {:else}
        <Moon size={18} />
      {/if}
    </button>

    <!-- Enhanced Notifications with Accessibility -->
    <div class="dropdown" class:active={showNotifications}>
      <button
        class="icon-btn notification-btn"
        on:click={toggleNotifications}
        aria-label="Notifications"
        aria-expanded={showNotifications}
        aria-haspopup="menu"
        type="button"
      >
        <Bell size={18} />
        {#if notifications.length > 0}
          <span class="notification-badge" aria-label="{notifications.length} unread notifications">
            {notifications.length}
          </span>
        {/if}
      </button>

      {#if showNotifications}
        <div
          bind:this={notificationDropdown}
          class="dropdown-menu notifications-menu"
          role="menu"
          aria-label="Notifications"
          tabindex="-1"
        >
          <div class="dropdown-header">
            <h2 id="notifications-title" class="dropdown-title">Notifications</h2>
            <button
              class="text-btn"
              role="menuitem"
              aria-label="Mark all notifications as read"
              type="button"
            >
              Mark all read
            </button>
          </div>

          <div class="notifications-list" role="group" aria-labelledby="notifications-title">
            {#each notifications as notification}
              <div
                class="notification-item"
                role="menuitem"
                tabindex="0"
                aria-describedby="notification-{notification.id}-desc"
              >
                <div class="notification-icon" aria-hidden="true">
                  {getNotificationIcon(notification.type)}
                </div>
                <div class="notification-content">
                  <div class="notification-title">{notification.title}</div>
                  <div id="notification-{notification.id}-desc" class="notification-message">
                    {notification.message}
                  </div>
                  <div class="notification-time" aria-label="Received {notification.time}">
                    {notification.time}
                  </div>
                </div>
              </div>
            {/each}
          </div>

          <div class="dropdown-footer">
            <a
              href="/notifications"
              class="text-btn"
              role="menuitem"
              aria-label="View all notifications in detail"
            >
              View all notifications
            </a>
          </div>
        </div>
      {/if}
    </div>

    <!-- Settings -->
    <a href="/settings" class="icon-btn settings-btn" aria-label="Go to settings" title="Settings">
      <Settings size={18} />
    </a>

    <!-- Enhanced User Menu with Accessibility -->
    <div class="dropdown" class:active={showUserMenu}>
      <button
        class="user-btn"
        on:click={toggleUserMenu}
        aria-label="User menu"
        aria-expanded={showUserMenu}
        aria-haspopup="menu"
        type="button"
      >
        <div class="user-avatar" aria-hidden="true">
          <User size={18} />
        </div>
        <div class="user-info">
          <span class="user-name">Admin</span>
          <span class="user-role">Administrator</span>
        </div>
        <svg
          class="chevron"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <polyline points="6,9 12,15 18,9" />
        </svg>
      </button>

      {#if showUserMenu}
        <div
          bind:this={userDropdown}
          class="dropdown-menu user-menu"
          role="menu"
          aria-label="User menu"
          tabindex="-1"
        >
          <div class="user-menu-header">
            <div class="user-avatar large" aria-hidden="true">
              <User size={24} />
            </div>
            <div class="user-details">
              <div class="user-name">Administrator</div>
              <div class="user-email">admin@wakedock.com</div>
            </div>
          </div>

          <div class="menu-divider" role="separator"></div>

          <a href="/profile" class="menu-item" role="menuitem" aria-label="Go to profile settings">
            <User size={16} aria-hidden="true" />
            Profile Settings
          </a>

          <a
            href="/preferences"
            class="menu-item"
            role="menuitem"
            aria-label="Go to user preferences"
          >
            <Settings size={16} aria-hidden="true" />
            Preferences
          </a>

          <div class="menu-divider" role="separator"></div>

          <button
            class="menu-item logout-btn"
            on:click={handleLogout}
            role="menuitem"
            aria-label="Sign out of your account"
            type="button"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16,17 21,12 16,7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign Out
          </button>
        </div>
      {/if}
    </div>
  </div>
</header>

<!-- Click outside handler -->
<svelte:window on:click={handleClickOutside} />

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-md) var(--spacing-lg);
    background: var(--gradient-surface);
    border-bottom: 1px solid var(--color-border-light);
    position: sticky;
    top: 0;
    z-index: 30;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: var(--shadow-sm);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
  }

  .menu-btn {
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    padding: var(--spacing-sm);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-normal);
  }

  .menu-btn:hover {
    background: var(--color-surface-hover);
    color: var(--color-text);
    transform: scale(1.05);
  }

  .breadcrumb {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .page-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text);
    margin: 0;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .page-subtitle {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  /* Search Container */
  .search-container {
    position: relative;
    margin-right: var(--spacing-md);
  }

  .search-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    transition: all var(--transition-normal);
  }

  .search-input-wrapper.expanded {
    transform: scale(1.02);
  }

  .search-input {
    width: 300px;
    padding: var(--spacing-sm) var(--spacing-md);
    padding-left: 2.5rem;
    padding-right: 3rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-full);
    background: var(--color-surface-glass);
    color: var(--color-text);
    font-size: 0.875rem;
    transition: all var(--transition-normal);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    width: 350px;
  }

  .search-input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .search-error {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--color-error);
    color: white;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius);
    font-size: 0.75rem;
    z-index: 1000;
    margin-top: var(--spacing-xs);
  }

  .search-icon {
    position: absolute;
    left: var(--spacing-sm);
    color: var(--color-text-muted);
    pointer-events: none;
    z-index: 1;
  }

  .search-kbd {
    position: absolute;
    right: var(--spacing-sm);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--spacing-xs);
    padding: 2px 6px;
    font-size: 0.7rem;
    color: var(--color-text-muted);
    font-family: monospace;
    pointer-events: none;
  }

  /* Icon Buttons */
  .icon-btn {
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    padding: var(--spacing-sm);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-normal);
    position: relative;
  }

  .icon-btn:hover {
    background: var(--color-surface-hover);
    color: var(--color-text);
    transform: scale(1.05);
  }

  .theme-toggle:hover {
    color: var(--color-primary);
  }

  /* Notification Badge */
  .notification-btn {
    position: relative;
  }

  .notification-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    background: var(--gradient-secondary);
    color: white;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    font-size: 0.7rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulse 2s infinite;
  }

  /* User Button */
  .user-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    background: var(--color-surface-glass);
    border: 1px solid var(--color-border);
    color: var(--color-text);
    cursor: pointer;
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-full);
    font-size: 0.875rem;
    transition: all var(--transition-normal);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }

  .user-btn:hover {
    background: var(--color-surface-hover);
    border-color: var(--color-primary-light);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  .user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--gradient-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .user-avatar.large {
    width: 48px;
    height: 48px;
  }

  .user-info {
    display: flex;
    flex-direction: column;
    text-align: left;
  }

  .user-name {
    font-weight: 500;
    line-height: 1.2;
  }

  .user-role {
    font-size: 0.75rem;
    color: var(--color-text-muted);
    line-height: 1.2;
  }

  .chevron {
    color: var(--color-text-muted);
    transition: transform var(--transition-normal);
  }

  .user-btn:hover .chevron {
    transform: rotate(180deg);
  }

  /* Dropdown Menus */
  .dropdown {
    position: relative;
  }

  .dropdown-menu {
    position: absolute;
    top: calc(100% + var(--spacing-sm));
    right: 0;
    min-width: 280px;
    background: var(--gradient-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-xl);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    z-index: 1000;
    animation: slideIn 0.2s ease-out;
    overflow: hidden;
  }

  .dropdown-header {
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-light);
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
  }

  .dropdown-header h3 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    color: var(--color-text);
  }

  .dropdown-footer {
    padding: var(--spacing-md) var(--spacing-lg);
    border-top: 1px solid var(--color-border-light);
    background: rgba(0, 0, 0, 0.02);
    text-align: center;
  }

  .text-btn {
    background: none;
    border: none;
    color: var(--color-primary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    transition: color var(--transition-normal);
  }

  .text-btn:hover {
    color: var(--color-primary-dark);
  }

  /* Notifications Menu */
  .notifications-list {
    max-height: 300px;
    overflow-y: auto;
  }

  .notification-item {
    display: flex;
    gap: var(--spacing-sm);
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-light);
    transition: background-color var(--transition-normal);
  }

  .notification-item:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .notification-item:last-child {
    border-bottom: none;
  }

  .notification-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
  }

  .notification-content {
    flex: 1;
    min-width: 0;
  }

  .notification-title {
    font-weight: 500;
    font-size: 0.875rem;
    color: var(--color-text);
    margin-bottom: var(--spacing-xs);
  }

  .notification-message {
    font-size: 0.8rem;
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-xs);
  }

  .notification-time {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  /* User Menu */
  .user-menu-header {
    padding: var(--spacing-lg);
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
  }

  .user-details .user-name {
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: var(--spacing-xs);
  }

  .user-email {
    font-size: 0.8rem;
    color: var(--color-text-muted);
  }

  .menu-divider {
    height: 1px;
    background: var(--color-border-light);
    margin: var(--spacing-sm) 0;
  }

  .menu-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-lg);
    color: var(--color-text-secondary);
    text-decoration: none;
    font-size: 0.875rem;
    transition: all var(--transition-normal);
    background: none;
    border: none;
    width: 100%;
    text-align: left;
    cursor: pointer;
  }

  .menu-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--color-text);
  }

  .logout-btn {
    color: var(--color-error);
  }

  .logout-btn:hover {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-error);
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
  :global(.keyboard-navigation) .icon-btn:focus,
  :global(.keyboard-navigation) .user-btn:focus,
  :global(.keyboard-navigation) .menu-item:focus,
  :global(.keyboard-navigation) .text-btn:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }

  /* Enhanced focus for dropdown items */
  .notification-item:focus,
  .menu-item:focus {
    background: var(--color-primary-light);
    color: var(--color-primary-dark);
    outline: 2px solid var(--color-primary);
    outline-offset: -2px;
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .header {
      border-bottom: 2px solid;
    }

    .icon-btn,
    .user-btn {
      border: 1px solid;
    }

    .dropdown-menu {
      border: 2px solid;
    }
  }

  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }

  /* Dark mode adjustments */
  @media (prefers-color-scheme: dark) {
    .header {
      background: var(--color-surface-dark);
      border-color: var(--color-border-dark);
    }
  }

  /* Focus trap styles for dropdowns */
  .dropdown-menu[tabindex='-1'] {
    outline: none;
  }

  .dropdown-menu[tabindex='-1']:focus-within {
    box-shadow: 0 0 0 3px var(--color-primary-light);
  }

  @media (max-width: 768px) {
    .menu-btn {
      display: flex;
    }

    .search-container {
      display: none;
    }

    .breadcrumb {
      display: none;
    }

    .user-info {
      display: none;
    }

    .dropdown-menu {
      min-width: 250px;
    }
  }

  @media (max-width: 480px) {
    .header {
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .header-right {
      gap: var(--spacing-xs);
    }

    .dropdown-menu {
      right: -50px;
      min-width: 200px;
    }
  }
</style>
