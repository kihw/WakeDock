<script lang="ts">
  import '../app.css';
  import '@fontsource/inter';
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import { page } from '$app/stores';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Header from '$lib/components/Header.svelte';
  import { initializeConfig } from '$lib/config/loader.js';

  export let data: any = {};

  let sidebarOpen = writable(false);
  let mounted = false;

  // Close sidebar on route change (mobile)
  $: if ($page.url.pathname && mounted) {
    if (window.innerWidth <= 768) {
      sidebarOpen.set(false);
    }
  }

  onMount(async () => {
    console.log('🚀 Layout mounting - initializing configuration...');
    
    // Initialize configuration FIRST before anything else
    await initializeConfig();
    
    mounted = true;

    // Handle escape key for sidebar
    function handleKeydown(event: KeyboardEvent) {
      if (event.key === 'Escape' && $sidebarOpen) {
        sidebarOpen.set(false);
      }
    }

    // Handle resize events
    function handleResize() {
      // Auto-close sidebar on mobile when resizing to desktop
      if (window.innerWidth > 768 && $sidebarOpen) {
        sidebarOpen.set(false);
      }
    }

    // Add event listeners
    document.addEventListener('keydown', handleKeydown);
    window.addEventListener('resize', handleResize);

    // Initialize theme from localStorage
    const savedTheme = localStorage.getItem('wakedock_theme');
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      // Default to system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    function handleThemeChange(e: MediaQueryListEvent) {
      const currentTheme = localStorage.getItem('wakedock_theme');
      if (!currentTheme || currentTheme === 'auto') {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      }
    }
    mediaQuery.addEventListener('change', handleThemeChange);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeydown);
      window.removeEventListener('resize', handleResize);
      mediaQuery.removeEventListener('change', handleThemeChange);
    };
  });
</script>

<div class="app" class:sidebar-open={$sidebarOpen}>
  <!-- Sidebar -->
  <Sidebar open={sidebarOpen} />

  <!-- Main Content Area -->
  <div class="main-container">
    <!-- Header -->
    <Header {sidebarOpen} />

    <!-- Main Content -->
    <main class="main-content">
      <div class="content-wrapper">
        <slot />
      </div>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
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
    min-height: 100vh;
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
    overflow: hidden;
  }

  .content-wrapper {
    flex: 1;
    padding: var(--spacing-lg);
    overflow-y: auto;
    position: relative;
    background: var(--color-background);

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
    max-width: 1400px;
    margin: 0 auto;
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
    .content-wrapper {
      padding: var(--spacing-md);
    }

    .footer-content {
      flex-direction: column;
      gap: var(--spacing-md);
      text-align: center;
    }

    .footer-links {
      order: 1;
    }

    .footer-version {
      order: 2;
    }

    .footer-left {
      order: 3;
    }

    .scroll-to-top {
      bottom: var(--spacing-lg);
      right: var(--spacing-lg);
      width: 44px;
      height: 44px;
    }
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
  [data-theme='dark'] .footer-text {
    color: var(--color-text-secondary);
  }

  [data-theme='dark'] .footer-link:hover {
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
