<script lang="ts">
  export let currentPath: string = '';
  
  interface NavItem {
    title: string;
    url: string;
    icon?: string;
    badge?: number;
  }

  const navItems: NavItem[] = [
    { title: 'Dashboard', url: '/', icon: '🏠' },
    { title: 'Services', url: '/services', icon: '🐳' },
    { title: 'Containers', url: '/containers', icon: '📦' },
    { title: 'Images', url: '/images', icon: '💿' },
    { title: 'Networks', url: '/networks', icon: '🌐' },
    { title: 'Volumes', url: '/volumes', icon: '💾' },
    { title: 'Monitoring', url: '/monitoring', icon: '📊' },
    { title: 'Security', url: '/security', icon: '🔒' },
    { title: 'Settings', url: '/settings', icon: '⚙️' }
  ];

  function isActive(url: string): boolean {
    if (url === '/') {
      return currentPath === '/';
    }
    return currentPath.startsWith(url);
  }
</script>

<nav class="hidden lg:flex lg:space-x-8" aria-label="Main navigation">
  {#each navItems as item}
    <a
      href={item.url}
      class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors duration-200
        {isActive(item.url)
          ? 'border-green-500 text-gray-900 dark:text-white'
          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-300 dark:hover:text-gray-100'}"
      aria-current={isActive(item.url) ? 'page' : undefined}
    >
      {#if item.icon}
        <span class="mr-2" aria-hidden="true">{item.icon}</span>
      {/if}
      {item.title}
      {#if item.badge}
        <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          {item.badge}
        </span>
      {/if}
    </a>
  {/each}
</nav>