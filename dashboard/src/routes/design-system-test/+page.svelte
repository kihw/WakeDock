<!--
  Design System Test Page
  Tests all atomic and molecular components
-->
<script lang="ts">
  import {
    Button,
    Input,
    Badge,
    Card,
    LoadingSpinner,
    Toast,
    Avatar,
  } from '$lib/components/ui/atoms';
  import { SearchInput, DataTable, FormField } from '$lib/components/ui/molecules';
  import { theme } from '$lib/utils/theme';

  let searchValue = '';
  let inputValue = '';
  let showToast = false;

  // Generate dynamic sample data for design system testing
  const generateSampleData = () => {
    const services = ['Web Server', 'API Gateway', 'Database', 'Cache', 'Queue'];
    const statuses = ['running', 'stopped', 'restarting'];
    
    return services.map((name, index) => ({
      id: index + 1,
      name,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      cpu: Math.round(Math.random() * 100 * 10) / 10
    }));
  };

  let sampleData = generateSampleData();

  const columns = [
    { key: 'name', label: 'Service Name' },
    { key: 'status', label: 'Status' },
    { key: 'cpu', label: 'CPU Usage' },
  ];

  function handleSearch(event) {
    searchValue = event.detail.value;
  }

  function toggleTheme() {
    theme.toggle();
  }

  function showToastMessage() {
    showToast = true;
    setTimeout(() => {
      showToast = false;
    }, 3000);
  }
</script>

<svelte:head>
  <title>Design System Test - WakeDock</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
  <div class="max-w-4xl mx-auto space-y-8">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
        WakeDock Design System Test
      </h1>
      <p class="text-gray-600 dark:text-gray-400">Testing all atomic and molecular components</p>
    </div>

    <!-- Theme Toggle -->
    <div class="flex justify-center mb-8">
      <Button variant="ghost" on:click={toggleTheme}>Toggle Theme</Button>
    </div>

    <!-- Atomic Components -->
    <Card>
      <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">Atomic Components</h2>

        <div class="space-y-6">
          <!-- Buttons -->
          <div>
            <h3 class="text-lg font-medium mb-3">Buttons</h3>
            <div class="flex flex-wrap gap-2">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="success">Success</Button>
              <Button variant="warning">Warning</Button>
              <Button variant="error">Error</Button>
              <Button variant="ghost">Ghost</Button>
            </div>
          </div>

          <!-- Input -->
          <div>
            <h3 class="text-lg font-medium mb-3">Input</h3>
            <Input
              bind:value={inputValue}
              placeholder="Enter text..."
              label="Test Input"
              helperText="This is a helper text"
            />
          </div>

          <!-- Badges -->
          <div>
            <h3 class="text-lg font-medium mb-3">Badges</h3>
            <div class="flex flex-wrap gap-2">
              <Badge variant="success">Running</Badge>
              <Badge variant="error">Stopped</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="info">Info</Badge>
              <Badge variant="neutral">Neutral</Badge>
            </div>
          </div>

          <!-- Avatar -->
          <div>
            <h3 class="text-lg font-medium mb-3">Avatar</h3>
            <div class="flex gap-2">
              <Avatar initials="JD" />
              <Avatar initials="AB" variant="success" />
              <Avatar initials="CD" variant="warning" />
            </div>
          </div>

          <!-- Loading Spinner -->
          <div>
            <h3 class="text-lg font-medium mb-3">Loading Spinner</h3>
            <LoadingSpinner />
          </div>
        </div>
      </div>
    </Card>

    <!-- Molecular Components -->
    <Card>
      <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">Molecular Components</h2>

        <div class="space-y-6">
          <!-- Search Input -->
          <div>
            <h3 class="text-lg font-medium mb-3">Search Input</h3>
            <SearchInput placeholder="Search services..." on:search={handleSearch} />
            {#if searchValue}
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Searching for: {searchValue}
              </p>
            {/if}
          </div>

          <!-- Form Field -->
          <div>
            <h3 class="text-lg font-medium mb-3">Form Field</h3>
            <FormField
              label="Service Name"
              type="text"
              placeholder="Enter service name"
              required
              helperText="This field is required"
            />
          </div>

          <!-- Data Table -->
          <div>
            <h3 class="text-lg font-medium mb-3">Data Table</h3>
            <DataTable {columns} data={sampleData} searchable={true} sortable={true} />
          </div>
        </div>
      </div>
    </Card>

    <!-- Toast Test -->
    <div class="text-center">
      <Button variant="success" on:click={showToastMessage}>Show Toast</Button>
    </div>
  </div>
</div>

<!-- Toast Component -->
{#if showToast}
  <div class="fixed top-4 right-4 z-50">
    <Toast
      variant="success"
      title="Success!"
      message="Design system is working correctly!"
      on:dismiss={() => (showToast = false)}
    />
  </div>
{/if}
