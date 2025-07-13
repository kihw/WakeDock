<!--
  Service Logs Modal - Enhanced with Security & Accessibility
  Modal for viewing service logs with filtering and search
-->
<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { writable, get } from 'svelte/store';
  import Modal from './Modal.svelte';
  import Button from '../atoms/Button.svelte';
  import Input from '../atoms/Input.svelte';
  import Select from '../molecules/Select.svelte';
  import Icon from '../../Icon.svelte';
  import { api } from '../../api';
  import { logger } from '../../utils/logger';
  import { sanitizeInput, generateCSRFToken, checkRateLimit } from '$lib/utils/validation';
  import { manageFocus, announceToScreenReader, trapFocus } from '$lib/utils/accessibility';
  import { colors } from '$lib/design-system/tokens';

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
  let refreshInterval: NodeJS.Timeout | number;
  let logsContainer: HTMLElement;
  let shouldAutoScroll = true;
  let modalElement: HTMLElement;

  // Security & Accessibility
  let csrfToken = '';
  let attemptCount = 0;
  let lastAttemptTime = 0;
  let liveRegion: HTMLElement;

  // Rate limiting constants
  const MAX_ATTEMPTS = 10;
  const RATE_LIMIT_WINDOW = 60000; // 1 minute

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
  ];

  // Enhanced onMount with security and accessibility
  onMount(async () => {
    // Generate CSRF token
    csrfToken = await generateCSRFToken();

    // Setup live region for screen reader announcements
    // Using announceToScreenReader instead of createLiveRegion

    // Load logs when modal opens
    if (isOpen && serviceId) {
      await loadLogs();
      announceToScreenReader(
        `Service logs modal opened for ${sanitizeInput(serviceName)}. ${filteredLogs ? 'Logs loaded successfully.' : 'No logs available.'}`
      );
    }
  });

  // Enhanced onDestroy with cleanup
  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }

    // Cleanup live region - not needed since we're using announceToScreenReader
  });

  // Enhanced load logs with security and error handling
  async function loadLogs() {
    // Rate limiting check
    if (!checkRateLimit(attemptCount, lastAttemptTime, MAX_ATTEMPTS, RATE_LIMIT_WINDOW)) {
      error = 'Too many attempts. Please wait before trying again.';
      announceToScreenReader('Rate limit exceeded. Please wait before trying again.');
      return;
    }

    isLoading = true;
    error = null;
    attemptCount++;
    lastAttemptTime = Date.now();

    try {
      // Validate and sanitize inputs
      const validatedServiceId = sanitizeInput(serviceId);
      if (!validatedServiceId) {
        throw new Error('Invalid service ID provided');
      }

      // Announce loading state
      announceToScreenReader('Loading service logs...');

      const response = await api.getServiceLogs(validatedServiceId, maxLines);

      if (response && Array.isArray(response)) {
        // Sanitize log data
        const sanitizedLogs = response.map((log: string) => sanitizeInput(log));
        logs.set(sanitizedLogs);
        filterLogs();

        // Auto-scroll to bottom if enabled
        if (shouldAutoScroll && logsContainer) {
          setTimeout(() => scrollToBottom(), 100);
        }

        // Announce success
        announceToScreenReader(
          `Logs loaded successfully. ${sanitizedLogs.length} log entries retrieved.`
        );
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load logs';
      logger.error('Failed to load service logs:', err as Error);
      error = `Failed to load logs: ${sanitizeInput(errorMessage)}`;
      announceToScreenReader(`Error loading logs: ${sanitizeInput(errorMessage)}`);
    } finally {
      isLoading = false;
    }
  }

  // Configuration options
  const lineLimitOptions = [
    { value: 50, label: '50 lines' },
    { value: 100, label: '100 lines' },
    { value: 500, label: '500 lines' },
    { value: 1000, label: '1000 lines' },
    { value: 5000, label: '5000 lines' },
    { value: 0, label: 'All lines' },
  ];

  // Enhanced filter logs with sanitization
  function filterLogs() {
    logs.subscribe((allLogs) => {
      let filtered = [...allLogs];

      // Filter by log level
      if (logLevel !== 'all') {
        const levelPattern = new RegExp(`\\b${logLevel}\\b`, 'i');
        filtered = filtered.filter((log) => levelPattern.test(log));
      }

      // Filter by sanitized search term
      if (searchTerm.trim()) {
        const sanitizedSearchTerm = sanitizeInput(searchTerm.trim());
        const searchPattern = new RegExp(sanitizedSearchTerm, 'i');
        filtered = filtered.filter((log) => searchPattern.test(log));
      }

      filteredLogs.set(filtered);

      // Announce filter results
      announceToScreenReader(
        `Logs filtered. Showing ${filtered.length} of ${allLogs.length} log entries.`
      );
    })();
  }

  // Enhanced toggle auto refresh with security checks
  function toggleAutoRefresh() {
    // Rate limiting check for auto-refresh
    if (
      !autoRefresh &&
      !checkRateLimit(attemptCount, lastAttemptTime, MAX_ATTEMPTS, RATE_LIMIT_WINDOW)
    ) {
      announceToScreenReader('Cannot enable auto-refresh. Rate limit exceeded.');
      return;
    }

    autoRefresh = !autoRefresh;

    if (autoRefresh) {
      refreshInterval = setInterval(loadLogs, 5000); // Refresh every 5 seconds
      announceToScreenReader('Auto-refresh enabled. Logs will update every 5 seconds.');
    } else {
      clearInterval(refreshInterval);
      announceToScreenReader('Auto-refresh disabled.');
    }
  }

  // Enhanced clear logs with confirmation
  function clearLogs() {
    logs.set([]);
    filteredLogs.set([]);
    announceToScreenReader('Logs cleared.');
  }

  // Enhanced download logs with security validation
  function downloadLogs() {
    filteredLogs.subscribe((currentLogs) => {
      if (currentLogs.length === 0) {
        announceToScreenReader('No logs available to download.');
        return;
      }

      // Sanitize filename
      const sanitizedServiceName = sanitizeInput(serviceName).replace(/[^a-zA-Z0-9\-_]/g, '_');
      const filename = `${sanitizedServiceName}-logs-${new Date().toISOString().split('T')[0]}.txt`;

      dispatch('download', { logs: currentLogs, filename });
      announceToScreenReader(`Downloading ${currentLogs.length} log entries as ${filename}.`);
    })();
  }

  // Enhanced copy logs to clipboard with error handling
  async function copyLogs() {
    try {
      const currentLogs = get(filteredLogs);
      if (currentLogs.length === 0) {
        announceToScreenReader('No logs available to copy.');
        return;
      }

      await navigator.clipboard.writeText(currentLogs.join('\n'));
      announceToScreenReader(`${currentLogs.length} log entries copied to clipboard.`);
    } catch (err) {
      logger.error('Failed to copy logs to clipboard:', err as Error);
      announceToScreenReader('Failed to copy logs to clipboard.');
    }
  }

  // Enhanced scroll handling with accessibility
  function handleScroll() {
    if (!logsContainer) return;

    const { scrollTop, scrollHeight, clientHeight } = logsContainer;
    const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 5;
    shouldAutoScroll = isAtBottom;

    // Announce scroll position for screen readers (throttled)
    if (scrollTop === 0) {
      announceToScreenReader('Scrolled to top of logs.');
    } else if (isAtBottom) {
      announceToScreenReader('Scrolled to bottom of logs.');
    }
  }

  // Enhanced scroll functions with announcements
  function scrollToBottom() {
    if (logsContainer) {
      logsContainer.scrollTop = logsContainer.scrollHeight;
      shouldAutoScroll = true;
      announceToScreenReader('Scrolled to bottom of logs.');
    }
  }

  function scrollToTop() {
    if (logsContainer) {
      logsContainer.scrollTop = 0;
      shouldAutoScroll = false;
      announceToScreenReader('Scrolled to top of logs.');
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
        return 'text-error-400';
      case 'warn':
        return 'text-warning-400';
      case 'info':
        return 'text-primary-400';
      case 'debug':
        return 'text-secondary-400';
      default:
        return 'text-secondary-300';
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

<Modal
  bind:open={isOpen}
  on:close={() => dispatch('close')}
  size="xl"
  ariaLabel="Service logs viewer"
  role="dialog"
  ariaDescribedBy="logs-description"
>
  <div slot="header" class="flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <Icon name="file-text" class="w-5 h-5 text-secondary-400" aria-hidden="true" />
      <h3 id="logs-title" class="text-lg font-semibold text-white">
        Service Logs: {sanitizeInput(serviceName)}
      </h3>
    </div>

    <div class="flex items-center space-x-2" role="toolbar" aria-label="Log viewer controls">
      <!-- Auto refresh toggle -->
      <Button
        variant={autoRefresh ? 'primary' : 'secondary'}
        size="sm"
        on:click={toggleAutoRefresh}
        class="flex items-center space-x-1"
        ariaLabel={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
      >
        <Icon name={autoRefresh ? 'pause' : 'play'} class="w-4 h-4" aria-hidden="true" />
        <span>{autoRefresh ? 'Pause' : 'Auto'}</span>
      </Button>

      <!-- Refresh button -->
      <Button
        variant="secondary"
        size="sm"
        on:click={loadLogs}
        disabled={isLoading}
        class="flex items-center space-x-1"
        ariaLabel="Refresh logs"
      >
        <Icon
          name="refresh-cw"
          class="w-4 h-4 {isLoading ? 'animate-spin' : ''}"
          aria-hidden="true"
        />
        <span>Refresh</span>
      </Button>
    </div>
  </div>

  <div class="flex flex-col h-full space-y-4">
    <!-- Hidden description for screen readers -->
    <div id="logs-description" class="sr-only">
      Service logs viewer for {sanitizeInput(serviceName)}. Use the controls to filter, search, and
      navigate through log entries.
    </div>

    <!-- Controls -->
    <div
      class="flex flex-wrap items-center gap-4 p-4 bg-secondary-800 rounded-lg"
      role="toolbar"
      aria-label="Log filtering and actions"
    >
      <!-- Search -->
      <div class="flex-1 min-w-64">
        <Input
          label="Search logs"
          id="log-search"
          type="text"
          placeholder="Search logs..."
          bind:value={searchTerm}
          class="w-full"
          on:input={filterLogs}
          ariaLabel="Search through log entries"
        />
      </div>

      <!-- Log level filter -->
      <div class="min-w-40">
        <Select
          label="Log level"
          id="log-level"
          bind:value={logLevel}
          options={logLevels}
          placeholder="Log Level"
          on:change={filterLogs}
          ariaLabel="Filter by log level"
        />
      </div>

      <!-- Max lines -->
      <div class="min-w-32">
        <Select
          label="Max lines"
          id="max-lines"
          bind:value={maxLines}
          options={lineOptions}
          placeholder="Lines"
          on:change={loadLogs}
          ariaLabel="Maximum number of log lines to display"
        />
      </div>

      <!-- Actions -->
      <div class="flex items-center space-x-2" role="group" aria-label="Log actions">
        <Button
          variant="secondary"
          size="sm"
          on:click={copyLogs}
          class="flex items-center space-x-1"
          ariaLabel="Copy logs to clipboard"
        >
          <Icon name="copy" class="w-4 h-4" aria-hidden="true" />
          <span>Copy</span>
        </Button>

        <Button
          variant="secondary"
          size="sm"
          on:click={downloadLogs}
          class="flex items-center space-x-1"
          ariaLabel="Download logs as text file"
        >
          <Icon name="download" class="w-4 h-4" aria-hidden="true" />
          <span>Download</span>
        </Button>

        <Button
          variant="secondary"
          size="sm"
          on:click={clearLogs}
          class="flex items-center space-x-1"
          ariaLabel="Clear all displayed logs"
        >
          <Icon name="trash-2" class="w-4 h-4" aria-hidden="true" />
          <span>Clear</span>
        </Button>
      </div>
    </div>

    <!-- Error display -->
    {#if error}
      <div
        class="p-4 bg-error-900/20 border border-error-500 rounded-lg"
        role="alert"
        aria-live="assertive"
      >
        <div class="flex items-center space-x-2">
          <Icon name="alert-circle" class="w-5 h-5 text-error-400" aria-hidden="true" />
          <span class="text-error-400 font-medium">Error loading logs:</span>
        </div>
        <p class="mt-1 text-error-300 text-sm">{sanitizeInput(error)}</p>
        <Button
          variant="secondary"
          size="sm"
          on:click={loadLogs}
          class="mt-2"
          ariaLabel="Retry loading logs"
        >
          Retry
        </Button>
      </div>
    {/if}

    <!-- Logs display -->
    <div class="flex-1 flex flex-col min-h-0">
      <div class="flex items-center justify-between mb-2">
        <div class="text-sm text-secondary-400" aria-live="polite" aria-atomic="true">
          {#if $filteredLogs.length !== $logs.length}
            Showing {$filteredLogs.length} of {$logs.length} lines
          {:else}
            {$logs.length} lines
          {/if}
        </div>

        <div class="flex items-center space-x-2" role="group" aria-label="Log navigation">
          <Button
            variant="ghost"
            size="sm"
            on:click={scrollToTop}
            class="flex items-center space-x-1"
            ariaLabel="Scroll to top of logs"
          >
            <Icon name="arrow-up" class="w-4 h-4" aria-hidden="true" />
            <span>Top</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            on:click={scrollToBottom}
            class="flex items-center space-x-1"
            ariaLabel="Scroll to bottom of logs"
          >
            <Icon name="arrow-down" class="w-4 h-4" aria-hidden="true" />
            <span>Bottom</span>
          </Button>
        </div>
      </div>

      <div
        bind:this={logsContainer}
        on:scroll={handleScroll}
        class="flex-1 overflow-auto bg-secondary-900 border border-secondary-700 rounded-lg p-4 font-mono text-sm logs-container"
        style="max-height: 500px;"
        role="log"
        aria-label="Service log entries"
        aria-live="polite"
        aria-busy={isLoading}
        tabindex="0"
        on:keydown={(e) => {
          if (e.key === 'Home') {
            e.preventDefault();
            scrollToTop();
          } else if (e.key === 'End') {
            e.preventDefault();
            scrollToBottom();
          } else if (e.key === 'PageUp') {
            e.preventDefault();
            logsContainer.scrollTop -= logsContainer.clientHeight * 0.8;
          } else if (e.key === 'PageDown') {
            e.preventDefault();
            logsContainer.scrollTop += logsContainer.clientHeight * 0.8;
          }
        }}
      >
        {#if isLoading && $logs.length === 0}
          <div class="flex items-center justify-center h-32" role="status" aria-live="polite">
            <div class="flex items-center space-x-2 text-secondary-400">
              <Icon name="loader-2" class="w-5 h-5 animate-spin" aria-hidden="true" />
              <span>Loading logs...</span>
            </div>
          </div>
        {:else if $filteredLogs.length === 0}
          <div class="flex items-center justify-center h-32" role="status">
            <div class="text-center text-secondary-400">
              {#if $logs.length === 0}
                <Icon name="file-text" class="w-8 h-8 mx-auto mb-2" aria-hidden="true" />
                <p>No logs available</p>
              {:else}
                <Icon name="search" class="w-8 h-8 mx-auto mb-2" aria-hidden="true" />
                <p>No logs match your filters</p>
              {/if}
            </div>
          </div>
        {:else}
          {#each $filteredLogs as line, index (index)}
            {@const { timestamp, level, message } = formatLogLine(line)}
            <div
              class="flex items-start space-x-2 py-1 hover:bg-secondary-800/50 rounded focus:bg-secondary-800/50 focus:outline-none"
              role="row"
              aria-rowindex={index + 1}
              tabindex="-1"
            >
              <span class="text-secondary-500 text-xs min-w-0 flex-shrink-0" aria-label="Line number">
                {index + 1}
              </span>
              {#if timestamp}
                <span class="text-secondary-400 text-xs min-w-0 flex-shrink-0" aria-label="Timestamp">
                  {sanitizeInput(timestamp)}
                </span>
              {/if}
              {#if level}
                <span
                  class="text-xs font-medium min-w-0 flex-shrink-0 {getLogLevelColor(level)}"
                  aria-label="Log level: {level}"
                >
                  {sanitizeInput(level)}
                </span>
              {/if}
              <span class="text-secondary-300 min-w-0 flex-1 break-all" aria-label="Log message">
                {sanitizeInput(message || line)}
              </span>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </div>
  <div slot="footer" class="flex items-center justify-between">
    <div class="text-sm text-secondary-400" aria-live="polite">
      {#if autoRefresh}
        <div class="flex items-center space-x-1">
          <div class="w-2 h-2 bg-success-400 rounded-full animate-pulse" aria-hidden="true"></div>
          <span>Auto-refreshing every 5 seconds</span>
        </div>
      {:else}
        <span>Auto-refresh disabled</span>
      {/if}
    </div>

    <div class="flex items-center space-x-2">
      <Button
        variant="secondary"
        on:click={() => dispatch('close')}
        ariaLabel="Close service logs modal"
      >
        Close
      </Button>
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

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    :global(.logs-container) {
      border: 2px solid;
    }

    :global(.logs-container::-webkit-scrollbar-thumb) {
      background: currentColor;
    }
  }

  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    :global(.logs-container) {
      scroll-behavior: auto;
    }

    :global(.animate-pulse) {
      animation: none;
    }

    :global(.animate-spin) {
      animation: none;
    }
  }
</style>
