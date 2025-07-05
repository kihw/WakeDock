<!-- Settings Navigation Tabs -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let tabs: Array<{ id: string; label: string; icon: string }> = [];
  export let activeTab = 'general';

  const dispatch = createEventDispatcher<{
    tabChange: { tab: string };
  }>();

  function handleTabClick(tabId: string) {
    if (tabId !== activeTab) {
      dispatch('tabChange', { tab: tabId });
    }
  }
</script>

<div class="settings-tabs">
  <nav class="tabs-nav" role="tablist">
    {#each tabs as tab (tab.id)}
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === tab.id}
        aria-controls="panel-{tab.id}"
        id="tab-{tab.id}"
        class="tab-button"
        class:active={activeTab === tab.id}
        on:click={() => handleTabClick(tab.id)}
      >
        <span class="tab-icon" aria-hidden="true">
          {tab.icon}
        </span>
        <span class="tab-label">
          {tab.label}
        </span>
      </button>
    {/each}
  </nav>
</div>

<style>
  .settings-tabs {
    @apply border-b border-slate-200 dark:border-slate-700;
  }

  .tabs-nav {
    @apply flex overflow-x-auto;
    scrollbar-width: none; /* Firefox */
    -ms-overflow-style: none; /* Internet Explorer 10+ */
  }

  .tabs-nav::-webkit-scrollbar {
    display: none; /* WebKit */
  }

  .tab-button {
    @apply flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors duration-200 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
  }

  .tab-button:not(.active) {
    @apply border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-600;
  }

  .tab-button.active {
    @apply border-blue-500 text-blue-600 dark:text-blue-400;
  }

  .tab-icon {
    @apply text-base leading-none;
  }

  .tab-label {
    @apply select-none;
  }

  /* Mobile responsive */
  @media (max-width: 640px) {
    .tab-button {
      @apply px-3 py-2 text-xs;
    }

    .tab-icon {
      @apply text-sm;
    }
  }
</style>
