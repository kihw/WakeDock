<!--
  Design System Test Page
  Tests all atomic and molecular components
-->
<script lang="ts">
  import {
    UnifiedButton,
    BaseInput,
    Badge,
    Card,
    LoadingSpinner,
    Toast,
    Avatar,
  } from '$lib/components/ui/atoms';
  import { 
    FormInput, 
    FieldInput, 
    SearchInput, 
    DataTable, 
    FormField 
  } from '$lib/components/ui/molecules';
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
      <UnifiedButton variant="ghost" on:click={toggleTheme}>Toggle Theme</UnifiedButton>
    </div>

    <!-- Atomic Components -->
    <Card>
      <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">Atomic Components</h2>

        <div class="space-y-6">
          <!-- Buttons -->
          <div>
            <h3 class="text-lg font-medium mb-3">UnifiedButton (Refactored)</h3>
            <div class="flex flex-wrap gap-2">
              <UnifiedButton variant="primary">Primary</UnifiedButton>
              <UnifiedButton variant="secondary">Secondary</UnifiedButton>
              <UnifiedButton variant="success">Success</UnifiedButton>
              <UnifiedButton variant="warning">Warning</UnifiedButton>
              <UnifiedButton variant="error">Error</UnifiedButton>
              <UnifiedButton variant="ghost">Ghost</UnifiedButton>
            </div>
            <div class="flex flex-wrap gap-2 mt-3">
              <UnifiedButton variant="primary" size="sm">Small</UnifiedButton>
              <UnifiedButton variant="primary" size="md">Medium</UnifiedButton>
              <UnifiedButton variant="primary" size="lg">Large</UnifiedButton>
              <UnifiedButton variant="primary" disabled>Disabled</UnifiedButton>
            </div>
          </div>

          <!-- Input System Refactored -->
          <div>
            <h3 class="text-lg font-medium mb-3">Input System (Refactored)</h3>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium mb-2">BaseInput (Atomic)</label>
                <BaseInput placeholder="Basic input without decorations" />
              </div>
              <div>
                <label class="block text-sm font-medium mb-2">FormInput (Molecular)</label>
                <FormInput
                  label="Email Address"
                  type="email"
                  placeholder="Enter your email"
                  helperText="We'll never share your email"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-2">FieldInput (Enhanced)</label>
                <FieldInput
                  label="Search Query"
                  leftIcon="search"
                  clearable
                  placeholder="Search with icons and actions..."
                />
              </div>
            </div>
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

    <!-- Design Tokens Showcase -->
    <Card variant="elevated">
      <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">Design Tokens Integration</h2>
        <div class="space-y-6">
          <!-- Card Variants -->
          <div>
            <h3 class="text-lg font-medium mb-3">Card Variants (Unified)</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card variant="default" padding="md">
                <div class="text-center py-4">
                  <h4 class="font-medium">Default</h4>
                  <p class="text-sm text-gray-600">Base styling</p>
                </div>
              </Card>
              <Card variant="elevated" padding="md">
                <div class="text-center py-4">
                  <h4 class="font-medium">Elevated</h4>
                  <p class="text-sm text-gray-600">Enhanced shadow</p>
                </div>
              </Card>
              <Card variant="outlined" padding="md">
                <div class="text-center py-4">
                  <h4 class="font-medium">Outlined</h4>
                  <p class="text-sm text-gray-600">Border emphasis</p>
                </div>
              </Card>
              <Card variant="filled" padding="md">
                <div class="text-center py-4">
                  <h4 class="font-medium">Filled</h4>
                  <p class="text-sm text-gray-600">Background tint</p>
                </div>
              </Card>
            </div>
          </div>

          <!-- Design System Progress -->
          <div>
            <h3 class="text-lg font-medium mb-3">Refactoring Progress</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                <span class="font-medium text-green-800">✅ TASK-UI-001: Button Unification</span>
                <Badge variant="success">Completed</Badge>
              </div>
              <div class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                <span class="font-medium text-green-800">✅ TASK-UI-002: Input System Refactoring</span>
                <Badge variant="success">Completed</Badge>
              </div>
              <div class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                <span class="font-medium text-green-800">✅ TASK-UI-003: Card Unification</span>
                <Badge variant="success">Completed</Badge>
              </div>
              <div class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                <span class="font-medium text-green-800">✅ TASK-UI-004: Design Tokens Integration</span>
                <Badge variant="success">Completed</Badge>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Toast Test -->
    <div class="text-center">
      <UnifiedButton variant="success" on:click={showToastMessage}>Show Toast</UnifiedButton>
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
