<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { link } from 'svelte-spa-router';
  import { authStore } from '../stores/auth';
  import { systemStore } from '../stores/system';
  import Icon from './Icon.svelte';

  const dispatch = createEventDispatcher();

  // Menu items
  const menuItems = [
    {
      id: 'profile',
      label: 'Profile',
      href: '/profile',
      icon: 'user',
    },
    {
      id: 'settings',
      label: 'Settings',
      href: '/settings',
      icon: 'settings',
    },
    {
      id: 'help',
      label: 'Help & Support',
      href: '/help',
      icon: 'help-circle',
    },
    {
      type: 'divider',
    },
    {
      id: 'logout',
      label: 'Log Out',
      action: () => dispatch('logout'),
      icon: 'log-out',
      danger: true,
    },
  ];

  function handleItemClick(item: any) {
    if (item.action) {
      item.action();
    }
  }
</script>

<div class="user-menu">
  <!-- User Info Header -->
  <div class="user-info">
    <div class="user-avatar">
      <Icon name="user" size="20" />
    </div>
    <div class="user-details">
      <h4 class="user-name">{$authStore.user?.username || 'User'}</h4>
      <p class="user-email">{$authStore.user?.email || 'user@example.com'}</p>
      <span class="user-role">{$authStore.user?.role || 'Administrator'}</span>
    </div>
  </div>

  <!-- Quick Stats -->
  <div class="quick-stats">
    <div class="stat-item">
      <Icon name="server" size="16" />
      <span class="stat-label">Services</span>
      <span class="stat-value">{$systemStore.services?.length || 0}</span>
    </div>
    <div class="stat-item">
      <Icon name="activity" size="16" />
      <span class="stat-label">Active</span>
      <span class="stat-value"
        >{$systemStore.services?.filter((s) => s.status === 'running').length || 0}</span
      >
    </div>
  </div>

  <!-- Menu Items -->
  <div class="menu-items">
    {#each menuItems as item}
      {#if item.type === 'divider'}
        <div class="menu-divider"></div>
      {:else if item.href}
        <a href={item.href} use:link class="menu-item" class:danger={item.danger}>
          <Icon name={item.icon} size="16" />
          <span class="menu-label">{item.label}</span>
        </a>
      {:else}
        <button class="menu-item" class:danger={item.danger} on:click={() => handleItemClick(item)}>
          <Icon name={item.icon} size="16" />
          <span class="menu-label">{item.label}</span>
        </button>
      {/if}
    {/each}
  </div>

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
