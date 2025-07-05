<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { sanitizeInput, checkRateLimit } from '$lib/utils/validation';
  import { announceToScreenReader, manageFocus } from '$lib/utils/accessibility';
  
  export let isOpen: boolean = false;
  
  const dispatch = createEventDispatcher<{
    search: { query: string; results: SearchResult[] };
    select: { item: SearchResult };
  }>();

  interface SearchResult {
    title: string;
    url: string;
    type: 'navigation' | 'service' | 'container' | 'command';
    icon?: string;
    description?: string;
  }

  let searchQuery = '';
  let searchResults: SearchResult[] = [];
  let searchInput: HTMLInputElement;
  let searchAttempts = 0;
  let isRateLimited = false;
  let selectedIndex = -1;

  const searchableItems: SearchResult[] = [
    { title: 'Dashboard', url: '/', type: 'navigation', icon: '🏠', description: 'Main dashboard overview' },
    { title: 'Services', url: '/services', type: 'navigation', icon: '🐳', description: 'Manage Docker services' },
    { title: 'Containers', url: '/containers', type: 'navigation', icon: '📦', description: 'View and manage containers' },
    { title: 'Images', url: '/images', type: 'navigation', icon: '💿', description: 'Docker images management' },
    { title: 'Networks', url: '/networks', type: 'navigation', icon: '🌐', description: 'Network configuration' },
    { title: 'Volumes', url: '/volumes', type: 'navigation', icon: '💾', description: 'Storage volumes' },
    { title: 'Monitoring', url: '/monitoring', type: 'navigation', icon: '📊', description: 'System monitoring' },
    { title: 'Security', url: '/security', type: 'navigation', icon: '🔒', description: 'Security settings' },
    { title: 'Settings', url: '/settings', type: 'navigation', icon: '⚙️', description: 'Application settings' },
    // Add more searchable items as needed
  ];

  function performSearch(query: string): SearchResult[] {
    if (query.length < 2) return [];
    
    const lowerQuery = query.toLowerCase();
    return searchableItems
      .filter(item => 
        item.title.toLowerCase().includes(lowerQuery) ||
        item.description?.toLowerCase().includes(lowerQuery)
      )
      .slice(0, 8); // Limit results
  }

  function handleSearch() {
    const sanitizedQuery = sanitizeInput(searchQuery);
    
    // Rate limiting
    const rateLimitResult = checkRateLimit('search', searchAttempts, 20, 60000);
    const allowed = typeof rateLimitResult === 'boolean' ? rateLimitResult : rateLimitResult.allowed;
    
    if (!allowed) {
      isRateLimited = true;
      announceToScreenReader('Search rate limit exceeded. Please wait before searching again.');
      return;
    }

    searchAttempts++;
    const results = performSearch(sanitizedQuery);
    searchResults = results;
    selectedIndex = -1;

    if (sanitizedQuery.length > 2) {
      announceToScreenReader(`Found ${results.length} results for "${sanitizedQuery}"`);
    }

    dispatch('search', { query: sanitizedQuery, results });
  }

  function handleKeydown(e: KeyboardEvent) {
    switch (e.key) {
      case 'Escape':
        closeSearch();
        break;
      case 'ArrowDown':
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, searchResults.length - 1);
        announceToScreenReader(`Selected ${searchResults[selectedIndex]?.title}`);
        break;
      case 'ArrowUp':
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, -1);
        if (selectedIndex >= 0) {
          announceToScreenReader(`Selected ${searchResults[selectedIndex]?.title}`);
        }
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && searchResults[selectedIndex]) {
          selectItem(searchResults[selectedIndex]);
        }
        break;
    }
  }

  function selectItem(item: SearchResult) {
    dispatch('select', { item });
    closeSearch();
    
    // Navigate to the item
    if (item.url) {
      window.location.href = item.url;
    }
  }

  function closeSearch() {
    isOpen = false;
    searchQuery = '';
    searchResults = [];
    selectedIndex = -1;
  }

  function openSearch() {
    isOpen = true;
    setTimeout(() => {
      if (searchInput) {
        manageFocus(searchInput);
        announceToScreenReader('Search opened. Type to search for services and content.');
      }
    }, 100);
  }

  // Expose openSearch function
  export { openSearch };

  $: if (searchQuery) {
    handleSearch();
  }
</script>

<div class="relative">
  <!-- Search Button -->
  <button
    type="button"
    class="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors duration-200"
    on:click={openSearch}
    aria-label="Open search"
  >
    <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
    <span class="hidden sm:block text-gray-500 dark:text-gray-300">Search...</span>
    <div class="hidden sm:flex items-center space-x-1">
      <kbd class="px-1.5 py-0.5 text-xs font-mono bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-500 rounded">⌘</kbd>
      <kbd class="px-1.5 py-0.5 text-xs font-mono bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-500 rounded">K</kbd>
    </div>
  </button>

  <!-- Search Modal -->
  {#if isOpen}
    <div class="fixed inset-0 z-50 bg-gray-500 bg-opacity-75 flex items-start justify-center pt-16 px-4">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-96 overflow-hidden">
        <!-- Search Input -->
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              bind:this={searchInput}
              bind:value={searchQuery}
              type="text"
              class="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              placeholder="Search services, containers, settings..."
              on:input={handleSearch}
              on:keydown={handleKeydown}
              disabled={isRateLimited}
            />
          </div>
          {#if isRateLimited}
            <p class="mt-2 text-sm text-red-600">Rate limit exceeded. Please wait before searching again.</p>
          {/if}
        </div>

        <!-- Search Results -->
        {#if searchResults.length > 0}
          <div class="max-h-64 overflow-y-auto">
            {#each searchResults as result, index}
              <button
                type="button"
                class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0
                  {index === selectedIndex ? 'bg-green-50 dark:bg-green-900' : ''}"
                on:click={() => selectItem(result)}
              >
                {#if result.icon}
                  <span class="text-lg" aria-hidden="true">{result.icon}</span>
                {/if}
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {result.title}
                  </p>
                  {#if result.description}
                    <p class="text-sm text-gray-500 dark:text-gray-400 truncate">
                      {result.description}
                    </p>
                  {/if}
                </div>
                <span class="text-xs text-gray-400 uppercase tracking-wide">
                  {result.type}
                </span>
              </button>
            {/each}
          </div>
        {:else if searchQuery.length > 2}
          <div class="px-4 py-8 text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">No results found for "{searchQuery}"</p>
          </div>
        {:else if searchQuery.length > 0}
          <div class="px-4 py-8 text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">Type at least 3 characters to search</p>
          </div>
        {/if}

        <!-- Footer -->
        <div class="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
          <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div class="flex items-center space-x-4">
              <div class="flex items-center space-x-1">
                <kbd class="px-1 py-0.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-xs">↑↓</kbd>
                <span>Navigate</span>
              </div>
              <div class="flex items-center space-x-1">
                <kbd class="px-1 py-0.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-xs">↵</kbd>
                <span>Select</span>
              </div>
            </div>
            <div class="flex items-center space-x-1">
              <kbd class="px-1 py-0.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-xs">esc</kbd>
              <span>Close</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>