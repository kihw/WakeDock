<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  
  export let items: Array<{
    id: string;
    label: string;
    icon: string;
    href: string;
    badge?: number;
  }> = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', href: '/' },
    { id: 'services', label: 'Services', icon: 'container', href: '/services' },
    { id: 'monitoring', label: 'Monitor', icon: 'activity', href: '/monitoring' },
    { id: 'logs', label: 'Logs', icon: 'file-text', href: '/logs' },
    { id: 'profile', label: 'Profile', icon: 'user', href: '/profile' }
  ];
  
  let activeRoute = '';
  let mounted = false;
  
  onMount(() => {
    mounted = true;
  });
  
  $: if (mounted && $page?.route?.id) {
    // Determine active route based on current page
    const currentPath = $page.url.pathname;
    const activeItem = items.find(item => 
      currentPath === item.href || 
      (item.href !== '/' && currentPath.startsWith(item.href))
    );
    activeRoute = activeItem?.id || 'dashboard';
  }
  
  function handleNavigation(href: string) {
    // Add haptic feedback for mobile devices
    if ('vibrate' in navigator) {
      navigator.vibrate(10);
    }
  }
</script>

<nav class="bottom-nav mobile-only safe-area-bottom" aria-label="Mobile navigation">
  {#each items as item (item.id)}
    <a 
      href={item.href}
      class="bottom-nav-item"
      class:active={activeRoute === item.id}
      on:click={() => handleNavigation(item.href)}
      aria-label={item.label}
      role="tab"
      aria-selected={activeRoute === item.id}
    >
      <div class="bottom-nav-icon">
        <Icon name={item.icon} size="24" />
        {#if item.badge && item.badge > 0}
          <span class="bottom-nav-badge" aria-label="{item.badge} notifications">
            {item.badge > 99 ? '99+' : item.badge}
          </span>
        {/if}
      </div>
      <span class="bottom-nav-label">{item.label}</span>
    </a>
  {/each}
</nav>

<style>
  .bottom-nav {
    display: none;
  }
  
  @media (max-width: 768px) {
    .bottom-nav {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: var(--color-surface);
      border-top: 1px solid var(--color-border);
      padding: var(--spacing-xs) 0;
      display: flex;
      justify-content: space-around;
      z-index: var(--z-fixed);
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow-lg);
    }
  }
  
  .bottom-nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xs);
    min-height: 56px;
    flex: 1;
    text-decoration: none;
    color: var(--color-text-muted);
    transition: all var(--transition-fast);
    border-radius: 8px;
    margin: 0 2px;
    position: relative;
  }
  
  .bottom-nav-item:active {
    transform: scale(0.95);
    background: var(--color-surface-hover);
  }
  
  .bottom-nav-item.active {
    color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.1);
  }
  
  .bottom-nav-icon {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    margin-bottom: 2px;
  }
  
  .bottom-nav-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: var(--color-danger);
    color: white;
    border-radius: 10px;
    padding: 1px 5px;
    font-size: 0.625rem;
    font-weight: 600;
    min-width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid var(--color-surface);
  }
  
  .bottom-nav-label {
    font-size: 0.75rem;
    font-weight: 500;
    line-height: 1;
    text-align: center;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .bottom-nav-item.active .bottom-nav-label {
    font-weight: 600;
  }
  
  /* Animation for active state */
  .bottom-nav-item.active .bottom-nav-icon {
    animation: bounce 0.3s ease;
  }
  
  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-2px); }
  }
  
  /* Hide on desktop */
  @media (min-width: 769px) {
    .bottom-nav {
      display: none !important;
    }
  }
</style>