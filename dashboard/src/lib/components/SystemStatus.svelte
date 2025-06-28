<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { systemStore } from '../stores/system';
  import Icon from './Icon.svelte';

  let updateInterval: number;

  // Status color mapping
  const statusColors = {
    healthy: 'var(--color-success)',
    warning: 'var(--color-warning)',
    error: 'var(--color-error)',
    unknown: 'var(--color-text-secondary)',
  };

  // Status icons
  const statusIcons = {
    healthy: 'check-circle',
    warning: 'alert-triangle',
    error: 'alert-circle',
    unknown: 'help-circle',
  };

  // Format uptime
  function formatUptime(seconds: number): string {
    if (!seconds) return '0s';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  // Format memory usage
  function formatMemory(bytes: number): string {
    if (!bytes) return '0B';

    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)}${units[unitIndex]}`;
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

<div class="system-status">
  <!-- Primary Status -->
  <div class="status-primary">
    <div
      class="status-indicator"
      style="color: {statusColors[$systemStore.status] || statusColors.unknown}"
    >
      <Icon name={statusIcons[$systemStore.status] || statusIcons.unknown} size="16" />
    </div>
    <span class="status-text">
      {$systemStore.status || 'Unknown'}
    </span>
  </div>

  <!-- Metrics -->
  <div class="status-metrics">
    <!-- CPU Usage -->
    <div class="metric">
      <Icon name="cpu" size="14" />
      <span class="metric-label">CPU</span>
      <div class="metric-bar">
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
      <span class="metric-value">{($systemStore.metrics?.cpu || 0).toFixed(1)}%</span>
    </div>

    <!-- Memory Usage -->
    <div class="metric">
      <Icon name="hard-drive" size="14" />
      <span class="metric-label">RAM</span>
      <div class="metric-bar">
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
      <span class="metric-value">{($systemStore.metrics?.memory || 0).toFixed(1)}%</span>
    </div>

    <!-- Disk Usage -->
    <div class="metric">
      <Icon name="database" size="14" />
      <span class="metric-label">Disk</span>
      <div class="metric-bar">
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
      <span class="metric-value">{($systemStore.metrics?.disk || 0).toFixed(1)}%</span>
    </div>
  </div>

  <!-- Additional Info -->
  <div class="status-info">
    <!-- Running Services -->
    <div class="info-item">
      <Icon name="server" size="12" />
      <span class="info-value"
        >{$systemStore.services?.filter((s) => s.status === 'running').length || 0}</span
      >
      <span class="info-label">running</span>
    </div>

    <!-- Uptime -->
    <div class="info-item">
      <Icon name="clock" size="12" />
      <span class="info-value">{formatUptime($systemStore.uptime || 0)}</span>
      <span class="info-label">uptime</span>
    </div>

    <!-- Memory Usage -->
    <div class="info-item">
      <Icon name="activity" size="12" />
      <span class="info-value">{formatMemory($systemStore.memoryUsed || 0)}</span>
      <span class="info-label">used</span>
    </div>
  </div>
</div>

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
