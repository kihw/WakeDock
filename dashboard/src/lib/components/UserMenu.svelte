<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { link } from 'svelte-spa-router';
  import { authStore } from '../stores/auth';
  import { systemStore } from '../stores/system';
  import Icon from './Icon.svelte';
  import { sanitizeInput, generateCSRFToken, checkRateLimit } from '../utils/validation';
  import { announceToScreenReader, manageFocus, trapFocus } from '../utils/accessibility';

  const dispatch = createEventDispatcher();

  // Security and accessibility state
  let csrfToken = '';
  let menuElement: HTMLDivElement;
  let isMenuOpen = false;
  let currentFocusIndex = -1;
  let focusableElements: HTMLElement[] = [];

  // Initialize security
  onMount(async () => {
    csrfToken = await generateCSRFToken();
    setupKeyboardNavigation();
    announceToScreenReader('User menu loaded');
  });

  // Cleanup
  onDestroy(() => {
    if (menuElement) {
      menuElement.removeEventListener('keydown', handleKeyDown);
    }
  });

  // Setup keyboard navigation
  function setupKeyboardNavigation() {
    if (menuElement) {
      menuElement.addEventListener('keydown', handleKeyDown);
    }
  }

  // Handle keyboard navigation
  function handleKeyDown(event: KeyboardEvent) {
    const focusableItems = Array.from(
      menuElement.querySelectorAll('a[href], button:not([disabled])')
    ) as HTMLElement[];

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        currentFocusIndex = (currentFocusIndex + 1) % focusableItems.length;
        focusableItems[currentFocusIndex]?.focus();
        break;
      case 'ArrowUp':
        event.preventDefault();
        currentFocusIndex =
          currentFocusIndex <= 0 ? focusableItems.length - 1 : currentFocusIndex - 1;
        focusableItems[currentFocusIndex]?.focus();
        break;
      case 'Home':
        event.preventDefault();
        currentFocusIndex = 0;
        focusableItems[0]?.focus();
        break;
      case 'End':
        event.preventDefault();
        currentFocusIndex = focusableItems.length - 1;
        focusableItems[currentFocusIndex]?.focus();
        break;
      case 'Escape':
        event.preventDefault();
        dispatch('close');
        break;
    }
  }

  // Menu items
  const menuItems = [
    {
      id: 'profile',
      label: 'Profile',
      href: '/profile',
      icon: 'user',
      ariaLabel: 'View and edit your profile settings',
    },
    {
      id: 'settings',
      label: 'Settings',
      href: '/settings',
      icon: 'settings',
      ariaLabel: 'Access application settings and preferences',
    },
    {
      id: 'help',
      label: 'Help & Support',
      href: '/help',
      icon: 'help-circle',
      ariaLabel: 'Get help and view support documentation',
    },
    {
      type: 'divider',
    },
    {
      id: 'logout',
      label: 'Log Out',
      action: () => handleLogout(),
      icon: 'log-out',
      danger: true,
      ariaLabel: 'Sign out of your account',
    },
  ];

  // Enhanced item click handler with security checks
  async function handleItemClick(item: any, event?: Event) {
    // Rate limiting check
    if (!checkRateLimit(`user-menu-${item.id}`, 5, 60000)) {
      announceToScreenReader(
        'Action blocked due to rate limiting. Please wait before trying again.'
      );
      return;
    }

    // Sanitize any user input if present
    if (item.action) {
      try {
        await item.action();
        announceToScreenReader(`${item.label} action completed`);
      } catch (error) {
        console.error('Menu action error:', error);
        announceToScreenReader(`Error executing ${item.label} action`);
      }
    }
  }

  // Enhanced logout handler
  async function handleLogout() {
    try {
      announceToScreenReader('Signing out...');
      dispatch('logout', { csrfToken });
      announceToScreenReader('Successfully signed out');
    } catch (error) {
      console.error('Logout error:', error);
      announceToScreenReader('Error signing out. Please try again.');
    }
  }
</script>

<div
  class="user-menu"
  bind:this={menuElement}
  role="menu"
  aria-label="User account menu"
  tabindex="-1"
>
  <!-- User Info Header -->
  <div class="user-info" role="group" aria-labelledby="user-info-heading">
    <h3 id="user-info-heading" class="sr-only">User Information</h3>
    <div class="user-avatar" role="img" aria-label="User avatar">
      <Icon name="user" size="20" />
    </div>
    <div class="user-details">
      <h4 class="user-name" aria-label="Username">
        {sanitizeInput($authStore.user?.username || 'User')}
      </h4>
      <p class="user-email" aria-label="Email address">
        {sanitizeInput($authStore.user?.email || 'user@example.com')}
      </p>
      <span class="user-role" aria-label="User role">
        {sanitizeInput($authStore.user?.role || 'Administrator')}
      </span>
    </div>
  </div>

  <!-- Quick Stats -->
  <div class="quick-stats" role="group" aria-labelledby="stats-heading">
    <h3 id="stats-heading" class="sr-only">Quick Statistics</h3>
    <div class="stat-item">
      <Icon name="server" size="16" aria-hidden="true" />
      <span class="stat-label">Services</span>
      <span class="stat-value" aria-label="Total services">
        {$systemStore.services?.length || 0}
      </span>
    </div>
    <div class="stat-item">
      <Icon name="activity" size="16" aria-hidden="true" />
      <span class="stat-label">Active</span>
      <span class="stat-value" aria-label="Active services">
        {$systemStore.services?.filter((s) => s.status === 'running').length || 0}
      </span>
    </div>
  </div>

  <!-- Menu Items -->
  <nav class="menu-items" role="navigation" aria-label="User menu navigation">
    {#each menuItems as item, index}
      {#if item.type === 'divider'}
        <hr class="menu-divider" role="separator" aria-hidden="true" />
      {:else if item.href}
        <a
          href={item.href}
          use:link
          class="menu-item"
          class:danger={item.danger}
          role="menuitem"
          aria-label={item.ariaLabel || item.label}
          tabindex="-1"
          on:click={(e) => handleItemClick(item, e)}
        >
          <Icon name={item.icon} size="16" aria-hidden="true" />
          <span class="menu-label">{item.label}</span>
        </a>
      {:else}
        <button
          class="menu-item"
          class:danger={item.danger}
          role="menuitem"
          aria-label={item.ariaLabel || item.label}
          tabindex="-1"
          on:click={(e) => handleItemClick(item, e)}
        >
          {#if item.icon}
            <Icon name={item.icon} size="16" aria-hidden="true" />
          {/if}
          <span class="menu-label">{item.label}</span>
        </button>
      {/if}
    {/each}
  </nav>

  <!-- Footer -->
  <div class="menu-footer">
    <div class="version-info">
      <span class="version-label">WakeDock v2.0</span>
      <span class="status-indicator" class:online={$systemStore.status === 'healthy'}>
        <Icon name="circle" size="8" />
      </span>
    </div>
  </div>
</div>

<style>
  .user-menu {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    width: 280px;
    background-color: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    z-index: 50;
    overflow: hidden;
  }

  .user-info {
    display: flex;
    gap: 0.75rem;
    padding: 1rem;
    background: linear-gradient(135deg, var(--color-primary-light), var(--color-primary));
    color: var(--color-primary-dark);
  }

  .user-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background-color: white;
    color: var(--color-primary);
    border-radius: 50%;
    flex-shrink: 0;
  }

  .user-details {
    flex: 1;
    min-width: 0;
  }

  .user-name {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-primary-dark);
    line-height: 1.2;
  }

  .user-email {
    margin: 0 0 0.25rem 0;
    font-size: 0.85rem;
    color: var(--color-primary-dark);
    opacity: 0.8;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .user-role {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    background-color: rgba(255, 255, 255, 0.2);
    color: var(--color-primary-dark);
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: var(--radius-sm);
  }

  .quick-stats {
    display: flex;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background-color: var(--color-background);
    border-bottom: 1px solid var(--color-border);
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
  }

  .stat-label {
    font-size: 0.8rem;
    color: var(--color-text-secondary);
    flex: 1;
  }

  .stat-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--color-text);
  }

  .menu-items {
    padding: 0.5rem 0;
  }

  .menu-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem 1rem;
    border: none;
    background: none;
    color: var(--color-text);
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
  }

  .menu-item:hover {
    background-color: var(--color-surface-hover);
  }

  .menu-item.danger {
    color: var(--color-error);
  }

  .menu-item.danger:hover {
    background-color: var(--color-error-light);
    color: var(--color-error-dark);
  }

  .menu-label {
    flex: 1;
    text-align: left;
  }

  .menu-divider {
    height: 1px;
    background-color: var(--color-border);
    margin: 0.5rem 0;
  }

  .menu-footer {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--color-border);
    background-color: var(--color-background);
  }

  .version-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .version-label {
    font-size: 0.8rem;
    color: var(--color-text-secondary);
    font-weight: 500;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    color: var(--color-error);
  }

  .status-indicator.online {
    color: var(--color-success);
  }

  /* Dark mode */
  @media (prefers-color-scheme: dark) {
    .user-menu {
      background-color: var(--color-surface-dark);
      border-color: var(--color-border-dark);
    }

    .user-info {
      background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
    }
  }
</style>
