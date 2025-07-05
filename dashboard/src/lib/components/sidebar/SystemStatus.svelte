<!-- System Status Component -->
<script lang="ts">
  import { sanitizeInput } from '$lib/utils/validation';

  export let systemStats = {
    cpu: 24,
    memory: 68,
    uptime: sanitizeInput('14h 32m'),
  };
</script>

<div class="sidebar-status" role="complementary" aria-labelledby="system-status-title">
  <div class="status-header">
    <h3 id="system-status-title" class="status-title">System Status</h3>
    <div class="status-indicator online" aria-label="System is online">
      <span class="status-dot" aria-hidden="true"></span>
      <span class="status-text">Online</span>
    </div>
  </div>

  <div class="status-metrics" role="group" aria-label="System metrics">
    <div class="metric">
      <div class="metric-header">
        <span class="metric-label">CPU</span>
        <span class="metric-value" aria-label="CPU usage {systemStats.cpu} percent">
          {systemStats.cpu}%
        </span>
      </div>
      <div
        class="metric-bar"
        role="progressbar"
        aria-valuenow={systemStats.cpu}
        aria-valuemin="0"
        aria-valuemax="100"
        tabindex="0"
      >
        <div class="metric-fill" style="width: {systemStats.cpu}%" aria-hidden="true"></div>
      </div>
    </div>

    <div class="metric">
      <div class="metric-header">
        <span class="metric-label">Memory</span>
        <span class="metric-value" aria-label="Memory usage {systemStats.memory} percent">
          {systemStats.memory}%
        </span>
      </div>
      <div
        class="metric-bar"
        role="progressbar"
        aria-valuenow={systemStats.memory}
        aria-valuemin="0"
        aria-valuemax="100"
        tabindex="0"
      >
        <div class="metric-fill high" style="width: {systemStats.memory}%" aria-hidden="true"></div>
      </div>
    </div>

    <div class="uptime">
      <span class="uptime-label">Uptime</span>
      <span class="uptime-value" aria-label="System uptime {systemStats.uptime}">
        {systemStats.uptime}
      </span>
    </div>
  </div>
</div>

<style>
  .sidebar-status {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--color-border-light);
    background: rgba(255, 255, 255, 0.02);
  }

  .status-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--spacing-md);
  }

  .status-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-text-muted);
    margin: 0;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-success);
    animation: pulse 2s infinite;
  }

  .status-text {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-success);
  }

  .status-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .metric {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .metric-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .metric-label {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .metric-value {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text);
  }

  .metric-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    position: relative;
  }

  .metric-fill {
    height: 100%;
    background: var(--color-primary);
    border-radius: 2px;
    transition: width var(--transition-normal);
  }

  .metric-fill.high {
    background: var(--color-warning);
  }

  .uptime {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-sm);
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius);
  }

  .uptime-label {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .uptime-value {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text);
    font-family: monospace;
  }

  .metric-bar:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .status-dot {
      animation: none;
    }
  }
</style>
