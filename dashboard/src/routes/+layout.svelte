<script lang="ts">
  import '../app.css';
  import '@fontsource/inter';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Header from '$lib/components/Header.svelte';
  import BottomNavigation from '$lib/components/mobile/BottomNavigation.svelte';
  import MobileMenu from '$lib/components/mobile/MobileMenu.svelte';
  import { initializeConfig } from '$lib/config/loader.js';
  import { sidebarOpen, mounted, closeSidebarOnMobile, handleEscapeKey, handleResize } from '$lib/stores/layout.js';
  import { initializeTheme } from '$lib/utils/theme.js';

  export let data: any = {};

  // Mobile menu state
  let mobileMenuOpen = false;
  
  // Navigation items for mobile
  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', href: '/' },
    { id: 'services', label: 'Services', icon: 'container', href: '/services' },
    { id: 'monitoring', label: 'Monitor', icon: 'activity', href: '/monitoring' },
    { id: 'logs', label: 'Logs', icon: 'file-text', href: '/logs' },
    { id: 'backup', label: 'Backup', icon: 'download', href: '/backup', section: 'tools' },
    { id: 'analytics', label: 'Analytics', icon: 'bar-chart', href: '/analytics', section: 'tools' },
    { id: 'settings', label: 'Settings', icon: 'settings', href: '/settings', section: 'admin' },
    { id: 'users', label: 'Users', icon: 'users', href: '/users', section: 'admin' },
    { id: 'profile', label: 'Profile', icon: 'user', href: '/profile', section: 'account' }
  ];

  // Toggle mobile menu
  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }
  
  // Handle mobile menu close
  function handleMobileMenuClose() {
    mobileMenuOpen = false;
  }

  // Close sidebar on route change (mobile)
  $: if ($page.url.pathname && $mounted) {
    closeSidebarOnMobile();
    // Also close mobile menu on route change
    mobileMenuOpen = false;
  }

  onMount(async () => {
    console.log('🚀 Layout mounting - initializing configuration...');

    // Initialize configuration FIRST before anything else
    await initializeConfig();

    // Initialize theme
    initializeTheme();

    mounted.set(true);

    // Handle escape key for sidebar and mobile menu
    function handleKeydown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        if (mobileMenuOpen) {
          mobileMenuOpen = false;
        } else if ($sidebarOpen) {
          handleEscapeKey(event);
        }
      }
    }

    // Add event listeners
    document.addEventListener('keydown', handleKeydown);
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeydown);
      window.removeEventListener('resize', handleResize);
    };
  });
</script>

<div class="app" class:sidebar-open={$sidebarOpen} class:mobile-menu-open={mobileMenuOpen}>
  <!-- Desktop Sidebar -->
  <Sidebar open={sidebarOpen} />

  <!-- Mobile Menu -->
  <MobileMenu 
    bind:isOpen={mobileMenuOpen} 
    menuItems={navigationItems}
    on:close={handleMobileMenuClose}
  />

  <!-- Main Content Area -->
  <div class="main-container">
    <!-- Header -->
    <Header {sidebarOpen} {toggleMobileMenu} />

    <!-- Main Content -->
    <main class="main-content" class:mobile-content={true}>
      <div class="content-wrapper safe-area-top">
        <slot />
      </div>
    </main>

    <!-- Desktop Footer -->
    <footer class="app-footer hidden-mobile">
      <div class="footer-content">
        <div class="footer-left">
          <p class="footer-text">© 2024 WakeDock. Made with ❤️ for Docker enthusiasts.</p>
        </div>
        <div class="footer-right">
          <div class="footer-links">
            <a href="/docs" class="footer-link">Documentation</a>
            <a href="/api" class="footer-link">API</a>
            <a href="/support" class="footer-link">Support</a>
            <a href="https://github.com/wakedock" class="footer-link" target="_blank">GitHub</a>
          </div>
          <div class="footer-version">
            <span class="version-badge">v1.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  </div>

  <!-- Mobile Bottom Navigation -->
  <BottomNavigation items={navigationItems.slice(0, 5)} />
</div>

<!-- Global Loading Indicator -->
<div class="loading-bar" class:loading={false}></div>

<!-- Scroll to Top Button -->
<button
  class="scroll-to-top"
  class:visible={false}
  on:click={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
>
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <polyline points="18,15 12,9 6,15" />
  </svg>
</button>

<style>
  .app {
    display: flex;
    flex: 1;
    background: var(--color-background);
    position: relative;
  }

  .main-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    transition: margin-left var(--transition-normal);
    position: relative;
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }

  .content-wrapper {
    flex: 1;
    padding: var(--spacing-lg);
    overflow-y: auto;
    position: relative;
    background: var(--color-background);
    width: 100%;

    /* Smooth scrolling */
    scroll-behavior: smooth;

    /* Custom scrollbar */
    scrollbar-width: thin;
    scrollbar-color: var(--color-border) transparent;
  }

  .content-wrapper::-webkit-scrollbar {
    width: 8px;
  }

  .content-wrapper::-webkit-scrollbar-track {
    background: transparent;
  }

  .content-wrapper::-webkit-scrollbar-thumb {
    background: var(--color-border);
    border-radius: var(--radius-full);
    border: 2px solid transparent;
    background-clip: content-box;
  }

  .content-wrapper::-webkit-scrollbar-thumb:hover {
    background: var(--color-text-muted);
    background-clip: content-box;
  }

  /* Footer */
  .app-footer {
    background: var(--gradient-surface);
    border-top: 1px solid var(--color-border-light);
    padding: var(--spacing-lg);
    margin-top: auto;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
  }

  .footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-lg);
  }

  .footer-left {
    flex: 1;
  }

  .footer-text {
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    margin: 0;
  }

  .footer-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
  }

  .footer-links {
    display: flex;
    gap: var(--spacing-md);
  }

  .footer-link {
    color: var(--color-text-secondary);
    text-decoration: none;
    font-size: 0.875rem;
    transition: color var(--transition-normal);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius);
  }

  .footer-link:hover {
    color: var(--color-primary);
    background: rgba(59, 130, 246, 0.1);
  }

  .footer-version {
    display: flex;
    align-items: center;
  }

  .version-badge {
    background: var(--gradient-primary);
    color: white;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 500;
    font-family: monospace;
  }

  /* Global Loading Bar */
  .loading-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
    transform: translateX(-100%);
    transition: transform var(--transition-normal);
    z-index: 9999;
  }

  .loading-bar.loading {
    animation: loading-slide 2s ease-in-out infinite;
  }

  /* Scroll to Top Button */
  .scroll-to-top {
    position: fixed;
    bottom: var(--spacing-xl);
    right: var(--spacing-xl);
    width: 48px;
    height: 48px;
    background: var(--gradient-primary);
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-normal);
    opacity: 0;
    visibility: hidden;
    transform: translateY(20px);
    z-index: 1000;
  }

  .scroll-to-top.visible {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
  }

  .scroll-to-top:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
  }

  /* Desktop Layout */
  @media (min-width: 769px) {
    .app {
      display: grid;
      grid-template-columns: 280px 1fr;
    }

    .main-container {
      margin-left: 0;
    }
  }

  /* Mobile Layout */
  @media (max-width: 768px) {
    .app {
      display: flex;
      flex-direction: column;
    }
    
    .app.mobile-menu-open {
      overflow: hidden;
    }
    
    .main-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      margin-left: 0;
    }
    
    .main-content.mobile-content {
      padding-bottom: 70px; /* Space for bottom navigation */
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
    }
    
    .content-wrapper {
      padding: var(--spacing-md);
      flex: 1;
    }
    
    .hidden-mobile {
      display: none !important;
    }

    .footer-content {
      flex-direction: column;
      gap: var(--spacing-md);
      text-align: center;
    }

    .footer-links {
      order: 1;
    }
    
    /* Mobile-specific app footer adjustments */
    .app-footer {
      padding: var(--spacing-md);
    }
    
    .app-footer .footer-content {
      padding: 0;
    }
  }
  
  /* Tablet adjustments */
  @media (min-width: 576px) and (max-width: 768px) {
    .content-wrapper {
      padding: var(--spacing-lg);
    }
    
    .main-content.mobile-content {
      padding-bottom: 0; /* No bottom nav on tablet */
    }
  }
  
  /* Mobile-first responsive improvements */
  @media (max-width: 575px) {
    .content-wrapper {
      padding: var(--spacing-sm);
    }
    
    /* Adjust scroll-to-top button for mobile */
    .scroll-to-top {
      bottom: 80px; /* Above bottom navigation */
      right: var(--spacing-md);
      width: 48px;
      height: 48px;
    }
    
    /* Loading bar adjustments for mobile */
    .loading-bar {
      height: 2px;
    }
  }
  
  /* Additional mobile styles for footer */
  @media (max-width: 575px) {
    .footer-version {
      order: 2;
    }

    .footer-left {
      order: 3;
    }
  }

  .scroll-to-top {
    position: fixed;
    bottom: var(--spacing-lg);
    right: var(--spacing-lg);
    width: 44px;
    height: 44px;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-normal);
    z-index: var(--z-fixed);
    opacity: 0;
    visibility: hidden;
  }
  
  .scroll-to-top.visible {
    opacity: 1;
    visibility: visible;
  }

  @media (max-width: 480px) {
    .content-wrapper {
      padding: var(--spacing-sm);
    }

    .footer-links {
      flex-wrap: wrap;
      justify-content: center;
    }

    .footer-link {
      padding: var(--spacing-xs);
    }
  }

  /* Reduced Motion */
  @media (prefers-reduced-motion: reduce) {
    .content-wrapper {
      scroll-behavior: auto;
    }

    .loading-bar,
    .scroll-to-top,
    .main-container {
      transition: none;
    }
  }

  /* High Contrast Mode */
  @media (prefers-contrast: high) {
    .footer-link {
      border: 1px solid var(--color-border);
    }

    .version-badge {
      border: 1px solid var(--color-primary);
    }
  }

  /* Print Styles */
  @media print {
    .app-footer,
    .scroll-to-top,
    .loading-bar {
      display: none;
    }

    .content-wrapper {
      overflow: visible;
      padding: 0;
    }

    .main-container {
      margin: 0;
    }
  }

  /* Focus Styles for Accessibility */
  .footer-link:focus,
  .scroll-to-top:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }

  /* Dark Mode Adjustments */
  :global([data-theme='dark']) .footer-text {
    color: var(--color-text-secondary);
  }

  :global([data-theme='dark']) .footer-link:hover {
    background: rgba(59, 130, 246, 0.2);
  }

  /* Loading Animation */
  @keyframes loading-slide {
    0% {
      transform: translateX(-100%);
    }
    50% {
      transform: translateX(0%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  /* Smooth Page Transitions */
  :global(.page-transition) {
    animation: pageEnter 0.3s ease-out;
  }

  @keyframes pageEnter {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Content Loading States */
  :global(.content-loading) {
    position: relative;
    overflow: hidden;
  }

  :global(.content-loading::after) {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    animation: contentShimmer 1.5s ease-in-out infinite;
  }

  @keyframes contentShimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  /* Error Boundaries */
  :global(.error-boundary) {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--color-error);
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--radius-lg);
    margin: var(--spacing-lg);
  }

  /* Skip Link for Accessibility */
  :global(.skip-link) {
    position: absolute;
    top: -40px;
    left: 6px;
    background: var(--color-primary);
    color: white;
    padding: 8px;
    text-decoration: none;
    border-radius: var(--radius);
    z-index: 10000;
    transition: top var(--transition-normal);
  }

  :global(.skip-link:focus) {
    top: 6px;
  }
</style>
