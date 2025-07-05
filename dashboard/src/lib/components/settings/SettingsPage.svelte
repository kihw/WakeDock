<!-- Settings Page Main Container -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { SystemSettings } from '$lib/types/settings';
  import SettingsHeader from './SettingsHeader.svelte';
  import SettingsTabs from './SettingsTabs.svelte';
  import SettingsContent from './SettingsContent.svelte';

  export let settings: SystemSettings;
  export let loading = false;
  export let saving = false;
  export let hasChanges = false;
  export let activeTab = 'general';

  const dispatch = createEventDispatcher<{
    save: void;
    reset: void;
    tabChange: { tab: string };
    testConnection: { type: 'docker' | 'caddy' };
  }>();

  const tabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'docker', label: 'Docker', icon: '🐳' },
    { id: 'caddy', label: 'Caddy', icon: '🌐' },
    { id: 'security', label: 'Security', icon: '🔒' },
    { id: 'logging', label: 'Logging', icon: '📝' },
    { id: 'monitoring', label: 'Monitoring', icon: '📊' },
  ];

  function handleSave() {
    dispatch('save');
  }

  function handleReset() {
    dispatch('reset');
  }

  function handleTabChange(event: CustomEvent<{ tab: string }>) {
    activeTab = event.detail.tab;
    dispatch('tabChange', event.detail);
  }

  function handleTestConnection(event: CustomEvent<{ type: 'docker' | 'caddy' }>) {
    dispatch('testConnection', event.detail);
  }
</script>

<svelte:head>
  <title>System Settings - WakeDock</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <SettingsHeader {hasChanges} {saving} on:save={handleSave} on:reset={handleReset} />

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  {:else}
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <SettingsTabs {tabs} {activeTab} on:tabChange={handleTabChange} />

      <SettingsContent {settings} {activeTab} on:testConnection={handleTestConnection} />
    </div>
  {/if}
</div>

<style>
  .container {
    @apply max-w-6xl;
  }
</style>
