<!--
  Service Logs Modal
  Modal for viewing service logs with filtering and search
-->
<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import Modal from './Modal.svelte';
  import Button from '../forms/Button.svelte';
  import Input from '../forms/Input.svelte';
  import Select from '../forms/Select.svelte';
  import Icon from '../Icon.svelte';
  import { api } from '../../config/api';
  import { logger } from '../../utils/logger';

  // Props
  export let isOpen = false;
  export let serviceId: string;
  export let serviceName: string;

  // Events
  const dispatch = createEventDispatcher<{
    close: void;
    download: { logs: string[]; filename: string };
  }>();

  // State
  let logs = writable<string[]>([]);
  let filteredLogs = writable<string[]>([]);
  let isLoading = false;
  let error: string | null = null;
  let autoRefresh = false;
  let searchTerm = '';
  let logLevel = 'all';
  let maxLines = 1000;
  let refreshInterval: number;
  let logsContainer: HTMLElement;
  let shouldAutoScroll = true;

  // Log levels for filtering
  const logLevels = [
    { value: 'all', label: 'All Levels' },
    { value: 'error', label: 'Error' },
    { value: 'warn', label: 'Warning' },
    { value: 'info', label: 'Info' },
    { value: 'debug', label: 'Debug' },
  ];

  // Line count options
  const lineOptions = [
    { value: 100, label: '100 lines' },
    { value: 500, label: '500 lines' },
    { value: 1000, label: '1000 lines' },
    { value: 5000, label: '5000 lines' },
    { value: 0, label: 'All lines' },
  ];

  // Load logs
  async function loadLogs() {
    if (!serviceId) return;

    isLoading = true;
    error = null;

    try {
      const response = await api.getServiceLogs(serviceId, maxLines);

      if (response.success && response.data) {
        const logLines = Array.isArray(response.data)
          ? response.data
          : response.data.split('\n').filter((line) => line.trim());

        logs.set(logLines);
        filterLogs();

        // Auto scroll to bottom if enabled
        if (shouldAutoScroll && logsContainer) {
          setTimeout(() => {
            logsContainer.scrollTop = logsContainer.scrollHeight;
          }, 50);
        }
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load logs';
      logger.error('Failed to load service logs:', err);
    } finally {
      isLoading = false;
    }
  }

  // Filter logs based on search term and log level
  function filterLogs() {
    logs.subscribe((allLogs) => {
      let filtered = [...allLogs];

      // Filter by log level
      if (logLevel !== 'all') {
        const levelPattern = new RegExp(`\\b${logLevel}\\b`, 'i');
        filtered = filtered.filter((log) => levelPattern.test(log));
      }

      // Filter by search term
      if (searchTerm.trim()) {
        const searchPattern = new RegExp(searchTerm, 'i');
        filtered = filtered.filter((log) => searchPattern.test(log));
      }

      filteredLogs.set(filtered);
    })();
  }

  // Toggle auto refresh
  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;

    if (autoRefresh) {
      refreshInterval = setInterval(loadLogs, 5000); // Refresh every 5 seconds
    } else {
      clearInterval(refreshInterval);
    }
  }

  // Clear logs
  function clearLogs() {
    logs.set([]);
    filteredLogs.set([]);
  }

  // Download logs
  function downloadLogs() {
    filteredLogs.subscribe((currentLogs) => {
      const filename = `${serviceName}-logs-${new Date().toISOString().split('T')[0]}.txt`;
      dispatch('download', { logs: currentLogs, filename });
    })();
  }

  // Copy logs to clipboard
  async function copyLogs() {
    try {
      const currentLogs = get(filteredLogs);
      await navigator.clipboard.writeText(currentLogs.join('\n'));
      // Show success notification (you could add a toast here)
    } catch (err) {
      logger.error('Failed to copy logs to clipboard:', err);
    }
  }

  // Scroll handling
  function handleScroll() {
    if (!logsContainer) return;

    const { scrollTop, scrollHeight, clientHeight } = logsContainer;
    const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 5;
    shouldAutoScroll = isAtBottom;
  }

  // Scroll to bottom
  function scrollToBottom() {
    if (logsContainer) {
      logsContainer.scrollTop = logsContainer.scrollHeight;
      shouldAutoScroll = true;
    }
  }

  // Scroll to top
  function scrollToTop() {
    if (logsContainer) {
      logsContainer.scrollTop = 0;
      shouldAutoScroll = false;
    }
  }

  // Format log line for display
  function formatLogLine(line: string): { timestamp: string; level: string; message: string } {
    // Try to parse timestamp and log level from the line
    const timestampMatch = line.match(/^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\.\d]*[Z]?)/);
    const levelMatch = line.match(/\b(ERROR|WARN|INFO|DEBUG|TRACE)\b/i);

    const timestamp = timestampMatch ? timestampMatch[1] : '';
    const level = levelMatch ? levelMatch[1].toUpperCase() : '';
    const message = line
      .replace(timestampMatch?.[0] || '', '')
      .replace(levelMatch?.[0] || '', '')
      .trim();

    return { timestamp, level, message };
  }

  // Get log level color class
  function getLogLevelColor(level: string): string {
    switch (level.toLowerCase()) {
      case 'error':
        return 'text-red-400';
      case 'warn':
        return 'text-yellow-400';
      case 'info':
        return 'text-blue-400';
      case 'debug':
        return 'text-gray-400';
      default:
        return 'text-gray-300';
    }
  }

  // Reactive statements
  $: if (searchTerm || logLevel) {
    filterLogs();
  }

  // Lifecycle
  onMount(() => {
    if (isOpen && serviceId) {
      loadLogs();
    }
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  // Watch for modal open/close
  $: if (isOpen && serviceId) {
    loadLogs();
  } else if (!isOpen && refreshInterval) {
    clearInterval(refreshInterval);
    autoRefresh = false;
  }
</script>

<Modal bind:isOpen on:close={() => dispatch('close')} size="xl">
  <div slot="header" class="flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <Icon name="file-text" class="w-5 h-5 text-gray-400" />
      <h3 class="text-lg font-semibold text-white">
        Service Logs: {serviceName}
      </h3>
    </div>

    <div class="flex items-center space-x-2">
      <!-- Auto refresh toggle -->
      <Button
        variant={autoRefresh ? 'primary' : 'secondary'}
        size="sm"
        on:click={toggleAutoRefresh}
        class="flex items-center space-x-1"
      >
        <Icon name={autoRefresh ? 'pause' : 'play'} class="w-4 h-4" />
        <span>{autoRefresh ? 'Pause' : 'Auto'}</span>
      </Button>

      <!-- Refresh button -->
      <Button
        variant="secondary"
        size="sm"
        on:click={loadLogs}
        disabled={isLoading}
        class="flex items-center space-x-1"
      >
        <Icon name="refresh-cw" class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" />
        <span>Refresh</span>
      </Button>
    </div>
  </div>

  <div slot="body" class="flex flex-col h-full space-y-4">
    <!-- Controls -->
    <div class="flex flex-wrap items-center gap-4 p-4 bg-gray-800 rounded-lg">
      <!-- Search -->
      <div class="flex-1 min-w-64">
        <Input type="text" placeholder="Search logs..." bind:value={searchTerm} class="w-full">
          <Icon slot="icon" name="search" class="w-4 h-4" />
        </Input>
      </div>

      <!-- Log level filter -->
      <div class="min-w-40">
        <Select bind:value={logLevel} options={logLevels} placeholder="Log Level" />
      </div>

      <!-- Max lines -->
      <div class="min-w-32">
        <Select
          bind:value={maxLines}
          options={lineOptions}
          placeholder="Lines"
          on:change={loadLogs}
        />
      </div>

      <!-- Actions -->
      <div class="flex items-center space-x-2">
        <Button
          variant="secondary"
          size="sm"
          on:click={copyLogs}
          class="flex items-center space-x-1"
        >
          <Icon name="copy" class="w-4 h-4" />
          <span>Copy</span>
        </Button>

        <Button
          variant="secondary"
          size="sm"
          on:click={downloadLogs}
          class="flex items-center space-x-1"
        >
          <Icon name="download" class="w-4 h-4" />
          <span>Download</span>
        </Button>

        <Button
          variant="secondary"
          size="sm"
          on:click={clearLogs}
          class="flex items-center space-x-1"
        >
          <Icon name="trash-2" class="w-4 h-4" />
          <span>Clear</span>
        </Button>
      </div>
    </div>

    <!-- Error display -->
    {#if error}
      <div class="p-4 bg-red-900/20 border border-red-500 rounded-lg">
        <div class="flex items-center space-x-2">
          <Icon name="alert-circle" class="w-5 h-5 text-red-400" />
          <span class="text-red-400 font-medium">Error loading logs:</span>
        </div>
        <p class="mt-1 text-red-300 text-sm">{error}</p>
        <Button variant="secondary" size="sm" on:click={loadLogs} class="mt-2">Retry</Button>
      </div>
    {/if}

    <!-- Logs display -->
    <div class="flex-1 flex flex-col min-h-0">
      <div class="flex items-center justify-between mb-2">
        <div class="text-sm text-gray-400">
          {#if $filteredLogs.length !== $logs.length}
            Showing {$filteredLogs.length} of {$logs.length} lines
          {:else}
            {$logs.length} lines
          {/if}
        </div>

        <div class="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            on:click={scrollToTop}
            class="flex items-center space-x-1"
          >
            <Icon name="arrow-up" class="w-4 h-4" />
            <span>Top</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            on:click={scrollToBottom}
            class="flex items-center space-x-1"
          >
            <Icon name="arrow-down" class="w-4 h-4" />
            <span>Bottom</span>
          </Button>
        </div>
      </div>

      <div
        bind:this={logsContainer}
        on:scroll={handleScroll}
        class="flex-1 overflow-auto bg-gray-900 border border-gray-700 rounded-lg p-4 font-mono text-sm"
        style="max-height: 500px;"
      >
        {#if isLoading && $logs.length === 0}
          <div class="flex items-center justify-center h-32">
            <div class="flex items-center space-x-2 text-gray-400">
              <Icon name="loader-2" class="w-5 h-5 animate-spin" />
              <span>Loading logs...</span>
            </div>
          </div>
        {:else if $filteredLogs.length === 0}
          <div class="flex items-center justify-center h-32">
            <div class="text-center text-gray-400">
              {#if $logs.length === 0}
                <Icon name="file-text" class="w-8 h-8 mx-auto mb-2" />
                <p>No logs available</p>
              {:else}
                <Icon name="search" class="w-8 h-8 mx-auto mb-2" />
                <p>No logs match your filters</p>
              {/if}
            </div>
          </div>
        {:else}
          {#each $filteredLogs as line, index (index)}
            {@const { timestamp, level, message } = formatLogLine(line)}
            <div class="flex items-start space-x-2 py-1 hover:bg-gray-800/50 rounded">
              <span class="text-gray-500 text-xs min-w-0 flex-shrink-0">
                {index + 1}
              </span>
              {#if timestamp}
                <span class="text-gray-400 text-xs min-w-0 flex-shrink-0">
                  {timestamp}
                </span>
              {/if}
              {#if level}
                <span class="text-xs font-medium min-w-0 flex-shrink-0 {getLogLevelColor(level)}">
                  {level}
                </span>
              {/if}
              <span class="text-gray-300 min-w-0 flex-1 break-all">
                {message || line}
              </span>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </div>

  <div slot="footer" class="flex items-center justify-between">
    <div class="text-sm text-gray-400">
      {#if autoRefresh}
        <div class="flex items-center space-x-1">
          <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span>Auto-refreshing every 5 seconds</span>
        </div>
      {/if}
    </div>

    <div class="flex items-center space-x-2">
      <Button variant="secondary" on:click={() => dispatch('close')}>Close</Button>
    </div>
  </div>
</Modal>

<style>
  /* Custom scrollbar for logs container */
  :global(.logs-container::-webkit-scrollbar) {
    width: 8px;
  }

  :global(.logs-container::-webkit-scrollbar-track) {
    background: #374151;
    border-radius: 4px;
  }

  :global(.logs-container::-webkit-scrollbar-thumb) {
    background: #6b7280;
    border-radius: 4px;
  }

  :global(.logs-container::-webkit-scrollbar-thumb:hover) {
    background: #9ca3af;
  }
</style>
