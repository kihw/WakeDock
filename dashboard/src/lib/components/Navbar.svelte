<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { authStore } from '../stores/auth';
  import { systemStore } from '../stores/system';
  import { toastStore } from '../stores/toastStore';
  import Icon from './Icon.svelte';
  import UserMenu from './UserMenu.svelte';
  import SystemStatus from './SystemStatus.svelte';

  const dispatch = createEventDispatcher();

  let showUserMenu = false;
  let showNotifications = false;

  function toggleSidebar() {
    dispatch('toggle-sidebar');
  }

  function toggleUserMenu() {
    showUserMenu = !showUserMenu;
    showNotifications = false;
  }

  function toggleNotifications() {
    showNotifications = !showNotifications;
    showUserMenu = false;
  }

  function handleLogout() {
    authStore.logout();
    showUserMenu = false;
    toastStore.add({
      type: 'success',
      message: 'Logged out successfully',
    });
  }

  // Close dropdowns when clicking outside
  function handleClickOutside() {
    showUserMenu = false;
    showNotifications = false;
  }
</script>

<nav class="navbar">
  <div class="navbar-start">
    <button class="sidebar-toggle" on:click={toggleSidebar} aria-label="Toggle sidebar">
      <Icon name="menu" size="20" />
    </button>

    <div class="navbar-brand">
      <Icon name="docker" size="24" />
      <span class="brand-text">WakeDock</span>
    </div>
  </div>

  <div class="navbar-center">
    <SystemStatus />
  </div>

  <div class="navbar-end">
    <!-- Search -->
    <div class="search-container">
      <div class="search-input-wrapper">
        <Icon name="search" size="16" />
        <input type="text" placeholder="Search services..." class="search-input" />
      </div>
    </div>

    <!-- Notifications -->
    <div class="dropdown" class:active={showNotifications}>
      <button
        class="navbar-button notification-button"
        on:click={toggleNotifications}
        aria-label="Notifications"
      >
        <Icon name="bell" size="18" />
        {#if ($systemStore.notifications || []).length > 0}
          <span class="notification-badge">{($systemStore.notifications || []).length}</span>
        {/if}
      </button>

      {#if showNotifications}
        <div class="dropdown-menu notifications-menu">
          <div class="dropdown-header">
            <h3>Notifications</h3>
            <button class="text-button">Mark all read</button>
          </div>

          <div class="notifications-list">
            {#if ($systemStore.notifications || []).length > 0}
              {#each $systemStore.notifications || [] as notification}
                <div class="notification-item" class:unread={!notification.read}>
                  <div
                    class="notification-icon"
                    class:error={notification.type === 'error'}
                    class:warning={notification.type === 'warning'}
                  >
                    <Icon
                      name={notification.type === 'error'
                        ? 'alert-circle'
                        : notification.type === 'warning'
                          ? 'alert-triangle'
                          : 'info'}
                      size="16"
                    />
                  </div>
                  <div class="notification-content">
                    <p class="notification-message">{notification.message}</p>
                    <span class="notification-time">{notification.timestamp}</span>
                  </div>
                </div>
              {/each}
            {:else}
              <div class="empty-notifications">
                <Icon name="bell-off" size="24" />
                <p>No notifications</p>
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <!-- User Menu -->
    <div class="dropdown" class:active={showUserMenu}>
      <button class="navbar-button user-button" on:click={toggleUserMenu} aria-label="User menu">
        <div class="user-avatar">
          <Icon name="user" size="16" />
        </div>
        <span class="user-name">{$authStore.user?.username || 'User'}</span>
        <Icon name="chevron-down" size="14" />
      </button>

      {#if showUserMenu}
        <UserMenu on:logout={handleLogout} />
      {/if}
    </div>
  </div>
</nav>

<!-- Click outside handler -->
{#if showUserMenu || showNotifications}
  <div class="overlay" on:click={handleClickOutside}></div>
{/if}

<style>
  .navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    padding: 0 1rem;
    background-color: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: 30;
  }

  .navbar-start,
  .navbar-center,
  .navbar-end {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .navbar-start {
    flex: 1;
  }

  .navbar-center {
    flex: 2;
    justify-content: center;
  }

  .navbar-end {
    flex: 1;
    justify-content: flex-end;
  }

  .sidebar-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border: none;
    background: none;
    color: var(--color-text-secondary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .sidebar-toggle:hover {
    background-color: var(--color-surface-hover);
    color: var(--color-text);
  }

  .navbar-brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--color-primary);
  }

  .brand-text {
    font-weight: 700;
  }

  .search-container {
    position: relative;
  }

  .search-input-wrapper {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background-color: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    min-width: 250px;
  }

  .search-input {
    flex: 1;
    border: none;
    background: none;
    outline: none;
    font-size: 0.9rem;
    color: var(--color-text);
  }

  .search-input::placeholder {
    color: var(--color-text-secondary);
  }

  .navbar-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    border: none;
    background: none;
    color: var(--color-text-secondary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }

  .navbar-button:hover {
    background-color: var(--color-surface-hover);
    color: var(--color-text);
  }

  .notification-button {
    position: relative;
  }

  .notification-badge {
    position: absolute;
    top: -2px;
    right: -2px;
    background-color: var(--color-error);
    color: white;
    font-size: 0.7rem;
    padding: 0.125rem 0.25rem;
    border-radius: 50%;
    min-width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .user-button {
    padding: 0.375rem 0.75rem;
  }

  .user-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background-color: var(--color-primary);
    color: white;
    border-radius: 50%;
  }

  .user-name {
    font-weight: 500;
    color: var(--color-text);
  }

  .dropdown {
    position: relative;
  }

  .dropdown.active .navbar-button {
    background-color: var(--color-surface-hover);
    color: var(--color-text);
  }

  .dropdown-menu {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    background-color: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    z-index: 50;
    min-width: 250px;
    max-height: 400px;
    overflow-y: auto;
  }

  .notifications-menu {
    width: 320px;
  }

  .dropdown-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    border-bottom: 1px solid var(--color-border);
  }

  .dropdown-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .text-button {
    border: none;
    background: none;
    color: var(--color-primary);
    font-size: 0.9rem;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
  }

  .text-button:hover {
    background-color: var(--color-primary-light);
  }

  .notifications-list {
    max-height: 300px;
    overflow-y: auto;
  }

  .notification-item {
    display: flex;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--color-border);
    transition: background-color 0.2s ease;
  }

  .notification-item:hover {
    background-color: var(--color-surface-hover);
  }

  .notification-item.unread {
    background-color: var(--color-primary-light);
  }

  .notification-item:last-child {
    border-bottom: none;
  }

  .notification-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--color-info);
    color: white;
    flex-shrink: 0;
  }

  .notification-icon.error {
    background-color: var(--color-error);
  }

  .notification-icon.warning {
    background-color: var(--color-warning);
  }

  .notification-content {
    flex: 1;
    min-width: 0;
  }

  .notification-message {
    margin: 0 0 0.25rem 0;
    font-size: 0.9rem;
    color: var(--color-text);
    line-height: 1.4;
  }

  .notification-time {
    font-size: 0.8rem;
    color: var(--color-text-secondary);
  }

  .empty-notifications {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 2rem;
    color: var(--color-text-secondary);
  }

  .overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 40;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .navbar-center {
      display: none;
    }

    .search-container {
      display: none;
    }

    .user-name {
      display: none;
    }
  }
</style>
