<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let activeTab = 'monitoring';

  const dispatch = createEventDispatcher<{
    tabChange: { tab: string };
  }>();

  const tabs = [
    { id: 'monitoring', label: 'Security Monitoring', icon: '🛡️' },
    { id: 'audit', label: 'Audit Logs', icon: '📋' },
  ];

  function handleTabClick(tabId: string) {
    activeTab = tabId;
    dispatch('tabChange', { tab: tabId });
  }
</script>

<div class="border-b border-gray-200 dark:border-gray-700 mb-6">
  <nav class="-mb-px flex space-x-8" aria-label="Security Tabs">
    {#each tabs as tab}
      <button
        type="button"
        class="group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab ===
        tab.id
          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'}"
        on:click={() => handleTabClick(tab.id)}
        aria-current={activeTab === tab.id ? 'page' : undefined}
      >
        <span class="mr-2 text-lg">{tab.icon}</span>
        {tab.label}
      </button>
    {/each}
  </nav>
</div>
