<!--
  Resource Chart Component
  Interactive chart for displaying resource usage (CPU, Memory, Network, etc.)
-->
<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { writable } from 'svelte/store';
  import Icon from '../../../Icon.svelte';
  import Button from '../../atoms/Button.svelte';
  import Select from '../../molecules/Select.svelte';

  // Props
  export let title = 'Resource Usage';
  export let data: Array<{ timestamp: Date; value: number; label?: string }> = [];
  export let type: 'line' | 'area' | 'bar' = 'line';
  export let color = '#3b82f6';
  export let height = 200;
  export let width = '100%';
  export let showGrid = true;
  export let showTooltip = true;
  export let showLegend = false;
  export let animate = true;
  export let autoRefresh = false;
  export let refreshInterval = 5000;
  export let maxDataPoints = 50;
  export let unit = '';
  export let format: 'number' | 'percentage' | 'bytes' | 'time' = 'number';
  export let threshold: { value: number; color: string; label: string } | null = null;

  // Events
  const dispatch = createEventDispatcher<{
    pointClick: { point: any; index: number };
    refresh: void;
  }>();

  // State
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let tooltipElement: HTMLDivElement;
  let refreshTimer: number;
  let isHovering = false;
  let hoveredPoint: { x: number; y: number; data: any; index: number } | null = null;

  // Chart dimensions
  let chartWidth = 0;
  let chartHeight = 0;
  let padding = { top: 20, right: 20, bottom: 40, left: 60 };

  // Time range options
  const timeRanges = [
    { value: '5m', label: '5 minutes' },
    { value: '15m', label: '15 minutes' },
    { value: '1h', label: '1 hour' },
    { value: '6h', label: '6 hours' },
    { value: '24h', label: '24 hours' },
  ];

  let selectedTimeRange = '1h';

  // Reactive data processing
  $: processedData = processData(data);
  $: if (canvas && processedData) {
    drawChart();
  }

  function processData(rawData: typeof data) {
    if (!rawData || rawData.length === 0) return [];

    // Sort by timestamp
    const sorted = [...rawData].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

    // Limit data points
    if (sorted.length > maxDataPoints) {
      const step = Math.floor(sorted.length / maxDataPoints);
      return sorted.filter((_, index) => index % step === 0);
    }

    return sorted;
  }

  function setupCanvas() {
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const devicePixelRatio = window.devicePixelRatio || 1;

    canvas.width = rect.width * devicePixelRatio;
    canvas.height = height * devicePixelRatio;

    chartWidth = canvas.width - (padding.left + padding.right) * devicePixelRatio;
    chartHeight = canvas.height - (padding.top + padding.bottom) * devicePixelRatio;

    ctx = canvas.getContext('2d')!;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    // Set canvas style dimensions
    canvas.style.width = rect.width + 'px';
    canvas.style.height = height + 'px';
  }

  function drawChart() {
    if (!ctx || !processedData.length) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate scales
    const xScale = createXScale();
    const yScale = createYScale();

    // Draw grid
    if (showGrid) {
      drawGrid(xScale, yScale);
    }

    // Draw threshold line
    if (threshold) {
      drawThreshold(yScale);
    }

    // Draw chart based on type
    switch (type) {
      case 'line':
        drawLine(xScale, yScale);
        break;
      case 'area':
        drawArea(xScale, yScale);
        break;
      case 'bar':
        drawBars(xScale, yScale);
        break;
    }

    // Draw axes
    drawAxes(xScale, yScale);
  }

  function createXScale() {
    const minTime = Math.min(...processedData.map((d) => d.timestamp.getTime()));
    const maxTime = Math.max(...processedData.map((d) => d.timestamp.getTime()));
    const range = maxTime - minTime || 1;

    return {
      domain: [minTime, maxTime],
      range: [padding.left, canvas.width / window.devicePixelRatio - padding.right],
      scale: (value: number) =>
        padding.left + ((value - minTime) / range) * (chartWidth / window.devicePixelRatio),
    };
  }

  function createYScale() {
    const values = processedData.map((d) => d.value);
    const minValue = Math.min(0, Math.min(...values));
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;

    return {
      domain: [minValue, maxValue],
      range: [canvas.height / window.devicePixelRatio - padding.bottom, padding.top],
      scale: (value: number) =>
        canvas.height / window.devicePixelRatio -
        padding.bottom -
        ((value - minValue) / range) * (chartHeight / window.devicePixelRatio),
    };
  }

  function drawGrid(xScale: any, yScale: any) {
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 2]);

    // Horizontal grid lines
    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
      const y = yScale.range[1] + (i / yTicks) * (yScale.range[0] - yScale.range[1]);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(canvas.width / window.devicePixelRatio - padding.right, y);
      ctx.stroke();
    }

    // Vertical grid lines
    const xTicks = 6;
    for (let i = 0; i <= xTicks; i++) {
      const x = xScale.range[0] + (i / xTicks) * (xScale.range[1] - xScale.range[0]);
      ctx.beginPath();
      ctx.moveTo(x, padding.top);
      ctx.lineTo(x, canvas.height / window.devicePixelRatio - padding.bottom);
      ctx.stroke();
    }

    ctx.setLineDash([]);
  }

  function drawThreshold(yScale: any) {
    if (!threshold) return;

    const y = yScale.scale(threshold.value);

    ctx.strokeStyle = threshold.color;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);

    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(canvas.width / window.devicePixelRatio - padding.right, y);
    ctx.stroke();

    ctx.setLineDash([]);
  }

  function drawLine(xScale: any, yScale: any) {
    if (processedData.length < 2) return;

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    processedData.forEach((point, index) => {
      const x = xScale.scale(point.timestamp.getTime());
      const y = yScale.scale(point.value);

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Draw points
    ctx.fillStyle = color;
    processedData.forEach((point) => {
      const x = xScale.scale(point.timestamp.getTime());
      const y = yScale.scale(point.value);

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function drawArea(xScale: any, yScale: any) {
    if (processedData.length < 2) return;

    // Create gradient
    const gradient = ctx.createLinearGradient(0, yScale.range[1], 0, yScale.range[0]);
    gradient.addColorStop(0, color + '80');
    gradient.addColorStop(1, color + '20');

    ctx.fillStyle = gradient;

    ctx.beginPath();
    // Start from bottom left
    ctx.moveTo(xScale.scale(processedData[0].timestamp.getTime()), yScale.range[0]);

    // Draw the line
    processedData.forEach((point) => {
      const x = xScale.scale(point.timestamp.getTime());
      const y = yScale.scale(point.value);
      ctx.lineTo(x, y);
    });

    // Close to bottom right
    ctx.lineTo(
      xScale.scale(processedData[processedData.length - 1].timestamp.getTime()),
      yScale.range[0]
    );
    ctx.closePath();
    ctx.fill();

    // Draw the line on top
    drawLine(xScale, yScale);
  }

  function drawBars(xScale: any, yScale: any) {
    const barWidth = ((xScale.range[1] - xScale.range[0]) / processedData.length) * 0.8;

    ctx.fillStyle = color;

    processedData.forEach((point) => {
      const x = xScale.scale(point.timestamp.getTime()) - barWidth / 2;
      const y = yScale.scale(point.value);
      const height = yScale.range[0] - y;

      ctx.fillRect(x, y, barWidth, height);
    });
  }

  function drawAxes(xScale: any, yScale: any) {
    ctx.strokeStyle = '#6b7280';
    ctx.lineWidth = 1;
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#9ca3af';

    // Y-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, canvas.height / window.devicePixelRatio - padding.bottom);
    ctx.stroke();

    // Y-axis labels
    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
      const value = yScale.domain[0] + (i / yTicks) * (yScale.domain[1] - yScale.domain[0]);
      const y = yScale.scale(value);
      const label = formatValue(value);

      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, padding.left - 10, y);
    }

    // X-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, canvas.height / window.devicePixelRatio - padding.bottom);
    ctx.lineTo(
      canvas.width / window.devicePixelRatio - padding.right,
      canvas.height / window.devicePixelRatio - padding.bottom
    );
    ctx.stroke();

    // X-axis labels
    const xTicks = 6;
    for (let i = 0; i <= xTicks; i++) {
      const time = xScale.domain[0] + (i / xTicks) * (xScale.domain[1] - xScale.domain[0]);
      const x = xScale.scale(time);
      const label = formatTime(new Date(time));

      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(label, x, canvas.height / window.devicePixelRatio - padding.bottom + 10);
    }
  }

  function formatValue(value: number): string {
    switch (format) {
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'bytes':
        return formatBytes(value);
      case 'time':
        return `${value.toFixed(1)}ms`;
      default:
        return value.toFixed(1) + (unit ? ` ${unit}` : '');
    }
  }

  function formatBytes(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }

  function formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function handleMouseMove(event: MouseEvent) {
    if (!canvas || !processedData.length) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find closest data point
    const xScale = createXScale();
    const yScale = createYScale();

    let closestPoint: { x: number; y: number; data: any; index: number } | null = null;
    let minDistance = Infinity;

    processedData.forEach((point, index) => {
      const px = xScale.scale(point.timestamp.getTime());
      const py = yScale.scale(point.value);
      const distance = Math.sqrt(Math.pow(x - px, 2) + Math.pow(y - py, 2));

      if (distance < minDistance && distance < 20) {
        minDistance = distance;
        closestPoint = { x: px, y: py, data: point, index };
      }
    });

    hoveredPoint = closestPoint;
    isHovering = !!closestPoint;

    if (closestPoint && showTooltip) {
      updateTooltip(event.clientX, event.clientY, (closestPoint as any).data);
    }
  }

  function handleMouseLeave() {
    isHovering = false;
    hoveredPoint = null;
    if (tooltipElement) {
      tooltipElement.style.display = 'none';
    }
  }

  function handleClick(event: MouseEvent) {
    if (hoveredPoint) {
      dispatch('pointClick', {
        point: hoveredPoint.data,
        index: hoveredPoint.index,
      });
    }
  }

  function updateTooltip(x: number, y: number, data: any) {
    if (!tooltipElement) return;

    tooltipElement.innerHTML = `
      <div class="font-semibold">${formatValue(data.value)}</div>
      <div class="text-sm text-gray-400">${formatTime(data.timestamp)}</div>
      ${data.label ? `<div class="text-xs text-gray-500">${data.label}</div>` : ''}
    `;

    tooltipElement.style.display = 'block';
    tooltipElement.style.left = x + 10 + 'px';
    tooltipElement.style.top = y - 10 + 'px';
  }

  function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);

    refreshTimer = window.setInterval(() => {
      dispatch('refresh');
    }, refreshInterval) as unknown as number;
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = 0;
    }
  }

  // Lifecycle
  onMount(() => {
    setupCanvas();

    if (autoRefresh) {
      startAutoRefresh();
    }

    // Handle window resize
    const handleResize = () => {
      if (canvas) {
        setupCanvas();
        drawChart();
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  });

  onDestroy(() => {
    stopAutoRefresh();
  });

  // Watch autoRefresh changes
  $: if (autoRefresh) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
</script>

<div class="bg-gray-800 rounded-lg p-4">
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-white">{title}</h3>

    <div class="flex items-center space-x-2">
      <!-- Time range selector -->
      <Select bind:value={selectedTimeRange} options={timeRanges} size="sm" class="w-32" label="" />

      <!-- Auto refresh toggle -->
      <Button
        variant={autoRefresh ? 'primary' : 'secondary'}
        size="sm"
        on:click={() => (autoRefresh = !autoRefresh)}
        class="flex items-center space-x-1"
      >
        <Icon name={autoRefresh ? 'pause' : 'play'} class="w-4 h-4" />
        <span class="hidden sm:inline">{autoRefresh ? 'Pause' : 'Auto'}</span>
      </Button>

      <!-- Manual refresh -->
      <Button
        variant="secondary"
        size="sm"
        on:click={() => dispatch('refresh')}
        class="flex items-center space-x-1"
      >
        <Icon name="refresh-cw" class="w-4 h-4" />
        <span class="hidden sm:inline">Refresh</span>
      </Button>
    </div>
  </div>

  <!-- Chart container -->
  <div class="relative" style="height: {height}px;">
    <canvas
      bind:this={canvas}
      class="w-full h-full cursor-crosshair"
      style="width: {width}; height: {height}px;"
      on:mousemove={handleMouseMove}
      on:mouseleave={handleMouseLeave}
      on:click={handleClick}
    ></canvas>

    <!-- Tooltip -->
    {#if showTooltip}
      <div
        bind:this={tooltipElement}
        class="absolute z-10 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white shadow-lg pointer-events-none"
        style="display: none;"
      ></div>
    {/if}

    <!-- No data message -->
    {#if !processedData.length}
      <div class="absolute inset-0 flex items-center justify-center">
        <div class="text-center text-gray-400">
          <Icon name="bar-chart-3" class="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No data available</p>
        </div>
      </div>
    {/if}
  </div>

  <!-- Legend -->
  {#if showLegend && threshold}
    <div class="mt-4 flex items-center justify-center space-x-6 text-sm">
      <div class="flex items-center space-x-2">
        <div class="w-4 h-0.5" style="background-color: {color};"></div>
        <span class="text-gray-300">Current</span>
      </div>
      <div class="flex items-center space-x-2">
        <div class="w-4 h-0.5 border-dashed" style="border-color: {threshold.color};"></div>
        <span class="text-gray-300">{threshold.label}</span>
      </div>
    </div>
  {/if}
</div>
