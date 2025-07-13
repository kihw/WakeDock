<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { page } from '$app/stores';
  import { browser } from '$app/environment';
  import Icon from '$lib/components/Icon.svelte';
  
  export let isOpen = false;
  export let menuItems: Array<{
    id: string;
    label: string;
    icon: string;
    href: string;
    badge?: number;
    section?: string;
  }> = [];
  
  const dispatch = createEventDispatcher();
  
  let menuElement: HTMLElement;
  let overlayElement: HTMLElement;
  let startY = 0;
  let currentY = 0;
  let isDragging = false;
  
  // Group menu items by section
  $: groupedItems = menuItems.reduce((acc, item) => {
    const section = item.section || 'main';
    if (!acc[section]) acc[section] = [];
    acc[section].push(item);
    return acc;
  }, {} as Record<string, typeof menuItems>);
  
  $: activeRoute = $page?.url?.pathname || '/';
  
  onMount(() => {
    if (!browser) return;
    
    // Handle escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeMenu();
      }
    };
    
    // Prevent background scroll when menu is open
    const handleBodyScroll = () => {
      if (isOpen) {
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
      } else {
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    handleBodyScroll();
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    };
  });
  
  $: if (browser && isOpen !== undefined) {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
    } else {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    }
  }
  
  function closeMenu() {
    isOpen = false;
    dispatch('close');
    
    // Add haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate(10);
    }
  }
  
  function handleOverlayClick() {
    closeMenu();
  }
  
  function handleMenuItemClick(href: string) {
    closeMenu();
    
    // Add haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate(20);
    }
  }
  
  // Touch gesture handling for swipe to close
  function handleTouchStart(e: TouchEvent) {
    startY = e.touches[0].clientY;
    isDragging = true;
  }
  
  function handleTouchMove(e: TouchEvent) {
    if (!isDragging) return;
    
    currentY = e.touches[0].clientY;
    const deltaY = currentY - startY;
    
    // Only allow upward swipe to close
    if (deltaY < 0) {
      const progress = Math.abs(deltaY) / 200; // 200px for full close
      const opacity = Math.max(0.3, 1 - progress);
      const transform = Math.min(deltaY, 0);
      
      if (menuElement) {
        menuElement.style.transform = `translateY(${transform}px)`;
        menuElement.style.opacity = opacity.toString();
      }
    }
  }
  
  function handleTouchEnd() {
    if (!isDragging) return;
    
    const deltaY = currentY - startY;
    
    if (deltaY < -100) { // Swipe up more than 100px to close
      closeMenu();
    }
    
    // Reset transform
    if (menuElement) {
      menuElement.style.transform = '';
      menuElement.style.opacity = '';
    }
    
    isDragging = false;
  }
  
  function isActiveRoute(href: string): boolean {
    if (href === '/') {
      return activeRoute === '/';
    }
    return activeRoute.startsWith(href);
  }
</script>

<!-- Overlay -->
{#if isOpen}
  <div 
    class="mobile-nav-overlay"
    class:open={isOpen}
    bind:this={overlayElement}
    on:click={handleOverlayClick}
    on:keydown={(e) => e.key === 'Enter' && handleOverlayClick()}
    role="button"
    tabindex="0"
    aria-label="Close menu"
  ></div>
{/if}

<!-- Menu Drawer -->
<div 
  class="mobile-nav-drawer"
  class:open={isOpen}
  bind:this={menuElement}
  on:touchstart={handleTouchStart}
  on:touchmove={handleTouchMove}
  on:touchend={handleTouchEnd}
  role="navigation"
  aria-label="Mobile navigation menu"
  aria-hidden={!isOpen}
>
  <!-- Menu Header -->
  <div class="mobile-nav-header safe-area-top">
    <div class="mobile-nav-brand">
      <Icon name="docker" size="32" />
      <div class="mobile-nav-brand-text">
        <h2>WakeDock</h2>
        <p>Container Management</p>
      </div>
    </div>
    <button 
      class="mobile-nav-close"
      on:click={closeMenu}
      aria-label="Close navigation menu"
    >
      <Icon name="x" size="24" />
    </button>
  </div>
  
  <!-- Swipe Indicator -->
  <div class="mobile-swipe-indicator">
    <div class="swipe-handle"></div>
    <span class="swipe-text">Swipe up to close</span>
  </div>
  
  <!-- Menu Content -->
  <div class="mobile-nav-content">
    {#each Object.entries(groupedItems) as [section, items]}
      {#if section !== 'main'}
        <div class="mobile-nav-section">
          <h3 class="mobile-nav-section-title">
            {section.charAt(0).toUpperCase() + section.slice(1)}
          </h3>
        </div>
      {/if}
      
      {#each items as item (item.id)}
        <a 
          href={item.href}
          class="mobile-nav-item"
          class:active={isActiveRoute(item.href)}
          on:click={() => handleMenuItemClick(item.href)}
          role="menuitem"
        >
          <div class="mobile-nav-icon">
            <Icon name={item.icon} size="24" />
          </div>
          <span class="mobile-nav-label">{item.label}</span>
          {#if item.badge && item.badge > 0}
            <span class="mobile-nav-badge">
              {item.badge > 99 ? '99+' : item.badge}
            </span>
          {/if}
          <div class="mobile-nav-arrow">
            <Icon name="chevron-right" size="16" />
          </div>
        </a>
      {/each}
    {/each}
  </div>
  
  <!-- Menu Footer -->
  <div class="mobile-nav-footer safe-area-bottom">
    <div class="mobile-nav-user">
      <div class="mobile-nav-avatar">
        <Icon name="user" size="20" />
      </div>
      <div class="mobile-nav-user-info">
        <p class="mobile-nav-username">Admin User</p>
        <p class="mobile-nav-role">Administrator</p>
      </div>
    </div>
    <button class="mobile-nav-settings" aria-label="Settings">
      <Icon name="settings" size="20" />
    </button>
  </div>
</div>

<style>
  .mobile-nav-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: var(--z-overlay);
    opacity: 0;
    visibility: hidden;
    transition: all var(--transition-normal);
  }
  
  .mobile-nav-overlay.open {
    opacity: 1;
    visibility: visible;
  }
  
  .mobile-nav-drawer {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 320px;
    max-width: 85vw;
    background: var(--color-surface);
    border-right: 1px solid var(--color-border);
    transform: translateX(-100%);
    transition: transform var(--transition-smooth);
    z-index: var(--z-modal);
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    display: flex;
    flex-direction: column;
  }
  
  .mobile-nav-drawer.open {
    transform: translateX(0);
  }
  
  .mobile-nav-header {
    padding: var(--spacing-lg);
    background: var(--color-primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
  
  .mobile-nav-brand {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }
  
  .mobile-nav-brand-text h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
  }
  
  .mobile-nav-brand-text p {
    margin: 0;
    font-size: 0.875rem;
    opacity: 0.9;
  }
  
  .mobile-nav-close {
    background: none;
    border: none;
    color: white;
    padding: var(--spacing-xs);
    border-radius: 6px;
    cursor: pointer;
    transition: background-color var(--transition-fast);
  }
  
  .mobile-nav-close:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .mobile-swipe-indicator {
    padding: var(--spacing-sm);
    text-align: center;
    border-bottom: 1px solid var(--color-border-light);
    background: var(--color-surface-glass);
  }
  
  .swipe-handle {
    width: 32px;
    height: 4px;
    background: var(--color-text-muted);
    border-radius: 2px;
    margin: 0 auto var(--spacing-xs);
    opacity: 0.5;
  }
  
  .swipe-text {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }
  
  .mobile-nav-content {
    flex: 1;
    padding: var(--spacing-sm) 0;
  }
  
  .mobile-nav-section {
    padding: var(--spacing-md) var(--spacing-lg) var(--spacing-sm);
  }
  
  .mobile-nav-section-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0;
  }
  
  .mobile-nav-item {
    display: flex;
    align-items: center;
    padding: var(--spacing-md) var(--spacing-lg);
    color: var(--color-text);
    text-decoration: none;
    border-bottom: 1px solid var(--color-border-light);
    min-height: 60px;
    transition: all var(--transition-fast);
    position: relative;
  }
  
  .mobile-nav-item:active {
    background-color: var(--color-surface-hover);
    transform: scale(0.98);
  }
  
  .mobile-nav-item.active {
    background-color: rgba(var(--color-primary-rgb), 0.1);
    color: var(--color-primary);
    font-weight: 600;
  }
  
  .mobile-nav-item.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--color-primary);
  }
  
  .mobile-nav-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: var(--spacing-md);
    flex-shrink: 0;
    border-radius: 8px;
    background: var(--color-surface-glass);
  }
  
  .mobile-nav-item.active .mobile-nav-icon {
    background: var(--color-primary);
    color: white;
  }
  
  .mobile-nav-label {
    flex: 1;
    font-size: 1rem;
  }
  
  .mobile-nav-badge {
    background: var(--color-danger);
    color: white;
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    min-width: 20px;
    text-align: center;
    margin-right: var(--spacing-sm);
  }
  
  .mobile-nav-arrow {
    color: var(--color-text-muted);
    transition: transform var(--transition-fast);
  }
  
  .mobile-nav-item:active .mobile-nav-arrow {
    transform: translateX(4px);
  }
  
  .mobile-nav-footer {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--color-border);
    background: var(--color-surface-glass);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
  
  .mobile-nav-user {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    flex: 1;
  }
  
  .mobile-nav-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--color-primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .mobile-nav-user-info {
    flex: 1;
    min-width: 0;
  }
  
  .mobile-nav-username {
    margin: 0;
    font-weight: 600;
    font-size: 0.875rem;
    line-height: 1.2;
  }
  
  .mobile-nav-role {
    margin: 0;
    font-size: 0.75rem;
    color: var(--color-text-muted);
    line-height: 1.2;
  }
  
  .mobile-nav-settings {
    background: none;
    border: none;
    color: var(--color-text-muted);
    padding: var(--spacing-xs);
    border-radius: 6px;
    cursor: pointer;
    transition: all var(--transition-fast);
  }
  
  .mobile-nav-settings:hover {
    background: var(--color-surface-hover);
    color: var(--color-text);
  }
  
  /* Hide on desktop */
  @media (min-width: 769px) {
    .mobile-nav-overlay,
    .mobile-nav-drawer {
      display: none !important;
    }
  }
</style>