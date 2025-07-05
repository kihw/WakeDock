<!-- Settings Content Container -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { SystemSettings } from '$lib/types/settings';
  import GeneralSettings from './sections/GeneralSettings.svelte';
  import DockerSettings from './sections/DockerSettings.svelte';
  import CaddySettings from './sections/CaddySettings.svelte';
  import SecuritySettings from './sections/SecuritySettings.svelte';
  import LoggingSettings from './sections/LoggingSettings.svelte';
  import MonitoringSettings from './sections/MonitoringSettings.svelte';

  export let settings: SystemSettings;
  export let activeTab = 'general';

  const dispatch = createEventDispatcher<{
    testConnection: { type: 'docker' | 'caddy' };
  }>();

  function handleTestConnection(event: CustomEvent<{ type: 'docker' | 'caddy' }>) {
    dispatch('testConnection', event.detail);
  }
</script>

<div class="settings-content">
  <div class="content-container">
    {#if activeTab === 'general'}
      <div role="tabpanel" id="panel-general" aria-labelledby="tab-general">
        <GeneralSettings bind:settings={settings.general} />
      </div>
    {:else if activeTab === 'docker'}
      <div role="tabpanel" id="panel-docker" aria-labelledby="tab-docker">
        <DockerSettings bind:settings={settings.docker} on:testConnection={handleTestConnection} />
      </div>
    {:else if activeTab === 'caddy'}
      <div role="tabpanel" id="panel-caddy" aria-labelledby="tab-caddy">
        <CaddySettings bind:settings={settings.caddy} on:testConnection={handleTestConnection} />
      </div>
    {:else if activeTab === 'security'}
      <div role="tabpanel" id="panel-security" aria-labelledby="tab-security">
        <SecuritySettings bind:settings={settings.security} />
      </div>
    {:else if activeTab === 'logging'}
      <div role="tabpanel" id="panel-logging" aria-labelledby="tab-logging">
        <LoggingSettings bind:settings={settings.logging} />
      </div>
    {:else if activeTab === 'monitoring'}
      <div role="tabpanel" id="panel-monitoring" aria-labelledby="tab-monitoring">
        <MonitoringSettings bind:settings={settings.monitoring} />
      </div>
    {/if}
  </div>
</div>

<style>
  .settings-content {
    @apply p-6;
  }

  .content-container {
    @apply max-w-4xl;
  }

  /* Tab panel fade-in animation */
  [role='tabpanel'] {
    animation: fadeIn 0.2s ease-in-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
