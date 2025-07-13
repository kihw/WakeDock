<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { systemStore } from '../stores/system';
  import Icon from './Icon.svelte';
  import { sanitizeInput } from '../utils/validation';
  import { announceToScreenReader } from '../utils/accessibility';

  let updateInterval: number;
  let previousStatus: string | null = null;
  let isHighContrast = false;
  let prefersReducedMotion = false;

  // Detect user preferences
  onMount(() => {
    // Check for high contrast preference
    isHighContrast = window.matchMedia('(prefers-contrast: high)').matches;

    // Check for reduced motion preference
    prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Listen for status changes and announce them
    const unsubscribe = systemStore.subscribe((store) => {
      const currentStatus = store.system?.status || 'unknown';
      if (previousStatus && currentStatus !== previousStatus) {
        announceToScreenReader(`System status changed to ${currentStatus}`);
      }
      previousStatus = currentStatus;
    });

    // Cleanup subscription
    return () => {
      unsubscribe();
    };
  });

  // Status color mapping with string index signature
  const statusColors: Record<string, string> = {
    healthy: 'var(--color-success)',
    warning: 'var(--color-warning)',
    error: 'var(--color-error)',
    unknown: 'var(--color-text-secondary)',
  };

  // Status icons with string index signature
  const statusIcons: Record<string, string> = {
    healthy: 'check-circle',
    warning: 'alert-triangle',
    error: 'alert-circle',
    unknown: 'help-circle',
  };

  // Computed values to handle null status safely
  $: currentStatus = $systemStore.status || 'unknown';
  $: statusColor = statusColors[currentStatus] || statusColors.unknown;
  $: statusIcon = statusIcons[currentStatus] || statusIcons.unknown;

  // Format uptime with proper sanitization
  function formatUptime(seconds: number): string {
    if (!seconds || typeof seconds !== 'number') return '0s';

    const sanitizedSeconds = Math.max(0, Math.floor(seconds));
    const days = Math.floor(sanitizedSeconds / 86400);
    const hours = Math.floor((sanitizedSeconds % 86400) / 3600);
    const minutes = Math.floor((sanitizedSeconds % 3600) / 60);

    if (days > 0) {
      return sanitizeInput(`${days}d ${hours}h`);
    } else if (hours > 0) {
      return sanitizeInput(`${hours}h ${minutes}m`);
    } else {
      return sanitizeInput(`${minutes}m`);
    }
  }

  // Format memory usage with proper sanitization
  function formatMemory(bytes: number): string {
    if (!bytes || typeof bytes !== 'number') return '0B';

    const sanitizedBytes = Math.max(0, bytes);
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = sanitizedBytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${(typeof size === 'number' ? size : 0).toFixed(1)}${units[unitIndex]}`;
  }

  onMount(() => {
    // Update system status every 30 seconds
    updateInterval = window.setInterval(() => {
      systemStore.loadSystemInfo();
    }, 30000);
  });

  onDestroy(() => {
    if (updateInterval) {
      clearInterval(updateInterval);
    }
  });
</script>

<section
  class="system-status"
  role="region"
  aria-labelledby="system-status-heading"
  class:high-contrast={isHighContrast}
  class:reduced-motion={prefersReducedMotion}
>
  <h2 id="system-status-heading" class="sr-only">System Status Information</h2>

  <!-- Primary Status -->
  <div class="status-primary" role="group" aria-labelledby="primary-status-label">
    <span id="primary-status-label" class="sr-only">Primary system status</span>
    <div
      class="status-indicator"
      style="color: {statusColor}"
      role="img"
      aria-label="Status indicator: {currentStatus}"
    >
      <Icon name={statusIcon} size="16" aria-hidden="true" />
    </div>
    <span class="status-text" aria-live="polite">
      {sanitizeInput(currentStatus)}
    </span>
  </div>

  <!-- Metrics -->
  <div class="status-metrics" role="group" aria-labelledby="metrics-heading">
    <h3 id="metrics-heading" class="sr-only">System Resource Metrics</h3>

    <!-- CPU Usage -->
    <div class="metric" role="group" aria-labelledby="cpu-metric-label">
      <Icon name="cpu" size="14" aria-hidden="true" />
      <span id="cpu-metric-label" class="metric-label">CPU</span>
      <div
        class="metric-bar"
        role="progressbar"
        aria-valuenow={$systemStore.metrics?.cpu || 0}
        aria-valuemin="0"
        aria-valuemax="100"
        aria-label="CPU usage percentage"
      >
        <div
          class="metric-fill"
          style="width: {$systemStore.metrics?.cpu || 0}%; background-color: {($systemStore.metrics
            ?.cpu || 0) > 80
            ? 'var(--color-error)'
            : ($systemStore.metrics?.cpu || 0) > 60
              ? 'var(--color-warning)'
              : 'var(--color-success)'}"
        ></div>
      </div>
      <span class="metric-value" aria-label="CPU usage value">
        {(typeof $systemStore.metrics?.cpu === 'number' ? $systemStore.metrics.cpu : 0).toFixed(1)}%
      </span>
    </div>

    <!-- Memory Usage -->
    <div class="metric" role="group" aria-labelledby="memory-metric-label">
      <Icon name="hard-drive" size="14" aria-hidden="true" />
      <span id="memory-metric-label" class="metric-label">RAM</span>
      <div
        class="metric-bar"
        role="progressbar"
        aria-valuenow={$systemStore.metrics?.memory || 0}
        aria-valuemin="0"
        aria-valuemax="100"
        aria-label="Memory usage percentage"
      >
        <div
          class="metric-fill"
          style="width: {$systemStore.metrics?.memory || 0}%; background-color: {($systemStore
            .metrics?.memory || 0) > 80
            ? 'var(--color-error)'
            : ($systemStore.metrics?.memory || 0) > 60
              ? 'var(--color-warning)'
              : 'var(--color-success)'}"
        ></div>
      </div>
      <span class="metric-value" aria-label="Memory usage value">
        {(typeof $systemStore.metrics?.memory === 'number'
          ? $systemStore.metrics.memory
          : 0
        ).toFixed(1)}%
      </span>
    </div>

    <!-- Disk Usage -->
    <div class="metric" role="group" aria-labelledby="disk-metric-label">
      <Icon name="database" size="14" aria-hidden="true" />
      <span id="disk-metric-label" class="metric-label">Disk</span>
      <div
        class="metric-bar"
        role="progressbar"
        aria-valuenow={$systemStore.metrics?.disk || 0}
        aria-valuemin="0"
        aria-valuemax="100"
        aria-label="Disk usage percentage"
      >
        <div
          class="metric-fill"
          style="width: {$systemStore.metrics?.disk || 0}%; background-color: {($systemStore.metrics
            ?.disk || 0) > 90
            ? 'var(--color-error)'
            : ($systemStore.metrics?.disk || 0) > 75
              ? 'var(--color-warning)'
              : 'var(--color-success)'}"
        ></div>
      </div>
      <span class="metric-value" aria-label="Disk usage value">
        {(typeof $systemStore.metrics?.disk === 'number' ? $systemStore.metrics.disk : 0).toFixed(
          1
        )}%
      </span>
    </div>
  </div>

  <!-- Additional Info -->
  <div class="status-info" role="group" aria-labelledby="additional-info-heading">
    <h3 id="additional-info-heading" class="sr-only">Additional System Information</h3>

    <!-- Running Services -->
    <div class="info-item" aria-label="Running services count">
      <Icon name="server" size="12" aria-hidden="true" />
      <span class="info-value" aria-live="polite">
        {sanitizeInput(
          String($systemStore.services?.filter((s) => s.status === 'running').length || 0)
        )}
      </span>
      <span class="info-label">running</span>
    </div>

    <!-- Uptime -->
    <div class="info-item" aria-label="System uptime">
      <Icon name="clock" size="12" aria-hidden="true" />
      <span class="info-value">
        {formatUptime($systemStore.uptime || 0)}
      </span>
      <span class="info-label">uptime</span>
    </div>

    <!-- Memory Usage -->
    <div class="info-item" aria-label="Memory usage">
      <Icon name="activity" size="12" aria-hidden="true" />
      <span class="info-value">
        {formatMemory($systemStore.memoryUsed || 0)}
      </span>
      <span class="info-label">used</span>
    </div>
  </div>
</section>

<style>
  .system-status {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 0.5rem 1rem;
    background-color: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 0.85rem;
  }

  .status-primary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .status-indicator {
    display: flex;
    align-items: center;
  }

  .status-text {
    font-weight: 600;
    color: var(--color-text);
    text-transform: capitalize;
  }

  .status-metrics {
    display: flex;
    gap: 1rem;
  }

  .metric {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    min-width: 0;
  }

  .metric-label {
    font-weight: 500;
    color: var(--color-text-secondary);
    font-size: 0.8rem;
    min-width: max-content;
  }

  .metric-bar {
    position: relative;
    width: 40px;
    height: 6px;
    background-color: var(--color-border);
    border-radius: 3px;
    overflow: hidden;
  }

  .metric-fill {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  .metric-value {
    font-weight: 600;
    color: var(--color-text);
    font-size: 0.8rem;
    min-width: max-content;
  }

  .status-info {
    display: flex;
    gap: 1rem;
  }

  .info-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    color: var(--color-text-secondary);
  }

  .info-value {
    font-weight: 600;
    color: var(--color-text);
  }

  .info-label {
    font-size: 0.75rem;
  }

  /* Accessibility Enhancements */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  /* High Contrast Support */
  .system-status.high-contrast {
    border-width: 2px;
    border-color: var(--color-text);
  }

  .system-status.high-contrast .metric-bar {
    border: 1px solid var(--color-text);
  }

  .system-status.high-contrast .metric-fill {
    border: 1px solid transparent;
  }

  .system-status.high-contrast .status-indicator {
    border: 1px solid var(--color-text);
    border-radius: 50%;
    padding: 2px;
  }

  /* Reduced Motion Support */
  .system-status.reduced-motion .metric-fill {
    transition: none;
  }

  .system-status.reduced-motion * {
    animation: none !important;
    transition: none !important;
  }

  /* Focus Management */
  .system-status:focus-within {
    outline: 2px solid var(--color-focus);
    outline-offset: 2px;
  }

  /* Screen Reader Improvements */
  [aria-live='polite'] {
    position: relative;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .system-status {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }

    .status-metrics {
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .status-info {
      flex-wrap: wrap;
      gap: 0.5rem;
    }
  }

  @media (max-width: 480px) {
    .system-status {
      padding: 0.75rem;
    }

    .metric-bar {
      width: 30px;
      height: 4px;
    }

    .info-item {
      font-size: 0.75rem;
    }
  }

  /* Responsive */
  @media (max-width: 1024px) {
    .status-metrics {
      display: none;
    }
  }

  @media (max-width: 768px) {
    .system-status {
      gap: 1rem;
    }

    .status-info {
      gap: 0.75rem;
    }

    .info-item {
      flex-direction: column;
      gap: 0.1rem;
      text-align: center;
    }
  }

  /* Animation for status changes */
  .status-indicator {
    transition: color 0.3s ease;
  }

  .metric-fill {
    transition:
      width 0.5s ease,
      background-color 0.3s ease;
  }

  /* Pulse animation for critical states */
  .status-primary:has(.status-indicator[style*='var(--color-error)']) {
    animation: pulse-error 2s infinite;
  }

  @keyframes pulse-error {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }
</style>
