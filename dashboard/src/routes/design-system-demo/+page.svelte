<script lang="ts">
  import { patterns } from '$lib/design-system/composition-patterns';
  import { variants, colors } from '$lib/design-system/tokens';
  import { themeManager, isDarkMode } from '$lib/design-system/theme-manager';
  import ThemeSwitcher from '$lib/components/ui/molecules/ThemeSwitcher.svelte';
  import LoadingSpinnerBackup from '$lib/components/ui/atoms/LoadingSpinnerBackup.svelte';
  import PrimaryButton from '$lib/components/ui/atoms/PrimaryButton.svelte';
  import SecondaryButton from '$lib/components/ui/atoms/SecondaryButton.svelte';
  import Alert from '$lib/components/ui/atoms/Alert.svelte';
  import Card from '$lib/components/ui/atoms/Card.svelte';
  import FormField from '$lib/components/ui/molecules/FormField.svelte';

  let activeTab = 'patterns';
  let showModal = false;
  let loadingVariant: 'spinner' | 'pulse' | 'dots' = 'spinner';

  const tabs = [
    { id: 'patterns', label: 'Composition Patterns' },
    { id: 'theming', label: 'Advanced Theming' },
    { id: 'components', label: 'Component Showcase' }
  ];

  // Sample data for demonstrations
  const sampleData = [
    { id: 1, name: 'Container Alpha', status: 'running', cpu: '12%' },
    { id: 2, name: 'Database Beta', status: 'stopped', cpu: '0%' },
    { id: 3, name: 'API Gateway', status: 'running', cpu: '8%' }
  ];
</script>

<svelte:head>
  <title>WakeDock Design System Demo</title>
  <meta name="description" content="Advanced design system features and composition patterns" />
</svelte:head>

<div class="demo-page">
  <!-- Header with theme switcher -->
  <header class="{patterns.form.card.header}">
    <h1 class="text-3xl font-bold text-secondary-900">Design System Demo</h1>
    <p class="text-secondary-600 mt-2">Showcase of advanced design system features</p>
    
    <div class="flex justify-end mt-4">
      <ThemeSwitcher compact />
    </div>
  </header>

  <!-- Navigation tabs -->
  <nav class="{patterns.navigation.tabs.container}">
    <div class="{patterns.navigation.tabs.list}">
      {#each tabs as tab}
        <button
          type="button"
          on:click={() => activeTab = tab.id}
          class="{activeTab === tab.id ? patterns.navigation.tabs.activeTab : patterns.navigation.tabs.tab}"
        >
          {tab.label}
        </button>
      {/each}
    </div>
  </nav>

  <main class="p-6 space-y-8">
    
    {#if activeTab === 'patterns'}
      <!-- Composition Patterns Demo -->
      <section>
        <h2 class="text-2xl font-bold text-secondary-900 mb-6">Composition Patterns</h2>
        
        <!-- Form Patterns -->
        <div class="space-y-8">
          <div>
            <h3 class="text-lg font-semibold text-secondary-800 mb-4">Form Layouts</h3>
            
            <!-- Inline Form -->
            <Card variant="base" class="p-6 mb-4">
              <h4 class="text-md font-medium text-secondary-700 mb-3">Inline Form Pattern</h4>
              <div class="{patterns.form.inline.container}">
                <div class="{patterns.form.inline.field}">
                  <FormField label="Search" type="text" placeholder="Enter search term..." />
                </div>
                <div class="{patterns.form.inline.action}">
                  <PrimaryButton>Search</PrimaryButton>
                </div>
              </div>
            </Card>

            <!-- Card Form -->
            <div class="{patterns.form.card.container}">
              <div class="{patterns.form.card.header}">
                <h4 class="text-lg font-semibold">Card Form Pattern</h4>
                <p class="text-secondary-600 text-sm">Example of card-based form layout</p>
              </div>
              
              <div class="{patterns.form.card.body}">
                <FormField label="Name" type="text" required />
                <FormField label="Email" type="email" required />
                <FormField label="Message" type="textarea" rows={3} />
              </div>
              
              <div class="{patterns.form.card.footer}">
                <SecondaryButton>Cancel</SecondaryButton>
                <PrimaryButton>Submit</PrimaryButton>
              </div>
            </div>
          </div>

          <!-- Data Patterns -->
          <div>
            <h3 class="text-lg font-semibold text-secondary-800 mb-4">Data Display Patterns</h3>
            
            <!-- Dashboard Grid -->
            <div class="{patterns.data.dashboard.container}">
              <div class="{patterns.data.dashboard.widget}">
                <div class="{patterns.data.dashboard.widgetHeader}">
                  <h4 class="{patterns.data.dashboard.widgetTitle}">Total Containers</h4>
                </div>
                <div class="{patterns.data.dashboard.widgetValue}">24</div>
              </div>
              
              <div class="{patterns.data.dashboard.widget}">
                <div class="{patterns.data.dashboard.widgetHeader}">
                  <h4 class="{patterns.data.dashboard.widgetTitle}">CPU Usage</h4>
                </div>
                <div class="{patterns.data.dashboard.widgetValue}">67%</div>
              </div>
              
              <div class="{patterns.data.dashboard.widget}">
                <div class="{patterns.data.dashboard.widgetHeader}">
                  <h4 class="{patterns.data.dashboard.widgetTitle}">Memory</h4>
                </div>
                <div class="{patterns.data.dashboard.widgetValue}">4.2GB</div>
              </div>
            </div>

            <!-- Action List -->
            <div class="{patterns.data.actionList.container} mt-6">
              {#each sampleData as item}
                <div class="{patterns.data.actionList.item}">
                  <div class="{patterns.data.actionList.content}">
                    <h5 class="font-medium text-secondary-900">{item.name}</h5>
                    <p class="text-sm text-secondary-600">CPU: {item.cpu}</p>
                  </div>
                  <div class="{patterns.data.actionList.actions}">
                    <span class="px-2 py-1 text-xs rounded-full {item.status === 'running' ? 'bg-success-100 text-success-700' : 'bg-error-100 text-error-700'}">
                      {item.status}
                    </span>
                    <SecondaryButton size="sm">Manage</SecondaryButton>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </section>

    {:else if activeTab === 'theming'}
      <!-- Advanced Theming Demo -->
      <section>
        <h2 class="text-2xl font-bold text-secondary-900 mb-6">Advanced Theming</h2>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Theme Controls -->
          <Card variant="elevated" class="p-6">
            <h3 class="text-lg font-semibold text-secondary-800 mb-4">Theme Controls</h3>
            <ThemeSwitcher />
          </Card>

          <!-- Theme Demo -->
          <Card variant="elevated" class="p-6">
            <h3 class="text-lg font-semibold text-secondary-800 mb-4">Theme Preview</h3>
            <div class="space-y-4">
              <Alert variant="info">
                Current theme: {$isDarkMode ? 'Dark' : 'Light'} mode
              </Alert>
              
              <div class="flex gap-3">
                <PrimaryButton>Primary Action</PrimaryButton>
                <SecondaryButton>Secondary Action</SecondaryButton>
              </div>
              
              <div class="p-4 border-2 border-dashed border-secondary-300 rounded-lg">
                <p class="text-secondary-600">
                  This content adapts automatically to your theme selection using CSS custom properties
                  and our advanced theme manager.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>

    {:else if activeTab === 'components'}
      <!-- Component Showcase -->
      <section>
        <h2 class="text-2xl font-bold text-secondary-900 mb-6">Component Showcase</h2>
        
        <div class="space-y-8">
          <!-- Loading Components -->
          <Card variant="elevated" class="p-6">
            <h3 class="text-lg font-semibold text-secondary-800 mb-4">Enhanced Loading Components</h3>
            
            <div class="space-y-6">
              <div>
                <h4 class="font-medium text-secondary-700 mb-3">Loading Variants</h4>
                <div class="flex items-center gap-4 mb-4">
                  <label class="flex items-center gap-2">
                    <input type="radio" bind:group={loadingVariant} value="spinner" />
                    Spinner
                  </label>
                  <label class="flex items-center gap-2">
                    <input type="radio" bind:group={loadingVariant} value="pulse" />
                    Pulse
                  </label>
                  <label class="flex items-center gap-2">
                    <input type="radio" bind:group={loadingVariant} value="dots" />
                    Dots
                  </label>
                </div>
                
                <div class="flex items-center gap-8">
                  <LoadingSpinnerBackup 
                    size="small" 
                    variant={loadingVariant}
                    text="Small"
                  />
                  <LoadingSpinnerBackup 
                    size="medium" 
                    variant={loadingVariant}
                    text="Medium"
                  />
                  <LoadingSpinnerBackup 
                    size="large" 
                    variant={loadingVariant}
                    text="Large"
                  />
                </div>
              </div>
            </div>
          </Card>

          <!-- Alert Components -->
          <Card variant="elevated" class="p-6">
            <h3 class="text-lg font-semibold text-secondary-800 mb-4">Alert Components</h3>
            <div class="space-y-3">
              <Alert variant="success">Operation completed successfully!</Alert>
              <Alert variant="warning">Please review your configuration.</Alert>
              <Alert variant="error">An error occurred while processing.</Alert>
              <Alert variant="info">New features are available in this update.</Alert>
            </div>
          </Card>
        </div>
      </section>
    {/if}
  </main>
</div>

<style>
  .demo-page {
    max-width: 1200px;
    margin: 0 auto;
    min-height: 100vh;
    background: var(--color-bg-primary);
  }

  /* Override any global styles that might interfere */
  :global(.demo-page *) {
    box-sizing: border-box;
  }

  /* Ensure proper spacing in complex layouts */
  .demo-page main > section:not(:last-child) {
    margin-bottom: 3rem;
  }
</style>