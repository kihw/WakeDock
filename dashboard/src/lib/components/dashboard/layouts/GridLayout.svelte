<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  interface WidgetConfig {
    id: string;
    component: any;
    size: 'small' | 'medium' | 'large';
    position: { x: number; y: number };
    props?: any;
  }

  export let widgets: WidgetConfig[] = [];
  export let dashboardData: any = null;
  export let editable: boolean = false;

  const dispatch = createEventDispatcher<{
    widgetMoved: { widgetId: string; newPosition: { x: number; y: number } };
    widgetResized: { widgetId: string; newSize: 'small' | 'medium' | 'large' };
  }>();

  // Grid configuration
  const gridCols = 4;
  const gridGap = 16; // px

  $: sortedWidgets = widgets.sort((a, b) => {
    if (a.position.y !== b.position.y) {
      return a.position.y - b.position.y;
    }
    return a.position.x - b.position.x;
  });
</script>

<div class="dashboard-grid" class:editable>
  {#each sortedWidgets as widget (widget.id)}
    <div 
      class="widget-container"
      data-widget-id={widget.id}
      style="grid-column: span {widget.size === 'small' ? 1 : widget.size === 'medium' ? 2 : 3}; grid-row: span {widget.size === 'large' ? 2 : 1};"
    >
      <svelte:component 
        this={widget.component} 
        {...(widget.props || {})}
        data={dashboardData}
        on:refresh
        on:configure
        on:expand
      />
    </div>
  {/each}
</div>

<style>
  .dashboard-grid {
    @apply grid gap-4 p-4;
    grid-template-columns: repeat(4, 1fr);
    grid-auto-rows: minmax(200px, auto);
  }

  .widget-container {
    @apply min-h-0; /* Allow grid items to shrink */
  }

  .dashboard-grid.editable .widget-container {
    @apply cursor-move;
  }

  /* Responsive adjustments */
  @media (max-width: 1024px) {
    .dashboard-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .widget-container {
      grid-column: span 1 !important;
    }
  }

  @media (max-width: 640px) {
    .dashboard-grid {
      grid-template-columns: 1fr;
      @apply p-2 gap-2;
    }

    .widget-container {
      grid-column: span 1 !important;
      grid-row: span 1 !important;
    }
  }
</style>