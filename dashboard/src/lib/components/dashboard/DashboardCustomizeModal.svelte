<script lang="ts">
  import { Eye, EyeOff, RotateCcw } from 'lucide-svelte';
  import { createEventDispatcher } from 'svelte';
  import Button from '../ui/atoms/Button.svelte';
  import Modal from '../ui/organisms/Modal.svelte';

  interface WidgetConfig {
    id: string;
    component: any;
    size: 'small' | 'medium' | 'large';
    position: { x: number; y: number };
    props?: any;
    visible?: boolean;
  }

  export let show = false;
  export let currentLayout: WidgetConfig[] = [];

  const dispatch = createEventDispatcher<{
    save: { layout: WidgetConfig[] };
  }>();

  // Available widgets
  const availableWidgets = [
    {
      id: 'system-overview',
      name: 'System Overview',
      description: 'CPU, Memory, and Disk usage',
      icon: '🖥️',
      defaultSize: 'large' as const,
    },
    {
      id: 'services-overview',
      name: 'Services Overview',
      description: 'Total, running, stopped services count',
      icon: '📊',
      defaultSize: 'medium' as const,
    },
    {
      id: 'running-services',
      name: 'Running Services',
      description: 'List of currently running services',
      icon: '🚀',
      defaultSize: 'medium' as const,
    },
    {
      id: 'quick-actions',
      name: 'Quick Actions',
      description: 'Start all, stop all, deploy buttons',
      icon: '⚡',
      defaultSize: 'small' as const,
    },
  ];

  // Working copy of layout
  let workingLayout = [...currentLayout];

  // Add visible property if not present
  workingLayout = workingLayout.map((widget) => ({
    ...widget,
    visible: widget.visible !== false,
  }));

  // Default layout for reset
  const defaultLayout: WidgetConfig[] = [
    {
      id: 'system-overview',
      component: null,
      size: 'large',
      position: { x: 0, y: 0 },
      visible: true,
    },
    {
      id: 'services-overview',
      component: null,
      size: 'medium',
      position: { x: 3, y: 0 },
      visible: true,
    },
    {
      id: 'running-services',
      component: null,
      size: 'medium',
      position: { x: 0, y: 2 },
      visible: true,
    },
    {
      id: 'quick-actions',
      component: null,
      size: 'small',
      position: { x: 2, y: 2 },
      visible: true,
    },
  ];

  function toggleWidgetVisibility(widgetId: string) {
    workingLayout = workingLayout.map((widget) =>
      widget.id === widgetId ? { ...widget, visible: !widget.visible } : widget
    );
  }

  function changeWidgetSize(widgetId: string, newSize: 'small' | 'medium' | 'large') {
    workingLayout = workingLayout.map((widget) =>
      widget.id === widgetId ? { ...widget, size: newSize } : widget
    );
  }

  function resetToDefault() {
    workingLayout = [...defaultLayout];
  }

  function handleSave() {
    dispatch('save', { layout: workingLayout });
  }

  function handleCancel() {
    // Reset working layout to original
    workingLayout = [...currentLayout];
    show = false;
  }

  // Get widget info by id
  function getWidgetInfo(widgetId: string) {
    return availableWidgets.find((w) => w.id === widgetId);
  }
</script>

<Modal bind:show title="Customize Dashboard" size="large">
  <div class="customize-dashboard">
    <!-- Header -->
    <div class="customize-header">
      <div class="header-info">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Dashboard Layout</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Customize which widgets to show and how they're arranged
        </p>
      </div>

      <Button variant="outline" size="sm" on:click={resetToDefault} class="flex items-center gap-2">
        <RotateCcw class="h-4 w-4" />
        Reset to Default
      </Button>
    </div>

    <!-- Widget Configuration -->
    <div class="widget-config">
      <h4 class="section-title">Widgets</h4>

      <div class="widget-list">
        {#each workingLayout as widget (widget.id)}
          {@const info = getWidgetInfo(widget.id)}
          {#if info}
            <div class="widget-item" class:disabled={!widget.visible}>
              <!-- Widget Info -->
              <div class="widget-info">
                <div class="widget-icon">
                  {info.icon}
                </div>
                <div class="widget-details">
                  <h5 class="widget-name">{info.name}</h5>
                  <p class="widget-description">{info.description}</p>
                </div>
              </div>

              <!-- Widget Controls -->
              <div class="widget-controls">
                <!-- Visibility Toggle -->
                <button
                  type="button"
                  class="control-btn"
                  class:active={widget.visible}
                  on:click={() => toggleWidgetVisibility(widget.id)}
                  aria-label={widget.visible ? 'Hide widget' : 'Show widget'}
                >
                  {#if widget.visible}
                    <Eye class="h-4 w-4" />
                  {:else}
                    <EyeOff class="h-4 w-4" />
                  {/if}
                </button>

                <!-- Size Selector -->
                <div class="size-selector">
                  <label class="size-label">Size:</label>
                  <select
                    bind:value={widget.size}
                    class="size-select"
                    disabled={!widget.visible}
                    on:change={(e) => changeWidgetSize(widget.id, e.target.value)}
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                  </select>
                </div>
              </div>
            </div>
          {/if}
        {/each}
      </div>
    </div>

    <!-- Preview Section -->
    <div class="preview-section">
      <h4 class="section-title">Layout Preview</h4>
      <div class="layout-preview">
        <div class="preview-grid">
          {#each workingLayout.filter((w) => w.visible) as widget}
            {@const info = getWidgetInfo(widget.id)}
            {#if info}
              <div
                class="preview-widget {widget.size}"
                style="grid-column: span {widget.size === 'large'
                  ? '3'
                  : widget.size === 'medium'
                    ? '2'
                    : '1'};"
              >
                <div class="preview-widget-content">
                  <span class="preview-icon">{info.icon}</span>
                  <span class="preview-name">{info.name}</span>
                </div>
              </div>
            {/if}
          {/each}
        </div>
      </div>
    </div>
  </div>

  <!-- Modal Actions -->
  <svelte:fragment slot="actions">
    <Button variant="outline" on:click={handleCancel}>Cancel</Button>
    <Button variant="primary" on:click={handleSave}>Save Layout</Button>
  </svelte:fragment>
</Modal>

<style>
  .customize-dashboard {
    @apply space-y-6;
  }

  .customize-header {
    @apply flex items-start justify-between;
  }

  .header-info {
    @apply flex-1;
  }

  .section-title {
    @apply text-base font-semibold text-gray-900 dark:text-white mb-4;
  }

  .widget-list {
    @apply space-y-3;
  }

  .widget-item {
    @apply flex items-center justify-between p-4 rounded-lg border;
    @apply border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700;
    @apply transition-all duration-200;
  }

  .widget-item.disabled {
    @apply opacity-50 bg-gray-50 dark:bg-gray-800;
  }

  .widget-info {
    @apply flex items-center gap-3 flex-1;
  }

  .widget-icon {
    @apply text-2xl;
  }

  .widget-details {
    @apply flex-1 min-w-0;
  }

  .widget-name {
    @apply text-sm font-medium text-gray-900 dark:text-white;
  }

  .widget-description {
    @apply text-xs text-gray-500 dark:text-gray-400 mt-0.5;
  }

  .widget-controls {
    @apply flex items-center gap-3;
  }

  .control-btn {
    @apply p-2 rounded-md border border-gray-300 dark:border-gray-600;
    @apply text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300;
    @apply transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500;
  }

  .control-btn.active {
    @apply bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-600;
    @apply text-green-600 dark:text-green-400;
  }

  .size-selector {
    @apply flex items-center gap-2;
  }

  .size-label {
    @apply text-xs font-medium text-gray-700 dark:text-gray-300;
  }

  .size-select {
    @apply text-xs border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1;
    @apply bg-white dark:bg-gray-700 text-gray-900 dark:text-white;
    @apply focus:outline-none focus:ring-2 focus:ring-green-500;
  }

  .size-select:disabled {
    @apply opacity-50 cursor-not-allowed;
  }

  .preview-section {
    @apply border-t border-gray-200 dark:border-gray-600 pt-6;
  }

  .layout-preview {
    @apply border border-gray-200 dark:border-gray-600 rounded-lg p-4;
    @apply bg-gray-50 dark:bg-gray-800;
  }

  .preview-grid {
    @apply grid grid-cols-6 gap-2;
  }

  .preview-widget {
    @apply aspect-square rounded border border-gray-300 dark:border-gray-600;
    @apply bg-white dark:bg-gray-700 flex items-center justify-center;
    @apply min-h-[60px];
  }

  .preview-widget.small {
    @apply col-span-1;
  }

  .preview-widget.medium {
    @apply col-span-2;
  }

  .preview-widget.large {
    @apply col-span-3;
  }

  .preview-widget-content {
    @apply text-center;
  }

  .preview-icon {
    @apply block text-lg mb-1;
  }

  .preview-name {
    @apply block text-xs font-medium text-gray-600 dark:text-gray-400;
  }
</style>
